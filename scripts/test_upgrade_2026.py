import sys
import os
import time

# Thêm đường dẫn project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.repositories.folder_repo import FolderRepository
from app.services.drive_service import get_drive_service, rename_drive_file
from app.core.folder_templates import FOLDER_TEMPLATES

repo = FolderRepository()
service = get_drive_service()

def ensure_folder_structure(parent_id, target_name):
    """
    Logic sửa đổi:
    1. Nếu có folder trùng tên 100% -> Trả về ID (Bỏ qua).
    2. Nếu có folder sai tên (nhưng cùng mục đích) -> Đổi tên cũ thành _CŨ, sau đó tạo mới.
    3. Nếu chưa có gì -> Tạo mới.
    """
    try:
        # Lấy danh sách folder con hiện có
        query = f"'{parent_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        results = service.files().list(
            q=query, fields="files(id, name)", supportsAllDrives=True, includeItemsFromAllDrives=True
        ).execute()
        children = results.get('files', [])

        # --- BƯỚC 1: KIỂM TRA KHỚP TUYỆT ĐỐI ---
        # Strip khoảng trắng để so sánh chính xác nhất
        target_name_clean = target_name.strip()
        
        exact_match = next((f for f in children if f['name'].strip() == target_name_clean), None)
        
        if exact_match:
            # Folder đã đúng tên rồi -> Không làm gì cả, trả về ID để đi sâu vào tiếp
            return exact_match['id']

        # --- BƯỚC 2: KIỂM TRA SAI CÚ PHÁP ---
        # Chỉ thực hiện bước này nếu KHÔNG tìm thấy exact_match ở trên
        
        # Lấy tiền tố (ví dụ: '1-' hoặc '2-')
        prefix = target_name_clean.split('-')[0] if '-' in target_name_clean else None
        
        # Tìm folder sai: cùng số thứ tự đầu (vd: '1.') hoặc chứa từ khóa quan trọng
        # Nhưng phải loại bỏ những folder đã có đuôi _CŨ rồi
        fuzzy_match = None
        for f in children:
            fname = f['name'].strip()
            if fname.endswith('_CŨ'): continue # Bỏ qua các folder đã đổi tên trước đó
            
            # Nếu folder bắt đầu bằng "1." hoặc "1 " thay vì "1-"
            if prefix and (fname.startswith(f"{prefix}.") or fname.startswith(f"{prefix} ")):
                fuzzy_match = f
                break
            
            # Hoặc nếu tên folder chứa từ khóa chính (ví dụ: "HOA DON MUA")
            keyword = target_name_clean.split('-')[-1]
            if len(keyword) > 4 and keyword.lower() in fname.lower():
                fuzzy_match = f
                break

        if fuzzy_match:
            old_name = fuzzy_match['name']
            new_old_name = f"{old_name}_CŨ"
            print(f"      ⚠️ Phát hiện sai tên: '{old_name}' -> Đổi thành '{new_old_name}'")
            rename_drive_file(service, fuzzy_match['id'], new_old_name)

        # --- BƯỚC 3: TẠO FOLDER MỚI ĐÚNG CHUẨN ---
        print(f"      ➕ Tạo mới folder chuẩn: {target_name_clean}")
        new_folder = service.files().create(
            body={
                "name": target_name_clean,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [parent_id]
            },
            fields="id",
            supportsAllDrives=True
        ).execute()
        return new_folder['id']

    except Exception as e:
        print(f"      ❌ Lỗi: {str(e)}")
        return None

def run_bulk_update():
    print("🚀 BẮT ĐẦU CHẠY CẬP NHẬT HÀNG LOẠT NĂM 2026 (PHIÊN BẢN FIX)...")
    
    all_folders = repo.get_all()
    # Lọc công ty Active
    active_folders = [f for f in all_folders if (getattr(f, 'status', None) or f.get('status')) == 'active']
    total = len(active_folders)
    
    print(f"👉 Tìm thấy {total} công ty Active.")

    for index, f in enumerate(active_folders):
        c_name = getattr(f, 'company_name', None) or f.get('company_name')
        c_code = getattr(f, 'company_code', None) or f.get('company_code')
        root_id = getattr(f, 'root_folder_id', None) or f.get('root_folder_id')
        template_name = getattr(f, 'template', None) or f.get('template') or "STANDARD"

        print(f"\n[{index + 1}/{total}] Xử lý: {c_name} ({c_code})")

        if not root_id:
            print("   ⏩ Bỏ qua: Thiếu Root ID")
            continue

        # Lấy các đường dẫn có chứa {Y} từ template
        paths = [p for p in FOLDER_TEMPLATES.get(template_name, []) if "{Y}" in p]

        for raw_path in paths:
            resolved_path = raw_path.replace("{TENVT}", c_name).replace("{Y}", "2026")
            parts = resolved_path.split("/")
            
            current_parent = root_id
            for part in parts:
                current_parent = ensure_folder_structure(current_parent, part)
                if not current_parent: break

        time.sleep(0.1) # Nghỉ ngắn

    print("\n🎉 HOÀN TẤT!")

if __name__ == "__main__":
    run_bulk_update()