from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session
import json

from app.core.database import get_db
from app.schemas.contract_schema import (
    ContractTypeCreate,
    ContractTypeResponse,
    ContractTypeUpdate,
    ContractTemplateCreate,
    ContractTemplateResponse,
    ContractTemplateUpdate,
    ContractTemplateListItem,
    TemplateFieldCreate,
    TemplateFieldResponse,
    ReorderFieldsRequest,
    ContractCreate,
    ContractUpdate,
    ContractResponse,
    ContractListItem,
    ContractPartnerCreate,
    ContractPartnerUpdate,
    ContractPartnerResponse,
    CompanyInfoFieldItem,
)
from app.services.contract_service import (
    ContractTypeService,
    ContractTemplateService,
    ContractService,
    ContractPartnerService,
    CompanyInfoFieldsService,
)
from app.services.contract_pdf_service import ContractPDFService

router = APIRouter(prefix="/contracts", tags=["Contracts"])


def get_contract_type_service(db: Session = Depends(get_db)) -> ContractTypeService:
    return ContractTypeService(db)


def get_contract_template_service(db: Session = Depends(get_db)) -> ContractTemplateService:
    return ContractTemplateService(db)


def get_contract_service(db: Session = Depends(get_db)) -> ContractService:
    return ContractService(db)


def get_contract_partner_service(db: Session = Depends(get_db)) -> ContractPartnerService:
    return ContractPartnerService(db)


# =========================
# Contract Type Endpoints
# =========================
@router.get("/types", response_model=List[ContractTypeResponse])
def list_contract_types(
    service: ContractTypeService = Depends(get_contract_type_service),
):
    """Get all contract types"""
    return service.get_all()


@router.get("/types/{type_id}", response_model=ContractTypeResponse)
def get_contract_type(
    type_id: int,
    service: ContractTypeService = Depends(get_contract_type_service),
):
    """Get contract type by ID"""
    return service.get_by_id(type_id)


@router.post("/types", response_model=ContractTypeResponse, status_code=status.HTTP_201_CREATED)
def create_contract_type(
    data: ContractTypeCreate,
    service: ContractTypeService = Depends(get_contract_type_service),
):
    """Create new contract type (admin only)"""
    return service.create(data)


@router.put("/types/{type_id}", response_model=ContractTypeResponse)
def update_contract_type(
    type_id: int,
    data: ContractTypeUpdate,
    service: ContractTypeService = Depends(get_contract_type_service),
):
    """Update contract type (admin only)"""
    return service.update(type_id, data)


@router.delete("/types/{type_id}", status_code=status.HTTP_200_OK)
def delete_contract_type(
    type_id: int,
    service: ContractTypeService = Depends(get_contract_type_service),
):
    """Delete contract type (admin only)"""
    return service.soft_delete(type_id)


# =========================
# Contract Template Endpoints
# =========================
@router.get("/templates", response_model=List[ContractTemplateListItem])
def list_contract_templates(
    type_id: Optional[int] = Query(None),
    service: ContractTemplateService = Depends(get_contract_template_service),
):
    """Get all active contract templates"""
    return service.get_all(type_id=type_id)


@router.get("/templates/{template_id}", response_model=ContractTemplateResponse)
def get_contract_template(
    template_id: int,
    service: ContractTemplateService = Depends(get_contract_template_service),
):
    """Get contract template detail with fields"""
    template = service.get_by_id(template_id)
    fields = service.get_fields(template_id)
    # Convert template to dict and add fields
    template_dict = {
        "id": template.id,
        "name": template.name,
        "contract_type_id": template.contract_type_id,
        "content": template.content,
        "version": template.version,
        "is_active": template.is_active,
        "created_by": template.created_by,
        "created_at": template.created_at,
        "updated_at": template.updated_at,
        "fields": fields,
    }
    return ContractTemplateResponse(**template_dict)


