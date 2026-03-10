# app/services/audit_gtgt_service.py
import traceback
from app.services.drive_service import (
    find_child_folder_by_name_contain, 
    find_child_folder_exact,
    get_all_files_recursive # Đảm bảo hàm này đã được chuyển sang drive_service.py
)
from app.services.smart_renamer_service import analyze_file_content
from app.services.audit_service import parse_exact_gtgt_xml

def get_gtgt_audit_data(service, company_root_id, year, period, company_code):
    """
    Xử lý đối soát GTGT theo từng Quý:
    1. Tìm đường dẫn: TAI-LIEU-THUE -> Năm -> GIA-TRI-GIA-TANG -> QUY X
    2. Nếu QUY X không có tệp (hoặc không tồn tại), fallback quét toàn bộ GIA-TRI-GIA-TANG
    3. Robot phân tích nội dung từng tệp để gợi ý tên chuẩn
    4. Nếu thấy file Tờ khai XML -> Bóc tách chính xác ct23, 24, 27, 28
    """
    print(f"--- 🔍 BẮT ĐẦU ĐỐI SOÁT GTGT: {company_code} | {period}/{year} ---")

    try:
        def _is_xml_file(file_item):
            mime_type = (file_item.get('mimeType') or '').lower()
            file_name = (file_item.get('name') or '').lower()
            return ('xml' in mime_type) or file_name.endswith('.xml')

        def _is_tk_vat_name(file_name):
            normalized = (file_name or '').upper().replace('_', '-').replace(' ', '')
            return ('TK-VAT' in normalized) or ('TKVAT' in normalized)

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

        # --- BƯỚC 1: TÌM ĐƯỜNG DẪN ĐẾN FOLDER QUÝ ---
        # Tìm nhánh THUẾ
        f_thue = _find_first_by_keywords(company_root_id, ["TAI-LIEU-THUE", "THUE"])
        if not f_thue:
            return {"status": "error", "message": "Không tìm thấy folder TAI-LIEU-THUE"}

        # Tìm folder Năm (VD: 2024)
        f_year = find_child_folder_exact(service, f_thue['id'], str(year))
        if not f_year:
            f_year = find_child_folder_by_name_contain(service, f_thue['id'], str(year))

        # Tìm folder GIA-TRI-GIA-TANG, ưu tiên theo nhánh năm; nếu thiếu thì fallback thẳng dưới THUẾ.
        f_gtgt_root = find_child_folder_by_name_contain(service, f_year['id'], "GIA-TRI-GIA-TANG") if f_year else None
        if not f_gtgt_root:
            f_gtgt_root = find_child_folder_by_name_contain(service, f_thue['id'], "GIA-TRI-GIA-TANG")
        if not f_gtgt_root:
            return {"status": "error", "message": "Không tìm thấy folder GIA-TRI-GIA-TANG"}

        # Tìm đích danh folder QUÝ (Hỗ trợ cả QUY 1 và QUÝ 1)
        q_num = period.replace("Q", "")
        f_quarter = _find_quarter_folder(f_gtgt_root['id'], q_num)

        # --- BƯỚC 2: QUÉT ĐỆ QUY LẤY TOÀN BỘ FILE ---
        # Ưu tiên quét folder Quý; nếu không có file thì fallback quét toàn bộ GIA-TRI-GIA-TANG
        scan_folder = None
        raw_files = []

        if f_quarter:
            print(f"📍 Đã vào folder Quý: {f_quarter['name']}")
            raw_files = get_all_files_recursive(service, f_quarter['id'])
            print(f"🔎 Tổng số tệp tin trong {f_quarter['name']}: {len(raw_files)}")
            if raw_files:
                scan_folder = f_quarter

        if not scan_folder:
            print("📂 Không có file trong folder Quý hoặc không tìm thấy folder Quý, fallback quét GIA-TRI-GIA-TANG")
            raw_files = get_all_files_recursive(service, f_gtgt_root['id'])
            print(f"🔎 Tổng số tệp tin trong {f_gtgt_root['name']}: {len(raw_files)}")
            scan_folder = f_gtgt_root

        # --- BƯỚC 3: PHÂN TÍCH NỘI DUNG VÀ BÓC SỐ LIỆU ---
        files_to_review = []
        xml_stats = {
            "buy_val": 0, "buy_tax": 0,
            "sell_val": 0, "sell_tax": 0,
            "found": False
        }

        for f in raw_files:
            try:
                f_id = f['id']
                f_name = f['name']
                m_type = f.get('mimeType', '')

                # Tối ưu: chỉ tải nội dung khi là XML, vì get_media là call tốn thời gian nhất.
                content = None
                suggested = f_name
                if _is_xml_file(f):
                    content = service.files().get_media(fileId=f_id, supportsAllDrives=True).execute()
                    suggested = analyze_file_content(f_name, content, company_code)

                    # Giữ logic nghiệp vụ: bóc số liệu từ XML tờ khai GTGT (ưu tiên tên TK-VAT).
                    if _is_tk_vat_name(f_name) or _is_tk_vat_name(suggested):
                        xml_stats = parse_exact_gtgt_xml(content)
                        if xml_stats["found"]:
                            print(f"   ✅ Đã bóc thành công số liệu từ: {f_name}")

                # Đóng gói thông tin trả về cho Frontend
                files_to_review.append({
                    "id": f_id,
                    "old_name": f_name,
                    "suggested_name": suggested,
                    "link": f.get('webViewLink', '#'),
                    "mime_type": m_type,
                    "createdTime": f.get('createdTime')
                })

            except Exception as fe:
                print(f"   ⚠️ Lỗi khi xử lý tệp {f.get('name')}: {fe}")
                continue

        return {
            "status": "success",
            "folder_name": scan_folder['name'],
            "total_files": len(files_to_review),
            "xml_stats": xml_stats,
            "files": files_to_review
        }

    except Exception as e:
        print(f"❌ LỖI NGHIÊM TRỌNG TẠI GTGT SERVICE:")
        traceback.print_exc()
        return {"status": "error", "message": str(e)}