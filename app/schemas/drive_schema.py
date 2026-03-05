# app/schemas/drive_schema.py
from pydantic import BaseModel
from typing import List, Optional

class DriveItem(BaseModel):
    id: int
    company_code: str
    company_name: str
    mst: str
    manager_employee_id: int
    root_folder_id: str
    year: int
    status: str
    created_at: str
    updated_at: str
    template: str

class SyncResponse(BaseModel):
    last_id: int
    items: List[DriveItem]