# app/models/company_info_model.py

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class CompanyInfo(Base):
    __tablename__ = "COMPANY_INFO"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # THÔNG TIN KHÁCH HÀNG DÙNG DỊCH VỤ KẾ TOÁN THUẾ
    ma_kh = Column(String(50), nullable=False, unique=True, index=True)  # Mã KH (bắt buộc)
    ten_cong_ty = Column(String(500), nullable=False)                     # Tên công ty (bắt buộc)
    phu_trach_hien_tai = Column(String(200), nullable=False)              # Phụ trách hiện tại (bắt buộc)

    # THÔNG TIN TỔNG QUAN
    ma_so_thue = Column(String(50), nullable=True, index=True)            # Mã số thuế
    nguoi_lien_he_va_chuc_vu = Column(String(300), nullable=True)         # Người liên hệ và chức vụ
    so_dien_thoai = Column(String(50), nullable=True)                     # Số điện thoại
    email_lien_he = Column(String(200), nullable=True)                    # Email liên hệ
    thong_tin_khac = Column(Text, nullable=True)                          # Thông tin khác

    # TOKEN
    cenvi_cam_token = Column(Boolean, default=False, nullable=False)      # CENVI có cầm token
    token_mat_khau = Column(String(500), nullable=True)                   # Mật khẩu token
    token_ngay = Column(DateTime, nullable=True)                          # Ngày token

    # TÀI KHOẢN THUẾ ĐIỆN TỬ
    thue_dt_tai_khoan = Column(String(200), nullable=True)                # Tài khoản đăng nhập
    thue_dt_mat_khau = Column(String(500), nullable=True)                 # Mật khẩu

    # TÀI KHOẢN HÓA ĐƠN ĐIỆN TỬ
    hddt_tai_khoan = Column(String(200), nullable=True)                   # Tài khoản đăng nhập
    hddt_mat_khau = Column(String(500), nullable=True)                    # Mật khẩu

    # TÀI KHOẢN XUẤT HÓA ĐƠN
    xuat_hd_link = Column(String(500), nullable=True)                     # Link đăng nhập
    xuat_hd_tai_khoan = Column(String(200), nullable=True)                # Tài khoản đăng nhập
    xuat_hd_mat_khau = Column(String(500), nullable=True)                 # Mật khẩu

    # TÀI KHOẢN BẢO HIỂM XÃ HỘI ĐIỆN TỬ
    bhxh_link = Column(String(500), nullable=True)                        # Link đăng nhập
    bhxh_ma_so = Column(String(100), nullable=True)                       # Mã số bảo hiểm
    bhxh_tai_khoan = Column(String(200), nullable=True)                   # Tài khoản đăng nhập
    bhxh_mat_khau = Column(String(500), nullable=True)                    # Mật khẩu

    # PHẦN MỀM KẾ TOÁN
    pmkt_ten = Column(String(200), nullable=True)                         # PMKT đang sử dụng
    pmkt_link = Column(String(500), nullable=True)                        # Link đăng nhập
    pmkt_tai_khoan = Column(String(200), nullable=True)                   # Tài khoản đăng nhập
    pmkt_mat_khau = Column(String(500), nullable=True)                    # Mật khẩu

    # HỢP ĐỒNG
    hop_dong_link = Column(String(500), nullable=True)                    # Link
    hop_dong_ngay_ky = Column(DateTime, nullable=True)                    # Ngày ký gần nhất
    hop_dong_loai_kh = Column(String(200), nullable=True)                 # Loại khách hàng
    hop_dong_thanh_toan = Column(String(500), nullable=True)              # Thanh toán

    created_at = Column(DateTime, default=lambda: datetime.now())
    updated_at = Column(DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())
