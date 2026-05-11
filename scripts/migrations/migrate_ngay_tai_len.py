import sqlite3
from datetime import datetime

def migrate_add_ngay_tai_len():
    conn = sqlite3.connect('cenvi_audit.db')
    cursor = conn.cursor()
    
    try:
        # Thêm cột Ngay_Tai_Len vào bảng PHIEN_BAN_TAI_LIEU
        cursor.execute("""
            ALTER TABLE PHIEN_BAN_TAI_LIEU 
            ADD COLUMN Ngay_Tai_Len TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        """)
        print("✓ Đã thêm cột Ngay_Tai_Len vào PHIEN_BAN_TAI_LIEU")
        
        # Cập nhật các bản ghi cũ với timestamp hiện tại
        cursor.execute("""
            UPDATE PHIEN_BAN_TAI_LIEU 
            SET Ngay_Tai_Len = CURRENT_TIMESTAMP 
            WHERE Ngay_Tai_Len IS NULL
        """)
        print("✓ Đã cập nhật timestamp cho các bản ghi cũ")
        
        conn.commit()
        print("✅ Migration hoàn tất!")
        
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("⚠ Cột Ngay_Tai_Len đã tồn tại")
        else:
            print(f"❌ Lỗi: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_add_ngay_tai_len()
