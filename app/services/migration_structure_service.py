# app/services/migration_structure_service.py

from app.services.drive_service import (
    get_drive_service, 
    list_drive_subfolders,
    rename_drive_file
)
from app.db.repositories.folder_repo import FolderRepository

# ==========================================
# CẤU HÌNH ĐỔI TÊN
# ==========================================
RENAME_MAP_COMPANY = {
    "1-HOA-DON-MUA": {
        "QUÝ 1": "HDM_QUY-1", "QUÝ 2": "HDM_QUY-2", "QUÝ 3": "HDM_QUY-3", "QUÝ 4": "HDM_QUY-4",
        "QUY-1": "HDM_QUY-1", "QUY-2": "HDM_QUY-2", "QUY-3": "HDM_QUY-3", "QUY-4": "HDM_QUY-4"
    },
    "2-HOA-DON-BAN": {
        "QUÝ 1": "HDB_QUY-1", "QUÝ 2": "HDB_QUY-2", "QUÝ 3": "HDB_QUY-3", "QUÝ 4": "HDB_QUY-4",
        "QUY-1": "HDB_QUY-1", "QUY-2": "HDB_QUY-2", "QUY-3": "HDB_QUY-3", "QUY-4": "HDB_QUY-4"
    }
}

RENAME_MAP_TAX = {
    "KE-TOAN": {
        "QUY-1": "KT_QUY-1", "QUY-2": "KT_QUY-2", "QUY-3": "KT_QUY-3", "QUY-4-VA-CA-NAM": "KT_QUY-4-VA-CA-NAM",
        "QUY 1": "KT_QUY-1", "QUY 2": "KT_QUY-2", "QUY 3": "KT_QUY-3", "QUY 4": "KT_QUY-4-VA-CA-NAM",
        "QUÝ 1": "KT_QUY-1", "QUÝ 2": "KT_QUY-2", "QUÝ 3": "KT_QUY-3", "QUÝ 4": "KT_QUY-4-VA-CA-NAM"
    }
}

# ==========================================
# 1. HÀM QUÉT (PREVIEW)
# ==========================================
def scan_structure_changes(limit: int = 20):
    repo = FolderRepository()
    service = get_drive_service()
    all_folders = repo.get_all()
    
    pending_changes = []
    api_call_count = 0 

    def scan_year_folder(year_folder, company_name, category_type):
        nonlocal api_call_count
        rule_map = RENAME_MAP_COMPANY if category_type == "COMPANY" else RENAME_MAP_TAX
        
        cats = list_drive_subfolders(service, year_folder['id'])
        api_call_count += 1
        
        for cat in cats:
            if cat['name'] in rule_map:
                map_items = rule_map[cat['name']]
                quarters = list_drive_subfolders(service, cat['id'])
                api_call_count += 1
                
                for q in quarters:
                    current_name = q['name'].strip()
                    if current_name in map_items:
                        new_name = map_items[current_name]
                        if current_name != new_name:
                            pending_changes.append({
                                "drive_id": q['id'],
                                "company_name": company_name,
                                "year": year_folder['name'],
                                "parent_folder": cat['name'],
                                "old_name": current_name,
                                "new_name": new_name,
                                "type": category_type
                            })

    for folder in all_folders:
        if len(pending_changes) >= limit: break
        if api_call_count > 50: break # Giới hạn call API để tránh timeout

        if not folder.get('root_folder_id'): continue
        
        try:
            root_items = list_drive_subfolders(service, folder['root_folder_id'])
            api_call_count += 1
            
            f_congty = next((f for f in root_items if "TAI-LIEU-CONG-TY" in f['name']), None)
            if f_congty:
                years = list_drive_subfolders(service, f_congty['id'])
                valid_years = [y for y in years if y['name'].isdigit() and len(y['name']) == 4]
                for y in valid_years:
                    scan_year_folder(y, folder['company_name'], "COMPANY")
                    if len(pending_changes) >= limit: break

            if len(pending_changes) < limit:
                f_thue = next((f for f in root_items if "TAI-LIEU-THUE" in f['name']), None)
                if f_thue:
                    years = list_drive_subfolders(service, f_thue['id'])
                    valid_years = [y for y in years if y['name'].isdigit() and len(y['name']) == 4]
                    for y in valid_years:
                        scan_year_folder(y, folder['company_name'], "TAX")
                        if len(pending_changes) >= limit: break
                    
        except Exception as e:
            print(f"Error scanning {folder['company_name']}: {e}")

    return pending_changes

