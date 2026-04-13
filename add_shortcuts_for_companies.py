#!/usr/bin/env python3
"""
Batch add shortcuts for all companies to their manager's folder
"""
import sys
from db_connection import DBConnection

print("=" * 100)
print("ADD SHORTCUTS FOR COMPANIES")
print("=" * 100)
print()

db = DBConnection()
if not db.connect():
    print("❌ Database connection failed!")
    sys.exit(1)

print("✅ Database connected")

# Get all companies with managers
print("\n⏳ Fetching companies and employees...")
companies = db.execute_query("""
    SELECT
        c.id,
        c.ma_kh,
        c.ten_cong_ty,
        c.drive_folder_id,
        c.phu_trach_hien_tai,
        e.id as employee_id,
        e.name as employee_name,
        e.drive_folder_id as employee_folder_id
    FROM COMPANY_INFO c
    LEFT JOIN employees e ON c.phu_trach_hien_tai = e.name
    WHERE c.drive_folder_id IS NOT NULL
    AND c.drive_folder_id != ''
    ORDER BY c.created_at DESC
""")

if not companies:
    print("❌ No companies found!")
    sys.exit(1)

print(f"✅ Found {len(companies)} companies")

# Try to add shortcuts
success_count = 0
skip_count = 0
error_count = 0
errors = []

try:
    from app.services.drive_service import get_drive_service
    drive = get_drive_service()
    print("✅ Drive service initialized")
except Exception as e:
    print(f"❌ Failed to initialize Drive service: {e}")
    sys.exit(1)

print("\n" + "-" * 100)
print("Adding shortcuts...")
print("-" * 100)

for i, company in enumerate(companies, 1):
    ma_kh = company['ma_kh']
    company_folder_id = company['drive_folder_id']
    employee_name = company['employee_name']
    employee_folder_id = company['employee_folder_id']

    # Check if employee exists and has folder
    if not employee_name:
        print(f"\n[{i}] ⏭️  {ma_kh}: Không có người phụ trách → bỏ qua")
        skip_count += 1
        continue

    if not employee_folder_id:
        print(f"\n[{i}] ⏭️  {ma_kh}: Nhân viên {employee_name} chưa có Drive folder → bỏ qua")
        skip_count += 1
        continue

    # Try to create shortcut
    print(f"\n[{i}] {ma_kh} ({employee_name})")
    try:
        # Get company folder name from Drive
        try:
            company_folder = drive.files().get(
                fileId=company_folder_id,
                fields='name',
                supportsAllDrives=True,
                supportsTeamDrives=True
            ).execute()
            shortcut_name = company_folder['name']
        except Exception as e:
            print(f"   ⚠️  Không lấy được tên folder, dùng mã_kh: {e}")
            shortcut_name = ma_kh

        # Check if shortcut already exists
        query = f"name = '{shortcut_name}' and '{employee_folder_id}' in parents and mimeType = 'application/vnd.google-apps.shortcut' and trashed = false"
        results = drive.files().list(
            q=query,
            spaces='drive',
            fields='files(id)',
            pageSize=1,
            supportsAllDrives=True,
            supportsTeamDrives=True
        ).execute()

        if results.get('files'):
            print(f"   ✅ Shortcut already exists")
            success_count += 1
            continue

        # Create shortcut
        shortcut_metadata = {
            'name': shortcut_name,
            'mimeType': 'application/vnd.google-apps.shortcut',
            'shortcutDetails': {
                'targetId': company_folder_id
            },
            'parents': [employee_folder_id]
        }

        shortcut = drive.files().create(
            body=shortcut_metadata,
            fields='id, name',
            supportsAllDrives=True,
            supportsTeamDrives=True
        ).execute()

        print(f"   ✅ Created shortcut '{shortcut['name']}'")
        success_count += 1

    except Exception as e:
        error_msg = f"{ma_kh}: {str(e)}"
        print(f"   ❌ Error: {error_msg}")
        errors.append(error_msg)
        error_count += 1

# Summary
print("\n" + "=" * 100)
print("SUMMARY")
print("=" * 100)
print(f"✅ Created/Exists: {success_count}")
print(f"⏭️  Skipped: {skip_count}")
print(f"❌ Errors: {error_count}")

if errors:
    print(f"\nError details:")
    for error in errors:
        print(f"  - {error}")

print("\n" + "=" * 100)
db.disconnect()
