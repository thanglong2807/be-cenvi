# app/models/notification_model.py
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class Notification(Base):
    """Thông báo trong app cho nhân viên / reviewer."""
    __tablename__ = "notifications"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    user_id     = Column(Integer, nullable=False, index=True)  # AdminUser.id
    type        = Column(String(50), nullable=False)
    # deadline_warning | task_approved | task_rejected | waiting_review
    title       = Column(String(300), nullable=False)
    body        = Column(Text, nullable=True)
    link        = Column(String(500), nullable=True)   # URL điều hướng khi click
    is_read     = Column(Boolean, default=False, nullable=False)
    created_at  = Column(DateTime, default=lambda: datetime.now())
