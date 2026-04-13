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
    SeedResult,
    CompanyTaxImportItem,
    BulkImportResult,
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
@router.delete("/{company_id}", status_code=status.HTTP_200_OK)
def delete_company(
    company_id: int,
    delete_drive_folder: bool = Query(True, description="Có xoá folder Google Drive không?"),
    service: CompanyInfoService = Depends(get_service),
):
    """
    Xoá công ty từ database.

    Query params:
    - delete_drive_folder: Có xoá folder Google Drive không? (default: True)
    """
    return service.delete(company_id, delete_drive_folder=delete_drive_folder)


# ---------------------------------------------------------------------------
# POST /company-info/seed-from-folders
# Import toàn bộ công ty từ folders.json vào DB
# ---------------------------------------------------------------------------
@router.post(
    "/seed-from-folders",
    response_model=SeedResult,
    status_code=status.HTTP_200_OK,
    summary="Import công ty từ folders.json vào DB",
)
def seed_from_folders(service: CompanyInfoService = Depends(get_service)):
    return service.seed_from_folders()


# ---------------------------------------------------------------------------
# POST /company-info/bulk-import
# Nhập danh sách công ty thuế điện tử
# ---------------------------------------------------------------------------
@router.post(
    "/bulk-import",
    response_model=BulkImportResult,
    status_code=status.HTTP_200_OK,
    summary="Nhập danh sách công ty thuế điện tử",
)
def bulk_import_companies(
    companies: List[CompanyTaxImportItem],
    service: CompanyInfoService = Depends(get_service),
):
    """
    Nhập danh sách công ty thuế điện tử.

    Mỗi công ty có thể cung cấp:
    - ma_to_chuc hoặc ma_kh: Mã tổ chức (bắt buộc)
    - ten_to_chuc hoặc ten_cong_ty: Tên tổ chức (bắt buộc)
    - ma_so_thue: Mã số thuế (tùy chọn)
    - nguoi_phu_trach hoặc phu_trach_hien_tai: Người phụ trách (tùy chọn)
    """
    companies_data = [c.model_dump() for c in companies]
    return service.bulk_import_tax_companies(companies_data)


# ---------------------------------------------------------------------------
# POST /company-info/{ma_kh}/add-shortcut
# Thêm shortcut công ty vào folder nhân viên
# ---------------------------------------------------------------------------
@router.post(
    "/{ma_kh}/add-shortcut",
    status_code=status.HTTP_200_OK,
    summary="Thêm shortcut công ty vào folder nhân viên",
)
def add_company_shortcut(
    ma_kh: str,
    employee_id: int = Query(..., description="Employee ID"),
    service: CompanyInfoService = Depends(get_service),
):
    """
    Thêm shortcut của công ty vào folder nhân viên.

    - ma_kh: Mã công ty
    - employee_id: ID của nhân viên
    """
    return service.add_shortcut_to_employee_folder(ma_kh, employee_id)
