# app/api/v1/employees.py

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

# Import Schemas
from app.schemas.employee_schema import (
    EmployeeCreate,
    EmployeeUpdate,
)

# Import Services
from app.services.employee_service import (
    list_employees,
    get_employee,
    create_employee,
    update_employee,
)
from app.services.folder_service import handover_folders

# ========= KHỞI TẠO ROUTER (CHỈ 1 LẦN DUY NHẤT) =========
router = APIRouter(
    prefix="/employees",
    tags=["Employees"]
)

# ========= SCHEMAS (Nên chuyển sang employee_schema.py nếu có thể) =========
class HandoverRequest(BaseModel):
    old_employee_id: int
    new_employee_id: int


# ========= API ENDPOINTS =========

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
        # Nếu dùng Pydantic v2 nên đổi .dict() thành .model_dump()
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


# ========= API BÀN GIAO (HANDOVER) =========
# URL thực tế sẽ là: POST /api/v1/employees/handover

@router.post("/handover")
def transfer_employee_rights(payload: HandoverRequest, background_tasks: BackgroundTasks):
    """
    API bàn giao công việc:
    - Chuyển quyền Drive từ nhân viên cũ sang mới
    - Tạo shortcut cho nhân viên mới
    - Xóa quyền nhân viên cũ
    """
    if payload.old_employee_id == payload.new_employee_id:
         raise HTTPException(status_code=400, detail="Người bàn giao và người nhận không được trùng nhau")

    try:
        # Gọi service xử lý
        result = handover_folders(payload.old_employee_id, payload.new_employee_id)
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Log lỗi ra console server để debug
        print(f"Handover Error: {e}")
        raise HTTPException(status_code=500, detail="Lỗi hệ thống khi bàn giao tài liệu.")