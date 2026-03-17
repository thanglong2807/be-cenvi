#!/usr/bin/env python3
"""
Batch script to check sao kê files for multiple companies
"""

import sys
import os
import json
from pathlib import Path

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from check_saoke import check_saoke_files

def load_companies_config(config_file='data_output_managers.json'):
    """Load companies configuration from JSON file"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('companies', [])
    except Exception as e:
        print(f"Error loading config: {e}")
        return []

def check_all_companies(year, config_file='data_output_managers.json'):
    """Check sao kê files for all companies"""
    companies = load_companies_config(config_file)
    results = []
    
    print(f"Checking sao kê files for year {year}...")
    print("=" * 50)
    
    for company in companies:
        company_name = company.get('name', 'Unknown')
        company_id = company.get('drive_folder_id')
        
        if not company_id:
            print(f"⚠️  {company_name}: No drive folder ID")
            continue
            
        print(f"\n📁 Checking: {company_name}")
        result = check_saoke_files(company_id, year)
        
        status_icon = "✅" if result['status'] == 'pass' else "⚠️"
        print(f"   {status_icon} {result['message']}")
        
        results.append({
            'company_name': company_name,
            'company_id': company_id,
            'status': result['status'],
            'message': result['message'],
            'files_count': result['files_count']
        })
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY:")
    passed = sum(1 for r in results if r['status'] == 'pass')
    warned = len(results) - passed
    
    print(f"✅ Passed: {passed}")
    print(f"⚠️  Warning: {warned}")
    print(f"📊 Total: {len(results)}")
    
    return results

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Batch check sao kê files for all companies')
    parser.add_argument('--year', required=True, type=int, help='Year to check')
    parser.add_argument('--config', default='data_output_managers.json', help='Config file path')
    parser.add_argument('--output', help='Output results to JSON file')
    
    args = parser.parse_args()
    
    results = check_all_companies(args.year, args.config)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n📄 Results saved to: {args.output}")
    
    # Exit with warning code if any warnings
    has_warnings = any(r['status'] == 'warning' for r in results)
    sys.exit(0 if not has_warnings else 1)

if __name__ == '__main__':
    main()
