import xml.etree.ElementTree as ET

def parse_invoice_xml(xml_content):
    root = ET.fromstring(xml_content)
    
    # Hàm helper lấy text từ tag
    def get_tag(path, default="---"):
        node = root.find(f".//{path}")
        return node.text if node is not None else default

    # Bóc tách thông tin theo chuẩn Thông tư 78 (Hóa đơn điện tử)
    data = {
        "info": {
            "shdon": get_tag("shdon"), # Số hóa đơn
            "khdon": get_tag("khdon"), # Ký hiệu
            "tdlap": get_tag("tdlap"), # Ngày lập
        },
        "seller": {
            "ten": get_tag("tenNBan"),
            "mst": get_tag("mstNBan"),
            "dchi": get_tag("dchiNBan"),
        },
        "buyer": {
            "ten": get_tag("tenNMua"),
            "mst": get_tag("mstNMua"),
        },
        "amounts": {
            "thue_suat": get_tag("tsuat"),
            "tien_hang": float(get_tag("thtien", 0)),
            "tien_thue": float(get_tag("tthue", 0)),
            "tong_cong": float(get_tag("tgtttoan", 0)),
        },
        "items": [] # Có thể bóc thêm chi tiết từng mặt hàng nếu cần
    }
    return data