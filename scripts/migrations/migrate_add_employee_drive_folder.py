#!/usr/bin/env python3
"""
Migration: Add drive_folder_id column to employees table
"""
import sys
from db_connection import DBConnection

print("=" * 100)
print("MIGRATION: Add drive_folder_id to employees table")
print("=" * 100)
print()

db = DBConnection()
if not db.connect():
    print("❌ Database connection failed!")
    sys.exit(1)

print("✅ Database connected")

try:
    # Step 1: Check if column exists
    print("\n[1] Checking if drive_folder_id column exists...")
    result = db.execute_query("""
        SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'employees' AND COLUMN_NAME = 'drive_folder_id'
    """)

    if result:
        print("✅ Column already exists")
    else:
        print("⏳ Column does not exist, adding...")

        # Add column
        db.cursor.execute("""
            ALTER TABLE employees
            ADD COLUMN drive_folder_id VARCHAR(255) NULL
            AFTER email
        """)
        db.connection.commit()
        print("✅ Column added successfully")

    # Step 2: Verify
    print("\n[2] Verifying employees table structure...")
    result = db.execute_query("DESCRIBE employees")
    if result:
        print("✅ Table structure:")
        for row in result:
            print(f"   {row['Field']:20} | {row['Type']:30} | {row['Null']:5}")

    print("\n" + "=" * 100)
    print("MIGRATION COMPLETE!")
    print("=" * 100)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

finally:
    db.disconnect()
