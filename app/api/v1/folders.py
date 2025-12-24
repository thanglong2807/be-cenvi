from fastapi import APIRouter, HTTPException, Body
from typing import Optional

# Import Schemas
from app.schemas.folder_schema import FolderCreate, FolderUpdate
from app.services.folder_service import (
    list_folders,
    get_folder_full_detail,
    get_folders_by_employee,
    create_folder,
    update_folder,
    delete_folder,
    browse_drive_folder # <--- Đảm bảo đã import hàm này
)

router = APIRouter(
    prefix="/folders",
    tags=["Folders"]
)

# ==================================================================
# 1. API DUYỆT DRIVE (STRING ID) - Đặt lên trên đầu
# ==================================================================

@router.get("/browse/{drive_id}", summary="Xem nội dung folder con (Dùng Drive ID)")
def browse_content(drive_id: str):
    """
    API này nhận vào **Google Drive ID** (chuỗi ký tự).
    Dùng để khi bấm vào folder con (vd: Kế toán, Nhân sự) thì gọi API này để xem file bên trong.
    """
    try:
        items = browse_drive_folder(drive_id)
        return {
            "drive_id": drive_id,
            "total_items": len(items),
            "items": items
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")


# ==================================================================
# 2. API CRUD DATABASE (INTEGER ID)
# ==================================================================

@router.get("", summary="Lấy danh sách folder (DB)")
def get_all():
    return {"items": list_folders()}


@router.get("/{folder_id}", summary="Xem chi tiết folder gốc (Dùng DB ID)")
def detail(folder_id: int):
    """
    API này nhận vào **Database ID** (số nguyên 1, 2, 3...).
    Trả về thông tin chi tiết, quyền hạn và danh sách folder con cấp 1.
    """
    data = get_folder_full_detail(folder_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy folder DB ID {folder_id}")
    return data


@router.get("/by-employee/{employee_id}")
def by_employee(employee_id: int):
    return {"items": get_folders_by_employee(employee_id)}


@router.post("")
def create(payload: FolderCreate):
    try:
        return create_folder(payload.dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{folder_id}")
def update(folder_id: int, payload: FolderUpdate):
    try:
        return update_folder(folder_id, payload.dict(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{folder_id}")
def delete(folder_id: int):
    try:
        delete_folder(folder_id)
        return {"success": True, "message": "Đã xóa thành công"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))