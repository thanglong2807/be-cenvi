import os

from app.services.drive_service import get_drive_service
from app.services.drive_folder_builder import apply_template
from app.db.repositories.folder_repo import FolderRepository
from app.db.repositories.employee_repo import EmployeeRepository
from app.core.folder_templates import FOLDER_TEMPLATES
from googleapiclient.errors import HttpError
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



# app/services/folder_service.py

# ... (Các import cũ giữ nguyên) ...

# ========================================================
# HELPER: ĐẾM FILE (MỚI THÊM)
# ========================================================
def _count_items_in_folder(service, folder_id: str) -> int:
    """
    Đếm số lượng item (file + folder) nằm trong folder_id.
    Lấy tối đa 1000 item (để tối ưu tốc độ, không loop trang).
    """
    try:
        query = f"'{folder_id}' in parents and trashed=false"
        # Chỉ lấy field id để payload nhẹ nhất có thể
        results = service.files().list(
            q=query,
            pageSize=1000, # Đếm tối đa 1000 file đầu tiên
            fields="files(id)", 
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        
        files = results.get("files", [])
        return len(files)
    except Exception:
        return 0

# ========================================================
# HELPER: DỊCH TÊN QUYỀN (Thêm hàm này vào file)
# ========================================================
def _map_role_name(role_code):
    """
    Map role code của Google sang tiếng Việt dễ hiểu hơn
    """
    mapping = {
        "organizer": "Quản lý (Manager)",
        "fileOrganizer": "QL Nội dung (Content Manager)",
        "writer": "Chỉnh sửa (Contributor)",
        "commenter": "Nhận xét",
        "reader": "Người xem (Viewer)",
        "owner": "Chủ sở hữu"
    }
    # Nếu không tìm thấy trong map thì trả về nguyên gốc
    return mapping.get(role_code, role_code)


# ========================================================
# HELPER: LẤY THÔNG TIN LIVE TỪ DRIVE (ĐÃ UPDATE)
# ========================================================
def _fetch_drive_info(root_folder_id: str):
    """
    Hàm nội bộ: 
    1. Lấy Permissions
    2. Lấy Sub-folders
    3. Đếm số file trong từng Sub-folder (Logic mới)
    """
    if not root_folder_id:
        return {"permissions": [], "sub_folders": []}

    try:
        service = get_drive_service()
        
        # --- 1. Lấy danh sách quyền (Permissions) ---
        perm_results = service.permissions().list(
            fileId=root_folder_id,
            fields="permissions(id, emailAddress, role, displayName, type)",
            supportsAllDrives=True
        ).execute()
        
        mapped_perms = []
        for p in perm_results.get("permissions", []):
            if p.get("type") in ["user", "group"]: 
                mapped_perms.append({
                    "name": p.get("displayName", "Unknown"),
                    "email": p.get("emailAddress", ""),
                    "role": p.get("role"),
                    "role_display": _map_role_name(p.get("role"))
                })

        # --- 2. Lấy danh sách Folder con ---
        query = f"'{root_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        file_results = service.files().list(
            q=query,
            fields="files(id, name, createdTime, webViewLink)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            pageSize=50
        ).execute()
        
        sub_folders = file_results.get("files", [])

        # --- 3. Đếm số file trong từng folder con (LOGIC MỚI) ---
        # Loop qua từng folder con để đếm
        for folder in sub_folders:
            f_id = folder.get("id")
            # Gọi hàm đếm
            count = _count_items_in_folder(service, f_id)
            folder["file_count"] = count  # Gán kết quả vào dict

        return {
            "permissions": mapped_perms,
            "sub_folders": sub_folders
        }

    except Exception as e:
        print(f"⚠️ Lỗi khi fetch Drive info: {e}")
        return {"permissions": [], "sub_folders": [], "drive_error": str(e)}

# ... (Các phần còn lại của file giữ nguyên) ...

# ========================================================
# MAIN FUNCTION: GET DETAIL
# ========================================================

def get_folder_full_detail(folder_id: int):
    """
    Lấy chi tiết folder từ DB + Kết hợp thông tin Live từ Drive
    """
    # 1. Lấy dữ liệu tĩnh từ Database
    folder_data = folder_repo.get_by_id(folder_id)
    if not folder_data:
        return None

    # 2. Lấy ID Drive
    root_id = folder_data.get("root_folder_id")

    # 3. Gọi Drive API để lấy thêm info (Quyền & Folder con)
    if root_id:
        print(f"🔍 Đang quét info live từ Drive ID: {root_id}...")
        drive_info = _fetch_drive_info(root_id)
        
        # Merge dữ liệu Drive vào kết quả trả về
        folder_data.update(drive_info)
    else:
        folder_data["permissions"] = []
        folder_data["sub_folders"] = []

    return folder_data


