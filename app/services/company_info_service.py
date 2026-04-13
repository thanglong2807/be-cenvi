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
from app.services.drive_service import get_drive_service, add_permission, find_shortcuts_by_target_id
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

        # Nếu chưa có manager_employee_id, tìm từ tên phu_trach_hien_tai
        employee_folder_id = None
        if not manager_employee_id and data.phu_trach_hien_tai:
            employee = self.db.query(Employee).filter(
                Employee.name == data.phu_trach_hien_tai
            ).first()
            if employee:
                manager_employee_id = employee.id
                employee_folder_id = employee.drive_folder_id
                print(f"✅ Tìm thấy nhân viên: {employee.name} (id={employee.id})")
                if employee_folder_id:
                    print(f"   Drive folder: {employee_folder_id}")

        # Tạo Drive folder nếu có manager_employee_id
        if manager_employee_id and not db_data.get("drive_folder_id"):
            drive_folder_id = self._create_drive_folder(
                ma_kh=data.ma_kh,
                ten_cong_ty=data.ten_cong_ty_viet_tat or data.ten_cong_ty,
                ma_so_thue=data.ma_so_thue or "",
                manager_employee_id=manager_employee_id,
                employee_folder_id=employee_folder_id,
                employee_name=data.phu_trach_hien_tai,
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
        employee_folder_id: Optional[str] = None,
        employee_name: Optional[str] = None,
    ) -> Optional[str]:
        """
        Tạo folder Drive cho công ty mới và shortcut trong folder nhân viên.
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

            # Tạo folder gốc trong Drive (support Shared Drive)
            root_obj = drive.files().create(
                body={
                    "name": folder_name,
                    "mimeType": "application/vnd.google-apps.folder",
                    "parents": [ROOT_DRIVE_FOLDER_ID],
                },
                fields="id",
                supportsAllDrives=True,
                supportsTeamDrives=True,
            ).execute()

            folder_id = root_obj["id"]

            # Cấp quyền cho nhân viên phụ trách
            add_permission(drive, folder_id, employee.email, role="fileOrganizer")

            # Tạo shortcut trong folder nhân viên nếu có
            if employee_folder_id:
                try:
                    # Lấy tên folder công ty từ Drive
                    company_folder = drive.files().get(
                        fileId=folder_id,
                        fields='name',
                        supportsAllDrives=True,
                        supportsTeamDrives=True
                    ).execute()

                    shortcut_name = company_folder['name']  # Dùng tên folder công ty
                    shortcut_metadata = {
                        'name': shortcut_name,
                        'mimeType': 'application/vnd.google-apps.shortcut',
                        'shortcutDetails': {
                            'targetId': folder_id
                        },
                        'parents': [employee_folder_id]
                    }
                    shortcut = drive.files().create(
                        body=shortcut_metadata,
                        fields='id, name',
                        supportsAllDrives=True,
                        supportsTeamDrives=True
                    ).execute()
                    print(f"✅ Đã tạo shortcut '{shortcut_name}' trong folder nhân viên")
                except Exception as e:
                    print(f"⚠️ Lỗi tạo shortcut (bỏ qua): {str(e)}")
                    print(f"   Kiểm tra: Folder nhân viên {employee_folder_id} có accessible không?")

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

        # Check nếu nhân viên phụ trách thay đổi
        old_phu_trach = obj.phu_trach_hien_tai
        new_phu_trach = data.phu_trach_hien_tai if hasattr(data, 'phu_trach_hien_tai') else None

        if new_phu_trach and new_phu_trach != old_phu_trach and obj.drive_folder_id:
            try:
                drive = get_drive_service()

                # Lấy tên folder công ty
                company_folder = drive.files().get(
                    fileId=obj.drive_folder_id,
                    fields='name',
                    supportsAllDrives=True,
                    supportsTeamDrives=True
                ).execute()
                shortcut_name = company_folder['name']

                # Xoá shortcut từ folder nhân viên cũ
                if old_phu_trach:
                    old_employee = self.db.query(Employee).filter(
                        Employee.name == old_phu_trach
                    ).first()

                    if old_employee and old_employee.drive_folder_id:
                        # Tìm shortcut bằng targetId thay vì tên
                        shortcut_ids = find_shortcuts_by_target_id(
                            drive,
                            old_employee.drive_folder_id,
                            obj.drive_folder_id
                        )

                        for shortcut_id in shortcut_ids:
                            drive.files().delete(
                                fileId=shortcut_id,
                                supportsAllDrives=True,
                                supportsTeamDrives=True
                            ).execute()

                        if shortcut_ids:
                            print(f"✅ Xoá shortcut từ folder nhân viên cũ: {old_phu_trach}")
                        else:
                            print(f"⏭️  Không tìm thấy shortcut ở nhân viên cũ: {old_phu_trach}")

                # Thêm shortcut vào folder nhân viên mới
                new_employee = self.db.query(Employee).filter(
                    Employee.name == new_phu_trach
                ).first()

                if new_employee and new_employee.drive_folder_id:
                    shortcut_metadata = {
                        'name': shortcut_name,
                        'mimeType': 'application/vnd.google-apps.shortcut',
                        'shortcutDetails': {
                            'targetId': obj.drive_folder_id
                        },
                        'parents': [new_employee.drive_folder_id]
                    }

                    shortcut = drive.files().create(
                        body=shortcut_metadata,
                        fields='id, name',
                        supportsAllDrives=True,
                        supportsTeamDrives=True
                    ).execute()
                    print(f"✅ Thêm shortcut vào folder nhân viên mới: {new_phu_trach}")

            except Exception as e:
                print(f"⚠️ Lỗi cập nhật shortcut: {e}")

        # Update fields
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        obj.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(obj)
        return self._enrich(obj)

    def delete(self, company_id: int, delete_drive_folder: bool = True) -> dict:
        """
        Xoá công ty từ database và tuỳ chọn xoá folder + shortcut trong Google Drive.

        Args:
            company_id: Company ID
            delete_drive_folder: Có xoá folder Drive không? (default: True)

        Returns:
            dict: Result with status
        """
        obj = self._get_or_404(company_id)
        ma_kh = obj.ma_kh
        drive_folder_id = obj.drive_folder_id
        phu_trach = obj.phu_trach_hien_tai

        shortcut_deleted = False

        # Xoá shortcut trong folder nhân viên
        if delete_drive_folder and phu_trach and drive_folder_id:
            try:
                # Tìm employee folder ID
                employee = self.db.query(Employee).filter(
                    Employee.name == phu_trach
                ).first()

                if employee and employee.drive_folder_id:
                    try:
                        drive = get_drive_service()

                        # Tìm shortcut bằng targetId (tránh vấn đề ký tự đặc biệt)
                        shortcut_ids = find_shortcuts_by_target_id(
                            drive,
                            employee.drive_folder_id,
                            drive_folder_id
                        )

                        # Xoá tất cả shortcut pointing tới company folder này
                        for shortcut_id in shortcut_ids:
                            drive.files().delete(
                                fileId=shortcut_id,
                                supportsAllDrives=True,
                                supportsTeamDrives=True
                            ).execute()
                            print(f"✅ Xoá shortcut '{shortcut_id}' từ folder nhân viên")
                            shortcut_deleted = True

                        if not shortcut_ids:
                            print(f"⏭️  Không tìm thấy shortcut trong folder nhân viên {employee.name}")

                    except Exception as e:
                        print(f"⚠️ Lỗi xoá shortcut: {e}")

            except Exception as e:
                print(f"⚠️ Lỗi khi tìm employee: {e}")

        # Xoá folder Drive nếu có
        if delete_drive_folder and drive_folder_id:
            try:
                drive = get_drive_service()
                drive.files().delete(
                    fileId=drive_folder_id,
                    supportsAllDrives=True,
                    supportsTeamDrives=True
                ).execute()
                print(f"✅ Xoá Drive folder thành công: {drive_folder_id}")
            except Exception as e:
                print(f"⚠️ Lỗi xoá Drive folder: {e}")

        # Xoá từ database
        self.db.delete(obj)
        self.db.commit()

        return {
            'status': 'success',
            'message': f"✅ Xoá công ty '{ma_kh}' thành công",
            'ma_kh': ma_kh,
            'drive_folder_deleted': delete_drive_folder and bool(drive_folder_id),
            'shortcut_deleted': shortcut_deleted
        }

    def add_shortcut_to_employee_folder(self, ma_kh: str, employee_id: int) -> dict:
        """
        Thêm shortcut công ty vào folder nhân viên

        Args:
            ma_kh: Company code
            employee_id: Employee ID

        Returns:
            dict: Result with status
        """
        # Get company
        company = self.get_by_ma_kh(ma_kh)
        if not company:
            raise HTTPException(status_code=404, detail=f"Công ty '{ma_kh}' không tồn tại")

        if not company.drive_folder_id:
            raise HTTPException(status_code=400, detail=f"Công ty '{ma_kh}' chưa có Drive folder")

        # Get employee
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail=f"Nhân viên id={employee_id} không tồn tại")

        if not employee.drive_folder_id:
            raise HTTPException(status_code=400, detail=f"Nhân viên '{employee.name}' chưa có Drive folder")

        try:
            drive = get_drive_service()

            # Lấy tên folder công ty từ Drive
            company_folder = drive.files().get(
                fileId=company.drive_folder_id,
                fields='name',
                supportsAllDrives=True,
                supportsTeamDrives=True
            ).execute()

            shortcut_name = company_folder['name']  # Dùng tên thật của folder
            shortcut_metadata = {
                'name': shortcut_name,
                'mimeType': 'application/vnd.google-apps.shortcut',
                'shortcutDetails': {
                    'targetId': company.drive_folder_id
                },
                'parents': [employee.drive_folder_id]
            }

            shortcut = drive.files().create(
                body=shortcut_metadata,
                fields='id, name',
                supportsAllDrives=True,
                supportsTeamDrives=True
            ).execute()

            return {
                'status': 'success',
                'message': f"✅ Tạo shortcut '{shortcut_name}' thành công",
                'shortcut_id': shortcut['id'],
                'shortcut_name': shortcut['name']
            }

        except Exception as e:
            print(f"❌ Lỗi tạo shortcut: {e}")
            raise HTTPException(status_code=500, detail=f"Lỗi tạo shortcut: {str(e)}")

    # ------------------------------------------------------------------
    # SEED từ folders.json
    # ------------------------------------------------------------------

    def seed_from_folders(self) -> SeedResult:
        """
        Upsert toàn bộ công ty từ bảng SQL `folders` vào bảng COMPANY_INFO.
        - Nếu chưa có (theo ma_kh): tạo mới
        - Nếu đã có: cập nhật folder_year, folder_template, folder_status,
          drive_folder_id, phu_trach_hien_tai (từ employees)
        """
        folders = self.db.query(Folder).all()

        # Map employee_id → name từ bảng employees
        employees = self.db.query(Employee).all()
        employee_map = {e.id: e.name for e in employees}

        created = 0
        updated = 0
        errors: list[str] = []

        for folder in folders:
            company_code = (folder.company_code or "").strip()
            if not company_code:
                errors.append(f"id={folder.id}: thiếu company_code, bỏ qua")
                continue

            phu_trach = employee_map.get(folder.manager_employee_id) if folder.manager_employee_id else None

            try:
                existing = self.get_by_ma_kh(company_code)

                if existing:
                    # Cập nhật các trường từ folders
                    existing.folder_year     = folder.year
                    existing.folder_template = folder.template or None
                    existing.folder_status   = folder.status or None
                    existing.drive_folder_id = folder.root_folder_id or existing.drive_folder_id
                    if phu_trach:
                        existing.phu_trach_hien_tai = phu_trach
                    existing.updated_at = datetime.now()
                    updated += 1
                else:
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
                    created += 1

                self.db.flush()
            except Exception as e:
                self.db.rollback()
                errors.append(f"{company_code}: {str(e)}")

        self.db.commit()
        return SeedResult(
            total_folders=len(folders),
            created=created,
            updated=updated,
            errors=errors,
        )

    # ------------------------------------------------------------------
    # BULK IMPORT - Nhập dữ liệu công ty từ danh sách
    # ------------------------------------------------------------------

    def bulk_import_tax_companies(self, companies_data: list) -> dict:
        """
        Nhập hoặc cập nhật danh sách công ty thuế điện tử.

        Args:
            companies_data: Danh sách dict với các trường:
                - ma_to_chuc hoặc ma_kh: Mã tổ chức (bắt buộc)
                - ten_to_chuc hoặc ten_cong_ty: Tên tổ chức (bắt buộc)
                - ma_so_thue: Mã số thuế (tùy chọn)
                - nguoi_phu_trach hoặc phu_trach_hien_tai: Người phụ trách (tùy chọn)

        Returns:
            Dict với counts: {'created': X, 'updated': Y, 'errors': Z, 'error_details': [...]}
        """
        result = {
            'created': 0,
            'updated': 0,
            'errors': 0,
            'error_details': []
        }

        for idx, company_data in enumerate(companies_data, 1):
            try:
                # Extract fields với nhiều tên khác nhau
                ma_kh = company_data.get('ma_to_chuc') or company_data.get('ma_kh')
                ten_cong_ty = company_data.get('ten_to_chuc') or company_data.get('ten_cong_ty')
                ma_so_thue = company_data.get('ma_so_thue')
                phu_trach = company_data.get('nguoi_phu_trach') or company_data.get('phu_trach_hien_tai')

                # Validate bắt buộc
                if not ma_kh or not ma_kh.strip():
                    result['errors'] += 1
                    result['error_details'].append(f"Row {idx}: Thiếu mã tổ chức (ma_to_chuc/ma_kh)")
                    continue

                if not ten_cong_ty or not ten_cong_ty.strip():
                    result['errors'] += 1
                    result['error_details'].append(f"Row {idx} ({ma_kh}): Thiếu tên tổ chức")
                    continue

                ma_kh = ma_kh.strip()
                ten_cong_ty = ten_cong_ty.strip()
                ma_so_thue = ma_so_thue.strip() if ma_so_thue else None

                # Kiểm tra công ty đã tồn tại
                existing = self.get_by_ma_kh(ma_kh)

                if existing:
                    # Cập nhật công ty hiện tại
                    existing.ten_cong_ty = ten_cong_ty
                    if ma_so_thue:
                        existing.ma_so_thue = ma_so_thue
                    if phu_trach and phu_trach.strip():
                        existing.phu_trach_hien_tai = phu_trach.strip()
                    existing.updated_at = datetime.now()
                    result['updated'] += 1
                else:
                    # Tạo công ty mới
                    now = datetime.now()
                    company = CompanyInfo(
                        ma_kh=ma_kh,
                        ten_cong_ty=ten_cong_ty,
                        ma_so_thue=ma_so_thue,
                        phu_trach_hien_tai=phu_trach.strip() if phu_trach else None,
                        created_at=now,
                        updated_at=now
                    )
                    self.db.add(company)
                    result['created'] += 1

                self.db.flush()

            except Exception as e:
                self.db.rollback()
                result['errors'] += 1
                result['error_details'].append(f"Row {idx}: {str(e)}")

        self.db.commit()
        return result
