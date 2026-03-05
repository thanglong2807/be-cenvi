from app.services.drive_service import get_drive_service
from app.core.database import SessionLocal
from app.models.drive_change_state import DriveChangeState

service = get_drive_service()
db = SessionLocal()

token = service.changes().getStartPageToken(
    supportsAllDrives=True
).execute()["startPageToken"]

db.query(DriveChangeState).delete()
db.add(DriveChangeState(start_page_token=token))
db.commit()

print("✅ startPageToken initialized")
