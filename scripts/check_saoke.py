#!/usr/bin/env python3
"""
Script to check for files in sao kê folder
Returns 'warning' if no files exist, 'pass' if files exist
Updates database with status
"""

import sys
import os
import time
import argparse
from datetime import datetime, timezone
from dotenv import load_dotenv

# Fix Unicode encoding for Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

load_dotenv()  # Load variables from .env

# Buộc ứng dụng tắt chế độ Docker trên Local Terminal
os.environ["DOCKER"] = "false"

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from app.models.audit import AuditSession           # type: ignore
from app.core.config import settings                # type: ignore
from app.db.repositories.folder_repo import FolderRepository  # type: ignore
from app.services.drive_service import (
    find_child_folder_by_name_contain, 
    find_child_folder_exact, 
    get_all_files_recursive,
    get_drive_service
)

# ---------------------------------------------------------------------------
# Khởi tạo DB — MySQL trước, fallback SQLite nếu lỗi
# ---------------------------------------------------------------------------
SQLITE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cenvi_audit.db")

def _create_session() -> tuple[Session, str]:
    """
    Thử kết nối MySQL. Nếu lỗi -> fallback SQLite.
    Trả về (session, db_type) với db_type là "mysql" hoặc "sqlite".
    """
    mysql_url = os.getenv("DATABASE_URL") 
    if not mysql_url:
        mysql_url = (
            f"mysql+pymysql://{os.getenv('DB_USER','root')}:{os.getenv('DB_PASSWORD','')}@"
            f"{os.getenv('DB_HOST','127.0.0.1')}:{os.getenv('DB_PORT','3307')}/{os.getenv('DB_NAME','cenvi_audit')}"
        )
    else:
        # Ensure DATABASE_URL uses pymysql
        if mysql_url.startswith("mysql://"):
            mysql_url = mysql_url.replace("mysql://", "mysql+pymysql://")
    try:
        engine = create_engine(mysql_url, connect_args={"connect_timeout": 5})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))  # Kiểm tra kết nối thật sự
        SessionFactory = sessionmaker(bind=engine)
        print(f"[OK] Ket noi MySQL thanh cong: {mysql_url.split('@')[-1]}")
        return SessionFactory(), "mysql"
    except Exception as e:
        print(f"[WARNING] MySQL loi: {e}")
        print(f"[WARNING] Fallback sang SQLite: {SQLITE_PATH}")
        sqlite_engine = create_engine(f"sqlite:///{SQLITE_PATH}")
        AuditSession.__table__.create(sqlite_engine, checkfirst=True)  # Tạo bảng nếu chưa có
        SessionFactory = sessionmaker(bind=sqlite_engine)
        return SessionFactory(), "sqlite"

# ---------------------------------------------------------------------------
# Cấu hình retry cho Google Drive API
# ---------------------------------------------------------------------------
DRIVE_RETRY_TIMES = 3       # Số lần thử lại khi Drive API lỗi
DRIVE_RETRY_DELAY = 3       # Giây chờ giữa các lần thử

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

