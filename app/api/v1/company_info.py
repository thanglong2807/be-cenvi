# app/api/v1/company_info.py

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.company_info_schema import (
    CompanyInfoCreate,
    CompanyInfoListItem,
    CompanyInfoResponse,
    CompanyInfoUpdate,
)
from app.services.company_info_service import CompanyInfoService

router = APIRouter(prefix="/company-info", tags=["Company Info"])


def get_service(db: Session = Depends(get_db)) -> CompanyInfoService:
    return CompanyInfoService(db)


# ---------------------------------------------------------------------------
# GET /company-info  – danh sách (có tìm kiếm)
# ---------------------------------------------------------------------------
@router.get("", response_model=List[CompanyInfoListItem])
def list_companies(
    keyword: Optional[str] = Query(None, description="Tìm theo tên công ty, mã KH, MST, phụ trách"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: CompanyInfoService = Depends(get_service),
):
    if keyword:
        return service.search(keyword, skip=skip, limit=limit)
    return service.get_all(skip=skip, limit=limit)


# ---------------------------------------------------------------------------
# GET /company-info/{id}  – chi tiết
# ---------------------------------------------------------------------------
@router.get("/{company_id}", response_model=CompanyInfoResponse)
def get_company(
    company_id: int,
    service: CompanyInfoService = Depends(get_service),
):
    return service.get_by_id(company_id)


# ---------------------------------------------------------------------------
# POST /company-info  – tạo mới
# ---------------------------------------------------------------------------
@router.post("", response_model=CompanyInfoResponse, status_code=status.HTTP_201_CREATED)
def create_company(
    data: CompanyInfoCreate,
    service: CompanyInfoService = Depends(get_service),
):
    return service.create(data)


# ---------------------------------------------------------------------------
# PUT /company-info/{id}  – cập nhật (partial update)
# ---------------------------------------------------------------------------
@router.put("/{company_id}", response_model=CompanyInfoResponse)
def update_company(
    company_id: int,
    data: CompanyInfoUpdate,
    service: CompanyInfoService = Depends(get_service),
):
    return service.update(company_id, data)


# ---------------------------------------------------------------------------
# DELETE /company-info/{id}
# ---------------------------------------------------------------------------
@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(
    company_id: int,
    service: CompanyInfoService = Depends(get_service),
):
    service.delete(company_id)
    return None
