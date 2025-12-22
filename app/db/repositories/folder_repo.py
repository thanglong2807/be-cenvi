from datetime import datetime
from app.db.json_db import JsonDB

class FolderRepository:
    def __init__(self):
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

    # 👉 HÀM CÒN THIẾU (QUAN TRỌNG)
    def update(self, folder_id: int, data: dict):
        db_data = self.db._read()

        for item in db_data["items"]:
            if item["id"] == folder_id:
                item.update(data)
                item["updated_at"] = datetime.utcnow().isoformat()
                self.db._write(db_data)
                return item

        return None
