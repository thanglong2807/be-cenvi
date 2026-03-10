from sqlalchemy import Column, Integer, String, DECIMAL, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.sqlite import JSON  # Sử dụng JSON cho SQLite
from datetime import datetime

Base = declarative_base()

class DanhMuc(Base):
    __tablename__ = "DANH_MUC"
    DM_ID = Column(Integer, primary_key=True, index=True)
    Ten_Danh_Muc = Column(String(255), index=True)
    Share_Drive_Folder_ID = Column(String(255))
    Metadata = Column(JSON) # Lưu trữ: ma_mau_hex, icon_code, ngay_tao

    muc_con = relationship("MucCon", back_populates="danh_muc", cascade="all, delete-orphan")

class MucCon(Base):
    __tablename__ = "MUC_CON"
    MC_ID = Column(Integer, primary_key=True, index=True)
    DM_ID = Column(Integer, ForeignKey("DANH_MUC.DM_ID"))
    Ten_Muc_Con = Column(String(255))
    Ngay_Het_Hieu_Luc = Column(DateTime, nullable=True)  # Ngày hết hiệu lực dự án
    
    # >>> THÊM DÒNG NÀY ĐỂ HẾT LỖI <<<
    Share_Drive_Folder_ID = Column(String(255)) 
    Metadata = Column(JSON) # Lưu trữ: ma_mau_hex, icon_code, ngay_tao
    # ================================

    danh_muc = relationship("DanhMuc", back_populates="muc_con")
    tai_lieu = relationship("TaiLieu", back_populates="muc_con", cascade="all, delete-orphan")

class TaiLieu(Base):
    __tablename__ = "TAI_LIEU"
    TL_ID = Column(Integer, primary_key=True, index=True)
    MC_ID = Column(Integer, ForeignKey("MUC_CON.MC_ID"))
    Tieu_De = Column(String(255))
    Ngay_Het_Hieu_Luc = Column(DateTime, nullable=True)  # Ngày hết hiệu lực tài liệu
    
    # ID của phiên bản mới nhất, trỏ đến PHIEN_BAN_TAI_LIEU
    Current_Version_ID = Column(Integer, ForeignKey("PHIEN_BAN_TAI_LIEU.PB_ID")) 
    Metadata = Column(JSON) # Lưu trữ: ma_mau_hex, icon_code, ngay_tao_item

    muc_con = relationship("MucCon", back_populates="tai_lieu")
    versions = relationship("PhienBanTaiLieu", back_populates="tai_lieu", foreign_keys="PhienBanTaiLieu.TL_ID", cascade="all, delete-orphan")
    
    # Relationship ngược để lấy thông tin phiên bản hiện tại
    current_version = relationship("PhienBanTaiLieu", foreign_keys=[Current_Version_ID], post_update=True) 

class PhienBanTaiLieu(Base):
    __tablename__ = "PHIEN_BAN_TAI_LIEU"
    PB_ID = Column(Integer, primary_key=True, index=True)
    TL_ID = Column(Integer, ForeignKey("TAI_LIEU.TL_ID"))
    So_Phien_Ban = Column(DECIMAL(5,2)) # Ví dụ: 1.0, 2.1
    Share_Drive_File_ID = Column(String(255)) # ID File Google Drive
    Ten_File_Tren_Drive = Column(String(255)) # Tên đã đổi kèm phiên bản
    Ngay_Tai_Len = Column(DateTime, default=lambda: datetime.now())  # Tự động lấy thời gian hiện tại

    Metadata = Column(JSON) # Lưu trữ: loai_tap_tin, kich_thuoc, ngay_tai_len, nguoi_tai_len_id

    tai_lieu = relationship("TaiLieu", back_populates="versions", foreign_keys=[TL_ID])

class PhanQuyenTruyCap(Base): 
    __tablename__ = "PHAN_QUYEN_TRUY_CAP"
    PQ_ID = Column(Integer, primary_key=True, index=True)
    TL_ID = Column(Integer, ForeignKey("TAI_LIEU.TL_ID"))
    ND_ID = Column(Integer, index=True) 
    Cap_Do_Truy_Cap = Column(String(20))