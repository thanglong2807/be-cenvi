from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os
import json
from datetime import datetime
from googleapiclient.errors import HttpError
# --- CẤU HÌNH ---
# Dùng quyền full để đảm bảo đọc được hết
SCOPES = ["https://www.googleapis.com/auth/drive"] 
ROOT_FOLDER_ID = "1A_Q8yu8jn80yP0QHh2YYbfmnVwtjkQLy"
OUTPUT_FILE = "data_output_managers.json"

# --- DANH SÁCH NHÂN VIÊN ---
EMPLOYEE_MAPPING = {
    "nhan.phan@cenvi.vn": 1,
    "lien.nguyen@cenvi.vn": 2,
    "phuong.tran.cenvi@gmail.com": 3,
    "van.vuong.cenvi@gmail.com": 4,
    "nhungdo.cenvi@gmail.com": 5,
    "minh66tk@gmail.com": 6,
    "qanh110603@gmail.com": 7,
    "trankhoi.forwork@gmail.com": 8,
    "hongnt901@gmail.com": 9,
    "nguyenlananh2974@gmail.com": 10
}

# ===== 1. AUTH =====
def get_drive_service():
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    return build("drive", "v3", credentials=creds)

# ===== 2. HÀM QUÉT MANAGER CỦA 1 FOLDER CỤ THỂ =====
def get_folder_manager(service, folder_id, folder_name):
    """
    Trả về ID nhân viên quản lý folder này.
    Nếu lỗi hoặc không tìm thấy ai, trả về 1.
    """
    try:
        # Gọi API lấy quyền
        # ĐÃ BỎ: useDomainAdminAccess=True (Nguyên nhân gây lỗi)
        results = service.permissions().list(
            fileId=folder_id,
            fields="permissions(emailAddress, role)",
            supportsAllDrives=True 
        ).execute()
        
        perms = results.get('permissions', [])
        
        for p in perms:
            email = p.get('emailAddress', '').lower()
            role = p.get('role')
            
            # Kiểm tra xem email có trong danh sách nhân viên không
            # role 'fileOrganizer' là Content Manager
            # role 'organizer' là Manager
            # role 'writer' là Contributor/Editor
            if role in ['fileOrganizer', 'organizer', 'writer']:
                if email in EMPLOYEE_MAPPING:
                    # print(f"✅ Found Manager: {email} for {folder_name}") # Bật nếu muốn xem
                    return EMPLOYEE_MAPPING[email]
        
        return 1 # Không tìm thấy nhân viên nào trong list -> Trả về mặc định

    except HttpError as error:
        # Bắt lỗi HTTP (404, 403...) để không làm dừng chương trình
        print(f"⚠️ Không thể check quyền folder '{folder_name}' (ID: {folder_id})")
        print(f"   Lý do: {error.resp.status} - {error.resp.reason}")
        return 1 # Gặp lỗi thì trả về mặc định là 1
        
    except Exception as e:
        # Bắt các lỗi khác
        print(f"❌ Lỗi không xác định folder '{folder_name}': {e}")
        return 1

# ===== 3. LOGIC CHÍNH =====
def scan_and_export_json():
    service = get_drive_service()
    
    # 1. Lấy danh sách folder
    print("📂 Đang lấy danh sách folder...")
    all_folders = []
    page_token = None
    while True:
        res = service.files().list(
            q=f"'{ROOT_FOLDER_ID}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
            corpora="allDrives", includeItemsFromAllDrives=True, supportsAllDrives=True,
            pageSize=1000, fields="nextPageToken, files(id, name, createdTime)", pageToken=page_token
        ).execute()
        all_folders.extend(res.get('files', []))
        page_token = res.get('nextPageToken')
        if not page_token: break

    print(f"🔍 Tìm thấy {len(all_folders)} folder. Đang quét quyền từng folder...")

    items = []
    current_id = 1
    current_timestamp = datetime.now().isoformat()

    for f in all_folders:
        folder_name = f["name"]
        folder_id = f["id"]
        
        # --- QUAN TRỌNG: GỌI HÀM CHECK MANAGER DỰA VÀO ID FOLDER ---
        manager_id = get_folder_manager(service, folder_id, folder_name)
        
        # Xử lý tên và MST
        parts = folder_name.split('_')
        if len(parts) >= 3:
            code, mst, name = parts[0].strip(), parts[-1].strip(), "_".join(parts[1:-1]).strip()
        elif len(parts) == 2:
            code, name, mst = parts[0].strip(), parts[1].strip(), ""
        else:
            code, name, mst = folder_name, folder_name, ""
            
        try:
            year = int(f.get("createdTime", "")[:4])
        except:
            year = datetime.now().year

        items.append({
            "company_code": code,
            "company_name": name,
            "mst": mst,
            "manager_employee_id": manager_id, # Đã map ID chuẩn
            "year": year,
            "template": "STANDARD",
            "created_at": current_timestamp,
            "updated_at": current_timestamp,
            "status": "active",
            "root_folder_id": folder_id,
            "id": current_id
        })
        current_id += 1

    # Xuất file
    final_data = {"last_id": items[-1]['id'] if items else 0, "items": items}
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    print(f"🎉 Xong! File lưu tại {OUTPUT_FILE}")

if __name__ == "__main__":
    scan_and_export_json()