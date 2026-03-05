# app/api/v1/work_links.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.services.work_link_service import WorkLinkService
from app.schemas.work_link_schema import (
    WorkLinkCreate,
    WorkLinkUpdate,
    WorkLinkResponse
)

router = APIRouter(prefix="/work-links", tags=["Work Links"])

def get_work_link_service(db: Session = Depends(get_db)):
    return WorkLinkService(db)

# ==================== CRUD ENDPOINTS ====================

@router.get("", response_model=List[WorkLinkResponse], summary="Lấy tất cả link công việc")
def get_all_work_links(service: WorkLinkService = Depends(get_work_link_service)):
    """
    Lấy danh sách tất cả các link công việc, sắp xếp theo thời gian tạo mới nhất
    """
    return service.get_all()

@router.get("/{link_id}", response_model=WorkLinkResponse, summary="Lấy chi tiết link công việc")
def get_work_link(link_id: int, service: WorkLinkService = Depends(get_work_link_service)):
    """
    Lấy thông tin chi tiết của một link công việc theo ID
    """
    return service.get_by_id(link_id)

@router.post("", response_model=WorkLinkResponse, status_code=201, summary="Tạo link công việc mới")
def create_work_link(data: WorkLinkCreate, service: WorkLinkService = Depends(get_work_link_service)):
    """
    Tạo mới một link công việc
    
    **Body:**
    - title: Tiêu đề link công việc (bắt buộc)
    - des: Mô tả chi tiết (tùy chọn)
    """
    return service.create(data)

@router.put("/{link_id}", response_model=WorkLinkResponse, summary="Cập nhật link công việc")
def update_work_link(
    link_id: int,
    data: WorkLinkUpdate,
    service: WorkLinkService = Depends(get_work_link_service)
):
    """
    Cập nhật thông tin link công việc
    
    **Body:**
    - title: Tiêu đề mới (tùy chọn)
    - des: Mô tả mới (tùy chọn)
    """
    return service.update(link_id, data)

@router.delete("/{link_id}", status_code=204, summary="Xóa link công việc")
def delete_work_link(link_id: int, service: WorkLinkService = Depends(get_work_link_service)):
    """
    Xóa một link công việc theo ID
    """
    service.delete(link_id)
    return None
