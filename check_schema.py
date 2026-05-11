#!/usr/bin/env python3
"""
Check COMPANY_INFO and FOLDERS table structure
"""
from db_connection import DBConnection

db = DBConnection()
if not db.connect():
    exit(1)

# Get COMPANY_INFO structure
print("=" * 100)
print("COMPANY_INFO TABLE STRUCTURE")
print("=" * 100)
result = db.execute_query("DESCRIBE COMPANY_INFO")
if result:
    for row in result:
        print(f"  {row['Field']:<30} {row['Type']:<30} Null:{row.get('Null', ''):<5} Key:{row.get('Key', '')}")

print("\n" + "=" * 100)
print("FOLDERS TABLE STRUCTURE")
print("=" * 100)
result = db.execute_query("DESCRIBE FOLDERS")
if result:
    for row in result:
        print(f"  {row['Field']:<30} {row['Type']:<30} Null:{row.get('Null', ''):<5} Key:{row.get('Key', '')}")
else:
    print("⚠️  FOLDERS table might not exist")

print("\n" + "=" * 100)
print("SAMPLE - COMPANY_INFO (first 1)")
print("=" * 100)
result = db.execute_query("SELECT * FROM COMPANY_INFO LIMIT 1")
if result:
    company = result[0]
    for key, val in company.items():
        print(f"  {key}: {val}")

print("\n" + "=" * 100)
print("SAMPLE - FOLDERS (first 1)")
print("=" * 100)
result = db.execute_query("SELECT * FROM FOLDERS LIMIT 1")
if result:
    folder = result[0]
    for key, val in folder.items():
        print(f"  {key}: {val}")
else:
    print("⚠️  No folders found or table doesn't exist")

print("\n" + "=" * 100)
print("COUNTS")
print("=" * 100)
result = db.execute_query("SELECT COUNT(*) as total FROM COMPANY_INFO")
print(f"  COMPANY_INFO: {result[0]['total']} records")

result = db.execute_query("SELECT COUNT(*) as total FROM FOLDERS")
if result:
    print(f"  FOLDERS: {result[0]['total']} records")
else:
    print("  FOLDERS: table doesn't exist or error")

db.disconnect()
