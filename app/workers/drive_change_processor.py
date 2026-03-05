from app.models.company_folder import CompanyFolder
from app.models.drive_file import DriveFile
from app.models.drive_usage_company import DriveUsageCompany
from app.models.drive_usage_user import DriveUsageUser
from app.models.drive_change_log import DriveChangeLog


def process_change(db, change: dict):
    file_id = change.get("fileId")

    # ❌ File bị remove hoàn toàn
    if change.get("removed"):
        handle_deleted_file(db, file_id)
        return

    file = change.get("file")
    if not file:
        return

    parents = file.get("parents")
    if not parents:
        return

    parent_folder_id = parents[0]

    # 1️⃣ Map folder → company + business_domain
    folder = db.query(CompanyFolder).filter_by(
        folder_id=parent_folder_id
    ).first()

    if not folder:
        # file ngoài scope quản lý
        return

    company_id = folder.company_id
    domain_id = folder.business_domain_id

    size = int(file.get("size", 0))
    email = (
        file.get("lastModifyingUser", {})
        .get("emailAddress")
    )

    # 2️⃣ Tìm file cũ
    existing = db.query(DriveFile).filter_by(
        file_id=file_id
    ).first()

    # 🟢 FILE MỚI
    if not existing:
        create_new_file(
            db, file_id, company_id, domain_id,
            parent_folder_id, file, size, email
        )
        return

    # 🟡 FILE UPDATE
    update_existing_file(
        db, existing, size, email
    )


# tạo file mới

def create_new_file(db, file_id, company_id, domain_id, parent_folder_id, file, size, email):
    db.add(DriveFile(
        file_id=file_id,
        company_id=company_id,
        business_domain_id=domain_id,
        parent_folder_id=parent_folder_id,
        name=file.get("name"),
        size=size,
        mime_type=file.get("mimeType"),
        last_modified_by=email
    ))

    increase_usage(db, company_id, domain_id, email, size)

    db.add(DriveChangeLog(
        change_id=file_id,
        file_id=file_id,
        company_id=company_id,
        business_domain_id=domain_id,
        change_type="created",
        delta_bytes=size,
        actor_email=email
    ))

    db.commit()


# xóa file 

def handle_deleted_file(db, file_id):
    file = db.query(DriveFile).filter_by(file_id=file_id).first()
    if not file:
        return

    decrease = -(file.size or 0)

    increase_usage(
        db,
        file.company_id,
        file.business_domain_id,
        file.last_modified_by,
        decrease
    )

    file.is_deleted = True
    file.size = 0

    db.add(DriveChangeLog(
        change_id=file_id,
        file_id=file_id,
        company_id=file.company_id,
        business_domain_id=file.business_domain_id,
        change_type="deleted",
        delta_bytes=decrease,
        actor_email=file.last_modified_by
    ))

    db.commit()

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

    db.commit()
