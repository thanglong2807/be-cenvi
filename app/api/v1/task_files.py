# app/api/v1/task_files.py
"""File/link đính kèm theo task của từng công ty — hỗ trợ lọc theo log_id (kỳ cụ thể)."""

import os, uuid, mimetypes
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.models.workflow_model import CompanyTaskFile

router = APIRouter(tags=["Task Files"])

UPLOAD_DIR = "static/task-files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".png", ".jpg", ".jpeg", ".gif", ".zip", ".rar", ".txt", ".csv",
}
MAX_SIZE_MB = 20


class LinkPayload(BaseModel):
    name: str
    url: str
    uploaded_by: Optional[str] = None
    log_id: Optional[int] = None


def _to_dict(f: CompanyTaskFile, request_base: str = "") -> dict:
    return {
        "id": f.id,
        "company_id": f.company_id,
        "task_id": f.task_id,
        "log_id": f.log_id,
        "name": f.name,
        "type": f.type,
        "path": f.path,
        "url": f.url if f.type == "link" else (f"{request_base}/{f.path}" if f.path else None),
        "uploaded_by": f.uploaded_by,
        "created_at": f.created_at,
    }


# ── List ──────────────────────────────────────────────────────────────────────

@router.get("/company-info/{company_id}/tasks/{task_id}/files")
def list_files(
    company_id: int,
    task_id: int,
    log_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(CompanyTaskFile).filter(
        CompanyTaskFile.company_id == company_id,
        CompanyTaskFile.task_id == task_id,
    )
    if log_id is not None:
        q = q.filter(CompanyTaskFile.log_id == log_id)
    files = q.order_by(CompanyTaskFile.created_at.desc()).all()
    return [_to_dict(f) for f in files]


# ── Upload file ───────────────────────────────────────────────────────────────

@router.post("/company-info/{company_id}/tasks/{task_id}/files/upload")
async def upload_file(
    company_id: int,
    task_id: int,
    file: UploadFile = File(...),
    uploaded_by: Optional[str] = Form(None),
    log_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Loại file không hỗ trợ: {ext}")

    content = await file.read()
    if len(content) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File quá lớn (tối đa {MAX_SIZE_MB}MB)")

    # Lưu theo log_id nếu có, để phân thư mục theo kỳ
    sub = str(log_id) if log_id else "shared"
    folder = os.path.join(UPLOAD_DIR, str(company_id), str(task_id), sub)
    os.makedirs(folder, exist_ok=True)

    unique_name = f"{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(folder, unique_name)
    with open(save_path, "wb") as f:
        f.write(content)

    record = CompanyTaskFile(
        company_id=company_id,
        task_id=task_id,
        log_id=log_id,
        name=file.filename or unique_name,
        type="file",
        path=save_path.replace("\\", "/"),
        uploaded_by=uploaded_by,
        created_at=datetime.now(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _to_dict(record)


# ── Add link ──────────────────────────────────────────────────────────────────

@router.post("/company-info/{company_id}/tasks/{task_id}/files/link")
def add_link(company_id: int, task_id: int, payload: LinkPayload, db: Session = Depends(get_db)):
    if not payload.url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL không hợp lệ")

    record = CompanyTaskFile(
        company_id=company_id,
        task_id=task_id,
        log_id=payload.log_id,
        name=payload.name,
        type="link",
        url=payload.url,
        uploaded_by=payload.uploaded_by,
        created_at=datetime.now(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _to_dict(record)


# ── Preview (inline) ─────────────────────────────────────────────────────────

INLINE_TYPES = {
    ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg",
    ".txt", ".csv", ".html",
}

@router.get("/files/{file_id}/preview")
def preview_file(file_id: int, db: Session = Depends(get_db)):
    """Serve file với Content-Disposition: inline để browser mở trực tiếp."""
    record = db.query(CompanyTaskFile).filter(CompanyTaskFile.id == file_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="File không tồn tại")
    if record.type == "link":
        raise HTTPException(status_code=400, detail="Đây là link, không phải file")
    if not record.path or not os.path.exists(record.path):
        raise HTTPException(status_code=404, detail="File vật lý không tìm thấy")

    ext = os.path.splitext(record.path)[1].lower()
    mime, _ = mimetypes.guess_type(record.path)
    mime = mime or "application/octet-stream"
    disposition = "inline" if ext in INLINE_TYPES else "attachment"

    return FileResponse(
        path=record.path,
        media_type=mime,
        filename=record.name,
        headers={"Content-Disposition": f'{disposition}; filename="{record.name}"'},
    )


# ── Delete ────────────────────────────────────────────────────────────────────

@router.delete("/company-info/{company_id}/tasks/{task_id}/files/{file_id}")
def delete_file(company_id: int, task_id: int, file_id: int, db: Session = Depends(get_db)):
    record = db.query(CompanyTaskFile).filter(
        CompanyTaskFile.id == file_id,
        CompanyTaskFile.company_id == company_id,
        CompanyTaskFile.task_id == task_id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="File không tồn tại")

    if record.type == "file" and record.path and os.path.exists(record.path):
        os.remove(record.path)

    db.delete(record)
    db.commit()
    return {"message": "Đã xóa"}
