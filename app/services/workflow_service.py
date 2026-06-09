# app/services/workflow_service.py

import secrets
from datetime import datetime, date
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.workflow_model import (
    WorkflowTemplate, WorkflowPhase, WorkflowTask,
    CompanyWorkflow, WorkflowTaskLog, CompanyTaskFile,
)
from app.models.company_info_model import CompanyInfo
from app.models.notification_model import Notification
from app.models.admin_user_model import AdminUser
from app.schemas.workflow_schema import (
    TemplateCreate, TemplateUpdate,
    PhaseCreate, PhaseUpdate,
    TaskCreate, TaskUpdate,
    CompanyWorkflowCreate, CompanyWorkflowUpdate,
    TaskLogUpdate, TaskLogReview,
)


def _periods_for_task(frequency: str, year: int, quarter: int) -> list[str]:
    """Sinh danh sách period cho task theo frequency và quý."""
    if frequency == "monthly":
        start_month = (quarter - 1) * 3 + 1
        return [f"{year}-{str(start_month + i).zfill(2)}" for i in range(3)]
    elif frequency == "quarterly":
        return [f"{year}-Q{quarter}"]
    else:  # yearly
        return [str(year)]


def _deadline_for_period(period: str) -> date:
    """Ngày cuối của một kỳ."""
    import calendar
    if "-Q" in period:
        year, q = period.split("-Q")
        last_month = int(q) * 3
        last_day = calendar.monthrange(int(year), last_month)[1]
        return date(int(year), last_month, last_day)
    elif len(period) == 4:  # yearly "2026"
        return date(int(period), 12, 31)
    else:  # monthly "2026-04"
        year, month = period.split("-")
        last_day = calendar.monthrange(int(year), int(month))[1]
        return date(int(year), int(month), last_day)


def _warning_days(frequency: str) -> int:
    return {"monthly": 5, "quarterly": 14, "yearly": 30}.get(frequency, 5)


def _is_near_deadline(period: str, frequency: str) -> bool:
    deadline = _deadline_for_period(period)
    days_left = (deadline - date.today()).days
    return 0 <= days_left <= _warning_days(frequency)


