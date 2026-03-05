# app/api/v1/migration.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

# ==========================================
# IMPORT SERVICES
# ==========================================
from app.services.folder_service import (
    check_migration_status, 
    execute_migration_step, 
    import_folder_from_drive, 
    delete_folder_on_drive,
    scan_folders_not_in_db, 
    link_drive_to_existing_db,
    get_admin_folder_link 
)

from app.services.migration_structure_service import (
    scan_structure_changes, 
    execute_rename_folder,
    fix_structure_single_company
)

# ==========================================
# ROUTER CONFIG
# ==========================================
router = APIRouter(prefix="/migration", tags=["Migration Tool"])

# ==========================================
# PYDANTIC MODELS (DEFINITIONS)
# ==========================================

class CheckPayload(BaseModel):
    company_code: str
    mst: str
    company_name: str
    manager_name: str

class ExecutePayload(BaseModel):
    folder_id: int
    action: str
    new_data: dict = {}

class ImportPayload(BaseModel):
    root_folder_id: str
    company_name: str
    company_code: Optional[str] = None
    mst: Optional[str] = None
    manager_employee_id: Optional[int] = None
    # Thêm 2 trường này để hỗ trợ tính năng chọn trạng thái/template
    status: str = "active"
    template: str = "STANDARD"

class LinkPayload(BaseModel):
    folder_db_id: int
    drive_id: str

class RenamePayload(BaseModel):
    drive_id: str
    new_name: str

class SingleFixPayload(BaseModel):
    folder_db_id: int


class AdminLinkPayload(BaseModel):
    company_code: str

# app/api/v1/migration.py

class RenameExecutePayload(BaseModel):
    drive_id: str
    new_name: str
    folder_id: int # Để lưu vết vào DB

@router.post("/analyze-and-suggest-name")
def analyze_file(drive_id: str, company_code: str):
    """
    API gọi khi bạn click vào 1 file:
    - Tải nội dung file về bộ nhớ tạm.
    - Đọc ruột file (XML/Excel).
    - Trả về dữ liệu nội dung + Tên gợi ý chuẩn.
    """
    service = get_drive_service()
    file_metadata = service.files().get(fileId=drive_id, fields="name, mimeType").execute()
    
    # Tải nội dung
    content = service.files().get_media(fileId=drive_id).execute()
    
    # Dùng hàm analyze_file_content đã viết ở bước trước
    suggested_name = analyze_file_content(file_metadata['name'], content, company_code)
    
    return {
        "old_name": file_metadata['name'],
        "suggested_name": suggested_name,
        "mime_type": file_metadata['mimeType'],
        # Trả thêm dữ liệu đã bóc tách để hiển thị trực quan
        "parsed_data": parse_file_to_json(content, file_metadata['mimeType']) 
    }

@router.post("/confirm-and-rename")
def confirm_and_rename(payload: RenameExecutePayload):
    """Bấm nút này để đổi tên thật trên Drive"""
    service = get_drive_service()
    success = rename_drive_file(service, payload.drive_id, payload.new_name)
    return {"status": "success" if success else "error"}
# ==========================================
# API ENDPOINTS
# ==========================================

# --- 1. MIGRATION TOOL (EXCEL VS DB) ---

@router.post("/check")
def check_item(payload: CheckPayload):
    """Kiểm tra sự khác biệt giữa Excel và Database"""
    return check_migration_status(
        payload.company_code, 
        payload.mst, 
        payload.company_name, 
        payload.manager_name
    )

@router.post("/execute")
def execute_item(payload: ExecutePayload):
    """Thực thi thay đổi (Sửa, Bàn giao, Active...)"""
    try:
        msg = execute_migration_step(payload.folder_id, payload.action, payload.new_data)
        return {"status": "success", "message": msg}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- 2. DRIVE SCANNER & IMPORT ---

@router.get("/scan-missing")
def scan_missing_drive_folders():
    """Quét các folder có trên Drive nhưng chưa lưu trong DB"""
    try:
        return scan_folders_not_in_db()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import")
def import_drive_folder(payload: ImportPayload):
    """Lưu folder từ Drive vào Database"""
    try:
        return import_folder_from_drive(payload.dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/drive-folder/{drive_id}")
def delete_drive_item(drive_id: str):
    """Xóa vĩnh viễn folder trên Drive"""
    try:
        delete_folder_on_drive(drive_id)
        return {"status": "success", "message": "Đã xóa folder trên Drive"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/link-drive")
def link_drive_folder(payload: LinkPayload):
    """Ghép nối folder Drive vào record DB có sẵn"""
    try:
        link_drive_to_existing_db(payload.folder_db_id, payload.drive_id)
        return {"status": "success", "message": "Đã ghép nối thành công"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- 3. STRUCTURE MIGRATION (ĐỔI TÊN FOLDER CON) ---

@router.get("/scan-structure")
def get_structure_diff(limit: int = 20):
    """
    Quét xem folder nào sai cấu trúc (Preview). 
    Có limit để tránh timeout.
    """
    try:
        changes = scan_structure_changes(limit=limit)
        return {"count": len(changes), "items": changes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute-rename")
def run_rename_folder(payload: RenamePayload):
    """Thực thi đổi tên 1 folder"""
    try:
        success = execute_rename_folder(payload.drive_id, payload.new_name)
        if success:
            return {"status": "success", "message": "Đã đổi tên thành công"}
        else:
            raise ValueError("Google Drive API trả về lỗi")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/fix-structure-single")
def fix_structure_single(payload: SingleFixPayload):
    """
    Deep Fixer: Chạy vòng lặp quét và sửa lỗi cho 1 công ty cụ thể.
    Dùng để in log realtime ở Frontend.
    """
    try:
        logs = fix_structure_single_company(payload.folder_db_id)
        return {"logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# app/api/v1/migration.py

@router.post("/get-admin-link")
def get_admin_link(payload: AdminLinkPayload):
    return get_admin_folder_link(payload.company_code)