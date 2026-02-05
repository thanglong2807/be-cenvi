# API Examples - Curl & Postman

## POST /documents/item - Tạo Item/Tài liệu

### CÁCH 1: Upload file từ máy tính

**Curl:**
```bash
curl -X POST "http://localhost:8000/documents/item" \
  -H "Content-Type: multipart/form-data" \
  -F "mc_id=5" \
  -F "tieu_de=Bảng kê chi tiết GTGT tháng 1" \
  -F "ngay_het_hieu_luc=2026-06-30" \
  -F "metadata={\"ma_mau_hex\": \"#2ecc71\", \"icon_code\": \"FileExcel\"}" \
  -F "ten_file_goc=GTGT_2025_T01.xlsx" \
  -F "kich_thuoc_byte=45678" \
  -F "file=@/path/to/your/file.xlsx"
```

**Postman:**
1. Method: `POST`
2. URL: `http://localhost:8000/documents/item`
3. Body → form-data:
   - `mc_id`: `5`
   - `tieu_de`: `Bảng kê chi tiết GTGT tháng 1`
   - `ngay_het_hieu_luc`: `2026-06-30`
   - `metadata`: `{"ma_mau_hex": "#2ecc71", "icon_code": "FileExcel"}`
   - `ten_file_goc`: `GTGT_2025_T01.xlsx`
   - `kich_thuoc_byte`: `45678`
   - `file`: [Chọn File từ máy]

**JavaScript (Fetch):**
```javascript
const formData = new FormData();
formData.append('mc_id', '5');
formData.append('tieu_de', 'Bảng kê chi tiết GTGT tháng 1');
formData.append('ngay_het_hieu_luc', '2026-06-30');
formData.append('metadata', JSON.stringify({
  ma_mau_hex: '#2ecc71',
  icon_code: 'FileExcel'
}));
formData.append('ten_file_goc', 'GTGT_2025_T01.xlsx');
formData.append('kich_thuoc_byte', '45678');
formData.append('file', fileInput.files[0]); // fileInput = <input type="file">

fetch('http://localhost:8000/documents/item', {
  method: 'POST',
  body: formData
})
.then(res => res.json())
.then(data => console.log(data));
```

**Python (requests):**
```python
import requests

url = "http://localhost:8000/documents/item"
files = {
    'file': open('/path/to/file.xlsx', 'rb')
}
data = {
    'mc_id': '5',
    'tieu_de': 'Bảng kê chi tiết GTGT tháng 1',
    'ngay_het_hieu_luc': '2026-06-30',
    'metadata': '{"ma_mau_hex": "#2ecc71", "icon_code": "FileExcel"}',
    'ten_file_goc': 'GTGT_2025_T01.xlsx',
    'kich_thuoc_byte': '45678'
}

response = requests.post(url, files=files, data=data)
print(response.json())
```

---

### CÁCH 2: Dán link (Google Drive, Website, v.v.)

**Ví dụ link hợp lệ:**
- Google Sheets: `https://docs.google.com/spreadsheets/d/1KF68El6c5-_2QwybKa2k-3N149L-xYU2-h6SsSAUXno/edit?gid=514374063#gid=514374063`
- Google Drive File: `https://drive.google.com/file/d/1ABC123xyz/view`
- Website: `https://cenvi.vn/`

**Curl (Google Sheets):**
```bash
curl -X POST "http://localhost:8000/documents/item" \
  -H "Content-Type: multipart/form-data" \
  -F "mc_id=5" \
  -F "tieu_de=Bảng dữ liệu KPI 2026" \
  -F "ngay_het_hieu_luc=2027-12-31" \
  -F "metadata={\"ma_mau_hex\": \"#2ecc71\", \"icon_code\": \"FileSpreadsheet\"}" \
  -F "share_drive_link=https://docs.google.com/spreadsheets/d/1KF68El6c5-_2QwybKa2k-3N149L-xYU2-h6SsSAUXno/edit?gid=514374063#gid=514374063" \
  -F "ten_file_tren_drive=KPI_2026.xlsx"
```

**Curl (Website):**
```bash
curl -X POST "http://localhost:8000/documents/item" \
  -H "Content-Type: multipart/form-data" \
  -F "mc_id=5" \
  -F "tieu_de=Link Website Cenvi" \
  -F "ngay_het_hieu_luc=2027-12-31" \
  -F "metadata={\"ma_mau_hex\": \"#3498db\", \"icon_code\": \"Globe\"}" \
  -F "share_drive_link=https://cenvi.vn/" \
  -F "ten_file_tren_drive=Website_Cenvi"
```

