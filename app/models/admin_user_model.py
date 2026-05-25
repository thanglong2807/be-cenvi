from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class AdminUser(Base):
    __tablename__ = "admin_users"

    id           = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username     = Column(String(100), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=True)
    email        = Column(String(255), nullable=True, unique=True)
    role         = Column(String(50), nullable=False, default="ADMIN")
    is_active    = Column(Boolean, default=True)
    created_at   = Column(DateTime, default=lambda: datetime.now())
    updated_at   = Column(DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())
