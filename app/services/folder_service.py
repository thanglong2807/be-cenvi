import os

from app.services.drive_service import get_drive_service, browse_drive_folder, get_drive_permissions
from app.services.drive_folder_builder import apply_template
from app.db.repositories.folder_repo import FolderRepository
from app.db.repositories.employee_repo import EmployeeRepository
from app.core.folder_templates import FOLDER_TEMPLATES
from googleapiclient.errors import HttpError
from datetime import datetime

# ========= LOAD ENV =========
ROOT_DRIVE_FOLDER_ID = os.getenv("COMPANY_PARENT_FOLDER_ID")
ROOT_DRIVE_HKD_ID = os.getenv("ROOT_DRIVE_HKD_ID") 
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

# app/services/folder_service.py

# ... (các import và biến ROOT_DRIVE_FOLDER_ID cũ) ...

# Load thêm biến HKD
ROOT_DRIVE_HKD_ID = os.getenv("ROOT_DRIVE_HKD_ID")

import os
from datetime import datetime
from app.services.drive_service import get_drive_service, add_permission
from app.services.drive_folder_builder import apply_template
from app.db.repositories.folder_repo import FolderRepository
from app.db.repositories.employee_repo import EmployeeRepository
from app.core.folder_templates import FOLDER_TEMPLATES

# ========= REPOSITORIES & ENV =========
folder_repo = FolderRepository()
employee_repo = EmployeeRepository()

ROOT_DRIVE_FOLDER_ID = os.getenv("ROOT_DRIVE_FOLDER_ID")
ROOT_DRIVE_HKD_ID = os.getenv("ROOT_DRIVE_HKD_ID")

def create_folder(data: dict):
    # 1. Lấy thông tin nhân viên để lấy Email
    manager = employee_repo.get_by_id(data["manager_employee_id"])
    if not manager or not manager.get("email"):
        raise ValueError("Nhân viên quản lý không tồn tại hoặc thiếu Email")
    
    manager_email = manager["email"]

    # 2. Lấy trạng thái mong muốn (Mới)
    # Nếu frontend không gửi status, mặc định là "active"
    target_status = data.get("status", "active")

    # 3. Check template
    template_name = data.get("template", "STANDARD")
    if template_name not in FOLDER_TEMPLATES:
        raise ValueError(f"Template '{template_name}' không hợp lệ")

    # 4. Check trùng lặp (Logic cũ: Xóa record lỗi, chặn record active)
    mst = data.get("mst")
    company_code = data.get("company_code")
    all_folders = folder_repo.get_all()
    existing = next((f for f in all_folders if f.get('mst') == mst or f.get('company_code') == company_code), None)
    
    if existing:
        if existing.get("status") == "active":
            raise ValueError(f"Dữ liệu đã tồn tại và đang hoạt động (ID: {existing['id']})")
        else:
            try:
                # Xóa record lỗi cũ để tạo cái mới
                folder_repo.delete(existing['id'])
            except:
                pass

    # 5. Lưu record vào DB trước (với trạng thái target_status)
    folder = folder_repo.create(data)

    try:
        service = get_drive_service()

        # 6. Xác định Folder cha gốc trên Drive (Cty vs HKD)
        target_parent_id = ROOT_DRIVE_FOLDER_ID
        if template_name == "HKD":
            if not ROOT_DRIVE_HKD_ID:
                raise RuntimeError("ROOT_DRIVE_HKD_ID chưa được khai báo trong .env")
            target_parent_id = ROOT_DRIVE_HKD_ID

        if not target_parent_id:
            raise RuntimeError("Chưa cấu hình ID thư mục gốc trên Drive")

        # 7. Tạo folder con mới trên Drive
        c_code = folder.get('company_code', 'NOCODE')
        c_name = folder.get('company_name', 'NONAME')
        c_mst = folder.get('mst', 'NOMST')
        root_name = f"{c_code}_{c_name}_{c_mst}"

        root_drive_obj = service.files().create(
            body={
                "name": root_name,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [target_parent_id]
            },
            fields="id",
            supportsAllDrives=True
        ).execute()

        new_sub_folder_id = root_drive_obj["id"]

        # 8. CẤP QUYỀN 'fileOrganizer' (Quản lý nội dung) cho nhân viên phụ trách
        # Quyền này chỉ áp dụng cho folder mới tạo này, ghi đè quyền xem ở folder tổng
        add_permission(service, new_sub_folder_id, manager_email, role="fileOrganizer")

        # 9. Logic tạo folder theo Năm (2024 -> Hiện tại)
        input_year = int(folder.get("year", datetime.now().year))
        current_year = datetime.now().year
        
        if input_year == 2024:
            # Tạo danh sách năm từ 2024 đến năm hiện tại
            years_to_process = list(range(2024, max(current_year, 2024) + 1))
        else:
            # Chỉ tạo đúng năm đã nhập
            years_to_process = [input_year]

        # 10. Áp template tạo cấu trúc sub-folders bên trong
        for y in years_to_process:
            apply_template(
                service=service,
                parent_folder_id=new_sub_folder_id,
                template_name=template_name,
                company_short_name=c_name,
                year=y
            )

        # 11. Cập nhật record DB lần cuối (Gắn ID Drive và set Status chính xác)
        folder_repo.update(folder["id"], {
            "root_folder_id": new_sub_folder_id,
            "status": target_status
        })

        # Trả về kết quả cho Frontend
        return {
            **folder, 
            "root_folder_id": new_sub_folder_id, 
            "status": target_status
        }

    except Exception as e:
        if f_id:
            folder_repo.update(f_id, {"status": "error"})
            
        # === THÊM DÒNG NÀY ĐỂ SOI LỖI TRÊN TERMINAL ===
        print("!!!!!!!! LỖI TẠI CREATE_FOLDER !!!!!!!!")
        import traceback
        traceback.print_exc() 
        print(f"Chi tiết: {str(e)}")
        # ==============================================
            
        raise ValueError(f"Lỗi hệ thống: {str(e)}") 


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
    old_full_name = f"{current_folder['company_code']}_{current_folder['company_name']}_{current_folder['mst']}"

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




