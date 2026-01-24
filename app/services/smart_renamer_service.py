import pandas as pd
import xml.etree.ElementTree as ET
from io import BytesIO

def analyze_file_content(file_name, file_content, company_code):
    """
    Phân tích nội dung file để gợi ý tên chuẩn
    """
    ext = file_name.split('.')[-1].lower()
    
    # 1. XỬ LÝ FILE XML (Tờ khai HTKK)
    if ext == 'xml':
        try:
            root = ET.fromstring(file_content)
            # Lấy kỳ thuế (Format HTKK thường là Q/YYYY hoặc MM/YYYY)
            ky_thue = root.find(".//kyThue")
            ky_hieu = root.find(".//maHSo") # Ví dụ: 01/GTGT
            
            val_ky = ky_thue.text if ky_thue is not None else "XX-XXXX"
            # Chuyển đổi format từ HTKK sang chuẩn của bạn (Ví dụ: Q1/2024 -> Q1_2024)
            period_part = val_ky.replace('/', '_')
            
            prefix = "TK-VAT" if "GTGT" in str(ky_hieu.text) else "TK-THUE"
            return f"{prefix}_{period_part}_{company_code}.xml"
        except:
            return f"LOI-DOC-FILE_{file_name}"

    # 2. XỬ LÝ FILE EXCEL (Bảng kê)
    if ext in ['xlsx', 'xls']:
        try:
            # Chỉ đọc vài dòng đầu của các sheet để tìm keyword
            xl = pd.ExcelFile(BytesIO(file_content))
            is_mua_vao = False
            is_ban_ra = False
            
            for sheet_name in xl.sheet_names:
                content = str(xl.parse(sheet_name, nrows=5)).lower()
                if "mua vào" in content: is_mua_vao = True
                if "bán ra" in content: is_ban_ra = True
            
            prefix = "BK-VAT"
            if is_mua_vao: prefix += "-MUA"
            if is_ban_ra: prefix += "-BAN"
            
            return f"{prefix}_KỲ-NĂM_{company_code}.xlsx"
        except:
            return f"LOI-DOC-FILE_{file_name}"

    return file_name # Không nhận diện được thì giữ nguyên