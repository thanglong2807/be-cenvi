# app/models/workflow_model.py

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()


class WorkflowTemplate(Base):
    """Template quy trình chuẩn — Admin tạo và quản lý."""
    __tablename__ = "workflow_templates"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    name        = Column(String(200), nullable=False)           # VD: "Quy trình kế toán thuế TNHH"
    description = Column(Text, nullable=True)
    is_active   = Column(Boolean, default=True, nullable=False)
    created_at  = Column(DateTime, default=lambda: datetime.now())
    updated_at  = Column(DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())

    phases      = relationship("WorkflowPhase", back_populates="template",
                               order_by="WorkflowPhase.order_index",
                               cascade="all, delete-orphan")


class WorkflowPhase(Base):
    """Giai đoạn trong template — VD: 'Thu thập chứng từ', 'Kê khai', 'Nộp thuế'."""
    __tablename__ = "workflow_phases"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(Integer, ForeignKey("workflow_templates.id", ondelete="CASCADE"), nullable=False, index=True)
    name        = Column(String(200), nullable=False)
    order_index = Column(Integer, nullable=False, default=0)
    created_at  = Column(DateTime, default=lambda: datetime.now())

    template    = relationship("WorkflowTemplate", back_populates="phases")
    tasks       = relationship("WorkflowTask", back_populates="phase",
                               order_by="WorkflowTask.order_index",
                               cascade="all, delete-orphan")


class WorkflowTask(Base):
    """Checklist item trong một giai đoạn."""
    __tablename__ = "workflow_tasks"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    phase_id    = Column(Integer, ForeignKey("workflow_phases.id", ondelete="CASCADE"), nullable=False, index=True)
    title           = Column(String(300), nullable=False)
    description     = Column(Text, nullable=True)
    is_required     = Column(Boolean, default=True, nullable=False)
    order_index     = Column(Integer, nullable=False, default=0)
    frequency         = Column(String(20), nullable=False, default="monthly")       # monthly / quarterly / yearly
    automation_type   = Column(String(20), nullable=False, default="manual")      # manual / script
    automation_note   = Column(Text, nullable=True)                               # mô tả việc cần tự động hoá
    automation_status = Column(String(20), nullable=False, default="pending_script")  # pending_script / ready
    created_at  = Column(DateTime, default=lambda: datetime.now())

    phase       = relationship("WorkflowPhase", back_populates="tasks")


class CompanyWorkflow(Base):
    """
    Instance quy trình của 1 công ty cho 1 quý cụ thể.
    Mỗi công ty mỗi quý chỉ có 1 workflow instance từ 1 template.
    """
    __tablename__ = "company_workflows"
    __table_args__ = (
        UniqueConstraint("company_id", "template_id", "year", "quarter",
                         name="uq_company_workflow_quarter"),
    )

    id                   = Column(Integer, primary_key=True, autoincrement=True)
    # company_id trỏ về COMPANY_INFO.id — dùng index, không dùng FK cross-Base
    company_id           = Column(Integer, nullable=False, index=True)
    template_id          = Column(Integer, ForeignKey("workflow_templates.id", ondelete="RESTRICT"),
                                  nullable=False, index=True)
    year                 = Column(Integer, nullable=False)
    quarter              = Column(Integer, nullable=False)          # 1, 2, 3, 4
    status               = Column(String(20), nullable=False,
                                  default="pending")               # pending / in_progress / completed
    # assigned_employee_id trỏ về employees.id — dùng index, không dùng FK cross-Base
    assigned_employee_id = Column(Integer, nullable=True, index=True)
    note                 = Column(Text, nullable=True)
    created_at           = Column(DateTime, default=lambda: datetime.now())
    updated_at           = Column(DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())

    task_logs            = relationship("WorkflowTaskLog", back_populates="company_workflow",
                                        cascade="all, delete-orphan")


class CompanyTaskFile(Base):
    """File hoặc link đính kèm theo task của một công ty — tồn tại lâu dài."""
    __tablename__ = "company_task_files"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    company_id  = Column(Integer, nullable=False, index=True)
    task_id     = Column(Integer, ForeignKey("workflow_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    name        = Column(String(300), nullable=False)          # tên hiển thị
    type        = Column(String(10), nullable=False)           # "file" | "link"
    path        = Column(String(500), nullable=True)           # đường dẫn file tĩnh (nếu type=file)
    url         = Column(String(1000), nullable=True)          # URL (nếu type=link)
    uploaded_by = Column(String(200), nullable=True)
    created_at  = Column(DateTime, default=lambda: datetime.now())


class WorkflowTaskLog(Base):
    """Trạng thái từng task theo từng kỳ (tháng/quý/năm)."""
    __tablename__ = "workflow_task_logs"

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    company_workflow_id = Column(Integer, ForeignKey("company_workflows.id", ondelete="CASCADE"),
                                 nullable=False, index=True)
    task_id             = Column(Integer, ForeignKey("workflow_tasks.id", ondelete="CASCADE"),
                                 nullable=False, index=True)
    period              = Column(String(20), nullable=False, default="")  # "2026-04" | "2026-Q2" | "2026"
    # pending / in_progress / paused / waiting_review / approved / rejected
    status              = Column(String(20), nullable=False, default="pending")
    note                = Column(Text, nullable=True)
    done_by             = Column(String(200), nullable=True)
    done_at             = Column(DateTime, nullable=True)
    # Review fields
    review_status       = Column(String(20), nullable=True)   # approved / rejected
    reviewed_by         = Column(String(200), nullable=True)
    reviewed_at         = Column(DateTime, nullable=True)
    review_note         = Column(Text, nullable=True)         # lý do từ chối
    submitted_by_user_id = Column(Integer, nullable=True)    # user_id của người submit
    created_at          = Column(DateTime, default=lambda: datetime.now())
    updated_at          = Column(DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())

    company_workflow    = relationship("CompanyWorkflow", back_populates="task_logs")
