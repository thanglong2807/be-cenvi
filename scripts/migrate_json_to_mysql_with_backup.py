import json
import os
import shutil
from datetime import datetime
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    select,
)
from sqlalchemy.dialects.mysql import insert as mysql_insert

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "app" / "data"
BACKUP_ROOT = ROOT_DIR / "backups"


def normalize_mysql_url(raw_url: str) -> str:
    if raw_url.startswith("mysql://"):
        return raw_url.replace("mysql://", "mysql+pymysql://", 1)
    return raw_url


def get_mysql_url() -> str:
    env_path = ROOT_DIR / ".env"
    env_values = dotenv_values(env_path)

    raw = (
        os.getenv("DATABASE_URL")
        or os.getenv("MYSQL_URL")
        or env_values.get("DATABASE_URL")
        or env_values.get("MYSQL_URL")
    )
    if not raw:
        raise RuntimeError("Không tìm thấy DATABASE_URL hoặc MYSQL_URL trong file .env")

    return normalize_mysql_url(raw)


def load_items(file_path: Path) -> list[dict]:
    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        return data.get("items", [])

    if isinstance(data, list):
        merged_items: list[dict] = []
        for part in data:
            if isinstance(part, dict) and isinstance(part.get("items"), list):
                merged_items.extend(part["items"])
        return merged_items

    return []


def parse_dt(value: str | None):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def create_tables(metadata: MetaData):
    companies = Table(
        "companies",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("code", String(100), nullable=False, unique=True),
        Column("name", String(255), nullable=False),
        Column("mst", String(100), nullable=True),
        Column("emails", JSON, nullable=True),
        Column("created_at", DateTime, nullable=True),
        Column("updated_at", DateTime, nullable=True),
    )

    employees = Table(
        "employees",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String(255), nullable=False),
        Column("title", String(255), nullable=True),
        Column("email", String(255), nullable=True),
        Column("status", String(50), nullable=True),
        Column("created_at", DateTime, nullable=True),
        Column("updated_at", DateTime, nullable=True),
    )

    folders = Table(
        "folders",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("company_code", String(100), nullable=False),
        Column("company_name", String(255), nullable=False),
        Column("mst", String(100), nullable=True),
        Column("manager_employee_id", Integer, nullable=True),
        Column("year", Integer, nullable=True),
        Column("template", String(100), nullable=True),
        Column("status", String(50), nullable=True),
        Column("root_folder_id", String(255), nullable=True),
        Column("created_at", DateTime, nullable=True),
        Column("updated_at", DateTime, nullable=True),
    )

    folder_permissions = Table(
        "folder_permissions",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("folder_id", Integer, nullable=False),
        Column("email", String(255), nullable=False),
        Column("role", String(50), nullable=False),
    )

    return companies, employees, folders, folder_permissions


def upsert_rows(conn, table: Table, rows: list[dict], update_columns: list[str]) -> int:
    if not rows:
        return 0

    stmt = mysql_insert(table).values(rows)
    stmt = stmt.on_duplicate_key_update(
        {col: stmt.inserted[col] for col in update_columns}
    )
    result = conn.execute(stmt)
    return result.rowcount or 0


def fetch_all(conn, table: Table) -> list[dict]:
    result = conn.execute(select(table)).mappings().all()
    normalized: list[dict] = []
    for row in result:
        item = {}
        for k, v in dict(row).items():
            if isinstance(v, datetime):
                item[k] = v.isoformat()
            else:
                item[k] = v
        normalized.append(item)
    return normalized


def build_backup_folder() -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = BACKUP_ROOT / f"db_migration_{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def backup_source_files(backup_dir: Path):
    src_backup = backup_dir / "source_json"
    src_backup.mkdir(parents=True, exist_ok=True)

    for file_name in [
        "companies.json",
        "employees.json",
        "folders.json",
        "folder_permissions.json",
        "companies_storage.json",
    ]:
        src = DATA_DIR / file_name
        if src.exists():
            shutil.copy2(src, src_backup / file_name)


