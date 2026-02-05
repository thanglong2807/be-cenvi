# app/models/work_link_model.py

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class WorkLink(Base):
    __tablename__ = "WORK_LINKS"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)  # Tiêu đề link công việc
    des = Column(String(1000), nullable=True)  # Mô tả chi tiết
    created_at = Column(DateTime, default=lambda: datetime.now())
    updated_at = Column(DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())