# ========================================================
# BROWSE FUNCTION (MỚI)
# ========================================================
def browse_drive_folder(drive_folder_id: str):
    try:
        service = get_drive_service()
        
        query = f"'{drive_folder_id}' in parents and trashed=false"
        
        results = service.files().list(
            q=query,
            # SỬA LẠI DÒNG NÀY (createdTime chỉ có 1 chữ i)
            fields="files(id, name, mimeType, webViewLink, createdTime, iconLink, size, lastModifyingUser)",
            pageSize=1000,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            orderBy="folder, name"
        ).execute()
        
        items = results.get("files", [])
        
        # Xử lý dữ liệu đẹp hơn cho Frontend
        processed_items = []
        for item in items:
            is_folder = item["mimeType"] == "application/vnd.google-apps.folder"
            
            processed_items.append({
                "id": item["id"],
                "name": item["name"],
                "type": "folder" if is_folder else "file",
                "mime_type": item["mimeType"],
                "link": item["webViewLink"],
                "created_at": item.get("createdTime"),
                "icon": item.get("iconLink"),
                "size": item.get("size", "-"), # Folder không có size
                "modified_by": item.get("lastModifyingUser", {}).get("displayName", "Unknown")
            })
            
        return processed_items

    except Exception as e:
        print(f"⚠️ Lỗi browse folder {drive_folder_id}: {e}")
        # Ném lỗi ra để API bắt được
        raise ValueError(f"Không thể đọc nội dung folder: {str(e)}")

# app/services/folder_service.py

# ... (các import cũ)
from app.services.drive_service import (
    get_drive_service, 
    add_permission, 
    remove_permission_by_email, 
    create_drive_shortcut
)

def handover_folders(old_employee_id: int, new_employee_id: int):
    # 1. Lấy thông tin 2 nhân viên
    old_emp = employee_repo.get_by_id(old_employee_id)
    new_emp = employee_repo.get_by_id(new_employee_id)

    if not old_emp or not new_emp:
        raise ValueError("Thông tin nhân viên không tồn tại")
    
    # === THAY ĐỔI Ở ĐÂY: KHÔNG BÁO LỖI NỮA ===
    # Lấy ID folder cha của nhân viên mới (nếu có)
    target_shortcut_parent = new_emp.get('root_folder_id')
    
    # 2. Lấy danh sách folder mà nhân viên cũ đang quản lý
    folders = folder_repo.get_by_employee(old_employee_id)
    
    if not folders:
        return {"message": "Nhân viên cũ không quản lý folder nào."}

    service = get_drive_service()
    processed_count = 0

    # 3. Duyệt qua từng folder để xử lý
    for folder in folders:
        folder_drive_id = folder['root_folder_id']
        folder_name = f"{folder['mst']} - {folder['company_name']}"

        if not folder_drive_id:
            continue

        # A. Cấp quyền cho nhân viên MỚI (Vẫn chạy bình thường)
        try:
            add_permission(service, folder_drive_id, new_emp['email'], role="writer")
        except Exception as e:
            print(f"Lỗi cấp quyền cho {folder_name}: {e}")

        # B. Tạo Shortcut (CHỈ CHẠY NẾU CÓ FOLDER CHA)
        if target_shortcut_parent:
            create_drive_shortcut(
                service=service,
                target_id=folder_drive_id,
                parent_id=target_shortcut_parent,
                name=f"Shortcut - {folder_name}"
            )
        # Nếu không có target_shortcut_parent thì dòng này tự động bị bỏ qua, không lỗi nữa.

        # C. Xóa quyền nhân viên CŨ (Vẫn chạy bình thường)
        if old_emp.get('email'):
            remove_permission_by_email(service, folder_drive_id, old_emp['email'])

        # D. Cập nhật DB (Quan trọng nhất)
        folder_repo.update(folder['id'], {
            "manager_employee_id": new_employee_id
        })
        
        processed_count += 1

    return {
        "status": "success", 
        "transferred": processed_count,
        "message": f"Đã bàn giao {processed_count} thư mục (Bỏ qua tạo shortcut nếu thiếu folder đích)"
    }
# app/services/folder_service.py

# ... (các import cũ)
from app.db.repositories.employee_repo import EmployeeRepository

