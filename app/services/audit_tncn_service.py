# app/services/audit_tncn_service.py
import re
import traceback
from app.services.drive_service import (
    find_child_folder_by_name_contain, 
    find_child_folder_exact
)
from app.services.smart_renamer_service import analyze_file_content

def detect_quarter_and_type(name):
    """
    Nhận diện Quý và Loại hồ sơ.
    Chuyển đổi thông minh: T01-T03 -> Q1, T04-T06 -> Q2...
    """
    name = name.upper()
    quarter = "UNKNOWN"
    file_type = "other"
    
    # 1. NHẬN DIỆN KỲ (Check Cả Năm trước)
    if any(k in name for k in ["CA-NAM", "CANAM", "YEAR", "FULL", "QT-NAM"]):
        quarter = "YEAR"
    else:
        # Tìm Q1-Q4
        q_match = re.search(r'Q([1-4])\b|QUY\s?([1-4])|QUÝ\s?([1-4])', name)
        if q_match:
            val = next(g for g in q_match.groups() if g is not None)
            quarter = f"Q{val}"
        else:
            # Tìm Tháng rồi quy đổi sang Quý
            m_match = re.search(r'(?:T|THANG|THÁNG)\s?0?([1-9]|1[0-2])\b', name)
            if m_match:
                m = int(m_match.group(1))
                if 1 <= m <= 3: quarter = "Q1"
                elif 4 <= m <= 6: quarter = "Q2"
                elif 7 <= m <= 9: quarter = "Q3"
                elif 10 <= m <= 12: quarter = "Q4"

    # 2. NHẬN DIỆN LOẠI HỒ SƠ
    if any(k in name for k in ["BL", "LUONG", "LƯƠNG"]): file_type = "payroll"
    elif any(k in name for k in ["BCC", "CHAM-CONG", "CHẤM CÔNG"]): file_type = "timesheet"
    elif any(k in name for k in ["HDLD", "HOP-DONG", "HỢP ĐỒNG"]): file_type = "contract"
    elif any(k in name for k in ["QT", "QUYET-TOAN", "QUYẾT TOÁN"]): file_type = "finalization"

    return quarter, file_type

def get_tncn_audit_data(service, company_root_id, year, company_code):
    try:
        print(f"--- 🔍 BẮT ĐẦU QUÉT TNCN: {company_code} | NĂM {year} ---")

        # 1. Tìm folder Năm trong nhánh THUẾ
        f_thue = find_child_folder_by_name_contain(service, company_root_id, "THUE")
        if not f_thue: return {"status": "error", "message": "Thiếu folder TAI-LIEU-THUE"}
        
        f_year = find_child_folder_exact(service, f_thue['id'], str(year))
        if not f_year: return {"status": "error", "message": f"Thiếu folder năm {year}"}

        # 2. Xác định 2 nhánh mẹ: TNCN và GTGT (để lấy bảng lương thuế)
        f_tncn_root = find_child_folder_by_name_contain(service, f_year['id'], "NHAN-CA-NHAN")
        f_gtgt_root = find_child_folder_by_name_contain(service, f_year['id'], "GIA-TRI-GIA-TANG")

        all_raw_files = []

        # Hàm trợ lý quét đệ quy và gắn nhãn nguồn gốc
        def scan_and_tag(root_folder_id, label):
            if not root_folder_id: return
            # Tìm tất cả folder con (Quý 1, 2, 3, 4...)
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
                        item['origin'] = label # Gắn nhãn TNCN hoặc GTGT
                        all_raw_files.append(item)
                except: continue

        # Quét cả 2 nhánh
        scan_and_tag(f_tncn_root['id'] if f_tncn_root else None, "TNCN")
        scan_and_tag(f_gtgt_root['id'] if f_gtgt_root else None, "GTGT")

        # 3. Phân loại dữ liệu vào cấu trúc 4 Quý + YEAR
        all_periods = ["Q1", "Q2", "Q3", "Q4", "YEAR"]
        structure = {p: {"payroll": [], "timesheet": [], "contract": [], "finalization": [], "others": []} for p in all_periods}
        unclassified = []

        for f in all_raw_files:
            q_label, f_type = detect_quarter_and_type(f['name'])
            
            file_info = {
                "id": f['id'],
                "name": f['name'],
                "link": f.get('webViewLink', '#'),
                "mime_type": f['mimeType'],
                "created_at": f.get('createdTime'),
                "origin": f.get('origin', 'TNCN') # Trả về cho FE hiển thị
            }
            
            if q_label != "UNKNOWN":
                target_group = f_type if f_type != "other" else "others"
                structure[q_label][target_group].append(file_info)
            else:
                unclassified.append(file_info)

        return {
            "status": "success",
            "structure": structure,
            "unclassified": unclassified,
            "total_count": len(all_raw_files)
        }

    except Exception as e:
        print(f"❌ LỖI TNCN SERVICE: {e}")
        traceback.print_exc()
        return {"status": "error", "message": str(e)}