# ==========================================
# 2. HÀM THỰC THI ĐỔI TÊN
# ==========================================
def execute_rename_folder(drive_id: str, new_name: str):
    service = get_drive_service()
    return rename_drive_file(service, drive_id, new_name)

# ==========================================
# 3. HÀM DEEP FIX (DÙNG CHO CONSOLE LOG UI)
# ==========================================
def fix_structure_single_company(folder_db_id: int):
    repo = FolderRepository()
    folder = repo.get_by_id(folder_db_id)
    
    logs = []
    logs.append(f"🔵 Bắt đầu xử lý: {folder['company_name']}")

    if not folder.get('root_folder_id'):
        logs.append("   ⚠️ Chưa có Root ID Drive -> Bỏ qua.")
        return logs

    service = get_drive_service()
    
    try:
        root_items = list_drive_subfolders(service, folder['root_folder_id'])
        
        # NHÁNH CÔNG TY
        f_congty = next((f for f in root_items if "TAI-LIEU-CONG-TY" in f['name']), None)
        if f_congty:
            sub_items = list_drive_subfolders(service, f_congty['id'])
            years = [f for f in sub_items if f['name'].isdigit() and len(f['name']) == 4]
            
            for yf in years:
                logs.append(f"   📂 Năm {yf['name']} (Công ty)...")
                cats = list_drive_subfolders(service, yf['id'])
                for cat in cats:
                    if cat['name'] in RENAME_MAP_COMPANY:
                        rule_map = RENAME_MAP_COMPANY[cat['name']]
                        quarters = list_drive_subfolders(service, cat['id'])
                        for q in quarters:
                            current_name = q['name'].strip()
                            if current_name in rule_map:
                                new_name = rule_map[current_name]
                                if current_name != new_name:
                                    if rename_drive_file(service, q['id'], new_name):
                                        logs.append(f"      ✅ Đã sửa: {cat['name']}/{current_name} -> {new_name}")
                                    else:
                                        logs.append(f"      ❌ Lỗi đổi tên: {current_name}")

        # NHÁNH THUẾ
        f_thue = next((f for f in root_items if "TAI-LIEU-THUE" in f['name']), None)
        if f_thue:
            sub_items = list_drive_subfolders(service, f_thue['id'])
            years = [f for f in sub_items if f['name'].isdigit() and len(f['name']) == 4]
            
            for yf in years:
                logs.append(f"   📂 Năm {yf['name']} (Thuế)...")
                cats = list_drive_subfolders(service, yf['id'])
                for cat in cats:
                    if cat['name'] in RENAME_MAP_TAX:
                        rule_map = RENAME_MAP_TAX[cat['name']]
                        quarters = list_drive_subfolders(service, cat['id'])
                        for q in quarters:
                            current_name = q['name'].strip()
                            if current_name in rule_map:
                                new_name = rule_map[current_name]
                                if current_name != new_name:
                                    if rename_drive_file(service, q['id'], new_name):
                                        logs.append(f"      ✅ Đã sửa: {cat['name']}/{current_name} -> {new_name}")
                                    else:
                                        logs.append(f"      ❌ Lỗi đổi tên: {current_name}")

    except Exception as e:
        logs.append(f"   🔥 Lỗi hệ thống: {str(e)}")

    return logs