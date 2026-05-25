from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_password, hash_password, create_access_token, create_refresh_token
from app.models.admin_user_model import AdminUser
from app.models.employee_model import Employee
from app.schemas.auth_schema import TokenResponse, UserOut, AdminCreate

router = APIRouter(prefix="/admin/auth", tags=["Auth"])


def _to_user_out(user: AdminUser) -> UserOut:
    return UserOut(
        id=user.id,
        username=user.username,
        display_name=user.display_name or user.username,
        email=user.email,
        role=user.role,
        roles=[user.role],
    )


@router.post("/login", response_model=TokenResponse)
def login(
    username: str = Form(...),
    password: str = Form(...),
    grant_type: str = Form(default=""),
    scope: str = Form(default=""),
    client_id: str = Form(default=""),
    client_secret: str = Form(default=""),
    db: Session = Depends(get_db),
):
    user = db.query(AdminUser).filter(AdminUser.username == username).first()

    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sai tài khoản hoặc mật khẩu",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tài khoản đã bị khóa")

    user_out = _to_user_out(user)
    access_token = create_access_token({"sub": str(user.id), "username": user.username})
    refresh_token = create_refresh_token({"sub": str(user.id), "username": user.username})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user_out,
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_first_admin(payload: AdminCreate, db: Session = Depends(get_db)):
    """Tạo tài khoản admin đầu tiên. Chỉ hoạt động khi chưa có admin nào trong hệ thống."""
    existing_count = db.query(AdminUser).count()
    if existing_count > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Đã có admin trong hệ thống. Liên hệ admin để được cấp tài khoản.",
        )

    if db.query(AdminUser).filter(AdminUser.username == payload.username).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username đã tồn tại")

    new_user = AdminUser(
        username=payload.username,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name or payload.username,
        email=payload.email,
        role=payload.role,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return _to_user_out(new_user)


@router.post("/create-user", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: AdminCreate,
    admin_key: str = Form(...),
    db: Session = Depends(get_db),
):
    """Tạo thêm user mới. Yêu cầu admin_key."""
    from app.core.config import settings
    if admin_key != settings.SECRET_KEY:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Không có quyền")

    if db.query(AdminUser).filter(AdminUser.username == payload.username).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username đã tồn tại")

    new_user = AdminUser(
        username=payload.username,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name or payload.username,
        email=payload.email,
        role=payload.role,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return _to_user_out(new_user)


class SeedResult(BaseModel):
    total: int
    created: int
    skipped: int
    skipped_no_email: int
    errors: List[str]


@router.post("/seed-from-employees", response_model=SeedResult)
def seed_accounts_from_employees(db: Session = Depends(get_db)):
    """
    Tự động tạo tài khoản cho toàn bộ nhân viên trong bảng employees.
    Username = email nhân viên, password mặc định = Cenvi@123.
    Bỏ qua nhân viên đã có tài khoản hoặc không có email.
    """
    DEFAULT_PASSWORD = "Cenvi@123"
    employees = db.query(Employee).filter(Employee.status == "active").all()

    created = 0
    skipped = 0
    skipped_no_email = 0
    errors: List[str] = []

    for emp in employees:
        if not emp.email:
            skipped_no_email += 1
            continue

        username = emp.email.strip().lower()
        exists = db.query(AdminUser).filter(AdminUser.username == username).first()
        if exists:
            skipped += 1
            continue

        try:
            new_user = AdminUser(
                username=username,
                password_hash=hash_password(DEFAULT_PASSWORD),
                display_name=emp.name or username,
                email=emp.email,
                role="USER",
            )
            db.add(new_user)
            db.commit()
            created += 1
        except Exception as e:
            db.rollback()
            errors.append(f"{emp.email}: {str(e)}")

    return SeedResult(
        total=len(employees),
        created=created,
        skipped=skipped,
        skipped_no_email=skipped_no_email,
        errors=errors,
    )
