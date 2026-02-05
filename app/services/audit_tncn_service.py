# app/services/audit_tncn_service.py
import re
import traceback
from app.services.drive_service import (
    get_drive_service, 
    find_child_folder_by_name_contain, 
    find_child_folder_exact
)
from app.services.smart_renamer_service import analyze_file_content

def detect_quarter_and_type(name):
    name = name.upper()
    quarter = "UNKNOWN"
    file_type = "other"
    
    # 1. NHẬN DIỆN KỲ
    if any(k in name for k in ["CA-NAM", "CANAM", "YEAR", "FULL", "QT-NAM"]):
        quarter = "YEAR"
    else:
        q_match = re.search(r'Q([1-4])\b|QUY\s?([1-4])|QUÝ\s?([1-4])', name)
        if q_match:
            val = next(g for g in q_match.groups() if g is not None)
            quarter = f"Q{val}"
        else:
            m_match = re.search(r'(?:T|THANG|THÁNG)\s?0?([1-9]|1[0-2])\b', name)
            if m_match:
                m = int(m_match.group(1))
                if 1 <= m <= 3: quarter = "Q1"
                elif 4 <= m <= 6: quarter = "Q2"
                elif 7 <= m <= 9: quarter = "Q3"
                else: quarter = "Q4"

    # 2. NHẬN DIỆN LOẠI HỒ SƠ
    if any(k in name for k in ["BL", "LUONG", "LƯƠNG"]): file_type = "payroll"
    elif any(k in name for k in ["BCC", "CHAM-CONG", "CHẤM CÔNG"]): file_type = "timesheet"
    elif any(k in name for k in ["HDLD", "HOP-DONG", "HỢP ĐỒNG"]): file_type = "contract"
    elif any(k in name for k in ["QT", "QUYET-TOAN", "QUYẾT TOÁN"]): file_type = "finalization"

    return quarter, file_type

def get_tncn_audit_data(service, company_root_id, year, company_code):
    try:
        all_raw_files = []

        # Hàm trợ lý quét và gắn nhãn nguồn gốc
        def scan_and_tag(root_folder_id, label):
            if not root_folder_id: return
            # Lấy folder mẹ và các folder Quý/Tháng con bên trong
            subs = service.files().list(
                q=f"'{root_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
                supportsAllDrives=True, includeItemsFromAllDrives=True
            ).execute().get('files', [])
            
            ids = [root_folder_id] + [s['id'] for s in subs]
            for fid in ids:
                try:
                    res = service.files().list(
                        q=f"'{fid}' in parents and mimeType != 'application/vnd.google-apps.folder' and trashed = false",
                        fields="files(id, name, mimeType, webViewLink, createdTime)",
                        supportsAllDrives=True, includeItemsFromAllDrives=True
                    ).execute()
                    for item in res.get('files', []):
                        item['origin'] = label
                        all_raw_files.append(item)
                except: continue

        # --- TÌM CÁC NHÁNH THƯ MỤC ---
        f_thue = find_child_folder_by_name_contain(service, company_root_id, "THUE")
        f_cty = find_child_folder_by_name_contain(service, company_root_id, "CONG-TY")

        # A. QUÉT NHÁNH THUẾ (TNCN & GTGT)
        if f_thue:
            f_year_thue = find_child_folder_exact(service, f_thue['id'], str(year))
            if f_year_thue:
                # Nhánh TNCN
                f_tncn = find_child_folder_by_name_contain(service, f_year_thue['id'], "NHAN-CA-NHAN")
                scan_and_tag(f_tncn['id'] if f_tncn else None, "THUE-TNCN")
                # Nhánh GTGT (Lấy bảng lương thuế)
                f_gtgt = find_child_folder_by_name_contain(service, f_year_thue['id'], "GIA-TRI-GIA-TANG")
                scan_and_tag(f_gtgt['id'] if f_gtgt else None, "THUE-GTGT")

        # B. QUÉT NHÁNH CÔNG TY (5-LUONG) - ĐÂY LÀ PHẦN MỚI BẠN YÊU CẦU
        if f_cty:
            f_year_cty = find_child_folder_exact(service, f_cty['id'], str(year))
            if f_year_cty:
                f_luong_root = find_child_folder_by_name_contain(service, f_year_cty['id'], "5-LUONG")
                if f_luong_root:
                    # Tìm folder BANG-LUONG-CHAM-CONG
                    f_target = find_child_folder_by_name_contain(service, f_luong_root['id'], "BANG-LUONG")
                    if not f_target: f_target = f_luong_root # Nếu ko có folder con thì quét thẳng folder Luong
                    
                    scan_and_tag(f_target['id'], "CTY-LUONG")

        # --- PHÂN LOẠI DỮ LIỆU ---
        all_periods = ["Q1", "Q2", "Q3", "Q4", "YEAR"]
        structure = {p: {"payroll": [], "timesheet": [], "contract": [], "finalization": [], "others": []} for p in all_periods}
        unclassified = []

        for f in all_raw_files:
            q_label, f_type = detect_quarter_and_type(f['name'])
            file_info = {
                "id": f['id'], "name": f['name'], "link": f.get('webViewLink', '#'),
                "mime_type": f['mimeType'], "created_at": f.get('createdTime'),
                "origin": f.get('origin', 'UNKNOWN')
            }
            if q_label != "UNKNOWN":
                target_group = f_type if f_type != "other" else "others"
                structure[q_label][target_group].append(file_info)
            else:
                unclassified.append(file_info)

        return {"status": "success", "structure": structure, "unclassified": unclassified, "total_count": len(all_raw_files)}

    except Exception as e:
        traceback.print_exc()
        return {"status": "error", "message": str(e)}