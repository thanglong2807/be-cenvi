#!/usr/bin/env python3
"""
Employee Folder Service - Manage employee folders in Google Drive
- Create employee folder
- Create shortcuts to company folders
"""
import os
import logging
from typing import Optional
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

# Root folder where all employee folders are located
EMPLOYEES_ROOT_FOLDER_ID = os.getenv('EMPLOYEES_ROOT_FOLDER_ID') or "0AIxlO0tI8hPBUk9PVA"


class EmployeeFolderService:
    """Service to manage employee folders in Google Drive"""

    def __init__(self):
        self.drive_service = None
        self._init_service()

    def _init_service(self):
        """Initialize Google Drive API service"""
        try:
            creds_path = "credentials/service_account.json"
            if not os.path.exists(creds_path):
                logger.error(f"Service account file not found: {creds_path}")
                return False

            credentials = Credentials.from_service_account_file(
                creds_path,
                scopes=['https://www.googleapis.com/auth/drive']
            )
            self.drive_service = build('drive', 'v3', credentials=credentials)
            logger.info("Employee Folder Service initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize service: {str(e)}")
            return False

    def create_employee_folder(self, employee_name: str, parent_folder_id: str = None) -> Optional[str]:
        """
        Create a folder for employee in Google Drive

        Args:
            employee_name: Employee name
            parent_folder_id: Parent folder (default: EMPLOYEES_ROOT_FOLDER_ID)

        Returns:
            str: Folder ID if created, None if error
        """
        if not self.drive_service:
            logger.error("Drive service not initialized")
            return None

        try:
            if not parent_folder_id:
                parent_folder_id = EMPLOYEES_ROOT_FOLDER_ID

            # Folder name: NV_Employee Name
            folder_name = f"NV_{employee_name}"

            # Check if folder already exists
            existing = self._find_folder_by_name(folder_name, parent_folder_id)
            if existing:
                logger.info(f"Employee folder already exists: {existing['id']} - {folder_name}")
                return existing['id']

            # Create folder
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_folder_id],
                'properties': {
                    'employee_name': employee_name,
                    'folder_type': 'employee_folder'
                }
            }

            folder = self.drive_service.files().create(
                body=file_metadata,
                fields='id, name, webViewLink',
                supportsAllDrives=True,
                supportsTeamDrives=True
            ).execute()

            logger.info(f"Created employee folder: {folder['id']} - {folder_name}")
            return folder['id']

        except Exception as e:
            logger.error(f"Error creating employee folder: {str(e)}")
            return None

    def create_shortcut_to_company_folder(
        self,
        employee_folder_id: str,
        company_folder_id: str,
        shortcut_name: str
    ) -> Optional[str]:
        """
        Create a shortcut (alias) to company folder in employee folder

        Args:
            employee_folder_id: Employee's folder ID
            company_folder_id: Company folder ID to create shortcut to
            shortcut_name: Shortcut name (e.g., "NV_Phùng Duy Anh" for company)

        Returns:
            str: Shortcut ID if created, None if error
        """
        if not self.drive_service:
            logger.error("Drive service not initialized")
            return None

        try:
            # Check if shortcut already exists
            existing = self._find_shortcut_by_name(shortcut_name, employee_folder_id)
            if existing:
                logger.info(f"Shortcut already exists: {existing['id']} - {shortcut_name}")
                return existing['id']

            # Create shortcut metadata
            file_metadata = {
                'name': shortcut_name,
                'mimeType': 'application/vnd.google-apps.shortcut',
                'shortcutDetails': {
                    'targetId': company_folder_id
                },
                'parents': [employee_folder_id]
            }

            shortcut = self.drive_service.files().create(
                body=file_metadata,
                fields='id, name, mimeType',
                supportsAllDrives=True,
                supportsTeamDrives=True
            ).execute()

            logger.info(f"Created shortcut: {shortcut['id']} - {shortcut_name}")
            return shortcut['id']

        except Exception as e:
            logger.error(f"Error creating shortcut: {str(e)}")
            return None

    def _find_folder_by_name(self, folder_name: str, parent_folder_id: str) -> Optional[dict]:
        """Find folder by name in parent directory"""
        try:
            query = f"name = '{folder_name}' and '{parent_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"

            results = self.drive_service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, webViewLink)',
                pageSize=1
            ).execute()

            files = results.get('files', [])
            return files[0] if files else None

        except Exception as e:
            logger.error(f"Error finding folder: {str(e)}")
            return None

    def _find_shortcut_by_name(self, shortcut_name: str, parent_folder_id: str) -> Optional[dict]:
        """Find shortcut by name in parent folder"""
        try:
            query = f"name = '{shortcut_name}' and '{parent_folder_id}' in parents and mimeType = 'application/vnd.google-apps.shortcut' and trashed = false"

            results = self.drive_service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, mimeType)',
                pageSize=1
            ).execute()

            files = results.get('files', [])
            return files[0] if files else None

        except Exception as e:
            logger.error(f"Error finding shortcut: {str(e)}")
            return None

    def remove_shortcut(self, shortcut_id: str) -> bool:
        """Remove a shortcut"""
        try:
            self.drive_service.files().delete(fileId=shortcut_id).execute()
            logger.info(f"Deleted shortcut: {shortcut_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting shortcut: {str(e)}")
            return False
