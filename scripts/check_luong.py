#!/usr/bin/env python3
"""
Script kiểm tra folder LUONG trên Drive.
Cấu trúc cần kiểm tra:
  root -> TAI-LIEU-CONG-TY -> {year} -> 5-LUONG -> BANG-LUONG-CHAM-CONG
  root -> TAI-LIEU-CONG-TY -> {year} -> 5-LUONG -> BAO-HIEM-XA-HOI

Nếu BANG-LUONG-CHAM-CONG hoặc BAO-HIEM-XA-HOI trống (hoặc không tồn tại)
-> đánh warning cho cả 4 quý (Q1, Q2, Q3, Q4).
Lưu ý: nhân viên có thể không chia folder theo quý mà lưu file trực tiếp,
nên chỉ cần kiểm tra có file nào trong folder hay không (đệ quy).
Nếu cả 2 đều có file -> giữ nguyên trạng thái.
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

QUARTERS = ["Q1", "Q2", "Q3", "Q4"]

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
# Kiểm tra folder LUONG (1 lần cho cả năm)
# ---------------------------------------------------------------------------
def check_luong_folders(company_root_id: str, year: int) -> dict:
    """
    Kiểm tra BANG-LUONG-CHAM-CONG và BAO-HIEM-XA-HOI bên trong 5-LUONG.

    Trả về:
      - 'warning' nếu một trong 2 folder trống hoặc không tồn tại
      - 'pass'    nếu cả 2 đều có ít nhất 1 file
    """
    try:
        service = get_drive_service()

        # 1. Tìm TAI-LIEU-CONG-TY
        f_cty = _call_with_retry(find_child_folder_by_name_contain, service, company_root_id, "TAI-LIEU-CONG-TY")
        if not f_cty:
            f_cty = _call_with_retry(find_child_folder_by_name_contain, service, company_root_id, "CONG-TY")
        if not f_cty:
            return {'status': 'warning', 'message': 'Khong tim thay folder TAI-LIEU-CONG-TY'}

        # 2. Tìm folder năm
        f_year = _call_with_retry(find_child_folder_exact, service, f_cty['id'], str(year))
        if not f_year:
            f_year = _call_with_retry(find_child_folder_by_name_contain, service, f_cty['id'], str(year))
        if not f_year:
            return {'status': 'warning', 'message': f'Khong tim thay folder nam {year}'}

        # 3. Tìm 5-LUONG
        f_luong = _call_with_retry(find_child_folder_by_name_contain, service, f_year['id'], "5-LUONG")
        if not f_luong:
            f_luong = _call_with_retry(find_child_folder_by_name_contain, service, f_year['id'], "LUONG")
        if not f_luong:
            return {'status': 'warning', 'message': 'Khong tim thay folder 5-LUONG'}

        missing = []

        # 4. Kiểm tra BANG-LUONG-CHAM-CONG
        f_bl = _call_with_retry(find_child_folder_by_name_contain, service, f_luong['id'], "BANG-LUONG-CHAM-CONG")
        if not f_bl:
            f_bl = _call_with_retry(find_child_folder_by_name_contain, service, f_luong['id'], "BANG-LUONG")
        if not f_bl:
            missing.append("Khong tim thay folder BANG-LUONG-CHAM-CONG")
        else:
            files_bl = _call_with_retry(get_all_files_recursive, service, f_bl['id'])
            if not files_bl:
                missing.append("Folder BANG-LUONG-CHAM-CONG rong")
            else:
                print(f"   -> BANG-LUONG-CHAM-CONG: {len(files_bl)} file")

        # 5. Kiểm tra BAO-HIEM-XA-HOI
        f_bh = _call_with_retry(find_child_folder_by_name_contain, service, f_luong['id'], "BAO-HIEM-XA-HOI")
        if not f_bh:
            f_bh = _call_with_retry(find_child_folder_by_name_contain, service, f_luong['id'], "BAO-HIEM")
        if not f_bh:
            missing.append("Khong tim thay folder BAO-HIEM-XA-HOI")
        else:
            files_bh = _call_with_retry(get_all_files_recursive, service, f_bh['id'])
            if not files_bh:
                missing.append("Folder BAO-HIEM-XA-HOI rong")
            else:
                print(f"   -> BAO-HIEM-XA-HOI: {len(files_bh)} file")

        if missing:
            return {'status': 'warning', 'message': ' | '.join(missing)}

        return {'status': 'pass', 'message': 'Ca 2 folder BANG-LUONG-CHAM-CONG va BAO-HIEM-XA-HOI deu co du lieu'}

    except Exception as e:
        return {'status': 'warning', 'message': f'Loi khi quet Drive: {str(e)}'}

# ---------------------------------------------------------------------------
# Ghi DB — đánh warning cho 1 quý
# ---------------------------------------------------------------------------
def _mark_as_missing(db: Session, folder_id: int, year: int, period: str, session_id: int | None, message: str):
    note = f"[He thong] Tu dong quet LUONG: {message}"
    try:
        if session_id:
            audit_sess = db.query(AuditSession).filter(AuditSession.id == session_id).first()
            if audit_sess:
                audit_sess.status       = "warning"
                audit_sess.category     = "Luong"
                audit_sess.period       = period
                audit_sess.overall_note = note
                audit_sess.updated_at   = datetime.utcnow()
                db.commit()
                print(f"   -> [OK] DB UPDATE id={session_id} ({period}) -> warning")
        else:
            audit_sess = AuditSession(
                folder_id      = folder_id,
                category       = "Luong",
                year           = year,
                period         = period,
                status         = "warning",
                checklist_data = [],
                overall_note   = note,
            )
            db.add(audit_sess)
            db.commit()
            db.refresh(audit_sess)
            print(f"   -> [OK] DB INSERT folder_id={folder_id} {period} -> warning")
    except Exception as e:
        print(f"   -> [ERROR] Loi khi luu DB ({period}): {e}")
        db.rollback()

# ---------------------------------------------------------------------------
# Hàm chính
# ---------------------------------------------------------------------------
def check_missing_luong(year: int, force: bool = False):
    settings.DOCKER = False

    print(f"Bat dau chay Script: Kiem tra LUONG cho Nam {year}")
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

        # Bỏ qua nếu đã có status đủ cả 4 quý
        if not force:
            existing = db.query(AuditSession).filter(
                AuditSession.folder_id == f_id,
                AuditSession.category  == "Luong",
                AuditSession.year      == year,
                AuditSession.period.in_(QUARTERS),
            ).all()
            done_periods = {s.period for s in existing if s.status and s.status != "empty"}
            if done_periods == set(QUARTERS):
                print(f"   -> Da co trang thai ca 4 quy. Bo qua.")
                count_skipped += 1
                continue

        try:
            result = check_luong_folders(root_id, year)

            if result['status'] == 'warning':
                print(f"   -> [WARNING] {result['message']}. Danh dau warning ca 4 quy.")
                for q in QUARTERS:
                    existing_q = db.query(AuditSession).filter(
                        AuditSession.folder_id == f_id,
                        AuditSession.category  == "Luong",
                        AuditSession.year      == year,
                        AuditSession.period    == q,
                    ).first()
                    if not force and existing_q and existing_q.status and existing_q.status != "empty":
                        print(f"   -> {q}: Da co trang thai ({existing_q.status}). Bo qua.")
                        continue
                    session_id = getattr(existing_q, "id", None) if existing_q else None
                    _mark_as_missing(db, f_id, year, q, session_id, result['message'])
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
    print(f"  Thieu LUONG (warning 4 quy) : {count_missing}")
    print(f"  Loi Drive API (skip)       : {count_error}")
    print("=" * 50)

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kiem tra folder LUONG tren Drive.")
    parser.add_argument("--year",  type=int, default=datetime.now().year, help="Nam can kiem tra (mac dinh: nam hien tai)")
    parser.add_argument("--force", "-f", action="store_true",             help="Bo qua trang thai cu, chay lai toan bo")
    args = parser.parse_args()

    print(f"\n{'='*50}")
    print(f"BAT DAU KIEM TRA LUONG NAM {args.year}")
    print(f"{'='*50}\n")

    check_missing_luong(args.year, force=args.force)

    print(f"\n{'='*50}")
    print(f"HOAN THANH KIEM TRA LUONG NAM {args.year}")
    print(f"{'='*50}")
