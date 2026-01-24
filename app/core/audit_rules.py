# app/core/audit_rules.py

# Định nghĩa vị trí folder tương ứng trên Drive để Robot biết đường đi tìm
CATEGORY_FOLDER_MAPPING = {
    "GTGT": "TAI-LIEU-THUE_{TENVT}/{Y}/GIA-TRI-GIA-TANG",
    "TNCN": "TAI-LIEU-THUE_{TENVT}/{Y}/THU-NHAP-CA-NHAN",
    "TNDN": "TAI-LIEU-THUE_{TENVT}/{Y}/THU-NHAP-DOA-NH-NGHIEP",
    "KT": "TAI-LIEU-THUE_{TENVT}/{Y}/KE-TOAN",
    "Hdon": "TAI-LIEU-CONG-TY_{TENVT}/{Y}/1-HOA-DON-MUA", # Hoặc cả Mua và Bán
    "Saoke": "TAI-LIEU-CONG-TY_{TENVT}/{Y}/4-SAO-KE-NGAN-HANG",
    "Luong": "TAI-LIEU-CONG-TY_{TENVT}/{Y}/5-LUONG",
    "HTK": "TAI-LIEU-CONG-TY_{TENVT}/{Y}/6-HANG-TON-KHO-VA-GIA-THANH"
}

# Danh mục checklist cho từng loại
DEFAULT_CHECKLISTS = {
    "GTGT": [
        {"id": "vat_xml_present", "task": "Có file XML Tờ khai", "is_auto": True},
        {"id": "vat_excel_present", "task": "Có file Excel Bảng kê", "is_auto": True},
        {"id": "vat_match_sum", "task": "Đối chiếu tổng tiền thuế XML vs Excel", "is_auto": True}
    ],
    "TNCN": [
        {"id": "pit_xml_present", "task": "Có file XML Tờ khai 05KK", "is_auto": True},
        {"id": "pit_match_payroll", "task": "Đối chiếu số thuế phải nộp vs Bảng lương", "is_auto": True}
    ],
    "TNDN": [
        {"id": "cit_temp_present", "task": "Có file XML Tạm tính 03 TNDN", "is_auto": True}
    ],
    "KT": [
        {"id": "nkc_balance", "task": "NKC cân đối (Nợ = Có)", "is_auto": True},
        {"id": "bctc_present", "task": "Có file BCTC", "is_auto": True}
    ],
    "Saoke": [
        {"id": "sk_continuity", "task": "Kiểm tra tính liên tục số dư các tháng", "is_auto": True},
        {"id": "sk_count", "task": "Đủ 12 file sao kê cho 12 tháng", "is_auto": True}
    ],
    "Luong": [
        {"id": "salary_match", "task": "Tổng lương thực nhận = Tổng chi trên sao kê", "is_auto": True},
        {"id": "salary_signed", "task": "Bảng lương đã có chữ ký/dấu", "is_auto": False} # Check tay
    ],
    "HTK": [
        {"id": "inv_balance", "task": "Nhập xuất tồn cân đối số lượng", "is_auto": True}
    ]
}

# app/core/audit_rules.py

DEFAULT_CHECKLISTS["TNDN"] = [
    {"id": "tndn_xml_present", "task": "Có file XML Tờ khai 03/TNDN", "is_auto": True},
    {"id": "tndn_excel_excluded_present", "task": "Có file Excel Danh sách chi phí loại", "is_auto": True},
    {"id": "tndn_match_b4", "task": "Đối chiếu Chỉ tiêu [B4] vs Tổng Excel", "is_auto": True},
    {"id": "tndn_check_mst", "task": "Kiểm tra MST trên tờ khai TNDN", "is_auto": True}
]