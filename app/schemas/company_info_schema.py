# app/schemas/company_info_schema.py

from pydantic import BaseModel, computed_field
from typing import Optional
from datetime import datetime


# ---------------------------------------------------------------------------
# Create schema
# ---------------------------------------------------------------------------

class CompanyInfoCreate(BaseModel):
    # THÔNG TIN KHÁCH HÀNG DÙNG DỊCH VỤ KẾ TOÁN THUẾ (bắt buộc)
    ma_kh: str
    ten_cong_ty: str
    phu_trach_hien_tai: str

    # THÔNG TIN TỔNG QUAN
    ma_so_thue: Optional[str] = None
    nguoi_lien_he_va_chuc_vu: Optional[str] = None
    so_dien_thoai: Optional[str] = None
    email_lien_he: Optional[str] = None
    thong_tin_khac: Optional[str] = None

    # LIÊN KẾT DRIVE
    drive_folder_id: Optional[str] = None
    folder_year: Optional[int] = None
    folder_template: Optional[str] = None
    folder_status: Optional[str] = None

    # TOKEN
    cenvi_cam_token: Optional[bool] = False
    token_mat_khau: Optional[str] = None
    token_ngay: Optional[datetime] = None

    # TÀI KHOẢN THUẾ ĐIỆN TỬ
    thue_dt_tai_khoan: Optional[str] = None
    thue_dt_mat_khau: Optional[str] = None

    # TÀI KHOẢN HÓA ĐƠN ĐIỆN TỬ
    hddt_tai_khoan: Optional[str] = None
    hddt_mat_khau: Optional[str] = None

    # TÀI KHOẢN XUẤT HÓA ĐƠN
    xuat_hd_link: Optional[str] = None
    xuat_hd_tai_khoan: Optional[str] = None
    xuat_hd_mat_khau: Optional[str] = None

    # TÀI KHOẢN BẢO HIỂM XÃ HỘI ĐIỆN TỬ
    bhxh_link: Optional[str] = None
    bhxh_ma_so: Optional[str] = None
    bhxh_tai_khoan: Optional[str] = None
    bhxh_mat_khau: Optional[str] = None

    # PHẦN MỀM KẾ TOÁN
    pmkt_ten: Optional[str] = None
    pmkt_link: Optional[str] = None
    pmkt_tai_khoan: Optional[str] = None
    pmkt_mat_khau: Optional[str] = None

    # HỢP ĐỒNG
    hop_dong_link: Optional[str] = None
    hop_dong_ngay_ky: Optional[datetime] = None
    hop_dong_loai_kh: Optional[str] = None
    hop_dong_thanh_toan: Optional[str] = None


# ---------------------------------------------------------------------------
# Update schema  (tất cả Optional để hỗ trợ partial update)
# ---------------------------------------------------------------------------

class CompanyInfoUpdate(BaseModel):
    # THÔNG TIN KHÁCH HÀNG DÙNG DỊCH VỤ KẾ TOÁN THUẾ
    ma_kh: Optional[str] = None
    ten_cong_ty: Optional[str] = None
    phu_trach_hien_tai: Optional[str] = None

    # THÔNG TIN TỔNG QUAN
    ma_so_thue: Optional[str] = None
    nguoi_lien_he_va_chuc_vu: Optional[str] = None
    so_dien_thoai: Optional[str] = None
    email_lien_he: Optional[str] = None
    thong_tin_khac: Optional[str] = None

    # LIÊN KẾT DRIVE
    drive_folder_id: Optional[str] = None
    folder_year: Optional[int] = None
    folder_template: Optional[str] = None
    folder_status: Optional[str] = None

    # TOKEN
    cenvi_cam_token: Optional[bool] = None
    token_mat_khau: Optional[str] = None
    token_ngay: Optional[datetime] = None

    # TÀI KHOẢN THUẾ ĐIỆN TỬ
    thue_dt_tai_khoan: Optional[str] = None
    thue_dt_mat_khau: Optional[str] = None

    # TÀI KHOẢN HÓA ĐƠN ĐIỆN TỬ
    hddt_tai_khoan: Optional[str] = None
    hddt_mat_khau: Optional[str] = None

    # TÀI KHOẢN XUẤT HÓA ĐƠN
    xuat_hd_link: Optional[str] = None
    xuat_hd_tai_khoan: Optional[str] = None
    xuat_hd_mat_khau: Optional[str] = None

    # TÀI KHOẢN BẢO HIỂM XÃ HỘI ĐIỆN TỬ
    bhxh_link: Optional[str] = None
    bhxh_ma_so: Optional[str] = None
    bhxh_tai_khoan: Optional[str] = None
    bhxh_mat_khau: Optional[str] = None

    # PHẦN MỀM KẾ TOÁN
    pmkt_ten: Optional[str] = None
    pmkt_link: Optional[str] = None
    pmkt_tai_khoan: Optional[str] = None
    pmkt_mat_khau: Optional[str] = None

    # HỢP ĐỒNG
    hop_dong_link: Optional[str] = None
    hop_dong_ngay_ky: Optional[datetime] = None
    hop_dong_loai_kh: Optional[str] = None
    hop_dong_thanh_toan: Optional[str] = None


# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------

class CompanyInfoResponse(BaseModel):
    id: int

    # THÔNG TIN KHÁCH HÀNG DÙNG DỊCH VỤ KẾ TOÁN THUẾ
    ma_kh: str
    ten_cong_ty: str
    phu_trach_hien_tai: Optional[str] = None

    # THÔNG TIN TỔNG QUAN
    ma_so_thue: Optional[str] = None
    nguoi_lien_he_va_chuc_vu: Optional[str] = None
    so_dien_thoai: Optional[str] = None
    email_lien_he: Optional[str] = None
    thong_tin_khac: Optional[str] = None

    # LIÊN KẾT DRIVE
    drive_folder_id: Optional[str] = None
    drive_folder_link: Optional[str] = None
    folder_year: Optional[int] = None
    folder_template: Optional[str] = None
    folder_status: Optional[str] = None

    # TOKEN
    cenvi_cam_token: bool
    token_mat_khau: Optional[str] = None
    token_ngay: Optional[datetime] = None

    # TÀI KHOẢN THUẾ ĐIỆN TỬ
    thue_dt_tai_khoan: Optional[str] = None
    thue_dt_mat_khau: Optional[str] = None

    # TÀI KHOẢN HÓA ĐƠN ĐIỆN TỬ
    hddt_tai_khoan: Optional[str] = None
    hddt_mat_khau: Optional[str] = None

    # TÀI KHOẢN XUẤT HÓA ĐƠN
    xuat_hd_link: Optional[str] = None
    xuat_hd_tai_khoan: Optional[str] = None
    xuat_hd_mat_khau: Optional[str] = None

    # TÀI KHOẢN BẢO HIỂM XÃ HỘI ĐIỆN TỬ
    bhxh_link: Optional[str] = None
    bhxh_ma_so: Optional[str] = None
    bhxh_tai_khoan: Optional[str] = None
    bhxh_mat_khau: Optional[str] = None

    # PHẦN MỀM KẾ TOÁN
    pmkt_ten: Optional[str] = None
    pmkt_link: Optional[str] = None
    pmkt_tai_khoan: Optional[str] = None
    pmkt_mat_khau: Optional[str] = None

    # HỢP ĐỒNG
    hop_dong_link: Optional[str] = None
    hop_dong_ngay_ky: Optional[datetime] = None
    hop_dong_loai_kh: Optional[str] = None
    hop_dong_thanh_toan: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}


# ---------------------------------------------------------------------------
# List-item schema
# ---------------------------------------------------------------------------

class CompanyInfoListItem(BaseModel):
    id: int
    ma_kh: str
    ten_cong_ty: str
    ma_so_thue: Optional[str] = None
    phu_trach_hien_tai: Optional[str] = None
    so_dien_thoai: Optional[str] = None
    email_lien_he: Optional[str] = None
    hop_dong_loai_kh: Optional[str] = None
    drive_folder_id: Optional[str] = None
    drive_folder_link: Optional[str] = None
    folder_year: Optional[int] = None
    folder_template: Optional[str] = None
    folder_status: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}


# ---------------------------------------------------------------------------
# Seed result schema
# ---------------------------------------------------------------------------

class SeedResult(BaseModel):
    total_folders: int
    created: int
    skipped: int
    errors: list[str]
