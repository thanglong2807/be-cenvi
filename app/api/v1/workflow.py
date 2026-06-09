# app/api/v1/workflow.py

from typing import List, Optional

from fastapi import APIRouter, Depends, Header, Request, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.connection_manager import manager as ws_manager
from app.core.security import decode_token
from app.services.workflow_service import WorkflowService
from app.schemas.workflow_schema import (
    TemplateCreate, TemplateUpdate, TemplateListItem, TemplateDetail,
    PhaseCreate, PhaseUpdate, PhaseResponse,
    TaskCreate, TaskUpdate, TaskResponse,
    CompanyWorkflowCreate, CompanyWorkflowUpdate,
    CompanyWorkflowListItem, CompanyWorkflowDetail,
    TaskLogUpdate, TaskLogReview,
)

router = APIRouter(tags=["Workflow"])


# =============================================================================
# WEBSOCKET — realtime broadcast
# =============================================================================

@router.websocket("/ws/workflow-updates")
async def workflow_websocket(websocket: WebSocket):
    """
    Clients connect here to receive realtime workflow events.
    Events emitted: task_updated, task_reviewed
    """
    conn_id = await ws_manager.connect(websocket)
    # Send current connection count as handshake
    try:
        await websocket.send_json({"event": "connected", "data": {"connections": ws_manager.connection_count}})
        while True:
            # Keep connection alive — client can send ping text
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(conn_id)
    except Exception:
        ws_manager.disconnect(conn_id)


def get_service(db: Session = Depends(get_db)) -> WorkflowService:
    return WorkflowService(db)


# =============================================================================
# TEMPLATES (Admin quản lý)
# =============================================================================

@router.get("/workflows/automations")
def list_automation_tasks(service: WorkflowService = Depends(get_service)):
    """Tổng hợp tất cả task có tự động hoá từ mọi template."""
    return service.list_automation_tasks()


@router.get("/workflows/templates", response_model=List[TemplateListItem])
def list_templates(service: WorkflowService = Depends(get_service)):
    """Danh sách tất cả template quy trình."""
    return service.list_templates()


@router.get("/workflows/templates/{template_id}", response_model=TemplateDetail)
def get_template(template_id: int, service: WorkflowService = Depends(get_service)):
    """Chi tiết template kèm phases và tasks."""
    return service.get_template(template_id)


@router.post("/workflows/templates", response_model=TemplateDetail,
             status_code=status.HTTP_201_CREATED)
def create_template(data: TemplateCreate, service: WorkflowService = Depends(get_service)):
    """
    Tạo template mới. Có thể tạo kèm phases và tasks ngay trong 1 request.

    Ví dụ body:
    ```json
    {
      "name": "Quy trình kế toán thuế TNHH",
      "phases": [
        {
          "name": "Thu thập chứng từ",
          "order_index": 1,
          "tasks": [
            {"title": "Tải sao kê ngân hàng", "is_required": true, "order_index": 1},
            {"title": "Tổng hợp hóa đơn mua vào", "is_required": true, "order_index": 2}
          ]
        },
        {
          "name": "Kê khai thuế",
          "order_index": 2,
          "tasks": [
            {"title": "Kê khai GTGT", "is_required": true, "order_index": 1},
            {"title": "Kê khai TNCN tạm tính", "is_required": false, "order_index": 2}
          ]
        }
      ]
    }
    ```
    """
    return service.create_template(data)


@router.put("/workflows/templates/{template_id}", response_model=TemplateDetail)
def update_template(template_id: int, data: TemplateUpdate,
                    service: WorkflowService = Depends(get_service)):
    return service.update_template(template_id, data)


@router.delete("/workflows/templates/{template_id}")
def delete_template(template_id: int, service: WorkflowService = Depends(get_service)):
    return service.delete_template(template_id)


# =============================================================================
# PHASES
# =============================================================================

@router.post("/workflows/templates/{template_id}/phases",
             response_model=PhaseResponse, status_code=status.HTTP_201_CREATED)
def add_phase(template_id: int, data: PhaseCreate,
              service: WorkflowService = Depends(get_service)):
    """Thêm giai đoạn mới vào template."""
    return service.add_phase(template_id, data)


@router.put("/workflows/phases/{phase_id}", response_model=PhaseResponse)
def update_phase(phase_id: int, data: PhaseUpdate,
                 service: WorkflowService = Depends(get_service)):
    return service.update_phase(phase_id, data)


@router.delete("/workflows/phases/{phase_id}")
def delete_phase(phase_id: int, service: WorkflowService = Depends(get_service)):
    return service.delete_phase(phase_id)


# =============================================================================
# TASKS
# =============================================================================

