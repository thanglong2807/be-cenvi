from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.document_service import DocumentService
from app.services.document_drive_service import DocumentDriveService 
from app.schemas.document_schema import (
    TaiLieuCreate, PhienBanCreate, NewVersionRequest, TaiLieuLatestResponse,
    CategoryCreateRequest, ProjectCreateRequest, BaseMetadata, CategoryTreeResponse,
    # [QUAN TRỌNG] Thêm import
    CategoryUpdateRequest, ProjectUpdateRequest, DocumentMetadataUpdate, TaiLieuCreateFromLink,
    NewVersionFromLink
)
from typing import List
import json

router = APIRouter(prefix="/documents", tags=["Document Storage"])

def get_doc_service(db: Session = Depends(get_db)):
    drive_service = DocumentDriveService() 
    return DocumentService(db, drive_service)

def get_current_user_id():
    return 1 

# --- API CRUD CATEGORY ---
@router.post("/categories", status_code=201)
def create_category(data: CategoryCreateRequest, doc_service: DocumentService = Depends(get_doc_service)):
    return doc_service.create_category(data)

@router.put("/categories/{dm_id}")
def update_category(dm_id: int, data: CategoryUpdateRequest, doc_service: DocumentService = Depends(get_doc_service)):
    return doc_service.update_category(dm_id, data)

@router.delete("/categories/{dm_id}")
def delete_category(dm_id: int, doc_service: DocumentService = Depends(get_doc_service)):
    return doc_service.delete_category(dm_id)

# --- API CRUD PROJECT ---
@router.post("/projects", status_code=201)
def create_project(data: ProjectCreateRequest, doc_service: DocumentService = Depends(get_doc_service)):
    return doc_service.create_project(data)

@router.put("/projects/{mc_id}")
def update_project(mc_id: int, data: ProjectUpdateRequest, doc_service: DocumentService = Depends(get_doc_service)):
    return doc_service.update_project(mc_id, data)

@router.delete("/projects/{mc_id}")
def delete_project(mc_id: int, doc_service: DocumentService = Depends(get_doc_service)):
    return doc_service.delete_project(mc_id)

# --- API CRUD FILE ---
@router.post("/item/from-link", status_code=201)
def create_document_from_link(
    data: TaiLieuCreateFromLink,
    doc_service: DocumentService = Depends(get_doc_service)
):
    """Tạo tài liệu từ link Google Drive có sẵn (không upload file mới)"""
    return doc_service.create_document_from_link(data)

@router.post("/item", status_code=201)
async def create_document(
    mc_id: int = Form(...),
    tieu_de: str = Form(...),
    metadata: str = Form(...),
    ngay_het_hieu_luc: str = Form(None),
    
    # Trường hợp 1: Upload file từ máy
    file: UploadFile = File(None),
    ten_file_goc: str = Form(None),
    kich_thuoc_byte: int = Form(None),
    
    # Trường hợp 2: Dán link (Google Drive, website, v.v.)
    share_drive_link: str = Form(None),
    ten_file_tren_drive: str = Form(None),
    
    user_id: int = Depends(get_current_user_id),
    doc_service: DocumentService = Depends(get_doc_service)
):
    """Tạo tài liệu: Upload file MỚI hoặc Dán link Google Drive"""
    try:
        item_meta = BaseMetadata.parse_raw(metadata)
    except Exception as e:
        raise HTTPException(400, f"Metadata lỗi: {str(e)}. Metadata phải là JSON string hợp lệ, ví dụ: '{{\"ma_mau_hex\": \"#2ecc71\", \"icon_code\": \"FileExcel\"}}'")
    
    # Parse ngày hết hạn
    ngay_het_hieu_luc_dt = None
    if ngay_het_hieu_luc:
        try:
            from datetime import datetime
            ngay_het_hieu_luc_dt = datetime.fromisoformat(ngay_het_hieu_luc.replace('Z', '+00:00'))
        except:
            pass
    
    item_data = TaiLieuCreate(
        MC_ID=mc_id,
        Tieu_De=tieu_de,
        Ngay_Het_Hieu_Luc=ngay_het_hieu_luc_dt,
        Metadata=item_meta
    )
    
    # TRƯỜNG HỢP 1: Upload file từ máy tính
    if file and file.filename:
        if not ten_file_goc or kich_thuoc_byte is None:
            raise HTTPException(400, "Thiếu thông tin file (ten_file_goc, kich_thuoc_byte)")
        
        version_data = PhienBanCreate(
            ten_file_goc=ten_file_goc,
            kich_thuoc_byte=kich_thuoc_byte,
            Loai_Tap_Tin=file.content_type,
            Nguoi_Tai_Len_ID=user_id
        )
        return await doc_service.create_new_document_item(item_data, version_data, await file.read())
    
    # TRƯỜNG HỢP 2: Dán link (Google Drive, website, v.v.)
    elif share_drive_link and ten_file_tren_drive:
        link_data = TaiLieuCreateFromLink(
            MC_ID=mc_id,
            Tieu_De=tieu_de,
            Ngay_Het_Hieu_Luc=ngay_het_hieu_luc_dt,
            Share_Drive_Link=share_drive_link,
            Ten_File_Tren_Drive=ten_file_tren_drive,
            Metadata=item_meta
        )
        return doc_service.create_document_from_link(link_data)
    
    else:
        raise HTTPException(400, "Phải cung cấp: (1) file để upload HOẶC (2) share_drive_link + ten_file_tren_drive để dán link")

