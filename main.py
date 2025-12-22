from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.employees import router as employee_router
from app.api.v1.companies import router as company_router
from app.api.v1.folders import router as folder_router

app = FastAPI(
    title="Cenvi BE",
    version="1.0.0"
)
origins = [
    "http://localhost:3000",           # React chạy ở máy local
    "https://tools.cenvi.vn"  # Frontend khi deploy lên mạng (nếu có)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Hoặc dùng ["*"] để cho phép tất cả (không khuyến khích khi production)
    allow_credentials=True,
    allow_methods=["*"],   # Cho phép tất cả các method: GET, POST, PUT, DELETE...
    allow_headers=["*"],   # Cho phép tất cả các header
)
# =========================
# API v1
# =========================
app.include_router(employee_router, prefix="/api/v1")
app.include_router(company_router, prefix="/api/v1")
app.include_router(folder_router, prefix="/api/v1")


# =========================
# Health check (rất nên có)
# =========================
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "cenvi-backend"
    }
