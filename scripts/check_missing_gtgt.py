import os
import sys
import time
import argparse
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env

# Buộc ứng dụng tắt chế độ Docker trên Local Terminal
os.environ["DOCKER"] = "false"

# Thêm đường dẫn gốc của project vào sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from app.models.audit import AuditSession           # type: ignore
from app.core.config import settings                # type: ignore
from app.db.repositories.folder_repo import FolderRepository  # type: ignore
from app.services.drive_service import (            # type: ignore
    get_drive_service,
    find_child_folder_by_name_contain,
    find_child_folder_exact,
    get_all_files_recursive,
)

# ---------------------------------------------------------------------------
# Khởi tạo DB — MySQL trước, fallback SQLite nếu lỗi
# ---------------------------------------------------------------------------
SQLITE_PATH = os.path.join(parent_dir, "cenvi_audit.db")

def _create_session() -> tuple[Session, str]:
    """
    Thử kết nối MySQL. Nếu lỗi -> fallback SQLite.
    Trả về (session, db_type) với db_type là "mysql" hoặc "sqlite".
    """
    mysql_url = os.getenv("DATABASE_URL") or (
        f"mysql+pymysql://{os.getenv('DB_USER','root')}:{os.getenv('DB_PASSWORD','')}@"
        f"{os.getenv('DB_HOST','127.0.0.1')}:{os.getenv('DB_PORT','3306')}/{os.getenv('DB_NAME','cenvi')}"
    )
    try:
        engine = create_engine(mysql_url, connect_args={"connect_timeout": 5})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))  # Kiểm tra kết nối thật sự
        SessionFactory = sessionmaker(bind=engine)
        print(f"✅ Kết nối MySQL thành công: {mysql_url.split('@')[-1]}")
        return SessionFactory(), "mysql"
    except Exception as e:
        print(f"⚠️  MySQL lỗi: {e}")
        print(f"⚠️  Fallback sang SQLite: {SQLITE_PATH}")
        sqlite_engine = create_engine(f"sqlite:///{SQLITE_PATH}")
        AuditSession.__table__.create(sqlite_engine, checkfirst=True)  # Tạo bảng nếu chưa có
        SessionFactory = sessionmaker(bind=sqlite_engine)
        return SessionFactory(), "sqlite"

# ---------------------------------------------------------------------------
# Cấu hình retry cho Google Drive API
# ---------------------------------------------------------------------------
DRIVE_RETRY_TIMES = 3       # Số lần thử lại khi Drive API lỗi
DRIVE_RETRY_DELAY = 3       # Giây chờ giữa các lần thử


