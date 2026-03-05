from app.core.database import Base, engine
from app.models.company_folder import CompanyFolder
from app.models.drive_usage_company import DriveUsageCompany
from app.models.drive_usage_user import DriveUsageUser
from app.models.drive_change_log import DriveChangeLog
from app.models.drive_change_state import DriveChangeState

Base.metadata.create_all(bind=engine)
print("✅ All DB tables created")
