from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from pydantic import BaseModel
from typing import Optional, List
import traceback

# --- Cấu hình Database & Repositories ---
from app.core.database import get_db
from app.models.audit import AuditSession
from app.db.repositories.folder_repo import FolderRepository
from app.db.repositories.employee_repo import EmployeeRepository

# --- Cấu hình Services ---
from app.services.drive_service import get_drive_service
from app.services.audit_service import get_file_content_logic, get_xml_thuyet_minh_logic
from app.services.audit_gtgt_service import get_gtgt_audit_data
from app.services.audit_tndn_service import get_tndn_audit_data
from app.services.audit_tncn_service import get_tncn_audit_data
from app.services.audit_kt_service import get_kt_audit_data, get_xml_thuyet_minh_tags

router = APIRouter(prefix="/audit", tags=["Audit"])

folder_repo = FolderRepository()
employee_repo = EmployeeRepository()

# Danh sách các hạng mục hiển thị 1 chấm to (theo năm)
YEARLY_CATEGORIES = ["TNDN", "KT", "HTK", "TNCN"]

# --- CÁC CLASS PAYLOAD ---
class AuditActionPayload(BaseModel):
    folder_id: int
    category: str
    year: int
    period: str
    action: str  # "match", "reject", "approve", "supplement"
    checklist_data: List[dict]
    overall_note: Optional[str] = ""

# =========================================================================
# 1. API MA TRẬN TRẠNG THÁI (MÀN HÌNH CHÍNH)
# =========================================================================
@router.get("/matrix")
def get_audit_matrix(year: int = datetime.now().year, db: Session = Depends(get_db)):
    all_folders = folder_repo.get_all()
    categories = ["GTGT", "TNCN", "TNDN", "KT", "Hdon", "Saoke", "Luong", "HTK"]
    periods = ["Q1", "Q2", "Q3", "Q4"]
    
    # Lấy toàn bộ session của năm để tối ưu tốc độ
    all_sessions = db.query(AuditSession).filter(AuditSession.year == year).all()
    
    matrix = []
    for f in all_folders:
        start_year = int(getattr(f, 'year', 0) or f.get('year', 0))
        if start_year > year:
            continue

        f_id = getattr(f, 'id', None) or f.get('id')
        c_code = getattr(f, 'company_code', None) or f.get('company_code')
        c_name = getattr(f, 'company_name', None) or f.get('company_name')
        db_status = getattr(f, 'status', 'active') or f.get('status')
        m_id = getattr(f, 'manager_employee_id', None) or f.get('manager_employee_id')
        
        manager = employee_repo.get_by_id(m_id) if m_id else None
        m_name = getattr(manager, 'name', 'N/A') if manager else 'N/A'

        status_map = {}
        for cat in categories:
            if cat in YEARLY_CATEGORIES:
                session = next((s for s in all_sessions if s.folder_id == f_id and s.category == cat and s.period in ["YEAR", "Năm"]), None)
                status_map[cat] = [session.status if session else "empty"]
            else:
                q_statuses = []
                for p in periods:
                    session = next((s for s in all_sessions if s.folder_id == f_id and s.category == cat and s.period == p), None)
                    q_statuses.append(session.status if session else "empty")
                status_map[cat] = q_statuses

        matrix.append({
            "id": f_id, "code": c_code, "name": c_name, "manager_id": str(m_id),
            "manager_name": m_name, "start_year": start_year, "db_status": db_status, 
            "status": status_map
        })
    return matrix

# =========================================================================
# 2. NHÓM API ĐỐI SOÁT CHI TIẾT (KẾT HỢP DRIVE + SQL)
# =========================================================================

# --- ĐỐI SOÁT GTGT ---
@router.get("/compare-gtgt/{folder_id}")
def compare_gtgt(folder_id: int, year: int, period: str, db: Session = Depends(get_db)):
    folder = folder_repo.get_by_id(folder_id)
    root_id = getattr(folder, 'root_folder_id', None) or folder.get('root_folder_id')
    c_code = getattr(folder, 'company_code', None) or folder.get('company_code')

    session = db.query(AuditSession).filter(AuditSession.folder_id == folder_id, AuditSession.category == "GTGT", AuditSession.period == period, AuditSession.year == year).first()
    try:
        service = get_drive_service()
        drive_data = get_gtgt_audit_data(service, root_id, year, period, c_code)
        drive_data["checklist_data"] = session.checklist_data if session else []
        drive_data["overall_note"] = session.overall_note if session else ""
        return drive_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- ĐỐI SOÁT TNDN ---
