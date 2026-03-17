#!/usr/bin/env python3
"""
Script kiểm tra folder HOÁ ĐƠN trên Drive (theo quý).
Nếu không có file hoá đơn (mua + bán) trong quý -> warning.
Nếu có -> giữ nguyên trạng thái (không đổi).
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
# Helper tìm folder
# ---------------------------------------------------------------------------
def _find_first_by_keywords(service, parent_id: str, keywords: list):
    for kw in keywords:
        found = _call_with_retry(find_child_folder_by_name_contain, service, parent_id, kw)
        if found:
            return found
    return None

def _find_quarter_folder(service, parent_id: str, q_num: str):
    candidates = [
        f"QUY {q_num}", f"QUY-{q_num}", f"QUY_{q_num}", f"Q{q_num}",
        f"QUY{q_num}", f"HDM_QUY-{q_num}", f"HDB_QUY-{q_num}",
    ]
    return _find_first_by_keywords(service, parent_id, candidates)

# ---------------------------------------------------------------------------
# Quét hóa đơn 1 quý
# ---------------------------------------------------------------------------
def check_hdon_files(company_root_id: str, year: int, period: str) -> dict:
    """
    Kiểm tra hoá đơn mua + bán cho 1 quý.

    Cấu trúc: root -> TAI-LIEU-CONG-TY/{year}/1-HOA-DON-MUA/QUY-{q}
                                              /2-HOA-DON-BAN/QUY-{q}

    Returns:
        dict với 'status' ('pass'|'warning'), 'files_count', 'message'
    """
    try:
        service = get_drive_service()
        q_num = period.replace("Q", "").replace("q", "").strip()

        # 1. Tìm folder CONG-TY
        f_cty = _find_first_by_keywords(service, company_root_id, ["TAI-LIEU-CONG-TY", "CONG-TY", "CONG TY"])
        if not f_cty:
            return {'status': 'warning', 'message': 'Khong tim thay folder TAI-LIEU-CONG-TY/CONG-TY', 'files_count': 0}

        # 2. Tìm folder năm
        f_year = _call_with_retry(find_child_folder_exact, service, f_cty['id'], str(year))
        if not f_year:
            f_year = _call_with_retry(find_child_folder_by_name_contain, service, f_cty['id'], str(year))
        if not f_year:
            return {'status': 'warning', 'message': f'Khong tim thay folder nam {year}', 'files_count': 0}

        total_files = 0

        # 3. Hoá đơn MUA
        f_buy = _find_first_by_keywords(service, f_year['id'], ["1-HOA-DON-MUA", "HOA-DON-MUA", "HD-MUA"])
        if f_buy:
            f_q_buy = _find_quarter_folder(service, f_buy['id'], q_num)
            if f_q_buy:
                buy_files = _call_with_retry(get_all_files_recursive, service, f_q_buy['id'])
                total_files += len(buy_files)
            else:
                # Không có folder quý, quét thẳng folder mua
                buy_files = _call_with_retry(get_all_files_recursive, service, f_buy['id'])
                total_files += len(buy_files)

        # 4. Hoá đơn BÁN
        f_sell = _find_first_by_keywords(service, f_year['id'], ["2-HOA-DON-BAN", "HOA-DON-BAN", "HD-BAN"])
        if f_sell:
            f_q_sell = _find_quarter_folder(service, f_sell['id'], q_num)
            if f_q_sell:
                sell_files = _call_with_retry(get_all_files_recursive, service, f_q_sell['id'])
                total_files += len(sell_files)
            else:
                sell_files = _call_with_retry(get_all_files_recursive, service, f_sell['id'])
                total_files += len(sell_files)

        if not f_buy and not f_sell:
            return {'status': 'warning', 'message': f'Khong tim thay folder HOA-DON-MUA va HOA-DON-BAN', 'files_count': 0}

        if total_files == 0:
            return {'status': 'warning', 'message': f'Khong co file hoa don nao trong {period}', 'files_count': 0}

        return {'status': 'pass', 'message': f'Tim thay {total_files} file hoa don trong {period}', 'files_count': total_files}

    except Exception as e:
        return {'status': 'warning', 'message': f'Loi khi quet Drive: {str(e)}', 'files_count': 0}

# ---------------------------------------------------------------------------
# Ghi DB
# ---------------------------------------------------------------------------
def _mark_as_missing(db: Session, folder_id: int, year: int, period: str, session_id: int | None, message: str):
    note = f"[He thong] Tu dong quet HOA DON {period}: {message}"
    try:
        if session_id:
            audit_sess = db.query(AuditSession).filter(AuditSession.id == session_id).first()
            if audit_sess:
                audit_sess.status       = "warning"
                audit_sess.category     = "Hdon"
                audit_sess.period       = period
                audit_sess.overall_note = note
                audit_sess.updated_at   = datetime.utcnow()
                db.commit()
                print(f"   -> [OK] DB UPDATE id={session_id} -> warning")
        else:
            audit_sess = AuditSession(
                folder_id      = folder_id,
                category       = "Hdon",
                year           = year,
                period         = period,
                status         = "warning",
                checklist_data = [],
                overall_note   = note,
            )
            db.add(audit_sess)
            db.commit()
            db.refresh(audit_sess)
            print(f"   -> [OK] DB INSERT id={audit_sess.id}, folder_id={folder_id} {period} -> warning")
    except Exception as e:
        print(f"   -> [ERROR] Loi khi luu DB: {e}")
        db.rollback()

# ---------------------------------------------------------------------------
# Hàm chính — 1 quý
# ---------------------------------------------------------------------------
def check_missing_hdon(year: int, period: str, force: bool = False):
    settings.DOCKER = False

    print(f"Bat dau chay Script: Kiem tra HOA DON cho Nam {year} - {period}")
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

        print(f"\n[{idx}/{len(all_folders)}] Dang xu ly: {c_code} - {c_name} | {period}")

        if not root_id:
            print("   -> Bo qua vi khong co root_folder_id tren Drive.")
            count_skipped += 1
            continue

        session = db.query(AuditSession).filter(
            AuditSession.folder_id == f_id,
            AuditSession.category  == "Hdon",
            AuditSession.year      == year,
            AuditSession.period    == period,
        ).first()

        if not force and session and session.status and session.status != "empty":
            print(f"   -> Da co trang thai ({session.status}). Bo qua.")
            count_skipped += 1
            continue

        session_id = getattr(session, "id", None) if session else None

        try:
            result = check_hdon_files(root_id, year, period)

            if result['status'] == 'warning':
                print(f"   -> [WARNING] {result['message']}. Danh dau warning.")
                _mark_as_missing(db, f_id, year, period, session_id, result['message'])
                count_missing += 1
            else:
                print(f"   -> [OK] {result['message']}. Khong thay doi trang thai.")
                count_ok += 1

        except Exception as e:
            print(f"   -> [ERROR] Loi Drive API sau khi retry: {e}. Bo qua.")
            count_error += 1

    db.close()

    print("\n" + "=" * 50)
    print(f"TONG KET {period} (DB: {db_type.upper()}):")
    print(f"  Tong so cong ty            : {len(all_folders)}")
    print(f"  Bo qua (da co trang thai)  : {count_skipped}")
    print(f"  Co du data (khong update)  : {count_ok}")
    print(f"  Thieu hoa don (warning)    : {count_missing}")
    print(f"  Loi Drive API (skip)       : {count_error}")
    print("=" * 50)

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kiem tra file HOA DON tren Drive.")
    parser.add_argument("--year",   type=int, default=datetime.now().year,
                        help="Nam can kiem tra (mac dinh: nam hien tai)")
    parser.add_argument("--period", type=str, default=None,
                        help="Quy can kiem tra: Q1, Q2, Q3, Q4. Bo trong de check ca 4 quy.")
    parser.add_argument("--force", "-f", action="store_true",
                        help="Bo qua trang thai cu, chay lai toan bo")
    args = parser.parse_args()

    quarters = [args.period.upper()] if args.period else ["Q1", "Q2", "Q3", "Q4"]

    print(f"\n{'='*50}")
    print(f"BAT DAU KIEM TRA HOA DON NAM {args.year}" + (f" - {args.period.upper()}" if args.period else " (CA 4 QUY)"))
    print(f"{'='*50}\n")

    for q in quarters:
        print(f"\n{'#'*50}")
        print(f"# DANG CHAY: {q} - NAM {args.year}")
        print(f"{'#'*50}")
        check_missing_hdon(args.year, q, force=args.force)

    print(f"\n{'='*50}")
    print(f"HOAN THANH KIEM TRA HOA DON NAM {args.year}")
    print(f"{'='*50}")