# app/services/folder_service.py

def get_folder_full_detail(folder_db_id: int):
    # 1. Lấy dữ liệu từ Database
    folder = folder_repo.get_by_id(folder_db_id)
    if not folder:
        return None

    # Khởi tạo object kết quả (Đảm bảo luôn có key 'children' và 'permissions')
    result = folder.copy() if isinstance(folder, dict) else folder.__dict__.copy()
    result['children'] = []
    result['permissions'] = []

    root_id = result.get('root_folder_id')
    if not root_id:
        return result

    try:
        service = get_drive_service()

        # 2. Lấy danh sách Folder con (Sử dụng hàm browse_drive_folder để có format chuẩn)
        # Hàm này sẽ trả về children có link, mime_type, created_at... như bạn đã thấy
        result['children'] = browse_drive_folder(root_id)

        # 3. Lấy danh sách Quyền truy cập (Permissions)
        try:
            perm_results = service.permissions().list(
                fileId=root_id,
                fields="permissions(id, displayName, emailAddress, role)",
                supportsAllDrives=True
            ).execute()
            
            raw_perms = perm_results.get('permissions', [])
            processed_perms = []
            
            # Bảng map role sang tên hiển thị
            role_map = {
                "organizer": "Manager",
                "fileOrganizer": "Content Manager",
                "writer": "Contributor",
                "reader": "Viewer"
            }

            for p in raw_perms:
                email = p.get('emailAddress')
                if email:
                    # Bỏ qua con bot quét để danh sách sạch
                    if "gserviceaccount.com" in email:
                        continue
                        
                    role = p.get('role', 'reader')
                    processed_perms.append({
                        "name": p.get('displayName') or email.split('@')[0],
                        "email": email,
                        "role": role,
                        "role_display": role_map.get(role, role.capitalize())
                    })
            
            # GÁN VÀO KẾT QUẢ TRẢ VỀ
            result['permissions'] = processed_perms

        except Exception as pe:
            print(f"⚠️ Không lấy được permissions: {pe}. Có thể Bot chưa có quyền Manager.")

    except Exception as e:
        print(f"🔥 Lỗi hệ thống khi gọi Drive: {e}")

    return result

# ========================================================
# BROWSE FUNCTION (MỚI)
# ========================================================
# app/services/folder_service.py