@router.get("/compare-tndn/{folder_id}")
def compare_tndn(folder_id: int, year: int, db: Session = Depends(get_db)):
    folder = folder_repo.get_by_id(folder_id)
    root_id = getattr(folder, 'root_folder_id', None) or folder.get('root_folder_id')
    c_code = getattr(folder, 'company_code', None) or folder.get('company_code')

    session = db.query(AuditSession).filter(AuditSession.folder_id == folder_id, AuditSession.category == "TNDN", AuditSession.period == "YEAR", AuditSession.year == year).first()
    try:
        service = get_drive_service()
        drive_data = get_tndn_audit_data(service, root_id, year, c_code)
        drive_data["checklist_data"] = session.checklist_data if session else []
        drive_data["overall_note"] = session.overall_note if session else ""
        return drive_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- ĐỐI SOÁT TNCN ---
@router.get("/compare-tncn/{folder_id}")
def compare_tncn(folder_id: int, year: int, db: Session = Depends(get_db)):
    folder = folder_repo.get_by_id(folder_id)
    root_id = getattr(folder, 'root_folder_id', None) or folder.get('root_folder_id')
    c_code = getattr(folder, 'company_code', None) or folder.get('company_code')

    session = db.query(AuditSession).filter(AuditSession.folder_id == folder_id, AuditSession.category == "TNCN", AuditSession.year == year, AuditSession.period == "YEAR").first()
    try:
        service = get_drive_service()
        drive_data = get_tncn_audit_data(service, root_id, year, c_code)
        drive_data["checklist_data"] = session.checklist_data if session else []
        drive_data["overall_note"] = session.overall_note if session else ""
        return drive_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- ĐỐI SOÁT KẾ TOÁN (KT) ---
@router.get("/compare-kt/{folder_id}")
def compare_kt(folder_id: int, year: int, db: Session = Depends(get_db)):
    folder = folder_repo.get_by_id(folder_id)
    root_id = getattr(folder, 'root_folder_id', None) or folder.get('root_folder_id')
    c_code = getattr(folder, 'company_code', None) or folder.get('company_code')

    session = db.query(AuditSession).filter(AuditSession.folder_id == folder_id, AuditSession.category == "KT", AuditSession.year == year, AuditSession.period == "YEAR").first()
    try:
        service = get_drive_service()
        drive_data = get_kt_audit_data(service, root_id, year, c_code)
        drive_data["checklist_data"] = session.checklist_data if session else []
        drive_data["overall_note"] = session.overall_note if session else ""
        return drive_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =========================================================================
# 3. NHÓM API XỬ LÝ TỆP TIN & THUYẾT MINH
# =========================================================================

@router.get("/file-content-raw/{drive_id}")
def get_raw_content(drive_id: str):
    service = get_drive_service()
    try:
        return get_file_content_logic(service, drive_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/xml-thuyet-minh/{drive_id}")
def get_tm_only(drive_id: str):
    service = get_drive_service()
    try:
        content = service.files().get_media(fileId=drive_id, supportsAllDrives=True).execute()
        tags = get_xml_thuyet_minh_tags(content) 
        return {"type": "xml_tax", "rows": tags}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Lỗi bóc tách thuyết minh: {str(e)}")

# =========================================================================
# 4. API LƯU HÀNH ĐỘNG (XÁC NHẬN/DUYỆT/SỬA)
# =========================================================================
@router.post("/action")
def handle_audit_action(payload: AuditActionPayload, db: Session = Depends(get_db)):
    prd = "YEAR" if payload.period in ["Năm", "YEAR", "year"] else payload.period

    session = db.query(AuditSession).filter(
        AuditSession.folder_id == payload.folder_id,
        AuditSession.category == payload.category,
        AuditSession.year == payload.year,
        AuditSession.period == prd
    ).first()

    status_map = {"approve": "pass", "reject": "fail", "match": "warning", "supplement": "warning"}
    new_status = status_map.get(payload.action, "warning")

    if not session:
        session = AuditSession(
            folder_id=payload.folder_id, category=payload.category,
            year=payload.year, period=prd,
            status=new_status,
            checklist_data=payload.checklist_data,
            overall_note=payload.overall_note
        )
        db.add(session)
    else:
        session.status = new_status
        session.checklist_data = payload.checklist_data
        session.overall_note = payload.overall_note
        session.updated_at = datetime.utcnow()
        flag_modified(session, "checklist_data")

    db.commit()
    return {"status": "success", "message": "Dữ liệu đã được lưu thành công"}