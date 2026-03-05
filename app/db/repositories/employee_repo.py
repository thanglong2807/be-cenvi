from datetime import datetime
from app.db.json_db import JsonDB

class EmployeeRepository:
    def __init__(self):
        self.db = JsonDB("app/data/employees.json")

    def get_all(self):
        return self.db.all()

    def get_by_id(self, employee_id: int):
        return self.db.find_by("id", employee_id)

    def get_by_email(self, email: str):
        return self.db.find_by("email", email)

    def create(self, payload: dict):
        now = datetime.utcnow().isoformat()

        payload.update({
            "created_at": now,
            "updated_at": now
        })

        return self.db.insert(payload)

    def update(self, employee_id: int, payload: dict):
        data = self.db._read()

        for item in data["items"]:
            if item["id"] == employee_id:
                item.update(payload)
                item["updated_at"] = datetime.utcnow().isoformat()
                self.db._write(data)
                return item

        return None
