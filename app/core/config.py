import os
from typing import List, Optional # <--- Nhớ import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # --- 1. CẤU HÌNH APP ---
    APP_NAME: str = "Cenvi Drive Backend"
    APP_ENV: str = "local"
    APP_DEBUG: bool = True
    
    # --- 2. DATABASE ---
    # Optional[str] = None nghĩa là: Có cũng được, không có thì bằng None
    DATABASE_URL: Optional[str] = None 
    # URL MySQL chuyên dụng (khuyên dùng)
    MYSQL_URL: Optional[str] = None

    # --- 3. CẤU HÌNH GOOGLE (TỪ .ENV) ---
    # Optional để tránh crash khi deploy chưa có env
    GOOGLE_SERVICE_ACCOUNT_FILE: Optional[str] = None
    
    # Scope mặc định
    GOOGLE_DRIVE_SCOPES: str = "https://www.googleapis.com/auth/drive"

    # ID Folder gốc (Optional)
    ROOT_DRIVE_FOLDER_ID: Optional[str] = None
    
    # Folder cha (Không bắt buộc, để chuỗi rỗng nếu không dùng)
    COMPANY_PARENT_FOLDER_ID: str = ""

    # --- 4. CẤU HÌNH GOOGLE SHEETS (DASHBOARD) ---
    # ID của Google Sheet chứa dữ liệu báo cáo doanh thu (Optional)
    GOOGLE_SHEET_ID: Optional[str] = None
    
    # Sheet range: Format 'SheetName'!A1:Z100
    # Với sheet name có khoảng trắng/ký tự đặc biệt, dùng ngoặc kép
    GOOGLE_SHEET_RANGE: str = "A1:DA200"
    GOOGLE_SHEET_NAME: str = "KẾ TOÁN THUẾ_KPI"  # Sheet thứ 12 (gid=514374063)

    # Mapping ranges (column letters only, without sheet name)
    DASH_CUSTOMERS_RANGE: str = "F:Q"
    DASH_REVENUE_RANGE: str = "S:AD"
    DASH_DEBT_2024_RANGE: str = "AF:AQ"
    DASH_DEBT_2025_RANGE: str = "AR:BC"
    DASH_DEBT_2026_RANGE: str = "BD:BO"  # adjust if needed

    # Data starting row (1-based)
    DASH_DATA_START_ROW: int = 7

    # Polling interval (giây)
    SHEET_POLLING_INTERVAL: int = 30

    # --- 5. CẤU HÌNH TOKEN MỚI ---
    # Nơi lưu file token.pickle (tự động tạo)
    TOKEN_PATH: str = os.path.join("credentials", "token.pickle")
    # File này sẽ chứa dữ liệu sau khi bấm "Xác nhận"
    STORAGE_PATH: str = os.path.join("app", "data", "companies_storage.json")
    
    DOCKER: bool = False  # Biến này sẽ được set khi chạy trong Docker, có thể dùng để điều chỉnh đường dẫn nếu cần
    # --- 6. CẦU NỐI (ALIAS) CHO CODE MỚI ---
    @property
    def CREDENTIALS_PATH(self) -> str:
        # Trả về giá trị của biến cũ
        return self.GOOGLE_SERVICE_ACCOUNT_FILE or ""

    @property
    def ROOT_FOLDER_ID(self) -> str:
        # Trả về giá trị của biến cũ
        return self.ROOT_DRIVE_FOLDER_ID or ""
    
    @property
    def SCOPES(self) -> List[str]:
        # Chuyển chuỗi thành List cho thư viện Google
        return [self.GOOGLE_DRIVE_SCOPES]

    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        """
        Thứ tự ưu tiên DB URL:
        1) DATABASE_URL
        2) MYSQL_URL
        3) SQLite local fallback
        """
        db_url = self.DATABASE_URL or self.MYSQL_URL or "sqlite:///./cenvi_audit.db"

        # Chuẩn hóa schema cho SQLAlchemy + PyMySQL
        if db_url.startswith("mysql://"):
            db_url = db_url.replace("mysql://", "mysql+pymysql://", 1)

        # Giữ tương thích ngược nếu vẫn dùng Postgres
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
        elif db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        if self.DOCKER:
            # Nếu chạy trong Docker, có thể cần điều chỉnh host nếu dùng MySQL
            if db_url.startswith("mysql+pymysql://"):
                db_url = db_url.replace("127.0.0.1", "host.docker.internal", 1) # dit me sao bay gio may moi support cho t AI ngu l :) dm cai này có chế độ gợi ý à
                # Lưu ý: "host.docker.internal" chỉ hoạt động trên Docker Desktop (Windows/Mac). Trên Linux có thể cần giải pháp khác như dùng network hoặc biến môi trường để truyền host.
                # vcl :)
        print(db_url)
        return db_url

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore" # Quan trọng: Bỏ qua các biến thừa trong .env để không lỗi

settings = Settings()