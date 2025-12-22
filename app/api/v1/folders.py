from fastapi import APIRouter, HTTPException

from app.schemas.folder_schema import FolderCreate
from app.services.folder_service import (
    list_folders,
    get_folder,
    get_folders_by_employee,
    create_folder
)

router = APIRouter(
    prefix="/folders",
    tags=["Folders"]
)


@router.get("")
def get_all():
    return {
        "items": list_folders()
    }


@router.get("/{folder_id}")
def detail(folder_id: int):
    data = get_folder(folder_id)
    if not data:
        raise HTTPException(status_code=404, detail="Folder not found")
    return data


@router.get("/by-employee/{employee_id}")
def by_employee(employee_id: int):
    return {
        "items": get_folders_by_employee(employee_id)
    }


@router.post("")
def create(payload: FolderCreate):
    """
    Tạo folder công ty:
    - Lưu dữ liệu
    - Tạo folder Google Drive
    - Áp template
    - Lưu root_folder_id
    """
    try:
        return create_folder(payload.dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
