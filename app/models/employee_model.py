# app/models/employee_model.py

from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Employee(Base):
    __tablename__ = "employees"

    id          = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username    = Column(String(100), nullable=True, unique=True)   # tên đăng nhập
    displayname = Column(String(200), nullable=True)                # tên hiển thị (= name trong JSON)
    email       = Column(String(200), nullable=True, unique=True, index=True)
    role_name   = Column(String(100), nullable=True)                # chức vụ (= title trong JSON)
