"""
Migration: đổi cột content/template_snapshot/field_values sang LONGTEXT
Lý do: TEXT giới hạn 65,535 bytes — template HTML thực tế vượt quá giới hạn này.

Chạy: python scripts/migrations/migrate_contract_longtext.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.core.database import engine
from sqlalchemy import text

MIGRATIONS = [
    "ALTER TABLE CONTRACT_TEMPLATES MODIFY COLUMN content LONGTEXT NOT NULL",
    "ALTER TABLE CONTRACTS MODIFY COLUMN template_snapshot LONGTEXT NOT NULL",
    "ALTER TABLE CONTRACTS MODIFY COLUMN field_values LONGTEXT NOT NULL",
]

def run():
    with engine.connect() as conn:
        for sql in MIGRATIONS:
            print(f"Running: {sql}")
            conn.execute(text(sql))
            conn.commit()
            print("  OK")
    print("\nMigration hoàn tất.")

if __name__ == "__main__":
    run()
