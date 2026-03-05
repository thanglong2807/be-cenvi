# app/schemas/work_link_schema.py

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Schema cho tạo mới
class WorkLinkCreate(BaseModel):
    title: str
    des: Optional[str] = None

# Schema cho cập nhật
class WorkLinkUpdate(BaseModel):
    title: Optional[str] = None
    des: Optional[str] = None

# Schema cho response
class WorkLinkResponse(BaseModel):
    id: int
    title: str
    des: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
