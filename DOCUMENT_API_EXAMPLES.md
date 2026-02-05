# Document API - JSON Examples

## 1. TẠO DANH MỤC (POST /documents/categories)

```json
{
  "Ten_Danh_Muc": "Tài liệu Kế toán",
  "ma_mau_hex": "#e74c3c",
  "icon_code": "FileText",
  "phong_ban": "Kế toán",
  "phu_trach": "Nguyễn Thị A",
  "ngay_ban_hanh": "2026-02-05"
}
```

**Response:**
```json
{
  "DM_ID": 1,
  "Ten_Danh_Muc": "Tài liệu Kế toán",
  "Share_Drive_Folder_ID": "folder_id_xxxxx",
  "Metadata": {
    "ma_mau_hex": "#e74c3c",
    "icon_code": "FileText",
    "phong_ban": "Kế toán",
    "phu_trach": "Nguyễn Thị A",
    "ngay_ban_hanh": "2026-02-05"
  }
}
```

---

## 2. TẠO DỰ ÁN (POST /documents/projects)

```json
{
  "DM_ID": 1,
  "Ten_Du_An": "Hồ sơ thuế 2025",
  "Ngay_Het_Hieu_Luc": "2026-12-31",
  "ma_mau_hex": "#3498db",
  "icon_code": "Folder",
  "phong_ban": "Kế toán",
  "phu_trach": "Trần Văn B",
  "ngay_ban_hanh": "2026-02-01"
}
```

**Response:**
```json
{
  "MC_ID": 5,
  "DM_ID": 1,
  "Ten_Muc_Con": "Hồ sơ thuế 2025",
  "Ngay_Het_Hieu_Luc": "2026-12-31T00:00:00",
  "Share_Drive_Folder_ID": "folder_id_yyyyy"
}
```

---

## 3. TẠO ITEM/TÀI LIỆU (POST /documents/item)

**Endpoint duy nhất hỗ trợ 2 cách:**

### 3.1 CÁCH 1: Upload file từ máy tính

**Form-data fields:**
```
mc_id: 5
tieu_de: "Bảng kê chi tiết GTGT tháng 1"
ngay_het_hieu_luc: "2026-06-30"  (optional)
metadata: "{\"ma_mau_hex\": \"#2ecc71\", \"icon_code\": \"FileExcel\"}"
ten_file_goc: "GTGT_2025_T01"
kich_thuoc_byte: 45678
file: <chọn file từ máy>
```

### 3.2 CÁCH 2: Dán link (Google Drive, Website, v.v.)

**Hỗ trợ mọi loại link:**
- Google Sheets: `https://docs.google.com/spreadsheets/d/...`
- Google Drive: `https://drive.google.com/file/d/...`
- Website: `https://cenvi.vn/`

**Form-data fields:**
```
mc_id: 5
tieu_de: "Bảng dữ liệu KPI 2026"
ngay_het_hieu_luc: "2027-12-31"  (optional)
metadata: "{\"ma_mau_hex\": \"#2ecc71\", \"icon_code\": \"FileSpreadsheet\"}"
share_drive_link: "https://docs.google.com/spreadsheets/d/1KF68El6c5-_2QwybKa2k-3N149L-xYU2-h6SsSAUXno/edit"
ten_file_tren_drive: "KPI_2026.xlsx"
```

**Lưu ý:**
- Phải cung cấp **1 trong 2** cách:
  - Upload: Cần `file`, `ten_file_goc`, `kich_thuoc_byte`
  - Dán link: Cần `share_drive_link`, `ten_file_tren_drive`
- `share_drive_link`: Full URL, hệ thống tự parse ID nếu là Google Drive
- `ngay_het_hieu_luc`: Nếu không truyền → tự động lấy từ dự án cha

**Response:**
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

## 4. CẬP NHẬT THÔNG TIN TÀI LIỆU (PUT /documents/item/{tl_id})

```json
{
  "Tieu_De": "Bảng kê chi tiết GTGT tháng 1 (Sửa)",
  "Ngay_Het_Hieu_Luc": "2026-07-31",
  "nha_cung_cap": "Công ty XYZ",
  "gia_tri_hd": "50000000",
  "ngay_ban_hanh": "2026-02-01",
  "phong_ban": "Kế toán",
  "phu_trach": "Nguyễn Thị A"
}
```

**Response:**
```json
{
  "TL_ID": 10,
  "MC_ID": 5,
  "Tieu_De": "Bảng kê chi tiết GTGT tháng 1 (Sửa)",
  "Ngay_Het_Hieu_Luc": "2026-07-31T00:00:00",
  "Current_Version_ID": 15,
  "Metadata": {
    "nha_cung_cap": "Công ty XYZ",
    "gia_tri_hd": "50000000",
    "ngay_ban_hanh": "2026-02-01",
    "phong_ban": "Kế toán",
    "phu_trach": "Nguyễn Thị A"
  }
}
```

---

## 5. CẬP NHẬT DỰ ÁN (PUT /documents/projects/{mc_id})

