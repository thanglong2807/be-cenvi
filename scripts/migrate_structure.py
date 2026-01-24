import sys
import os

# 1. Thêm đường dẫn project vào hệ thống để import được app
# Giả sử file này nằm trong folder "scripts/", ta cần lùi lại 1 cấp để thấy folder "app"
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.repositories.folder_repo import FolderRepository
from app.services.drive_service import get_drive_service

# ==========================================
# CẤU HÌNH ĐỔI TÊN (MAPPING)
# ==========================================

# 1. Nhánh TÀI LIỆU CÔNG TY
RENAME_MAP_COMPANY = {
    "1-HOA-DON-MUA": {
        "QUÝ 1": "HDM_QUY-1", "QUÝ 2": "HDM_QUY-2", "QUÝ 3": "HDM_QUY-3", "QUÝ 4": "HDM_QUY-4",
        "QUY 1": "HDM_QUY-1", "QUY 2": "HDM_QUY-2", "QUY 3": "HDM_QUY-3", "QUY 4": "HDM_QUY-4"
    },
    "2-HOA-DON-BAN": {
        "QUÝ 1": "HDB_QUY-1", "QUÝ 2": "HDB_QUY-2", "QUÝ 3": "HDB_QUY-3", "QUÝ 4": "HDB_QUY-4",
        "QUY 1": "HDB_QUY-1", "QUY 2": "HDB_QUY-2", "QUY 3": "HDB_QUY-3", "QUY 4": "HDB_QUY-4"
    }
}

# 2. Nhánh TÀI LIỆU THUẾ
RENAME_MAP_TAX = {
    "KE-TOAN": {
        "QUY-1": "KT_QUY-1", "QUY-2": "KT_QUY-2", "QUY-3": "KT_QUY-3", 
        "QUY-4-VA-CA-NAM": "KT_QUY-4-VA-CA-NAM",
        "QUY 4": "KT_QUY-4-VA-CA-NAM", # Phòng trường hợp tên cũ khác chút
        "QUÝ 1": "KT_QUY-1", "QUÝ 2": "KT_QUY-2", "QUÝ 3": "KT_QUY-3", "QUÝ 4": "KT_QUY-4-VA-CA-NAM"
    }
}

# ==========================================
# HELPER FUNCTIONS (Viết lại ở đây cho gọn)
# ==========================================
def list_children(service, parent_id):
    """Lấy danh sách file/folder con"""
    items = []
    page_token = None
    while True:
        try:
            res = service.files().list(
                q=f"'{parent_id}' in parents and trashed = false and mimeType = 'application/vnd.google-apps.folder'",
                fields="nextPageToken, files(id, name)",
                pageToken=page_token,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                pageSize=1000
            ).execute()
            items.extend(res.get('files', []))
            page_token = res.get('nextPageToken')
            if not page_token: break
        except: break
    return items

def rename_file(service, file_id, new_name):
    try:
        service.files().update(
            fileId=file_id,
            body={"name": new_name},
            supportsAllDrives=True
        ).execute()
        return True
    except Exception as e:
        print(f"    ❌ Lỗi Rename: {e}")
        return False

# ==========================================
# MAIN LOGIC
# ==========================================
def run_script():
    print("🚀 BẮT ĐẦU SCRIPT CHUYỂN ĐỔI CẤU TRÚC FOLDER...")
    
    repo = FolderRepository()
    service = get_drive_service()
    
    # 1. Lấy tất cả folder trong DB
    all_folders = repo.get_all()
    print(f"👉 Tìm thấy {len(all_folders)} công ty trong Database.")

    for i, folder in enumerate(all_folders):
        company_name = folder['company_name']
        root_id = folder.get('root_folder_id')
        
        print(f"\n[{i+1}/{len(all_folders)}] Xử lý: {company_name}")
        
        if not root_id:
            print("   ⚠️ Chưa có Root ID Drive -> Bỏ qua.")
            continue

        try:
            # Lấy danh sách cấp 1 (để tìm TAI-LIEU-CONG-TY và TAI-LIEU-THUE)
            lv1_items = list_children(service, root_id)
            
            # --- XỬ LÝ NHÁNH CÔNG TY ---
            # Tìm folder có tên chứa "TAI-LIEU-CONG-TY"
            folder_cong_ty = next((f for f in lv1_items if "TAI-LIEU-CONG-TY" in f['name']), None)
            
            if folder_cong_ty:
                # Quét các năm (folder con là số có 4 chữ số)
                sub_cty = list_children(service, folder_cong_ty['id'])
                years = [f for f in sub_cty if f['name'].isdigit() and len(f['name']) == 4]
                
                for yf in years:
                    print(f"   📂 Đang quét năm {yf['name']} (Công ty)...")
                    # Vào trong năm, tìm các folder mục tiêu (1-HOA-DON-MUA...)
                    cats = list_children(service, yf['id'])
                    
                    for cat in cats:
                        # Nếu tên folder nằm trong danh sách cần sửa
                        if cat['name'] in RENAME_MAP_COMPANY:
                            rule_map = RENAME_MAP_COMPANY[cat['name']]
                            # Lấy các folder Quý bên trong
                            quarters = list_children(service, cat['id'])
                            
                            for q in quarters:
                                if q['name'] in rule_map:
                                    new_name = rule_map[q['name']]
                                    if q['name'] != new_name:
                                        if rename_file(service, q['id'], new_name):
                                            print(f"      ✅ Đổi: {cat['name']}/{q['name']} -> {new_name}")

            # --- XỬ LÝ NHÁNH THUẾ ---
            # Tìm folder có tên chứa "TAI-LIEU-THUE"
            folder_thue = next((f for f in lv1_items if "TAI-LIEU-THUE" in f['name']), None)
            
            if folder_thue:
                sub_thue = list_children(service, folder_thue['id'])
                years = [f for f in sub_thue if f['name'].isdigit() and len(f['name']) == 4]
                
                for yf in years:
                    print(f"   📂 Đang quét năm {yf['name']} (Thuế)...")
                    # Vào trong năm, tìm KE-TOAN
                    cats = list_children(service, yf['id'])
                    
                    for cat in cats:
                        if cat['name'] in RENAME_MAP_TAX:
                            rule_map = RENAME_MAP_TAX[cat['name']]
                            quarters = list_children(service, cat['id'])
                            
                            for q in quarters:
                                if q['name'] in rule_map:
                                    new_name = rule_map[q['name']]
                                    if q['name'] != new_name:
                                        if rename_file(service, q['id'], new_name):
                                            print(f"      ✅ Đổi: {cat['name']}/{q['name']} -> {new_name}")

        except Exception as e:
            print(f"   ❌ Lỗi xử lý công ty này: {e}")

    print("\n🎉 HOÀN TẤT TOÀN BỘ!")

if __name__ == "__main__":
    run_script()