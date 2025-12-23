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

# ========= UPDATE (SỬA) =========
def update_folder(folder_id: int, data: dict):
    """
    Cập nhật folder:
    1. Đổi tên folder Drive (nếu đổi thông tin công ty).
    2. Cập nhật quyền Drive (nếu đổi nhân viên phụ trách).
    3. Lưu vào Database.
    """
    # 1. Lấy dữ liệu cũ
    current_folder = folder_repo.get_by_id(folder_id)
    if not current_folder:
        raise ValueError(f"Không tìm thấy folder {folder_id}")

    root_folder_id = current_folder.get("root_folder_id")
    service = None # Khởi tạo biến service
    
    # Hàm helper lazy load service (chỉ kết nối khi cần)
    def get_service_instance():
        nonlocal service
        if not service:
            service = get_drive_service()
        return service

    # =========================================================
    # LOGIC 1: ĐỔI TÊN FOLDER (Như code trước)
    # =========================================================
    new_code = data.get("company_code", current_folder["company_code"])
    new_name = data.get("company_name", current_folder["company_name"])
    new_mst = data.get("mst", current_folder["mst"])

    new_full_name = f"{new_code}-{new_name}-{new_mst}"
    old_full_name = f"{current_folder['company_code']}-{current_folder['company_name']}-{current_folder['mst']}"

    if root_folder_id and new_full_name != old_full_name:
        try:
            srv = get_service_instance()
            srv.files().update(
                fileId=root_folder_id,
                body={"name": new_full_name},
                supportsAllDrives=True
            ).execute()
            print(f"✅ [Drive] Đã đổi tên thành: {new_full_name}")
        except Exception as e:
            print(f"⚠️ [Drive Error] Không thể đổi tên: {e}")

    # =========================================================
    # LOGIC 2: XỬ LÝ QUYỀN NHÂN VIÊN (LOGIC MỚI)
    # =========================================================
    new_manager_id = data.get("manager_employee_id")
    old_manager_id = current_folder.get("manager_employee_id")

    # Chỉ chạy khi có thay đổi nhân viên và folder đã tồn tại trên Drive
    if root_folder_id and new_manager_id and new_manager_id != old_manager_id:
        try:
            srv = get_service_instance()
            
            # --- BƯỚC A: LẤY EMAIL ---
            new_emp = employee_repo.get_by_id(new_manager_id)
            if not new_emp:
                raise ValueError(f"Nhân viên mới ID {new_manager_id} không tồn tại")
            new_email = new_emp["email"] # Giả sử trường email là "email"

            # --- BƯỚC B: CẤP QUYỀN CHO NHÂN VIÊN MỚI (CONTENT MANAGER) ---
            print(f"🔄 [Drive] Cấp quyền Content Manager cho: {new_email}")
            srv.permissions().create(
                fileId=root_folder_id,
                body={
                    "role": "fileOrganizer", # fileOrganizer = Content Manager
                    "type": "user",
                    "emailAddress": new_email
                },
                supportsAllDrives=True,
                sendNotificationEmail=True # Gửi mail thông báo
            ).execute()

            # --- BƯỚC C: HẠ QUYỀN NHÂN VIÊN CŨ (VIEWER) ---
            if old_manager_id:
                old_emp = employee_repo.get_by_id(old_manager_id)
                if old_emp:
                    old_email = old_emp["email"]
                    print(f"🔄 [Drive] Đang tìm quyền của nhân viên cũ: {old_email}")
                    
                    # 1. Phải tìm Permission ID của email cũ trong folder này
                    # (Google API yêu cầu ID quyền chứ không cho update thẳng bằng email)
                    permissions_list = srv.permissions().list(
                        fileId=root_folder_id,
                        fields="permissions(id, emailAddress, role)",
                        supportsAllDrives=True
                    ).execute().get("permissions", [])

                    target_perm_id = None
                    for p in permissions_list:
                        if p.get("emailAddress", "").lower() == old_email.lower():
                            target_perm_id = p.get("id")
                            break
                    
                    # 2. Nếu tìm thấy thì hạ quyền
                    if target_perm_id:
                        srv.permissions().update(
                            fileId=root_folder_id,
                            permissionId=target_perm_id,
                            body={"role": "reader"}, # reader = Viewer
                            supportsAllDrives=True
                        ).execute()
                        print(f"✅ [Drive] Đã hạ quyền {old_email} xuống Viewer")
                    else:
                        print(f"⚠️ Không tìm thấy quyền của {old_email} trong folder để hạ.")

        except Exception as e:
            print(f"⚠️ [Drive Permission Error] Lỗi cập nhật quyền: {e}")
            # Không raise lỗi để vẫn cho phép lưu vào DB (có thể phân quyền tay sau)

    # =========================================================
    # LOGIC 3: LƯU DB
    # =========================================================
    updated_folder = folder_repo.update(folder_id, data)
    return updated_folder

# ========= DELETE (XÓA) =========
def delete_folder(folder_id: int):
    """
    Xóa folder trong DB và chuyển folder trên Drive vào thùng rác
    """
    # 1. Lấy thông tin để có Drive ID
    folder = folder_repo.get_by_id(folder_id)
    if not folder:
        raise ValueError(f"Không tìm thấy folder có ID {folder_id}")

    root_folder_id = folder.get("root_folder_id")

    # 2. Xóa trên Google Drive (Chuyển vào thùng rác - Trash)
    if root_folder_id:
        try:
            service = get_drive_service()
            # trashed=True nghĩa là đưa vào thùng rác, chưa xóa vĩnh viễn (an toàn)
            service.files().update(
                fileId=root_folder_id,
                body={"trashed": True},
                supportsAllDrives=True
            ).execute()
            print(f"🗑️ Đã chuyển folder {root_folder_id} vào thùng rác Drive")
        except Exception as e:
            # Nếu folder trên drive đã bị xóa thủ công từ trước thì bỏ qua lỗi này
            print(f"⚠️ Không thể xóa folder trên Drive (có thể đã bị xóa trước đó). Lỗi: {str(e)}")

    # 3. Xóa trong Database
    result = folder_repo.delete(folder_id)
    return result