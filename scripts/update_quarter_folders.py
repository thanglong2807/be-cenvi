import sys
import os
import re # Thêm thư viện Regex

# Thêm đường dẫn để import module từ app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.repositories.folder_repo import FolderRepository
from app.services.drive_service import (
    get_drive_service, 
    find_child_folder_by_name_contain,
    list_drive_subfolders
)

# Cấu hình
TARGET_CATEGORIES = ["THU-NHAP-CA-NHAN"]

def check_and_create_quarters(service, parent_id, category_name):
    """
    Quét và tạo các folder Quý 1->4 nếu chưa có bất kỳ biến thể nào
    """
    # 1. Lấy tất cả folder con hiện có trong mục này
    existing_subfolders = list_drive_subfolders(service, parent_id)
    
    results_log = []

    for i in range(1, 5): # Chạy từ Quý 1 đến Quý 4
        # Biểu thức chính quy tìm: (QUY hoặc QUÝ) + (khoảng trắng) + (Số Quý)
        # Không phân biệt hoa thường (re.IGNORECASE)
        pattern = re.compile(f"QU[YÝ]\\s*{i}", re.IGNORECASE)
        
        # Kiểm tra xem có folder nào trong danh sách khớp với pattern không
        found_folder = next((f for f in existing_subfolders if pattern.search(f['name'])), None)

        if found_folder:
            results_log.append(f"[Q{i} ✓ ({found_folder['name']})]")
        else:
            # Nếu hoàn toàn không thấy biến thể nào -> Tạo mới folder chuẩn "QUY X"
            new_name = f"QUY {i}"
            file_metadata = {
                'name': new_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id]
            }
            service.files().create(
                body=file_metadata, 
                fields='id',
                supportsAllDrives=True
            ).execute()
            results_log.append(f"[Q{i} ✨ (Tạo mới)]")
            
    return " ".join(results_log)

def run_update():
    print("🚀 BẮT ĐẦU CẬP NHẬT CẤU TRÚC QUÝ (KIỂM TRA BIẾN THỂ TÊN)...")
    
    repo = FolderRepository()
    service = get_drive_service()
    all_folders = repo.get_all()
    
    print(f"👉 Tìm thấy {len(all_folders)} công ty trong DB.")

    for i, folder in enumerate(all_folders):
        company_name = folder.get('company_name')
        root_id = folder.get('root_folder_id')
        
        if not root_id: continue

        print(f"\n[{i+1}/{len(all_folders)}] {company_name}:")

        try:
            # 1. Tìm folder TAI-LIEU-THUE
            f_thue = find_child_folder_by_name_contain(service, root_id, "TAI-LIEU-THUE")
            if not f_thue:
                print("   ⚠️ Không thấy folder TAI-LIEU-THUE.")
                continue

            # 2. Lấy danh sách các năm
            sub_thue = list_drive_subfolders(service, f_thue['id'])
            year_folders = [f for f in sub_thue if f['name'].isdigit() and len(f['name']) == 4]

            for yf in year_folders:
                print(f"   📂 Năm {yf['name']}:")
                
                # 3. Duyệt qua GTGT và TNCN
                for cat_name in TARGET_CATEGORIES:
                    target_cat = find_child_folder_by_name_contain(service, yf['id'], cat_name)
                    if target_cat:
                        # Gọi hàm check biến thể và tạo Quý
                        log = check_and_create_quarters(service, target_cat['id'], cat_name)
                        print(f"      📁 {cat_name}: {log}")
                    else:
                        print(f"      ❌ Không thấy {cat_name}")

        except Exception as e:
            print(f"   🔥 Lỗi: {str(e)}")

    print("\n✅ HOÀN TẤT!")

if __name__ == "__main__":
    run_update()