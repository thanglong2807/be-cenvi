#!/usr/bin/env python3
"""
Sync service to synchronize COMPANY_INFO with FOLDERS table
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.company_info_model import CompanyInfo
from app.models.folder_model import Folder
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SyncService:
    """Service to sync data from COMPANY_INFO to FOLDERS"""

    @staticmethod
    def find_missing_folders(db: Session):
        """
        Find companies in COMPANY_INFO that don't have corresponding FOLDERS record

        Returns:
            list: List of companies that need folder records
        """
        # Get all company codes from COMPANY_INFO
        company_codes_in_info = db.query(CompanyInfo.ma_kh).all()
        company_codes_info = [code[0] for code in company_codes_in_info]

        # Get all company codes from FOLDERS
        company_codes_in_folders = db.query(Folder.company_code).all()
        company_codes_folders = [code[0] for code in company_codes_in_folders]

        # Find missing
        missing_codes = set(company_codes_info) - set(company_codes_folders)

        # Get companies with missing folders
        missing_companies = db.query(CompanyInfo).filter(
            CompanyInfo.ma_kh.in_(missing_codes)
        ).all()

        return missing_companies

    @staticmethod
    def sync_missing_folders(db: Session):
        """
        Create FOLDER records for missing companies

        Returns:
            dict: Sync result with counts and details
        """
        missing_companies = SyncService.find_missing_folders(db)

        created_count = 0
        errors = []

        for company in missing_companies:
            try:
                # Create new folder record
                folder = Folder(
                    company_code=company.ma_kh,
                    company_name=company.ten_cong_ty_viet_tat or company.ten_cong_ty[:50],
                    mst=company.ma_so_thue,
                    manager_employee_id=None,  # Will need to map from employee
                    year=company.folder_year or 2025,
                    template=company.folder_template or 'STANDARD',
                    status=company.folder_status or 'active',
                    root_folder_id=company.drive_folder_id,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                db.add(folder)
                created_count += 1
                logger.info(f"Created folder for: {company.ma_kh} - {company.ten_cong_ty}")

            except Exception as e:
                error_msg = f"Error creating folder for {company.ma_kh}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        # Commit all changes
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            return {
                "status": "error",
                "message": f"Database commit failed: {str(e)}",
                "created": created_count,
                "errors": errors
            }

        return {
            "status": "success",
            "message": f"Successfully created {created_count} folder records",
            "created": created_count,
            "missing_total": len(missing_companies),
            "errors": errors
        }

    @staticmethod
    def sync_folder_data(db: Session, company_code: str = None):
        """
        Update FOLDER data from COMPANY_INFO

        Args:
            company_code: Optional specific company to sync, if None sync all

        Returns:
            dict: Sync result
        """
        updated_count = 0
        errors = []

        if company_code:
            # Sync specific company
            folders = db.query(Folder).filter(Folder.company_code == company_code).all()
        else:
            # Sync all
            folders = db.query(Folder).all()

        for folder in folders:
            try:
                # Get corresponding company info
                company = db.query(CompanyInfo).filter(
                    CompanyInfo.ma_kh == folder.company_code
                ).first()

                if not company:
                    continue

                # Update folder fields from company info
                folder.company_name = company.ten_cong_ty_viet_tat or company.ten_cong_ty[:50]
                folder.mst = company.ma_so_thue
                folder.year = company.folder_year or 2025
                folder.template = company.folder_template or 'STANDARD'
                folder.status = company.folder_status or 'active'
                folder.root_folder_id = company.drive_folder_id
                folder.updated_at = datetime.now()

                updated_count += 1
                logger.info(f"Updated folder for: {company.ma_kh}")

            except Exception as e:
                error_msg = f"Error updating folder {folder.company_code}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        # Commit changes
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            return {
                "status": "error",
                "message": f"Database commit failed: {str(e)}",
                "updated": updated_count,
                "errors": errors
            }

        return {
            "status": "success",
            "message": f"Successfully updated {updated_count} folder records",
            "updated": updated_count,
            "errors": errors
        }

    @staticmethod
    def get_sync_status(db: Session):
        """
        Get current sync status between COMPANY_INFO and FOLDERS

        Returns:
            dict: Status information
        """
        total_companies = db.query(CompanyInfo).count()
        total_folders = db.query(Folder).count()

        missing_companies = SyncService.find_missing_folders(db)
        missing_count = len(missing_companies)

        return {
            "total_companies": total_companies,
            "total_folders": total_folders,
            "missing_folders": missing_count,
            "sync_percentage": ((total_folders / total_companies) * 100) if total_companies > 0 else 0,
            "missing_company_codes": [c.ma_kh for c in missing_companies[:10]]  # First 10
        }
