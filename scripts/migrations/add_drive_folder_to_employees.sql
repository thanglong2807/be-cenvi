-- Add drive_folder_id column to employees table
USE cenvi_audit;

-- Check if column exists
SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'employees' AND COLUMN_NAME = 'drive_folder_id';

-- Add column if not exists
ALTER TABLE employees
ADD COLUMN drive_folder_id VARCHAR(255) NULL
AFTER email;

-- Verify
DESCRIBE employees;
