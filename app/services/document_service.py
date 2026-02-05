from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from fastapi import HTTPException
from typing import List, Tuple
from datetime import datetime
import os

# Import Models
from app.models.document_model import TaiLieu, PhienBanTaiLieu, MucCon, DanhMuc, PhanQuyenTruyCap
# (Có thể bỏ import Employee nếu không dùng nữa)

# Import Schemas
from app.schemas.document_schema import (
    TaiLieuCreate, 
    PhienBanCreate, 
    NewVersionRequest, 
    FileMetadata,
    CategoryCreateRequest,
    ProjectCreateRequest,
    CategoryUpdateRequest,
    ProjectUpdateRequest,
    DocumentMetadataUpdate
)

# Import Service
from app.services.document_drive_service import DocumentDriveService

class DocumentService:
    ROOT_DRIVE_ID = "0ADyH3Kpce7PJUk9PVA" 

    def __init__(self, db: Session, drive_service: DocumentDriveService):
        self.db = db
        self.drive_service = drive_service 

    # =========================================================================
    # LOGIC LẤY DỮ LIỆU (ĐÃ BỎ PHÂN QUYỀN PHÒNG BAN)
    # =========================================================================

    def get_full_document_tree(self) -> List[DanhMuc]:
        categories = self.db.query(DanhMuc).options(
            joinedload(DanhMuc.muc_con)
            .joinedload(MucCon.tai_lieu)
            .joinedload(TaiLieu.current_version)
        ).all()
        return categories

    def get_category_detail(self, dm_id: int) -> DanhMuc:
        category = self.db.query(DanhMuc).options(
            joinedload(DanhMuc.muc_con)
            .joinedload(MucCon.tai_lieu)
            .joinedload(TaiLieu.current_version)
        ).filter(DanhMuc.DM_ID == dm_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Danh mục không tồn tại")
        return category

    # =========================================================================
    # CÁC HÀM CRUD KHÁC (GIỮ NGUYÊN)
    # =========================================================================

    def _get_folder_id_for_upload(self, mc_id: int) -> str:
        project = self.db.query(MucCon).filter(MucCon.MC_ID == mc_id).first()
        if not project: raise HTTPException(404, detail="Dự án không tồn tại.")
        if not project.Share_Drive_Folder_ID: return "mock_folder_id" 
        return project.Share_Drive_Folder_ID

    def create_category(self, data: CategoryCreateRequest):
        folder_id = self.drive_service.create_folder(data.Ten_Danh_Muc, self.ROOT_DRIVE_ID)
        new_cat = DanhMuc(
            Ten_Danh_Muc=data.Ten_Danh_Muc,
            Share_Drive_Folder_ID=folder_id,
            Metadata={
                'ma_mau_hex': data.ma_mau_hex, 
                'icon_code': data.icon_code, 
                'phong_ban': data.phong_ban, 
                'phu_trach': data.phu_trach, 
                'ngay_ban_hanh': data.ngay_ban_hanh
            }
        )
        self.db.add(new_cat)
        self.db.commit()
        self.db.refresh(new_cat)
        return new_cat

    def create_project(self, data: ProjectCreateRequest):
        parent_cat = self.db.query(DanhMuc).filter(DanhMuc.DM_ID == data.DM_ID).first()
        if not parent_cat: raise HTTPException(404, "Danh mục cha không tồn tại.")
        
        folder_id = self.drive_service.create_folder(data.Ten_Du_An, parent_cat.Share_Drive_Folder_ID)
        
        new_project = MucCon(
            DM_ID=data.DM_ID,
            Ten_Muc_Con=data.Ten_Du_An,
            Ngay_Het_Hieu_Luc=data.Ngay_Het_Hieu_Luc,
            Share_Drive_Folder_ID=folder_id # Cột này giờ đã tồn tại ở Bước 1
        )
        self.db.add(new_project)
        self.db.commit()
        self.db.refresh(new_project)
        return new_project

    def _extract_drive_id_from_link(self, link: str) -> str:
        """Parse Google Drive ID từ full URL, nếu không phải Google Drive thì trả về link nguyên văn"""
        import re
        # Pattern cho Google Drive links
        patterns = [
            r'/d/([a-zA-Z0-9_-]+)',  # /d/FILE_ID
            r'id=([a-zA-Z0-9_-]+)',   # ?id=FILE_ID
            r'/folders/([a-zA-Z0-9_-]+)',  # /folders/FOLDER_ID
        ]
        
        for pattern in patterns:
            match = re.search(pattern, link)
            if match:
                return match.group(1)
        
        # Nếu không phải Google Drive link, trả về link nguyên văn
        return link
    
    def create_document_from_link(self, item_data):
        """Tạo tài liệu từ link (Google Drive, website, v.v.)"""
        # Nếu item không có ngày hết hạn, lấy từ dự án cha
        ngay_het_hieu_luc = item_data.Ngay_Het_Hieu_Luc
        if not ngay_het_hieu_luc:
            project = self.db.query(MucCon).filter(MucCon.MC_ID == item_data.MC_ID).first()
            if project:
                ngay_het_hieu_luc = project.Ngay_Het_Hieu_Luc
        
        # Parse ID từ link (nếu là Google Drive) hoặc giữ nguyên link
        drive_id_or_link = self._extract_drive_id_from_link(item_data.Share_Drive_Link)
        
        # Tạo phiên bản đầu tiên với link có sẵn
        new_version = PhienBanTaiLieu(
            So_Phien_Ban=1.0,
            Share_Drive_File_ID=drive_id_or_link,  # Lưu ID hoặc full link
            Ten_File_Tren_Drive=item_data.Ten_File_Tren_Drive,
            Ngay_Tai_Len=datetime.now(),  # Tự động set timestamp
            Metadata=FileMetadata(
                Ten_File_Goc=item_data.Ten_File_Tren_Drive,
                Loai_Tap_Tin="application/vnd.google-apps.file",
                Kich_Thuoc_Byte=0,
                Nguoi_Tai_Len_ID=1,
                original_link=item_data.Share_Drive_Link  # Lưu link gốc trong metadata
            ).dict()
        )
        self.db.add(new_version)
        self.db.flush()
        
        # Tạo item mới
        new_item = TaiLieu(
            MC_ID=item_data.MC_ID,
            Tieu_De=item_data.Tieu_De,
            Ngay_Het_Hieu_Luc=ngay_het_hieu_luc,
            Current_Version_ID=new_version.PB_ID,
            Metadata=item_data.Metadata.dict()
        )
        self.db.add(new_item)
        self.db.flush()
        
        new_version.TL_ID = new_item.TL_ID
        self.db.commit()
        self.db.refresh(new_item)
        return new_item

    async def create_new_document_item(self, item_data: TaiLieuCreate, version_data: PhienBanCreate, file_data: bytes):
        folder_id = self._get_folder_id_for_upload(item_data.MC_ID)
        file_id, file_name_on_drive = await self.drive_service.upload_file(file_data, folder_id, version_data.ten_file_goc, 1.0)
        
        # Nếu item không có ngày hết hạn, lấy từ dự án cha
        ngay_het_hieu_luc = item_data.Ngay_Het_Hieu_Luc
        if not ngay_het_hieu_luc:
            project = self.db.query(MucCon).filter(MucCon.MC_ID == item_data.MC_ID).first()
            if project:
                ngay_het_hieu_luc = project.Ngay_Het_Hieu_Luc
        
        new_version = PhienBanTaiLieu(
            So_Phien_Ban=1.0, Share_Drive_File_ID=file_id, Ten_File_Tren_Drive=file_name_on_drive,
            Ngay_Tai_Len=datetime.now(),  # Tự động set timestamp
            Metadata=FileMetadata(
                Ten_File_Goc=version_data.ten_file_goc, Loai_Tap_Tin=version_data.Loai_Tap_Tin,
                Kich_Thuoc_Byte=version_data.kich_thuoc_byte, Nguoi_Tai_Len_ID=version_data.Nguoi_Tai_Len_ID
            ).dict()
        )
        self.db.add(new_version)
        self.db.flush() 

        new_item = TaiLieu(
            MC_ID=item_data.MC_ID, 
            Tieu_De=item_data.Tieu_De,
            Ngay_Het_Hieu_Luc=ngay_het_hieu_luc,
            Current_Version_ID=new_version.PB_ID, 
            Metadata=item_data.Metadata.dict()
        )
        self.db.add(new_item)
        self.db.flush()
        
        new_version.TL_ID = new_item.TL_ID
        self.db.commit()
        return new_item

    async def update_new_version(self, tl_id: int, version_update: NewVersionRequest, file_data: bytes):
        current_item = self.db.query(TaiLieu).filter(TaiLieu.TL_ID == tl_id).first()
        if not current_item: raise HTTPException(404, "Tài liệu không tồn tại.")
        
        old_version = current_item.current_version
        old_version_num = float(old_version.So_Phien_Ban)
        new_version_num = float(int(old_version_num) + 1.0)
        
        root_filename = old_version.Metadata.get('Ten_File_Goc', old_version.Ten_File_Tren_Drive)
        root_name_base, _ = os.path.splitext(root_filename)
        _, new_file_ext = os.path.splitext(version_update.ten_file_goc)
        if not new_file_ext: new_file_ext = ""
        name_for_upload = f"{root_name_base}{new_file_ext}"

        try:
            old_drive_name = old_version.Ten_File_Tren_Drive
            base_drive, ext_drive = os.path.splitext(old_drive_name)
            await self.drive_service.rename_file(old_version.Share_Drive_File_ID, f"{base_drive}_ARCHIVED{ext_drive}")
        except: pass

        folder_id = self._get_folder_id_for_upload(current_item.MC_ID)
        file_id_new, file_name_on_drive_new = await self.drive_service.upload_file(file_data, folder_id, name_for_upload, new_version_num)

        new_version = PhienBanTaiLieu(
            TL_ID=tl_id, So_Phien_Ban=new_version_num, Share_Drive_File_ID=file_id_new, Ten_File_Tren_Drive=file_name_on_drive_new,
            Ngay_Tai_Len=datetime.now(),  # Tự động set timestamp
            Metadata=FileMetadata(
                Ten_File_Goc=root_filename, Loai_Tap_Tin=version_update.Loai_Tap_Tin,
                Kich_Thuoc_Byte=version_update.kich_thuoc_byte, Nguoi_Tai_Len_ID=version_update.Nguoi_Tai_Len_ID
            ).dict()
        )
        self.db.add(new_version)
        self.db.flush()
        current_item.Current_Version_ID = new_version.PB_ID
        self.db.commit()
        return new_version

    def update_version_from_link(self, tl_id: int, link_data):
        """Cập nhật phiên bản mới từ link (không upload file)"""
        current_item = self.db.query(TaiLieu).filter(TaiLieu.TL_ID == tl_id).first()
        if not current_item:
            raise HTTPException(404, "Tài liệu không tồn tại.")
        
        old_version = current_item.current_version
        old_version_num = float(old_version.So_Phien_Ban)
        new_version_num = float(int(old_version_num) + 1.0)
        
        # Parse ID từ link (nếu là Google Drive) hoặc giữ nguyên link
        drive_id_or_link = self._extract_drive_id_from_link(link_data.Share_Drive_Link)
        
        # Tạo phiên bản mới từ link
        new_version = PhienBanTaiLieu(
            TL_ID=tl_id,
            So_Phien_Ban=new_version_num,
            Share_Drive_File_ID=drive_id_or_link,
            Ten_File_Tren_Drive=link_data.Ten_File_Tren_Drive,
            Ngay_Tai_Len=datetime.now(),
            Metadata=FileMetadata(
                Ten_File_Goc=link_data.Ten_File_Tren_Drive,
                Loai_Tap_Tin="application/vnd.google-apps.file",
                Kich_Thuoc_Byte=0,
                Nguoi_Tai_Len_ID=1,
                original_link=link_data.Share_Drive_Link
            ).dict()
        )
        self.db.add(new_version)
        self.db.flush()
        current_item.Current_Version_ID = new_version.PB_ID
        self.db.commit()
        self.db.refresh(new_version)
        return new_version

    def delete_document(self, tl_id: int):
        """Xóa tài liệu trong Database và Google Drive"""
        # Lấy thông tin tài liệu cần xóa
        doc = self.db.query(TaiLieu).filter(TaiLieu.TL_ID == tl_id).first()
        if not doc:
            raise HTTPException(404, "Tài liệu không tồn tại.")
        
        # Xóa tất cả phiên bản file trên Google Drive
        versions = self.db.query(PhienBanTaiLieu).filter(PhienBanTaiLieu.TL_ID == tl_id).all()
        for version in versions:
            if version.Share_Drive_File_ID:
                self.drive_service.delete_file(version.Share_Drive_File_ID)
        
        # Xóa từ Database
        self.db.query(PhienBanTaiLieu).filter(PhienBanTaiLieu.TL_ID == tl_id).delete(False)
        self.db.query(PhanQuyenTruyCap).filter(PhanQuyenTruyCap.TL_ID == tl_id).delete(False)
        self.db.query(TaiLieu).filter(TaiLieu.TL_ID == tl_id).delete(False)
        self.db.commit()
        return {"message": "Đã xóa tài liệu khỏi Database và Google Drive"}
    def update_category(self, dm_id: int, data: CategoryUpdateRequest):
        cat = self.db.query(DanhMuc).filter(DanhMuc.DM_ID == dm_id).first()
        if not cat: raise HTTPException(404, "Danh mục không tồn tại")
        
        # Cập nhật DB
        cat.Ten_Danh_Muc = data.Ten_Danh_Muc
        # Update Metadata
        meta = cat.Metadata or {}
        if data.ma_mau_hex: meta['ma_mau_hex'] = data.ma_mau_hex
        if data.icon_code: meta['icon_code'] = data.icon_code
        cat.Metadata = meta
        
        # (Tùy chọn) Gọi Drive Service đổi tên Folder trên Drive nếu cần
        # await self.drive_service.rename_file(cat.Share_Drive_Folder_ID, data.Ten_Danh_Muc)

        self.db.commit()
        self.db.refresh(cat)
        return cat

    # --- XÓA DANH MỤC ---
    def delete_category(self, dm_id: int):
        """Xóa danh mục và toàn bộ dự án, tài liệu con trong Database và Google Drive"""
        cat = self.db.query(DanhMuc).filter(DanhMuc.DM_ID == dm_id).first()
        if not cat: raise HTTPException(404, "Danh mục không tồn tại")
        
        # Lấy tất cả dự án con
        projects = self.db.query(MucCon).filter(MucCon.DM_ID == dm_id).all()
        
        # Xóa tất cả file trong mỗi dự án trên Google Drive
        for project in projects:
            docs = self.db.query(TaiLieu).filter(TaiLieu.MC_ID == project.MC_ID).all()
            for doc in docs:
                versions = self.db.query(PhienBanTaiLieu).filter(PhienBanTaiLieu.TL_ID == doc.TL_ID).all()
                for version in versions:
                    if version.Share_Drive_File_ID:
                        self.drive_service.delete_file(version.Share_Drive_File_ID)
            
            # Xóa folder dự án trên Drive
            if project.Share_Drive_Folder_ID:
                self.drive_service.delete_file(project.Share_Drive_Folder_ID)
        
        # Xóa folder danh mục trên Drive
        if cat.Share_Drive_Folder_ID:
            self.drive_service.delete_file(cat.Share_Drive_Folder_ID)
        
        # Xóa từ Database (cascade sẽ tự xóa các con)
        self.db.delete(cat)
        self.db.commit()
        return {"message": "Đã xóa danh mục khỏi Database và Google Drive"}

    # --- SỬA DỰ ÁN ---
    def update_project(self, mc_id: int, data: ProjectUpdateRequest):
        proj = self.db.query(MucCon).filter(MucCon.MC_ID == mc_id).first()
        if not proj: raise HTTPException(404, "Dự án không tồn tại")
        
        proj.Ten_Muc_Con = data.Ten_Du_An
        if data.Ngay_Het_Hieu_Luc:
            proj.Ngay_Het_Hieu_Luc = data.Ngay_Het_Hieu_Luc
        # Cập nhật logic metadata tương tự Category nếu MucCon có Metadata
        
        self.db.commit()
        self.db.refresh(proj)
        return proj

    # --- XÓA DỰ ÁN ---
    def delete_project(self, mc_id: int):
        """Xóa dự án và toàn bộ tài liệu con trong Database và Google Drive"""
        proj = self.db.query(MucCon).filter(MucCon.MC_ID == mc_id).first()
        if not proj: raise HTTPException(404, "Dự án không tồn tại")
        
        # Xóa tất cả file trong dự án trên Google Drive
        docs = self.db.query(TaiLieu).filter(TaiLieu.MC_ID == mc_id).all()
        for doc in docs:
            versions = self.db.query(PhienBanTaiLieu).filter(PhienBanTaiLieu.TL_ID == doc.TL_ID).all()
            for version in versions:
                if version.Share_Drive_File_ID:
                    self.drive_service.delete_file(version.Share_Drive_File_ID)
        
        # Xóa folder dự án trên Drive
        if proj.Share_Drive_Folder_ID:
            self.drive_service.delete_file(proj.Share_Drive_Folder_ID)
        
        # Xóa từ Database (cascade sẽ tự xóa các con)
        self.db.delete(proj)
        self.db.commit()
        return {"message": "Đã xóa dự án khỏi Database và Google Drive"}

    # --- SỬA THÔNG TIN TÀI LIỆU (KHÔNG UP FILE MỚI) ---
    def update_document_metadata(self, tl_id: int, data: DocumentMetadataUpdate):
        doc = self.db.query(TaiLieu).filter(TaiLieu.TL_ID == tl_id).first()
        if not doc: raise HTTPException(404, "Tài liệu không tồn tại")

        doc.Tieu_De = data.Tieu_De
        if data.Ngay_Het_Hieu_Luc:
            doc.Ngay_Het_Hieu_Luc = data.Ngay_Het_Hieu_Luc
        
        # Cập nhật Metadata
        meta = doc.Metadata or {}
        meta['nha_cung_cap'] = data.nha_cung_cap
        meta['gia_tri_hd'] = data.gia_tri_hd
        meta['ngay_ban_hanh'] = data.ngay_ban_hanh
        meta['phong_ban'] = data.phong_ban
        meta['phu_trach'] = data.phu_trach
        # Giữ lại màu và icon cũ nếu không truyền lên
        doc.Metadata = meta
        
        # Cập nhật lại tên file gốc trong phiên bản hiện tại nếu đổi tên Tieu_De (Tùy chọn)
        
        self.db.commit()
        self.db.refresh(doc)
        return doc