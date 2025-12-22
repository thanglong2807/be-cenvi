from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class EmployeeCreate(BaseModel):
    name: str
    title: str
    email: EmailStr
    status: str = "active"


class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    status: Optional[str] = None


class EmployeeResponse(BaseModel):
    id: int
    name: str
    title: str
    email: EmailStr
    status: str
    created_at: datetime
    updated_at: datetime
