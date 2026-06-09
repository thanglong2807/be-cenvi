from app.core.database import engine
from sqlalchemy import text
from datetime import datetime

now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

with engine.connect() as c:
    logs = c.execute(text("""
        SELECT wtl.id, wtl.task_id, wtl.period, wtl.status, wtl.review_note,
               wtl.company_workflow_id, cw.company_id
        FROM workflow_task_logs wtl
        JOIN company_workflows cw ON cw.id = wtl.company_workflow_id
        WHERE wtl.status = 'rejected'
    """)).fetchall()

    tasks = {}
    for row in logs:
        if row.task_id not in tasks:
            r = c.execute(text(f"SELECT id, title FROM workflow_tasks WHERE id={row.task_id}")).fetchone()
            if r: tasks[r.id] = r.title

    inserted = 0
    for log in logs:
        task_name = tasks.get(log.task_id, f"Task #{log.task_id}")
        period = log.period or ""
        if "-Q" in period:
            y, q = period.split("-Q"); ps = f"Q{q}/{y}"
        elif len(period) == 4:
            ps = f"Năm {period}"
        elif "-" in period:
            parts = period.split("-"); ps = f"{parts[1]}/{parts[0]}"
        else:
            ps = period

        body = f'"{task_name}" — kỳ {ps} bị từ chối.'
        if log.review_note:
            body += f"\nLý do: {log.review_note}"

        c.execute(text("""
            INSERT INTO notifications (user_id, type, title, body, link, is_read, created_at)
            VALUES (14, 'task_rejected', '❌ Task bị từ chối — cần sửa lại', :body, :link, 0, :now)
        """), {
            "body": body,
            "link": f"/my-companies?company={log.company_id}&workflow={log.company_workflow_id}",
            "now": now,
        })
        inserted += 1
    c.commit()
    print(f"Inserted {inserted} rejected notifications for user_id=14")
