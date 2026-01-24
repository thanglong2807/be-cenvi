# app/services/drive_folder_builder.py

from app.services.drive_service import get_drive_service
from app.core.folder_templates import FOLDER_TEMPLATES

def find_folder_in_parent(service, parent_id, name):
    """Tìm xem folder con đã tồn tại chưa"""
    try:
        query = (
            f"'{parent_id}' in parents "
            f"and name = '{name}' "
            "and mimeType = 'application/vnd.google-apps.folder' "
            "and trashed = false"
        )
        results = service.files().list(
            q=query, 
            fields="files(id)", 
            pageSize=1,
            supportsAllDrives=True, 
            includeItemsFromAllDrives=True
        ).execute()
        files = results.get('files', [])
        return files[0]['id'] if files else None
    except:
        return None

def get_or_create_folder(service, name, parent_id, cache):
    """
    Nếu có rồi thì lấy ID, chưa có thì tạo mới.
    Sử dụng cache để tránh gọi API quá nhiều.
    """
    cache_key = f"{parent_id}/{name}"
    
    # 1. Check cache cục bộ (trong lần chạy này)
    if cache_key in cache:
        return cache[cache_key]

    # 2. Check trên Google Drive (tránh trùng với lần chạy trước)
    existing_id = find_folder_in_parent(service, parent_id, name)
    if existing_id:
        cache[cache_key] = existing_id
        return existing_id

    # 3. Nếu chưa có -> Tạo mới
    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id]
    }
    folder = service.files().create(
        body=metadata,
        fields="id",
        supportsAllDrives=True
    ).execute()
    
    new_id = folder["id"]
    cache[cache_key] = new_id
    return new_id


def apply_template(
    service, # Nhận service từ bên ngoài
    parent_folder_id: str,
    template_name: str,
    company_short_name: str,
    year: int
):
    paths = FOLDER_TEMPLATES.get(template_name, [])
    
    # Cache lưu các folder đã xử lý trong phiên này: Key = "ParentID/Name" -> Value = ID
    folder_cache = {} 

    for path in paths:
        # Resolve placeholder
        resolved = (
            path
            .replace("{TENVT}", company_short_name)
            .replace("{Y}", str(year))
        )

        parts = resolved.split("/")
        current_parent = parent_folder_id

        for part in parts:
            part = part.strip()
            if not part: continue
            
            # Hàm này sẽ tự quyết định lấy ID cũ hay tạo mới
            folder_id = get_or_create_folder(service, part, current_parent, folder_cache)
            
            current_parent = folder_id