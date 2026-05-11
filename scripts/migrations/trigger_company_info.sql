-- Create MySQL Trigger to auto-create FOLDERS record when COMPANY_INFO is inserted
USE cenvi_audit;

-- Drop existing trigger if it exists
DROP TRIGGER IF EXISTS trigger_auto_create_folder;

-- Create log table for trigger errors (if not exists)
CREATE TABLE IF NOT EXISTS trigger_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    trigger_name VARCHAR(100),
    action VARCHAR(50),
    error_message TEXT,
    created_at DATETIME
);

-- Create trigger
DELIMITER //

CREATE TRIGGER trigger_auto_create_folder
AFTER INSERT ON COMPANY_INFO
FOR EACH ROW
BEGIN
    DECLARE exit handler for sqlexception
    BEGIN
        INSERT INTO trigger_logs (trigger_name, action, error_message, created_at)
        VALUES ('trigger_auto_create_folder', 'INSERT', CONCAT('Error creating folder for ', NEW.ma_kh), NOW());
    END;

    -- Insert new FOLDER record only if it doesn't already exist
    INSERT IGNORE INTO FOLDERS (
        company_code,
        company_name,
        mst,
        year,
        template,
        status,
        root_folder_id,
        created_at,
        updated_at
    ) VALUES (
        NEW.ma_kh,
        COALESCE(NEW.ten_cong_ty_viet_tat, SUBSTRING(NEW.ten_cong_ty, 1, 50)),
        NEW.ma_so_thue,
        COALESCE(NEW.folder_year, YEAR(NOW())),
        COALESCE(NEW.folder_template, 'STANDARD'),
        COALESCE(NEW.folder_status, 'active'),
        NEW.drive_folder_id,
        NOW(),
        NOW()
    );

END //

DELIMITER ;

-- Verify trigger was created
SELECT TRIGGER_NAME, EVENT_MANIPULATION, TRIGGER_SCHEMA
FROM INFORMATION_SCHEMA.TRIGGERS
WHERE TRIGGER_NAME = 'trigger_auto_create_folder';
