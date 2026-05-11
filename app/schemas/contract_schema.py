from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


# =========================
# Contract Type Schemas
# =========================
class ContractTypeCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ContractTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ContractTypeResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =========================
# Template Field Schemas
# =========================
class TemplateFieldCreate(BaseModel):
    field_name: str
    field_label: str
    field_type: str  # text, textarea, date, number, dropdown, checkbox, currency
    field_options: Optional[str] = None  # JSON string for dropdown options
    source: str  # company_info, manual, custom
    company_info_field: Optional[str] = None  # Maps to CompanyInfo column
    is_required: bool = False
    display_order: int = 0


class TemplateFieldUpdate(BaseModel):
    field_name: Optional[str] = None
    field_label: Optional[str] = None
    field_type: Optional[str] = None
    field_options: Optional[str] = None
    source: Optional[str] = None
    company_info_field: Optional[str] = None
    is_required: Optional[bool] = None
    display_order: Optional[int] = None


class TemplateFieldResponse(BaseModel):
    id: int
    template_id: int
    field_name: str
    field_label: str
    field_type: str
    field_options: Optional[str] = None
    source: str
    company_info_field: Optional[str] = None
    is_required: bool
    display_order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReorderFieldsRequest(BaseModel):
    field_ids: List[int]  # Ordered list of field IDs


# =========================
# Contract Template Schemas
# =========================
class ContractTemplateCreate(BaseModel):
    name: str
    contract_type_id: int
    content: str  # Template content with {{variables}}
    fields: List[TemplateFieldCreate] = []


class ContractTemplateUpdate(BaseModel):
    name: Optional[str] = None
    contract_type_id: Optional[int] = None
    content: Optional[str] = None
    fields: Optional[List[TemplateFieldCreate]] = None


class ContractTemplateListItem(BaseModel):
    id: int
    name: str
    contract_type_id: int
    version: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ContractTemplateResponse(BaseModel):
    id: int
    name: str
    contract_type_id: int
    content: str
    version: int
    is_active: bool
    created_by: str
    fields: List[TemplateFieldResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =========================
# Contract Schemas
# =========================
class ContractCreate(BaseModel):
    title: str
    template_id: int
    partner_company_id: Optional[int] = None
    partner_name: str
    partner_address: Optional[str] = None
    partner_tax_id: Optional[str] = None
    partner_representative: Optional[str] = None
    partner_position: Optional[str] = None
    field_values: Dict[str, Any]  # {field_name: value}


class ContractUpdate(BaseModel):
    title: Optional[str] = None
    field_values: Optional[Dict[str, Any]] = None
    status: Optional[str] = None  # draft, final


class ContractResponse(BaseModel):
    id: int
    title: str
    template_id: int
    template_snapshot: str  # JSON string
    partner_company_id: Optional[int] = None
    partner_name: str
    partner_address: Optional[str] = None
    partner_tax_id: Optional[str] = None
    partner_representative: Optional[str] = None
    partner_position: Optional[str] = None
    field_values: str  # JSON string
    status: str
    pdf_path: Optional[str] = None
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContractListItem(BaseModel):
    id: int
    title: str
    template_id: int
    partner_name: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# =========================
# Contract Partner Schemas
# =========================
class ContractPartnerCreate(BaseModel):
    name: str
    address: Optional[str] = None
    tax_id: Optional[str] = None
    representative: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None


class ContractPartnerUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = None
    representative: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None


class ContractPartnerResponse(BaseModel):
    id: int
    name: str
    address: Optional[str] = None
    tax_id: Optional[str] = None
    representative: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =========================
# Company Info Fields Mapping
# =========================
class CompanyInfoFieldItem(BaseModel):
    field_name: str
    field_label: str
    variable_name: str  # e.g. {{ten_cong_ty}}
