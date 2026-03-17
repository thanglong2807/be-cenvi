#!/usr/bin/env python3
"""
Script kiểm tra folder KẾ TOÁN trên Drive.
Nếu tổng số file < 4 -> đánh warning.
Nếu >= 4 file -> ghi nhận OK, không đổi trạng thái (kiểm tra thủ công).
"""

import sys
import os
import time
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Fix Unicode encoding for Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

load_dotenv()

# Buộc ứng dụng tắt chế độ Docker trên Local Terminal
os.environ["DOCKER"] = "false"

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir  = os.path.dirname(current_dir)
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
# Ngưỡng tối thiểu: < MIN_FILES -> warning
# ---------------------------------------------------------------------------
MIN_FILES = 4

# ---------------------------------------------------------------------------
# DB — MySQL trước, fallback SQLite
# ---------------------------------------------------------------------------
SQLITE_PATH = os.path.join(parent_dir, "cenvi_audit.db")

def _create_session() -> tuple[Session, str]:
    mysql_url = os.getenv("DATABASE_URL") or (
        f"mysql+pymysql://{os.getenv('DB_USER','root')}:{os.getenv('DB_PASSWORD','')}@"
        f"{os.getenv('DB_HOST','127.0.0.1')}:{os.getenv('DB_PORT','3307')}/{os.getenv('DB_NAME','cenvi_audit')}"
    )
    if mysql_url.startswith("mysql://"):
        mysql_url = mysql_url.replace("mysql://", "mysql+pymysql://", 1)
    try:
        engine = create_engine(mysql_url, connect_args={"connect_timeout": 5})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        SessionFactory = sessionmaker(bind=engine)
        print(f"[OK] Ket noi MySQL thanh cong: {mysql_url.split('@')[-1]}")
        return SessionFactory(), "mysql"
    except Exception as e:
        print(f"[WARNING] MySQL loi: {e}")
        print(f"[WARNING] Fallback sang SQLite: {SQLITE_PATH}")
        sqlite_engine = create_engine(f"sqlite:///{SQLITE_PATH}")
        AuditSession.__table__.create(sqlite_engine, checkfirst=True)
        SessionFactory = sessionmaker(bind=sqlite_engine)
        return SessionFactory(), "sqlite"

# ---------------------------------------------------------------------------
# Retry wrapper
# ---------------------------------------------------------------------------
DRIVE_RETRY_TIMES = 3
DRIVE_RETRY_DELAY = 3