@router.post("/templates", response_model=ContractTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_contract_template(
    data: ContractTemplateCreate,
    service: ContractTemplateService = Depends(get_contract_template_service),
):
    """Create new contract template with fields (admin only)"""
    template = service.create(data)
    # Return with fields
    fields = service.get_fields(template.id)
    template_dict = {
        "id": template.id,
        "name": template.name,
        "contract_type_id": template.contract_type_id,
        "content": template.content,
        "version": template.version,
        "is_active": template.is_active,
        "created_by": template.created_by,
        "created_at": template.created_at,
        "updated_at": template.updated_at,
        "fields": fields,
    }
    return ContractTemplateResponse(**template_dict)


@router.put("/templates/{template_id}", response_model=ContractTemplateResponse)
def update_contract_template(
    template_id: int,
    data: ContractTemplateUpdate,
    service: ContractTemplateService = Depends(get_contract_template_service),
):
    """Update contract template → creates new version (admin only)"""
    template = service.update(template_id, data)
    fields = service.get_fields(template.id)
    template_dict = {
        "id": template.id,
        "name": template.name,
        "contract_type_id": template.contract_type_id,
        "content": template.content,
        "version": template.version,
        "is_active": template.is_active,
        "created_by": template.created_by,
        "created_at": template.created_at,
        "updated_at": template.updated_at,
        "fields": fields,
    }
    return ContractTemplateResponse(**template_dict)


@router.delete("/templates/{template_id}", status_code=status.HTTP_200_OK)
def delete_contract_template(
    template_id: int,
    service: ContractTemplateService = Depends(get_contract_template_service),
):
    """Delete contract template (admin only)"""
    return service.soft_delete(template_id)


# =========================
# Template Field Endpoints
# =========================
@router.get("/templates/{template_id}/fields", response_model=List[TemplateFieldResponse])
def get_template_fields(
    template_id: int,
    service: ContractTemplateService = Depends(get_contract_template_service),
):
    """Get all fields for a template"""
    return service.get_fields(template_id)


@router.post("/templates/{template_id}/fields", response_model=TemplateFieldResponse, status_code=status.HTTP_201_CREATED)
def add_template_field(
    template_id: int,
    field: TemplateFieldCreate,
    service: ContractTemplateService = Depends(get_contract_template_service),
):
    """Add new field to template (admin only)"""
    return service.add_field(template_id, field)


@router.put("/templates/{template_id}/fields/{field_id}", response_model=TemplateFieldResponse)
def update_template_field(
    template_id: int,
    field_id: int,
    field: TemplateFieldCreate,
    service: ContractTemplateService = Depends(get_contract_template_service),
):
    """Update template field (admin only)"""
    return service.update_field(field_id, field)


@router.delete("/templates/{template_id}/fields/{field_id}", status_code=status.HTTP_200_OK)
def delete_template_field(
    template_id: int,
    field_id: int,
    service: ContractTemplateService = Depends(get_contract_template_service),
):
    """Delete field from template (admin only)"""
    return service.delete_field(field_id)


@router.put("/templates/{template_id}/fields/reorder", status_code=status.HTTP_200_OK)
def reorder_template_fields(
    template_id: int,
    request: ReorderFieldsRequest,
    service: ContractTemplateService = Depends(get_contract_template_service),
):
    """Reorder fields in template (admin only)"""
    return service.reorder_fields(template_id, request.field_ids)


# =========================
# Company Info Fields Endpoint
# =========================
@router.get("/company-info-fields", response_model=List[CompanyInfoFieldItem])
def get_company_info_fields():
    """Get available CompanyInfo fields for template variables"""
    return CompanyInfoFieldsService.get_available_fields()


# =========================
# Contract Endpoints
# =========================
@router.get("", response_model=List[ContractListItem])
def list_contracts(
    keyword: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: ContractService = Depends(get_contract_service),
):
    """Get all contracts with optional search"""
    return service.get_all(skip=skip, limit=limit, keyword=keyword)


@router.get("/{contract_id}", response_model=ContractResponse)
def get_contract(
    contract_id: int,
    service: ContractService = Depends(get_contract_service),
):
    """Get contract detail"""
    return service.get_by_id(contract_id)


@router.post("", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
def create_contract(
    data: ContractCreate,
    service: ContractService = Depends(get_contract_service),
):
    """Create new contract from template"""
    return service.create(data)


@router.put("/{contract_id}", response_model=ContractResponse)
def update_contract(
    contract_id: int,
    data: ContractUpdate,
    service: ContractService = Depends(get_contract_service),
):
    """Update contract (only draft contracts)"""
    return service.update(contract_id, data)


@router.delete("/{contract_id}", status_code=status.HTTP_200_OK)
def delete_contract(
    contract_id: int,
    service: ContractService = Depends(get_contract_service),
):
    """Delete contract"""
    return service.delete(contract_id)


# =========================
# Contract PDF Endpoints
# =========================
@router.get("/{contract_id}/pdf")
def download_contract_pdf(
    contract_id: int,
    db: Session = Depends(get_db),
):
    """Download contract as PDF"""
    pdf_service = ContractPDFService()
    try:
        pdf_path = pdf_service.generate_pdf(contract_id, db)
        return FileResponse(
            path=pdf_path,
            filename=f"contract_{contract_id}.pdf",
            media_type="application/pdf",
        )
    except Exception as e:
        return {"error": str(e)}


@router.get("/{contract_id}/preview")
def preview_contract(
    contract_id: int,
    db: Session = Depends(get_db),
):
    """Preview contract as HTML"""
    from app.models.contract_model import Contract

    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        return {"error": "Contract not found"}

    template_snapshot = json.loads(contract.template_snapshot)
    field_values = json.loads(contract.field_values)

    html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>{contract.title}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 40px auto;
                line-height: 1.6;
                color: #333;
            }}
            .header {{
                background-color: #f3f4f6;
                padding: 20px;
                margin-bottom: 20px;
                border-radius: 4px;
            }}
            .content {{
                white-space: pre-wrap;
                background-color: #fafafa;
                padding: 20px;
                border: 1px solid #e5e7eb;
                border-radius: 4px;
            }}
            .info {{
                margin: 10px 0;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{contract.title}</h1>
            <div class="info"><strong>Mã:</strong> HDTC-{contract_id}</div>
            <div class="info"><strong>Trạng Thái:</strong> {contract.status}</div>
            <div class="info"><strong>Bên B (Đối Tác):</strong> {contract.partner_name}</div>
        </div>
        <div class="content">
{template_snapshot.get('content', '')}
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


# =========================
# Contract Partner Endpoints
# =========================
@router.get("/partners", response_model=List[ContractPartnerResponse])
def list_contract_partners(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: ContractPartnerService = Depends(get_contract_partner_service),
):
    """Get all saved contract partners"""
    return service.get_all(skip=skip, limit=limit)


@router.get("/partners/{partner_id}", response_model=ContractPartnerResponse)
def get_contract_partner(
    partner_id: int,
    service: ContractPartnerService = Depends(get_contract_partner_service),
):
    """Get partner detail"""
    return service.get_by_id(partner_id)


@router.post("/partners", response_model=ContractPartnerResponse, status_code=status.HTTP_201_CREATED)
def create_contract_partner(
    data: ContractPartnerCreate,
    service: ContractPartnerService = Depends(get_contract_partner_service),
):
    """Save new contract partner for reuse"""
    return service.create(data)


@router.put("/partners/{partner_id}", response_model=ContractPartnerResponse)
def update_contract_partner(
    partner_id: int,
    data: ContractPartnerUpdate,
    service: ContractPartnerService = Depends(get_contract_partner_service),
):
    """Update contract partner"""
    return service.update(partner_id, data)


@router.delete("/partners/{partner_id}", status_code=status.HTTP_200_OK)
def delete_contract_partner(
    partner_id: int,
    service: ContractPartnerService = Depends(get_contract_partner_service),
):
    """Delete contract partner"""
    return service.delete(partner_id)
