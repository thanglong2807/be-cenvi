# app/services/audit_htk_service.py
import xml.etree.ElementTree as ET
from app.services.drive_service import (
    find_child_folder_by_name_contain, 
    find_child_folder_exact, 
    get_all_files_recursive
)

def parse_htk_xml_indicators(xml_content):
    """Bóc mã 152, 153, 155, 156 từ bảng Cân đối tài khoản (PL_CDTK)"""
    try:
        xml_text = xml_content.decode('utf-8')
        if '---' in xml_text: xml_text = xml_text.split('---', 2)[-1].strip()
        root = ET.fromstring(xml_text)
        
        target_codes = ["ct152", "ct153", "ct155", "ct156"]
        results = {}

        for code in target_codes:
            # Tìm số dư cuối kỳ (No) của từng mã trong PL_CDTK
            node = root.find(f".//{{*}}PL_CDTK//{{*}}SoDuCuoiKy//{{*}}No//{{*}}{code}")
            results[code] = float(node.text) if node is not None and node.text else 0
            
        return results
    except:
        return {c: 0 for c in ["ct152", "ct153", "ct155", "ct156"]}

def get_htk_init_data(service, company_root_id, year):
    """Gom XML từ cả TNDN và GTGT"""
    f_thue = find_child_folder_by_name_contain(service, company_root_id, "THUE")
    if not f_thue: return []
    f_year = find_child_folder_exact(service, f_thue['id'], str(year))
    if not f_year: return []

    xml_files = []
    # Quét trong folder TNDN và GTGT
    for folder_name in ["DOANH-NGHIEP", "GIA-TRI-GIA-TANG"]:
        target = find_child_folder_by_name_contain(service, f_year['id'], folder_name)
        if target:
            res = service.files().list(
                q=f"'{target['id']}' in parents and mimeType = 'application/xml' and trashed = false",
                fields="files(id, name, webViewLink)",
                supportsAllDrives=True, includeItemsFromAllDrives=True
            ).execute()
            xml_files.extend(res.get('files', []))
    return xml_files

def get_inventory_files_logic(service, company_root_id, year):
    """Lấy file trong folder 6-HANG-TON-KHO-VA-GIA-THANH"""
    f_cty = find_child_folder_by_name_contain(service, company_root_id, "CONG-TY")
    f_year = find_child_folder_exact(service, f_cty['id'], str(year)) if f_cty else None
    f_htk = find_child_folder_by_name_contain(service, f_year['id'], "6-HANG-TON-KHO") if f_year else None
    
    if f_htk:
        return get_all_files_recursive(service, f_htk['id'])
    return []