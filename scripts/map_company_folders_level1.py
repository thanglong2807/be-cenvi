import unicodedata
import re

from app.services.drive_service import get_drive_service
from app.core.database import SessionLocal
from app.models.company_folder import CompanyFolder


# ==============================
# NORMALIZE FOLDER NAME
# ==============================
def normalize_name(name: str) -> str:
    """
    Ví dụ:
    HANH-CHINH_ASANA           -> HANH-CHINH
    TAI-LIEU-CONG-TY_ABC       -> TAI-LIEU-CONG-TY
    TÀI LIỆU CÔNG TY           -> TAI-LIEU-CONG-TY
    """

    # bỏ hậu tố _ASANA, _ABC, ...
    name = name.split("_")[0]

    # bỏ dấu tiếng Việt
    name = unicodedata.normalize("NFD", name)
    name = "".join(c for c in name if unicodedata.category(c) != "Mn")

    name = name.upper()

    # mọi ký tự không phải chữ/số -> "-"
    name = re.sub(r"[^A-Z0-9]+", "-", name)

    return name.strip("-")


# ==============================
# DOMAIN MAP (SAU NORMALIZE)
# ==============================
DOMAIN_MAP = {
    "HANH-CHINH": "HANH_CHINH",
    "TAI-LIEU-CONG-TY": "TAI_LIEU_CONG_TY",
    "TAI-LIEU-THUE": "TAI_LIEU_THUE",
}


# ==============================
# MAIN LOGIC
# ==============================
def run():
    service = get_drive_service()
    db = SessionLocal()

    # map code -> id
    domain_map = {
        d.code: d.id
        for d in db.query(BusinessDomain).all()
    }

    companies = db.query(Company).all()

    if not companies:
        print("❌ Không có company nào trong DB")
        return

    for company in companies:
        print(f"\n🔍 Mapping LEVEL-1 folders for: {company.name}")

        results = service.files().list(
            q=(
                f"'{company.drive_folder_id}' in parents "
                "and mimeType='application/vnd.google-apps.folder' "
                "and trashed=false"
            ),
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            fields="files(id,name)"
        ).execute()

        folders = results.get("files", [])

        if not folders:
            print("  ⚠️ Không tìm thấy folder con cấp 1")
            continue

        for f in folders:
            raw_name = f["name"]
            normalized = normalize_name(raw_name)

            if normalized not in DOMAIN_MAP:
                print(f"  ⚠️ Ignored (no domain): {raw_name}")
                continue

            domain_code = DOMAIN_MAP[normalized]

            if domain_code not in domain_map:
                print(f"  ❌ Domain chưa tồn tại trong DB: {domain_code}")
                continue

            exists = db.query(CompanyFolder).filter_by(
                folder_id=f["id"]
            ).first()

            if exists:
                print(f"  ⏩ Skip (exists): {raw_name}")
                continue

            db.add(CompanyFolder(
                company_id=company.id,
                folder_id=f["id"],
                business_domain_id=domain_map[domain_code],
                parent_folder_id=company.drive_folder_id,
                level=1
            ))

            print(f"  ✅ Mapped: {raw_name} → {domain_code}")

        db.commit()

    db.close()
    print("\n🎉 Mapping LEVEL-1 folders DONE")


# ==============================
# ENTRY
# ==============================
if __name__ == "__main__":
    run()
