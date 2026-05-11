import json
from typing import List, Optional
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.contract_model import (
    ContractType,
    ContractTemplate,
    ContractTemplateField,
    Contract,
    ContractPartner,
)
from app.schemas.contract_schema import (
    ContractTypeCreate,
    ContractTypeUpdate,
    ContractTemplateCreate,
    ContractTemplateUpdate,
    ContractCreate,
    ContractUpdate,
    ContractPartnerCreate,
    ContractPartnerUpdate,
    TemplateFieldCreate,
    CompanyInfoFieldItem,
)


# =========================
# Contract Type Service
# =========================
class ContractTypeService:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self):
        return self.db.query(ContractType).filter(ContractType.is_active == True).all()

    def get_by_id(self, type_id: int):
        contract_type = self.db.query(ContractType).filter(ContractType.id == type_id).first()
        if not contract_type:
            raise HTTPException(status_code=404, detail="Contract type not found")
        return contract_type

    def create(self, data: ContractTypeCreate):
        db_type = ContractType(**data.model_dump())
        self.db.add(db_type)
        self.db.commit()
        self.db.refresh(db_type)
        return db_type

    def update(self, type_id: int, data: ContractTypeUpdate):
        contract_type = self.get_by_id(type_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(contract_type, key, value)
        self.db.commit()
        self.db.refresh(contract_type)
        return contract_type

    def soft_delete(self, type_id: int):
        contract_type = self.get_by_id(type_id)
        contract_type.is_active = False
        self.db.commit()
        return {"message": "Contract type deleted"}


# =========================
# Contract Template Service
# =========================
class ContractTemplateService:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, type_id: Optional[int] = None):
        query = self.db.query(ContractTemplate).filter(ContractTemplate.is_active == True)
        if type_id:
            query = query.filter(ContractTemplate.contract_type_id == type_id)
        # Return only latest version for each unique (name, contract_type_id)
        return query.all()

    def get_by_id(self, template_id: int):
        template = self.db.query(ContractTemplate).filter(ContractTemplate.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Contract template not found")
        return template

    def create(self, data: ContractTemplateCreate):
        db_template = ContractTemplate(
            name=data.name,
            contract_type_id=data.contract_type_id,
            content=data.content,
            version=1,
            created_by="system",
        )
        self.db.add(db_template)
        self.db.flush()

        # Create fields
        if data.fields:
            for field in data.fields:
                db_field = ContractTemplateField(
                    template_id=db_template.id,
                    **field.model_dump(),
                )
                self.db.add(db_field)

        self.db.commit()
        self.db.refresh(db_template)
        return db_template

    def update(self, template_id: int, data: ContractTemplateUpdate):
        # Get old template
        old_template = self.get_by_id(template_id)

        # Create new version
        new_version = old_template.version + 1
        db_template = ContractTemplate(
            name=data.name or old_template.name,
            contract_type_id=data.contract_type_id or old_template.contract_type_id,
            content=data.content or old_template.content,
            version=new_version,
            created_by="system",
        )
        self.db.add(db_template)
        self.db.flush()

        # Copy or update fields
        if data.fields:
            for field in data.fields:
                db_field = ContractTemplateField(
                    template_id=db_template.id,
                    **field.model_dump(),
                )
                self.db.add(db_field)
        else:
            # Copy old fields
            old_fields = (
                self.db.query(ContractTemplateField)
                .filter(ContractTemplateField.template_id == template_id)
                .all()
            )
            for old_field in old_fields:
                db_field = ContractTemplateField(
                    template_id=db_template.id,
                    field_name=old_field.field_name,
                    field_label=old_field.field_label,
                    field_type=old_field.field_type,
                    field_options=old_field.field_options,
                    source=old_field.source,
                    company_info_field=old_field.company_info_field,
                    is_required=old_field.is_required,
                    display_order=old_field.display_order,
                )
                self.db.add(db_field)

        # Mark old as inactive
        old_template.is_active = False

        self.db.commit()
        self.db.refresh(db_template)
        return db_template

    def soft_delete(self, template_id: int):
        template = self.get_by_id(template_id)
        template.is_active = False
        self.db.commit()
        return {"message": "Contract template deleted"}

    def get_fields(self, template_id: int):
        self.get_by_id(template_id)  # Verify template exists
        fields = (
            self.db.query(ContractTemplateField)
            .filter(ContractTemplateField.template_id == template_id)
            .order_by(ContractTemplateField.display_order)
            .all()
        )
        return fields

    def add_field(self, template_id: int, field: TemplateFieldCreate):
        self.get_by_id(template_id)  # Verify template exists
        db_field = ContractTemplateField(
            template_id=template_id,
            **field.model_dump(),
        )
        self.db.add(db_field)
        self.db.commit()
        self.db.refresh(db_field)
        return db_field

    def update_field(self, field_id: int, field: TemplateFieldCreate):
        db_field = self.db.query(ContractTemplateField).filter(ContractTemplateField.id == field_id).first()
        if not db_field:
            raise HTTPException(status_code=404, detail="Field not found")

        update_data = field.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_field, key, value)
        self.db.commit()
        self.db.refresh(db_field)
        return db_field

    def delete_field(self, field_id: int):
        db_field = self.db.query(ContractTemplateField).filter(ContractTemplateField.id == field_id).first()
        if not db_field:
            raise HTTPException(status_code=404, detail="Field not found")
        self.db.delete(db_field)
        self.db.commit()
        return {"message": "Field deleted"}

    def reorder_fields(self, template_id: int, field_ids: List[int]):
        self.get_by_id(template_id)  # Verify template exists
        for order, field_id in enumerate(field_ids):
            field = self.db.query(ContractTemplateField).filter(ContractTemplateField.id == field_id).first()
            if not field:
                raise HTTPException(status_code=404, detail=f"Field {field_id} not found")
            field.display_order = order
        self.db.commit()
        return {"message": "Fields reordered"}