def _call_with_retry(func, *args, **kwargs):
    last_error = None
    for attempt in range(1, DRIVE_RETRY_TIMES + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_error = e
            print(f"   -> [RETRY {attempt}/{DRIVE_RETRY_TIMES}] Drive API loi: {e}. Thu lai sau {DRIVE_RETRY_DELAY}s...")
            time.sleep(DRIVE_RETRY_DELAY)
    raise last_error

# ---------------------------------------------------------------------------
# Quét folder KẾ TOÁN
# ---------------------------------------------------------------------------
def check_kt_files(company_root_id: str, year: int) -> dict:
    """
    Tìm folder KẾ TOÁN và đếm file.

    Cấu trúc:  root -> TAI-LIEU-THUE (hoặc THUE) -> {year} -> KE-TOAN
    Thêm:      root -> TAI-LIEU-THUE -> {year} -> DOANH-NGHIEP (file XML BCTC)

    Returns:
        dict với 'status' ('pass'|'warning'), 'files_count', 'message'
    """
    try:
        service = get_drive_service()

        # 1. Tìm TAI-LIEU-THUE
        f_thue = _call_with_retry(find_child_folder_by_name_contain, service, company_root_id, "TAI-LIEU-THUE")
        if not f_thue:
            f_thue = _call_with_retry(find_child_folder_by_name_contain, service, company_root_id, "THUE")
        if not f_thue:
            return {'status': 'warning', 'message': 'Khong tim thay folder TAI-LIEU-THUE/THUE', 'files_count': 0}

        # 2. Tìm folder năm
        f_year = _call_with_retry(find_child_folder_exact, service, f_thue['id'], str(year))
        if not f_year:
            f_year = _call_with_retry(find_child_folder_by_name_contain, service, f_thue['id'], str(year))
        if not f_year:
            return {'status': 'warning', 'message': f'Khong tim thay folder nam {year}', 'files_count': 0}

        all_files = []

        # 3. Quét DOANH-NGHIEP (file XML BCTC)
        f_dn = _call_with_retry(find_child_folder_by_name_contain, service, f_year['id'], "DOANH-NGHIEP")
        if f_dn:
            dn_files = _call_with_retry(get_all_files_recursive, service, f_dn['id'])
            all_files.extend(dn_files)

        # 4. Quét KE-TOAN (file Excel sổ sách)
        f_kt = _call_with_retry(find_child_folder_by_name_contain, service, f_year['id'], "KE-TOAN")
        if f_kt:
            kt_files = _call_with_retry(get_all_files_recursive, service, f_kt['id'])
            all_files.extend(kt_files)

        if not f_dn and not f_kt:
            return {'status': 'warning', 'message': 'Khong tim thay folder KE-TOAN va DOANH-NGHIEP', 'files_count': 0}

        total = len(all_files)
        if total < MIN_FILES:
            return {
                'status': 'warning',
                'message': f'Chi co {total} file (yeu cau toi thieu {MIN_FILES})',
                'files_count': total,
            }

        return {
            'status': 'pass',
            'message': f'Tim thay {total} file',
            'files_count': total,
        }

    except Exception as e:
        return {'status': 'warning', 'message': f'Loi khi quet Drive: {str(e)}', 'files_count': 0}

# ---------------------------------------------------------------------------
# Ghi DB
# ---------------------------------------------------------------------------
def _mark_as_missing(db: Session, folder_id: int, year: int, session_id: int | None, message: str):
    note = f"[He thong] Tu dong quet KE TOAN: {message}"
    try:
        if session_id:
            audit_sess = db.query(AuditSession).filter(AuditSession.id == session_id).first()
            if audit_sess:
                audit_sess.status       = "warning"
                audit_sess.category     = "KT"
                audit_sess.period       = "YEAR"
                audit_sess.overall_note = note
                audit_sess.updated_at   = datetime.utcnow()
                db.commit()
                print(f"   -> [OK] DB UPDATE id={session_id} -> warning")
        else:
            audit_sess = AuditSession(
                folder_id      = folder_id,
                category       = "KT",
                year           = year,
                period         = "YEAR",
                status         = "warning",
                checklist_data = [],
                overall_note   = note,
            )
            db.add(audit_sess)
            db.commit()
            db.refresh(audit_sess)
            print(f"   -> [OK] DB INSERT id={audit_sess.id}, folder_id={folder_id} -> warning")
    except Exception as e:
        print(f"   -> [ERROR] Loi khi luu DB: {e}")
        db.rollback()

# ---------------------------------------------------------------------------
# Hàm chính
# ---------------------------------------------------------------------------
def check_missing_kt(year: int, force: bool = False):
    settings.DOCKER = False

    print(f"Bat dau chay Script: Kiem tra KE TOAN cho Nam {year} (nguong: {MIN_FILES} file)")
    db, db_type = _create_session()
    print(f"[DB] Dang dung DB: {db_type.upper()}")
    folder_repo = FolderRepository()

    try:
        get_drive_service()
    except Exception as e:
        print(f"[ERROR] Loi ket noi Google Drive: {e}")
        db.close()
        return

    all_folders = folder_repo.get_all()
    count_ok      = 0
    count_missing = 0
    count_skipped = 0
    count_error   = 0

    for idx, folder in enumerate(all_folders, 1):
        f_id    = getattr(folder, "id", None)             or folder.get("id")
        c_code  = getattr(folder, "company_code", None)   or folder.get("company_code")
        c_name  = getattr(folder, "company_name", None)   or folder.get("company_name")
        root_id = getattr(folder, "root_folder_id", None) or folder.get("root_folder_id")

        print(f"\n[{idx}/{len(all_folders)}] Dang xu ly: {c_code} - {c_name}")

        if not root_id:
            print("   -> Bo qua vi khong co root_folder_id tren Drive.")
            count_skipped += 1
            continue

        session = db.query(AuditSession).filter(
            AuditSession.folder_id == f_id,
            AuditSession.category  == "KT",
            AuditSession.year      == year,
        ).first()

        if not force and session and session.status and session.status != "empty":
            print(f"   -> Da co trang thai ({session.status}). Bo qua.")
            count_skipped += 1
            continue

        session_id = getattr(session, "id", None) if session else None

        try:
            result = check_kt_files(root_id, year)

            if result['status'] == 'warning':
                print(f"   -> [WARNING] {result['message']}. Danh dau warning.")
                _mark_as_missing(db, f_id, year, session_id, result['message'])
                count_missing += 1
            else:
                print(f"   -> [OK] {result['message']}. Khong thay doi trang thai.")
                count_ok += 1

        except Exception as e:
            print(f"   -> [ERROR] Loi Drive API sau khi retry: {e}. Bo qua.")
            count_error += 1

    db.close()

    print("\n" + "=" * 50)
    print(f"TONG KET (DB: {db_type.upper()}):")
    print(f"  Tong so cong ty            : {len(all_folders)}")
    print(f"  Bo qua (da co trang thai)  : {count_skipped}")
    print(f"  Co du data (khong update)  : {count_ok}")
    print(f"  Thieu / it file (warning)  : {count_missing}")
    print(f"  Loi Drive API (skip)       : {count_error}")
    print("=" * 50)

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kiem tra file KE TOAN tren Drive.")
    parser.add_argument("--year",  type=int, default=datetime.now().year, help="Nam can kiem tra (mac dinh: nam hien tai)")
    parser.add_argument("--force", "-f", action="store_true",             help="Bo qua trang thai cu, chay lai toan bo")
    args = parser.parse_args()

    print(f"\n{'='*50}")
    print(f"BAT DAU KIEM TRA KE TOAN NAM {args.year}")
    print(f"{'='*50}\n")

    check_missing_kt(args.year, force=args.force)

    print(f"\n{'='*50}")
    print(f"HOAN THANH KIEM TRA KE TOAN NAM {args.year}")
    print(f"{'='*50}")
