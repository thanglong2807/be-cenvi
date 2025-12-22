from app.db.json_db import JsonDB

class CompanyRepository:
    def __init__(self):
        self.db = JsonDB("app/data/companies.json")

    def get_all(self):
        return self.db.all()

    def get_by_code(self, code: str):
        return self.db.find_by("code", code)

    def create(self, payload: dict):
        return self.db.insert(payload)
