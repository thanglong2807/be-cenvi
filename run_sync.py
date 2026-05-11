#!/usr/bin/env python3
"""
Quick sync script to synchronize COMPANY_INFO with FOLDERS
Run this to sync without needing the API
"""
import sys
import codecs
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Fix Unicode encoding for Windows
if sys.platform == "win32":
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

# Import models and config
from app.core.database import engine, get_db
from app.core.config import settings
from app.services.sync_service import SyncService
from sqlalchemy.orm import Session

print("=" * 100)
print("COMPANY_INFO ↔ FOLDERS SYNC TOOL")
print("=" * 100)
print()

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    # Step 1: Show current status
    print("📊 SYNC STATUS:")
    print("-" * 100)
    status = SyncService.get_sync_status(db)
    print(f"  Total Companies in COMPANY_INFO: {status['total_companies']}")
    print(f"  Total Folders in FOLDERS: {status['total_folders']}")
    print(f"  Missing Folders: {status['missing_folders']}")
    print(f"  Sync Percentage: {status['sync_percentage']:.1f}%")
    print(f"  Sample Missing Codes: {', '.join(status['missing_company_codes'][:5])}")
    print()

    if status['missing_folders'] == 0:
        print("✅ All companies have folder records!")
        print()
    else:
        # Step 2: Create missing folders
        print("🔧 CREATING MISSING FOLDERS...")
        print("-" * 100)
        create_result = SyncService.sync_missing_folders(db)
        print(f"  Status: {create_result['status']}")
        print(f"  Message: {create_result['message']}")
        print(f"  Created: {create_result['created']} folders")
        if create_result['errors']:
            print(f"  Errors: {len(create_result['errors'])}")
            for error in create_result['errors'][:5]:  # Show first 5 errors
                print(f"    - {error}")
        print()

    # Step 3: Update folder data
    print("📝 UPDATING FOLDER DATA FROM COMPANY_INFO...")
    print("-" * 100)
    update_result = SyncService.sync_folder_data(db)
    print(f"  Status: {update_result['status']}")
    print(f"  Message: {update_result['message']}")
    print(f"  Updated: {update_result['updated']} folders")
    if update_result['errors']:
        print(f"  Errors: {len(update_result['errors'])}")
        for error in update_result['errors'][:5]:  # Show first 5 errors
            print(f"    - {error}")
    print()

    # Step 4: Show final status
    print("✅ FINAL STATUS:")
    print("-" * 100)
    final_status = SyncService.get_sync_status(db)
    print(f"  Total Companies: {final_status['total_companies']}")
    print(f"  Total Folders: {final_status['total_folders']}")
    print(f"  Missing Folders: {final_status['missing_folders']}")
    print(f"  Sync Percentage: {final_status['sync_percentage']:.1f}%")
    print()

    print("=" * 100)
    if final_status['missing_folders'] == 0:
        print("✅ SYNC COMPLETE! All companies are synced with folders.")
    else:
        print(f"⚠️  SYNC PARTIALLY COMPLETE! Still {final_status['missing_folders']} missing folders.")
    print("=" * 100)

except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()

finally:
    db.close()
