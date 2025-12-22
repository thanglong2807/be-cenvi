from fastapi import FastAPI

from app.api.v1.employees import router as employee_router
from app.api.v1.companies import router as company_router
from app.api.v1.folders import router as folder_router

app = FastAPI(
    title="Cenvi BE",
    version="1.0.0"
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
