# Migration Script - Tạo bảng WORK_LINKS

import sqlite3

def migrate_create_work_links():
    conn = sqlite3.connect('cenvi_audit.db')
    cursor = conn.cursor()
    
    try:
        # Tạo bảng WORK_LINKS
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS WORK_LINKS (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(255) NOT NULL,
                des VARCHAR(1000),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✓ Đã tạo bảng WORK_LINKS")
        
        conn.commit()
        print("✅ Migration hoàn tất!")
        
    except sqlite3.OperationalError as e:
        if "already exists" in str(e):
            print("⚠ Bảng WORK_LINKS đã tồn tại")
        else:
            print(f"❌ Lỗi: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_create_work_links()
