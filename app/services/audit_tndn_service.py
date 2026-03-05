import pandas as pd
import xml.etree.ElementTree as ET
from io import BytesIO
from app.services.drive_service import (
    get_drive_service, 
    find_child_folder_by_name_contain, 
    find_child_folder_exact,
    get_all_files_recursive
)
from app.services.smart_renamer_service import analyze_file_content


def find_tax_target_folders_recursive(service, parent_id, keyword_list):
    """Tìm đệ quy tất cả folder có tên chứa một trong các từ khóa"""
    matched_folders = []
    page_token = None

    try:
        while True:
            results = service.files().list(
                q=(
                    f"'{parent_id}' in parents "
                    "and mimeType = 'application/vnd.google-apps.folder' "
                    "and trashed = false"
                ),
                fields="nextPageToken, files(id, name, mimeType)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                pageSize=1000,
                pageToken=page_token
            ).execute()

            subfolders = results.get('files', [])
            for folder in subfolders:
                folder_name_upper = folder.get('name', '').upper()
                if any(keyword in folder_name_upper for keyword in keyword_list):
                    matched_folders.append(folder)

                matched_folders.extend(
                    find_tax_target_folders_recursive(service, folder['id'], keyword_list)
                )

            page_token = results.get('nextPageToken')
            if not page_token:
                break
    except Exception as e:
        print(f"⚠️ Lỗi khi đệ quy folder thuế: {e}")

    return matched_folders


def download_drive_file_content(service, file_id, mime_type):
    """Tải nội dung file Drive an toàn: file binary dùng get_media, Docs Editors dùng export_media"""
    export_map = {
        "application/vnd.google-apps.document": "text/plain",
        "application/vnd.google-apps.spreadsheet": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.google-apps.presentation": "application/pdf",
        "application/vnd.google-apps.drawing": "image/png",
    }

    try:
        if mime_type in export_map:
            return service.files().export_media(
                fileId=file_id,
                mimeType=export_map[mime_type]
            ).execute()

        return service.files().get_media(fileId=file_id, supportsAllDrives=True).execute()
    except Exception as e:
        print(f"   ⚠️ Không thể tải nội dung file {file_id}: {e}")
        return None

def parse_bctc_xml_logic(xml_content):
    """Bóc tách số liệu BCTC từ XML HTKK"""
    try:
        root = ET.fromstring(xml_content)
        def get_val(tag_name):
            node = root.find(f".//{{*}}{tag_name}")
            if node is not None and node.text:
                return float(node.text)
            return 0
        return {
            "tong_tai_san": get_val("ct270"),
            "doanh_thu": get_val("ct01"),
            "loi_nhuan": get_val("ct60"),
            "mst": root.find(".//{{*}}mst").text if root.find(".//{{*}}mst") is not None else "---"
        }
    except:
        return None

