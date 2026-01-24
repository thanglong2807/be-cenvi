import pandas as pd
import xml.etree.ElementTree as ET
from io import BytesIO
from app.services.drive_service import (
    get_drive_service, 
    find_child_folder_by_name_contain, 
    find_child_folder_exact
)
from app.services.smart_renamer_service import analyze_file_content

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

    # 1. Tìm folder TAI-LIEU-THUE
    f_thue = find_child_folder_by_name_contain(service, company_root_id, "TAI-LIEU-THUE")
    if not f_thue:
        return {"status": "error", "message": "Không tìm thấy folder TAI-LIEU-THUE"}

    # 2. Tìm folder Năm (Ví dụ: 2024)
    f_year = find_child_folder_exact(service, f_thue['id'], str(year))
    if not f_year:
        return {"status": "error", "message": f"Không tìm thấy folder năm {year}"}

    # 3. Tìm folder THU-NHAP-DOANH-NGHIEP (Hoặc TNDN)
    f_target = find_child_folder_by_name_contain(service, f_year['id'], "THU-NHAP-DOANH-NGHIEP")
    if not f_target:
        f_target = find_child_folder_by_name_contain(service, f_year['id'], "TNDN")

    if not f_target:
        return {"status": "error", "message": "Không tìm thấy folder con THU-NHAP-DOANH-NGHIEP hoặc TNDN"}

    print(f"📍 Đã vào đúng folder: {f_target['name']} (ID: {f_target['id']})")

    # 4. Liệt kê TOÀN BỘ file (Thêm các tham số BẮT BUỘC cho Shared Drive)
    query = f"'{f_target['id']}' in parents and trashed = false"
    
    results = service.files().list(
        q=query,
        # Lấy đầy đủ fields để tránh lỗi undefined ở FE
        fields="files(id, name, mimeType, webViewLink, createdTime)", 
        supportsAllDrives=True, 
        includeItemsFromAllDrives=True,
        pageSize=1000
    ).execute()
    
    raw_files = results.get('files', [])
    print(f"🔎 Google Drive trả về: {len(raw_files)} items")

    bctc_content = None
    bctc_found = False
    files_to_review = []

    for f in raw_files:
        try:
            # Tải nội dung file để phân tích (Cũng cần supportsAllDrives)
            content = service.files().get_media(fileId=f['id'], supportsAllDrives=True).execute()
            
            # Robot phân tích gợi ý tên
            suggested = analyze_file_content(f['name'], content, company_code)
            
            # Nhận diện BCTC
            is_bctc = "BCTC" in f['name'].upper() or "BCTC" in suggested.upper()
            if is_bctc and "xml" in f['mimeType']:
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
        "folder_name": f_target['name'],
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