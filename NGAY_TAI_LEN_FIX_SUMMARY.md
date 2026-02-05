# Khắc phục lỗi thiếu Ngay_Tai_Len trong API

## Vấn đề
Khi tạo document item lần đầu tiên (upload file hoặc dán link), API response không có trường `Ngay_Tai_Len` trong `current_version`.

## Nguyên nhân
PhienBanTaiLieu model có cột `Ngay_Tai_Len` trong database, nhưng khi tạo object mới trong code, không set giá trị cho trường này.

## Giải pháp đã thực hiện

### 1. Thêm cột Ngay_Tai_Len vào model PhienBanTaiLieu
**File:** `app/models/document_model.py`

```python
class PhienBanTaiLieu(Base):
    __tablename__ = "PHIEN_BAN_TAI_LIEU"
    PB_ID = Column(Integer, primary_key=True, index=True)
    TL_ID = Column(Integer, ForeignKey("TAI_LIEU.TL_ID"))
    So_Phien_Ban = Column(DECIMAL(5,2))
    Share_Drive_File_ID = Column(String(255))
    Ten_File_Tren_Drive = Column(String(255))
    Ngay_Tai_Len = Column(DateTime, default=lambda: datetime.now())  # Tự động lấy thời gian hiện tại
    Metadata = Column(JSON)
```

### 2. Thêm import datetime
**File:** `app/models/document_model.py`

```python
from datetime import datetime
```

### 3. Cập nhật service khi tạo PhienBanTaiLieu
**File:** `app/services/document_service.py`

#### a) Hàm create_document_from_link()
```python
new_version = PhienBanTaiLieu(
    So_Phien_Ban=1.0,
    Share_Drive_File_ID=drive_id_or_link,
    Ten_File_Tren_Drive=item_data.Ten_File_Tren_Drive,
    Ngay_Tai_Len=datetime.now(),  # ← Thêm dòng này
    Metadata=FileMetadata(...).dict()
)
```

#### b) Hàm create_new_document_item()
```python
new_version = PhienBanTaiLieu(
    So_Phien_Ban=1.0, 
    Share_Drive_File_ID=file_id, 
    Ten_File_Tren_Drive=file_name_on_drive,
    Ngay_Tai_Len=datetime.now(),  # ← Thêm dòng này
    Metadata=FileMetadata(...).dict()
)
```

#### c) Hàm update_new_version()
```python
new_version = PhienBanTaiLieu(
    TL_ID=tl_id, 
    So_Phien_Ban=new_version_num, 
    Share_Drive_File_ID=file_id_new, 
    Ten_File_Tren_Drive=file_name_on_drive_new,
    Ngay_Tai_Len=datetime.now(),  # ← Thêm dòng này
    Metadata=FileMetadata(...).dict()
)
```

### 4. Database migration
**File:** `migrate_ngay_tai_len.py`

```bash
# Chạy migration để thêm cột vào database
python migrate_ngay_tai_len.py
```

Kết quả: Cột đã tồn tại (có thể đã được tạo trong migration trước đó)

## Schema response đã có sẵn
**File:** `app/schemas/document_schema.py`

```python
class PhienBanTaiLieuResponse(BaseModel):
    PB_ID: int
    So_Phien_Ban: float
    Share_Drive_File_ID: Optional[str] = None
    Ten_File_Tren_Drive: Optional[str] = None
    Ngay_Tai_Len: Optional[datetime] = None  # ← Đã có từ trước
    class Config:
        from_attributes = True
```

## Kết quả sau khi fix

### Response mẫu khi POST /documents/item
```json
{
  "TL_ID": 10,
  "MC_ID": 5,
  "Tieu_De": "Bảng kê chi tiết GTGT tháng 1",
  "Ngay_Het_Hieu_Luc": "2026-06-30T00:00:00",
  "Current_Version_ID": 15,
  "Metadata": {
    "ma_mau_hex": "#2ecc71",
    "icon_code": "FileExcel"
  },
  "current_version": {
    "PB_ID": 15,
    "So_Phien_Ban": 1.0,
    "Share_Drive_File_ID": "file_id_zzzzz",
    "Ten_File_Tren_Drive": "GTGT_2025_T01_v1.0.xlsx",
    "Ngay_Tai_Len": "2026-02-05T10:30:00"  ← Đã có timestamp
  }
}
```

## Files đã chỉnh sửa
1. ✅ `app/models/document_model.py` - Thêm cột Ngay_Tai_Len với default datetime.now()
2. ✅ `app/services/document_service.py` - Thêm Ngay_Tai_Len=datetime.now() vào 3 hàm create/update
3. ✅ `migrate_ngay_tai_len.py` - Migration script (cột đã tồn tại)

## Xác nhận hoạt động
- ✅ Model có cột Ngay_Tai_Len với default lambda
- ✅ Service set timestamp khi tạo mới version
- ✅ Schema response đã có trường Ngay_Tai_Len
- ✅ Database đã có cột Ngay_Tai_Len
- ✅ Không có lỗi compile/lint

## Test API
Bạn có thể test ngay bằng cách:

### Upload file:
```bash
curl -X POST "http://localhost:8000/documents/item" \
  -F "file=@file.xlsx" \
  -F "mc_id=5" \
  -F "tieu_de=Test upload" \
  -F "metadata={\"ma_mau_hex\": \"#3498db\", \"icon_code\": \"FileText\"}" \
  -F "ten_file_goc=test.xlsx" \
  -F "kich_thuoc_byte=1234"
```

### Dán link:
```bash
curl -X POST "http://localhost:8000/documents/item" \
  -F "mc_id=5" \
  -F "tieu_de=Test link" \
  -F "metadata={\"ma_mau_hex\": \"#2ecc71\", \"icon_code\": \"Link\"}" \
  -F "share_drive_link=https://docs.google.com/spreadsheets/d/abc123/edit" \
  -F "ten_file_tren_drive=Sheet_Test.xlsx"
```

Cả 2 request đều sẽ trả về response có **Ngay_Tai_Len** trong current_version.
