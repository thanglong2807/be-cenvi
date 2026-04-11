#!/usr/bin/env python3
"""
Script to seed electronic tax companies from a data list.
Imports companies with organization code, name, tax ID, and person in charge.

Usage:
  python scripts/seed_tax_companies.py < data.json

  or with data argument:
  python scripts/seed_tax_companies.py --data companies_data.json
"""

import sys
import os
import json
import argparse
from datetime import datetime
from typing import Optional, List, Dict, Any

# Fix Unicode encoding for Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.company_info_model import CompanyInfo
from app.models.employee_model import Employee


def get_or_create_employee(db: Session, name: str) -> Optional[Employee]:
    """
    Get employee by name, or create a new one if not found.
    Returns the employee object or None if name is empty.
    """
    if not name or not name.strip():
        return None

    name = name.strip()

    # Try to find existing employee
    employee = db.query(Employee).filter(Employee.name == name).first()
    if employee:
        return employee

    # Create new employee
    try:
        employee = Employee(
            name=name,
            status="active"
        )
        db.add(employee)
        db.flush()
        return employee
    except Exception as e:
        print(f"⚠️ Error creating employee '{name}': {e}")
        return None


def import_tax_companies(db: Session, companies_data: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Import or update electronic tax companies.

    Args:
        db: Database session
        companies_data: List of company dictionaries with keys:
            - ma_to_chuc or ma_kh: Organization code (required)
            - ten_to_chuc or ten_cong_ty: Organization name (required)
            - ma_so_thue: Tax ID (optional)
            - nguoi_phu_trach: Person in charge (optional)

    Returns:
        Dictionary with counts: {'created': X, 'updated': Y, 'errors': Z}
    """
    result = {
        'created': 0,
        'updated': 0,
        'errors': 0,
        'error_details': []
    }

    for idx, company_data in enumerate(companies_data, 1):
        try:
            # Extract fields with multiple possible key names
            ma_kh = company_data.get('ma_to_chuc') or company_data.get('ma_kh')
            ten_cong_ty = company_data.get('ten_to_chuc') or company_data.get('ten_cong_ty')
            ma_so_thue = company_data.get('ma_so_thue')
            phu_trach = company_data.get('nguoi_phu_trach') or company_data.get('phu_trach_hien_tai')

            # Validate required fields
            if not ma_kh or not ma_kh.strip():
                result['errors'] += 1
                result['error_details'].append(f"Row {idx}: Missing organization code (ma_to_chuc/ma_kh)")
                continue

            if not ten_cong_ty or not ten_cong_ty.strip():
                result['errors'] += 1
                result['error_details'].append(f"Row {idx} ({ma_kh}): Missing organization name")
                continue

            ma_kh = ma_kh.strip()
            ten_cong_ty = ten_cong_ty.strip()
            ma_so_thue = ma_so_thue.strip() if ma_so_thue else None

            # Check if company already exists
            existing = db.query(CompanyInfo).filter(CompanyInfo.ma_kh == ma_kh).first()

            # Extract Easybooks and other fields
            pmkt_ten = company_data.get('pmkt_ten')
            pmkt_link = company_data.get('pmkt_link')
            pmkt_tai_khoan = company_data.get('pmkt_tai_khoan')
            pmkt_mat_khau = company_data.get('pmkt_mat_khau')

            if existing:
                # Update existing company
                existing.ten_cong_ty = ten_cong_ty
                if ma_so_thue:
                    existing.ma_so_thue = ma_so_thue

                if phu_trach and phu_trach.strip():
                    phu_trach = phu_trach.strip()
                    # Try to get or create employee
                    employee = get_or_create_employee(db, phu_trach)
                    if employee:
                        existing.phu_trach_hien_tai = phu_trach

                # Update Easybooks fields
                if pmkt_ten:
                    existing.pmkt_ten = pmkt_ten
                if pmkt_link:
                    existing.pmkt_link = pmkt_link
                if pmkt_tai_khoan:
                    existing.pmkt_tai_khoan = pmkt_tai_khoan
                if pmkt_mat_khau:
                    existing.pmkt_mat_khau = pmkt_mat_khau

                existing.updated_at = datetime.now()
                result['updated'] += 1
                print(f"✅ Updated: {ma_kh} - {ten_cong_ty}")
            else:
                # Create new company
                phu_trach_name = None
                if phu_trach and phu_trach.strip():
                    phu_trach = phu_trach.strip()
                    employee = get_or_create_employee(db, phu_trach)
                    if employee:
                        phu_trach_name = phu_trach

                now = datetime.now()
                company = CompanyInfo(
                    ma_kh=ma_kh,
                    ten_cong_ty=ten_cong_ty,
                    ma_so_thue=ma_so_thue,
                    phu_trach_hien_tai=phu_trach_name,
                    pmkt_ten=pmkt_ten,
                    pmkt_link=pmkt_link,
                    pmkt_tai_khoan=pmkt_tai_khoan,
                    pmkt_mat_khau=pmkt_mat_khau,
                    created_at=now,
                    updated_at=now
                )
                db.add(company)
                result['created'] += 1
                print(f"✅ Created: {ma_kh} - {ten_cong_ty}")

            db.flush()

        except Exception as e:
            db.rollback()
            result['errors'] += 1
            result['error_details'].append(f"Row {idx}: {str(e)}")
            print(f"❌ Error on row {idx}: {e}")

    db.commit()
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Import electronic tax companies into the database"
    )
    parser.add_argument(
        '--data',
        '-d',
        type=str,
        help='Path to JSON file containing company data'
    )

    args = parser.parse_args()

    # Read data from file or stdin
    companies_data = []

    try:
        if args.data:
            # Read from file
            with open(args.data, 'r', encoding='utf-8') as f:
                companies_data = json.load(f)
        else:
            # Read from stdin
            input_text = sys.stdin.read()
            if input_text.strip():
                companies_data = json.loads(input_text)
            else:
                print("❌ No data provided. Usage:")
                print("  python scripts/seed_tax_companies.py --data companies.json")
                print("  or")
                print("  python scripts/seed_tax_companies.py < companies.json")
                return

        if not isinstance(companies_data, list):
            print("❌ Data must be a JSON array of company objects")
            return

        print(f"📋 Starting import of {len(companies_data)} companies...")

        db = SessionLocal()
        result = import_tax_companies(db, companies_data)
        db.close()

        print("\n" + "="*60)
        print("IMPORT SUMMARY")
        print("="*60)
        print(f"Created: {result['created']}")
        print(f"Updated: {result['updated']}")
        print(f"Errors:  {result['errors']}")

        if result['error_details']:
            print("\nError Details:")
            for error in result['error_details'][:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(result['error_details']) > 10:
                print(f"  ... and {len(result['error_details']) - 10} more errors")

    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON format: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
