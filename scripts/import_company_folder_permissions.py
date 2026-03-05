import os
import pandas as pd

from app.core.database import SessionLocal
from app.models.employee import Employee
from app.models.company_folder_permissions import CompanyFolderPermission


# =========================
# CONFIG
# =========================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXCEL_FILE = os.path.join(BASE_DIR, "Phân quyền drive cho Cenvi.xlsx")
SHEET_NAME = 0


# =========================
# UTIL
# =========================
def clean_value(val):
    if pd.isna(val):
        return None

    val = str(val).strip()
    if val.lower() == "nan":
        return None

    return val


def normalize_company_code(raw_code: str | None):
    # VD: "2024KH13 +14" → "2024KH13"
    if not raw_code:
        return None
    return raw_code.split("+")[0].strip()


def normalize_year(val):
    try:
        return int(float(val))
    except Exception:
        return None


# =========================
# MAIN
# =========================
def run():
    db = SessionLocal()

    df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)

    print(f"📄 Loaded {len(df)} rows from Excel\n")

    for idx, row in df.iterrows():
        row_no = idx + 2  # Excel row number

        try:
            # =========================
            # READ EXCEL
            # =========================
            raw_company_code = clean_value(row.get("Mã công ty"))
            company_code = normalize_company_code(raw_company_code)

            folder_name = clean_value(row.get("Tên Folder"))

            email = clean_value(row.get("Gmail"))
            if not email:
                print(f"❌ Row {row_no}: Missing Gmail")
                continue
            email = email.lower()

            start_year = normalize_year(row.get("Năm bắt đầu"))
            if not start_year:
                print(f"❌ Row {row_no}: Invalid year")
                continue

            employee_name = clean_value(row.get("Nhân viên phụ trách"))

            # =========================
            # FIND COMPANY
            # =========================
            company = db.query(Company).filter(
                Company.code == company_code
            ).first()

            if not company:
                print(f"❌ Row {row_no}: Company not found: {raw_company_code}")
                continue

            # =========================
            # FIND EMPLOYEE (OPTIONAL)
            # =========================
            employee_id = None
            if employee_name:
                emp = db.query(Employee).filter(
                    Employee.full_name.ilike(f"%{employee_name}%")
                ).first()
                if emp:
                    employee_id = emp.id

            # =========================
            # CHECK DUPLICATE
            # =========================
            exists = db.query(CompanyFolderPermission).filter_by(
                company_id=company.id,
                email=email,
                start_year=start_year
            ).first()

            if exists:
                print(
                    f"⏩ Row {row_no}: Skip duplicate "
                    f"({company.code}, {email}, {start_year})"
                )
                continue

            # =========================
            # INSERT
            # =========================
            db.add(
                CompanyFolderPermission(
                    company_id=company.id,
                    folder_id=None,          # sync từ Drive sau
                    folder_name=folder_name,
                    email=email,
                    start_year=start_year,
                    employee_id=employee_id,
                    note=None,
                )
            )

            db.commit()

            print(
                f"✅ Row {row_no}: Inserted "
                f"({company.code}, {email}, {start_year})"
            )

        except Exception as e:
            db.rollback()
            print(f"❌ Row {row_no}: Error - {e}")

    db.close()
    print("\n🎉 Import company_folder_permissions DONE")


if __name__ == "__main__":
    run()
