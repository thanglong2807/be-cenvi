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
from app.services.audit_saoke_service import get_saoke_init_data, get_bank_files_logic, parse_saoke_xml_indicator

# --- Cấu hình Services ---
from app.services.drive_service import (
    get_drive_service, 
    get_all_files_recursive, 
    find_child_folder_by_name_contain,
    find_child_folder_exact
)
from app.services.audit_service import get_file_content_logic, get_xml_thuyet_minh_logic
from app.services.audit_gtgt_service import get_gtgt_audit_data
from app.services.audit_tndn_service import get_tndn_audit_data
from app.services.audit_tncn_service import get_tncn_audit_data
from app.services.audit_kt_service import get_kt_audit_data, get_xml_thuyet_minh_tags
from app.services.audit_hdon_service import get_hdon_audit_data
from app.services.audit_htk_service import get_htk_init_data, get_inventory_files_logic, parse_htk_xml_indicators

router = APIRouter(prefix="/audit", tags=["Audit"])

folder_repo = FolderRepository()
employee_repo = EmployeeRepository()

# Các hạng mục hiển thị 1 chấm to trên Ma trận
YEARLY_CATEGORIES = ["TNDN", "KT", "HTK", "TNCN", "Saoke"] 

# --- CÁC CLASS PAYLOAD ---
class AuditActionPayload(BaseModel):
    folder_id: int
    category: str
    year: int
    period: str
    action: str  # "match", "reject", "approve", "supplement"
    checklist_data: List[dict]
    overall_note: Optional[str] = ""

class FetchInvoicesPayload(BaseModel):
    folder_id: int
    xml_drive_id: str  # Sửa từ string thành str
    year: int
    period: str        # Sửa từ string thành str

# =========================================================================
# 1. API MA TRẬN TRẠNG THÁI (DASHBOARD CHÍNH)
# =========================================================================
@router.get("/matrix")
def get_audit_matrix(year: int = datetime.now().year, db: Session = Depends(get_db)):
    all_folders = folder_repo.get_all()
    categories = ["GTGT", "TNCN", "TNDN", "KT", "Hdon", "Saoke", "Luong", "HTK"]
    periods = ["Q1", "Q2", "Q3", "Q4"]
    
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

def get_session_info(db, f_id, cat, year, period):
    """Helper lấy checklist và note đã lưu trong SQL"""
    session = db.query(AuditSession).filter(
        AuditSession.folder_id == f_id,
        AuditSession.category == cat,
        AuditSession.year == year,
        AuditSession.period == period
    ).first()
    return {
        "checklist_data": session.checklist_data if session else [],
        "overall_note": session.overall_note if session else "",
        "session_status": session.status if session else "empty"
    }

