# File: app/services/drive_service.py

import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Cấu hình Scopes
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")


def get_drive_service():
    """
    Khởi tạo Google Drive Service sử dụng Service Account
    """
    creds_path = SERVICE_ACCOUNT_FILE
    if not creds_path or not os.path.exists(creds_path):
        raise FileNotFoundError(f"Không tìm thấy file credentials tại: {creds_path}. Hãy kiểm tra file .env")

    creds = service_account.Credentials.from_service_account_file(
        creds_path, 
        scopes=SCOPES
    )
    service = build('drive', 'v3', credentials=creds)
    return service


def browse_drive_folder(drive_folder_id: str):
    """
    Lấy danh sách file/folder con bên trong một folder ID cụ thể
    """
    service = get_drive_service()
    try:
        results = service.files().list(
            q=f"'{drive_folder_id}' in parents and trashed = false",
            fields="files(id, name, mimeType, webViewLink, iconLink, createdTime)",
            orderBy="folder, name",
            pageSize=1000,
            supportsAllDrives=True,
            supportsTeamDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        
        return results.get('files', [])
    except Exception as e:
        print(f"Lỗi browse_drive_folder: {e}")
        return []


def get_drive_permissions(service, file_id: str):
    """
    Lấy danh sách thành viên. Bắt buộc Bot phải có quyền Manager.
    """
    try:
        results = service.permissions().list(
            fileId=file_id,
            fields="permissions(id, displayName, emailAddress, role, type)",
            supportsAllDrives=True,
            supportsTeamDrives=True,
            useDomainAdminAccess=False 
        ).execute()
        
        raw_permissions = results.get('permissions', [])
        processed = []
        
        role_map = {
            "organizer": "Manager",
            "fileOrganizer": "Content Manager",
            "writer": "Contributor",
            "commenter": "Commenter",
            "reader": "Viewer"
        }
        
        for p in raw_permissions:
            if p.get('type') in ['user', 'group']:
                email = p.get('emailAddress', 'N/A')
                if "gserviceaccount.com" in email:
                    continue
                    
                role = p.get('role', 'reader')
                processed.append({
                    "name": p.get('displayName') or email.split('@')[0],
                    "email": email,
                    "role": role,
                    "role_display": role_map.get(role, role.capitalize())
                })
        
        return processed
    except Exception as e:
        print(f"❌ Lỗi API Google Permissions: {e}")
        return []


def find_child_folder_by_name_contain(service, parent_id, name_part):
    """
    Tìm folder con có tên CHỨA từ khóa (Ví dụ: TAI-LIEU-THUE)
    """
    try:
        query = (
            f"'{parent_id}' in parents "
            f"and name contains '{name_part}' "
            "and mimeType = 'application/vnd.google-apps.folder' "
            "and trashed = false"
        )
        results = service.files().list(
            q=query,
            fields="files(id, name)",
            supportsAllDrives=True,
            supportsTeamDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        files = results.get('files', [])
        return files[0] if files else None
    except Exception as e:
        print(f"Lỗi find_child_folder_by_name_contain: {e}")
        return None


def find_child_folder_exact(service, parent_id, exact_name):
    """
    Tìm folder con có tên CHÍNH XÁC (Ví dụ: '2024')
    """
    try:
        query = (
            f"'{parent_id}' in parents "
            f"and name = '{exact_name}' "
            "and mimeType = 'application/vnd.google-apps.folder' "
            "and trashed = false"
        )
        results = service.files().list(
            q=query,
            fields="files(id, name)",
            supportsAllDrives=True,
            supportsTeamDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        files = results.get('files', [])
        return files[0] if files else None
    except Exception as e:
        print(f"Lỗi find_child_folder_exact: {e}")
        return None


def add_permission(service, file_id, email, role="fileOrganizer"):
    """
    Cấp quyền đích danh trên một folder con.
    """
    try:
        service.permissions().create(
            fileId=file_id,
            body={
                "type": "user",
                "role": role,
                "emailAddress": email
            },
            supportsAllDrives=True,
            supportsTeamDrives=True,
            sendNotificationEmail=False
        ).execute()
        return True
    except Exception as e:
        print(f"Lỗi nâng cấp quyền Content Manager cho {email}: {e}")
        return False


def remove_permission_by_email(service, file_id, email):
    """
    Xóa quyền truy cập bằng email
    """
    try:
        permissions = service.permissions().list(
            fileId=file_id,
            fields="permissions(id, emailAddress)",
            supportsAllDrives=True
        ).execute()

        perm_id = next((p['id'] for p in permissions.get('permissions', []) 
                       if p.get('emailAddress', '').lower() == email.lower()), None)
        
        if perm_id:
            service.permissions().delete(
                fileId=file_id,
                permissionId=perm_id,
                supportsAllDrives=True
            ).execute()
    except Exception as e:
        print(f"Lỗi remove_permission {file_id}: {e}")


def create_drive_shortcut(service, target_id, parent_id, name):
    """
    Tạo shortcut trỏ đến target_id, đặt trong parent_id (support Shared Drive)
    """
    try:
        service.files().create(
            body={
                "name": name,
                "mimeType": "application/vnd.google-apps.shortcut",
                "parents": [parent_id],
                "shortcutDetails": {"targetId": target_id}
            },
            supportsAllDrives=True,
            supportsTeamDrives=True
        ).execute()
    except Exception as e:
        print(f"Lỗi tạo shortcut: {e}")


def rename_drive_file(service, file_id, new_name):
    """
    Đổi tên file hoặc folder trên Google Drive
    """
    try:
        service.files().update(
            fileId=file_id,
            body={"name": new_name},
            supportsAllDrives=True
        ).execute()
        return True
    except Exception as e:
        print(f"Lỗi rename {file_id}: {e}")
        return False


def list_drive_subfolders(service, parent_id):
    """
    Lấy danh sách toàn bộ folder con trực tiếp của parent_id
    """
    folders = []
    page_token = None
    while True:
        try:
            query = (
                f"'{parent_id}' in parents "
                "and mimeType = 'application/vnd.google-apps.folder' "
                "and trashed = false"
            )
            response = service.files().list(
                q=query,
                spaces='drive',
                fields='nextPageToken, files(id, name, webViewLink)',
                pageToken=page_token,
                supportsAllDrives=True,
            supportsTeamDrives=True,
                includeItemsFromAllDrives=True,
                pageSize=1000
            ).execute()

            folders.extend(response.get('files', []))
            page_token = response.get('nextPageToken')
            if not page_token:
                break
        except Exception as e:
            print(f"Lỗi khi list folder: {e}")
            break
    return folders



def find_shortcuts_by_target_id(service, parent_id, target_id):
    """
    Tìm tất cả shortcut trong folder parent_id có pointing tới target_id.
    Trả về list của shortcut IDs.

    Args:
        service: Google Drive service
        parent_id: Folder ID để tìm shortcut
        target_id: Target folder ID mà shortcut pointing tới

    Returns:
        List của shortcut IDs
    """
    shortcut_ids = []
    try:
        # List tất cả shortcut trong folder
        query = (
            f"'{parent_id}' in parents "
            "and mimeType = 'application/vnd.google-apps.shortcut' "
            "and trashed = false"
        )
        results = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, shortcutDetails)',
            pageSize=1000,
            supportsAllDrives=True,
            supportsTeamDrives=True,
            includeItemsFromAllDrives=True
        ).execute()

        files = results.get('files', [])
        for f in files:
            shortcut_details = f.get('shortcutDetails', {})
            if shortcut_details.get('targetId') == target_id:
                shortcut_ids.append(f['id'])
    except Exception as e:
        print(f"Lỗi find_shortcuts_by_target_id: {e}")

    return shortcut_ids


def get_all_files_recursive(service, parent_id, include_extended_fields=True):
    """
    Tìm tất cả file trong folder và các folder con sâu vô tận.

    include_extended_fields:
    - True: trả thêm webViewLink/createdTime (mặc định, tương thích ngược).
    - False: chỉ trả id/name/mimeType để giảm payload và tăng tốc.
    """
    all_files = []
    try:
        file_fields = "files(id, name, mimeType, webViewLink, createdTime)" if include_extended_fields else "files(id, name, mimeType)"
        page_token = None
        while True:
            results = service.files().list(
                q=f"'{parent_id}' in parents and trashed = false",
                fields=f"nextPageToken, {file_fields}",
                supportsAllDrives=True,
            supportsTeamDrives=True,
                includeItemsFromAllDrives=True,
                pageSize=1000,
                pageToken=page_token
            ).execute()
            items = results.get('files', [])

            for item in items:
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    all_files.extend(get_all_files_recursive(service, item['id'], include_extended_fields=include_extended_fields))
                else:
                    all_files.append(item)

            page_token = results.get('nextPageToken')
            if not page_token:
                break
    except Exception as e:
        print(f"Lỗi get_all_files_recursive({parent_id}): {e}")
    return all_files