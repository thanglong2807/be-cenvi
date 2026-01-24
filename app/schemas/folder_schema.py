from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FolderCreate(BaseModel):
    company_code: str
    company_name: str
    mst: str
    year: int
    template: str
    manager_employee_id: int
    # === THÊM TRƯỜNG NÀY ===
    status: Optional[str] = "active"


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

class FolderBase(BaseModel):
    company_code: str
    company_name: str
    mst: str
    year: int
    template: str
    manager_employee_id: int



class FolderUpdate(BaseModel):
    # Tất cả để Optional để cho phép sửa từng phần
    company_code: Optional[str] = None
    company_name: Optional[str] = None
    mst: Optional[str] = None
    year: Optional[int] = None
    template: Optional[str] = None
    manager_employee_id: Optional[int] = None
    