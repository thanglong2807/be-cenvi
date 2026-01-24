import os
import re
from unidecode import unidecode
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# =========================
# CẤU HÌNH NGƯỜI DÙNG
# =========================

# ID CỦA THƯ MỤC GỐC (Shared Drive ID hoặc Folder ID)
ROOT_DIR_ID = '1A_N5N8nfMtluji8RY0Nvs22-w0qXXa-o' 

# CHẾ ĐỘ CHẠY
# True: CHỈ IN RA những thay đổi sẽ xảy ra (Dry Run).
# False: THỰC HIỆN đổi tên, COPY và XÓA (thực thi giải pháp).
DRY_RUN = False

# Tên file key của Service Account
SERVICE_ACCOUNT_FILE = 'service_account.json'

# Phạm vi (Scope) cho phép truy cập và thay đổi file trên Drive
SCOPES = ['https://www.googleapis.com/auth/drive'] 

# Danh sách MIME Type của các loại file Google Workspace Native (Bỏ qua)
GOOGLE_NATIVE_MIME_TYPES = [
    'application/vnd.google-apps.document',  
    'application/vnd.google-apps.spreadsheet',
    'application/vnd.google-apps.presentation',
    'application/vnd.google-apps.drawing',
    'application/vnd.google-apps.form',         
    'application/vnd.google-apps.shortcut',     
]

# =========================
# HÀM CHUẨN HÓA
# =========================

def normalize_vietnamese(name):
    """
    Chuyển tên từ tiếng Việt có dấu, có khoảng cách thành tiếng Việt không dấu,
    thay khoảng cách bằng gạch ngang (-). Chuyển '&' thành 'va'.
    """
    # 1. Thay thế '&' thành ' va '
    name = re.sub(r'&', ' va ', name)
    
    # 2. Bỏ dấu tiếng Việt
    name = unidecode(name)
    
    # 3. Chuyển thành chữ thường
    name = name.lower()
    
    # 4. Thay thế khoảng trắng, dấu chấm (.), dấu phẩy (,) bằng gạch ngang (-)
    name = re.sub(r'[.\s,]+', '-', name)

    # 5. Loại bỏ các ký tự đặc biệt khác và làm sạch các gạch ngang thừa
    name = re.sub(r'[^a-z0-9-]', '', name)
    name = re.sub(r'-+', '-', name).strip('-') 
    
    return name

# =========================
# HÀM API & LOGIC (CẬP NHẬT)
# =========================

def get_drive_service():
    """Tạo đối tượng dịch vụ Google Drive bằng Service Account."""
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

def rename_copy_delete_file(service, file_id, original_name, parent_id, dry_run=True):
    """Đổi tên, Copy thành file mới và Xóa file gốc đã đổi tên (CHỈ ÁP DỤNG CHO FILES)."""
    
    base_name, extension = os.path.splitext(original_name)
    
    new_base_name = normalize_vietnamese(base_name)
    temp_name = new_base_name + extension # Tên tạm thời (đã chuẩn hóa)
    
    # Bỏ qua nếu tên đã chuẩn hóa
    if original_name == temp_name:
        return True # Không cần làm gì
    
    if dry_run:
        print(f"[DRY RUN - FILE] \t'{original_name}' -> '{temp_name}' (Sẽ Copy/Xóa)")
        return True # Giả định thành công trong dry run

    try:
        # BƯỚC 1: Đổi tên file gốc thành tên chuẩn hóa (temp_name)
        # Việc này là cần thiết để chuẩn hóa tên trước khi copy
        service.files().update(
            fileId=file_id,
            body={'name': temp_name},
            supportsAllDrives=True
        ).execute()
        print(f"[ĐỔI THÀNH CÔNG] Tên file ID {file_id} -> '{temp_name}'")

        # BƯỚC 2: Copy file đã đổi tên đó, tạo ra file mới (Copy) với tên TỐT
        # Việc này tạo ra File ID mới, buộc Google Drive Desktop tạo đường dẫn sạch
        copied_file = service.files().copy(
            fileId=file_id,
            body={'name': temp_name, 'parents': [parent_id]}, # Giữ nguyên tên chuẩn hóa và trong cùng folder
            supportsAllDrives=True
        ).execute()
        print(f"[COPY THÀNH CÔNG] File mới '{copied_file['name']}' (ID: {copied_file['id']})")
        
        # BƯỚC 3: Xóa file gốc đã đổi tên (temp_name)
        service.files().delete(
            fileId=file_id,
            supportsAllDrives=True
        ).execute()
        print(f"[XÓA THÀNH CÔNG] File gốc ID {file_id}")
        
        return True # Thành công

    except HttpError as e:
        print(f"[LỖI Drive API] Không thể Rename/Copy/Delete file '{original_name}': {e}")
        return False # Thất bại

