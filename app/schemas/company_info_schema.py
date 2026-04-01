# app/schemas/company_info_schema.py

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# ---------------------------------------------------------------------------
# Sub-schemas (nhóm trường) – dùng trong Create / Update / Response
# ---------------------------------------------------------------------------

class ThongTinKhachHang(BaseModel):
    ma_kh: Optional[str] = None
    ten_cong_ty: str
    phu_trach_hien_tai: Optional[str] = None


class ThongTinTongQuan(BaseModel):
    ma_so_thue: Optional[str] = None
    nguoi_lien_he_va_chuc_vu: Optional[str] = None
    so_dien_thoai: Optional[str] = None
    email_lien_he: Optional[str] = None
    thong_tin_khac: Optional[str] = None


class Token(BaseModel):
    cenvi_cam_token: Optional[bool] = False
    token_mat_khau: Optional[str] = None
    token_ngay: Optional[datetime] = None


class TaiKhoanThuedt(BaseModel):
    thue_dt_tai_khoan: Optional[str] = None
    thue_dt_mat_khau: Optional[str] = None


class TaiKhoanHddt(BaseModel):
    hddt_tai_khoan: Optional[str] = None
    hddt_mat_khau: Optional[str] = None


class TaiKhoanXuatHd(BaseModel):
    xuat_hd_link: Optional[str] = None
    xuat_hd_tai_khoan: Optional[str] = None
    xuat_hd_mat_khau: Optional[str] = None


class TaiKhoanBhxh(BaseModel):
    bhxh_link: Optional[str] = None
    bhxh_ma_so: Optional[str] = None
    bhxh_tai_khoan: Optional[str] = None
    bhxh_mat_khau: Optional[str] = None


class PhanMemKeToan(BaseModel):
    pmkt_ten: Optional[str] = None
    pmkt_link: Optional[str] = None
    pmkt_tai_khoan: Optional[str] = None
    pmkt_mat_khau: Optional[str] = None


class HopDong(BaseModel):
    hop_dong_link: Optional[str] = None
    hop_dong_ngay_ky: Optional[datetime] = None
    hop_dong_loai_kh: Optional[str] = None
    hop_dong_thanh_toan: Optional[str] = None


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
# Response schema  – trả về dữ liệu theo nhóm cho frontend dễ dùng
# ---------------------------------------------------------------------------

class CompanyInfoResponse(BaseModel):
    id: int

    # THÔNG TIN KHÁCH HÀNG DÙNG DỊCH VỤ KẾ TOÁN THUẾ
    ma_kh: str
    ten_cong_ty: str
    phu_trach_hien_tai: str

    # THÔNG TIN TỔNG QUAN
    ma_so_thue: Optional[str] = None
    nguoi_lien_he_va_chuc_vu: Optional[str] = None
    so_dien_thoai: Optional[str] = None
    email_lien_he: Optional[str] = None
    thong_tin_khac: Optional[str] = None

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
# List-item schema (trả về danh sách gọn hơn)
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
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}