def main():
    mysql_url = get_mysql_url()
    engine = create_engine(mysql_url)
    metadata = MetaData()
    companies_tbl, employees_tbl, folders_tbl, permissions_tbl = create_tables(metadata)

    backup_dir = build_backup_folder()
    backup_source_files(backup_dir)

    companies_raw = load_items(DATA_DIR / "companies.json")
    employees_raw = load_items(DATA_DIR / "employees.json")
    folders_raw = load_items(DATA_DIR / "folders.json")
    permissions_raw = load_items(DATA_DIR / "folder_permissions.json")

    company_rows = []
    for idx, item in enumerate(companies_raw, start=1):
        code = item.get("code") or item.get("company_code")
        name = item.get("name") or item.get("company_name")
        if not code or not name:
            continue
        company_rows.append(
            {
                "id": item.get("id") or idx,
                "code": code,
                "name": name,
                "mst": item.get("mst"),
                "emails": item.get("emails", []),
                "created_at": parse_dt(item.get("created_at")),
                "updated_at": parse_dt(item.get("updated_at")),
            }
        )

    employee_rows = []
    for idx, item in enumerate(employees_raw, start=1):
        name = item.get("name")
        if not name:
            continue
        employee_rows.append(
            {
                "id": item.get("id") or idx,
                "name": name,
                "title": item.get("title"),
                "email": item.get("email"),
                "status": item.get("status"),
                "created_at": parse_dt(item.get("created_at")),
                "updated_at": parse_dt(item.get("updated_at")),
            }
        )

    folder_rows = []
    for idx, item in enumerate(folders_raw, start=1):
        code = item.get("company_code")
        name = item.get("company_name")
        if not code or not name:
            continue
        folder_rows.append(
            {
                "id": item.get("id") or idx,
                "company_code": code,
                "company_name": name,
                "mst": item.get("mst"),
                "manager_employee_id": item.get("manager_employee_id"),
                "year": item.get("year"),
                "template": item.get("template"),
                "status": item.get("status"),
                "root_folder_id": item.get("root_folder_id"),
                "created_at": parse_dt(item.get("created_at")),
                "updated_at": parse_dt(item.get("updated_at")),
            }
        )

    permission_rows = []
    for idx, item in enumerate(permissions_raw, start=1):
        folder_id = item.get("folder_id")
        email = item.get("email")
        role = item.get("role")
        if not folder_id or not email or not role:
            continue
        permission_rows.append(
            {
                "id": item.get("id") or idx,
                "folder_id": folder_id,
                "email": email,
                "role": role,
            }
        )

    with engine.begin() as conn:
        metadata.create_all(conn)

        upsert_rows(conn, companies_tbl, company_rows, ["code", "name", "mst", "emails", "updated_at"])
        upsert_rows(
            conn,
            employees_tbl,
            employee_rows,
            ["name", "title", "email", "status", "updated_at"],
        )
        upsert_rows(
            conn,
            folders_tbl,
            folder_rows,
            [
                "company_code",
                "company_name",
                "mst",
                "manager_employee_id",
                "year",
                "template",
                "status",
                "root_folder_id",
                "updated_at",
            ],
        )
        upsert_rows(conn, permissions_tbl, permission_rows, ["folder_id", "email", "role"])

        snapshot = {
            "exported_at": datetime.now().isoformat(),
            "counts": {
                "companies": len(company_rows),
                "employees": len(employee_rows),
                "folders": len(folder_rows),
                "folder_permissions": len(permission_rows),
            },
            "data": {
                "companies": fetch_all(conn, companies_tbl),
                "employees": fetch_all(conn, employees_tbl),
                "folders": fetch_all(conn, folders_tbl),
                "folder_permissions": fetch_all(conn, permissions_tbl),
            },
        }

    backup_file = backup_dir / "mysql_data_backup.json"
    with backup_file.open("w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    report_file = backup_dir / "migration_report.json"
    report = {
        "status": "success",
        "mysql_url_masked": mysql_url.replace(mysql_url.split("@")[0], "mysql+pymysql://***:***"),
        "backup_dir": str(backup_dir),
        "backup_file": str(backup_file),
        "counts": snapshot["counts"],
    }
    with report_file.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("✅ Đã migrate dữ liệu JSON sang MySQL thành công")
    print(f"📦 Backup thư mục: {backup_dir}")
    print(f"🧾 Backup dữ liệu: {backup_file}")
    print(f"📊 Thống kê: {snapshot['counts']}")


if __name__ == "__main__":
    main()
