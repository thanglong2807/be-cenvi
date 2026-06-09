# app/schemas/workflow_schema.py

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ---------------------------------------------------------------------------
# Task schemas
# ---------------------------------------------------------------------------

FREQUENCY_VALUES = {"monthly", "quarterly", "yearly"}


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    is_required: bool = True
    order_index: int = 0
    frequency: str = "monthly"
    automation_type: str = "manual"
    automation_note: Optional[str] = None
    automation_status: str = "pending_script"


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_required: Optional[bool] = None
    order_index: Optional[int] = None
    frequency: Optional[str] = None
    automation_type: Optional[str] = None
    automation_note: Optional[str] = None
    automation_status: Optional[str] = None


class TaskResponse(BaseModel):
    id: int
    phase_id: int
    title: str
    description: Optional[str] = None
    is_required: bool
    order_index: int
    frequency: str = "monthly"
    automation_type: str = "manual"
    automation_note: Optional[str] = None
    automation_status: str = "pending_script"
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Phase schemas
# ---------------------------------------------------------------------------

class PhaseCreate(BaseModel):
    name: str
    order_index: int = 0
    tasks: Optional[List[TaskCreate]] = []


class PhaseUpdate(BaseModel):
    name: Optional[str] = None
    order_index: Optional[int] = None


class PhaseResponse(BaseModel):
    id: int
    template_id: int
    name: str
    order_index: int
    tasks: List[TaskResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Template schemas
# ---------------------------------------------------------------------------

class TemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True
    phases: Optional[List[PhaseCreate]] = []


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class TemplateListItem(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_active: bool
    phase_count: int = 0
    task_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TemplateDetail(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_active: bool
    phases: List[PhaseResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Company Workflow schemas
# ---------------------------------------------------------------------------

class CompanyWorkflowCreate(BaseModel):
    template_id: int
    year: int
    quarter: int                            # 1-4
    assigned_employee_id: Optional[int] = None
    note: Optional[str] = None


class CompanyWorkflowUpdate(BaseModel):
    status: Optional[str] = None           # pending / in_progress / completed
    assigned_employee_id: Optional[int] = None
    note: Optional[str] = None


class TaskLogUpdate(BaseModel):
    # pending / in_progress / paused / waiting_review
    status: str
    note: Optional[str] = None
    done_by: Optional[str] = None


class TaskLogReview(BaseModel):
    """Reviewer duyệt hoặc từ chối task."""
    action: str          # approved / rejected
    review_note: Optional[str] = None
    reviewed_by: Optional[str] = None


class TaskLogResponse(BaseModel):
    id: int
    task_id: int
    period: str = ""
    status: str
    note: Optional[str] = None
    done_by: Optional[str] = None
    done_at: Optional[datetime] = None
    review_status: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_note: Optional[str] = None
    updated_at: datetime
    near_deadline: bool = False

    class Config:
        from_attributes = True


class TaskWithLog(BaseModel):
    """Task kèm danh sách logs theo từng kỳ."""
    task_id: int
    title: str
    description: Optional[str] = None
    is_required: bool
    order_index: int
    frequency: str = "monthly"
    automation_type: str = "manual"
    automation_note: Optional[str] = None
    logs: List[TaskLogResponse] = []  # nhiều log (1 per period)


class PhaseWithProgress(BaseModel):
    phase_id: int
    name: str
    order_index: int
    tasks: List[TaskWithLog] = []
    total: int = 0      # tổng số log kỳ
    done: int = 0       # số log approved hoặc waiting_review


class CompanyWorkflowDetail(BaseModel):
    id: int
    company_id: int
    template_id: int
    template_name: str
    year: int
    quarter: int
    status: str
    assigned_employee_id: Optional[int] = None
    note: Optional[str] = None
    phases: List[PhaseWithProgress] = []
    total_tasks: int = 0
    done_tasks: int = 0
    progress_pct: float = 0.0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CompanyWorkflowListItem(BaseModel):
    id: int
    company_id: int
    template_id: int
    template_name: str
    year: int
    quarter: int
    status: str
    assigned_employee_id: Optional[int] = None
    total_tasks: int = 0
    done_tasks: int = 0
    progress_pct: float = 0.0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
