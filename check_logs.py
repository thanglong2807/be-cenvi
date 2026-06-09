from app.core.database import engine
from sqlalchemy import text
with engine.connect() as c:
    r = c.execute(text("SELECT id, task_id, period, status, company_workflow_id FROM workflow_task_logs WHERE status = 'waiting_review' LIMIT 10"))
    rows = r.fetchall()
    print("waiting_review rows:", len(rows))
    for row in rows:
        print(dict(row._mapping))

    r2 = c.execute(text("SELECT id, task_id, period, status FROM workflow_task_logs ORDER BY updated_at DESC LIMIT 10"))
    print("\nLatest 10 logs:")
    for row in r2.fetchall():
        print(dict(row._mapping))
