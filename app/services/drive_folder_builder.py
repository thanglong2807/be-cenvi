# file drive_folder_builder.py
from app.core.folder_templates import FOLDER_TEMPLATES

# Xóa dòng import get_drive_service vì ta sẽ truyền service vào hàm

def create_drive_folder_api(service, name, parent_id):
    """
    Hàm helper gọi Google Drive API
    """
    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id]
    }
    
    # THÊM supportsAllDrives=True để hỗ trợ Shared Drive
    folder = service.files().create(
        body=metadata,
        fields="id",
        supportsAllDrives=True 
    ).execute()
    
    return folder["id"]


def apply_template(
    service,  # <--- THÊM tham số service
    parent_folder_id: str,
    template_name: str,
    company_short_name: str,
    year: int
):
    paths = FOLDER_TEMPLATES.get(template_name)
    if not paths:
        raise ValueError(f"Template '{template_name}' không tồn tại")

    created_cache = {} # Đổi tên biến cho rõ nghĩa

    for path in paths:
        # Resolve placeholder
        resolved_path = (
            path
            .replace("{TENVT}", company_short_name)
            .replace("{Y}", str(year))
        )

        parts = resolved_path.split("/")
        current_parent_id = parent_folder_id

        # Duyệt qua từng cấp thư mục trong path
        for part in parts:
            # Tạo key duy nhất để tránh tạo trùng folder trong cùng 1 lần chạy
            # Key dạng: ID_CHA/TEN_CON
            unique_key = f"{current_parent_id}/{part}"

            if unique_key not in created_cache:
                folder_id = create_drive_folder_api(service, part, current_parent_id)
                created_cache[unique_key] = folder_id
                current_parent_id = folder_id
            else:
                # Nếu đã tạo rồi thì lấy ID từ cache để làm cha cho folder tiếp theo
                current_parent_id = created_cache[unique_key]