def check_saoke_files(company_root_id, year):
    """
    Kiểm tra 2 điều kiện:
      1. Folder 4-SAO-KE-NGAN-HANG (nhánh CONG-TY) có file không.
      2. Folder DOANH-NGHIEP (nhánh TAI-LIEU-THUE / TNDN) có file XML không.
    Cả 2 phải có dữ liệu thì mới là 'pass'.
    """
    try:
        service = get_drive_service()
        missing = []

        # ----------------------------------------------------------------
        # 1. Kiểm tra SAO KE NGAN HANG (nhánh CONG-TY)
        # ----------------------------------------------------------------
        f_cty = _call_with_retry(find_child_folder_by_name_contain, service, company_root_id, "CONG-TY")
        if not f_cty:
            f_cty = _call_with_retry(find_child_folder_by_name_contain, service, company_root_id, "TAI-LIEU-CONG-TY")

        if not f_cty:
            missing.append("Khong tim thay folder TAI-LIEU-CONG-TY")
        else:
            f_year_cty = _call_with_retry(find_child_folder_exact, service, f_cty['id'], str(year))
            if not f_year_cty:
                f_year_cty = _call_with_retry(find_child_folder_by_name_contain, service, f_cty['id'], str(year))

            if not f_year_cty:
                missing.append(f"TAI-LIEU-CONG-TY: Khong tim thay folder nam {year}")
            else:
                f_bank = _call_with_retry(find_child_folder_by_name_contain, service, f_year_cty['id'], "4-SAO-KE-NGAN-HANG")
                if not f_bank:
                    missing.append("Khong tim thay folder 4-SAO-KE-NGAN-HANG")
                else:
                    bank_files = _call_with_retry(get_all_files_recursive, service, f_bank['id'])
                    if not bank_files:
                        missing.append("Folder 4-SAO-KE-NGAN-HANG rong")
                    else:
                        print(f"   -> SAO-KE-NGAN-HANG: {len(bank_files)} file")

        # ----------------------------------------------------------------
        # 2. Kiểm tra file XML trong DOANH-NGHIEP (nhánh TAI-LIEU-THUE / TNDN)
        # ----------------------------------------------------------------
        f_thue = _call_with_retry(find_child_folder_by_name_contain, service, company_root_id, "TAI-LIEU-THUE")
        if not f_thue:
            f_thue = _call_with_retry(find_child_folder_by_name_contain, service, company_root_id, "THUE")

        if not f_thue:
            missing.append("Khong tim thay folder TAI-LIEU-THUE")
        else:
            f_year_thue = _call_with_retry(find_child_folder_exact, service, f_thue['id'], str(year))
            if not f_year_thue:
                f_year_thue = _call_with_retry(find_child_folder_by_name_contain, service, f_thue['id'], str(year))

            if not f_year_thue:
                missing.append(f"TAI-LIEU-THUE: Khong tim thay folder nam {year}")
            else:
                # Ưu tiên KE-TOAN (lấy tất cả file đệ quy, chia theo quý bên trong)
                f_kt = _call_with_retry(find_child_folder_by_name_contain, service, f_year_thue['id'], "KE-TOAN")
                if f_kt:
                    kt_files = _call_with_retry(get_all_files_recursive, service, f_kt['id'])
                    if not kt_files:
                        missing.append("Folder KE-TOAN rong")
                    else:
                        print(f"   -> KE-TOAN: {len(kt_files)} file")
                else:
                    # Fallback: DOANH-NGHIEP (chỉ lấy XML)
                    f_dn = _call_with_retry(find_child_folder_by_name_contain, service, f_year_thue['id'], "DOANH-NGHIEP")
                    if not f_dn:
                        missing.append("Khong tim thay folder KE-TOAN va DOANH-NGHIEP (TNDN)")
                    else:
                        all_dn_files = _call_with_retry(get_all_files_recursive, service, f_dn['id'])
                        xml_files = [
                            f for f in all_dn_files
                            if 'xml' in (f.get('mimeType') or '').lower()
                            or (f.get('name') or '').lower().endswith('.xml')
                        ]
                        if not xml_files:
                            missing.append("Folder DOANH-NGHIEP (TNDN) khong co file XML")
                        else:
                            print(f"   -> DOANH-NGHIEP (TNDN): {len(xml_files)} file XML")

        if missing:
            return {
                'status': 'warning',
                'message': ' | '.join(missing),
                'files_count': 0,
                'files': []
            }

        return {
            'status': 'pass',
            'message': f'SAO-KE va DOANH-NGHIEP deu co du lieu nam {year}',
            'files_count': 1,
            'files': []
        }

    except Exception as e:
        return {
            'status': 'warning',
            'message': f'Loi khi quet Drive: {str(e)}',
            'files_count': 0,
            'files': []
        }


