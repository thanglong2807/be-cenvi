import os

from app.services.drive_service import get_drive_service
from app.services.drive_folder_builder import apply_template
from app.db.repositories.folder_repo import FolderRepository
from app.db.repositories.employee_repo import EmployeeRepository
from app.core.folder_templates import FOLDER_TEMPLATES

# ========= LOAD ENV =========
ROOT_DRIVE_FOLDER_ID = os.getenv("COMPANY_PARENT_FOLDER_ID")
if not ROOT_DRIVE_FOLDER_ID:
    raise RuntimeError("ROOT_DRIVE_FOLDER_ID chưa được khai báo trong .env")

# ========= REPOSITORIES =========
folder_repo = FolderRepository()
employee_repo = EmployeeRepository()


# ========= READ =========
def list_folders():
    return folder_repo.get_all()


def get_folder(folder_id: int):
    return folder_repo.get_by_id(folder_id)


def get_folders_by_employee(employee_id: int):
    return folder_repo.get_by_employee(employee_id)


# ========= CREATE (GẮN DRIVE) =========
def create_folder(data: dict):
    # 1. Check nhân viên
    if not employee_repo.get_by_id(data["manager_employee_id"]):
        raise ValueError("Nhân viên quản lý không tồn tại")

    # 2. Check template
    if data["template"] not in FOLDER_TEMPLATES:
        raise ValueError("Template không hợp lệ")

    # 3. Tạo record trước
    folder = folder_repo.create(data)

    try:
        service = get_drive_service()

        # 4. Tạo folder Drive
        root_name = f"{folder['company_code']}-{folder['company_name']}-{folder['mst']}"

        root = service.files().create(
        body={
            "name": root_name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [ROOT_DRIVE_FOLDER_ID]
        },
        fields="id",
        supportsAllDrives=True
    ).execute()


        root_folder_id = root["id"]

        # 5. Áp template
        apply_template(
            service=service,
            parent_folder_id=root_folder_id,
            template_name=folder["template"],
            company_short_name=folder["company_name"],
            year=folder["year"]
        )

        # 6. Update record
        folder_repo.update(folder["id"], {
            "root_folder_id": root_folder_id
        })

        folder["root_folder_id"] = root_folder_id
        return folder

    except Exception as e:
        folder_repo.update(folder["id"], {
            "status": "error"
        })
        raise ValueError(f"Lỗi tạo Drive: {str(e)}")
