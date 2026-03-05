"""
Script để cập nhật database: Thêm cột Ngay_Het_Hieu_Luc vào bảng TAI_LIEU và MUC_CON
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "cenvi_audit.db"

def migrate_database():
    """Thêm cột Ngay_Het_Hieu_Luc vào các bảng"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        print("🔄 Bắt đầu migrate database...")
        
        # 1. Thêm cột Ngay_Het_Hieu_Luc vào bảng TAI_LIEU
        print("📝 Thêm cột Ngay_Het_Hieu_Luc vào bảng TAI_LIEU...")
        try:
            cursor.execute("""
                ALTER TABLE TAI_LIEU 
                ADD COLUMN Ngay_Het_Hieu_Luc DATETIME
            """)
            print("✅ Đã thêm cột Ngay_Het_Hieu_Luc vào TAI_LIEU")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e):
                print("⚠️  Cột Ngay_Het_Hieu_Luc đã tồn tại trong TAI_LIEU")
            else:
                raise
        
        # 2. Thêm cột Ngay_Het_Hieu_Luc vào bảng MUC_CON
        print("📝 Thêm cột Ngay_Het_Hieu_Luc vào bảng MUC_CON...")
        try:
            cursor.execute("""
                ALTER TABLE MUC_CON 
                ADD COLUMN Ngay_Het_Hieu_Luc DATETIME
            """)
            print("✅ Đã thêm cột Ngay_Het_Hieu_Luc vào MUC_CON")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e):
                print("⚠️  Cột Ngay_Het_Hieu_Luc đã tồn tại trong MUC_CON")
            else:
                raise
        
        # 3. Commit các thay đổi
        conn.commit()
        print("\n✅ Migration hoàn tất thành công!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Lỗi migrate: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
