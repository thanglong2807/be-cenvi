from app.services.drive_service import get_drive_service
from app.core.database import SessionLocal
from app.models.company_folder import CompanyFolder
from app.models.drive_file import DriveFile
from app.models.drive_usage_company import DriveUsageCompany
from app.models.drive_usage_user import DriveUsageUser


def run_drive_seed_worker():
    service = get_drive_service()
    db = SessionLocal()

    folders = db.query(CompanyFolder).all()
    print(f"🔍 Seeding {len(folders)} folders")

    for folder in folders:
        seed_folder(
            service,
            db,
            folder.folder_id,
            folder.company_id,
            folder.business_domain_id
        )

    db.close()
    print("🎉 Seed completed")

# SEED FILE THEO FOLDER (CÓ PHÂN TRANG)


def seed_folder(service, db, folder_id, company_id, domain_id):
    page_token = None
    total = 0

    while True:
        response = service.files().list(
            q=(
                f"'{folder_id}' in parents "
                "and trashed=false"
            ),
            fields="nextPageToken,files(id,name,size,mimeType,lastModifyingUser(emailAddress))",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            pageToken=page_token,
            pageSize=1000
        ).execute()

        for f in response.get("files", []):
            size = int(f.get("size", 0))
            email = f.get("lastModifyingUser", {}).get("emailAddress")

            if db.query(DriveFile).filter_by(file_id=f["id"]).first():
                continue

            db.add(DriveFile(
                file_id=f["id"],
                company_id=company_id,
                business_domain_id=domain_id,
                parent_folder_id=folder_id,
                name=f.get("name"),
                size=size,
                mime_type=f.get("mimeType"),
                last_modified_by=email
            ))

            increase_usage(db, company_id, domain_id, email, size)
            total += size

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    db.commit()
    print(f"✔ Seeded folder {folder_id} ({total} bytes)")


# UPDATE USAGE (DÙNG LẠI LOGIC CŨ)

def increase_usage(db, company_id, domain_id, email, delta):
    usage = db.query(DriveUsageCompany).filter_by(
        company_id=company_id,
        business_domain_id=domain_id
    ).first()

    if not usage:
        usage = DriveUsageCompany(
            company_id=company_id,
            business_domain_id=domain_id,
            total_bytes=0
        )
        db.add(usage)

    usage.total_bytes += delta

    if email:
        user = db.query(DriveUsageUser).filter_by(
            company_id=company_id,
            business_domain_id=domain_id,
            email=email
        ).first()

        if not user:
            user = DriveUsageUser(
                company_id=company_id,
                business_domain_id=domain_id,
                email=email,
                total_bytes=0
            )
            db.add(user)

        user.total_bytes += delta
