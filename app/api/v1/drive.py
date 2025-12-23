from fastapi import APIRouter, HTTPException, Depends
from typing import Any

# Import Service mới (đã đổi tên thành drive_search)
from app.services.drive_search import drive_search_service
# Import Schema trả về
from app.schemas.drive_schema import SyncResponse
from app.services.storage_service import storage_service
router = APIRouter()

@router.get("/sync", response_model=SyncResponse, summary="Quét và đồng bộ dữ liệu từ Google Drive")
async def sync_drive_data() -> Any:
    """
    API thực hiện quy trình quét Google Drive:
    
    1. **Quét Folder**: Lấy danh sách folder con trong Root Folder cấu hình.
    2. **Phân tích tên**: Tách Mã công ty, Tên công ty, MST từ tên folder.
    3. **Xác định Manager**: 
       - Kiểm tra quyền (Permissions) trên Drive.
       - Map Email tìm được với danh sách nhân viên trong `app/data/employees.py`.
    4. **Trả về kết quả**: Dạng JSON chuẩn hóa.
    """
    try:
        # Gọi hàm quét từ service drive_search
        data = drive_search_service.scan_and_parse()
        return data
    
    except Exception as e:
        # In lỗi ra terminal để dễ debug
        print(f"❌ Lỗi API Sync: {str(e)}")
        # Trả về lỗi 500 cho client
        raise HTTPException(
            status_code=500, 
            detail=f"Lỗi hệ thống khi quét Drive: {str(e)}"
        )

@router.get("/employees-check", summary="Kiểm tra danh sách nhân viên (Debug)")
async def check_employees_mapping():
    """
    API phụ để kiểm tra xem hệ thống đã load đúng danh sách nhân viên
    từ file employees.py hay chưa.
    """
    try:
        # Gọi hàm debug từ service (bạn cần thêm hàm này vào service nếu muốn dùng)
        # Hoặc trả về trực tiếp dữ liệu mapping đã xử lý
        return {
            "message": "Danh sách mapping Email -> ID đang sử dụng",
            "mapping_data": drive_search_service.employee_mapping
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. API Xác nhận (Confirm) - Logic Mới
@router.post("/confirm", summary="Bước 2: Xác nhận và lưu dữ liệu vào hệ thống")
async def confirm_update(payload: SyncResponse):
    """
    Nhận dữ liệu JSON (đầu ra của Bước 1) và lưu chính thức vào file `companies_storage.json`.
    
    - **payload**: Toàn bộ cục JSON gồm `last_id` và `items`.
    """
    try:
        # Gọi service để lưu file
        result = storage_service.save_data(payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 3. API Lấy dữ liệu đã lưu (Optional) - Để hiển thị lên web
@router.get("/companies", summary="Lấy danh sách công ty đã lưu")
async def get_saved_companies():
    try:
        return storage_service.load_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))