# app/schemas/document_schema.py

import json
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime

# --- Pydantic Schemas for JSON Metadata ---
class BaseMetadata(BaseModel):
    ma_mau_hex: Optional[str] = '#3498db'
    icon_code: Optional[str] = 'FileText'

class FileMetadata(BaseModel):
    Ten_File_Goc: str
    Loai_Tap_Tin: Optional[str] = None # MIME type
    Kich_Thuoc_Byte: Optional[int] = 0
    Nguoi_Tai_Len_ID: int
    original_link: Optional[str] = None  # Lưu full URL gốc

# --- Schemas for Create/Update ---
class TaiLieuCreate(BaseModel):
    MC_ID: int
    Tieu_De: str
    Ngay_Het_Hieu_Luc: Optional[datetime] = None
    Metadata: BaseMetadata
    # Không cần version data ở đây, sẽ truyền riêng

class FileUploadBase(BaseModel):
    ten_file_goc: str
    kich_thuoc_byte: int

# ĐƯỢC DÙNG KHI TẠO MỚI (CREATE)
class PhienBanCreate(FileUploadBase):
    Loai_Tap_Tin: str = 'application/octet-stream'
    Nguoi_Tai_Len_ID: int = 1

# ĐƯỢC DÙNG KHI CẬP NHẬT PHIÊN BẢN (UPDATE)
class NewVersionRequest(FileUploadBase):
    TL_ID: int # Cần biết tài liệu nào đang được cập nhật
    Loai_Tap_Tin: str = 'application/octet-stream'
    Nguoi_Tai_Len_ID: int = 1

# ĐƯỢC DÙNG KHI CẬP NHẬT PHIÊN BẢN TỪ LINK
class NewVersionFromLink(BaseModel):
    TL_ID: int
    Share_Drive_Link: str
    Ten_File_Tren_Drive: str

# --- Response Schemas ---
class PhienBanTaiLieuResponse(BaseModel):
    PB_ID: int
    So_Phien_Ban: float
    Share_Drive_File_ID: Optional[str] = None
    Ten_File_Tren_Drive: Optional[str] = None
    Ngay_Tai_Len: Optional[datetime] = None 
    class Config:
        from_attributes = True

class TaiLieuLatestResponse(BaseModel):
    TL_ID: int
    MC_ID: int
    Tieu_De: str
    Ngay_Het_Hieu_Luc: Optional[datetime] = None
    Metadata: Dict[str, Any] = Field(default_factory=dict)
    Current_Version_ID: int
    current_version: PhienBanTaiLieuResponse 

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class CategoryCreateRequest(BaseModel):
    Ten_Danh_Muc: str
    ma_mau_hex: Optional[str] = '#3b82f6'
    icon_code: Optional[str] = 'Folder'
    phong_ban: Optional[str] = None
    phu_trach: Optional[str] = None
    ngay_ban_hanh: Optional[str] = None


class ProjectCreateRequest(BaseModel):
    DM_ID: int
    Ten_Du_An: str
    Ngay_Het_Hieu_Luc: Optional[datetime] = None
    ma_mau_hex: Optional[str] = '#3b82f6'
    icon_code: Optional[str] = 'Folder'
    phong_ban: Optional[str] = None
    phu_trach: Optional[str] = None
    ngay_ban_hanh: Optional[str] = None

class TaiLieuTreeItem(BaseModel):
    TL_ID: int
    MC_ID: int
    Tieu_De: str
    Ngay_Het_Hieu_Luc: Optional[datetime] = None
    Metadata: Dict[str, Any] = Field(default_factory=dict)
    current_version: Optional[PhienBanTaiLieuResponse] = None

    @field_validator('Metadata', mode='before')
    @classmethod
    def parse_metadata(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return {}
        return v or {}

    class Config:
        from_attributes = True
# 2. Dự án (Mục Con) trong cây
class ProjectTreeItem(BaseModel):
    MC_ID: int
    Ten_Muc_Con: str
    Ngay_Het_Hieu_Luc: Optional[datetime] = None
    tai_lieu: List[TaiLieuTreeItem] = Field(default_factory=list)
    class Config:
        from_attributes = True


# 3. Danh mục trong cây
class CategoryTreeResponse(BaseModel):
    DM_ID: int
    Ten_Danh_Muc: str
    Metadata: Dict[str, Any] = Field(default_factory=dict)
    muc_con: List[ProjectTreeItem] = Field(default_factory=list)

    @field_validator('Metadata', mode='before')
    @classmethod
    def parse_metadata(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return {}
        return v or {}

    class Config:
        from_attributes = True

# === SCHEMAS CHO CẬP NHẬT (UPDATE) ===
class CategoryUpdateRequest(BaseModel):
    Ten_Danh_Muc: str
    ma_mau_hex: Optional[str] = None
    icon_code: Optional[str] = None
    phong_ban: Optional[str] = None
    phu_trach: Optional[str] = None
    ngay_ban_hanh: Optional[str] = None

class ProjectUpdateRequest(BaseModel):
    Ten_Du_An: str
    Ngay_Het_Hieu_Luc: Optional[datetime] = None
    ma_mau_hex: Optional[str] = None
    icon_code: Optional[str] = None
    phong_ban: Optional[str] = None
    phu_trach: Optional[str] = None
    ngay_ban_hanh: Optional[str] = None

class DocumentMetadataUpdate(BaseModel):
    Tieu_De: str
    Ngay_Het_Hieu_Luc: Optional[datetime] = None
    nha_cung_cap: Optional[str] = None
    gia_tri_hd: Optional[str] = None
    ngay_ban_hanh: Optional[str] = None
    phong_ban: Optional[str] = None
    phu_trach: Optional[str] = None
    # ma_mau_hex và icon_code cho file nếu cần

class TaiLieuCreateFromLink(BaseModel):
    MC_ID: int
    Tieu_De: str
    Ngay_Het_Hieu_Luc: Optional[datetime] = None
    Share_Drive_Link: str  # Full URL: Google Drive, website, v.v.
    Ten_File_Tren_Drive: str
    Metadata: BaseMetadata