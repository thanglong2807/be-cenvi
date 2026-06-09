from app.core.database import get_db
from app.services.workflow_service import WorkflowService

db = next(get_db())
svc = WorkflowService(db)
try:
    result = svc.list_waiting_review()
    print(f"Total waiting: {len(result)}")
    for item in result[:3]:
        print(item)
except Exception as e:
    print(f"ERROR: {e}")
    import traceback; traceback.print_exc()
