"""
Helper script để list tất cả sheet names trong Google Sheet
"""

import os
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Load .env
load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SHEET_ID = "1KF68El6c5-_2QwybKa2k-3N149L-xYU2-h6SsSAUXno"

creds_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
if not creds_path or not os.path.exists(creds_path):
    print(f"❌ Credentials không tìm thấy: {creds_path}")
    print(f"   Kiểm tra .env file")
    exit(1)

creds = service_account.Credentials.from_service_account_file(creds_path, scopes=SCOPES)
service = build('sheets', 'v4', credentials=creds)

try:
    spreadsheet = service.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
    sheets = spreadsheet.get('sheets', [])
    
    print(f"\n📊 Tổng {len(sheets)} sheets:\n")
    for i, sheet in enumerate(sheets, 1):
        title = sheet['properties']['title']
        sheet_id = sheet['properties']['sheetId']
        print(f"{i:2d}. {title:40s} (gid={sheet_id})")
    
except Exception as e:
    print(f"❌ Error: {e}")
