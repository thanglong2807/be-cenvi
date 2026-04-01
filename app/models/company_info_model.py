# app/models/company_info_model.py

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class CompanyInfo(Base):
    __tablename__ = "COMPANY_INFO"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # THÔNG TIN KHÁCH HÀNG DÙNG DỊCH VỤ KẾ TOÁN THUẾ
    # ma_kh khớp với company_code trong folders.json
    ma_kh = Column(String(50), nullable=False, unique=True, index=True)  # Mã KH = company_code
    ten_cong_ty = Column(String(500), nullable=False)                     # Tên công ty
    phu_trach_hien_tai = Column(String(200), nullable=True)               # Tên nhân viên phụ trách

    # THÔNG TIN TỔNG QUAN
    # ma_so_thue khớp với mst trong folders.json
    ma_so_thue = Column(String(50), nullable=True, index=True)            # MST = mst
    nguoi_lien_he_va_chuc_vu = Column(String(300), nullable=True)
    so_dien_thoai = Column(String(50), nullable=True)
    email_lien_he = Column(String(200), nullable=True)
    thong_tin_khac = Column(Text, nullable=True)

    # LIÊN KẾT DRIVE (từ folders.json)
    drive_folder_id = Column(String(200), nullable=True)                  # root_folder_id
    folder_year = Column(Integer, nullable=True)                          # year
    folder_template = Column(String(50), nullable=True)                   # template
    folder_status = Column(String(50), nullable=True)                     # status (active/inactive)

    # TOKEN
    cenvi_cam_token = Column(Boolean, default=False, nullable=False)
    token_mat_khau = Column(String(500), nullable=True)
    token_ngay = Column(DateTime, nullable=True)

    # TÀI KHOẢN THUẾ ĐIỆN TỬ
    thue_dt_tai_khoan = Column(String(200), nullable=True)
    thue_dt_mat_khau = Column(String(500), nullable=True)

    # TÀI KHOẢN HÓA ĐƠN ĐIỆN TỬ
    hddt_tai_khoan = Column(String(200), nullable=True)
    hddt_mat_khau = Column(String(500), nullable=True)

    # TÀI KHOẢN XUẤT HÓA ĐƠN
    xuat_hd_link = Column(String(500), nullable=True)
    xuat_hd_tai_khoan = Column(String(200), nullable=True)
    xuat_hd_mat_khau = Column(String(500), nullable=True)

    # TÀI KHOẢN BẢO HIỂM XÃ HỘI ĐIỆN TỬ
    bhxh_link = Column(String(500), nullable=True)
    bhxh_ma_so = Column(String(100), nullable=True)
    bhxh_tai_khoan = Column(String(200), nullable=True)
    bhxh_mat_khau = Column(String(500), nullable=True)

    # PHẦN MỀM KẾ TOÁN
    pmkt_ten = Column(String(200), nullable=True)
    pmkt_link = Column(String(500), nullable=True)
    pmkt_tai_khoan = Column(String(200), nullable=True)
    pmkt_mat_khau = Column(String(500), nullable=True)

    # HỢP ĐỒNG
    hop_dong_link = Column(String(500), nullable=True)
    hop_dong_ngay_ky = Column(DateTime, nullable=True)
    hop_dong_loai_kh = Column(String(200), nullable=True)
    hop_dong_thanh_toan = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now())
    updated_at = Column(DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())
