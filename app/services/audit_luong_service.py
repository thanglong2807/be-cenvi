# app/services/audit_luong_service.py
from app.services.drive_service import (
    find_child_folder_by_name_contain, 
    find_child_folder_exact, 
    get_all_files_recursive
)

def get_luong_init_data(service, company_root_id, year, period):
    """
    Gom dữ liệu cho mục Lương:
    1. Lấy file từ folder THUẾ -> KE-TOAN -> KT_QUY-X
    2. Lấy file đệ quy từ folder CÔNG TY -> 5-LUONG
    """
    q_num = period.replace("Q", "")
    
    # --- NHÁNH 1: LẤY FILE NGUỒN (KE-TOAN) ---
    f_thue = find_child_folder_by_name_contain(service, company_root_id, "THUE")
    f_year_thue = find_child_folder_exact(service, f_thue['id'], str(year)) if f_thue else None
    f_kt_root = find_child_folder_by_name_contain(service, f_year_thue['id'], "KE-TOAN") if f_year_thue else None
    
    source_files = []
    if f_kt_root:
        # Tìm folder KT_QUY-X
        f_q_kt = find_child_folder_by_name_contain(service, f_kt_root['id'], f"KT_QUY-{q_num}")
        if f_q_kt:
            res = service.files().list(
                q=f"'{f_q_kt['id']}' in parents and trashed = false",
                fields="files(id, name, webViewLink, mimeType)",
                supportsAllDrives=True, includeItemsFromAllDrives=True
            ).execute()
            source_files = res.get('files', [])

    # --- NHÁNH 2: LẤY FILE ĐỐI CHỨNG (5-LUONG) ---
    f_cty = find_child_folder_by_name_contain(service, company_root_id, "CONG-TY")
    f_year_cty = find_child_folder_exact(service, f_cty['id'], str(year)) if f_cty else None
    f_luong = find_child_folder_by_name_contain(service, f_year_cty['id'], "5-LUONG") if f_year_cty else None
    
    evidence_files = []
    if f_luong:
        # Quét đệ quy toàn bộ các cấp folder bên trong 5-LUONG
        evidence_files = get_all_files_recursive(service, f_luong['id'])

    return {
        "status": "success",
        "source_files": source_files,   # File trong KT_QUY-X
        "evidence_files": evidence_files # File trong 5-LUONG (đệ quy)
    }