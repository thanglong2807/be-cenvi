import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import các router
from app.api.v1.employees import router as employee_router
from app.api.v1.folders import router as folder_router
from app.api.v1.audit import router as audit_router
from app.api.v1.migration import router as migration_router 

from app.core.database import engine
from app.models import audit

app = FastAPI(
    title="Cenvi BE",
    version="1.0.0"
)

# Tạo bảng database
audit.Base.metadata.create_all(bind=engine)

# =========================
# 1. CẤU HÌNH CORS
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# 2. ĐĂNG KÝ ROUTER
# =========================

# ĐỔI TÊN HÀM Ở ĐÂY ĐỂ TRÁNH TRÙNG LẶP
@app.api_route("/", methods=["GET", "HEAD"])
def api_home_page(): # <--- Đã đổi từ read_root thành api_home_page
    return {"message": "Server is running..."}

app.include_router(employee_router, prefix="/api/v1")
app.include_router(folder_router, prefix="/api/v1")
app.include_router(migration_router, prefix="/api/v1") 
app.include_router(audit_router, prefix="/api/v1")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)