# Cenvi Drive Backend

## Run local
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

## Run với Docker

### 1) Chuẩn bị biến môi trường
Tạo file `.env` ở thư mục gốc (có thể dùng lại cấu hình DB như bên dưới).

### 2) Build image
```bash
docker compose build
```

### 3) Chạy container
```bash
docker compose up -d
```

API chạy tại: `http://localhost:8100`

### 4) Xem log
```bash
docker compose logs -f server
```

### 5) Dừng container
```bash
docker compose down
```

## Cấu hình MySQL làm DB

Tạo file `.env` ở thư mục gốc dự án và khai báo 1 trong 2 cách:

### Cách 1 (khuyên dùng): `MYSQL_URL`
```env
MYSQL_URL=mysql://<USER>:<PASSWORD>@<HOST>:3306/<DATABASE>
```

### Cách 2: `DATABASE_URL`
```env
DATABASE_URL=mysql://<USER>:<PASSWORD>@<HOST>:3306/<DATABASE>
```

Ghi chú:
- App sẽ ưu tiên `DATABASE_URL`, sau đó tới `MYSQL_URL`.
- App tự chuyển `mysql://...` thành `mysql+pymysql://...` cho SQLAlchemy.
- Nếu không có cả 2 biến trên, app fallback về SQLite local `cenvi_audit.db`.

## Khởi tạo schema trên MySQL

Sau khi cấu hình `.env`, chạy:

```bash
python scripts/init_mysql_db.py
```

Script sẽ:
- Tạo toàn bộ bảng theo model SQLAlchemy hiện có.
- Kiểm tra kết nối DB bằng truy vấn `SELECT 1`.
