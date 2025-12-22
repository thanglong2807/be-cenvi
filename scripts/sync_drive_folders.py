from app.core.database import SessionLocal
from app.services.drive_service import get_drive_service
from app.models.company_folder_permissions import CompanyFolderPermission

def detect_domain(folder_name: str):
    name = folder_name.upper()

    if name.startswith("HANH-CHINH"):
        return "HANH_CHINH"
    if name.startswith("TAI-LIEU-CONG-TY"):
        return "TAI_LIEU_CONG_TY"
    if name.startswith("TAI-LIEU-THUE"):
        return "TAI_LIEU_THUE"

    return None


def list_level1_folders(service, parent_id):
    results = service.files().list(
        q=(
            f"'{parent_id}' in parents "
            "and mimeType='application/vnd.google-apps.folder' "
            "and trashed=false"
        ),
        fields="files(id,name)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
    ).execute()

    return results.get("files", [])


def run():
    db = SessionLocal()
    service = get_drive_service()

    companies = db.query(Company).filter(
        Company.drive_folder_id.isnot(None)
    ).all()

    print(f"🔍 Syncing {len(companies)} companies\n")

    for company in companies:
        print(f"🏢 Company: {company.code}")

        folders = list_level1_folders(service, company.drive_folder_id)

        if not folders:
            print("  ⚠️ No level-1 folders found")
        continue

    # lấy permission rows của công ty
    perms = db.query(CompanyFolderPermission).filter(
        CompanyFolderPermission.company_id == company.id
    ).all()

    for f in folders:
        domain = detect_domain(f["name"])

        if not domain:
            print(f"  ⚠️ Unknown domain: {f['name']}")
            continue

        print(f"  📁 {domain}: {f['name']}")

        # gán folder cho permission tương ứng domain
        for p in perms:
            if p.folder_id is None:
                p.folder_id = f["id"]
                p.folder_name = f["name"]

    try:
        db.commit()
        print("  ✅ Synced\n")
    except Exception as e:
        db.rollback()
        print(f"  ❌ Commit error: {e}\n")

    db.close()
    print("🎉 SYNC DRIVE DONE")


if __name__ == "__main__":
    run()
