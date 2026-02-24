# app/models/audit.py
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text
from app.core.database import Base
from datetime import datetime

class AuditSession(Base):
    __tablename__ = "audit_sessions"

    id = Column(Integer, primary_key=True, index=True)
    folder_id = Column(Integer, index=True)
    category = Column(String(50)) # GTGT, TNDN...
    period = Column(String(20))   # Q1, Q2, YEAR...
    year = Column(Integer)
    status = Column(String(20))   # pass, fail, warning
    checklist_data = Column(JSON) # Lưu mảng các task
    overall_note = Column(Text)   # Lời nhắn của sếp
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)