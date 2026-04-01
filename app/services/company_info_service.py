# app/services/company_info_service.py

from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.company_info_model import CompanyInfo
from app.schemas.company_info_schema import CompanyInfoCreate, CompanyInfoUpdate


class CompanyInfoService:
    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_or_404(self, company_id: int) -> CompanyInfo:
        obj = self.db.query(CompanyInfo).filter(CompanyInfo.id == company_id).first()
        if not obj:
            raise HTTPException(status_code=404, detail=f"Không tìm thấy công ty với id={company_id}")
        return obj

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def get_all(self, skip: int = 0, limit: int = 100) -> List[CompanyInfo]:
        return (
            self.db.query(CompanyInfo)
            .order_by(CompanyInfo.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_id(self, company_id: int) -> CompanyInfo:
        return self._get_or_404(company_id)

    def get_by_ma_kh(self, ma_kh: str) -> Optional[CompanyInfo]:
        return self.db.query(CompanyInfo).filter(CompanyInfo.ma_kh == ma_kh).first()

    def search(self, keyword: str, skip: int = 0, limit: int = 100) -> List[CompanyInfo]:
        kw = f"%{keyword}%"
        return (
            self.db.query(CompanyInfo)
            .filter(
                CompanyInfo.ten_cong_ty.ilike(kw)
                | CompanyInfo.ma_kh.ilike(kw)
                | CompanyInfo.ma_so_thue.ilike(kw)
                | CompanyInfo.phu_trach_hien_tai.ilike(kw)
            )
            .order_by(CompanyInfo.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create(self, data: CompanyInfoCreate) -> CompanyInfo:
        # Kiểm tra trùng Mã KH
        if data.ma_kh:
            existing = self.get_by_ma_kh(data.ma_kh)
            if existing:
                raise HTTPException(
                    status_code=409,
                    detail=f"Mã KH '{data.ma_kh}' đã tồn tại (id={existing.id})",
                )

        now = datetime.now()
        obj = CompanyInfo(
            **data.model_dump(),
            created_at=now,
            updated_at=now,
        )
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, company_id: int, data: CompanyInfoUpdate) -> CompanyInfo:
        obj = self._get_or_404(company_id)

        # Kiểm tra trùng Mã KH (bỏ qua chính nó)
        if data.ma_kh and data.ma_kh != obj.ma_kh:
            existing = self.get_by_ma_kh(data.ma_kh)
            if existing:
                raise HTTPException(
                    status_code=409,
                    detail=f"Mã KH '{data.ma_kh}' đã tồn tại (id={existing.id})",
                )

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(obj, field, value)

        obj.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, company_id: int) -> None:
        obj = self._get_or_404(company_id)
        self.db.delete(obj)
        self.db.commit()