class WorkflowService:
    def __init__(self, db: Session):
        self.db = db

    # =========================================================================
    # TEMPLATE CRUD (Admin)
    # =========================================================================

    def list_templates(self) -> list:
        templates = self.db.query(WorkflowTemplate).order_by(WorkflowTemplate.id).all()
        result = []
        for t in templates:
            task_count = sum(len(p.tasks) for p in t.phases)
            result.append({
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "is_active": t.is_active,
                "phase_count": len(t.phases),
                "task_count": task_count,
                "created_at": t.created_at,
                "updated_at": t.updated_at,
            })
        return result

    def get_template(self, template_id: int) -> WorkflowTemplate:
        obj = self.db.query(WorkflowTemplate).filter(WorkflowTemplate.id == template_id).first()
        if not obj:
            raise HTTPException(status_code=404, detail=f"Template id={template_id} không tồn tại")
        return obj

    def create_template(self, data: TemplateCreate) -> WorkflowTemplate:
        now = datetime.now()
        template = WorkflowTemplate(
            name=data.name,
            description=data.description,
            is_active=data.is_active,
            created_at=now,
            updated_at=now,
        )
        self.db.add(template)
        self.db.flush()  # lấy template.id

        for phase_data in (data.phases or []):
            self._add_phase(template.id, phase_data)

        self.db.commit()
        self.db.refresh(template)
        return template

    def update_template(self, template_id: int, data: TemplateUpdate) -> WorkflowTemplate:
        obj = self.get_template(template_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        obj.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete_template(self, template_id: int) -> dict:
        obj = self.get_template(template_id)
        # Kiểm tra có company workflow đang dùng không
        in_use = self.db.query(CompanyWorkflow).filter(
            CompanyWorkflow.template_id == template_id
        ).count()
        if in_use:
            raise HTTPException(
                status_code=409,
                detail=f"Template đang được dùng bởi {in_use} quy trình công ty, không thể xóa"
            )
        self.db.delete(obj)
        self.db.commit()
        return {"message": f"Đã xóa template '{obj.name}'"}

    # =========================================================================
    # PHASE CRUD
    # =========================================================================

    def _add_phase(self, template_id: int, data: PhaseCreate) -> WorkflowPhase:
        phase = WorkflowPhase(
            template_id=template_id,
            name=data.name,
            order_index=data.order_index,
            created_at=datetime.now(),
        )
        self.db.add(phase)
        self.db.flush()
        for task_data in (data.tasks or []):
            self._add_task(phase.id, task_data)
        return phase

    def add_phase(self, template_id: int, data: PhaseCreate) -> WorkflowPhase:
        self.get_template(template_id)  # 404 check
        phase = self._add_phase(template_id, data)
        self.db.commit()
        self.db.refresh(phase)
        return phase

    def update_phase(self, phase_id: int, data: PhaseUpdate) -> WorkflowPhase:
        obj = self.db.query(WorkflowPhase).filter(WorkflowPhase.id == phase_id).first()
        if not obj:
            raise HTTPException(status_code=404, detail=f"Phase id={phase_id} không tồn tại")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete_phase(self, phase_id: int) -> dict:
        obj = self.db.query(WorkflowPhase).filter(WorkflowPhase.id == phase_id).first()
        if not obj:
            raise HTTPException(status_code=404, detail=f"Phase id={phase_id} không tồn tại")
        name = obj.name
        self.db.delete(obj)
        self.db.commit()
        return {"message": f"Đã xóa phase '{name}'"}

    # =========================================================================
    # TASK CRUD
    # =========================================================================

    def list_automation_tasks(self) -> list:
        """Tổng hợp tất cả task có automation_type='script' từ mọi template."""
        tasks = (
            self.db.query(WorkflowTask)
            .filter(WorkflowTask.automation_type == "script")
            .order_by(WorkflowTask.id)
            .all()
        )
        result = []
        for task in tasks:
            phase = self.db.query(WorkflowPhase).filter(WorkflowPhase.id == task.phase_id).first()
            template = self.db.query(WorkflowTemplate).filter(WorkflowTemplate.id == phase.template_id).first() if phase else None
            result.append({
                "task_id": task.id,
                "task_title": task.title,
                "automation_note": task.automation_note,
                "automation_status": task.automation_status,
                "phase_id": phase.id if phase else None,
                "phase_name": phase.name if phase else None,
                "template_id": template.id if template else None,
                "template_name": template.name if template else None,
            })
        return result

    def _add_task(self, phase_id: int, data: TaskCreate) -> WorkflowTask:
        task = WorkflowTask(
            phase_id=phase_id,
            title=data.title,
            description=data.description,
            is_required=data.is_required,
            order_index=data.order_index,
            frequency=data.frequency,
            automation_type=data.automation_type,
            automation_note=data.automation_note,
            automation_status=data.automation_status,
            created_at=datetime.now(),
        )
        self.db.add(task)
        return task

    def add_task(self, phase_id: int, data: TaskCreate) -> WorkflowTask:
        phase = self.db.query(WorkflowPhase).filter(WorkflowPhase.id == phase_id).first()
        if not phase:
            raise HTTPException(status_code=404, detail=f"Phase id={phase_id} không tồn tại")
        task = self._add_task(phase_id, data)
        self.db.commit()
        self.db.refresh(task)
        return task

    def update_task(self, task_id: int, data: TaskUpdate) -> WorkflowTask:
        obj = self.db.query(WorkflowTask).filter(WorkflowTask.id == task_id).first()
        if not obj:
            raise HTTPException(status_code=404, detail=f"Task id={task_id} không tồn tại")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete_task(self, task_id: int) -> dict:
        obj = self.db.query(WorkflowTask).filter(WorkflowTask.id == task_id).first()
        if not obj:
            raise HTTPException(status_code=404, detail=f"Task id={task_id} không tồn tại")
        title = obj.title
        self.db.delete(obj)
        self.db.commit()
        return {"message": f"Đã xóa task '{title}'"}

    # =========================================================================
    # COMPANY WORKFLOW
    # =========================================================================

    def start_company_workflow(self, company_id: int, data: CompanyWorkflowCreate) -> dict:
        """
        Tạo workflow instance cho công ty theo quý.
        Tự động tạo WorkflowTaskLog (pending) cho tất cả task trong template.
        """
        # Validate
        company = self.db.query(CompanyInfo).filter(CompanyInfo.id == company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail=f"Công ty id={company_id} không tồn tại")

        template = self.get_template(data.template_id)
        if not template.is_active:
            raise HTTPException(status_code=400, detail="Template này đã bị vô hiệu hóa")

        if not 1 <= data.quarter <= 4:
            raise HTTPException(status_code=400, detail="Quarter phải là 1, 2, 3 hoặc 4")

        # Kiểm tra đã tồn tại chưa
        existing = self.db.query(CompanyWorkflow).filter(
            CompanyWorkflow.company_id == company_id,
            CompanyWorkflow.template_id == data.template_id,
            CompanyWorkflow.year == data.year,
            CompanyWorkflow.quarter == data.quarter,
        ).first()
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Quy trình Q{data.quarter}/{data.year} với template này đã tồn tại (id={existing.id})"
            )

        now = datetime.now()
        workflow = CompanyWorkflow(
            company_id=company_id,
            template_id=data.template_id,
            year=data.year,
            quarter=data.quarter,
            status="pending",
            assigned_employee_id=data.assigned_employee_id,
            note=data.note,
            created_at=now,
            updated_at=now,
        )
        self.db.add(workflow)
        self.db.flush()

        # Tạo task logs theo từng kỳ (period) dựa vào frequency
        log_count = 0
        for phase in template.phases:
            for task in phase.tasks:
                for period in _periods_for_task(task.frequency, data.year, data.quarter):
                    log = WorkflowTaskLog(
                        company_workflow_id=workflow.id,
                        task_id=task.id,
                        period=period,
                        status="pending",
                        created_at=now,
                        updated_at=now,
                    )
                    self.db.add(log)
                    log_count += 1

        self.db.commit()
        self.db.refresh(workflow)
        return self._build_workflow_detail(workflow)

    def list_company_workflows(self, company_id: int) -> list:
        """Danh sách tất cả workflow của 1 công ty, kèm progress."""
        workflows = (
            self.db.query(CompanyWorkflow)
            .filter(CompanyWorkflow.company_id == company_id)
            .order_by(CompanyWorkflow.year.desc(), CompanyWorkflow.quarter.desc())
            .all()
        )
        return [self._build_workflow_list_item(w) for w in workflows]

    def get_company_workflow(self, company_id: int, workflow_id: int) -> dict:
        """Chi tiết workflow kèm toàn bộ phases, tasks và trạng thái từng task."""
        workflow = self.db.query(CompanyWorkflow).filter(
            CompanyWorkflow.id == workflow_id,
            CompanyWorkflow.company_id == company_id,
        ).first()
        if not workflow:
            raise HTTPException(status_code=404, detail=f"Workflow id={workflow_id} không tồn tại")
        return self._build_workflow_detail(workflow)

    def update_company_workflow(self, company_id: int, workflow_id: int,
                                data: CompanyWorkflowUpdate) -> dict:
        workflow = self.db.query(CompanyWorkflow).filter(
            CompanyWorkflow.id == workflow_id,
            CompanyWorkflow.company_id == company_id,
        ).first()
        if not workflow:
            raise HTTPException(status_code=404, detail=f"Workflow id={workflow_id} không tồn tại")

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(workflow, field, value)
        workflow.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(workflow)
        return self._build_workflow_detail(workflow)

    def update_task_log(self, company_id: int, workflow_id: int,
                        task_id: int, period: str, data: TaskLogUpdate,
                        submitter_user_id: Optional[int] = None) -> dict:
        """Nhân viên cập nhật trạng thái 1 task theo kỳ."""
        workflow = self.db.query(CompanyWorkflow).filter(
            CompanyWorkflow.id == workflow_id,
            CompanyWorkflow.company_id == company_id,
        ).first()
        if not workflow:
            raise HTTPException(status_code=404, detail=f"Workflow id={workflow_id} không tồn tại")

        log = self.db.query(WorkflowTaskLog).filter(
            WorkflowTaskLog.company_workflow_id == workflow_id,
            WorkflowTaskLog.task_id == task_id,
            WorkflowTaskLog.period == period,
        ).first()
        if not log:
            task_exists = self.db.query(WorkflowTask).filter(WorkflowTask.id == task_id).first()
            if not task_exists:
                raise HTTPException(status_code=404, detail=f"Task id={task_id} không tồn tại")
            now = datetime.now()
            log = WorkflowTaskLog(
                company_workflow_id=workflow_id,
                task_id=task_id,
                period=period,
                status="pending",
                created_at=now,
                updated_at=now,
            )
            self.db.add(log)
            self.db.flush()

        # Khi chuyển sang waiting_review thì set done_at
        now = datetime.now()
        log.status = data.status
        log.note = data.note
        log.done_by = data.done_by
        log.done_at = now if data.status == "waiting_review" else log.done_at
        log.updated_at = now
        # Lưu lại user_id của người submit để dùng cho notification sau này
        if submitter_user_id and data.status == "waiting_review":
            log.submitted_by_user_id = submitter_user_id

        # Nếu submit chờ duyệt → tạo notification cho reviewer
        if data.status == "waiting_review":
            self._notify_reviewers(task_id, company_id, workflow_id, period)

        self._sync_workflow_status(workflow)
        self.db.commit()

        return {"task_id": task_id, "period": period, "status": log.status}

    def review_task_log(self, company_id: int, workflow_id: int,
                        task_id: int, period: str, data: TaskLogReview,
                        reviewer_name: str) -> dict:
        """Reviewer duyệt hoặc từ chối task."""
        if data.action not in ("approved", "rejected"):
            raise HTTPException(status_code=400, detail="action phải là approved hoặc rejected")

        log = self.db.query(WorkflowTaskLog).filter(
            WorkflowTaskLog.company_workflow_id == workflow_id,
            WorkflowTaskLog.task_id == task_id,
            WorkflowTaskLog.period == period,
        ).first()
        if not log:
            raise HTTPException(status_code=404, detail="Không tìm thấy log")
        if log.status != "waiting_review":
            raise HTTPException(status_code=400, detail="Task chưa ở trạng thái chờ duyệt")

        now = datetime.now()
        log.review_status = data.action
        log.reviewed_by = reviewer_name
        log.reviewed_at = now
        log.review_note = data.review_note
        log.status = data.action  # approved / rejected
        log.updated_at = now

        # Notify nhân viên
        self._notify_employee_review(log, data.action, data.review_note, company_id, workflow_id)

        workflow = self.db.query(CompanyWorkflow).filter(CompanyWorkflow.id == workflow_id).first()
        if workflow:
            self._sync_workflow_status(workflow)

        self.db.commit()
        return {"task_id": task_id, "period": period, "status": log.status, "review_status": log.review_status}

    def _notify_reviewers(self, task_id: int, company_id: int, workflow_id: int, period: str):
        """Tạo thông báo cho tất cả reviewer."""
        task = self.db.query(WorkflowTask).filter(WorkflowTask.id == task_id).first()
        task_name = task.title if task else f"Task #{task_id}"
        period_str = self._format_period(period)
        # Gửi cho REVIEWER và ADMIN (phòng khi chưa có ai role REVIEWER)
        reviewers = self.db.query(AdminUser).filter(
            AdminUser.role.in_(["REVIEWER", "ADMIN"]),
            AdminUser.is_active == True,
        ).all()
        for r in reviewers:
            self.db.add(Notification(
                user_id=r.id,
                type="waiting_review",
                title="🔔 Có task cần kiểm duyệt",
                body=f'"{task_name}"' + (f" — kỳ {period_str}" if period_str else "") + " đang chờ phê duyệt.",
                link=f"/reviewer/dashboard?workflow={workflow_id}&company={company_id}",
            ))

    @staticmethod
    def _format_period(period: str) -> str:
        """Chuyển '2026-06' → '06/2026', '2026-Q2' → 'Q2/2026', '2026' → 'Năm 2026'."""
        if not period:
            return ""
        if "-Q" in period:
            y, q = period.split("-Q")
            return f"Q{q}/{y}"
        if len(period) == 4:
            return f"Năm {period}"
        parts = period.split("-")
        if len(parts) == 2:
            return f"{parts[1]}/{parts[0]}"
        return period

    def _notify_employee_review(self, log: WorkflowTaskLog, action: str,
                                 review_note: Optional[str], company_id: int, workflow_id: int):
        """Tạo thông báo cho nhân viên phụ trách workflow."""
        workflow = self.db.query(CompanyWorkflow).filter(CompanyWorkflow.id == workflow_id).first()
        if not workflow:
            return

        # Ưu tiên: user đã submit task (có user_id thực)
        user = None
        if log.submitted_by_user_id:
            user = self.db.query(AdminUser).filter(
                AdminUser.id == log.submitted_by_user_id
            ).first()

        # Fallback: user theo assigned_employee_id
        if not user and workflow.assigned_employee_id:
            user = self.db.query(AdminUser).filter(
                AdminUser.employee_id == workflow.assigned_employee_id
            ).first()

        if not user:
            # Fallback cuối: gửi cho tất cả ADMIN + REVIEWER
            recipients = self.db.query(AdminUser).filter(
                AdminUser.role.in_(["ADMIN", "REVIEWER"]),
                AdminUser.is_active == True,
            ).all()
        else:
            recipients = [user]
        task = self.db.query(WorkflowTask).filter(WorkflowTask.id == log.task_id).first()
        task_name = task.title if task else f"Task #{log.task_id}"
        period_str = self._format_period(log.period)

        if action == "approved":
            title = "✅ Task đã được duyệt"
            body = f'"{task_name}"'
            if period_str:
                body += f" — kỳ {period_str}"
            body += " đã được phê duyệt."
        else:
            title = "❌ Task bị từ chối — cần sửa lại"
            body = f'"{task_name}"'
            if period_str:
                body += f" — kỳ {period_str}"
            body += " bị từ chối."
            if review_note:
                body += f'\nLý do: {review_note}'

        for recipient in recipients:
            self.db.add(Notification(
                user_id=recipient.id,
                type=f"task_{action}",
                title=title,
                body=body,
                link=f"/my-companies?company={company_id}&workflow={workflow_id}",
            ))

    def list_waiting_review(self) -> list:
        """Lấy tất cả task đang chờ duyệt trên toàn hệ thống."""
        from app.models.company_info_model import CompanyInfo
        logs = self.db.query(WorkflowTaskLog).filter(
            WorkflowTaskLog.status == "waiting_review"
        ).order_by(WorkflowTaskLog.updated_at.desc()).all()

        result = []
        for log in logs:
            wf = self.db.query(CompanyWorkflow).filter(CompanyWorkflow.id == log.company_workflow_id).first()
            if not wf:
                continue
            task = self.db.query(WorkflowTask).filter(WorkflowTask.id == log.task_id).first()
            company = self.db.query(CompanyInfo).filter(CompanyInfo.id == wf.company_id).first()
            # Lấy files đính kèm của task này (theo company + task)
            files = self.db.query(CompanyTaskFile).filter(
                CompanyTaskFile.company_id == wf.company_id,
                CompanyTaskFile.task_id == log.task_id,
            ).order_by(CompanyTaskFile.created_at.desc()).all()

            result.append({
                "log_id": log.id,
                "company_id": wf.company_id,
                "company_name": company.ten_cong_ty if company else f"Company #{wf.company_id}",
                "workflow_id": wf.id,
                "template_name": self._get_template_name(wf.template_id),
                "year": wf.year,
                "quarter": wf.quarter,
                "task_id": log.task_id,
                "task_title": task.title if task else f"Task #{log.task_id}",
                "task_frequency": task.frequency if task else "monthly",
                "period": log.period,
                "status": log.status,
                "note": log.note,
                "done_by": log.done_by,
                "done_at": log.done_at.isoformat() if log.done_at else None,
                "updated_at": log.updated_at.isoformat() if log.updated_at else None,
                "files": [
                    {
                        "id": f.id,
                        "name": f.name,
                        "type": f.type,
                        "url": f.url or f.path,
                    }
                    for f in files
                ],
            })
        return result

    def _get_template_name(self, template_id: int) -> str:
        tmpl = self.db.query(WorkflowTemplate).filter(WorkflowTemplate.id == template_id).first()
        return tmpl.name if tmpl else f"Template #{template_id}"

    def get_company_warnings(self, company_id: int) -> list:
        """Danh sách task gần deadline hoặc quá hạn chưa hoàn thành."""
        workflows = self.db.query(CompanyWorkflow).filter(
            CompanyWorkflow.company_id == company_id
        ).all()
        warnings = []
        for wf in workflows:
            logs = self.db.query(WorkflowTaskLog).filter(
                WorkflowTaskLog.company_workflow_id == wf.id,
                WorkflowTaskLog.status.notin_(["approved", "waiting_review"]),
            ).all()
            for log in logs:
                task = self.db.query(WorkflowTask).filter(WorkflowTask.id == log.task_id).first()
                if not task:
                    continue
                if _is_near_deadline(log.period, task.frequency):
                    deadline = _deadline_for_period(log.period)
                    warnings.append({
                        "workflow_id": wf.id,
                        "task_id": log.task_id,
                        "task_title": task.title,
                        "period": log.period,
                        "status": log.status,
                        "deadline": deadline.isoformat(),
                        "days_left": (deadline - date.today()).days,
                    })
        return warnings

    def get_reviewer_ids(self) -> list[int]:
        """Trả về list user_id của tất cả REVIEWER đang active."""
        reviewers = self.db.query(AdminUser).filter(
            AdminUser.role == "REVIEWER", AdminUser.is_active == True
        ).all()
        return [r.id for r in reviewers]

    def get_workflow_employee_user_id(self, workflow_id: int, task_id: Optional[int] = None, period: str = "") -> Optional[int]:
        """Trả về user_id của nhân viên phụ trách workflow.
        Ưu tiên: submitted_by_user_id trên log → assigned_employee_id → None."""
        # Thử lấy từ log submitted_by_user_id
        if task_id:
            log = self.db.query(WorkflowTaskLog).filter(
                WorkflowTaskLog.company_workflow_id == workflow_id,
                WorkflowTaskLog.task_id == task_id,
                WorkflowTaskLog.period == period,
            ).first()
            if log and log.submitted_by_user_id:
                return log.submitted_by_user_id

        workflow = self.db.query(CompanyWorkflow).filter(CompanyWorkflow.id == workflow_id).first()
        if not workflow or not workflow.assigned_employee_id:
            return None
        user = self.db.query(AdminUser).filter(
            AdminUser.employee_id == workflow.assigned_employee_id
        ).first()
        return user.id if user else None

    def list_notifications(self, user_id: int) -> list:
        notifs = self.db.query(Notification).filter(
            Notification.user_id == user_id
        ).order_by(Notification.created_at.desc()).limit(50).all()
        return [
            {
                "id": n.id,
                "type": n.type,
                "title": n.title,
                "body": n.body,
                "link": n.link,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in notifs
        ]

    def mark_notification_read(self, notification_id: int) -> dict:
        n = self.db.query(Notification).filter(Notification.id == notification_id).first()
        if not n:
            raise HTTPException(status_code=404, detail="Không tìm thấy thông báo")
        n.is_read = True
        self.db.commit()
        return {"id": notification_id, "is_read": True}

    def mark_all_notifications_read(self, user_id: int) -> dict:
        self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False,
        ).update({"is_read": True})
        self.db.commit()
        return {"message": "Đã đánh dấu tất cả đã đọc"}

    def delete_company_workflow(self, company_id: int, workflow_id: int) -> dict:
        workflow = self.db.query(CompanyWorkflow).filter(
            CompanyWorkflow.id == workflow_id,
            CompanyWorkflow.company_id == company_id,
        ).first()
        if not workflow:
            raise HTTPException(status_code=404, detail=f"Workflow id={workflow_id} không tồn tại")
        self.db.delete(workflow)
        self.db.commit()
        return {"message": f"Đã xóa workflow Q{workflow.quarter}/{workflow.year}"}

    # =========================================================================
    # Internal helpers
    # =========================================================================

    def _sync_workflow_status(self, workflow: CompanyWorkflow):
        logs = self.db.query(WorkflowTaskLog).filter(
            WorkflowTaskLog.company_workflow_id == workflow.id
        ).all()
        if not logs:
            return
        done_statuses = {"approved", "waiting_review"}
        if all(l.status in done_statuses for l in logs):
            workflow.status = "completed"
        elif any(l.status not in ("pending",) for l in logs):
            workflow.status = "in_progress"
        else:
            workflow.status = "pending"
        workflow.updated_at = datetime.now()

    def _build_workflow_list_item(self, workflow: CompanyWorkflow) -> dict:
        template = self.db.query(WorkflowTemplate).filter(
            WorkflowTemplate.id == workflow.template_id
        ).first()

        logs = self.db.query(WorkflowTaskLog).filter(
            WorkflowTaskLog.company_workflow_id == workflow.id
        ).all()

        total = len(logs)
        done = sum(1 for l in logs if l.status in ("done", "skipped"))
        pct = round(done / total * 100, 1) if total else 0.0

        return {
            "id": workflow.id,
            "company_id": workflow.company_id,
            "template_id": workflow.template_id,
            "template_name": template.name if template else "—",
            "year": workflow.year,
            "quarter": workflow.quarter,
            "status": workflow.status,
            "assigned_employee_id": workflow.assigned_employee_id,
            "total_tasks": total,
            "done_tasks": done,
            "progress_pct": pct,
            "created_at": workflow.created_at,
            "updated_at": workflow.updated_at,
        }

    def _log_to_dict(self, log: WorkflowTaskLog, frequency: str = "monthly") -> dict:
        return {
            "id": log.id,
            "task_id": log.task_id,
            "period": log.period,
            "status": log.status,
            "note": log.note,
            "done_by": log.done_by,
            "done_at": log.done_at,
            "review_status": log.review_status,
            "reviewed_by": log.reviewed_by,
            "reviewed_at": log.reviewed_at,
            "review_note": log.review_note,
            "updated_at": log.updated_at,
            "near_deadline": _is_near_deadline(log.period, frequency) and log.status not in ("approved",),
        }

    def _ensure_period_logs(self, workflow: CompanyWorkflow, template):
        """Tạo logs còn thiếu cho các task chưa có log theo kỳ (migration cũ hoặc task mới thêm)."""
        if not template:
            return
        existing = {
            (l.task_id, l.period)
            for l in self.db.query(WorkflowTaskLog).filter(
                WorkflowTaskLog.company_workflow_id == workflow.id
            ).all()
        }
        created = False
        now = datetime.now()
        for phase in template.phases:
            for task in phase.tasks:
                for period in _periods_for_task(task.frequency, workflow.year, workflow.quarter):
                    if (task.id, period) not in existing:
                        self.db.add(WorkflowTaskLog(
                            company_workflow_id=workflow.id,
                            task_id=task.id,
                            period=period,
                            status="pending",
                            created_at=now,
                            updated_at=now,
                        ))
                        created = True
        if created:
            self.db.commit()

    def _build_workflow_detail(self, workflow: CompanyWorkflow) -> dict:
        template = self.db.query(WorkflowTemplate).filter(
            WorkflowTemplate.id == workflow.template_id
        ).first()

        # Đảm bảo tất cả task đều có logs theo kỳ (fix migration cũ)
        self._ensure_period_logs(workflow, template)

        # Load tất cả logs nhóm theo task_id
        from collections import defaultdict
        logs_by_task: dict[int, list] = defaultdict(list)
        for log in self.db.query(WorkflowTaskLog).filter(
            WorkflowTaskLog.company_workflow_id == workflow.id
        ).order_by(WorkflowTaskLog.period).all():
            # Bỏ qua các log cũ không có period (trước migration)
            if log.period:
                logs_by_task[log.task_id].append(log)

        done_statuses = {"approved", "waiting_review"}
        phases_out = []
        total_logs = 0
        done_logs = 0

        if template:
            for phase in template.phases:
                tasks_out = []
                for task in phase.tasks:
                    task_logs = logs_by_task.get(task.id, [])
                    near_deadline = any(
                        _is_near_deadline(l.period, task.frequency) and l.status == "pending"
                        for l in task_logs
                    )
                    tasks_out.append({
                        "task_id": task.id,
                        "title": task.title,
                        "description": task.description,
                        "is_required": task.is_required,
                        "order_index": task.order_index,
                        "frequency": task.frequency,
                        "automation_type": task.automation_type,
                        "automation_note": task.automation_note,
                        "near_deadline": near_deadline,
                        "logs": [self._log_to_dict(l, task.frequency) for l in task_logs],
                    })
                    total_logs += len(task_logs)
                    done_logs += sum(1 for l in task_logs if l.status in done_statuses)

                phase_total = sum(len(t["logs"]) for t in tasks_out)
                phase_done = sum(1 for t in tasks_out for l in t["logs"] if l["status"] in done_statuses)
                phases_out.append({
                    "phase_id": phase.id,
                    "name": phase.name,
                    "order_index": phase.order_index,
                    "tasks": tasks_out,
                    "total": phase_total,
                    "done": phase_done,
                })

        pct = round(done_logs / total_logs * 100, 1) if total_logs else 0.0

        return {
            "id": workflow.id,
            "company_id": workflow.company_id,
            "template_id": workflow.template_id,
            "template_name": template.name if template else "—",
            "year": workflow.year,
            "quarter": workflow.quarter,
            "status": workflow.status,
            "assigned_employee_id": workflow.assigned_employee_id,
            "note": workflow.note,
            "phases": phases_out,
            "total_tasks": total_logs,
            "done_tasks": done_logs,
            "progress_pct": pct,
            "created_at": workflow.created_at,
            "updated_at": workflow.updated_at,
        }
