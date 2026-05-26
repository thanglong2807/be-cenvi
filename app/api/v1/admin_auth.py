from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Form, Header
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_password, hash_password, create_access_token, create_refresh_token, decode_token
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
        is_active=user.is_active,
        employee_id=user.employee_id,
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


# ─── Helper: lấy user từ Authorization header ────────────────────────────────
def _get_current_user(authorization: Optional[str], db: Session) -> AdminUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Chưa đăng nhập")
    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token không hợp lệ hoặc đã hết hạn")
    user = db.query(AdminUser).filter(AdminUser.id == int(payload["sub"])).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy tài khoản")
    return user


# ─── GET /me ─────────────────────────────────────────────────────────────────
@router.get("/me", response_model=UserOut)
def get_me(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    user = _get_current_user(authorization, db)
    return _to_user_out(user)


# ─── PUT /me ─────────────────────────────────────────────────────────────────
class ProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    email: Optional[EmailStr] = None


@router.put("/me", response_model=UserOut)
def update_me(
    payload: ProfileUpdate,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    user = _get_current_user(authorization, db)

    if payload.display_name is not None:
        user.display_name = payload.display_name.strip() or user.display_name
    if payload.email is not None:
        existing = db.query(AdminUser).filter(
            AdminUser.email == payload.email, AdminUser.id != user.id
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email đã được dùng bởi tài khoản khác")
        user.email = payload.email

    db.commit()
    db.refresh(user)
    return _to_user_out(user)


# ─── PUT /me/password ────────────────────────────────────────────────────────
class PasswordChange(BaseModel):
    old_password: str
    new_password: str


@router.put("/me/password")
def change_password(
    payload: PasswordChange,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    user = _get_current_user(authorization, db)

    if not verify_password(payload.old_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mật khẩu hiện tại không đúng")
    if len(payload.new_password) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mật khẩu mới phải có ít nhất 6 ký tự")

    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"message": "Đổi mật khẩu thành công"}


# ─── Helper: yêu cầu ADMIN ───────────────────────────────────────────────────
def _require_admin(authorization: Optional[str], db: Session) -> AdminUser:
    user = _get_current_user(authorization, db)
    if user.role != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chỉ Admin mới có quyền này")
    return user


# ─── GET /users ──────────────────────────────────────────────────────────────
@router.get("/users", response_model=List[UserOut])
def list_users(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    _require_admin(authorization, db)
    users = db.query(AdminUser).order_by(AdminUser.id).all()
    return [_to_user_out(u) for u in users]


# ─── POST /users ─────────────────────────────────────────────────────────────
class UserCreate(BaseModel):
    username: str
    password: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    role: str = "USER"
    employee_id: Optional[int] = None
    is_active: bool = True


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user_admin(
    payload: UserCreate,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    _require_admin(authorization, db)
    if db.query(AdminUser).filter(AdminUser.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Username đã tồn tại")
    if payload.email and db.query(AdminUser).filter(AdminUser.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email đã được dùng bởi tài khoản khác")

    new_user = AdminUser(
        username=payload.username,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name or payload.username,
        email=payload.email,
        role=payload.role,
        is_active=payload.is_active,
        employee_id=payload.employee_id,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return _to_user_out(new_user)


# ─── PUT /users/{user_id} ─────────────────────────────────────────────────────
class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    employee_id: Optional[int] = None
    new_password: Optional[str] = None  # reset mật khẩu nếu có


@router.put("/users/{user_id}", response_model=UserOut)
def update_user_admin(
    user_id: int,
    payload: UserUpdate,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    _require_admin(authorization, db)
    user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản")

    if payload.display_name is not None:
        user.display_name = payload.display_name.strip() or user.display_name
    if payload.email is not None:
        existing = db.query(AdminUser).filter(AdminUser.email == payload.email, AdminUser.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email đã được dùng bởi tài khoản khác")
        user.email = payload.email
    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.employee_id is not None:
        user.employee_id = payload.employee_id
    elif "employee_id" in payload.model_fields_set:
        user.employee_id = None
    if payload.new_password:
        if len(payload.new_password) < 6:
            raise HTTPException(status_code=400, detail="Mật khẩu mới phải có ít nhất 6 ký tự")
        user.password_hash = hash_password(payload.new_password)

    db.commit()
    db.refresh(user)
    return _to_user_out(user)


# ─── DELETE /users/{user_id} ──────────────────────────────────────────────────
@router.delete("/users/{user_id}")
def delete_user_admin(
    user_id: int,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    admin = _require_admin(authorization, db)
    if admin.id == user_id:
        raise HTTPException(status_code=400, detail="Không thể xóa chính mình")
    user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản")
    db.delete(user)
    db.commit()
    return {"message": "Đã xóa tài khoản"}


# ─── GET /employees-list (dùng để chọn khi link tài khoản) ───────────────────
class EmployeeOption(BaseModel):
    id: int
    name: Optional[str] = None
    email: Optional[str] = None
    title: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("/employees-list", response_model=List[EmployeeOption])
def list_employees_for_picker(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    _require_admin(authorization, db)
    employees = db.query(Employee).filter(Employee.status == "active").order_by(Employee.name).all()
    return [EmployeeOption(id=e.id, name=e.name, email=e.email, title=e.title) for e in employees]