@router.post("/item/{tl_id}/version", status_code=201)
async def update_version(
    tl_id: int,
    # Trường hợp 1: Upload file mới
    file: UploadFile = File(None),
    ten_file_goc: str = Form(None),
    kich_thuoc_byte: int = Form(None),
    # Trường hợp 2: Dán link
    share_drive_link: str = Form(None),
    ten_file_tren_drive: str = Form(None),
    
    user_id: int = Depends(get_current_user_id),
    doc_service: DocumentService = Depends(get_doc_service)
):
    """Cập nhật phiên bản mới: Upload file MỚI hoặc Dán link"""
    # TRƯỜNG HỢP 1: Upload file từ máy tính
    if file and file.filename:
        if not ten_file_goc or kich_thuoc_byte is None:
            raise HTTPException(400, "Thiếu thông tin file (ten_file_goc, kich_thuoc_byte)")
        
        version_update = NewVersionRequest(
            TL_ID=tl_id,
            ten_file_goc=ten_file_goc,
            kich_thuoc_byte=kich_thuoc_byte,
            Loai_Tap_Tin=file.content_type,
            Nguoi_Tai_Len_ID=user_id
        )
        return await doc_service.update_new_version(tl_id, version_update, await file.read())
    
    # TRƯỜNG HỢP 2: Dán link
    elif share_drive_link and ten_file_tren_drive:
        link_data = NewVersionFromLink(
            TL_ID=tl_id,
            Share_Drive_Link=share_drive_link,
            Ten_File_Tren_Drive=ten_file_tren_drive
        )
        return doc_service.update_version_from_link(tl_id, link_data)
    
    else:
        raise HTTPException(400, "Phải cung cấp: (1) file để upload HOẶC (2) share_drive_link + ten_file_tren_drive để dán link")

# API Sửa thông tin tài liệu
@router.put("/item/{tl_id}")
def update_document_info(tl_id: int, data: DocumentMetadataUpdate, doc_service: DocumentService = Depends(get_doc_service)):
    return doc_service.update_document_metadata(tl_id, data)

@router.delete("/item/{tl_id}", status_code=204)
def delete_document(tl_id: int, doc_service: DocumentService = Depends(get_doc_service)):
    return doc_service.delete_document(tl_id)

@router.get("/tree", response_model=List[CategoryTreeResponse])
def get_document_tree(doc_service: DocumentService = Depends(get_doc_service)):
    return doc_service.get_full_document_tree()

@router.get("/categories/{dm_id}/detail", response_model=CategoryTreeResponse)
def get_category_detail(dm_id: int, doc_service: DocumentService = Depends(get_doc_service)):
    return doc_service.get_category_detail(dm_id)

# app/api/v1/document_api.py

@router.delete("/categories/{dm_id}")
def delete_category(dm_id: int, doc_service: DocumentService = Depends(get_doc_service)):
    return doc_service.delete_category(dm_id)

@router.delete("/projects/{mc_id}")
def delete_project(mc_id: int, doc_service: DocumentService = Depends(get_doc_service)):
    return doc_service.delete_project(mc_id)