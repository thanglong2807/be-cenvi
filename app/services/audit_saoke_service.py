# app/services/audit_saoke_service.py
from app.services.drive_service import (
    find_child_folder_by_name_contain, 
    find_child_folder_exact, 
    get_all_files_recursive
)
import xml.etree.ElementTree as ET

def parse_saoke_xml_indicator(xml_content):
    """Bóc mã ct112 từ cụm PLuc (như bạn yêu cầu)"""
    try:
        xml_text = xml_content.decode('utf-8')
        if '---' in xml_text: xml_text = xml_text.split('---', 2)[-1].strip()
        root = ET.fromstring(xml_text)
        
        # Tìm ct112 trong SoDuDauKy, SoPhatSinh, SoDuCuoiKy
        # Ở đây ta lấy Tổng phát sinh Nợ + Có của cả năm
        def get_val(path):
            node = root.find(f".//{{*}}PLuc//{{*}}SoPhatSinhTrongKy//{{*}}{path}//{{*}}ct112")
            return float(node.text) if node is not None and node.text else 0

        return get_val("No") + get_val("Co")
    except:
        return 0

def get_saoke_init_data(service, company_root_id, year):
    """
    Lấy tất cả file trong folder KE-TOAN (chia theo quý bên trong).
    Fallback sang DOANH-NGHIEP nếu không tìm thấy KE-TOAN.
    Cấu trúc: root -> TAI-LIEU-THUE -> {year} -> KE-TOAN -> Q1/Q2/Q3/Q4 -> files
    """
    f_thue = find_child_folder_by_name_contain(service, company_root_id, "TAI-LIEU-THUE")
    if not f_thue:
        f_thue = find_child_folder_by_name_contain(service, company_root_id, "THUE")
    if not f_thue:
        return []

    f_year = find_child_folder_exact(service, f_thue['id'], str(year))
    if not f_year:
        f_year = find_child_folder_by_name_contain(service, f_thue['id'], str(year))
    if not f_year:
        return []

    # Ưu tiên KE-TOAN (lấy toàn bộ file đệ quy gồm cả subfolder quý)
    f_kt = find_child_folder_by_name_contain(service, f_year['id'], "KE-TOAN")
    if f_kt:
        return get_all_files_recursive(service, f_kt['id'])

    # Fallback: DOANH-NGHIEP (chỉ lấy XML trực tiếp)
    f_dn = find_child_folder_by_name_contain(service, f_year['id'], "DOANH-NGHIEP")
    if not f_dn:
        f_dn = find_child_folder_by_name_contain(service, f_year['id'], "TNDN")
    if f_dn:
        res = service.files().list(
            q=f"'{f_dn['id']}' in parents and mimeType = 'application/xml' and trashed = false",
            fields="files(id, name, webViewLink)",
            supportsAllDrives=True, includeItemsFromAllDrives=True
        ).execute()
        return res.get('files', [])

    return []

def get_bank_files_logic(service, company_root_id, year):
    """Lấy toàn bộ file trong folder 4-SAO-KE-NGAN-HANG (Đệ quy cả năm)"""
    f_cty = find_child_folder_by_name_contain(service, company_root_id, "CONG-TY")
    f_year = find_child_folder_exact(service, f_cty['id'], str(year)) if f_cty else None
    f_bank = find_child_folder_by_name_contain(service, f_year['id'], "4-SAO-KE-NGAN-HANG")
    
    if f_bank:
        # Lấy tất cả file PDF/Excel sao kê của cả 12 tháng nộp trong này
        return get_all_files_recursive(service, f_bank['id'])
    return []