# Cache nhân viên để tìm cho nhanh (đỡ query DB nhiều lần)
def get_employee_by_name_approx(name_raw: str):
    if not name_raw: return None
    clean_name = name_raw.split("_")[0].strip().lower() # Xóa hậu tố
    repo = EmployeeRepository()
    all_emps = repo.get_all()
    
    for emp in all_emps:
        if emp['name'].lower() == clean_name:
            return emp
    return None

def check_migration_status(mst: str, company_name: str, new_manager_name: str):
    """
    Hàm này KHÔNG thay đổi dữ liệu, chỉ trả về thông tin so sánh
    """
    mst_clean = mst.replace('"', '').strip()
    folders = folder_repo.get_all()
    # Tìm folder theo MST
    target_folder = next((f for f in folders if f.get('mst') == mst_clean), None)

    if not target_folder:
        return {
            "status": "not_found",
            "message": f"Không tìm thấy MST {mst_clean} trong hệ thống"
        }

    current_manager_id = target_folder.get('manager_employee_id')
    current_status = target_folder.get('status')
    
    # Logic xác định hành động
    action = "none" # Không làm gì
    action_desc = "Dữ liệu khớp, không cần thay đổi"
    new_data = {}

    # Trường hợp 1: Dừng dịch vụ
    if new_manager_name == "Đã dừng dịch vụ":
        if current_status == 'active':
            action = "deactivate"
            action_desc = "⛔ Chuyển trạng thái sang: DỪNG DỊCH VỤ + Xóa quyền Drive"
        else:
            action_desc = "Đã dừng dịch vụ rồi. Bỏ qua."
    
    # Trường hợp 2: Có nhân viên quản lý
    else:
        new_emp = get_employee_by_name_approx(new_manager_name)
        if not new_emp:
            return {
                "status": "warning",
                "message": f"⚠️ Không tìm thấy nhân viên tên '{new_manager_name}' trong DB"
            }
        
        new_data['new_employee_id'] = new_emp['id']
        new_data['new_employee_name'] = new_emp['name']

        if current_manager_id != new_emp['id']:
            action = "handover"
            action_desc = f"🔄 Bàn giao từ ID {current_manager_id} sang {new_emp['name']}"
        elif current_status != 'active':
            action = "activate"
            action_desc = "✅ Kích hoạt lại dịch vụ (Active)"

    return {
        "status": "ok",
        "folder_id": target_folder['id'],
        "root_folder_id": target_folder['root_folder_id'],
        "company_name": target_folder['company_name'],
        "current_manager_id": current_manager_id,
        "action": action,
        "description": action_desc,
        "new_data": new_data
    }

def execute_migration_step(folder_id: int, action: str, new_data: dict = None):
    """
    Hàm thực thi thay đổi thật sự
    """
    folder = folder_repo.get_by_id(folder_id)
    service = get_drive_service()
    
    if action == "deactivate":
        # 1. Update DB
        folder_repo.update(folder_id, {"status": "inactive"})
        # 2. Xóa quyền (nếu cần thiết và có logic lấy email cũ)
        # (Bạn có thể thêm logic remove_permission ở đây như script trước)
        return "Đã dừng dịch vụ thành công"

    elif action == "handover":
        old_id = folder['manager_employee_id']
        new_id = new_data['new_employee_id']
        if old_id:
             handover_folders(old_id, new_id)
        else:
             # Trường hợp cũ chưa có ai, chỉ update người mới
             folder_repo.update(folder_id, {"manager_employee_id": new_id})
        
        return "Đã bàn giao quyền thành công"
    
    elif action == "activate":
        folder_repo.update(folder_id, {"status": "active"})
        return "Đã kích hoạt lại thành công"

    return "Không có hành động nào được thực hiện"


# app/services/folder_service.py

