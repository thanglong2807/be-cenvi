-- Add Metadata column to MUC_CON table
ALTER TABLE MUC_CON ADD COLUMN Metadata JSON DEFAULT NULL;

-- Update existing records with default metadata values
UPDATE MUC_CON SET Metadata = JSON_OBJECT(
    'ma_mau_hex', '#10b981',
    'icon_code', 'Folder',
    'phong_ban', 'Công ty',
    'phu_trach', 'Phùng Duy Anh',
    'ngay_ban_hanh', '2026-02-05'
) WHERE Metadata IS NULL;
