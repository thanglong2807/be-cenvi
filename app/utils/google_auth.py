import os
import pickle
import json
import sys
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from app.core.config import settings

def get_drive_service():
    creds = None
    
    # [DEBUG] In ra đường dẫn hiện tại để kiểm tra trên Render
    print(f"🔍 [AUTH DEBUG] Đang tìm credentials tại: '{settings.CREDENTIALS_PATH}'")
    print(f"📂 [AUTH DEBUG] Thư mục hiện tại (CWD): '{os.getcwd()}'")

    # 1. Kiểm tra file tồn tại
    if not os.path.exists(settings.CREDENTIALS_PATH):
        # Liệt kê các file trong thư mục credentials để debug
        cred_dir = os.path.dirname(settings.CREDENTIALS_PATH)
        if os.path.exists(cred_dir):
            print(f"📂 File trong thư mục '{cred_dir}': {os.listdir(cred_dir)}")
        else:
            print(f"❌ Thư mục '{cred_dir}' không tồn tại!")
            
        raise FileNotFoundError(f"❌ CRITICAL ERROR: Không tìm thấy file credentials tại {settings.CREDENTIALS_PATH}. Hãy kiểm tra lại biến môi trường hoặc Secret Files.")

    # 2. Đọc file JSON
    try:
        with open(settings.CREDENTIALS_PATH, 'r', encoding='utf-8') as f:
            key_data = json.load(f)
            
        # Kiểm tra loại key
        is_service_account = key_data.get('type') == 'service_account'
        
    except json.JSONDecodeError:
        raise ValueError(f"❌ File {settings.CREDENTIALS_PATH} không phải là JSON hợp lệ. Kiểm tra lại nội dung copy-paste.")

    # --- TRƯỜNG HỢP 1: SERVICE ACCOUNT (Khuyên dùng cho Server) ---
    if is_service_account:
        print(f"✅ [AUTH] Đang dùng Service Account: {key_data.get('client_email')}")
        creds = service_account.Credentials.from_service_account_info(
            key_data, 
            scopes=settings.SCOPES
        )
    
    # --- TRƯỜNG HỢP 2: OAUTH CLIENT (Nguy hiểm trên Server) ---
    else:
        print("⚠️ [AUTH] Đang dùng OAuth Client (User Mode).")
        
        # Kiểm tra token
        if os.path.exists(settings.TOKEN_PATH):
            print("   -> Tìm thấy token.pickle")
            with open(settings.TOKEN_PATH, "rb") as token:
                creds = pickle.load(token)
        else:
            print("   -> Không thấy token.pickle")

        # Refresh hoặc Login
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("   -> Token hết hạn, đang refresh...")
                creds.refresh(Request())
            else:
                # --- CHẶN ĐỨNG LỖI TRÊN SERVER TẠI ĐÂY ---
                # Nếu đang chạy trên Server mà đòi mở trình duyệt -> Báo lỗi ngay thay vì treo máy
                # Cách nhận biết Server đơn giản: check biến môi trường RENDER (hoặc CI/CD)
                if os.environ.get("RENDER") or os.environ.get("DYNO"): # Render hoặc Heroku
                    raise RuntimeError("❌ LỖI NGHIÊM TRỌNG: Bạn đang dùng OAuth Client trên Server nhưng Token đã hết hạn hoặc không tồn tại. Server không thể mở trình duyệt để login. Vui lòng chuyển sang dùng Service Account.")
                
                # Nếu là Local thì mới cho mở trình duyệt
                print("🌐 Đang mở trình duyệt để đăng nhập...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    settings.CREDENTIALS_PATH, settings.SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Lưu token (chỉ hoạt động nếu thư mục có quyền ghi)
            try:
                with open(settings.TOKEN_PATH, "wb") as token:
                    pickle.dump(creds, token)
            except Exception as e:
                print(f"⚠️ Không thể lưu token mới (có thể do permission): {e}")

    return build("drive", "v3", credentials=creds)