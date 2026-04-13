from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class EmployeeCreate(BaseModel):
    name: str
    title: Optional[str] = None
    email: EmailStr
    status: str = "active"
    drive_folder_id: Optional[str] = None  # Google Drive folder ID


class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    email: Optional[EmailStr] = None
    status: Optional[str] = None
    drive_folder_id: Optional[str] = None  # Google Drive folder ID


class EmployeeResponse(BaseModel):
    id: int
    name: Optional[str] = None
    title: Optional[str] = None
    email: Optional[str] = None
    status: Optional[str] = None
    drive_folder_id: Optional[str] = None  # Google Drive folder ID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class EmployeeOption(BaseModel):
    id: int
    name: Optional[str] = None
    title: Optional[str] = None

    class Config:
        from_attributes = True


class SeedEmployeeResult(BaseModel):
    total: int
    created: int
    skipped: int
    errors: list[str]
