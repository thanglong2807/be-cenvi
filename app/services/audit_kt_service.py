
# app/services/audit_kt_service.py
import xml.etree.ElementTree as ET
from app.services.drive_service import (
    find_child_folder_by_name_contain, 
    find_child_folder_exact,
    get_drive_service
)
from app.services.audit_service import get_file_content_logic

def get_kt_audit_data(service, company_root_id, year, company_code):
    print(f"--- 🚀 ĐANG TRUY QUÉT ĐỆ QUY TOÀN BỘ CÂY THƯ MỤC KẾ TOÁN ---")

    # 1. Tìm folder gốc THUẾ -> NĂM
    f_thue = find_child_folder_by_name_contain(service, company_root_id, "THUE")
    if not f_thue: return {"status": "error", "message": "Thiếu folder TAI-LIEU-THUE"}
    
    f_year = find_child_folder_exact(service, f_thue['id'], str(year))
    if not f_year: return {"status": "error", "message": f"Thiếu folder năm {year}"}

    all_files = []

    # 2. LẤY FILE TỪ NHÁNH TNDN (BCTC XML) - Quét đệ quy luôn cho chắc
    f_tndn = find_child_folder_by_name_contain(service, f_year['id'], "DOANH-NGHIEP")
    xml_source_files = []
    if f_tndn:
        xml_source_files = get_all_files_recursive(service, f_tndn['id'], "DOANH-NGHIEP")
        all_files.extend(xml_source_files)

    # 3. QUÉT ĐỆ QUY TOÀN BỘ NHÁNH KẾ TOÁN
    f_kt_root = find_child_folder_by_name_contain(service, f_year['id'], "KE-TOAN")
    excel_target_files = []
    if f_kt_root:
        # Gọi hàm đệ quy để lấy sạch file ở mọi cấp độ folder con
        excel_target_files = get_all_files_recursive(service, f_kt_root['id'], "KE-TOAN")
        all_files.extend(excel_target_files)

    # 4. Danh mục đối soát mặc định
    checklist_schema = [
        {"task": "NKC", "reason": "Bắt buộc"},
        {"task": "Sổ chi tiết", "reason": "Bắt buộc"},
        {"task": "Công nợ 131", "reason": "Bắt buộc"},
        {"task": "Công nợ 331", "reason": "Bắt buộc"},
    ]

    print(f"✅ Robot đã 'đào' được tổng cộng {len(all_files)} tệp tin.")

    return {
        "status": "success",
        "files": all_files,
        "xml_source_files": xml_source_files,
        "excel_target_files": excel_target_files,
        "checklist_schema": checklist_schema
    }






# app/services/audit_kt_service.py
import xml.etree.ElementTree as ET

# app/services/audit_kt_service.py
import xml.etree.ElementTree as ET

def get_xml_thuyet_minh_tags(xml_content):
    """
    Hàm bóc tách dữ liệu sạch cho BCTC:
    Tích hợp logic xóa TTinChung và PLuc để lấy đúng giá trị CTieuTKhaiChinh
    """
    try:
        # 1. Giải mã và Xóa dòng "--- START OF FILE..." (Logic của Sếp)
        xml_text = xml_content.decode('utf-8')
        if '---' in xml_text:
            xml_text = xml_text.split('---', 2)[-1].strip()

        # 2. Định nghĩa Namespace và các thẻ chuẩn của HTKK
        NAMESPACE_URI = 'http://kekhaithue.gdt.gov.vn/TKhaiThue'
        NS = {'ns': NAMESPACE_URI}
        TTIN_CHUNG_TAG = f'{{{NAMESPACE_URI}}}TTinChung'
        PLUC_TAG = f'{{{NAMESPACE_URI}}}PLuc'

        # 3. Parse XML
        root = ET.fromstring(xml_text)

        # 4. Tìm thẻ HSoKhaiThue để bắt đầu dọn dẹp (Logic của Sếp)
        hso_khai_thue = root.find('.//ns:HSoKhaiThue', NS)

        if hso_khai_thue is not None:
            # Lặp qua các phần tử con và xóa những thẻ không cần thiết
            elements_to_remove = []
            for child in hso_khai_thue:
                # Nếu là Thông tin chung hoặc Phụ lục thì đánh dấu xóa
                if child.tag == TTIN_CHUNG_TAG or child.tag == PLUC_TAG:
                    elements_to_remove.append(child)
            
            # Thực hiện lệnh xóa vật lý khỏi cây XML
            for element in elements_to_remove:
                hso_khai_thue.remove(element)

        # 5. TRẢI PHẲNG DỮ LIỆU ĐÃ LỌC SẠCH
        rows = []
        # iter() sẽ quét qua các thẻ còn lại (chủ yếu nằm trong CTieuTKhaiChinh)
        for elem in root.iter():
            # Xóa bỏ namespace prefix để tên thẻ gọn gàng (ví dụ: ct270)
            tag_name = elem.tag.split('}')[-1] 
            
            # Chỉ lấy các thẻ có chứa giá trị văn bản trực tiếp
            if elem.text and elem.text.strip():
                rows.append({
                    "field": tag_name,
                    "value": elem.text.strip()
                })
        
        # Sắp xếp theo tên thẻ A-Z để sếp dễ soi trên FE
        return sorted(rows, key=lambda x: x['field'])

    except Exception as e:
        print(f"❌ Lỗi xử lý XML Thuyết minh (Cleaned): {e}")
        return []


def get_all_files_recursive(service, parent_id, folder_path=""):
    """
    Hàm đệ quy: Tìm TẤT CẢ các file nằm trong folder và các folder con sâu vô tận.
    """
    all_files = []
    
    # 1. Gọi API lấy tất cả item (cả file và folder) trong folder hiện tại
    results = service.files().list(
        q=f"'{parent_id}' in parents and trashed = false",
        fields="files(id, name, mimeType, webViewLink, createdTime)",
        supportsAllDrives=True, 
        includeItemsFromAllDrives=True,
        pageSize=1000
    ).execute()
    
    items = results.get('files', [])

    for item in items:
        # Nếu là Folder -> Tiếp tục đệ quy xuống dưới
        if item['mimeType'] == 'application/vnd.google-apps.folder':
            new_path = f"{folder_path}/{item['name']}" if folder_path else item['name']
            all_files.extend(get_all_files_recursive(service, item['id'], new_path))
        
        # Nếu là File -> Thêm vào danh sách kết quả
        else:
            item['folder_path'] = folder_path # Lưu lại đường dẫn để sếp biết file nằm ở đâu
            all_files.append(item)
            
    return all_files