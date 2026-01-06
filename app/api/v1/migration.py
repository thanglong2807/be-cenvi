from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
# Import các hàm xử lý từ service
from app.services.folder_service import check_migration_status, execute_migration_step

router = APIRouter(prefix="/migration", tags=["Migration Tool"])

# Model cho API check
class CheckPayload(BaseModel):
    company_code: str
    mst: str
    company_name: str
    manager_name: str

# Model cho API execute
class ExecutePayload(BaseModel):
    folder_id: int
    action: str
    new_data: dict = {}

@router.post("/check")
def check_item(payload: CheckPayload):
    # Gọi hàm check bên service
    return check_migration_status(
        payload.company_code, 
        payload.mst, 
        payload.company_name, 
        payload.manager_name
    )

@router.post("/execute")
def execute_item(payload: ExecutePayload):
    try:
        # Gọi hàm execute bên service
        msg = execute_migration_step(payload.folder_id, payload.action, payload.new_data)
        return {"status": "success", "message": msg}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))