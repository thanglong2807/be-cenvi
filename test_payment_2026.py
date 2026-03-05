#!/usr/bin/env python3

from app.services.dashboard_sheet_service import dashboard_service

def test_payment_2026():
    print("=== Testing Payment 2026 Data ===")
    
    # Fetch data from sheet
    data = dashboard_service.fetch_data()
    if not data:
        print("❌ Cannot fetch data from sheet")
        return
    
    print(f"Total columns: {len(data['data'][0]) if data['data'] else 0}")
    print(f"First 20 columns: {data['data'][0][:20] if data['data'] else 'No data'}")
    
    # Check if we have enough columns for DB:DR range
    if data['data'] and len(data['data'][0]) >= 120:
        print("✅ Sheet has enough columns for payment 2026 (DB:DR)")
        
        # Check some sample data in payment 2026 range
        print("\n=== Sample Payment 2026 Data ===")
        for i, row in enumerate(data['data'][7:10]):  # Check rows 8-10
            payment_2026 = row[107:120] if len(row) > 120 else []
            print(f"Row {i+8} payment 2026: {payment_2026}")
    else:
        print("❌ Sheet does not have enough columns for payment 2026")
        print(f"Available columns: {len(data['data'][0]) if data['data'] else 0}, Required: ~120")
    
    # Test parsed data
    print("\n=== Testing Parsed Data ===")
    parsed = dashboard_service.parse_sheet_for_kpis()
    if parsed:
        for i, item in enumerate(parsed[:3]):  # Check first 3 items
            print(f"Item {i+1}: {item.get('code')} - {item.get('name')}")
            print(f"  Payment 2026: {item['by_type']['payments']['2026']}")
    else:
        print("❌ Cannot parse data")

if __name__ == "__main__":
    test_payment_2026()
