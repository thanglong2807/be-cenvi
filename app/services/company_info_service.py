# app/services/company_info_service.py

import json
import os
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.company_info_model import CompanyInfo
from app.schemas.company_info_schema import CompanyInfoCreate, CompanyInfoUpdate, SeedResult

DRIVE_FOLDER_BASE = "https://drive.google.com/drive/folders/"
FOLDERS_JSON = "app/data/folders.json"
EMPLOYEES_JSON = "app/data/employees.json"


def _build_drive_link(folder_id: Optional[str]) -> Optional[str]:
    if not folder_id:
        return None
    return f"{DRIVE_FOLDER_BASE}{folder_id}"


def _load_employee_map() -> dict:
    """Trả về dict {employee_id: employee_name}"""
    try:
        with open(EMPLOYEES_JSON, encoding="utf-8") as f:
            data = json.load(f)
        items = data.get("items", []) if isinstance(data, dict) else data
        return {emp["id"]: emp.get("name", "") for emp in items}
    except Exception:
        return {}


def _load_folders() -> list:
    try:
        with open(FOLDERS_JSON, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("items", []) if isinstance(data, dict) else data
    except Exception:
        return []


class CompanyInfoService:
    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_or_404(self, company_id: int) -> CompanyInfo:
        obj = self.db.query(CompanyInfo).filter(CompanyInfo.id == company_id).first()
        if not obj:
            raise HTTPException(status_code=404, detail=f"Không tìm thấy công ty với id={company_id}")
        return obj

    def _enrich(self, obj: CompanyInfo) -> dict:
        """Thêm drive_folder_link vào dict trả về."""
        data = {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
        data["drive_folder_link"] = _build_drive_link(obj.drive_folder_id)
        return data

    def get_by_ma_kh(self, ma_kh: str) -> Optional[CompanyInfo]:
        return self.db.query(CompanyInfo).filter(CompanyInfo.ma_kh == ma_kh).first()

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def get_all(self, skip: int = 0, limit: int = 100) -> List[dict]:
        rows = (
            self.db.query(CompanyInfo)
            .order_by(CompanyInfo.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [self._enrich(r) for r in rows]

    def get_by_id(self, company_id: int) -> dict:
        return self._enrich(self._get_or_404(company_id))

    def search(self, keyword: str, skip: int = 0, limit: int = 100) -> List[dict]:
        kw = f"%{keyword}%"
        rows = (
            self.db.query(CompanyInfo)
            .filter(
                CompanyInfo.ten_cong_ty.ilike(kw)
                | CompanyInfo.ma_kh.ilike(kw)
                | CompanyInfo.ma_so_thue.ilike(kw)
                | CompanyInfo.phu_trach_hien_tai.ilike(kw)
            )
            .order_by(CompanyInfo.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [self._enrich(r) for r in rows]

    def create(self, data: CompanyInfoCreate) -> dict:
        if self.get_by_ma_kh(data.ma_kh):
            raise HTTPException(
                status_code=409,
                detail=f"Mã KH '{data.ma_kh}' đã tồn tại",
            )
        now = datetime.now()
        obj = CompanyInfo(**data.model_dump(), created_at=now, updated_at=now)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return self._enrich(obj)

    def update(self, company_id: int, data: CompanyInfoUpdate) -> dict:
        obj = self._get_or_404(company_id)
        if data.ma_kh and data.ma_kh != obj.ma_kh:
            existing = self.get_by_ma_kh(data.ma_kh)
            if existing:
                raise HTTPException(
                    status_code=409,
                    detail=f"Mã KH '{data.ma_kh}' đã tồn tại (id={existing.id})",
                )
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        obj.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(obj)
        return self._enrich(obj)

    def delete(self, company_id: int) -> None:
        obj = self._get_or_404(company_id)
        self.db.delete(obj)
        self.db.commit()

    # ------------------------------------------------------------------
    # SEED từ folders.json
    # ------------------------------------------------------------------

    def seed_from_folders(self) -> SeedResult:
        """
        Import toàn bộ công ty từ folders.json vào bảng COMPANY_INFO.
        - ma_kh        ← company_code
        - ten_cong_ty  ← company_name
        - ma_so_thue   ← mst
        - phu_trach    ← tên nhân viên tra qua manager_employee_id
        - drive_folder_id ← root_folder_id
        Bỏ qua các bản ghi có ma_kh đã tồn tại (không ghi đè).
        """
        folders = _load_folders()
        employee_map = _load_employee_map()

        created = 0
        skipped = 0
        errors: list[str] = []

        for folder in folders:
            company_code = folder.get("company_code", "").strip()
            if not company_code:
                errors.append(f"id={folder.get('id')}: thiếu company_code, bỏ qua")
                continue

            # Bỏ qua nếu đã có
            if self.get_by_ma_kh(company_code):
                skipped += 1
                continue

            try:
                emp_id = folder.get("manager_employee_id")
                phu_trach = employee_map.get(emp_id, "") if emp_id else ""

                now = datetime.now()
                obj = CompanyInfo(
                    ma_kh=company_code,
                    ten_cong_ty=folder.get("company_name", company_code),
                    phu_trach_hien_tai=phu_trach or None,
                    ma_so_thue=folder.get("mst") or None,
                    drive_folder_id=folder.get("root_folder_id") or None,
                    created_at=now,
                    updated_at=now,
                )
                self.db.add(obj)
                self.db.flush()   # để bắt lỗi sớm, chưa commit
                created += 1
            except Exception as e:
                self.db.rollback()
                errors.append(f"{company_code}: {str(e)}")
                continue

        self.db.commit()
        return SeedResult(
            total_folders=len(folders),
            created=created,
            skipped=skipped,
            errors=errors,
        )