def rename_drive_folder(service, folder_id, original_name, dry_run=True):
    """Thực hiện đổi tên folder (Chỉ đổi tên, không copy/xóa)."""
    
    new_name = normalize_vietnamese(original_name)
    
    if original_name == new_name:
        return original_name # Không cần đổi tên
    
    if dry_run:
        print(f"[DRY RUN - THƯ MỤC] \t'{original_name}' -> '{new_name}'")
        return new_name

    try:
        service.files().update(
            fileId=folder_id,
            body={'name': new_name},
            supportsAllDrives=True
        ).execute()
        print(f"[ĐỔI THÀNH CÔNG - THƯ MỤC] \t'{original_name}' -> '{new_name}'")
        return new_name
    except HttpError as e:
        print(f"[LỖI Drive API] Không thể đổi tên thư mục '{original_name}': {e}")
            
    return original_name 

def list_files_and_folders(service, folder_id):
    """Lấy danh sách các mục (files và folders) bên trong một folder ID."""
    
    folder_mime_type = 'application/vnd.google-apps.folder'
    q = f"'{folder_id}' in parents and trashed=false"
    
    results = service.files().list(
        q=q,
        spaces='drive',
        fields='nextPageToken, files(id, name, mimeType, parents)',
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()
    
    items = results.get('files', [])
    
    folders = []
    files = []

    for item in items:
        mime_type = item['mimeType']
        
        if mime_type == folder_mime_type:
            folders.append(item)
        elif mime_type not in GOOGLE_NATIVE_MIME_TYPES:
            files.append(item)
            
    return folders, files

def recursive_rename(service, current_folder_id, dry_run):
    """Đệ quy duyệt và đổi tên tất cả các mục bên trong."""
    
    try:
        folders, files = list_files_and_folders(service, current_folder_id)
        
        # 1. ĐỔI TÊN FILES (TẤT CẢ FILE NON-NATIVE) -> BƯỚC NÀY GỒM COPY/XÓA
        for file in files:
            # Lấy parent_id từ file gốc để đảm bảo file copy nằm đúng chỗ
            parent_id = file['parents'][0] if file.get('parents') else current_folder_id 
            rename_copy_delete_file(service, file['id'], file['name'], parent_id, dry_run)
            
        # 2. Đệ quy vào FOLDERS
        for folder in folders:
            recursive_rename(service, folder['id'], dry_run)
            
        # 3. ĐỔI TÊN FOLDERS (sau khi đã đổi tên nội dung bên trong)
        for folder in folders:
            rename_drive_folder(service, folder['id'], folder['name'], dry_run)

    except HttpError as e:
        print(f"[LỖI Drive API] Lỗi khi truy cập folder ID {current_folder_id}: {e}")
        
def main():
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        print(f"LỖI: Không tìm thấy file {SERVICE_ACCOUNT_FILE}. Vui lòng tải về từ Google Cloud Console.")
        return
        
    if ROOT_DIR_ID == 'ĐƯỜNG DẪN THƯ MỤC CẦN ĐỔI TÊN':
        print("LỖI: Vui lòng thay đổi giá trị biến ROOT_DIR_ID.")
        return

    try:
        service = get_drive_service()
        
        print(f"Bắt đầu quá trình quét và đổi tên trên Google Drive (Dry Run: {DRY_RUN})...")
        
        root_info = service.files().get(fileId=ROOT_DIR_ID, fields='name', supportsAllDrives=True).execute()
        print(f"Thư mục gốc: {root_info.get('name', 'Không xác định')} (ID: {ROOT_DIR_ID})\n")
        
        recursive_rename(service, ROOT_DIR_ID, DRY_RUN)
        
        print("\nQuá trình đổi tên đã hoàn tất.")

    except Exception as e:
        print(f"LỖI CHUNG: {e}")


if __name__ == '__main__':
    main()