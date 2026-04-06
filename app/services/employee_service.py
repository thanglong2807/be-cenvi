# app/services/employee_service.py

import json
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.employee_model import Employee
from app.schemas.employee_schema import EmployeeCreate, EmployeeUpdate, SeedEmployeeResult

EMPLOYEES_JSON = "app/data/employees.json"


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
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, employee_id: int, data: EmployeeUpdate) -> Employee:
        obj = self._get_or_404(employee_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        obj.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(obj)
        return obj

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
