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
    """Lấy XML từ folder TNDN (Quyết toán năm)"""
    f_thue = find_child_folder_by_name_contain(service, company_root_id, "THUE")
    f_year = find_child_folder_exact(service, f_thue['id'], str(year)) if f_thue else None
    
    # Vào folder THU-NHAP-DOANH-NGHIEP để lấy tờ khai năm
    f_tndn = find_child_folder_by_name_contain(service, f_year['id'], "DOANH-NGHIEP") if f_year else None
    if not f_tndn: f_tndn = find_child_folder_by_name_contain(service, f_year['id'], "TNDN")

    if f_tndn:
        res = service.files().list(
            q=f"'{f_tndn['id']}' in parents and mimeType = 'application/xml' and trashed = false",
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

