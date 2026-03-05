import os
import io
from typing import Tuple
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from fastapi import HTTPException

# Cấu hình Scopes
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")

class DocumentDriveService:
    """
    Service chuyên biệt cho module Quản lý tài liệu (CENVI Docs).
    Chịu trách nhiệm: Tạo Folder Danh mục/Dự án, Upload file phiên bản, Đổi tên file cũ.
    """
    
    def __init__(self):
        self._service = self._get_drive_client()
        self._mock_id_counter = 1
        
        if not self._service:
            print("⚠️ DocumentDriveService: Chạy chế độ MOCK (Không tìm thấy Credentials).")
            self._is_mock = True
        else:
            self._is_mock = False

    def _get_drive_client(self):
        """Hàm nội bộ để khởi tạo kết nối Google Drive"""
        creds_path = SERVICE_ACCOUNT_FILE
        if not creds_path or not os.path.exists(creds_path):
            return None
        try:
            creds = service_account.Credentials.from_service_account_file(
                creds_path, scopes=SCOPES
            )
            return build('drive', 'v3', credentials=creds)
        except Exception as e:
            print(f"❌ Lỗi khởi tạo Drive Client: {e}")
            return None

    # =========================================================================
    # CÁC CHỨC NĂNG CORE
    # =========================================================================

    def create_folder(self, folder_name: str, parent_id: str) -> str:
        """
        Tạo folder mới nằm trong parent_id. Trả về ID của folder vừa tạo.
        """
        if self._is_mock:
            mock_id = f"mock_folder_{self._mock_id_counter}_{int(datetime.now().timestamp())}"
            self._mock_id_counter += 1
            print(f"[MOCK DRIVE] Created folder '{folder_name}' inside '{parent_id}' -> ID: {mock_id}")
            return mock_id

        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id]
            }
            folder = self._service.files().create(
                body=file_metadata,
                fields='id',
                supportsAllDrives=True
            ).execute()
            
            print(f"✅ Đã tạo folder: {folder_name} (ID: {folder.get('id')})")
            return folder.get('id')
        except Exception as e:
            print(f"❌ Lỗi tạo folder '{folder_name}': {e}")
            raise HTTPException(status_code=500, detail=f"Google Drive Error: {str(e)}")

    async def upload_file(self, file_data: bytes, folder_id: str, original_name: str, version: float) -> Tuple[str, str]:
        """
        Upload file lên folder_id và đổi tên theo chuẩn version: [Name]_v[Ver].[ext]
        """
        # Xử lý tên file
        name_parts = original_name.rsplit('.', 1)
        name_base = name_parts[0]
        name_ext = name_parts[1] if len(name_parts) > 1 else ''
        file_name_on_drive = f"{name_base}_v{version:.1f}.{name_ext}"
        
        if self._is_mock:
            mock_id = f"mock_file_{self._mock_id_counter}_{int(datetime.now().timestamp())}"
            self._mock_id_counter += 1
            print(f"[MOCK DRIVE] Uploaded '{file_name_on_drive}' to '{folder_id}'")
            return mock_id, file_name_on_drive

        try:
            file_metadata = {
                'name': file_name_on_drive,
                'parents': [folder_id]
            }
            
            media = MediaIoBaseUpload(
                io.BytesIO(file_data), 
                mimetype='application/octet-stream',
                resumable=True
            )
            
            file = self._service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name',
                supportsAllDrives=True
            ).execute()
            
            return file.get('id'), file.get('name')
        except Exception as e:
            print(f"❌ Lỗi Upload file: {e}")
            raise HTTPException(status_code=500, detail=f"Google Drive Upload Error: {str(e)}")

    async def rename_file(self, file_id: str, new_name: str):
        """
        Đổi tên file cũ (Dùng khi update version mới).
        """
        if self._is_mock:
            print(f"[MOCK DRIVE] Renamed '{file_id}' to '{new_name}'")
            return True
            
        try:
            self._service.files().update(
                fileId=file_id,
                body={'name': new_name},
                supportsAllDrives=True
            ).execute()
            return True
        except Exception as e:
            print(f"❌ Lỗi Rename file {file_id}: {e}")
            return False

    def delete_file(self, file_id: str) -> bool:
        """
        Xóa file/folder trên Google Drive.
        Returns: True nếu xóa thành công, False nếu lỗi
        """
        if self._is_mock:
            print(f"[MOCK DRIVE] Deleted file '{file_id}'")
            return True
            
        try:
            self._service.files().delete(
                fileId=file_id,
                supportsAllDrives=True
            ).execute()
            print(f"✅ Đã xóa file/folder trên Drive: {file_id}")
            return True
        except Exception as e:
            print(f"❌ Lỗi xóa file {file_id}: {e}")
            return False