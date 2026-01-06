# File: app/services/drive_service.py

import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Các biến môi trường hoặc config credential
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE") # hoặc lấy từ env

def get_drive_service():
    """
    Khởi tạo Google Drive Service sử dụng Service Account
    """
    # 1. Lấy đường dẫn file JSON từ .env
    creds_path = SERVICE_ACCOUNT_FILE

    if not creds_path or not os.path.exists(creds_path):
        raise FileNotFoundError(f"Không tìm thấy file credentials tại: {creds_path}. Hãy kiểm tra file .env")

    # 2. Load credentials
    creds = service_account.Credentials.from_service_account_file(
        creds_path, 
        scopes=SCOPES
    )

    # 3. Build service
    service = build('drive', 'v3', credentials=creds)
    
    return service

def add_permission(service, file_id, email, role="writer"):
    """
    role: 'reader', 'writer' (Editor), 'organizer' (Manager trong Shared Drive)
    """
    try:
        service.permissions().create(
            fileId=file_id,
            body={
                "role": role,
                "type": "user",
                "emailAddress": email
            },
            supportsAllDrives=True,
            sendNotificationEmail=True  # Gửi mail báo cho nhân viên mới
        ).execute()
    except Exception as e:
        print(f"Lỗi add_permission {file_id}: {e}")

def remove_permission_by_email(service, file_id, email):
    """
    Drive API bắt buộc xóa bằng permission_id, không xóa được bằng email trực tiếp.
    Nên phải tìm ID trước.
    """
    try:
        # 1. Tìm permission_id của email này
        permissions = service.permissions().list(
            fileId=file_id,
            fields="permissions(id, emailAddress)",
            supportsAllDrives=True
        ).execute()

        perm_id = None
        for p in permissions.get('permissions', []):
            if p.get('emailAddress', '').lower() == email.lower():
                perm_id = p['id']
                break
        
        # 2. Xóa nếu tìm thấy
        if perm_id:
            service.permissions().delete(
                fileId=file_id,
                permissionId=perm_id,
                supportsAllDrives=True
            ).execute()
    except Exception as e:
        print(f"Lỗi remove_permission {file_id}: {e}")

def create_drive_shortcut(service, target_id, parent_id, name):
    """
    Tạo shortcut trỏ đến target_id, đặt trong parent_id
    """
    try:
        service.files().create(
            body={
                "name": name, # Tên shortcut (thường đặt giống tên folder gốc)
                "mimeType": "application/vnd.google-apps.shortcut",
                "parents": [parent_id],
                "shortcutDetails": {
                    "targetId": target_id
                }
            },
            supportsAllDrives=True
        ).execute()
    except Exception as e:
        print(f"Lỗi tạo shortcut: {e}")