# ---------------------------------------------------------------------------
# Cập nhật DB status
# ---------------------------------------------------------------------------
def _mark_as_missing(
    db: Session,
    folder_id: int,
    year: int,
    message: str,
    session_id: int | None = None,
):
    """Cập nhật hoặc tạo mới AuditSession với status = warning."""
    note = f"[He thong] Tu dong quet SAO KE: {message}"
    try:
        if session_id:
            audit_sess = db.query(AuditSession).filter(AuditSession.id == session_id).first()
            if audit_sess:
                audit_sess.status       = "warning"
                audit_sess.category     = "Saoke"
                audit_sess.period       = "YEAR"
                audit_sess.overall_note = note
                audit_sess.updated_at   = datetime.now(timezone.utc)
                db.commit()
                print(f"   -> [OK] DB UPDATE id={session_id} -> warning")
        else:
            audit_sess = AuditSession(
                folder_id      = folder_id,
                category       = "Saoke",
                year           = year,
                period         = "YEAR",
                status         = "warning",
                checklist_data = [],
                overall_note   = note,
            )
            db.add(audit_sess)
            db.commit()
            db.refresh(audit_sess)
            print(f"   -> [OK] DB INSERT folder_id={folder_id} -> warning")
    except Exception as e:
        print(f"   -> [ERROR] Loi khi luu DB: {e}")
        db.rollback()

def check_missing_saoke(year: int, force: bool = False):
    """Main function to check all companies for sao kê files"""
    settings.DOCKER = False

    print(f"Bat dau chay Script: Kiem tra THIEU file SAO KÊ cho Nam {year}")
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
            AuditSession.category  == "Saoke",
            AuditSession.year      == year,
        ).first()

        if not force and session and session.status and session.status != "empty":
            print(f"   -> Da co trang thai ({session.status}). Bo qua.")
            count_skipped += 1
            continue

        session_id = getattr(session, "id", None) if session else None

        # --- Quét Drive ---
        try:
            result = check_saoke_files(root_id, year)
            
            if result.get("status") == "warning":
                msg = result.get('message', 'Loi khong xac dinh')
                print(f"   -> [WARNING] {msg}")
                _mark_as_missing(db, f_id, year, msg, session_id)
                count_missing += 1
            else:
                print(f"   -> [OK] {result.get('message')}. Khong thay doi trang thai.")
                count_ok += 1

        except Exception as e:
            # Sau khi đã retry hết mà vẫn lỗi -> log, không đánh warning tránh false-positive
            print(f"   -> [ERROR] Loi Drive API sau khi retry: {e}. Bo qua cong ty nay.")
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

def main():
    """Main function to run the check"""
    parser = argparse.ArgumentParser(description='Check for files in sao kê folder')
    parser.add_argument('--year', type=int, default=datetime.now().year, help='Year to check (default: current year)')
    parser.add_argument('--company-id', help='Single company root folder ID (optional - if not provided, check all companies)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed output')
    parser.add_argument('--force', '-f', action='store_true', help='Bỏ qua trạng thái cũ, chạy lại toàn bộ')
    
    args = parser.parse_args()
    
    if args.company_id:
        # Single company mode (original functionality)
        result = check_saoke_files(args.company_id, args.year)
        
        # Print result
        print(f"Status: {result['status']}")
        print(f"Message: {result['message']}")
        print(f"Files count: {result['files_count']}")
        
        if args.verbose and result['files']:
            print("\nFiles found:")
            for file in result['files']:
                print(f"  - {file['name']} ({file.get('mimeType', 'unknown')})")
        
        # Exit with appropriate code
        sys.exit(0 if result['status'] == 'pass' else 1)
    else:
        # Batch mode with database integration
        print(f"\n{'='*50}")
        print(f"BAT DAU KIEM TRA SAO KÊ NAM {args.year}")
        print(f"{'='*50}\n")
        
        check_missing_saoke(args.year, force=args.force)
        
        print(f"\n{'='*50}")
        print(f"HOAN THANH KIEM TRA SAO KÊ NAM {args.year}")
        print(f"{'='*50}")

if __name__ == '__main__':
    main()