**Postman:**
1. Method: `POST`
2. URL: `http://localhost:8000/documents/item`
3. Body → form-data:
   - `mc_id`: `5`
   - `tieu_de`: `Bảng dữ liệu KPI 2026`
   - `ngay_het_hieu_luc`: `2027-12-31`
   - `metadata`: `{"ma_mau_hex": "#2ecc71", "icon_code": "FileSpreadsheet"}`
   - `share_drive_link`: `https://docs.google.com/spreadsheets/d/1KF68El6c5-_2QwybKa2k-3N149L-xYU2-h6SsSAUXno/edit`
   - `ten_file_tren_drive`: `KPI_2026.xlsx`

**JavaScript (Fetch):**
```javascript
const formData = new FormData();
formData.append('mc_id', '5');
formData.append('tieu_de', 'Bảng dữ liệu KPI 2026');
formData.append('ngay_het_hieu_luc', '2027-12-31');
formData.append('metadata', JSON.stringify({
  ma_mau_hex: '#2ecc71',
  icon_code: 'FileSpreadsheet'
}));
formData.append('share_drive_link', 'https://docs.google.com/spreadsheets/d/1KF68El6c5-_2QwybKa2k-3N149L-xYU2-h6SsSAUXno/edit?gid=514374063#gid=514374063');
formData.append('ten_file_tren_drive', 'KPI_2026.xlsx');

fetch('http://localhost:8000/documents/item', {
  method: 'POST',
  body: formData
})
.then(res => res.json())
.then(data => console.log(data));
```

**Python (requests):**
```python
import requests

url = "http://localhost:8000/documents/item"
data = {
    'mc_id': '5',
    'tieu_de': 'Bảng dữ liệu KPI 2026',
    'ngay_het_hieu_luc': '2027-12-31',
    'metadata': '{"ma_mau_hex": "#2ecc71", "icon_code": "FileSpreadsheet"}',
    'share_drive_link': 'https://docs.google.com/spreadsheets/d/1KF68El6c5-_2QwybKa2k-3N149L-xYU2-h6SsSAUXno/edit?gid=514374063',
    'ten_file_tren_drive': 'KPI_2026.xlsx'
}

response = requests.post(url, data=data)
print(response.json())
```

---

### CÁCH 3: Không truyền ngày hết hạn (kế thừa từ dự án)

**Curl:**
```bash
curl -X POST "http://localhost:8000/documents/item" \
  -H "Content-Type: multipart/form-data" \
  -F "mc_id=5" \
  -F "tieu_de=Hóa đơn mua tháng 1" \
  -F "metadata={\"ma_mau_hex\": \"#f39c12\", \"icon_code\": \"FileInvoice\"}" \
  -F "ten_file_goc=HDON_MUA_T01.xlsx" \
  -F "kich_thuoc_byte=12345" \
  -F "file=@/path/to/invoice.xlsx"
```

**JavaScript (Fetch):**
```javascript
const formData = new FormData();
formData.append('mc_id', '5');
formData.append('tieu_de', 'Hóa đơn mua tháng 1');
// Không truyền ngay_het_hieu_luc
formData.append('metadata', JSON.stringify({
  ma_mau_hex: '#f39c12',
  icon_code: 'FileInvoice'
}));
formData.append('ten_file_goc', 'HDON_MUA_T01.xlsx');
formData.append('kich_thuoc_byte', '12345');
formData.append('file', fileInput.files[0]);

fetch('http://localhost:8000/documents/item', {
  method: 'POST',
  body: formData
})
.then(res => res.json())
.then(data => console.log(data));
```

---

## Response mẫu (cho cả 3 cách)

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
    "Ngay_Tai_Len": "2026-02-05T10:30:00"
  }
}
```

---

## Lưu ý quan trọng

1. **Content-Type**: Phải là `multipart/form-data`
2. **Các trường bắt buộc**:
   - `mc_id`, `tieu_de`, `metadata`: Luôn bắt buộc
   - **Upload file**: Cần `file`, `ten_file_goc`, `kich_thuoc_byte`
   - **Dán link**: Cần `share_drive_link`, `ten_file_tren_drive`
3. **share_drive_link**: Hỗ trợ mọi loại link
   - Google Drive: `https://drive.google.com/file/d/...`
   - Google Sheets: `https://docs.google.com/spreadsheets/d/...`
   - Website: `https://cenvi.vn/`
   - Hệ thống tự động parse ID nếu là Google Drive, hoặc lưu link nguyên văn
4. **ngay_het_hieu_luc**: 
   - Format: `YYYY-MM-DD` hoặc `YYYY-MM-DDTHH:MM:SS`
   - Nếu không truyền → tự động lấy từ dự án cha
4. **metadata**: Phải là JSON string hợp lệ

---

## Error Responses

**400 - Bad Request (Thiếu thông tin)**
```json
{
  "detail": "Phải cung cấp: (1) file để upload HOẶC (2) share_drive_link + ten_file_tren_drive để dán link"
}
```

**400 - Bad Request (Metadata lỗi)**
```json
{
  "detail": "Metadata lỗi"
}
```