def browse_drive_folder(drive_folder_id: str):
    service = get_drive_service()
    try:
        results = service.files().list(
            q=f"'{drive_folder_id}' in parents and trashed = false",
            # Bắt buộc phải có webViewLink trong fields
            fields="files(id, name, mimeType, webViewLink, iconLink, createdTime, lastModifyingUser)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        
        raw_items = results.get('files', [])
        
        # CHUẨN HÓA DỮ LIỆU TRƯỚC KHI TRẢ VỀ FRONTEND
        processed_items = []
        for item in raw_items:
            processed_items.append({
                "id": item.get("id"),
                "name": item.get("name"),
                "mime_type": item.get("mimeType"),
                "link": item.get("webViewLink"), # Chuyển webViewLink thành link ở đây
                "created_at": item.get("createdTime"),
                "modified_by": item.get("lastModifyingUser", {}).get("displayName", "N/A")
            })
        return processed_items
    except Exception as e:
        raise ValueError(f"Lỗi: {str(e)}")

# 2. Hàm lấy chi tiết Folder (Kết hợp DB và Drive)
def get_folder_full_detail(folder_db_id: int):
    folder = folder_repo.get_by_id(folder_db_id)
    if not folder:
        return None

    root_id = folder.get('root_folder_id')
    if not root_id:
        return {**folder, "children": [], "permissions": []}

    service = get_drive_service()

    # 1. Gọi hàm lấy danh sách con (Gán vào key 'children' cho khớp FE)
    children = browse_drive_folder(root_id)

    # 2. Gọi hàm lấy danh sách thành viên
    permissions = get_drive_permissions(service, root_id)

    # 3. Gộp dữ liệu trả về
    result = folder.copy() if isinstance(folder, dict) else folder.__dict__.copy()
    result['children'] = children
    result['permissions'] = permissions
    
    return result
# ... (các import cũ)
from app.services.drive_service import (
    get_drive_service, 
    add_permission, 
    remove_permission_by_email, 
    create_drive_shortcut,
    list_drive_subfolders
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


# app/services/folder_service.py

# app/services/folder_service.py

import os

# app/services/folder_service.py

def scan_folders_not_in_db():
    all_db = folder_repo.get_all()
    all_db_folders = folder_repo.get_all() 
    # Gom dữ liệu để tra cứu
    db_root_ids = set()
    db_mst_map = {}
    db_code_map = {}

    def clean_str(val):
        if not val: return ""
        return str(val).strip().replace("'", "").replace('"', '').lstrip('0').lower()

    for f in all_db:
        rid = getattr(f, 'root_folder_id', None) or f.get('root_folder_id')
        mst = getattr(f, 'mst', None) or f.get('mst')
        code = getattr(f, 'company_code', None) or f.get('company_code')
        
        rid_s = str(rid).strip() if rid else ""
        if rid_s: db_root_ids.add(rid_s)
        
        # Map dùng để truy tìm bản ghi cũ qua MST/Code
        if mst: db_mst_map[clean_str(mst)] = f
        if code: db_code_map[clean_str(code)] = f

    # Lấy dữ liệu Drive
    service = get_drive_service()
    drive_folders = list_drive_subfolders(service, ROOT_DRIVE_FOLDER_ID)
    hkd_id = os.getenv("ROOT_DRIVE_HKD_ID")
    if hkd_id: drive_folders.extend(list_drive_subfolders(service, hkd_id))

    results = []
    for item in drive_folders:
        did = str(item['id']).strip()
        if did in db_root_ids: continue # Đã khớp ID -> Bỏ qua

        name = item['name']
        parts = name.split('_')
        s_code = clean_str(parts[0].strip() if len(parts) > 0 else "")
        s_mst = clean_str(parts[2].strip() if len(parts) > 2 else "")

        match_db_id = None
        match_info = ""
        action_type = "create" # Mặc định là tạo mới

        # KIỂM TRA TRÙNG MST HOẶC MÃ ĐỂ CẬP NHẬT
        matched_record = db_mst_map.get(s_mst) or db_code_map.get(s_code)
        
        if matched_record:
            action_type = "update" # Tìm thấy record cũ -> Chuyển sang chế độ Update
            match_db_id = getattr(matched_record, 'id', None) or matched_record.get('id')
            match_info = getattr(matched_record, 'company_name', None) or matched_record.get('company_name')

        results.append({
            "drive_id": did,
            "drive_name": name,
            "drive_link": item.get('webViewLink'),
            "suggested_code": parts[0].strip() if len(parts) > 0 else "",
            "suggested_mst": parts[2].strip() if len(parts) > 2 else "",
            "action_type": action_type,
            "match_db_id": match_db_id,
            "match_info": match_info
        })

    return {
        "total_drive": len(drive_folders), # Tổng số folder robot thấy trên Drive
        "total_db": len(all_db_folders),    # Tổng số hồ sơ đang có trong Database
        "missing_count": len(results),      # Số lượng chưa đồng bộ (hiển thị trong bảng)
        "items": results
    }

# --- THÊM HÀM MỚI ĐỂ GHÉP NỐI ---
def link_drive_to_existing_db(folder_db_id: int, drive_id: str):
    """
    Cập nhật root_folder_id cho một record đã có
    """
    # Check xem drive_id này có ai dùng chưa
    all_db = folder_repo.get_all()
    if any(f.get('root_folder_id') == drive_id for f in all_db):
        raise ValueError("Folder Drive này đã được gắn cho công ty khác rồi!")

    folder_repo.update(folder_db_id, {
        "root_folder_id": drive_id,
        "status": "active"
    })
    return True


def import_folder_from_drive(data: dict):
    """
    Lưu folder đã có sẵn trên Drive vào Database.
    """
    # 1. Validate dữ liệu cơ bản
    if not data.get("company_name") or not data.get("root_folder_id"):
        raise ValueError("Thiếu tên công ty hoặc ID Drive")

    # 2. Kiểm tra trùng lặp (SỬA ĐOẠN NÀY)
    # Thay vì gọi get_by_root_id, ta lấy tất cả và lọc
    all_folders = folder_repo.get_all()
    
    # Tìm xem có folder nào trùng root_folder_id không
    existing = next((f for f in all_folders if f.get('root_folder_id') == data["root_folder_id"]), None)

    if existing:
        raise ValueError(f"Folder này đã tồn tại trong hệ thống (Mã: {existing.get('company_code', 'N/A')})")

    # 3. Tạo record trong DB
    new_folder = folder_repo.create({
        "company_name": data["company_name"],
        "company_code": data.get("company_code"),
        "mst": data.get("mst"),
        "manager_employee_id": data.get("manager_employee_id"),
        "root_folder_id": data["root_folder_id"],
        "year": data.get("year", 2025),
        
        # === SỬA ĐOẠN NÀY ===
        # Lấy từ dữ liệu gửi lên, nếu không có thì mới dùng mặc định
        "status": data.get("status", "active"), 
        "template": data.get("template", "STANDARD") 
        # ====================
    })
    
    return new_folder
def delete_folder_on_drive(drive_id: str):
    """
    Xóa vĩnh viễn folder trên Google Drive
    """
    service = get_drive_service()
    try:
        service.files().delete(fileId=drive_id, supportsAllDrives=True).execute()
        return True
    except Exception as e:
        raise ValueError(f"Lỗi xóa Drive: {str(e)}")


# app/services/folder_service.py

# app/services/folder_service.py

def get_admin_folder_link(company_code: str):
    # 1. Tìm công ty trong Database
    all_folders = folder_repo.get_all()
    
    # Tìm folder dựa theo mã công ty (check cả Object và Dict)
    folder = next((f for f in all_folders if (getattr(f, 'company_code', None) == company_code or f.get('company_code') == company_code)), None)
    
    if not folder:
        return {"status": "error", "message": f"Không tìm thấy mã {company_code} trong DB"}
    
    root_id = getattr(folder, 'root_folder_id', None) or folder.get('root_folder_id')
    if not root_id:
        return {"status": "error", "message": "Công ty này chưa được liên kết Drive"}

    # 2. Truy cập Drive để tìm folder con chứa chữ "HANH-CHINH"
    try:
        from app.services.drive_service import get_drive_service # Import tại chỗ để tránh vòng lặp import
        service = get_drive_service()
        
        # Tìm folder con có tên chứa chữ "HANH-CHINH"
        query = f"'{root_id}' in parents and name contains 'HANH-CHINH' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        results = service.files().list(
            q=query,
            fields="files(id, name, webViewLink)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        
        files = results.get('files', [])
        if not files:
            return {"status": "error", "message": "Không tìm thấy folder con nào tên HANH-CHINH"}
        
        # Trả về folder đầu tiên tìm thấy
        return {
            "status": "success",
            "company_name": getattr(folder, 'company_name', None) or folder.get('company_name'),
            "folder_name": files[0]['name'],
            "link": files[0]['webViewLink']
        }
    except Exception as e:
        return {"status": "error", "message": f"Lỗi Drive: {str(e)}"}