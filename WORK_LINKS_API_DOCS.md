# API Documentation - Work Links (Link Công Việc)

Base URL: `http://localhost:8000/api/v1/work-links`

---

## 1. Lấy tất cả link công việc

**Endpoint:** `GET /api/v1/work-links`

**Curl:**
```bash
curl -X GET "http://localhost:8000/api/v1/work-links"
```

**Response:**
```json
[
  {
    "id": 1,
    "title": "Trello Board - Dự án ABC",
    "des": "Bảng quản lý công việc chính của dự án ABC",
    "created_at": "2026-02-05T10:30:00",
    "updated_at": "2026-02-05T10:30:00"
  },
  {
    "id": 2,
    "title": "Google Drive - Tài liệu nội bộ",
    "des": "Thư mục chứa tất cả tài liệu nội bộ công ty",
    "created_at": "2026-02-05T09:15:00",
    "updated_at": "2026-02-05T09:15:00"
  }
]
```

---

## 2. Lấy chi tiết một link công việc

**Endpoint:** `GET /api/v1/work-links/{id}`

**Curl:**
```bash
curl -X GET "http://localhost:8000/api/v1/work-links/1"
```

**Response:**
```json
{
  "id": 1,
  "title": "Trello Board - Dự án ABC",
  "des": "Bảng quản lý công việc chính của dự án ABC",
  "created_at": "2026-02-05T10:30:00",
  "updated_at": "2026-02-05T10:30:00"
}
```

**Error 404:**
```json
{
  "detail": "Link công việc không tồn tại"
}
```

---

## 3. Tạo link công việc mới

**Endpoint:** `POST /api/v1/work-links`

**Curl:**
```bash
curl -X POST "http://localhost:8000/api/v1/work-links" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Notion - Tài liệu kỹ thuật",
    "des": "Trang Notion chứa tài liệu kỹ thuật và hướng dẫn API"
  }'
```

**Postman:**
1. Method: `POST`
2. URL: `http://localhost:8000/api/v1/work-links`
3. Headers:
   - Content-Type: `application/json`
4. Body (raw JSON):
```json
{
  "title": "Notion - Tài liệu kỹ thuật",
  "des": "Trang Notion chứa tài liệu kỹ thuật và hướng dẫn API"
}
```

**JavaScript (Fetch):**
```javascript
fetch('http://localhost:8000/api/v1/work-links', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    title: 'Notion - Tài liệu kỹ thuật',
    des: 'Trang Notion chứa tài liệu kỹ thuật và hướng dẫn API'
  })
})
.then(res => res.json())
.then(data => console.log(data));
```

**Python (requests):**
```python
import requests

url = "http://localhost:8000/api/v1/work-links"
data = {
    "title": "Notion - Tài liệu kỹ thuật",
    "des": "Trang Notion chứa tài liệu kỹ thuật và hướng dẫn API"
}

response = requests.post(url, json=data)
print(response.json())
```

**Response (201 Created):**
```json
{
  "id": 3,
  "title": "Notion - Tài liệu kỹ thuật",
  "des": "Trang Notion chứa tài liệu kỹ thuật và hướng dẫn API",
  "created_at": "2026-02-05T14:20:00",
  "updated_at": "2026-02-05T14:20:00"
}
```

---

## 4. Cập nhật link công việc

**Endpoint:** `PUT /api/v1/work-links/{id}`

**Curl (Cập nhật cả title và des):**
```bash
curl -X PUT "http://localhost:8000/api/v1/work-links/1" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Trello Board - Dự án ABC (Updated)",
    "des": "Bảng quản lý công việc đã được cập nhật mới"
  }'
```

**Curl (Chỉ cập nhật title):**
```bash
curl -X PUT "http://localhost:8000/api/v1/work-links/1" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Trello Board - Dự án XYZ"
  }'
```

**Postman:**
1. Method: `PUT`
2. URL: `http://localhost:8000/api/v1/work-links/1`
3. Headers:
   - Content-Type: `application/json`
4. Body (raw JSON):
```json
{
  "title": "Trello Board - Dự án ABC (Updated)",
  "des": "Bảng quản lý công việc đã được cập nhật mới"
}
```

**JavaScript (Fetch):**
```javascript
fetch('http://localhost:8000/api/v1/work-links/1', {
  method: 'PUT',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    title: 'Trello Board - Dự án ABC (Updated)',
    des: 'Bảng quản lý công việc đã được cập nhật mới'
  })
})
.then(res => res.json())
.then(data => console.log(data));
```

**Python (requests):**
```python
import requests

url = "http://localhost:8000/api/v1/work-links/1"
data = {
    "title": "Trello Board - Dự án ABC (Updated)",
    "des": "Bảng quản lý công việc đã được cập nhật mới"
}

response = requests.put(url, json=data)
print(response.json())
```

**Response:**
```json
{
  "id": 1,
  "title": "Trello Board - Dự án ABC (Updated)",
  "des": "Bảng quản lý công việc đã được cập nhật mới",
  "created_at": "2026-02-05T10:30:00",
  "updated_at": "2026-02-05T15:45:00"
}
```

**Error 404:**
```json
{
  "detail": "Link công việc không tồn tại"
}
```

---

## 5. Xóa link công việc

**Endpoint:** `DELETE /api/v1/work-links/{id}`

**Curl:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/work-links/1"
```

**Postman:**
1. Method: `DELETE`
2. URL: `http://localhost:8000/api/v1/work-links/1`

**JavaScript (Fetch):**
```javascript
fetch('http://localhost:8000/api/v1/work-links/1', {
  method: 'DELETE'
})
.then(res => {
  if (res.status === 204) {
    console.log('Đã xóa thành công');
  }
});
```

**Python (requests):**
```python
import requests

url = "http://localhost:8000/api/v1/work-links/1"
response = requests.delete(url)

if response.status_code == 204:
    print("Đã xóa thành công")
```

**Response:** `204 No Content` (Không có body)

**Error 404:**
```json
{
  "detail": "Link công việc không tồn tại"
}
```

---

## Lưu ý quan trọng

1. **Content-Type:** Tất cả request đều dùng `application/json`
2. **Trường bắt buộc:**
   - `title`: Bắt buộc khi tạo mới
   - `des`: Tùy chọn (có thể null)
3. **Update:** Có thể cập nhật một hoặc cả hai trường title/des
4. **Timestamps:** 
   - `created_at`: Tự động set khi tạo
   - `updated_at`: Tự động cập nhật khi sửa
5. **Sắp xếp:** Danh sách trả về theo thứ tự tạo mới nhất

---

## Ví dụ sử dụng thực tế

### Tạo nhiều link công việc
```bash
# Link 1: Trello
curl -X POST "http://localhost:8000/api/v1/work-links" \
  -H "Content-Type: application/json" \
  -d '{"title": "Trello - Sprint Planning", "des": "Board theo dõi sprint hiện tại"}'

# Link 2: Google Drive
curl -X POST "http://localhost:8000/api/v1/work-links" \
  -H "Content-Type: application/json" \
  -d '{"title": "Google Drive - Tài liệu", "des": "Thư mục tài liệu dự án"}'

# Link 3: Figma
curl -X POST "http://localhost:8000/api/v1/work-links" \
  -H "Content-Type: application/json" \
  -d '{"title": "Figma - UI Design", "des": "File design giao diện người dùng"}'
```

### Lấy và hiển thị danh sách
```javascript
// Lấy tất cả links và hiển thị
fetch('http://localhost:8000/api/v1/work-links')
  .then(res => res.json())
  .then(links => {
    links.forEach(link => {
      console.log(`${link.title}: ${link.des}`);
    });
  });
```
