from sqlalchemy.orm import Session
from app.models.audit import AuditSession
from app.core.audit_rules import DEFAULT_CHECKLISTS
import pandas as pd
import xml.etree.ElementTree as ET
from io import BytesIO

class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def init_audit_session(self, folder_id: int, category: str, period: str, year: int):
        """Khởi tạo một phiên kiểm tra mới dựa trên template"""
        # Lấy checklist mẫu
        template = DEFAULT_CHECKLISTS.get(category, [])
        
        # Tạo dữ liệu checklist ban đầu (trạng thái 'waiting')
        initial_data = []
        for item in template:
            initial_data.append({
                "task_id": item["id"],
                "task_name": item["task"],
                "status": "waiting",
                "robot_log": "",
                "human_note": ""
            })
            
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

    def run_auto_audit(self, session_id: int):
        """Robot thực hiện đọc file và điền kết quả"""
        session = self.db.query(AuditSession).filter(AuditSession.id == session_id).first()
        if not session: return None

        # Logic giả định: Robot sẽ lấy file từ Drive dựa trên session.folder_id
        # Sau đó duyệt qua từng dòng trong session.checklist_data để update
        
        current_data = list(session.checklist_data)
        for task in current_data:
            if task["task_id"] == "check_files":
                # Ví dụ logic: Quét Drive thấy đủ file thì PASS
                task["status"] = "pass"
                task["robot_log"] = "Tìm thấy file TK-VAT và BK-VAT"
            
            if task["task_id"] == "match_tax":
                # Ví dụ logic: Giả sử Robot đọc được XML=100tr, Excel=100tr
                task["status"] = "pass"
                task["robot_log"] = "Số liệu khớp: 100,000,000đ"

        # Lưu lại kết quả sau khi Robot quét xong
        session.checklist_data = current_data
        session.status = "done"
        self.db.commit()
        return session