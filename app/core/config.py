import os
from typing import List, Optional # <--- Nhớ import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # --- 1. CẤU HÌNH APP ---
    APP_NAME: str = "Cenvi Drive Backend"
    APP_ENV: str = "local"
    APP_DEBUG: bool = True
    
    # --- 2. DATABASE (ĐÃ SỬA) ---
    # Optional[str] = None nghĩa là: Có cũng được, không có thì bằng None
    DATABASE_URL: Optional[str] = None 

    # --- 3. CẤU HÌNH GOOGLE (TỪ .ENV) ---
    # Bắt buộc phải có đường dẫn file key
    GOOGLE_SERVICE_ACCOUNT_FILE: str = Field(..., env="GOOGLE_SERVICE_ACCOUNT_FILE")
    
    # Scope mặc định
    GOOGLE_DRIVE_SCOPES: str = "https://www.googleapis.com/auth/drive"

    # ID Folder gốc (Bắt buộc)
    ROOT_DRIVE_FOLDER_ID: str = Field(..., env="ROOT_DRIVE_FOLDER_ID")
    
    # Folder cha (Không bắt buộc, để chuỗi rỗng nếu không dùng)
    COMPANY_PARENT_FOLDER_ID: str = ""

    # --- 4. CẤU HÌNH TOKEN MỚI ---
    # Nơi lưu file token.pickle (tự động tạo)
    TOKEN_PATH: str = os.path.join("credentials", "token.pickle")
    # File này sẽ chứa dữ liệu sau khi bấm "Xác nhận"
    STORAGE_PATH: str = os.path.join("app", "data", "companies_storage.json")
    # --- 5. CẦU NỐI (ALIAS) CHO CODE MỚI ---
    @property
    def CREDENTIALS_PATH(self) -> str:
        # Trả về giá trị của biến cũ
        return self.GOOGLE_SERVICE_ACCOUNT_FILE

    @property
    def ROOT_FOLDER_ID(self) -> str:
        # Trả về giá trị của biến cũ
        return self.ROOT_DRIVE_FOLDER_ID
    
    @property
    def SCOPES(self) -> List[str]:
        # Chuyển chuỗi thành List cho thư viện Google
        return [self.GOOGLE_DRIVE_SCOPES]

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore" # Quan trọng: Bỏ qua các biến thừa trong .env để không lỗi

settings = Settings()