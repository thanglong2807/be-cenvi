-- Thêm cột log_id vào company_task_files để phân biệt file theo từng kỳ
ALTER TABLE company_task_files
    ADD COLUMN IF NOT EXISTS log_id INT NULL,
    ADD CONSTRAINT fk_task_file_log
        FOREIGN KEY (log_id) REFERENCES workflow_task_logs(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS ix_company_task_files_log_id ON company_task_files(log_id);