@router.post("/workflows/phases/{phase_id}/tasks",
             response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def add_task(phase_id: int, data: TaskCreate,
             service: WorkflowService = Depends(get_service)):
    """Thêm task vào giai đoạn."""
    return service.add_task(phase_id, data)


@router.put("/workflows/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, data: TaskUpdate,
                service: WorkflowService = Depends(get_service)):
    return service.update_task(task_id, data)


@router.delete("/workflows/tasks/{task_id}")
def delete_task(task_id: int, service: WorkflowService = Depends(get_service)):
    return service.delete_task(task_id)


# =============================================================================
# COMPANY WORKFLOWS (Nhân viên thực hiện)
# =============================================================================

@router.get("/company-info/{company_id}/workflows",
            response_model=List[CompanyWorkflowListItem])
def list_company_workflows(company_id: int,
                           service: WorkflowService = Depends(get_service)):
    """Danh sách tất cả quy trình của 1 công ty (theo quý)."""
    return service.list_company_workflows(company_id)


@router.post("/company-info/{company_id}/workflows",
             response_model=CompanyWorkflowDetail, status_code=status.HTTP_201_CREATED)
def start_company_workflow(company_id: int, data: CompanyWorkflowCreate,
                           service: WorkflowService = Depends(get_service)):
    """
    Khởi tạo quy trình cho công ty theo quý.
    Tự động tạo task logs (pending) cho tất cả tasks trong template.
    """
    return service.start_company_workflow(company_id, data)


@router.get("/company-info/{company_id}/workflows/{workflow_id}",
            response_model=CompanyWorkflowDetail)
def get_company_workflow(company_id: int, workflow_id: int,
                         service: WorkflowService = Depends(get_service)):
    """Chi tiết quy trình kèm trạng thái từng task."""
    return service.get_company_workflow(company_id, workflow_id)


@router.put("/company-info/{company_id}/workflows/{workflow_id}",
            response_model=CompanyWorkflowDetail)
def update_company_workflow(company_id: int, workflow_id: int,
                            data: CompanyWorkflowUpdate,
                            service: WorkflowService = Depends(get_service)):
    """Cập nhật trạng thái hoặc người phụ trách workflow."""
    return service.update_company_workflow(company_id, workflow_id, data)


@router.delete("/company-info/{company_id}/workflows/{workflow_id}")
def delete_company_workflow(company_id: int, workflow_id: int,
                            service: WorkflowService = Depends(get_service)):
    return service.delete_company_workflow(company_id, workflow_id)


@router.put("/company-info/{company_id}/workflows/{workflow_id}/tasks/{task_id}")
async def update_task_log(company_id: int, workflow_id: int, task_id: int,
                          data: TaskLogUpdate,
                          request: Request,
                          period: Optional[str] = None,
                          service: WorkflowService = Depends(get_service)):
    """
    Nhân viên cập nhật trạng thái 1 task theo kỳ.
    period: "2026-04" | "2026-Q2" | "2026"
    """
    # Lấy user_id của người đang submit từ JWT token
    submitter_user_id: Optional[int] = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        payload = decode_token(auth_header[7:])
        if payload and payload.get("sub"):
            try:
                submitter_user_id = int(payload["sub"])
            except (ValueError, TypeError):
                pass

    result = service.update_task_log(
        company_id, workflow_id, task_id, period or "", data,
        submitter_user_id=submitter_user_id,
    )
    await ws_manager.broadcast("task_updated", {
        "company_id": company_id,
        "workflow_id": workflow_id,
        "task_id": task_id,
        "period": period or "",
        "status": data.status,
    })
    # Nếu submit chờ duyệt → push notification cho reviewer
    if data.status == "waiting_review":
        reviewer_ids = service.get_reviewer_ids()
        for uid in reviewer_ids:
            await ws_manager.broadcast("notification", {"user_id": uid})
    return result


@router.post("/company-info/{company_id}/workflows/{workflow_id}/tasks/{task_id}/review")
async def review_task_log(company_id: int, workflow_id: int, task_id: int,
                          data: TaskLogReview,
                          period: Optional[str] = None,
                          x_reviewer_name: Optional[str] = Header(None),
                          service: WorkflowService = Depends(get_service)):
    """
    Reviewer duyệt hoặc từ chối task.
    action: approved | rejected
    """
    reviewer = x_reviewer_name or data.reviewed_by or "Reviewer"
    result = service.review_task_log(company_id, workflow_id, task_id, period or "", data, reviewer)
    await ws_manager.broadcast("task_reviewed", {
        "company_id": company_id,
        "workflow_id": workflow_id,
        "task_id": task_id,
        "period": period or "",
        "action": data.action,
    })
    # Push notification cho nhân viên phụ trách
    employee_uid = service.get_workflow_employee_user_id(workflow_id, task_id, period or "")
    if employee_uid:
        await ws_manager.broadcast("notification", {"user_id": employee_uid})
    return result


@router.get("/reviewer/waiting-review")
def list_waiting_review(service: WorkflowService = Depends(get_service)):
    """Danh sách tất cả task đang chờ kiểm duyệt (toàn hệ thống)."""
    return service.list_waiting_review()


@router.get("/company-info/{company_id}/warnings")
def get_company_warnings(company_id: int, service: WorkflowService = Depends(get_service)):
    """Lấy danh sách task gần deadline cho 1 công ty."""
    return service.get_company_warnings(company_id)


# =============================================================================
# NOTIFICATIONS
# =============================================================================

@router.get("/notifications")
def list_notifications(user_id: int, service: WorkflowService = Depends(get_service)):
    """Danh sách thông báo của user."""
    return service.list_notifications(user_id)


@router.put("/notifications/{notification_id}/read")
def mark_notification_read(notification_id: int, service: WorkflowService = Depends(get_service)):
    return service.mark_notification_read(notification_id)


@router.put("/notifications/read-all")
def mark_all_notifications_read(user_id: int, service: WorkflowService = Depends(get_service)):
    return service.mark_all_notifications_read(user_id)
