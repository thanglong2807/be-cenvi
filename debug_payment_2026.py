#!/usr/bin/env python3

from app.services.dashboard_sheet_service import dashboard_service
from app.core.config import settings

def debug_payment_2026():
    print("=== DEBUG PAYMENT 2026 ===")
    
    # Fetch data
    data = dashboard_service.fetch_data()
    if not data or not data['data']:
        print("❌ Cannot fetch data")
        return
    
    print(f"Total columns: {len(data['data'][0])}")
    
    # Kiểm tra columns DB đến DM (108-115)
    print("\n=== Kiểm tra columns DB đến DM ===")
    if len(data['data']) > 7:  # Row 8 exists
        row_8 = data['data'][7]  # Index 7 = Row 8
        for i in range(108, min(116, len(row_8))):
            col_letter = chr(65 + (i // 26)) + chr(65 + (i % 26)) if i >= 26 else chr(65 + i)
            value = row_8[i] if i < len(row_8) else "N/A"
            print(f"Column {col_letter} (index {i}): {value}")
    
    # Test _slice_row_by_letters function
    print("\n=== Test slice function ===")
    if len(data['data']) > 7:
        test_row = data['data'][7]
        print(f"Test row length: {len(test_row)}")
        
        # Test slice DB:DM
        slice_result = dashboard_service._slice_row_by_letters(test_row, 'DB', 'DM')
        print(f"Slice DB:DM result: {slice_result}")
        print(f"Slice length: {len(slice_result)}")
    
    # Test parse function
    print("\n=== Test parse function ===")
    parsed = dashboard_service.parse_sheet_for_kpis()
    if parsed and len(parsed) > 0:
        first_item = parsed[0]
        print(f"First item: {first_item.get('code')} - {first_item.get('name')}")
        print(f"Payment 2026 data: {first_item['by_type']['payments']['2026']}")
        print(f"Length of payment 2026: {len(first_item['by_type']['payments']['2026'])}")
    else:
        print("❌ Parse failed")

if __name__ == "__main__":
    debug_payment_2026()
