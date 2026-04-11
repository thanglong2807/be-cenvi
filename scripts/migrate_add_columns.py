#!/usr/bin/env python3
"""
Script to add missing columns to COMPANY_INFO table without losing data
"""

import sys
import os
import sqlite3

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

SQLITE_PATH = os.path.join(os.path.dirname(__file__), '..', 'cenvi_audit.db')

def add_missing_columns():
    """Add missing columns to COMPANY_INFO table"""

    try:
        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()

        # Danh sách các cột cần thêm
        columns_to_add = [
            ('ten_cong_ty_viet_tat', 'VARCHAR(200)'),
            ('pmkt_ten', 'VARCHAR(200)'),
            ('pmkt_link', 'VARCHAR(500)'),
            ('pmkt_tai_khoan', 'VARCHAR(200)'),
            ('pmkt_mat_khau', 'VARCHAR(500)'),
        ]

        # Kiểm tra và thêm các cột
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
