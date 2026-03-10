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
            f"QUY {q}", f"QUY-{q}", f"QUY_{q}", f"Q{q}",
            f"QUÝ {q}", f"QUY{q}", f"QUÝ{q}",
            f"HDM_QUY-{q}", f"HDM QUY {q}", f"HDM_Q{q}",
            f"HDB_QUY-{q}", f"HDB QUY {q}", f"HDB_Q{q}"
        ]
        return _find_first_by_keywords(parent_id, candidates)

    f_thue = _find_first_by_keywords(company_root_id, ["TAI-LIEU-THUE", "THUE"])
    f_year_thue = find_child_folder_exact(service, f_thue['id'], str(year)) if f_thue else None
    if not f_year_thue and f_thue:
        f_year_thue = find_child_folder_by_name_contain(service, f_thue['id'], str(year))

    # Ưu tiên đi qua folder năm; nếu không có thì fallback tìm thẳng dưới nhánh THUẾ.
    f_gtgt_root = find_child_folder_by_name_contain(service, f_year_thue['id'], "GIA-TRI-GIA-TANG") if f_year_thue else None
    if not f_gtgt_root and f_thue:
        f_gtgt_root = find_child_folder_by_name_contain(service, f_thue['id'], "GIA-TRI-GIA-TANG")

    f_q_thue = _find_quarter_folder(f_gtgt_root['id'], q_num) if f_gtgt_root else None
    
    def _is_xml_file(file_item):
        mime_type = (file_item.get('mimeType') or '').lower()
        file_name = (file_item.get('name') or '').lower()
        return ('xml' in mime_type) or file_name.endswith('.xml')

    def _is_tk_vat_file(file_name):
        normalized = (file_name or '').upper().replace('_', '-').replace(' ', '')
        return ('TK-VAT' in normalized) or ('TKVAT' in normalized)

    instruction = {"buy_val": 0, "sell_val": 0, "found_xml": False}
    tax_files = []
    xml_candidates = []

    # Ưu tiên quét folder quý; nếu không có (hoặc không có XML),
    # fallback quét đệ quy toàn bộ folder GIA-TRI-GIA-TANG.
    if f_q_thue:
        tax_files = get_all_files_recursive(service, f_q_thue['id'])
        xml_candidates = [f for f in tax_files if _is_xml_file(f)]

    if not xml_candidates and f_gtgt_root:
        # Đúng yêu cầu: nếu không có folder quý thì lấy toàn bộ file trong GIA-TRI-GIA-TANG.
        tax_files = get_all_files_recursive(service, f_gtgt_root['id'])
        xml_candidates = [f for f in tax_files if _is_xml_file(f)]

    prioritized_xml = [f for f in xml_candidates if _is_tk_vat_file(f.get('name'))]
    fallback_xml = [f for f in xml_candidates if not _is_tk_vat_file(f.get('name'))]

    for f in prioritized_xml + fallback_xml:
        parsed = get_file_content_logic(service, f['id'])
        if parsed.get('type') != 'xml_tax':
            continue

        d = parsed.get('data', {})
        instruction = {
            "buy_val": float(d.get('ct23', 0)),
            "sell_val": float(d.get('ct34', 0)),
            "found_xml": True
        }
        break

    # --- BƯỚC 2: LẤY FILE TỪ NHÁNH CÔNG TY DỰA TRÊN SỐ LIỆU ---
    f_cty = _find_first_by_keywords(company_root_id, ["TAI-LIEU-CONG-TY", "CONG-TY", "CONG TY"])
    f_year_cty = find_child_folder_exact(service, f_cty['id'], str(year)) if f_cty else None
    if not f_year_cty and f_cty:
        f_year_cty = find_child_folder_by_name_contain(service, f_cty['id'], str(year))
    
    buy_files = []
    sell_files = []

    if f_year_cty:
        # Nếu có giá trị mua vào (ct23)
        if instruction["buy_val"] > 0:
            f_buy = _find_first_by_keywords(f_year_cty['id'], ["1-HOA-DON-MUA", "HOA-DON-MUA", "HD-MUA"])
            if f_buy:
                f_q_buy = _find_quarter_folder(f_buy['id'], q_num)
                if f_q_buy: buy_files = get_all_files_recursive(service, f_q_buy['id'])

        # Nếu có giá trị bán ra (ct34)
        if instruction["sell_val"] > 0:
            f_sell = _find_first_by_keywords(f_year_cty['id'], ["2-HOA-DON-BAN", "HOA-DON-BAN", "HD-BAN"])
            if f_sell:
                f_q_sell = _find_quarter_folder(f_sell['id'], q_num)
                if f_q_sell: sell_files = get_all_files_recursive(service, f_q_sell['id'])

    return {
        "status": "success",
        "instruction": instruction,
        "tax_files": tax_files,
        "files": buy_files + sell_files, # Gộp lại cho sếp chọn ở FE
        "total_tax_files": len(tax_files),
        "total_buy": len(buy_files),
        "total_sell": len(sell_files)
    }