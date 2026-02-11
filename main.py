import uvicorn
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path

# Import các router
from app.api.v1.employees import router as employee_router
from app.api.v1.folders import router as folder_router
from app.api.v1.audit import router as audit_router
from app.api.v1.migration import router as migration_router 
from app.api.v1.document_api import router as document_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.work_links import router as work_link_router

# Import Database
from app.core.database import engine
# Import Models để tạo bảng
from app.models import audit, document_model, work_link_model

# Import Services
from app.services.dashboard_sheet_service import dashboard_service
from app.api.v1.dashboard import broadcast_sheet_update
from app.core.config import settings

# ====================================================================
# BACKGROUND TASK - POLLING GOOGLE SHEET
# ====================================================================
def _can_poll_sheet() -> bool:
    return bool(settings.GOOGLE_SERVICE_ACCOUNT_FILE and settings.ROOT_DRIVE_FOLDER_ID and settings.GOOGLE_SHEET_ID)

async def poll_sheet_updates():
    """
    Background task chạy định kỳ để kiểm tra Google Sheet
    Nếu có thay đổi, broadcast tới tất cả clients WebSocket
    """
    print("🚀 Bắt đầu polling Google Sheet...")
    
    while True:
        try:
            if not _can_poll_sheet():
                await asyncio.sleep(settings.SHEET_POLLING_INTERVAL)
                continue
            # Lấy dữ liệu mới từ Sheet (để None để dùng default từ config)
            new_data = dashboard_service.fetch_data(None)
            
            if new_data and dashboard_service.has_changed(new_data):
                print(f"📢 Phát hiện thay đổi, broadcast tới clients...")
                await broadcast_sheet_update(new_data)
            
            # Chờ trước khi check lần tiếp theo
            await asyncio.sleep(settings.SHEET_POLLING_INTERVAL)
            
        except Exception as e:
            print(f"❌ Lỗi polling sheet: {e}")
            await asyncio.sleep(5)  # Retry sau 5s nếu lỗi


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle context manager cho FastAPI
    Chạy startup task khi app khởi động
    """
    # Startup
    task = None
    if _can_poll_sheet():
        task = asyncio.create_task(poll_sheet_updates())
        print("✅ Background polling task khởi động")
    else:
        print("⚠️ Bỏ qua polling Google Sheet (thiếu env GOOGLE_SERVICE_ACCOUNT_FILE/ROOT_DRIVE_FOLDER_ID/GOOGLE_SHEET_ID)")
    
    yield
    
    # Shutdown
    if task:
        task.cancel()
        print("🛑 Background polling task dừng")


app = FastAPI(
    title="Cenvi BE",
    version="1.0.0",
    lifespan=lifespan
)

# =========================
# 0. TẠO BẢNG DATABASE
# =========================
audit.Base.metadata.create_all(bind=engine)
document_model.Base.metadata.create_all(bind=engine)
work_link_model.Base.metadata.create_all(bind=engine)

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
# 2. KHÔNG DÙNG SEED DATA NỮA
# =========================
# (Đã xóa hàm seed_document_data)

# =========================
# 3. ĐĂNG KÝ ROUTER
# =========================
@app.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)
def api_home_page(): 
    return {"message": "Server is running...", "dashboard": "Visit /dashboard.html for real-time dashboard"}

app.include_router(employee_router, prefix="/api/v1")
app.include_router(folder_router, prefix="/api/v1")
app.include_router(migration_router, prefix="/api/v1") 
app.include_router(audit_router, prefix="/api/v1")
app.include_router(document_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(work_link_router, prefix="/api/v1")

# =========================
# 4. SERVE STATIC FILES (Dashboard HTML)
# =========================
# Thêm route để serve file HTML dashboard
@app.get("/dashboard.html")
async def serve_dashboard():
    """Serve HTML dashboard file"""
    dashboard_path = Path("app/dashboard.html")
    if dashboard_path.exists():
        with open(dashboard_path, 'r', encoding='utf-8') as f:
            from fastapi.responses import HTMLResponse
            return HTMLResponse(content=f.read())
    return {"error": "Dashboard file not found"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8100, reload=True)