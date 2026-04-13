#!/usr/bin/env python3
"""
API endpoints for syncing COMPANY_INFO and FOLDERS data
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.sync_service import SyncService
from pydantic import BaseModel
from typing import Optional

router = APIRouter(
    prefix="/api/v1/sync",
    tags=["sync"],
    responses={404: {"description": "Not found"}},
)


class SyncResponse(BaseModel):
    """Sync operation response"""
    status: str
    message: str
    created: Optional[int] = None
    updated: Optional[int] = None
    errors: list = []


class SyncStatusResponse(BaseModel):
    """Sync status information"""
    total_companies: int
    total_folders: int
    missing_folders: int
    sync_percentage: float
    missing_company_codes: list


@router.get("/status", response_model=SyncStatusResponse, summary="Get sync status")
def get_sync_status(db: Session = Depends(get_db)):
    """
    Get current sync status between COMPANY_INFO and FOLDERS

    Returns:
        - total_companies: Total companies in COMPANY_INFO
        - total_folders: Total folders in FOLDERS table
        - missing_folders: Number of folders that need to be created
        - sync_percentage: Percentage of companies with folders
        - missing_company_codes: List of company codes missing folders
    """
    try:
        status = SyncService.get_sync_status(db)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-missing-folders", response_model=SyncResponse, summary="Create missing folder records")
def create_missing_folders(db: Session = Depends(get_db)):
    """
    Create FOLDER records for all companies in COMPANY_INFO that don't have folders

    This will:
    1. Find all companies in COMPANY_INFO
    2. Check which ones don't have FOLDERS records
    3. Create new FOLDER records for missing companies
    4. Sync relevant data (company code, name, MST, year, template, status, etc.)

    Returns:
        - status: success or error
        - created: Number of folder records created
        - errors: List of any errors that occurred
    """
    try:
        result = SyncService.sync_missing_folders(db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-folder-data", response_model=SyncResponse, summary="Update folder data from COMPANY_INFO")
def update_folder_data(company_code: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Update existing FOLDER records with latest data from COMPANY_INFO

    Query Parameters:
        - company_code: Optional - if provided, only sync that specific company

    This will sync:
    - company_name (from ten_cong_ty_viet_tat)
    - mst (from ma_so_thue)
    - year, template, status (from folder_year, folder_template, folder_status)
    - root_folder_id (from drive_folder_id)

    Returns:
        - status: success or error
        - updated: Number of folder records updated
        - errors: List of any errors that occurred
    """
    try:
        result = SyncService.sync_folder_data(db, company_code)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync-all", response_model=dict, summary="Complete sync: create missing + update data")
def sync_all(db: Session = Depends(get_db)):
    """
    Perform complete sync:
    1. Create missing FOLDER records
    2. Update all FOLDER data with latest COMPANY_INFO data

    Returns:
        Combined results from both operations
    """
    try:
        # Step 1: Create missing folders
        create_result = SyncService.sync_missing_folders(db)

        # Step 2: Update folder data
        update_result = SyncService.sync_folder_data(db)

        return {
            "status": "completed",
            "create_missing": create_result,
            "update_data": update_result,
            "total_created": create_result.get("created", 0),
            "total_updated": update_result.get("updated", 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
