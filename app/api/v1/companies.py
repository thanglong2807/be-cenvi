from fastapi import APIRouter, HTTPException
from app.services.company_service import (
    get_companies,
    get_company_detail,
    create_company
)
from app.schemas.company_schema import CompanyCreate

router = APIRouter(prefix="/companies", tags=["Companies"])

@router.get("")
def list_companies():
    return {"companies": get_companies()}

@router.get("/{company_code}")
def company_detail(company_code: str):
    data = get_company_detail(company_code)
    if not data:
        raise HTTPException(status_code=404, detail="Company not found")
    return data

@router.post("")
def create(payload: CompanyCreate):
    try:
        return create_company(payload.dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
