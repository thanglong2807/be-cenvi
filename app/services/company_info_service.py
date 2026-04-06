# app/services/company_info_service.py

import os
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.company_info_model import CompanyInfo
from app.models.employee_model import Employee
from app.models.folder_model import Folder
from app.schemas.company_info_schema import CompanyInfoCreate, CompanyInfoUpdate, SeedResult
from app.services.drive_service import get_drive_service, add_permission
from app.services.drive_folder_builder import apply_template
from app.core.folder_templates import FOLDER_TEMPLATES

DRIVE_FOLDER_BASE = "https://drive.google.com/drive/folders/"
ROOT_DRIVE_FOLDER_ID = os.getenv("ROOT_DRIVE_FOLDER_ID") or os.getenv("COMPANY_PARENT_FOLDER_ID")


def _build_drive_link(folder_id: Optional[str]) -> Optional[str]:
    if not folder_id:
        return None
    return f"{DRIVE_FOLDER_BASE}{folder_id}"


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

        # Tách manager_employee_id ra trước (không lưu vào DB)
        manager_employee_id = data.manager_employee_id
        db_data = data.model_dump(exclude={"manager_employee_id"})

        # Tạo Drive folder nếu có manager_employee_id
        if manager_employee_id and not db_data.get("drive_folder_id"):
            drive_folder_id = self._create_drive_folder(
                ma_kh=data.ma_kh,
                ten_cong_ty=data.ten_cong_ty,
                ma_so_thue=data.ma_so_thue or "",
                manager_employee_id=manager_employee_id,
                template=data.folder_template or "STANDARD",
                year=data.folder_year or datetime.now().year,
            )
            if drive_folder_id:
                db_data["drive_folder_id"] = drive_folder_id
                db_data["folder_status"] = "active"

        now = datetime.now()
        obj = CompanyInfo(**db_data, created_at=now, updated_at=now)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return self._enrich(obj)

    def _create_drive_folder(
        self,
        ma_kh: str,
        ten_cong_ty: str,
        ma_so_thue: str,
        manager_employee_id: int,
        template: str,
        year: int,
    ) -> Optional[str]:
        """
        Tạo folder Drive cho công ty mới.
        Trả về folder_id nếu thành công, None nếu lỗi.
        """
        # Lấy email nhân viên từ DB
        employee = self.db.query(Employee).filter(Employee.id == manager_employee_id).first()
        if not employee or not employee.email:
            print(f"⚠️ Không tìm thấy email nhân viên id={manager_employee_id}, bỏ qua tạo Drive")
            return None

        if not ROOT_DRIVE_FOLDER_ID:
            print("⚠️ Chưa cấu hình ROOT_DRIVE_FOLDER_ID, bỏ qua tạo Drive")
            return None

        if template not in FOLDER_TEMPLATES:
            template = "STANDARD"

        try:
            drive = get_drive_service()

            # Tên folder: {ma_kh}_{ten_cong_ty}_{ma_so_thue}
            folder_name = f"{ma_kh}_{ten_cong_ty}_{ma_so_thue}"

            # Tạo folder gốc trong Drive
            root_obj = drive.files().create(
                body={
                    "name": folder_name,
                    "mimeType": "application/vnd.google-apps.folder",
                    "parents": [ROOT_DRIVE_FOLDER_ID],
                },
                fields="id",
                supportsAllDrives=True,
            ).execute()

            folder_id = root_obj["id"]

            # Cấp quyền cho nhân viên phụ trách
            add_permission(drive, folder_id, employee.email, role="fileOrganizer")

            # Áp template tạo cấu trúc sub-folders
            current_year = datetime.now().year
            years = list(range(year, max(current_year, year) + 1)) if year <= 2024 else [year]
            for y in years:
                apply_template(
                    service=drive,
                    parent_folder_id=folder_id,
                    template_name=template,
                    company_short_name=ten_cong_ty,
                    year=y,
                )

            print(f"✅ Đã tạo Drive folder '{folder_name}' id={folder_id}")
            return folder_id

        except Exception as e:
            print(f"⚠️ Lỗi tạo Drive folder: {e}")
            return None

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
        Import toàn bộ công ty từ bảng SQL `folders` vào bảng COMPANY_INFO.
        - ma_kh           ← company_code
        - ten_cong_ty     ← company_name
        - ma_so_thue      ← mst
        - phu_trach       ← tên nhân viên tra qua manager_employee_id → employees.name
        - drive_folder_id ← root_folder_id
        - folder_year     ← year
        - folder_template ← template
        - folder_status   ← status
        Bỏ qua các bản ghi có ma_kh đã tồn tại (không ghi đè).
        """
        folders = self.db.query(Folder).all()

        # Map employee_id → name từ bảng employees
        employees = self.db.query(Employee).all()
        employee_map = {e.id: e.name for e in employees}

        created = 0
        skipped = 0
        errors: list[str] = []

        for folder in folders:
            company_code = (folder.company_code or "").strip()
            if not company_code:
                errors.append(f"id={folder.id}: thiếu company_code, bỏ qua")
                continue

            if self.get_by_ma_kh(company_code):
                skipped += 1
                continue

            try:
                phu_trach = employee_map.get(folder.manager_employee_id) if folder.manager_employee_id else None

                now = datetime.now()
                obj = CompanyInfo(
                    ma_kh=company_code,
                    ten_cong_ty=folder.company_name or company_code,
                    phu_trach_hien_tai=phu_trach,
                    ma_so_thue=folder.mst or None,
                    drive_folder_id=folder.root_folder_id or None,
                    folder_year=folder.year,
                    folder_template=folder.template or None,
                    folder_status=folder.status or None,
                    created_at=now,
                    updated_at=now,
                )
                self.db.add(obj)
                self.db.flush()
                created += 1
            except Exception as e:
                self.db.rollback()
                errors.append(f"{company_code}: {str(e)}")

        self.db.commit()
        return SeedResult(
            total_folders=len(folders),
            created=created,
            skipped=skipped,
            errors=errors,
        )