# ---------------------------------------------------------------------------
# Wrapper retry cho các hàm gọi Drive API
# ---------------------------------------------------------------------------
def _call_with_retry(func, *args, **kwargs):
    """Gọi hàm Drive API, tự retry khi gặp lỗi tạm thời."""
    last_error = None
    for attempt in range(1, DRIVE_RETRY_TIMES + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_error = e
            print(f"   -> [RETRY {attempt}/{DRIVE_RETRY_TIMES}] Drive API lỗi: {e}. Thử lại sau {DRIVE_RETRY_DELAY}s...")
            time.sleep(DRIVE_RETRY_DELAY)
    raise last_error


# ---------------------------------------------------------------------------
# Helpers tìm folder
# ---------------------------------------------------------------------------
def _find_first_by_keywords(service, parent_id, keywords):
    if not parent_id:
        return None
    for keyword in keywords:
        found = _call_with_retry(find_child_folder_by_name_contain, service, parent_id, keyword)
        if found:
            return found
    return None


def _find_quarter_folder(service, parent_id, q):
    candidates = [
        f"QUY {q}", f"QUY-{q}", f"QUY_{q}", f"Q{q}",
        f"QUÝ {q}", f"QUY{q}", f"QUÝ{q}",
    ]
    return _find_first_by_keywords(service, parent_id, candidates)


# ---------------------------------------------------------------------------
# Hàm tìm folder GTGT — tách riêng để logic rõ ràng hơn
# ---------------------------------------------------------------------------
def _find_gtgt_folder(service, f_thue_id, year):
    """
    Tìm folder GIA-TRI-GIA-TANG theo thứ tự ưu tiên:
      1. TAI-LIEU-THUE / {year} / GIA-TRI-GIA-TANG
      2. TAI-LIEU-THUE / GIA-TRI-GIA-TANG  (fallback, log warning)
    Trả về (folder | None, found_in_year_folder: bool)
    """
    # Bước 1: tìm folder năm
    f_year = _call_with_retry(find_child_folder_exact, service, f_thue_id, str(year))
    if not f_year:
        f_year = _call_with_retry(find_child_folder_by_name_contain, service, f_thue_id, str(year))

    if f_year:
        f_gtgt = _call_with_retry(find_child_folder_by_name_contain, service, f_year["id"], "GIA-TRI-GIA-TANG")
        if f_gtgt:
            return f_gtgt, True   # tìm thấy đúng trong folder năm
        print(f"   -> [INFO] Khong tim thay GIA-TRI-GIA-TANG trong folder nam {year}. Fallback len TAI-LIEU-THUE.")
    else:
        print(f"   -> [INFO] Khong tim thay folder nam {year} trong TAI-LIEU-THUE. Fallback len TAI-LIEU-THUE.")

    # Bước 2: fallback — tìm trong TAI-LIEU-THUE (có thể tìm thấy folder năm khác, log rõ)
    f_gtgt = _call_with_retry(find_child_folder_by_name_contain, service, f_thue_id, "GIA-TRI-GIA-TANG")
    if f_gtgt:
        print(f"   -> [WARNING] Dang dung folder GIA-TRI-GIA-TANG FALLBACK (co the chua du lieu nam khac): {f_gtgt.get('name')}")
    return f_gtgt, False


# ---------------------------------------------------------------------------
# Hàm chính
# ---------------------------------------------------------------------------
def check_missing_gtgt(year: int, period: str):
    settings.DOCKER = False

    print(f"Bat dau chay Script: Kiem tra THIEU file GTGT cho Nam {year} - {period}")
    db, db_type = _create_session()
    print(f"📦 Đang dùng DB: {db_type.upper()}")
    folder_repo = FolderRepository()

    try:
        service = get_drive_service()
    except Exception as e:
        print(f"❌ Lỗi kết nối Google Drive: {e}")
        db.close()
        return

    all_folders = folder_repo.get_all()
    q_num = period.replace("Q", "").replace("q", "").strip()

    count_ok       = 0   # Có đủ dữ liệu, không cần update DB
    count_missing  = 0   # Thiếu / rỗng -> đánh warning
    count_skipped  = 0   # Bỏ qua (đã có trạng thái hoặc lỗi cấu hình)
    count_error    = 0   # Lỗi Drive API sau khi retry hết

    for idx, folder in enumerate(all_folders, 1):
        f_id    = getattr(folder, "id", None)            or folder.get("id")
        c_code  = getattr(folder, "company_code", None)  or folder.get("company_code")
        c_name  = getattr(folder, "company_name", None)  or folder.get("company_name")
        root_id = getattr(folder, "root_folder_id", None) or folder.get("root_folder_id")

        print(f"\n[{idx}/{len(all_folders)}] Dang xu ly: {c_code} - {c_name}")

        # --- Bỏ qua nếu chưa cấu hình Drive ---
        if not root_id:
            print("   -> Bo qua vi khong co root_folder_id tren Drive.")
            count_skipped += 1
            continue

        # --- Kiểm tra trạng thái hiện tại trong CSDL ---
        session = db.query(AuditSession).filter(
            AuditSession.folder_id == f_id,
            AuditSession.category  == "GTGT",
            AuditSession.year      == year,
            AuditSession.period    == period,
        ).first()

        if session and session.status and session.status != "empty":
            print(f"   -> Da co trang thai ({session.status}). Bo qua.")
            count_skipped += 1
            continue

        session_id = getattr(session, "id", None) if session else None

        # --- Quét Drive ---
        try:
            # 1. Tìm TAI-LIEU-THUE
            f_thue = _find_first_by_keywords(service, root_id, ["TAI-LIEU-THUE", "THUE"])
            if not f_thue:
                print("   -> [WARNING] Khong tim thay nhanh TAI-LIEU-THUE. Danh dau warning thieu file.")
                _mark_as_missing(db, f_id, year, period, session_id)
                count_missing += 1
                continue

            # 2. Tìm GIA-TRI-GIA-TANG (có retry + log rõ khi fallback)
            f_gtgt, in_year_folder = _find_gtgt_folder(service, f_thue["id"], year)
            if not f_gtgt:
                print("   -> [WARNING] Khong tim thay nhanh GIA-TRI-GIA-TANG. Danh dau warning thieu file.")
                _mark_as_missing(db, f_id, year, period, session_id)
                count_missing += 1
                continue

            # 3. Tìm folder Quý
            f_quarter = _find_quarter_folder(service, f_gtgt["id"], q_num)

            if f_quarter:
                print(f"   -> Da tim thay folder Quy: {f_quarter['name']}")
                raw_files = _call_with_retry(get_all_files_recursive, service, f_quarter["id"])
            else:
                print("   -> Khong co folder Quy, quet toan bo GIA-TRI-GIA-TANG")
                raw_files = _call_with_retry(get_all_files_recursive, service, f_gtgt["id"])

            # 4. Kiểm tra có file hay không
            if len(raw_files) == 0:
                print("   -> [WARNING] RONG (0 file). Danh dau warning thieu file.")
                _mark_as_missing(db, f_id, year, period, session_id)
                count_missing += 1
            else:
                print(f"   -> [OK] Co du lieu ({len(raw_files)} files). Khong thay doi trang thai.")
                count_ok += 1

        except Exception as e:
            # Sau khi đã retry hết mà vẫn lỗi -> log, không đánh warning tránh false-positive
            print(f"   -> ❌ Loi Drive API sau khi retry: {e}. Bo qua cong ty nay.")
            count_error += 1
            continue

    db.close()

    print("\n" + "=" * 50)
    print(f"TONG KET (DB: {db_type.upper()}):")
    print(f"  Tong so cong ty            : {len(all_folders)}")
    print(f"  Bo qua (da co trang thai)  : {count_skipped}")
    print(f"  Co du data (khong update)  : {count_ok}")
    print(f"  Thieu / rong (warning)     : {count_missing}")
    print(f"  Loi Drive API (skip)       : {count_error}")
    print("=" * 50)


# ---------------------------------------------------------------------------
# Cập nhật DB status = warning
# ---------------------------------------------------------------------------
def _mark_as_missing(
    db: Session,
    folder_id: int,
    year: int,
    period: str,
    session_id: int | None = None,
):
    """Cập nhật hoặc tạo mới AuditSession với status = warning."""
    try:
        if session_id:
            audit_sess = db.query(AuditSession).filter(AuditSession.id == session_id).first()
            if audit_sess:
                audit_sess.status       = "warning"
                audit_sess.overall_note = "[Hệ thống] Tự động quét: Không tìm thấy file tờ khai/folder rỗng."
                audit_sess.updated_at   = datetime.utcnow()
                db.commit()
                print(f"   -> ✅ DB cập nhật (UPDATE) AuditSession id={session_id} -> warning")
        else:
            audit_sess = AuditSession(
                folder_id      = folder_id,
                category       = "GTGT",
                year           = year,
                period         = period,
                status         = "warning",
                checklist_data = [],
                overall_note   = "[Hệ thống] Tự động quét: Không tìm thấy file tờ khai/folder rỗng.",
            )
            db.add(audit_sess)
            db.commit()
            db.refresh(audit_sess)
            print(f"   -> ✅ DB ghi mới (INSERT) AuditSession id={audit_sess.id}, folder_id={folder_id}, {year}-{period} -> warning")
    except Exception as e:
        print(f"   -> ❌ Lỗi khi lưu DB: {e}")
        db.rollback()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kiem tra thieu file GTGT tren Drive.")
    parser.add_argument(
        "--year",
        type=int,
        default=datetime.now().year,
        help="Nam can kiem tra (Vi du: 2024)",
    )
    parser.add_argument(
        "--period",
        type=str,
        default=None,
        help="Quy can kiem tra (Vi du: Q1, Q2, Q3, Q4). Bo trong de check ca 4 quy.",
    )

    args = parser.parse_args()

    if args.period:
        # Chạy 1 quý cụ thể
        check_missing_gtgt(args.year, args.period.upper())
    else:
        # Chạy cả 4 quý
        quarters = ["Q1", "Q2", "Q3", "Q4"]
        print(f"\n{'='*50}")
        print(f"BAT DAU KIEM TRA CA 4 QUY NAM {args.year}")
        print(f"{'='*50}\n")

        for q in quarters:
            print(f"\n{'#'*50}")
            print(f"# DANG CHAY: {q} - NAM {args.year}")
            print(f"{'#'*50}")
            check_missing_gtgt(args.year, q)

        print(f"\n{'='*50}")
        print(f"HOAN THANH KIEM TRA CA 4 QUY NAM {args.year}")
        print(f"{'='*50}")