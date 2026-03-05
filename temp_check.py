# temp_check.py

import os, sys
# Thêm thư mục gốc của project vào PYTHONPATH để Python tìm thấy app/
sys.path.append(os.path.dirname(os.path.abspath(__file__))) 

# Chỉ cố gắng import model bị lỗi
from app.models.document_model import PhanQuyenTruyCap

print("PhanQuyenTruyCap imported successfully!")