#!/usr/bin/env python3
"""
Script to add missing columns to COMPANY_INFO table without losing data
"""

import sys
import os
import sqlite3
import codecs

# Fix Unicode encoding for Windows
if sys.platform == "win32":
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

SQLITE_PATH = os.path.join(os.path.dirname(__file__), '..', 'cenvi_audit.db')

def add_missing_columns():
    """Add missing columns to COMPANY_INFO table"""

    try:
        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()

        # Thêm cột cho bảng employees nếu chưa có
        employees_columns = [
            ('name', 'VARCHAR(255)'),
            ('title', 'VARCHAR(255)'),
            ('status', 'VARCHAR(50)'),
            ('created_at', 'DATETIME'),
            ('updated_at', 'DATETIME'),
        ]

        print("🔧 Kiểm tra bảng employees...")
        for col_name, col_type in employees_columns:
            try:
                cursor.execute(f'ALTER TABLE employees ADD COLUMN {col_name} {col_type}')
                print(f"✅ Đã thêm cột employees.{col_name}")
            except sqlite3.OperationalError as e:
                if 'duplicate column name' in str(e):
                    print(f"⚠️ Cột employees.{col_name} đã tồn tại")
                else:
                    print(f"❌ Lỗi thêm cột {col_name}: {e}")

        # Danh sách các cột cần thêm
        columns_to_add = [
            ('ten_cong_ty_viet_tat', 'VARCHAR(200)'),
            ('nguoi_lien_he_va_chuc_vu', 'VARCHAR(300)'),
            ('so_dien_thoai', 'VARCHAR(50)'),
            ('email_lien_he', 'VARCHAR(200)'),
            ('thong_tin_khac', 'TEXT'),
            ('folder_year', 'INTEGER'),
            ('folder_template', 'VARCHAR(50)'),
            ('folder_status', 'VARCHAR(50)'),
            ('cenvi_cam_token', 'BOOLEAN'),
            ('token_mat_khau', 'VARCHAR(500)'),
            ('token_ngay', 'DATETIME'),
            ('thue_dt_tai_khoan', 'VARCHAR(200)'),
            ('thue_dt_mat_khau', 'VARCHAR(500)'),
            ('hddt_tai_khoan', 'VARCHAR(200)'),
            ('hddt_mat_khau', 'VARCHAR(500)'),
            ('xuat_hd_link', 'VARCHAR(500)'),
            ('xuat_hd_tai_khoan', 'VARCHAR(200)'),
            ('xuat_hd_mat_khau', 'VARCHAR(500)'),
            ('bhxh_link', 'VARCHAR(500)'),
            ('bhxh_ma_so', 'VARCHAR(100)'),
            ('bhxh_tai_khoan', 'VARCHAR(200)'),
            ('bhxh_mat_khau', 'VARCHAR(500)'),
            ('pmkt_ten', 'VARCHAR(200)'),
            ('pmkt_link', 'VARCHAR(500)'),
            ('pmkt_tai_khoan', 'VARCHAR(200)'),
            ('pmkt_mat_khau', 'VARCHAR(500)'),
            ('hop_dong_link', 'VARCHAR(500)'),
            ('hop_dong_ngay_ky', 'DATETIME'),
            ('hop_dong_loai_kh', 'VARCHAR(200)'),
            ('hop_dong_thanh_toan', 'VARCHAR(500)'),
        ]

        # Kiểm tra và thêm các cột cho COMPANY_INFO
        print("\n🔧 Kiểm tra bảng COMPANY_INFO...")
        for col_name, col_type in columns_to_add:
            try:
                # Thử thêm cột
                cursor.execute(f'ALTER TABLE COMPANY_INFO ADD COLUMN {col_name} {col_type}')
                print(f"✅ Đã thêm cột: {col_name}")
            except sqlite3.OperationalError as e:
                if 'duplicate column name' in str(e):
                    print(f"⚠️ Cột {col_name} đã tồn tại, bỏ qua")
                else:
                    print(f"❌ Lỗi thêm cột {col_name}: {e}")
                    raise

        conn.commit()
        conn.close()

        print("\n" + "="*60)
        print("✅ Migration hoàn tất!")
        print("="*60)
        print("\nBây giờ bạn có thể chạy:")
        print("  python scripts/seed_tax_companies.py --data app/data/companies.json")

    except Exception as e:
        print(f"❌ Lỗi migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    add_missing_columns()
