# app/services/audit_hdon_service.py
from app.services.drive_service import find_child_folder_by_name_contain, find_child_folder_exact, get_all_files_recursive
from app.services.audit_service import get_file_content_logic

def get_hdon_audit_data(service, company_root_id, year, period, company_code):
    """
    Quy trình Hdon:
    1. Vào folder THUẾ lấy file XML -> Bóc ct23 (Mua) và ct34 (Bán).
    2. Nếu ct23 > 0: Vào folder CÔNG TY/1-HOA-DON-MUA lấy file.
    3. Nếu ct34 > 0: Vào folder CÔNG TY/2-HOA-DON-BAN lấy file.
    """
    q_num = period.replace("Q", "")
    
    # --- BƯỚC 1: LẤY CHỈ THỊ TỪ XML THUẾ ---
    f_thue = find_child_folder_by_name_contain(service, company_root_id, "TAI-LIEU-THUE")
    f_year_thue = find_child_folder_exact(service, f_thue['id'], str(year)) if f_thue else None
    f_gtgt_root = find_child_folder_by_name_contain(service, f_year_thue['id'], "GIA-TRI-GIA-TANG") if f_year_thue else None
    f_q_thue = find_child_folder_by_name_contain(service, f_gtgt_root['id'], f"QUY {q_num}") if f_gtgt_root else None
    if not f_q_thue: f_q_thue = find_child_folder_by_name_contain(service, f_gtgt_root['id'], f"QUÝ {q_num}")

    instruction = {"buy_val": 0, "sell_val": 0, "found_xml": False}
    if f_q_thue:
        res = service.files().list(q=f"'{f_q_thue['id']}' in parents and mimeType = 'application/xml'").execute()
        for f in res.get('files', []):
            if "TK-VAT" in f['name'].upper():
                parsed = get_file_content_logic(service, f['id'])
                if parsed.get('type') == 'xml_tax':
                    d = parsed.get('data', {})
                    instruction = {
                        "buy_val": float(d.get('ct23', 0)),
                        "sell_val": float(d.get('ct34', 0)),
                        "found_xml": True
                    }
                break

    # --- BƯỚC 2: LẤY FILE TỪ NHÁNH CÔNG TY DỰA TRÊN SỐ LIỆU ---
    f_cty = find_child_folder_by_name_contain(service, company_root_id, "TAI-LIEU-CONG-TY")
    f_year_cty = find_child_folder_exact(service, f_cty['id'], str(year)) if f_cty else None
    
    buy_files = []
    sell_files = []

    if f_year_cty:
        # Nếu có giá trị mua vào (ct23)
        if instruction["buy_val"] > 0:
            f_buy = find_child_folder_by_name_contain(service, f_year_cty['id'], "1-HOA-DON-MUA")
            if f_buy:
                f_q_buy = find_child_folder_by_name_contain(service, f_buy['id'], f"HDM_QUY-{q_num}")
                if f_q_buy: buy_files = get_all_files_recursive(service, f_q_buy['id'])

        # Nếu có giá trị bán ra (ct34)
        if instruction["sell_val"] > 0:
            f_sell = find_child_folder_by_name_contain(service, f_year_cty['id'], "2-HOA-DON-BAN")
            if f_sell:
                f_q_sell = find_child_folder_by_name_contain(service, f_sell['id'], f"HDB_QUY-{q_num}")
                if f_q_sell: sell_files = get_all_files_recursive(service, f_q_sell['id'])

    return {
        "status": "success",
        "instruction": instruction,
        "files": buy_files + sell_files, # Gộp lại cho sếp chọn ở FE
        "total_buy": len(buy_files),
        "total_sell": len(sell_files)
    }