# Sao kê Files Check Scripts

## Overview
These scripts check for the existence of files in sao kê (bank statement) folders and return appropriate status:
- **pass**: Files exist in the sao kê folder
- **warning**: No files found or folder doesn't exist

## Scripts

### 1. check_saoke.py
Check sao kê files for a single company.

**Usage:**
```bash
python check_saoke.py --company-id <FOLDER_ID> --year <YEAR> [--verbose]
```

**Parameters:**
- `--company-id`: Drive folder ID of the company root
- `--year`: Year to check (e.g., 2024)
- `--verbose`: Show detailed file list (optional)

**Examples:**
```bash
# Basic check
python check_saoke.py --company-id "1ABC123XYZ" --year 2024

# With verbose output
python check_saoke.py --company-id "1ABC123XYZ" --year 2024 --verbose
```

**Exit Codes:**
- `0`: Pass (files found)
- `1`: Warning (no files found or error)

### 2. check_saoke_batch.py
Check sao kê files for all companies in batch mode.

**Usage:**
```bash
python check_saoke_batch.py --year <YEAR> [--config <CONFIG_FILE>] [--output <OUTPUT_FILE>]
```

**Parameters:**
- `--year`: Year to check (e.g., 2024)
- `--config`: Path to companies config file (default: data_output_managers.json)
- `--output`: Save results to JSON file (optional)

**Examples:**
```bash
# Check all companies for 2024
python check_saoke_batch.py --year 2024

# Save results to file
python check_saoke_batch.py --year 2024 --output sao_ke_results_2024.json

# Use custom config file
python check_saoke_batch.py --year 2024 --config custom_companies.json
```

## Folder Structure Checked
The scripts look for files in this folder structure:
```
Company Root/
└── CONG-TY/
    └── <YEAR>/
        └── 4-SAO-KE-NGAN-HANG/
            ├── (files and subfolders)
            └── (recursive search for all files)
```

## Output Format

### Single Company Script
Returns status, message, and file count:
```
Status: pass
Message: Tìm thấy 15 file trong folder sao kê ngân hàng năm 2024
Files count: 15
```

### Batch Script
Shows detailed progress and summary:
```
Checking sao kê files for year 2024...
==================================================

📁 Checking: Company A
   ✅ Tìm thấy 12 file trong folder sao kê ngân hàng năm 2024

📁 Checking: Company B
   ⚠️ Không tìm thấy folder 4-SAO-KE-NGAN-HANG cho năm 2024

==================================================
SUMMARY:
✅ Passed: 1
⚠️  Warning: 1
📊 Total: 2
```

## Integration with CI/CD
These scripts can be integrated into CI/CD pipelines:

```bash
# In CI/CD script
python check_saoke_batch.py --year 2024
if [ $? -eq 0 ]; then
    echo "All sao kê checks passed"
else
    echo "Some sao kê checks failed - review warnings"
    exit 1
fi
```

## Requirements
- Python 3.6+
- Google Drive API credentials configured
- Access to the required Drive folders
