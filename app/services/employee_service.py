# app/services/employee_service.py

import json
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.employee_model import Employee
from app.schemas.employee_schema import EmployeeCreate, EmployeeUpdate, SeedEmployeeResult
from app.db.repositories.folder_repo import FolderRepository
from app.services.drive_service import get_drive_service, add_permission, remove_permission_by_email

EMPLOYEES_JSON = "app/data/employees.json"
folder_repo = FolderRepository()


class EmployeeService:
    def __init__(self, db: Session):
        self.db = db

    def _get_or_404(self, employee_id: int) -> Employee:
        obj = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not obj:
            raise HTTPException(status_code=404, detail=f"Không tìm thấy nhân viên id={employee_id}")
        return obj

    def get_by_email(self, email: str) -> Optional[Employee]:
        return self.db.query(Employee).filter(Employee.email == email).first()

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def get_all(self) -> List[Employee]:
        return self.db.query(Employee).order_by(Employee.id).all()

    def get_by_id(self, employee_id: int) -> Employee:
        return self._get_or_404(employee_id)

    def create(self, data: EmployeeCreate) -> Employee:
        if self.get_by_email(data.email):
            raise HTTPException(status_code=409, detail="Email nhân viên đã tồn tại")

        now = datetime.now()
        obj = Employee(**data.model_dump(), created_at=now, updated_at=now)

        # Tạo folder employee trong Google Drive (nếu chưa có)
        if not obj.drive_folder_id:
            try:
                from app.services.employee_folder_service import EmployeeFolderService
                import os

                folder_service = EmployeeFolderService()
                parent_folder_id = os.getenv('EMPLOYEES_ROOT_FOLDER_ID', '0AIxlO0tI8hPBUk9PVA')

                folder_id = folder_service.create_employee_folder(
                    employee_name=obj.name,
                    parent_folder_id=parent_folder_id
                )

                if folder_id:
                    obj.drive_folder_id = folder_id
                    print(f"✅ Tạo Drive folder cho nhân viên '{obj.name}': {folder_id}")

            except Exception as e:
                print(f"⚠️ Lỗi tạo Drive folder cho nhân viên: {e}")

        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, employee_id: int, data: EmployeeUpdate) -> Employee:
        obj = self._get_or_404(employee_id)

        new_email = data.email if hasattr(data, "email") else None
        old_email = obj.email

        # Nếu email thay đổi → cập nhật quyền Drive
        if new_email and new_email != old_email:
            # Kiểm tra email mới chưa được dùng
            if self.get_by_email(new_email):
                raise HTTPException(status_code=409, detail=f"Email '{new_email}' đã được dùng bởi nhân viên khác")
            self._update_drive_permissions(employee_id, old_email, new_email)

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        obj.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def _update_drive_permissions(self, employee_id: int, old_email: str, new_email: str):
        """
        Với mỗi folder do nhân viên phụ trách:
        - Thêm quyền email mới
        - Xóa quyền email cũ
        """
        folders = folder_repo.get_by_employee(employee_id)
        if not folders:
            return

        try:
            drive = get_drive_service()
        except Exception as e:
            # Không có Drive credentials → bỏ qua, chỉ cập nhật DB
            print(f"⚠️ Không kết nối được Drive, bỏ qua cập nhật quyền: {e}")
            return

        for folder in folders:
            folder_id = folder.get("root_folder_id")
            if not folder_id:
                continue
            try:
                add_permission(drive, folder_id, new_email)
                remove_permission_by_email(drive, folder_id, old_email)
                print(f"✅ Folder {folder_id}: cập nhật quyền {old_email} → {new_email}")
            except Exception as e:
                print(f"⚠️ Folder {folder_id}: lỗi cập nhật quyền - {e}")

    def delete(self, employee_id: int) -> None:
        obj = self._get_or_404(employee_id)
        self.db.delete(obj)
        self.db.commit()

    # ------------------------------------------------------------------
    # SEED từ employees.json
    # ------------------------------------------------------------------

    def seed_from_json(self) -> SeedEmployeeResult:
        try:
            with open(EMPLOYEES_JSON, encoding="utf-8") as f:
                data = json.load(f)
            items = data.get("items", []) if isinstance(data, dict) else data
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Không đọc được file JSON: {e}")

        created = 0
        skipped = 0
        errors: list[str] = []

        for emp in items:
            email = emp.get("email", "").strip()
            if not email:
                errors.append(f"id={emp.get('id')}: thiếu email, bỏ qua")
                continue
            if self.get_by_email(email):
                skipped += 1
                continue
            try:
                now = datetime.now()
                obj = Employee(
                    name=emp.get("name") or None,
                    title=emp.get("title") or None,
                    email=email,
                    status=emp.get("status", "active"),
                    created_at=now,
                    updated_at=now,
                )
                self.db.add(obj)
                self.db.flush()
                created += 1
            except Exception as e:
                self.db.rollback()
                errors.append(f"{email}: {str(e)}")

        self.db.commit()
        return SeedEmployeeResult(total=len(items), created=created, skipped=skipped, errors=errors)
