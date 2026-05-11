from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class ContractType(Base):
    __tablename__ = "CONTRACT_TYPES"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now())
    updated_at = Column(DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())


class ContractTemplate(Base):
    __tablename__ = "CONTRACT_TEMPLATES"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    contract_type_id = Column(Integer, ForeignKey("CONTRACT_TYPES.id"), nullable=False)
    content = Column(LONGTEXT, nullable=False)  # Template content with {{variables}}
    version = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now())
    updated_at = Column(DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())


class ContractTemplateField(Base):
    __tablename__ = "CONTRACT_TEMPLATE_FIELDS"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    template_id = Column(Integer, ForeignKey("CONTRACT_TEMPLATES.id"), nullable=False)
    field_name = Column(String(100), nullable=False)  # Used as {{field_name}}
    field_label = Column(String(200), nullable=False)  # Display label
    field_type = Column(String(50), nullable=False)  # text, textarea, date, number, dropdown, checkbox, currency
    field_options = Column(Text, nullable=True)  # JSON for dropdown options
    source = Column(String(50), nullable=False)  # company_info, manual, custom
    company_info_field = Column(String(100), nullable=True)  # Maps to CompanyInfo column
    is_required = Column(Boolean, default=False)
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now())
    updated_at = Column(DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())


class Contract(Base):
    __tablename__ = "CONTRACTS"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(300), nullable=False)
    template_id = Column(Integer, ForeignKey("CONTRACT_TEMPLATES.id"), nullable=False)
    template_snapshot = Column(LONGTEXT, nullable=False)  # JSON snapshot of template + fields at creation
    partner_company_id = Column(Integer, nullable=True)  # FK to COMPANY_INFO (optional)
    partner_name = Column(String(300), nullable=False)
    partner_address = Column(Text, nullable=True)
    partner_tax_id = Column(String(50), nullable=True)
    partner_representative = Column(String(200), nullable=True)
    partner_position = Column(String(200), nullable=True)
    field_values = Column(LONGTEXT, nullable=False)  # JSON of {field_name: value}
    status = Column(String(20), default="draft", nullable=False)  # draft, final
    pdf_path = Column(String(500), nullable=True)
    created_by = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now())
    updated_at = Column(DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())


class ContractPartner(Base):
    __tablename__ = "CONTRACT_PARTNERS"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(300), nullable=False)
    address = Column(Text, nullable=True)
    tax_id = Column(String(50), nullable=True)
    representative = Column(String(200), nullable=True)
    position = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now())
    updated_at = Column(DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())
