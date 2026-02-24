from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from app.core.config import settings

# DATABASE_URL đã được chuẩn hóa trong settings (hỗ trợ Supabase + SQLite fallback)
DEFAULT_SQLITE_URL = "sqlite:///./cenvi_audit.db"
SQLALCHEMY_DATABASE_URL = settings.SQLALCHEMY_DATABASE_URL


def _build_engine(database_url: str):
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args)


def _resolve_engine_with_fallback():
    global SQLALCHEMY_DATABASE_URL

    primary_url = SQLALCHEMY_DATABASE_URL
    engine = _build_engine(primary_url)

    try:
        with engine.connect():
            pass
        return engine
    except SQLAlchemyError as exc:
        if primary_url.startswith("sqlite"):
            raise

        fallback_url = DEFAULT_SQLITE_URL
        print(f"⚠️ Không kết nối được DB chính ({primary_url}). Chuyển sang SQLite ({fallback_url}). Lỗi: {exc}")
        SQLALCHEMY_DATABASE_URL = fallback_url
        fallback_engine = _build_engine(fallback_url)
        with fallback_engine.connect():
            pass
        return fallback_engine

engine = _resolve_engine_with_fallback()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Hàm helper để lấy session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()