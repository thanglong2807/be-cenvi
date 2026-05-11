import json
import re
import os
from pathlib import Path
from datetime import datetime
from io import BytesIO
from sqlalchemy.orm import Session
from fastapi import HTTPException

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm, inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from app.models.contract_model import Contract
from app.models.company_info_model import CompanyInfo


class ContractPDFService:
    """Service để tạo PDF hợp đồng từ template"""

    PDF_DIR = "static/contracts"

    def __init__(self):
        # Create static/contracts directory if not exists
        Path(self.PDF_DIR).mkdir(parents=True, exist_ok=True)

    def generate_pdf(self, contract_id: int, db: Session) -> str:
        """
        Generate PDF from contract
        Returns: PDF file path
        """
        if not REPORTLAB_AVAILABLE:
            raise HTTPException(status_code=500, detail="reportlab not installed. Please install: pip install reportlab==4.2.5")

        # Get contract from DB
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")

        # Parse template snapshot
        template_snapshot = json.loads(contract.template_snapshot)
        field_values = json.loads(contract.field_values)

        # Get company info (if selected)
        company_data = {}
        if contract.partner_company_id:
            company = db.query(CompanyInfo).filter(CompanyInfo.id == contract.partner_company_id).first()
            if company:
                company_data = self._extract_company_fields(company)

        # Build variable map
        variables = {}
        variables.update(company_data)  # Add company fields
        variables.update(field_values)  # Add filled field values

        # Replace variables in template content
        content = template_snapshot.get("content", "")
        rendered_content = self._replace_variables(content, variables)

        # Generate PDF
        pdf_path = self._create_pdf_document(
            contract_id,
            contract.title,
            rendered_content,
            contract,
            template_snapshot,
        )

        # Update contract with PDF path
        contract.pdf_path = pdf_path
        contract.updated_at = datetime.now()
        db.commit()

        return pdf_path

    def _extract_company_fields(self, company: CompanyInfo) -> dict:
        """Extract company fields as variables"""
        return {
            "{{ten_cong_ty}}": company.ten_cong_ty or "",
            "{{ten_viet_tat}}": company.ten_cong_ty_viet_tat or "",
            "{{ma_so_thue}}": company.ma_so_thue or "",
            "{{ma_kh}}": company.ma_kh or "",
            "{{nguoi_lien_he}}": company.nguoi_lien_he_va_chuc_vu or "",
            "{{so_dien_thoai}}": company.so_dien_thoai or "",
            "{{email}}": company.email_lien_he or "",
            "{{hop_dong_ngay_ky}}": str(company.hop_dong_ngay_ky) if company.hop_dong_ngay_ky else "",
            "{{hop_dong_thanh_toan}}": company.hop_dong_thanh_toan or "",
        }

    def _replace_variables(self, content: str, variables: dict) -> str:
        """Replace {{variable}} with actual values"""
        result = content
        for var_name, value in variables.items():
            result = result.replace(var_name, str(value))

        # Replace any remaining unreplaced variables with empty string
        result = re.sub(r"\{\{[\w_]+\}\}", "", result)

        return result

    def _create_pdf_document(
        self,
        contract_id: int,
        title: str,
        content: str,
        contract: Contract,
        template_snapshot: dict,
    ) -> str:
        """Create actual PDF file"""
        # Create PDF file path
        filename = f"contract_{contract_id}_{datetime.now().timestamp()}.pdf"
        filepath = os.path.join(self.PDF_DIR, filename)

        # Setup PDF document
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=15*mm,
            leftMargin=15*mm,
            topMargin=15*mm,
            bottomMargin=15*mm,
        )

        # Get styles
        styles = getSampleStyleSheet()

        # Create custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=14,
            textColor=colors.HexColor('#1f2937'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=11,
            textColor=colors.HexColor('#374151'),
            spaceAfter=8,
            spaceBefore=8,
            fontName='Helvetica-Bold',
        )

        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=10,
            textColor=colors.HexColor('#111827'),
            spaceAfter=6,
            alignment=TA_JUSTIFY,
            fontName='Helvetica',
        )

        # Build story (content for PDF)
        story = []

        # Add title
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 6*mm))

        # Add contract info header
        header_data = [
            ['Mã Hợp Đồng:', f'HDTC-{contract_id}'],
            ['Ngày Tạo:', datetime.now().strftime('%d/%m/%Y')],
            ['Trạng Thái:', contract.status.upper()],
        ]

        header_table = Table(header_data, colWidths=[3*cm, 5*cm])
        header_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6b7280')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 8*mm))

        # Parse and render content
        # Handle both plain text and HTML-like markup
        content_lines = content.split('\n')
        for line in content_lines:
            if line.strip():
                # Try to detect section headers (lines in **bold**)
                if line.startswith('**') and line.endswith('**'):
                    heading_text = line.strip('*')
                    story.append(Paragraph(heading_text, heading_style))
                else:
                    story.append(Paragraph(line, body_style))
            else:
                story.append(Spacer(1, 4*mm))

        story.append(Spacer(1, 10*mm))

        # Add signature section
        sig_style = ParagraphStyle(
            'SignatureStyle',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#6b7280'),
            alignment=TA_CENTER,
        )

        story.append(Paragraph("Ký Tên", heading_style))
        story.append(Spacer(1, 15*mm))

        sig_data = [
            [
                f"Bên A:<br/>{contract.partner_name}",
                "Bên B:<br/>Cenvi",
            ]
        ]
        sig_table = Table(sig_data, colWidths=[4*cm, 4*cm])
        story.append(sig_table)

        # Build PDF
        doc.build(story)

        return filepath

    def generate_pdf_bytes(self, contract_id: int, db: Session) -> BytesIO:
        """Generate PDF as bytes (for streaming)"""
        # Generate PDF file first
        pdf_path = self.generate_pdf(contract_id, db)

        # Read file and return as bytes
        with open(pdf_path, 'rb') as f:
            return BytesIO(f.read())

    @staticmethod
    def get_pdf_path(contract_id: int) -> str:
        """Get the PDF path for a contract"""
        pdf_dir = Path(ContractPDFService.PDF_DIR)
        if pdf_dir.exists():
            # Find the latest PDF for this contract
            pattern = f"contract_{contract_id}_*.pdf"
            files = list(pdf_dir.glob(pattern))
            if files:
                return str(sorted(files)[-1])
        return None
