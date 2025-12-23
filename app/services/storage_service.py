# app/services/storage_service.py
import json
import os
from typing import Dict, Any
from app.core.config import settings
from app.schemas.drive_schema import SyncResponse

class StorageService:
    def __init__(self):
        self.file_path = settings.STORAGE_PATH
        # Tạo thư mục app/data nếu chưa có
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

    def save_data(self, data: SyncResponse) -> Dict[str, Any]:
        """
        Lưu dữ liệu JSON xuống ổ cứng (Ghi đè)
        """
        try:
            # Chuyển đổi Pydantic model thành Dict
            # mode='json' để đảm bảo datetime được serialize đúng
            json_content = data.model_dump(mode='json')
            
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(json_content, f, ensure_ascii=False, indent=2)
                
            return {
                "status": "success",
                "message": f"Đã lưu thành công {len(data.items)} bản ghi.",
                "path": self.file_path
            }
        except Exception as e:
            raise Exception(f"Lỗi khi ghi file: {str(e)}")

    def load_data(self) -> Dict[str, Any]:
        """
        Đọc dữ liệu đã lưu
        """
        if not os.path.exists(self.file_path):
            return {"last_id": 0, "items": []}
            
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"Lỗi khi đọc file: {str(e)}")

storage_service = StorageService()