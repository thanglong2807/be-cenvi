from fastapi import APIRouter, HTTPException
from app.schemas.employee_schema import (
    EmployeeCreate,
    EmployeeUpdate,
)
from app.services.employee_service import (
    list_employees,
    get_employee,
    create_employee,
    update_employee,
)

router = APIRouter(
    prefix="/employees",
    tags=["Employees"]
)


@router.get("")
def get_employees():
    return {
        "items": list_employees()
    }


@router.get("/{employee_id}")
def get_employee_detail(employee_id: int):
    data = get_employee(employee_id)
    if not data:
        raise HTTPException(status_code=404, detail="Employee not found")
    return data


@router.post("")
def create(payload: EmployeeCreate):
    try:
        return create_employee(payload.dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{employee_id}")
def update(employee_id: int, payload: EmployeeUpdate):
    try:
        return update_employee(
            employee_id,
            {k: v for k, v in payload.dict().items() if v is not None}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
