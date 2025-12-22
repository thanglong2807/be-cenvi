from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FolderCreate(BaseModel):
    company_code: str
    company_name: str
    mst: str               # 👈 THÊM
    manager_employee_id: int
    year: int
    template: str = "STANDARD"


class FolderResponse(BaseModel):
    id: int
    company_code: str
    company_name: str
    manager_employee_id: int
    mst:str
    year: int
    template: str
    root_folder_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