def check_migration_status(company_code: str, mst: str, company_name: str, new_manager_name: str):
    """
    Tìm folder dựa trên MST hoặc Mã công ty.
    """
    # 1. Chuẩn hóa dữ liệu đầu vào
    mst_clean = mst.replace('"', '').replace("'", "").strip()
    code_clean = company_code.strip()
    
    # 2. Lấy tất cả folder để tìm kiếm
    # (Nếu DB lớn, nên viết query trong Repo: find_by_mst_or_code)
    all_folders = folder_repo.get_all()
    
    target_folder = None

    # --- LOGIC TÌM KIẾM ---
    # Cách 1: Tìm theo MST trước (Chính xác nhất)
    if mst_clean:
        target_folder = next((f for f in all_folders if f.get('mst') and f.get('mst').strip() == mst_clean), None)
    
    # Cách 2: Nếu không thấy MST, tìm theo Mã công ty
    if not target_folder and code_clean:
         target_folder = next((f for f in all_folders if f.get('company_code') and f.get('company_code').strip() == code_clean), None)

    # -----------------------

    if not target_folder:
        return {
            "status": "not_found",
            "message": f"❌ Không tìm thấy MST '{mst_clean}' hoặc Mã '{code_clean}' trong DB"
        }

    # Lấy thông tin hiện tại
    current_manager_id = target_folder.get('manager_employee_id')
    current_status = target_folder.get('status')
    current_code = target_folder.get('company_code')
    
    # Logic xác định hành động
    action = "none"
    action_desc = "✅ Dữ liệu khớp/Không thay đổi"
    new_data = {}

    # Logic 1: Dừng dịch vụ
    if new_manager_name == "Đã dừng dịch vụ":
        if current_status == 'active':
            action = "deactivate"
            action_desc = "⛔ Chuyển trạng thái sang: DỪNG DỊCH VỤ + Xóa quyền Drive"
        else:
            action_desc = "ℹ️ Đã dừng dịch vụ rồi. Bỏ qua."
    
    # Logic 2: Có người quản lý (Chuyển quyền hoặc Active lại)
    else:
        new_emp = get_employee_by_name_approx(new_manager_name)
        if not new_emp:
            return {
                "status": "warning",
                "message": f"⚠️ Không tìm thấy nhân viên tên '{new_manager_name}' trong hệ thống"
            }
        
        new_data['new_employee_id'] = new_emp['id']
        new_data['new_employee_name'] = new_emp['name']

        # Nếu người quản lý khác nhau -> Bàn giao
        if current_manager_id != new_emp['id']:
            action = "handover"
            # Tìm tên người cũ để hiển thị cho rõ
            old_emp_name = "Chưa có"
            if current_manager_id:
                old_emp = employee_repo.get_by_id(current_manager_id)
                if old_emp: old_emp_name = old_emp['name']
                
            action_desc = f"🔄 Bàn giao: {old_emp_name} ➡ {new_emp['name']}"
        
        # Nếu đang Inactive mà lại có người quản lý -> Kích hoạt lại
        elif current_status != 'active':
            action = "activate"
            action_desc = "✅ Kích hoạt lại dịch vụ (Active)"

    return {
        "status": "ok",
        "folder_id": target_folder['id'],
        "db_code": current_code,   # Trả về để so sánh trên UI
        "db_mst": target_folder.get('mst'),
        "db_name": target_folder.get('company_name'), # Tên trong DB để user so sánh
        "action": action,
        "description": action_desc,
        "new_data": new_data
    }
    """
    Logic tìm kiếm ưu tiên MST -> Company Code.
    Bỏ qua Company Name khi tìm kiếm.
    """
    # 1. Chuẩn hóa dữ liệu đầu vào
    mst_clean = str(mst).replace('"', '').replace("'", "").strip()
    code_clean = str(company_code).strip()
    
    folders = folder_repo.get_all()
    target_folder = None

    # 2. Tìm kiếm (Ưu tiên MST trước)
    # Lọc MST: Chỉ lấy số và dấu gạch ngang (bỏ khoảng trắng thừa)
    
    # Tìm theo MST chính xác
    target_folder = next((f for f in folders if str(f.get('mst', '')).strip() == mst_clean), None)

    # Nếu không thấy MST, tìm theo Company Code (nếu Code hợp lệ và khác NOCODE)
    if not target_folder and code_clean and "NOCODE" not in code_clean.upper():
        target_folder = next((f for f in folders if str(f.get('company_code', '')).strip() == code_clean), None)

    # 3. Kết quả tìm kiếm
    if not target_folder:
        return {
            "status": "not_found",
            "message": f"❌ Không tìm thấy MST: {mst_clean} hoặc Code: {code_clean}"
        }

    # 4. Logic xử lý (Giữ nguyên như cũ)
    current_manager_id = target_folder.get('manager_employee_id')
    current_status = target_folder.get('status')
    
    action = "none"
    action_desc = "Dữ liệu khớp, không cần thay đổi"
    new_data = {}

    # Case: Dừng dịch vụ
    if new_manager_name == "Đã dừng dịch vụ":
        if current_status == 'active':
            action = "deactivate"
            action_desc = "⛔ Chuyển trạng thái sang: DỪNG DỊCH VỤ + Xóa quyền Drive"
        else:
            action_desc = "Đã dừng dịch vụ rồi. Bỏ qua."
    
    # Case: Có nhân viên quản lý
    else:
        new_emp = get_employee_by_name_approx(new_manager_name)
        if not new_emp:
            return {
                "status": "warning",
                "message": f"⚠️ Không tìm thấy nhân viên tên '{new_manager_name}' trong DB"
            }
        
        new_data['new_employee_id'] = new_emp['id']
        new_data['new_employee_name'] = new_emp['name']

        if current_manager_id != new_emp['id']:
            action = "handover"
            action_desc = f"🔄 Bàn giao: {target_folder.get('company_code')} - {target_folder.get('mst')} \nTừ ID {current_manager_id} sang {new_emp['name']}"
        elif current_status != 'active':
            action = "activate"
            action_desc = "✅ Kích hoạt lại dịch vụ (Active)"

    return {
        "status": "ok",
        "folder_id": target_folder['id'],
        "root_folder_id": target_folder['root_folder_id'],
        # Trả về tên trong DB để người dùng đối chiếu với tên trong Excel xem có lệch nhiều không
        "company_name_db": target_folder['company_name'], 
        "mst_db": target_folder['mst'],
        "company_code_db": target_folder.get('company_code'),
        "current_manager_id": current_manager_id,
        "action": action,
        "description": action_desc,
        "new_data": new_data
    }