```json
{
  "Ten_Du_An": "Hồ sơ thuế 2025 (Updated)",
  "Ngay_Het_Hieu_Luc": "2026-11-30",
  "ma_mau_hex": "#9b59b6",
  "icon_code": "FolderOpen"
}
```

**Response:**
```json
{
  "MC_ID": 5,
  "DM_ID": 1,
  "Ten_Muc_Con": "Hồ sơ thuế 2025 (Updated)",
  "Ngay_Het_Hieu_Luc": "2026-11-30T00:00:00",
  "Share_Drive_Folder_ID": "folder_id_yyyyy"
}
```

---

## 6. LẤY TOÀN BỘ CÂY TÀI LIỆU (GET /documents/tree)

**Response:**
```json
[
  {
    "DM_ID": 1,
    "Ten_Danh_Muc": "Tài liệu Kế toán",
    "Metadata": {
      "ma_mau_hex": "#e74c3c",
      "icon_code": "FileText",
      "phong_ban": "Kế toán",
      "phu_trach": "Nguyễn Thị A",
      "ngay_ban_hanh": "2026-02-05"
    },
    "muc_con": [
      {
        "MC_ID": 5,
        "Ten_Muc_Con": "Hồ sơ thuế 2025",
        "Ngay_Het_Hieu_Luc": "2026-12-31T00:00:00",
        "tai_lieu": [
          {
            "TL_ID": 10,
            "MC_ID": 5,
            "Tieu_De": "Bảng kê chi tiết GTGT tháng 1",
            "Ngay_Het_Hieu_Luc": "2026-06-30T00:00:00",
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
          },
          {
            "TL_ID": 11,
            "MC_ID": 5,
            "Tieu_De": "Hóa đơn mua tháng 1",
            "Ngay_Het_Hieu_Luc": "2026-12-31T00:00:00",
            "Metadata": {
              "ma_mau_hex": "#f39c12",
              "icon_code": "FileInvoice"
            },
            "current_version": {
              "PB_ID": 16,
              "So_Phien_Ban": 1.0,
              "Share_Drive_File_ID": "file_id_wwwww",
              "Ten_File_Tren_Drive": "HDON_MUA_T01_v1.0.xlsx",
              "Ngay_Tai_Len": "2026-02-05T11:00:00"
            }
          }
        ]
      }
    ]
  }
]
```

---

## 7. LẤY CHI TIẾT DANH MỤC (GET /documents/categories/{dm_id}/detail)

**Response:** (Cấu trúc giống như item trong `/tree` nhưng chỉ 1 danh mục)
```json
{
  "DM_ID": 1,
  "Ten_Danh_Muc": "Tài liệu Kế toán",
  "Metadata": {
    "ma_mau_hex": "#e74c3c",
    "icon_code": "FileText",
    "phong_ban": "Kế toán",
    "phu_trach": "Nguyễn Thị A",
    "ngay_ban_hanh": "2026-02-05"
  },
  "muc_con": [
    {
      "MC_ID": 5,
      "Ten_Muc_Con": "Hồ sơ thuế 2025",
      "Ngay_Het_Hieu_Luc": "2026-12-31T00:00:00",
      "tai_lieu": [
        {
          "TL_ID": 10,
          "MC_ID": 5,
          "Tieu_De": "Bảng kê chi tiết GTGT tháng 1",
          "Ngay_Het_Hieu_Luc": "2026-06-30T00:00:00",
          "Metadata": {},
          "current_version": {}
        }
      ]
    }
  ]
}
```

---

## 8. CẬP NHẬT PHIÊN BẢN FILE (POST /documents/item/{tl_id}/version)

```json
{
  "ten_file_goc": "GTGT_2025_T01_v2",
  "kich_thuoc_byte": 52000,
  "file": "<file_binary>"
}
```

**Response:**
```json
{
  "PB_ID": 20,
  "TL_ID": 10,
  "So_Phien_Ban": 2.0,
  "Share_Drive_File_ID": "file_id_new",
  "Ten_File_Tren_Drive": "GTGT_2025_T01_v2.0.xlsx",
  "Ngay_Tai_Len": "2026-02-05T15:45:00"
}
```

---

## 9. XÓA DANH MỤC (DELETE /documents/categories/{dm_id})

**Response:**
```json
{
  "message": "Đã xóa danh mục khỏi Database và Google Drive"
}
```

---

## 10. XÓA DỰ ÁN (DELETE /documents/projects/{mc_id})

**Response:**
```json
{
  "message": "Đã xóa dự án khỏi Database và Google Drive"
}
```

---

## 11. XÓA ITEM (DELETE /documents/item/{tl_id})

**Response:**
```json
{
  "message": "Đã xóa tài liệu khỏi Database và Google Drive"
}
```

---

## Notes:
- **Ngay_Het_Hieu_Luc**: Có thể để trống (null). Item sẽ kế thừa từ dự án nếu không cấp rõ.
- **Metadata**: Tùy chuyên, có thể thêm các trường khác tùy nhu cầu.
- **So_Phien_Ban**: Tự động tăng khi upload phiên bản mới (1.0 → 2.0 → 3.0...).
- **File**: Sử dụng multipart/form-data khi upload.
