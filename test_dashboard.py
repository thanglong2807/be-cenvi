"""
Debug script để test fetch data từ Google Sheet
"""

import os
import sys
from dotenv import load_dotenv

# Load config
load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

from app.services.dashboard_sheet_service import dashboard_service
from app.core.config import settings

print("=" * 60)
print("🔍 DEBUG: Google Sheet Configuration")
print("=" * 60)

print(f"\n📋 Sheet Settings:")
print(f"  Sheet ID: {settings.GOOGLE_SHEET_ID}")
print(f"  Sheet Name: {settings.GOOGLE_SHEET_NAME}")
print(f"  Range: {settings.GOOGLE_SHEET_RANGE}")

# Test fetch
print(f"\n🔄 Testing fetch_data()...")

range_name = f"'{settings.GOOGLE_SHEET_NAME}'!{settings.GOOGLE_SHEET_RANGE}"
print(f"  Range Name: {range_name}")

data = dashboard_service.fetch_data(range_name)

if data:
    print(f"\n✅ SUCCESS! Dữ liệu lấy được:")
    print(f"  Rows: {data['rows_count']}")
    print(f"  Cols: {data['cols_count']}")
    print(f"  Timestamp: {data['timestamp']}")
    print(f"\n  📊 Sample data (5 rows):")
    for i, row in enumerate(data['data'][:5]):
        print(f"    Row {i}: {row[:5]}...")  # Show first 5 cols
else:
    print(f"\n❌ FAILED! Không lấy được dữ liệu")
    print(f"  Kiểm tra:")
    print(f"  1. Sheet name 'Hoa hồng' có đúng không?")
    print(f"  2. Google Sheets API đã enable chưa?")
    print(f"  3. Service account có quyền access sheet không?")
