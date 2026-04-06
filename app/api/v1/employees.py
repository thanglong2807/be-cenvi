# app/api/v1/employees.py

from typing import List

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.employee_schema import EmployeeCreate, EmployeeUpdate, EmployeeResponse, SeedEmployeeResult
from app.services.employee_service import EmployeeService
from app.services.folder_service import handover_folders

router = APIRouter(prefix="/employees", tags=["Employees"])


def get_service(db: Session = Depends(get_db)) -> EmployeeService:
    return EmployeeService(db)


class HandoverRequest(BaseModel):
    old_employee_id: int
    new_employee_id: int


# ---------------------------------------------------------------------------
# GET /employees
# ---------------------------------------------------------------------------
@router.get("", response_model=List[EmployeeResponse])
def get_employees(service: EmployeeService = Depends(get_service)):
    return service.get_all()


# ---------------------------------------------------------------------------
# GET /employees/{id}
# ---------------------------------------------------------------------------
@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee_detail(employee_id: int, service: EmployeeService = Depends(get_service)):
    return service.get_by_id(employee_id)


# ---------------------------------------------------------------------------
# POST /employees
# ---------------------------------------------------------------------------
@router.post("", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create(payload: EmployeeCreate, service: EmployeeService = Depends(get_service)):
    return service.create(payload)


# ---------------------------------------------------------------------------
# PUT /employees/{id}
# ---------------------------------------------------------------------------
@router.put("/{employee_id}", response_model=EmployeeResponse)
def update(employee_id: int, payload: EmployeeUpdate, service: EmployeeService = Depends(get_service)):
    return service.update(employee_id, payload)


# ---------------------------------------------------------------------------
# DELETE /employees/{id}
# ---------------------------------------------------------------------------
@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(employee_id: int, service: EmployeeService = Depends(get_service)):
    service.delete(employee_id)
    return None


# ---------------------------------------------------------------------------
# POST /employees/seed-from-json
# ---------------------------------------------------------------------------
@router.post("/seed-from-json", response_model=SeedEmployeeResult)
def seed(service: EmployeeService = Depends(get_service)):
    return service.seed_from_json()


# ---------------------------------------------------------------------------
# POST /employees/handover
# ---------------------------------------------------------------------------
@router.post("/handover")
def transfer_employee_rights(payload: HandoverRequest, background_tasks: BackgroundTasks):
    if payload.old_employee_id == payload.new_employee_id:
        raise HTTPException(status_code=400, detail="Người bàn giao và người nhận không được trùng nhau")
    try:
        return handover_folders(payload.old_employee_id, payload.new_employee_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Handover Error: {e}")
        raise HTTPException(status_code=500, detail="Lỗi hệ thống khi bàn giao tài liệu.")
