import sys
from pathlib import Path

from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import engine
from app.models import audit, document_model, work_link_model


def init_mysql_db() -> None:
    """Create all configured SQLAlchemy tables and verify DB connectivity."""
    audit.Base.metadata.create_all(bind=engine)
    document_model.Base.metadata.create_all(bind=engine)
    work_link_model.Base.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    print("✅ MySQL schema initialized successfully")


if __name__ == "__main__":
    init_mysql_db()
