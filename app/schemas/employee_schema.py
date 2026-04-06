from pydantic import BaseModel, EmailStr
from typing import Optional


class EmployeeCreate(BaseModel):
    username: Optional[str] = None
    displayname: str
    email: EmailStr
    role_name: Optional[str] = None


class EmployeeUpdate(BaseModel):
    username: Optional[str] = None
    displayname: Optional[str] = None
    role_name: Optional[str] = None


class EmployeeResponse(BaseModel):
    id: int
    username: Optional[str] = None
    displayname: Optional[str] = None
    email: Optional[str] = None
    role_name: Optional[str] = None

    class Config:
        from_attributes = True


class SeedEmployeeResult(BaseModel):
    total: int
    created: int
    skipped: int
    errors: list[str]
