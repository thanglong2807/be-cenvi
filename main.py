import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import các router cũ
from app.api.v1.employees import router as employee_router
from app.api.v1.folders import router as folder_router
# Import router MỚI (Migration Tool)
from app.api.v1.migration import router as migration_router 

app = FastAPI(
    title="Cenvi BE",
    version="1.0.0"
)

# =========================
# 1. CẤU HÌNH CORS (Bắt buộc để Tool HTML chạy được)
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép mọi nguồn (file html, localhost, v.v.)
    allow_credentials=True,
    allow_methods=["*"],  # Cho phép mọi method (POST, GET, OPTIONS...)
    allow_headers=["*"],
)

# =========================
# 2. ĐĂNG KÝ ROUTER
# =========================
app.include_router(employee_router, prefix="/api/v1")
app.include_router(folder_router, prefix="/api/v1")
# Đăng ký router migration vào hệ thống
app.include_router(migration_router, prefix="/api/v1") 


@app.api_route("/", methods=["GET", "HEAD"])
def read_root():
    return {"message": "Server is running..."}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)