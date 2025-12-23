from fastapi import APIRouter, HTTPException

# Import thêm FolderUpdate (Schema dùng cho việc sửa)
from app.schemas.folder_schema import FolderCreate, FolderUpdate 
from app.services.folder_service import (
    list_folders,
    get_folder,
    get_folders_by_employee,
    create_folder,
    update_folder, # <--- Import hàm sửa
    delete_folder  # <--- Import hàm xóa
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
    - Lưu dữ liệu vào DB
    - Tạo folder trên Google Drive
    - Áp template
    """
    try:
        return create_folder(payload.dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{folder_id}")
def update(folder_id: int, payload: FolderUpdate):
    """
    Cập nhật thông tin folder:
    - Update DB
    - Tự động đổi tên trên Google Drive nếu Mã/Tên/MST thay đổi
    """
    try:
        # exclude_unset=True giúp chỉ update những trường người dùng gửi lên
        return update_folder(folder_id, payload.dict(exclude_unset=True))
    except ValueError as e:
        # Trả về 404 nếu không tìm thấy ID, hoặc 400 nếu lỗi logic
        status = 404 if "Không tìm thấy" in str(e) else 400
        raise HTTPException(status_code=status, detail=str(e))


@router.delete("/{folder_id}")
def delete(folder_id: int):
    """
    Xóa folder:
    - Xóa khỏi DB
    - Chuyển folder trên Google Drive vào thùng rác (Trash)
    """
    try:
        return delete_folder(folder_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))