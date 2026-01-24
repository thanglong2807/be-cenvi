import pandas as pd
import xml.etree.ElementTree as ET
from io import BytesIO
import traceback
from fastapi import HTTPException
from zipfile import BadZipFile
from sqlalchemy.orm import Session
from app.models.audit import AuditSession
from app.core.audit_rules import DEFAULT_CHECKLISTS

class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def init_audit_session(self, folder_id: int, category: str, period: str, year: int):
        """Khởi tạo một phiên kiểm tra mới dựa trên template mẫu"""
        template = DEFAULT_CHECKLISTS.get(category, [])
        initial_data = [
            {"task_id": item["id"], "task_name": item["task"], "status": "waiting", "robot_log": "", "human_note": ""} 
            for item in template
        ]
        new_session = AuditSession(
            folder_id=folder_id,
            category=category,
            period=period,
            year=year,
            checklist_data=initial_data
        )
        self.db.add(new_session)
        self.db.commit()
        self.db.refresh(new_session)
        return new_session

    def init_all_categories_for_company(self, folder_id: int, year: int):
        """Tạo hàng loạt checklist cho 1 công ty/năm"""
        created_sessions = []
        for category in DEFAULT_CHECKLISTS.keys():
            existing = self.db.query(AuditSession).filter(
                AuditSession.folder_id == folder_id,
                AuditSession.category == category,
                AuditSession.year == year
            ).first()
            if not existing:
                period_type = "YEAR" if category in ["TNDN", "KT", "HTK"] else "Q1" 
                session = self.init_audit_session(folder_id, category, period_type, year)
                created_sessions.append(session)
        return created_sessions

# =========================================================================
# 1. HÀM DÀNH RIÊNG CHO KẾ TOÁN (KT): LỌC THUYẾT MINH SẠCH
# =========================================================================
def get_xml_thuyet_minh_logic(service, drive_id):
    """
    Logic bóc tách dành riêng cho mục Kế Toán:
    - Xóa TTinChung, PLuc (Theo yêu cầu sếp).
    - Trải phẳng các thẻ ct* có giá trị khác 0.
    """
    try:
        content = service.files().get_media(fileId=drive_id, supportsAllDrives=True).execute()
        xml_text = content.decode('utf-8')
        
        # Xóa header rác nếu có
        if '---' in xml_text:
            xml_text = xml_text.split('---', 2)[-1].strip()

        NAMESPACE_URI = 'http://kekhaithue.gdt.gov.vn/TKhaiThue'
        NS = {'ns': NAMESPACE_URI}
        TTIN_CHUNG_TAG = f'{{{NAMESPACE_URI}}}TTinChung'
        PLUC_TAG = f'{{{NAMESPACE_URI}}}PLuc'

        root = ET.fromstring(xml_text)
        hso_khai_thue = root.find('.//ns:HSoKhaiThue', NS)

        if hso_khai_thue is not None:
            # Xóa bỏ các cụm thẻ không cần thiết theo yêu cầu
            elements_to_remove = [child for child in hso_khai_thue if child.tag in [TTIN_CHUNG_TAG, PLUC_TAG]]
            for element in elements_to_remove:
                hso_khai_thue.remove(element)

        # Trải phẳng và lọc thẻ ct* khác 0
        rows = []
        for elem in root.iter():
            tag_name = elem.tag.split('}')[-1]
            if tag_name.startswith('ct'):
                val_raw = elem.text.strip() if elem.text else ""
                if val_raw:
                    try:
                        # Lọc giá trị khác 0
                        if float(val_raw.replace(',', '.')) != 0:
                            rows.append({"field": tag_name, "value": val_raw})
                    except ValueError:
                        # Nếu là text (không phải số) thì vẫn lấy
                        rows.append({"field": tag_name, "value": val_raw})
        
        return {
            "type": "xml_tax",
            "rows": sorted(rows, key=lambda x: x['field'])
        }
    except Exception as e:
        print(f"Lỗi bóc Thuyết minh: {e}")
        return {"type": "error", "message": str(e)}

# =========================================================================
# 2. HÀM ĐỌC LƯỚI DỮ LIỆU THÔ (DÙNG CHO CLICK-SELECT TRÊN UI)
# =========================================================================
def get_file_content_logic(service, drive_id):
    try:
        meta = service.files().get(fileId=drive_id, fields="mimeType, name", supportsAllDrives=True).execute()
        m_type = meta.get('mimeType', '')
        f_name = meta.get('name', '')
        content = service.files().get_media(fileId=drive_id, supportsAllDrives=True).execute()
        file_bytes = BytesIO(content)

        # XỬ LÝ EXCEL
        if "spreadsheet" in m_type or f_name.lower().endswith(('.xlsx', '.xls')):
            df = None
            try:
                file_bytes.seek(0)
                df = pd.read_excel(file_bytes, header=None, engine='openpyxl')
            except (BadZipFile, Exception):
                try:
                    file_bytes.seek(0)
                    df = pd.read_excel(file_bytes, header=None, engine='xlrd')
                except:
                    raise ValueError("Không đọc được định dạng Excel (.xls hoặc .xlsx)")

            if df is not None:
                df = df.fillna("")
                clean_rows = [[str(cell) for cell in row] for row in df.values.tolist()]
                return {"type": "excel", "name": f_name, "rows": clean_rows}

        # XỬ LÝ XML THÔNG THƯỜNG
        if "xml" in m_type or f_name.lower().endswith('.xml'):
            root = ET.fromstring(content)
            data_map = {}
            rows = []
            for elem in root.iter():
                tag = elem.tag.split('}')[-1]
                if elem.text and elem.text.strip():
                    val = elem.text.strip()
                    rows.append({"field": tag, "value": val})
                    if tag.startswith('ct'): data_map[tag] = val
            
            return {
                "type": "xml_tax",
                "header": {"ten_to_khai": f_name, "mst": "", "ky_thue": ""},
                "data": data_map,
                "rows": rows
            }
            
        return {"type": "unsupported", "name": f_name, "message": f"Loại file {m_type} không hỗ trợ"}

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

# =========================================================================
# 3. HÀM DÀNH RIÊNG CHO GTGT: BÓC 4 CHỈ SỐ CT23, 24, 27, 28
# =========================================================================
def parse_exact_gtgt_xml(xml_content):
    try:
        root = ET.fromstring(xml_content)
        def get_value_from_group(parent_tag, child_tag):
            parent_node = root.find(f".//{{*}}{parent_tag}")
            if parent_node is not None:
                target_node = parent_node.find(f"./{{*}}{child_tag}")
                if target_node is not None and target_node.text:
                    return float(target_node.text)
            return 0
        return {
            "buy_val": get_value_from_group("GiaTriVaThueGTGTHHDVMuaVao", "ct23"),
            "buy_tax": get_value_from_group("GiaTriVaThueGTGTHHDVMuaVao", "ct24"),
            "sell_val": get_value_from_group("HHDVBRaChiuThueGTGT", "ct27"),
            "sell_tax": get_value_from_group("HHDVBRaChiuThueGTGT", "ct28"),
            "found": True
        }
    except:
        return {"buy_val": 0, "buy_tax": 0, "sell_val": 0, "sell_tax": 0, "found": False}