**404 - Not Found (Dự án không tồn tại)**
```json
{
  "detail": "Dự án không tồn tại."
}
```

---

# II. CẬP NHẬT PHIÊN BẢN MỚI (Update Version)

**Endpoint:** `POST /documents/item/{tl_id}/version`

Khi cần cập nhật tài liệu lên phiên bản mới (ví dụ từ v1.0 → v2.0), bạn có thể:
- **Upload file mới** từ máy tính
- **Dán link mới** (Google Drive, website, v.v.)

---

## CÁCH 1: Upload file mới

**Curl:**
```bash
curl -X POST "http://localhost:8000/documents/item/10/version" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/updated_file.xlsx" \
  -F "ten_file_goc=GTGT_2025_T01_Updated.xlsx" \
  -F "kich_thuoc_byte=52000"
```

**Postman:**
1. Method: `POST`
2. URL: `http://localhost:8000/documents/item/10/version`
3. Body → form-data:
   - `file`: (Chọn file từ máy)
   - `ten_file_goc`: `GTGT_2025_T01_Updated.xlsx`
   - `kich_thuoc_byte`: `52000`

**JavaScript (Fetch):**
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('ten_file_goc', 'GTGT_2025_T01_Updated.xlsx');
formData.append('kich_thuoc_byte', '52000');

fetch('http://localhost:8000/documents/item/10/version', {
  method: 'POST',
  body: formData
})
.then(res => res.json())
.then(data => console.log(data));
```

**Python (requests):**
```python
import requests

url = "http://localhost:8000/documents/item/10/version"
files = {'file': open('/path/to/updated_file.xlsx', 'rb')}
data = {
    'ten_file_goc': 'GTGT_2025_T01_Updated.xlsx',
    'kich_thuoc_byte': '52000'
}

response = requests.post(url, files=files, data=data)
print(response.json())
```

---

## CÁCH 2: Dán link mới

**Curl:**
```bash
curl -X POST "http://localhost:8000/documents/item/10/version" \
  -H "Content-Type: multipart/form-data" \
  -F "share_drive_link=https://docs.google.com/spreadsheets/d/NEW_SHEET_ID/edit" \
  -F "ten_file_tren_drive=GTGT_2025_T01_v2.xlsx"
```

**Postman:**
1. Method: `POST`
2. URL: `http://localhost:8000/documents/item/10/version`
3. Body → form-data:
   - `share_drive_link`: `https://docs.google.com/spreadsheets/d/NEW_SHEET_ID/edit`
   - `ten_file_tren_drive`: `GTGT_2025_T01_v2.xlsx`

**JavaScript (Fetch):**
```javascript
const formData = new FormData();
formData.append('share_drive_link', 'https://docs.google.com/spreadsheets/d/NEW_SHEET_ID/edit');
formData.append('ten_file_tren_drive', 'GTGT_2025_T01_v2.xlsx');

fetch('http://localhost:8000/documents/item/10/version', {
  method: 'POST',
  body: formData
})
.then(res => res.json())
.then(data => console.log(data));
```

**Python (requests):**
```python
import requests

url = "http://localhost:8000/documents/item/10/version"
data = {
    'share_drive_link': 'https://docs.google.com/spreadsheets/d/NEW_SHEET_ID/edit',
    'ten_file_tren_drive': 'GTGT_2025_T01_v2.xlsx'
}

response = requests.post(url, data=data)
print(response.json())
```

---

## Response mẫu (Update Version)

```json
{
  "PB_ID": 16,
  "So_Phien_Ban": 2.0,
  "Share_Drive_File_ID": "new_file_id_or_link",
  "Ten_File_Tren_Drive": "GTGT_2025_T01_v2.0.xlsx",
  "Ngay_Tai_Len": "2026-02-05T14:20:00"
}
```

---

## Lưu ý khi update version

1. **Content-Type**: Phải là `multipart/form-data`
2. **tl_id**: ID tài liệu cần update (trong URL path)
3. **Upload file**: Cần `file`, `ten_file_goc`, `kich_thuoc_byte`
4. **Dán link**: Cần `share_drive_link`, `ten_file_tren_drive`
5. **Phiên bản tự động tăng**: Hệ thống tự động tăng số phiên bản (1.0 → 2.0 → 3.0...)
6. **File cũ**: File phiên bản cũ sẽ được đổi tên thành `*_ARCHIVED.*` trên Drive (chỉ với upload file, không áp dụng cho link)

---

## Error Responses (Update Version)

**400 - Bad Request (Thiếu thông tin)**
```json
{
  "detail": "Phải cung cấp: (1) file để upload HOẶC (2) share_drive_link + ten_file_tren_drive để dán link"
}
```

**404 - Not Found (Tài liệu không tồn tại)**
```json
{
  "detail": "Tài liệu không tồn tại."
}
```