# =========================
# Contract Service
# =========================
class ContractService:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 100, keyword: Optional[str] = None):
        query = self.db.query(Contract)
        if keyword:
            query = query.filter(
                (Contract.title.ilike(f"%{keyword}%")) |
                (Contract.partner_name.ilike(f"%{keyword}%"))
            )
        return query.offset(skip).limit(limit).all()

    def get_by_id(self, contract_id: int):
        contract = self.db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        return contract

    def create(self, data: ContractCreate):
        # Get template and fields
        template = self.db.query(ContractTemplate).filter(ContractTemplate.id == data.template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        fields = (
            self.db.query(ContractTemplateField)
            .filter(ContractTemplateField.template_id == data.template_id)
            .order_by(ContractTemplateField.display_order)
            .all()
        )

        # Create snapshot of template + fields
        template_snapshot = {
            "id": template.id,
            "name": template.name,
            "content": template.content,
            "version": template.version,
            "fields": [
                {
                    "id": f.id,
                    "field_name": f.field_name,
                    "field_label": f.field_label,
                    "field_type": f.field_type,
                    "field_options": f.field_options,
                    "source": f.source,
                    "company_info_field": f.company_info_field,
                    "is_required": f.is_required,
                    "display_order": f.display_order,
                }
                for f in fields
            ],
        }

        db_contract = Contract(
            title=data.title,
            template_id=data.template_id,
            template_snapshot=json.dumps(template_snapshot),
            partner_company_id=data.partner_company_id,
            partner_name=data.partner_name,
            partner_address=data.partner_address,
            partner_tax_id=data.partner_tax_id,
            partner_representative=data.partner_representative,
            partner_position=data.partner_position,
            field_values=json.dumps(data.field_values),
            status="draft",
            created_by="system",
        )
        self.db.add(db_contract)
        self.db.commit()
        self.db.refresh(db_contract)
        return db_contract

    def update(self, contract_id: int, data: ContractUpdate):
        contract = self.get_by_id(contract_id)

        # Only allow updating draft contracts
        if contract.status != "draft":
            raise HTTPException(status_code=400, detail="Only draft contracts can be updated")

        if data.title:
            contract.title = data.title
        if data.field_values:
            contract.field_values = json.dumps(data.field_values)
        if data.status:
            contract.status = data.status

        self.db.commit()
        self.db.refresh(contract)
        return contract

    def delete(self, contract_id: int):
        contract = self.get_by_id(contract_id)
        self.db.delete(contract)
        self.db.commit()
        return {"message": "Contract deleted"}


# =========================
# Contract Partner Service
# =========================
class ContractPartnerService:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 100):
        return self.db.query(ContractPartner).offset(skip).limit(limit).all()

    def get_by_id(self, partner_id: int):
        partner = self.db.query(ContractPartner).filter(ContractPartner.id == partner_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="Partner not found")
        return partner

    def create(self, data: ContractPartnerCreate):
        db_partner = ContractPartner(**data.model_dump())
        self.db.add(db_partner)
        self.db.commit()
        self.db.refresh(db_partner)
        return db_partner

    def update(self, partner_id: int, data: ContractPartnerUpdate):
        partner = self.get_by_id(partner_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(partner, key, value)
        self.db.commit()
        self.db.refresh(partner)
        return partner

    def delete(self, partner_id: int):
        partner = self.get_by_id(partner_id)
        self.db.delete(partner)
        self.db.commit()
        return {"message": "Partner deleted"}


# =========================
# Company Info Fields Helper
# =========================
class CompanyInfoFieldsService:
    @staticmethod
    def get_available_fields() -> List[CompanyInfoFieldItem]:
        """
        Return all available CompanyInfo fields that can be used as contract variables
        """
        return [
            CompanyInfoFieldItem(
                field_name="ten_cong_ty",
                field_label="Tên Công Ty",
                variable_name="{{ten_cong_ty}}",
            ),
            CompanyInfoFieldItem(
                field_name="ten_cong_ty_viet_tat",
                field_label="Tên Viết Tắt",
                variable_name="{{ten_viet_tat}}",
            ),
            CompanyInfoFieldItem(
                field_name="ma_so_thue",
                field_label="Mã Số Thuế",
                variable_name="{{ma_so_thue}}",
            ),
            CompanyInfoFieldItem(
                field_name="ma_kh",
                field_label="Mã Khách Hàng",
                variable_name="{{ma_kh}}",
            ),
            CompanyInfoFieldItem(
                field_name="nguoi_lien_he_va_chuc_vu",
                field_label="Người Liên Hệ & Chức Vụ",
                variable_name="{{nguoi_lien_he}}",
            ),
            CompanyInfoFieldItem(
                field_name="so_dien_thoai",
                field_label="Số Điện Thoại",
                variable_name="{{so_dien_thoai}}",
            ),
            CompanyInfoFieldItem(
                field_name="email_lien_he",
                field_label="Email Liên Hệ",
                variable_name="{{email}}",
            ),
            CompanyInfoFieldItem(
                field_name="hop_dong_ngay_ky",
                field_label="Ngày Ký Hợp Đồng",
                variable_name="{{hop_dong_ngay_ky}}",
            ),
            CompanyInfoFieldItem(
                field_name="hop_dong_thanh_toan",
                field_label="Điều Khoản Thanh Toán",
                variable_name="{{hop_dong_thanh_toan}}",
            ),
        ]
