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