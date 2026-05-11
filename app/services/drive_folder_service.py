#!/usr/bin/env python3
"""
Google Drive Folder Creation Service
Auto-creates folders in Google Drive when company is added
"""
import os
import logging
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from google.api_python_client import build
from datetime import datetime

logger = logging.getLogger(__name__)


class DriveFolderService:
    """Service to create and manage Google Drive folders"""

    def __init__(self):
        """Initialize Google Drive service"""
        self.service = None
        self.drive_service = None
        self._init_service()

    def _init_service(self):
        """Initialize Google Drive API service"""
        try:
            # Path to service account credentials
            creds_path = "credentials/service_account.json"

            if not os.path.exists(creds_path):
                logger.error(f"Service account file not found: {creds_path}")
                return False

            # Build the Drive service
            credentials = Credentials.from_service_account_file(
                creds_path,
                scopes=['https://www.googleapis.com/auth/drive']
            )

            self.drive_service = build('drive', 'v3', credentials=credentials)
            logger.info("Google Drive service initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Drive service: {str(e)}")
            return False

    def create_company_folder(self, company_code: str, company_name: str, mst: str = None,
                             parent_folder_id: str = None, employee_folder_id: str = None,
                             employee_name: str = None):
        """
        Create a folder for company in Google Drive and shortcut in employee folder

        Args:
            company_code: Company code (ma_kh)
            company_name: Company name
            mst: Tax ID (optional)
            parent_folder_id: Parent folder ID (if None, uses ROOT_DRIVE_FOLDER_ID)
            employee_folder_id: Employee folder ID (to create shortcut)
            employee_name: Employee name (for shortcut naming)

        Returns:
            dict: Created folder info with folder_id, or None if error
        """
        if not self.drive_service:
            logger.error("Drive service not initialized")
            return None

        try:
            # Get parent folder ID from env if not provided
            if not parent_folder_id:
                parent_folder_id = os.getenv('COMPANY_PARENT_FOLDER_ID', os.getenv('ROOT_DRIVE_FOLDER_ID'))

            if not parent_folder_id:
                logger.error("Parent folder ID not configured")
                return None

            # Create folder name: company_code_company_name_mst
            folder_name = self._generate_folder_name(company_code, company_name, mst)

            # Check if folder already exists
            existing = self._find_folder_by_name(folder_name, parent_folder_id)
            if existing:
                logger.info(f"Folder already exists: {existing['id']} - {folder_name}")
                return existing

            # Create the folder (support Shared Drive)
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_folder_id],
                'properties': {
                    'company_code': company_code,
                    'tax_id': mst or 'N/A',
                    'created_by': 'Cenvi Auto',
                    'created_at': datetime.now().isoformat()
                }
            }

            folder = self.drive_service.files().create(
                body=file_metadata,
                fields='id, name, webViewLink, parents',
                supportsAllDrives=True,
                supportsTeamDrives=True
            ).execute()

            logger.info(f"Created folder: {folder['id']} - {folder_name}")

            folder_id = folder['id']

            # Create shortcut in employee folder if provided
            if employee_folder_id and employee_name:
                self._create_shortcut_in_employee_folder(
                    employee_folder_id=employee_folder_id,
                    company_folder_id=folder_id,
                    company_code=company_code,
                    employee_name=employee_name
                )

            return {
                'folder_id': folder_id,
                'folder_name': folder['name'],
                'folder_link': folder.get('webViewLink'),
                'parent_id': parent_folder_id,
                'created_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error creating folder for {company_code}: {str(e)}")
            return None

    def _find_folder_by_name(self, folder_name: str, parent_folder_id: str):
        """
        Find folder by name in parent directory

        Args:
            folder_name: Name of folder to find
            parent_folder_id: Parent folder ID

        Returns:
            dict: Folder info if found, None otherwise
        """
        try:
            query = f"name = '{folder_name}' and '{parent_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"

            results = self.drive_service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, webViewLink, parents)',
                pageSize=1
            ).execute()

            files = results.get('files', [])
            if files:
                return files[0]
            return None

        except Exception as e:
            logger.error(f"Error finding folder {folder_name}: {str(e)}")
            return None

    def _generate_folder_name(self, company_code: str, company_name: str, mst: str = None):
        """
        Generate folder name format: company_code_company_name_mst

        Args:
            company_code: Company code
            company_name: Company name
            mst: Tax ID (optional)

        Returns:
            str: Formatted folder name
        """
        # Clean company name - remove special characters, limit length
        clean_name = company_name.replace(' ', '_').replace('/', '_').replace('\\', '_')[:30]

        # Combine parts
        if mst and mst != 'NA':
            folder_name = f"{company_code}_{clean_name}_{mst}"
        else:
            folder_name = f"{company_code}_{clean_name}"

        return folder_name

    def _create_shortcut_in_employee_folder(self, employee_folder_id: str, company_folder_id: str,
                                           company_code: str, employee_name: str):
        """
        Create a shortcut to company folder in employee's folder

        Args:
            employee_folder_id: Employee's folder ID
            company_folder_id: Company folder ID
            company_code: Company code (for shortcut name)
            employee_name: Employee name
        """
        if not self.drive_service or not employee_folder_id:
            return

        try:
            # Shortcut name: NV_Company Code (e.g., "NV_2026TEST_AUTO")
            shortcut_name = f"NV_{company_code}"

            # Check if shortcut already exists
            query = f"name = '{shortcut_name}' and '{employee_folder_id}' in parents and mimeType = 'application/vnd.google-apps.shortcut' and trashed = false"
            results = self.drive_service.files().list(
                q=query,
                spaces='drive',
                fields='files(id)',
                pageSize=1
            ).execute()

            if results.get('files'):
                logger.info(f"Shortcut already exists: {shortcut_name}")
                return

            # Create shortcut
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
                fields='id, name',
                supportsAllDrives=True,
                supportsTeamDrives=True
            ).execute()

            logger.info(f"Created shortcut in employee folder: {shortcut['id']} - {shortcut_name}")

        except Exception as e:
            logger.error(f"Error creating shortcut: {str(e)}")

    def share_folder_with_user(self, folder_id: str, user_email: str, role: str = 'editor'):
        """
        Share folder with a user

        Args:
            folder_id: Folder ID
            user_email: Email to share with
            role: 'reader', 'commenter', or 'editor'

        Returns:
            bool: Success status
        """
        if not self.drive_service:
            return False

        try:
            permission = {
                'type': 'user',
                'role': role,
                'emailAddress': user_email
            }

            self.drive_service.permissions().create(
                fileId=folder_id,
                body=permission,
                fields='id'
            ).execute()

            logger.info(f"Shared folder {folder_id} with {user_email} ({role})")
            return True

        except Exception as e:
            logger.error(f"Error sharing folder {folder_id}: {str(e)}")
            return False

    def create_subfolder(self, parent_folder_id: str, subfolder_name: str):
        """
        Create subfolder in Drive

        Args:
            parent_folder_id: Parent folder ID
            subfolder_name: Name of subfolder to create

        Returns:
            dict: Created folder info, or None if error
        """
        if not self.drive_service:
            return None

        try:
            # Check if subfolder already exists
            existing = self._find_folder_by_name(subfolder_name, parent_folder_id)
            if existing:
                return existing

            file_metadata = {
                'name': subfolder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_folder_id]
            }

            folder = self.drive_service.files().create(
                body=file_metadata,
                fields='id, name, webViewLink'
            ).execute()

            logger.info(f"Created subfolder: {folder['id']} - {subfolder_name}")
            return folder

        except Exception as e:
            logger.error(f"Error creating subfolder {subfolder_name}: {str(e)}")
            return None
