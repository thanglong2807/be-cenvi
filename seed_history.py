"""Seed dữ liệu mẫu: 3 workflows lịch sử để test tính năng xem lịch sử."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import SessionLocal
from app.models.workflow_model import CompanyWorkflow, WorkflowTaskLog, WorkflowTask, WorkflowPhase
from datetime import datetime, timedelta
import random

db = SessionLocal()

COMPANY_ID = 1358
TEMPLATE_ID = 4

history_workflows = [
    {"year": 2026, "quarter": 1, "status": "completed"},
    {"year": 2025, "quarter": 4, "status": "completed"},
    {"year": 2025, "quarter": 3, "status": "completed"},
]

tasks = (
    db.query(WorkflowTask)
    .join(WorkflowPhase)
    .filter(WorkflowPhase.template_id == TEMPLATE_ID)
    .all()
)
print(f"Found {len(tasks)} tasks in template {TEMPLATE_ID}")

random.seed(42)

for hw in history_workflows:
    yr, qt = hw["year"], hw["quarter"]

    # Kiểm tra đã tồn tại chưa
    existing = db.query(CompanyWorkflow).filter(
        CompanyWorkflow.company_id == COMPANY_ID,
        CompanyWorkflow.year == yr,
        CompanyWorkflow.quarter == qt,
    ).first()
    if existing:
        print(f"Skip Q{qt}/{yr} — already exists (id={existing.id})")
        continue

    wf = CompanyWorkflow(
        company_id=COMPANY_ID,
        template_id=TEMPLATE_ID,
        year=yr,
        quarter=qt,
        status=hw["status"],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(wf)
    db.flush()
    wf_id = wf.id
    print(f"Created workflow id={wf_id} Q{qt}/{yr}")

    for task in tasks:
        freq = task.frequency
        if freq == "monthly":
            months = [(qt - 1) * 3 + 1, (qt - 1) * 3 + 2, (qt - 1) * 3 + 3]
            periods = [f"{yr}-{str(m).zfill(2)}" for m in months]
        elif freq == "quarterly":
            periods = [f"{yr}-Q{qt}"]
        else:
            periods = [str(yr)]

        for period in periods:
            r = random.random()
            if r < 0.75:
                status = "approved"
                review_status = "approved"
                done_at = datetime.now() - timedelta(days=random.randint(30, 180))
                reviewed_at = done_at + timedelta(days=2)
                reviewed_by = "Admin"
                note = "Đã xử lý xong, file đính kèm đầy đủ."
            elif r < 0.9:
                status = "waiting_review"
                review_status = None
                done_at = datetime.now() - timedelta(days=random.randint(10, 30))
                reviewed_at = None
                reviewed_by = None
                note = "Đã hoàn thành, chờ kiểm duyệt."
            else:
                status = "pending"
                review_status = None
                done_at = None
                reviewed_at = None
                reviewed_by = None
                note = None

            log = WorkflowTaskLog(
                company_workflow_id=wf_id,
                task_id=task.id,
                period=period,
                status=status,
                review_status=review_status,
                done_by="Nguyen Van A",
                done_at=done_at,
                note=note,
                reviewed_at=reviewed_at,
                reviewed_by=reviewed_by,
                updated_at=datetime.now(),
            )
            db.add(log)

db.commit()
print("Done! History workflows created successfully.")
db.close()
