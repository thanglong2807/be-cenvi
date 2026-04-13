# app/models/employee_model.py

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Employee(Base):
    __tablename__ = "employees"

    id                = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name              = Column(String(255), nullable=True)
    title             = Column(String(255), nullable=True)
    email             = Column(String(255), nullable=True, unique=True, index=True)
    status            = Column(String(50), nullable=True, default="active")
    drive_folder_id   = Column(String(255), nullable=True)  # Google Drive folder ID for employee
    created_at        = Column(DateTime, default=lambda: datetime.now())
    updated_at        = Column(DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())
