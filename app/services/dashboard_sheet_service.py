"""
Service để đọc dữ liệu từ Google Sheets
Chuyên dụng cho Dashboard báo cáo doanh thu và tiến độ công việc
"""

import os
import json
from typing import Dict, Any, Optional
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from app.core.config import settings

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']


class DashboardSheetService:
    """Service xử lý Google Sheets API cho Dashboard"""
    
    def __init__(self):
        self.sheet_id = settings.GOOGLE_SHEET_ID
        self.service = self._get_sheets_client()
        self._last_data: Optional[Dict[str, Any]] = None
        self._last_hash: Optional[str] = None
        
    def _get_sheets_client(self):
        """Khởi tạo Google Sheets Client"""
        creds_path = settings.GOOGLE_SERVICE_ACCOUNT_FILE
        if not creds_path or not os.path.exists(creds_path):
            print(f"⚠️ DashboardSheetService: Credentials không tìm thấy tại {creds_path}")
            return None
            
        try:
            creds = service_account.Credentials.from_service_account_file(
                creds_path, scopes=SCOPES
            )
            return build('sheets', 'v4', credentials=creds)
        except Exception as e:
            print(f"❌ Lỗi khởi tạo Sheets Client: {e}")
            return None
    
    def _clean_data(self, values: list) -> list:
        """
        Làm sạch dữ liệu từ sheet:
        - Loại bỏ cột Unnamed
        - Convert số string thành number
        """
        if not values:
            return []
        
        cleaned = []
        for row in values:
            cleaned_row = []
            for cell in row:
                if cell is None:
                    cleaned_row.append(None)
                elif isinstance(cell, str):
                    # Thử convert sang số
                    try:
                        if ',' in cell:
                            cleaned_row.append(float(cell.replace(',', '')))
                        else:
                            cleaned_row.append(float(cell))
                    except:
                        cleaned_row.append(cell)
                else:
                    cleaned_row.append(cell)
            cleaned.append(cleaned_row)
        
        return cleaned
    
    def fetch_data(self, range_name: str = None) -> Optional[Dict[str, Any]]:
        """
        Lấy dữ liệu từ Google Sheet
        
        Args:
            range_name: Range trong sheet (VD: "'Sheet1'!A1:Z100" hoặc "Sheet1!A1:Z100")
                       Nếu None, sẽ dùng default từ config
            
        Returns:
            Dict chứa: {
                'timestamp': datetime ISO string,
                'data': [[...], [...], ...],  # 2D array
                'columns': ['col1', 'col2', ...],
                'rows_count': int,
                'cols_count': int
            }
        """
        if not range_name:
            # Default range nếu không truyền: nếu config.GOOGLE_SHEET_RANGE là placeholder
            # (ví dụ 'A1:Z100') thì request toàn bộ sheet bằng cách chỉ truyền sheet name,
            # còn nếu người dùng cấu hình range cụ thể thì sử dụng sheet!range
            from app.core.config import settings
            cfg_range = getattr(settings, 'GOOGLE_SHEET_RANGE', '') or ''
            sheet_name = getattr(settings, 'GOOGLE_SHEET_NAME', 'KẾ TOÁN THUẾ_KPI')
            if cfg_range.strip() == '' or cfg_range.strip().upper() == 'A1:Z100':
                range_name = f"'{sheet_name}'"
            else:
                range_name = f"'{sheet_name}'!{cfg_range}"
        if not self.service:
            print("❌ Sheets Client không khả dụng")
            return None
        if not self.sheet_id:
            print("❌ Thiếu GOOGLE_SHEET_ID nên không thể fetch dữ liệu từ Sheet")
            return None
        
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=range_name,
                majorDimension='ROWS'
            ).execute()
            
            values = result.get('values', [])
            if not values:
                print("⚠️ Sheet trống")
                return None
            
            # Làm sạch dữ liệu
            cleaned_values = self._clean_data(values)
            
            # Lấy headers (dòng đầu)
            headers = cleaned_values[0] if cleaned_values else []
            data_rows = cleaned_values[1:] if len(cleaned_values) > 1 else []
            
            # Convert thành list of dicts (nếu cần)
            data_list = []
            for row in data_rows:
                row_dict = {}
                for i, header in enumerate(headers):
                    if i < len(row):
                        row_dict[str(header) if header else f"col_{i}"] = row[i]
                    else:
                        row_dict[str(header) if header else f"col_{i}"] = None
                data_list.append(row_dict)
            
            response = {
                'timestamp': datetime.now().isoformat(),
                'data': cleaned_values,  # Raw 2D array
                'data_as_list': data_list,  # List of dicts
                'columns': headers,
                'rows_count': len(cleaned_values),
                'cols_count': len(headers) if headers else 0
            }
            
            return response
            
        except Exception as e:
            print(f"❌ Lỗi fetch data từ Sheet: {e}")
            return None
    
    def has_changed(self, new_data: Dict[str, Any]) -> bool:
        """
        Kiểm tra xem dữ liệu có thay đổi so với lần trước không
        Dùng hash để so sánh
        """
        if not new_data:
            return False
        
        # Tạo hash từ dữ liệu
        data_str = json.dumps(new_data['data'], default=str, sort_keys=True)
        new_hash = str(hash(data_str))
        
        if self._last_hash is None:
            # Lần đầu tiên
            self._last_hash = new_hash
            self._last_data = new_data
            return True
        
        # So sánh hash
        if new_hash != self._last_hash:
            self._last_hash = new_hash
            self._last_data = new_data
            return True
        
        return False
    
    def get_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tạo summary từ dữ liệu sheet
        Hữu ích cho dashboard
        """
        if not data or 'data_as_list' not in data:
            return {}
        
        summary = {
            'total_rows': len(data['data_as_list']),
            'total_columns': data['cols_count'],
            'last_updated': data['timestamp'],
            'sample_data': data['data_as_list'][:5] if data['data_as_list'] else []
        }
        
        return summary

    def _col_letter_to_index(self, letter: str) -> int:
        """Convert column letter (e.g., 'A', 'AA') to 0-based index."""
        letter = letter.upper()
        idx = 0
        for ch in letter:
            if 'A' <= ch <= 'Z':
                idx = idx * 26 + (ord(ch) - ord('A') + 1)
        return idx - 1

    def _slice_row_by_letters(self, row: list, start_letter: str, end_letter: str) -> list:
        start = self._col_letter_to_index(start_letter)
        end = self._col_letter_to_index(end_letter)
        if end < start:
            return []
        # pad row if shorter
        if len(row) <= end:
            row = row + [None] * (end + 1 - len(row))
        return row[start:end+1]

    def parse_sheet_for_kpis(self, range_name: str = None, start_row: int = None) -> Optional[list]:
        """
        Parse the sheet and return list of dicts per employee with extracted blocks.
        Returns None on error.
        """
        from app.core.config import settings
        if start_row is None:
            start_row = getattr(settings, 'DASH_DATA_START_ROW', 7)

        # ensure range
        if not range_name:
            range_name = f"'{settings.GOOGLE_SHEET_NAME}'!{settings.GOOGLE_SHEET_RANGE}"

        data = self.fetch_data(range_name)
        if not data:
            return None

        rows = data['data']
        # rows is full 2D array including header rows; user told data starts at start_row (1-based)
        idx_start = max(0, start_row - 1)

        parsed = []
        # mapping ranges
        cust_range = getattr(settings, 'DASH_CUSTOMERS_RANGE', 'F:Q')
        rev_range = getattr(settings, 'DASH_REVENUE_RANGE', 'S:AD')
        debt24 = getattr(settings, 'DASH_DEBT_2024_RANGE', 'AF:AQ')
        debt25 = getattr(settings, 'DASH_DEBT_2025_RANGE', 'AR:BC')
        debt26 = getattr(settings, 'DASH_DEBT_2026_RANGE', 'BD:BX')
        receivables = getattr(settings, 'DASH_RECEIVABLES_RANGE', 'BQ:CB')
        payment_2024_range = getattr(settings, 'DASH_PAYMENT_2024_RANGE', 'CD:CO')
        payment_2025_range = getattr(settings, 'DASH_PAYMENT_2025_RANGE', 'CP:DA')

        for r in rows[idx_start:]:
            # ensure row has enough columns
            r = r + [None] * 200
            
            # Extract raw slices
            customers_quarterly = self._slice_row_by_letters(r, *cust_range.split(':'))  # F:Q = 12 quarters
            revenue_monthly = self._slice_row_by_letters(r, *rev_range.split(':'))
            debt_2024 = self._slice_row_by_letters(r, *debt24.split(':'))
            debt_2025 = self._slice_row_by_letters(r, *debt25.split(':'))
            debt_2026 = self._slice_row_by_letters(r, *debt26.split(':'))
            receivables_all = self._slice_row_by_letters(r, *receivables.split(':'))  # 12 quarters (Q1-24 to Q4-26)
            payment_2024 = self._slice_row_by_letters(r, *payment_2024_range.split(':'))
            payment_2025 = self._slice_row_by_letters(r, *payment_2025_range.split(':'))
            
            # Split customers by year (4 quarters per year)
            customers_2024 = customers_quarterly[0:4] if len(customers_quarterly) >= 4 else []
            customers_2025 = customers_quarterly[4:8] if len(customers_quarterly) >= 8 else []
            customers_2026 = customers_quarterly[8:12] if len(customers_quarterly) >= 12 else []
            
            # Split revenue by year (4 quarters per year, total 12 quarters for 2024-2026)
            revenue_2024 = revenue_monthly[0:4] if len(revenue_monthly) >= 4 else []
            revenue_2025 = revenue_monthly[4:8] if len(revenue_monthly) >= 8 else []
            revenue_2026 = revenue_monthly[8:12] if len(revenue_monthly) >= 12 else []
            
            # Split receivables by year (4 quarters per year)
            receivables_2024 = receivables_all[0:4] if len(receivables_all) >= 4 else []
            receivables_2025 = receivables_all[4:8] if len(receivables_all) >= 8 else []
            receivables_2026 = receivables_all[8:12] if len(receivables_all) >= 12 else []
            
            item = {
                'code': r[1] if len(r) > 1 else None,
                'name': r[2] if len(r) > 2 else None,
                'status': r[3] if len(r) > 3 else None,
                
                # Organized by type → year → quarter/month
                'by_type': {
                    'customers': {
                        '2024': customers_2024,
                        '2025': customers_2025,
                        '2026': customers_2026
                    },
                    'revenue': {
                        '2024': revenue_2024,
                        '2025': revenue_2025,
                        '2026': revenue_2026
                    },
                    'debt': {
                        '2024': debt_2024,
                        '2025': debt_2025,
                        '2026': debt_2026
                    },
                    'payments': {
                        '2024': payment_2024,
                        '2025': payment_2025
                    },
                    'receivables': {
                        '2024': receivables_2024,
                        '2025': receivables_2025,
                        '2026': receivables_2026
                    }
                }
            }
            # only append if has code or name
            if item['code'] or item['name']:
                parsed.append(item)

        return parsed


# Global instance
dashboard_service = DashboardSheetService()