def get_tndn_audit_data(service, company_root_id, year, company_code):
    print(f"\n--- 🚀 ĐANG QUÉT HỒ SƠ TNDN: {company_code} (Năm {year}) ---")
    year_str = str(year)

    # 1. Tìm folder TAI-LIEU-THUE
    f_thue = find_child_folder_by_name_contain(service, company_root_id, "TAI-LIEU-THUE")
    if not f_thue:
        return {"status": "error", "message": "Không tìm thấy folder TAI-LIEU-THUE"}

    # 2. Tìm folder Năm (ưu tiên exact, sau đó kiểm tra năm có nằm trong tên folder)
    f_year = find_child_folder_exact(service, f_thue['id'], year_str)
    if not f_year:
        f_year = find_child_folder_by_name_contain(service, f_thue['id'], year_str)

    scan_folder_name = ""
    raw_files = []

    # 3. Nếu có folder năm -> vào nhánh TNDN/THU-NHAP-DOANH-NGHIEP trước
    if f_year:
        print(f"📂 Đã tìm thấy folder năm: {f_year['name']} (ID: {f_year['id']})")

        f_target = find_child_folder_by_name_contain(service, f_year['id'], "THU-NHAP-DOANH-NGHIEP")
        if not f_target:
            f_target = find_child_folder_by_name_contain(service, f_year['id'], "TNDN")

        if f_target:
            scan_folder_name = f_target['name']
            print(f"📍 Đã vào folder: {f_target['name']} (ID: {f_target['id']})")

            # Luồng cũ: lấy trực tiếp từ folder đích
            direct_results = service.files().list(
                q=f"'{f_target['id']}' in parents and trashed = false",
                fields="files(id, name, mimeType, webViewLink, createdTime)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                pageSize=1000
            ).execute()
            raw_files = [
                item for item in direct_results.get('files', [])
                if item.get('mimeType') != 'application/vnd.google-apps.folder'
            ]

            # Nếu luồng cũ không có file -> kiểm tra các folder bên trong và đệ quy lấy toàn bộ file
            if not raw_files:
                print("📂 Luồng cũ không có file, fallback đệ quy toàn bộ folder con trong THU-NHAP-DOANH-NGHIEP/TNDN")
                raw_files = get_all_files_recursive(service, f_target['id'])
        else:
            scan_folder_name = f_year['name']
            print("📂 Không thấy folder THU-NHAP-DOANH-NGHIEP/TNDN, fallback quét toàn bộ folder năm")
            raw_files = get_all_files_recursive(service, f_year['id'])

    # 4. Nếu không có folder năm -> đệ quy toàn bộ TAI-LIEU-THUE và lọc file theo năm
    if not f_year:
        print(f"📂 Không tìm thấy folder có năm {year_str}, tìm đệ quy toàn bộ nhánh TNDN để lọc file theo năm")
        target_folders = find_tax_target_folders_recursive(
            service,
            f_thue['id'],
            ["THU-NHAP-DOANH-NGHIEP", "TNDN"]
        )

        if target_folders:
            unique_files = {}
            for folder in target_folders:
                folder_files = get_all_files_recursive(service, folder['id'])
                for file_item in folder_files:
                    if year_str in file_item.get('name', ''):
                        unique_files[file_item['id']] = file_item
            raw_files = list(unique_files.values())
            scan_folder_name = f"Nhánh TNDN trong {f_thue['name']} (lọc theo năm {year_str})"
        else:
            all_tax_files = get_all_files_recursive(service, f_thue['id'])
            raw_files = [f for f in all_tax_files if year_str in f.get('name', '')]
            scan_folder_name = f"{f_thue['name']} (lọc theo năm {year_str})"

    if not raw_files:
        return {"status": "error", "message": f"Không tìm thấy file nào cho năm {year_str} trong tài liệu thuế"}

    print(f"🔎 Google Drive trả về: {len(raw_files)} items")

    bctc_content = None
    bctc_found = False
    files_to_review = []

    for f in raw_files:
        try:
            # Tải nội dung file để phân tích (hỗ trợ cả Google Docs Editors)
            content = download_drive_file_content(service, f['id'], f.get('mimeType', ''))

            # Robot phân tích gợi ý tên
            suggested = f['name']
            if content:
                suggested = analyze_file_content(f['name'], content, company_code)
            
            # Nhận diện BCTC
            is_bctc = "BCTC" in f['name'].upper() or "BCTC" in suggested.upper()
            if content and is_bctc and "xml" in f['mimeType']:
                parsed = parse_bctc_xml_logic(content)
                if parsed:
                    bctc_content = parsed
                    bctc_found = True
                    print(f"   ✅ Đã bóc được số liệu từ: {f['name']}")

            # Đưa vào danh sách kết quả (Khớp 100% với Frontend của bạn)
            files_to_review.append({
                "id": f['id'],
                "old_name": f['name'],
                "suggested_name": suggested,
                "link": f.get('webViewLink', '#'),
                "mime_type": f['mimeType'],
                "createdTime": f.get('createdTime')
            })
        except Exception as e:
            print(f"   ⚠️ Lỗi khi đọc tệp {f['name']}: {e}")

    print(f"--- ✅ Hoàn tất quét. Trả về {len(files_to_review)} tệp cho giao diện ---\n")

    return {
        "status": "success",
        "folder_name": scan_folder_name,
        "bctc_found": bctc_found,
        "bctc_content": bctc_content,
        "files": files_to_review,
        "total_files": len(files_to_review)
    }

def sum_tm_bctc_excel(file_content):
    """Bóc số liệu từ file Thuyết minh BCTC (Excel)"""
    try:
        df = pd.read_excel(BytesIO(file_content))
        data = {"tong_tai_san": 0, "doanh_thu": 0, "loi_nhuan": 0}
        
        # Robot đi tìm từ khóa ở cột bất kỳ và lấy số ở cột bên cạnh
        for index, row in df.iterrows():
            row_str = " ".join([str(val).lower() for val in row.values])
            # Tìm dòng Tổng cộng tài sản
            if "tổng cộng tài sản" in row_str or "mã số 270" in row_str:
                data["tong_tai_san"] = extract_first_number(row)
            # Tìm doanh thu
            if "doanh thu bán hàng" in row_str or "mã số 01" in row_str:
                data["doanh_thu"] = extract_first_number(row)
            # Tìm lợi nhuận
            if "lợi nhuận sau thuế" in row_str or "mã số 60" in row_str:
                data["loi_nhuan"] = extract_first_number(row)
        return data
    except:
        return None

def extract_first_number(row):
    """Tìm con số đầu tiên xuất hiện trong một hàng Excel"""
    for val in row.values:
        try:
            num = float(str(val).replace(',', ''))
            if num != 0: return num
        except: continue
    return 0

# Trong hàm get_tndn_audit_data, bổ sung:
# ... quét danh sách file ...
# if "TM" in f['name'].upper() or "THUYET-MINH" in suggested.upper():
#    tm_content = sum_tm_bctc_excel(content)