@router.get("/compare-gtgt/{folder_id}")
def compare_gtgt(folder_id: int, year: int, period: str, db: Session = Depends(get_db)):
    folder = folder_repo.get_by_id(folder_id)
    root_id = getattr(folder, 'root_folder_id', None) or folder.get('root_folder_id')
    c_code = getattr(folder, 'company_code', None) or folder.get('company_code')
    try:
        service = get_drive_service()
        drive_data = get_gtgt_audit_data(service, root_id, year, period, c_code)
        sql_info = get_session_info(db, folder_id, "GTGT", year, period)
        return {**drive_data, **sql_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/compare-tndn/{folder_id}")
def compare_tndn(folder_id: int, year: int, db: Session = Depends(get_db)):
    folder = folder_repo.get_by_id(folder_id)
    root_id = getattr(folder, 'root_folder_id', None) or folder.get('root_folder_id')
    c_code = getattr(folder, 'company_code', None) or folder.get('company_code')
    try:
        service = get_drive_service()
        drive_data = get_tndn_audit_data(service, root_id, year, c_code)
        sql_info = get_session_info(db, folder_id, "TNDN", year, "YEAR")
        return {**drive_data, **sql_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/compare-tncn/{folder_id}")
def compare_tncn(folder_id: int, year: int, db: Session = Depends(get_db)):
    folder = folder_repo.get_by_id(folder_id)
    root_id = getattr(folder, 'root_folder_id', None) or folder.get('root_folder_id')
    c_code = getattr(folder, 'company_code', None) or folder.get('company_code')
    try:
        service = get_drive_service()
        drive_data = get_tncn_audit_data(service, root_id, year, c_code)
        sql_info = get_session_info(db, folder_id, "TNCN", year, "YEAR")
        return {**drive_data, **sql_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/compare-kt/{folder_id}")
def compare_kt(folder_id: int, year: int, db: Session = Depends(get_db)):
    folder = folder_repo.get_by_id(folder_id)
    root_id = getattr(folder, 'root_folder_id', None) or folder.get('root_folder_id')
    c_code = getattr(folder, 'company_code', None) or folder.get('company_code')
    try:
        service = get_drive_service()
        drive_data = get_kt_audit_data(service, root_id, year, c_code)
        sql_info = get_session_info(db, folder_id, "KT", year, "YEAR")
        return {**drive_data, **sql_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =========================================================================
# 3. NHÓM API HÓA ĐƠN (HDON)
# =========================================================================

@router.get("/hdon/tax-files/{folder_id}")
def get_hdon_tax_files(folder_id: int, year: int, period: str):
    folder = folder_repo.get_by_id(folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Không tìm thấy doanh nghiệp")
    root_id = getattr(folder, 'root_folder_id', None) or folder.get('root_folder_id')
    try:
        service = get_drive_service()
        data = get_gtgt_audit_data(service, root_id, year, period, folder.get('company_code'))
        return {"files": data.get('files', [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/hdon/fetch-invoices")
def fetch_invoices_by_xml(payload: FetchInvoicesPayload):
    service = get_drive_service()
    try:
        def _find_first_by_keywords(parent_id, keywords):
            if not parent_id:
                return None
            for keyword in keywords:
                found = find_child_folder_by_name_contain(service, parent_id, keyword)
                if found:
                    return found
            return None

        def _find_quarter_folder(parent_id, q):
            candidates = [
                f"QUY {q}", f"QUÝ {q}", f"Q{q}", f"QUY-{q}", f"QUY_{q}",
                f"HDM_QUY-{q}", f"HDM QUY {q}", f"HDM_Q{q}",
                f"HDB_QUY-{q}", f"HDB QUY {q}", f"HDB_Q{q}"
            ]
            return _find_first_by_keywords(parent_id, candidates)

        parsed = get_file_content_logic(service, payload.xml_drive_id)
        if parsed.get('type') != 'xml_tax':
            return {
                "val23": 0,
                "val34": 0,
                "buy_files": [],
                "sell_files": [],
                "has_data": False,
                "message": "File đã chọn không phải XML tờ khai GTGT hợp lệ"
            }

        d = parsed.get('data', {})
        val23 = float(d.get('ct23', 0))
        val34 = float(d.get('ct34', 0))

        folder = folder_repo.get_by_id(payload.folder_id)
        if not folder:
            raise HTTPException(status_code=404, detail="Không tìm thấy doanh nghiệp")
        root_id = folder.get('root_folder_id')
        q_num = payload.period.replace("Q", "")

        f_cty = _find_first_by_keywords(root_id, ["TAI-LIEU-CONG-TY", "CONG-TY", "CONG TY"])
        f_year = find_child_folder_exact(service, f_cty['id'], str(payload.year)) if f_cty else None
        if not f_year and f_cty:
            f_year = find_child_folder_by_name_contain(service, f_cty['id'], str(payload.year))

        buy_files, sell_files = [], []
        if f_year:
            if val23 > 0:
                f_buy_root = _find_first_by_keywords(f_year['id'], ["1-HOA-DON-MUA", "HOA-DON-MUA", "HD-MUA"])
                if f_buy_root:
                    f_q_buy = _find_quarter_folder(f_buy_root['id'], q_num)
                    if f_q_buy: buy_files = get_all_files_recursive(service, f_q_buy['id'])
            if val34 > 0:
                f_sell_root = _find_first_by_keywords(f_year['id'], ["2-HOA-DON-BAN", "HOA-DON-BAN", "HD-BAN"])
                if f_sell_root:
                    f_q_sell = _find_quarter_folder(f_sell_root['id'], q_num)
                    if f_q_sell: sell_files = get_all_files_recursive(service, f_q_sell['id'])

        return {"val23": val23, "val34": val34, "buy_files": buy_files, "sell_files": sell_files, "has_data": (val23 > 0 or val34 > 0)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =========================================================================
# 4. NHÓM TIỆN ÍCH FILE (VIEWER / DOWNLOAD)
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

@router.get("/files-only/{folder_id}")
def get_files_only(folder_id: int, year: int, period: str):
    folder = folder_repo.get_by_id(folder_id)
    root_id = getattr(folder, 'root_folder_id', None) or folder.get('root_folder_id')
    try:
        service = get_drive_service()
        all_files = get_all_files_recursive(service, root_id)
        relevant_files = [f for f in all_files if str(year) in f['name'] or period.upper() in f['name'].upper()]
        return {"status": "success", "files": relevant_files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =========================================================================
# 5. API LƯU HÀNH ĐỘNG (XÁC NHẬN / DUYỆT / SỬA)
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


# app/api/v1/audit.py

@router.get("/hdon/all-files/{folder_id}")
def get_all_hdon_files(folder_id: int, year: int, period: str):
    """
    API phục vụ sếp chọn file thủ công cho mục Hóa đơn.
    Gom file từ 3 folder: Thuế GTGT, Hóa đơn mua, Hóa đơn bán.
    """
    folder = folder_repo.get_by_id(folder_id)
    if not folder: raise HTTPException(status_code=404)
    
    root_id = getattr(folder, 'root_folder_id', None) or folder.get('root_folder_id')
    q_num = period.replace("Q", "")

    def _is_xml_file(file_item):
        mime_type = (file_item.get('mimeType') or file_item.get('mime_type') or '').lower()
        file_name = (file_item.get('name') or '').lower()
        return ('xml' in mime_type) or file_name.endswith('.xml')

    def _find_first_by_keywords(service, parent_id, keywords):
        if not parent_id:
            return None
        for keyword in keywords:
            found = find_child_folder_by_name_contain(service, parent_id, keyword)
            if found:
                return found
        return None

    def _find_quarter_folder(service, parent_id, q):
        candidates = [
            f"QUY {q}", f"QUÝ {q}", f"Q{q}", f"QUY-{q}", f"QUY_{q}",
            f"HDM_QUY-{q}", f"HDM QUY {q}", f"HDM_Q{q}",
            f"HDB_QUY-{q}", f"HDB QUY {q}", f"HDB_Q{q}"
        ]
        return _find_first_by_keywords(service, parent_id, candidates)
    
    try:
        from app.services.drive_service import get_drive_service, find_child_folder_by_name_contain, get_all_files_recursive, find_child_folder_exact
        service = get_drive_service()

        # 1. Lấy file XML từ nhánh THUẾ (Để sếp chọn làm tờ khai gốc)
        # Ưu tiên folder Quý, nếu không có thì fallback quét toàn bộ GIA-TRI-GIA-TANG trong năm
        tax_files = []
        f_thue = _find_first_by_keywords(service, root_id, ["TAI-LIEU-THUE", "THUE"])
        if f_thue:
            f_year = find_child_folder_exact(service, f_thue['id'], str(year))
            if not f_year:
                f_year = find_child_folder_by_name_contain(service, f_thue['id'], str(year))
            f_gtgt = find_child_folder_by_name_contain(service, f_year['id'], "GIA-TRI-GIA-TANG") if f_year else None
            f_q = _find_quarter_folder(service, f_gtgt['id'], q_num) if f_gtgt else None

            gtgt_files = []
            if f_q:
                gtgt_files = get_all_files_recursive(service, f_q['id'])

            if not gtgt_files and f_gtgt:
                gtgt_files = get_all_files_recursive(service, f_gtgt['id'])

            tax_files = [f for f in gtgt_files if _is_xml_file(f)]

        # 2. Lấy file từ folder 1-HOA-DON-MUA của nhánh CÔNG TY
        buy_files = []
        f_cty = _find_first_by_keywords(service, root_id, ["TAI-LIEU-CONG-TY", "CONG-TY", "CONG TY"])
        f_year_c = None
        if f_cty:
            f_year_c = find_child_folder_exact(service, f_cty['id'], str(year))
            if not f_year_c:
                f_year_c = find_child_folder_by_name_contain(service, f_cty['id'], str(year))
            f_buy_root = _find_first_by_keywords(service, f_year_c['id'], ["1-HOA-DON-MUA", "HOA-DON-MUA", "HD-MUA"]) if f_year_c else None
            f_q_buy = _find_quarter_folder(service, f_buy_root['id'], q_num) if f_buy_root else None
            if f_q_buy: buy_files = get_all_files_recursive(service, f_q_buy['id'])

        # 3. Lấy file từ folder 2-HOA-DON-BAN của nhánh CÔNG TY
        sell_files = []
        f_sell_root = _find_first_by_keywords(service, f_year_c['id'], ["2-HOA-DON-BAN", "HOA-DON-BAN", "HD-BAN"]) if f_year_c else None
        f_q_sell = _find_quarter_folder(service, f_sell_root['id'], q_num) if f_sell_root else None
        if f_q_sell: sell_files = get_all_files_recursive(service, f_q_sell['id'])

        return {
            "tax_xml_list": tax_files,
            "buy_folder_files": buy_files,
            "sell_folder_files": sell_files
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/saoke/init/{folder_id}")
def saoke_init(folder_id: int, year: int, db: Session = Depends(get_db)):
    folder = folder_repo.get_by_id(folder_id)
    if not folder: raise HTTPException(status_code=404)
    root_id = getattr(folder, 'root_folder_id', None) or folder.get('root_folder_id')
    
    # Lấy checklist cũ từ SQL (nếu có)
    session = db.query(AuditSession).filter(
        AuditSession.folder_id == folder_id,
        AuditSession.category == "Saoke",
        AuditSession.year == year,
        AuditSession.period == "YEAR"
    ).first()

    try:
        from app.services.audit_saoke_service import get_saoke_init_data, get_bank_files_logic
        service = get_drive_service()
        
        return {
            "tax_xml_files": get_saoke_init_data(service, root_id, year),
            "bank_drive_files": get_bank_files_logic(service, root_id, year),
            "checklist_data": session.checklist_data if session else [],
            "overall_note": session.overall_note if session else ""
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/saoke/check-112/{drive_id}")
def check_xml_112(drive_id: str):
    service = get_drive_service()
    content = service.files().get_media(fileId=drive_id, supportsAllDrives=True).execute()
    val = parse_saoke_xml_indicator(content)
    return {"ct112": val}
# app/api/v1/audit.py

@router.get("/saoke/check-112/{drive_id}")
def check_xml_112(drive_id: str):
    service = get_drive_service()
    try:
        # Tải nội dung file XML từ Drive
        content = service.files().get_media(fileId=drive_id, supportsAllDrives=True).execute()
        
        # Gọi hàm xử lý đã định nghĩa ở Bước 1
        val = parse_saoke_xml_indicator(content)
        
        return {"ct112": val}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


# app/api/v1/audit.py

@router.get("/htk/init/{folder_id}")
def htk_init(folder_id: int, year: int):
    folder = folder_repo.get_by_id(folder_id)
    root_id = getattr(folder, 'root_folder_id', None) or folder.get('root_folder_id')
    service = get_drive_service()
    return {
        "source_xml_files": get_htk_init_data(service, root_id, year),
        "inventory_drive_files": get_inventory_files_logic(service, root_id, year)
    }

@router.get("/htk/check-codes/{drive_id}")
def check_htk_xml(drive_id: str):
    service = get_drive_service()
    content = service.files().get_media(fileId=drive_id, supportsAllDrives=True).execute()
    return parse_htk_xml_indicators(content)


# app/api/v1/audit.py
from app.services.audit_luong_service import get_luong_init_data

@router.get("/luong/init/{folder_id}")
def luong_init(folder_id: int, year: int, period: str):
    folder = folder_repo.get_by_id(folder_id)
    root_id = getattr(folder, 'root_folder_id', None) or folder.get('root_folder_id')
    try:
        service = get_drive_service()
        return get_luong_init_data(service, root_id, year, period)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))