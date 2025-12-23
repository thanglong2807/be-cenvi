# app/services/drive_service.py
from datetime import datetime
from googleapiclient.errors import HttpError
from app.utils.google_auth import get_drive_service
from app.core.config import settings
from app.data.employees import EMPLOYEES_DATA
from app.schemas.drive_schema import SyncResponse, DriveItem

class DriveSearchService:
    def __init__(self):
        self.service = get_drive_service()
        # --- LOGIC MỚI: Tự động tạo map Email -> ID từ dữ liệu JSON ---
        self.employee_mapping = {}
        if "items" in EMPLOYEES_DATA:
            for emp in EMPLOYEES_DATA["items"]:
                email = emp.get("email", "").lower()
                emp_id = emp.get("id")
                if email and emp_id:
                    self.employee_mapping[email] = emp_id
        # -------------------------------------------------------------

    def _get_folder_manager(self, folder_id: str) -> int:
        """Tìm ID nhân viên quản lý folder"""
        try:
            results = self.service.permissions().list(
                fileId=folder_id,
                fields="permissions(emailAddress, role)",
                supportsAllDrives=True
            ).execute()
            
            for p in results.get('permissions', []):
                email = p.get('emailAddress', '').lower()
                role = p.get('role')
                if role in ['fileOrganizer', 'organizer', 'writer']:
                    # Tra cứu trong self.employee_mapping đã tạo ở __init__
                    if email in self.employee_mapping:
                        return self.employee_mapping[email]
            return 1 # Fallback ID
        except Exception:
            return 1

    def scan_and_parse(self) -> SyncResponse:
        folders = []
        page_token = None
        
        # 1. Quét toàn bộ folder
        while True:
            try:
                res = self.service.files().list(
                    q=f"'{settings.ROOT_FOLDER_ID}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
                    corpora="allDrives", includeItemsFromAllDrives=True, supportsAllDrives=True,
                    pageSize=1000, fields="nextPageToken, files(id, name, createdTime)", pageToken=page_token
                ).execute()
                folders.extend(res.get('files', []))
                page_token = res.get('nextPageToken')
                if not page_token: break
            except Exception as e:
                print(f"Error scanning: {e}")
                break

        # 2. Xử lý dữ liệu
        items = []
        current_id = 1
        current_ts = datetime.now().isoformat()

        for f in folders:
            folder_name = f["name"]
            folder_id = f["id"]
            
            # 2a. Check permission
            manager_id = self._get_folder_manager(folder_id)

            # 2b. Parse tên (Mã_Tên_MST)
            parts = folder_name.split('_')
            if len(parts) >= 3:
                code, mst, name = parts[0].strip(), parts[-1].strip(), "_".join(parts[1:-1]).strip()
            elif len(parts) == 2:
                code, name, mst = parts[0].strip(), parts[1].strip(), ""
            else:
                code, name, mst = folder_name, folder_name, ""
            
            # 2c. Năm
            try:
                year = int(f.get("createdTime", "")[:4])
            except:
                year = datetime.now().year

            item = DriveItem(
                id=current_id,
                company_code=code,
                company_name=name,
                mst=mst,
                manager_employee_id=manager_id,
                root_folder_id=folder_id,
                year=year,
                template="STANDARD",
                status="active",
                created_at=current_ts,
                updated_at=current_ts
            )
            items.append(item)
            current_id += 1
            
        return SyncResponse(last_id=current_id - 1 if items else 0, items=items)

# Tạo instance
drive_search_service = DriveSearchService()