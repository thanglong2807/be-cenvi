from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from app.core.database import Base
from datetime import datetime

class AuditSession(Base):
    __tablename__ = "audit_sessions"

    id = Column(Integer, primary_key=True, index=True)
    folder_id = Column(Integer, index=True) # ID của folder trong DB cũ của bạn
    category = Column(String) # GTGT, KE-TOAN, LUONG...
    period = Column(String)   # Q1, Q2, T01...
    year = Column(Integer)
    status = Column(String, default="pending") # pending, approved, rejected
    
    # Đây là nơi lưu toàn bộ checklist và kết quả robot
    # Cấu trúc: [{"task": "...", "status": "pass/fail", "note": "..."}]
    checklist_data = Column(JSON) 
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)