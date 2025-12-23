from datetime import datetime
from app.db.json_db import JsonDB

class FolderRepository:
    def __init__(self):
        # Bạn đang dùng JsonDB wrapper, nên biến là self.db
        self.db = JsonDB("app/data/folders.json")

    def get_all(self):
        return self.db.all()

    def get_by_id(self, folder_id: int):
        return self.db.find_by("id", folder_id)

    def get_by_employee(self, employee_id: int):
        return [
            f for f in self.db.all()
            if f["manager_employee_id"] == employee_id
        ]

    def create(self, payload: dict):
        now = datetime.utcnow().isoformat()
        payload.update({
            "created_at": now,
            "updated_at": now,
            "status": "active",
            "root_folder_id": None
        })
        return self.db.insert(payload)

    def update(self, folder_id: int, data: dict):
        # Đọc dữ liệu thô từ JsonDB
        db_data = self.db._read()

        for item in db_data["items"]:
            if item["id"] == folder_id:
                item.update(data)
                item["updated_at"] = datetime.utcnow().isoformat()
                # Lưu lại
                self.db._write(db_data)
                return item

        return None

    # === HÀM DELETE ĐÃ SỬA LỖI ===
    def delete(self, folder_id: int) -> bool:
        """
        Xóa folder dựa trên cơ chế của JsonDB
        """
        # 1. Đọc dữ liệu thô (giống hàm update)
        db_data = self.db._read()
        items = db_data.get("items", [])
        
        initial_count = len(items)

        # 2. Tạo danh sách mới loại bỏ item cần xóa
        # (Giữ lại các item có id KHÁC folder_id)
        new_items = [item for item in items if item["id"] != folder_id]

        # 3. Kiểm tra xem có item nào bị xóa không
        if len(new_items) == initial_count:
            # Độ dài không đổi nghĩa là không tìm thấy ID này
            return False

        # 4. Cập nhật lại danh sách items và ghi xuống file
        db_data["items"] = new_items
        self.db._write(db_data)
        
        return True