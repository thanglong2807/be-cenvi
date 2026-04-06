# app/models/folder_model.py

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Folder(Base):
    __tablename__ = "folders"

    id                  = Column(Integer, primary_key=True, index=True)
    company_code        = Column(String(100), nullable=True, index=True)
    company_name        = Column(String(500), nullable=True)
    mst                 = Column(String(50), nullable=True, index=True)
    manager_employee_id = Column(Integer, nullable=True)
    year                = Column(Integer, nullable=True)
    template            = Column(String(50), nullable=True)
    status              = Column(String(50), nullable=True)
    root_folder_id      = Column(String(200), nullable=True)
    created_at          = Column(DateTime, nullable=True)
    updated_at          = Column(DateTime, nullable=True)
