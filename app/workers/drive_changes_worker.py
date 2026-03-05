from app.services.drive_service import get_drive_service
from app.core.database import SessionLocal
from app.models.drive_change_state import DriveChangeState
from app.workers.drive_change_processor import process_change


def run_drive_changes_worker():
    service = get_drive_service()
    db = SessionLocal()

    # 1️⃣ Lấy startPageToken
    state = db.query(DriveChangeState).first()

    if not state:
        token = service.changes().getStartPageToken(
            supportsAllDrives=True
        ).execute()["startPageToken"]

        state = DriveChangeState(
            start_page_token=token
        )
        db.add(state)
        db.commit()
        print("✅ Initialized startPageToken")
        return

    page_token = state.start_page_token
    print("▶ Start syncing from token:", page_token)

    while True:
        response = service.changes().list(
            pageToken=page_token,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            fields="nextPageToken,newStartPageToken,changes(fileId,removed,file(name,parents,size,mimeType,lastModifyingUser(emailAddress)))"
        ).execute()

        for change in response.get("changes", []):
            process_change(db, change)

        # next page
        page_token = response.get("nextPageToken")

        if not page_token:
            # update new token
            new_token = response.get("newStartPageToken")
            if new_token:
                state.start_page_token = new_token
                db.commit()
                print("✔ Sync complete, token updated")
            break

    db.close()
