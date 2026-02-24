import json
import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy import MetaData, Table, create_engine, inspect, text
from sqlalchemy.dialects.mysql import insert as mysql_insert

ROOT_DIR = Path(__file__).resolve().parents[1]
SQLITE_PATH = ROOT_DIR / "cenvi_audit.db"
BACKUP_DIR = ROOT_DIR / "backups"


def normalize_mysql_url(url: str) -> str:
    if url.startswith("mysql://"):
        return url.replace("mysql://", "mysql+pymysql://", 1)
    return url


def get_mysql_url() -> str:
    env_values = dotenv_values(ROOT_DIR / ".env")
    raw = (
        os.getenv("DATABASE_URL")
        or os.getenv("MYSQL_URL")
        or env_values.get("DATABASE_URL")
        or env_values.get("MYSQL_URL")
    )
    if not raw:
        raise RuntimeError("Không tìm thấy MYSQL_URL/DATABASE_URL")
    return normalize_mysql_url(raw)


def get_sqlite_tables(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    return [r[0] for r in rows]


def chunked(items: list[dict], size: int = 500):
    for idx in range(0, len(items), size):
        yield items[idx : idx + size]


def main() -> None:
    if not SQLITE_PATH.exists():
        raise FileNotFoundError(f"Không tìm thấy file SQLite: {SQLITE_PATH}")

    mysql_url = get_mysql_url()
    mysql_engine = create_engine(mysql_url)

    # kiểm tra kết nối MySQL
    with mysql_engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = BACKUP_DIR / f"sqlite_to_mysql_{ts}"
    run_dir.mkdir(parents=True, exist_ok=True)

    # copy file nguồn để lưu backup bản gốc
    sqlite_copy = run_dir / "cenvi_audit.db"
    shutil.copy2(SQLITE_PATH, sqlite_copy)

    sqlite_conn = sqlite3.connect(str(SQLITE_PATH))
    sqlite_conn.row_factory = sqlite3.Row

    mysql_inspector = inspect(mysql_engine)
    mysql_tables = set(mysql_inspector.get_table_names())

    sqlite_tables = get_sqlite_tables(sqlite_conn)

    migrated = {}
    skipped = {}

    with mysql_engine.begin() as mysql_conn:
        mysql_conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        try:
            for table_name in sqlite_tables:
                if table_name not in mysql_tables:
                    skipped[table_name] = "table_not_found_in_mysql"
                    continue

                mysql_meta = MetaData()
                mysql_table = Table(table_name, mysql_meta, autoload_with=mysql_engine)

                sqlite_rows = sqlite_conn.execute(f'SELECT * FROM "{table_name}"').fetchall()
                if not sqlite_rows:
                    migrated[table_name] = 0
                    continue

                mysql_columns = {c.name for c in mysql_table.columns}
                payload = []
                for row in sqlite_rows:
                    record = dict(row)
                    filtered = {k: v for k, v in record.items() if k in mysql_columns}
                    payload.append(filtered)

                if not payload:
                    skipped[table_name] = "no_common_columns"
                    continue

                total = 0
                for batch in chunked(payload, 500):
                    stmt = mysql_insert(mysql_table).values(batch).prefix_with("IGNORE")
                    result = mysql_conn.execute(stmt)
                    total += result.rowcount or 0

                migrated[table_name] = total
        finally:
            mysql_conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))

    sqlite_conn.close()

    report = {
        "status": "success",
        "run_at": datetime.now().isoformat(),
        "sqlite_source": str(SQLITE_PATH),
        "sqlite_backup_copy": str(sqlite_copy),
        "mysql_url_masked": mysql_url.replace(mysql_url.split("@")[0], "mysql+pymysql://***:***"),
        "sqlite_tables": sqlite_tables,
        "migrated": migrated,
        "skipped": skipped,
    }

    report_path = run_dir / "migration_report.json"
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("✅ Backup/Migrate từ SQLite sang MySQL hoàn tất")
    print(f"📦 Thư mục backup: {run_dir}")
    print(f"🧾 Report: {report_path}")
    print(f"📊 Migrated tables: {migrated}")
    if skipped:
        print(f"⚠️ Skipped tables: {skipped}")


if __name__ == "__main__":
    main()
