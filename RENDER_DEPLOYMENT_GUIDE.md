# Deployment Guide - Render

## Vấn đề đã sửa

**Lỗi ban đầu khi deploy lên Render:**
```
ModuleNotFoundError: No module named 'pandas'
```

### Nguyên nhân
Code sử dụng `pandas`, `openpyxl`, `xlrd` để xử lý Excel files nhưng các thư viện này chưa được khai báo trong `requirements.txt`.

### Giải pháp
Thêm các dependencies vào `requirements.txt`:
```txt
pandas==2.2.0
openpyxl==3.1.2
xlrd==2.0.1
```

---

## Cách Deploy lên Render (Chi tiết)

### 1. Chuẩn bị GitHub Repository

**Đẩy code lên GitHub:**
```bash
git add .
git commit -m "Add pandas, openpyxl, xlrd dependencies"
git push origin main
```

**Repository cần có:**
- ✅ `requirements.txt` (với đầy đủ dependencies)
- ✅ `render.yaml` (cấu hình tự động)
- ✅ `main.py` (entry point)
- ✅ `.env` hoặc Render Environment Variables

---

### 2. Connect GitHub to Render

1. Vào **render.com** → Login
2. Click **New** → **Web Service**
3. Chọn **Connect a repository**
4. Tìm và chọn repository của bạn
5. Click **Connect**

---

### 3. Render Configuration (Tự động từ render.yaml)

Render sẽ tự đọc `render.yaml` và apply:

```yaml
services:
  - type: web
    name: be-cenvi
    runtime: python
    plan: free
    autoDeploy: false
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
```

---

### 4. Add Environment Variables

Vào **Environment** tab, thêm các biến:

```
GOOGLE_SERVICE_ACCOUNT_FILE=/path/to/service_account.json
ROOT_DRIVE_FOLDER_ID=your_folder_id
GOOGLE_SHEET_ID=your_sheet_id
DATABASE_URL=mysql+pymysql://user:password@host:port/dbname?charset=utf8mb4
```

**Lưu ý:**
- Nếu dùng SQLite (local): `DATABASE_URL=sqlite:///./cenvi_audit.db`
- Nếu dùng MySQL (production): `DATABASE_URL=mysql+pymysql://USER:PASSWORD@HOST:PORT/DBNAME?charset=utf8mb4`

---

### 5. Database Setup (MySQL)

**Option A: Dùng MySQL ngoài (recommended)**

1. Tạo database trên MySQL:
```sql
CREATE DATABASE cenvi_audit CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2. Set `DATABASE_URL` trên Render:
```
DATABASE_URL=mysql+pymysql://root:password@mysql.server.com:3306/cenvi_audit?charset=utf8mb4
```

**Option B: Dùng SQLite (ephemeral, mất dữ liệu mỗi deploy)**
- Server Render không lưu file, mỗi lần redeploy sẽ xóa `cenvi_audit.db`
- Chỉ dùng cho testing

---

### 6. Deploy

1. Click **Create Web Service** (hoặc **Deploy** nếu đã connect)
2. Render sẽ:
   - Clone repository
   - Chạy `pip install -r requirements.txt`
   - Chạy `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. Chờ ~1-2 phút
4. Xem logs để debug nếu có lỗi

---

### 7. Verify Deployment

**Sau khi deploy thành công:**

1. Vào **Logs** tab để xem:
```
✅ Background polling task khởi động
🚀 Bắt đầu polling Google Sheet...
INFO:     Application startup complete.
```

2. Test API:
```bash
curl https://your-app.onrender.com/api/v1/work-links
```

3. Xem realtime logs:
```bash
Render → Your Service → Logs
```

---

## File Checklist

✅ `requirements.txt` - Chứa tất cả dependencies:
- fastapi, uvicorn, pydantic
- google-api-python-client, google-auth
- SQLAlchemy, PyMySQL, psycopg2
- **pandas, openpyxl, xlrd** (mới thêm)

✅ `render.yaml` - Cấu hình Render

✅ `.env` hoặc Render Environment Variables:
- GOOGLE_SERVICE_ACCOUNT_FILE
- ROOT_DRIVE_FOLDER_ID
- DATABASE_URL

✅ `main.py` - Khởi tạo FastAPI app

✅ GitHub repository - Public hoặc Private (nếu private, cần Render Deploy Token)

---

## Troubleshooting

### Lỗi: ModuleNotFoundError

**Nguyên nhân:** Thư viện chưa được khai báo trong requirements.txt

**Giải pháp:**
```bash
# 1. Cài thư viện tại local
pip install -r requirements.txt

# 2. Kiểm tra requirements.txt
cat requirements.txt

# 3. Commit và push
git add requirements.txt
git commit -m "Update requirements"
git push
```

### Lỗi: Database connection failed

**Nguyên nhân:** DATABASE_URL không đúng hoặc MySQL server không khả dụng

**Kiểm tra:**
```bash
# Test MySQL connection
mysql -h HOST -u USER -pPASSWORD -D DBNAME
```

### Lỗi: Port already in use

Render tự động assign port qua environment variable `$PORT`, không cần chỉnh sửa

---

## Monitoring

**Xem realtime logs:**
- Render Dashboard → Logs

**Health check:**
```bash
curl https://your-app.onrender.com/
# Nên trả về: {"message": "Server is running..."}
```

**Metrics:**
- Render → Metrics tab

---

## Auto-Redeploy

Để Render tự động redeploy khi push code:

1. Vào **Settings** tab
2. Tìm **Auto-Deploy**
3. Chọn **Yes** → **Deploy on push**

---

## Rollback

Nếu deployment bị lỗi:

1. Vào **Deploys** tab
2. Tìm deployment cũ (đã success)
3. Click **Redeploy**

---

## API URL

Sau deploy, URL sẽ là:
```
https://be-cenvi.onrender.com
```

Các endpoint:
```
GET  /api/v1/work-links
POST /api/v1/work-links
PUT  /api/v1/work-links/{id}
DELETE /api/v1/work-links/{id}
```

---

## Cost (Plan Free)

- ✅ 0.5 GB RAM
- ✅ Shared CPU
- ✅ 100GB bandwidth/month
- ⚠️ Hibernates sau 15 min inactivity
- ⚠️ 750 free tier hours/month

**Upgrade to Starter:** $7/month để avoid hibernation & dedicated CPU

