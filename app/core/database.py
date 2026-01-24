from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Tạo file database.db ngay tại thư mục gốc
SQLALCHEMY_DATABASE_URL = "sqlite:///./cenvi_audit.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Hàm helper để lấy session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()