def transfer_single_folder(folder_id: int, new_manager_id: int):
    # A. Lấy thông tin
    folder = folder_repo.get_by_id(folder_id)
    new_emp = employee_repo.get_by_id(new_manager_id)
    
    if not folder or not new_emp:
        raise ValueError("Dữ liệu không tồn tại")

    current_manager_id = folder.get('manager_employee_id')
    folder_drive_id = folder.get('root_folder_id')

    # B. Xử lý Google Drive (Chỉ làm nếu có folder trên Drive)
    if folder_drive_id:
        service = get_drive_service()
        
        # 1. Cấp quyền cho Manager Mới (ID=2)
        try:
            add_permission(service, folder_drive_id, new_emp['email'], role="writer")
        except Exception as e:
            print(f"Warning add_permission: {e}")

        # 2. Xóa quyền Manager Cũ (Nếu có)
        if current_manager_id:
            old_emp = employee_repo.get_by_id(current_manager_id)
            if old_emp and old_emp.get('email'):
                try:
                    remove_permission_by_email(service, folder_drive_id, old_emp['email'])
                except Exception as e:
                    print(f"Warning remove_permission: {e}")
        
        # 3. Tạo Shortcut (Bỏ qua nếu chưa có folder đích - theo yêu cầu của bạn)
        target_parent = new_emp.get('root_folder_id')
        if target_parent:
            try:
                create_drive_shortcut(
                    service=service, 
                    target_id=folder_drive_id, 
                    parent_id=target_parent, 
                    name=f"Shortcut - {folder['mst']} - {folder['company_name']}"
                )
            except Exception as e:
                print(f"Warning shortcut: {e}")

    # C. CẬP NHẬT DATABASE (QUAN TRỌNG NHẤT)
    # Dòng này đảm bảo manager_employee_id được set về 2 (hoặc ID bất kỳ được truyền vào)
    folder_repo.update(folder_id, {
        "manager_employee_id": new_manager_id,
        "status": "active" # Đảm bảo active lại nếu đang inactive
    })

    return f"Đã chuyển folder {folder['company_name']} sang {new_emp['name']} (ID: {new_manager_id})"


# 3. Cập nhật hàm Execute để gọi hàm mới
def execute_migration_step(folder_id: int, action: str, new_data: dict = None):
    """
    Hàm thực thi thay đổi
    """
    folder = folder_repo.get_by_id(folder_id)
    
    if action == "deactivate":
        folder_repo.update(folder_id, {"status": "inactive"})
        # Logic xóa quyền Drive nếu cần...
        return "Đã dừng dịch vụ thành công"

    elif action == "handover":
        new_id = new_data['new_employee_id'] # Đây chính là ID=2 từ frontend gửi xuống
        
        # GỌI HÀM MỚI VIẾT Ở TRÊN
        msg = transfer_single_folder(folder_id, new_id)
        return msg
    
    elif action == "activate":
        folder_repo.update(folder_id, {"status": "active"})
        return "Đã kích hoạt lại thành công"

    return "Không có hành động nào được thực hiện"