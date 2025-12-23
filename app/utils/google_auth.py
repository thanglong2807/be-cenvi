import os
import pickle
import json
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2 import service_account  # <--- Thêm thư viện này
from app.core.config import settings

def get_drive_service():
    creds = None
    
    # 1. Kiểm tra xem file Credentials là loại nào
    if not os.path.exists(settings.CREDENTIALS_PATH):
        raise FileNotFoundError(f"Không tìm thấy file: {settings.CREDENTIALS_PATH}")

    # Đọc file để xác định loại (Service Account hay OAuth Client)
    with open(settings.CREDENTIALS_PATH, 'r', encoding='utf-8') as f:
        key_data = json.load(f)
        is_service_account = key_data.get('type') == 'service_account'

    # --- TRƯỜNG HỢP 1: DÙNG SERVICE ACCOUNT (File bạn đang có) ---
    if is_service_account:
        print("🔑 Đang sử dụng: Service Account Credentials")
        creds = service_account.Credentials.from_service_account_info(
            key_data, 
            scopes=settings.SCOPES
        )
    
    # --- TRƯỜNG HỢP 2: DÙNG OAUTH USER (Đăng nhập trình duyệt) ---
    else:
        print("👤 Đang sử dụng: OAuth 2.0 User Credentials")
        # Kiểm tra token cũ
        if os.path.exists(settings.TOKEN_PATH):
            with open(settings.TOKEN_PATH, "rb") as token:
                creds = pickle.load(token)

        # Nếu không có token hoặc hết hạn thì login lại
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    settings.CREDENTIALS_PATH, settings.SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Lưu token mới
            with open(settings.TOKEN_PATH, "wb") as token:
                pickle.dump(creds, token)

    return build("drive", "v3", credentials=creds)