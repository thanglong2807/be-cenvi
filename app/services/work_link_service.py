# app/services/work_link_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import List
from datetime import datetime

from app.models.work_link_model import WorkLink
from app.schemas.work_link_schema import WorkLinkCreate, WorkLinkUpdate

class WorkLinkService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self) -> List[WorkLink]:
        """Lấy tất cả link công việc"""
        return self.db.query(WorkLink).order_by(WorkLink.created_at.desc()).all()
    
    def get_by_id(self, link_id: int) -> WorkLink:
        """Lấy link công việc theo ID"""
        link = self.db.query(WorkLink).filter(WorkLink.id == link_id).first()
        if not link:
            raise HTTPException(status_code=404, detail="Link công việc không tồn tại")
        return link
    
    def create(self, data: WorkLinkCreate) -> WorkLink:
        """Tạo link công việc mới"""
        new_link = WorkLink(
            title=data.title,
            des=data.des,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.db.add(new_link)
        self.db.commit()
        self.db.refresh(new_link)
        return new_link
    
    def update(self, link_id: int, data: WorkLinkUpdate) -> WorkLink:
        """Cập nhật link công việc"""
        link = self.get_by_id(link_id)
        
        if data.title is not None:
            link.title = data.title
        if data.des is not None:
            link.des = data.des
        
        link.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(link)
        return link
    
    def delete(self, link_id: int) -> dict:
        """Xóa link công việc"""
        link = self.get_by_id(link_id)
        self.db.delete(link)
        self.db.commit()
        return {"message": "Đã xóa link công việc thành công"}
