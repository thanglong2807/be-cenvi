#!/usr/bin/env python3
"""
Setup trigger script - create trigger_auto_create_folder
"""
import sys
from db_connection import DBConnection

print("=" * 100)
print("SETTING UP TRIGGER: trigger_auto_create_folder")
print("=" * 100)
print()

# Connect to database
db = DBConnection()
if not db.connect():
    print("❌ Database connection failed!")
    sys.exit(1)

print("✅ Database connected")

# Execute SQL commands
print("\n⏳ Running SQL commands...")
print("-" * 100)

try:
    # Step 1: Use correct database
    print("\n[1] Using cenvi_audit database...")
    db.cursor.execute("USE cenvi_audit")
    db.connection.commit()
    print("✅ Success")

    # Step 2: Drop existing trigger
    print("\n[2] Dropping existing trigger if exists...")
    db.cursor.execute("DROP TRIGGER IF EXISTS trigger_auto_create_folder")
    db.connection.commit()
    print("✅ Success")

    # Step 3: Create log table
    print("\n[3] Creating trigger_logs table...")
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS trigger_logs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        trigger_name VARCHAR(100),
        action VARCHAR(50),
        error_message TEXT,
        created_at DATETIME
    )
    """
    db.cursor.execute(create_table_sql)
    db.connection.commit()
    print("✅ Success")

    # Step 4: Create trigger
    print("\n[4] Creating trigger_auto_create_folder...")
    trigger_sql = """
    CREATE TRIGGER trigger_auto_create_folder
    AFTER INSERT ON COMPANY_INFO
    FOR EACH ROW
    BEGIN
        DECLARE exit handler for sqlexception
        BEGIN
            INSERT INTO trigger_logs (trigger_name, action, error_message, created_at)
            VALUES ('trigger_auto_create_folder', 'INSERT', CONCAT('Error creating folder for ', NEW.ma_kh), NOW());
        END;

        INSERT IGNORE INTO FOLDERS (
            company_code,
            company_name,
            mst,
            year,
            template,
            status,
            root_folder_id,
            created_at,
            updated_at
        ) VALUES (
            NEW.ma_kh,
            COALESCE(NEW.ten_cong_ty_viet_tat, SUBSTRING(NEW.ten_cong_ty, 1, 50)),
            NEW.ma_so_thue,
            COALESCE(NEW.folder_year, YEAR(NOW())),
            COALESCE(NEW.folder_template, 'STANDARD'),
            COALESCE(NEW.folder_status, 'active'),
            NEW.drive_folder_id,
            NOW(),
            NOW()
        );
    END
    """
    db.cursor.execute(trigger_sql)
    db.connection.commit()
    print("✅ Success")

    print("\n" + "-" * 100)
    print("✅ All SQL commands executed successfully!")

    # Verify trigger exists
    print("\n✅ Verifying trigger...")
    result = db.execute_query("""
        SELECT TRIGGER_NAME, EVENT_MANIPULATION, TRIGGER_SCHEMA
        FROM INFORMATION_SCHEMA.TRIGGERS
        WHERE TRIGGER_NAME = 'trigger_auto_create_folder'
    """)

    if result:
        trigger = result[0]
        print(f"✅ Trigger verified:")
        print(f"   Name: {trigger['TRIGGER_NAME']}")
        print(f"   Event: {trigger['EVENT_MANIPULATION']}")
        print(f"   Schema: {trigger['TRIGGER_SCHEMA']}")
    else:
        print("⚠️  Trigger not found!")
        sys.exit(1)

except Exception as e:
    print(f"❌ Error executing SQL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

finally:
    db.disconnect()

print("\n" + "=" * 100)
print("SETUP COMPLETE!")
print("=" * 100)
print("\n✅ Trigger is ready to use!")
print("   When you add a company to COMPANY_INFO, FOLDERS record will be created automatically")
