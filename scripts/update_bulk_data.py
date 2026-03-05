import sys
import os

# Thêm đường dẫn project vào sys.path để import được app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.repositories.folder_repo import FolderRepository
from app.db.repositories.employee_repo import EmployeeRepository
from app.services.folder_service import handover_folders
from app.services.drive_service import get_drive_service, remove_permission_by_email

# Dữ liệu bạn cung cấp (Tôi để vào biến string)
RAW_DATA = """
2024KH02BM	CÔNG TY CỔ PHẦN CHUYỂN PHÁT NHANH BÌNH MINH	Vương Cẩm Vân	0103068169
2024KH30FO	CÔNG TY TNHH FOTECO - HÀ NỘI	Nguyễn Lan Anh	0110222005
2024KH20	CÔNG TY CỔ PHẦN CV MEDIA	Hoàng Nhật Minh	0110296832
2024KH68	CÔNG TY CỔ PHẦN TƯ VẤN PHÁT TRIỂN ASANA	Hoàng Nhật Minh	0109394497
2024KH11	CÔNG TY TNHH BẤT ĐỘNG SẢN UPLAND	Đã dừng dịch vụ	0110064398
2024KH32AI	CÔNG TY CỔ PHẦN AIBOX	Đã dừng dịch vụ	0109481848
2024KH69	CÔNG TY CỔ PHẦN GIẢI PHÁP CHUYỂN ĐỔI SỐ THG	Nguyễn Thị Hồng	0109563064
2024KH109	CÔNG TY TNHH CÔNG NGHỆ VÀ ĐẦU TƯ VHTECH	Đã dừng dịch vụ	0110789919
2024KH13 +14	CÔNG TY CỔ PHẦN HANAMI GROUP	Hoàng Nhật Minh	0110622589
2024KH41	CÔNG TY TNHH THƯƠNG MẠI VÀ DỊCH VỤ MASTERY GROUP	Nguyễn Lan Anh	0110426584
2024KH51	CÔNG TY TNHH ASAHIKO VIỆT NAM	Nguyễn Thị Hồng	0110699006
2024KH72	CÔNG TY TNHH TƯ VẤN VÀ DỊCH VỤ LUẬT MINH LANG	Đã dừng dịch vụ	0110722294
2024KH83	CÔNG TY TNHH TƯ VẤN CÔNG NGHỆ SỐ NAM VIỆT	Trần Đình Khôi	0110760268
2024KH84	CÔNG TY TNHH DỊCH VỤ TƯ VẤN VIỆT ADS	Đã dừng dịch vụ	0110761624
2024KH93	CÔNG TY CỔ PHẦN PILATES STATION	Phùng Duy Anh	0109768294
2024KH94	CÔNG TY CỔ PHẦN Q.F.S	Phùng Duy Anh	0109376522
2024KH103	CÔNG TY TNHH CÂN ĐIỆN TỬ PRO VIỆT NAM 	Trần Thị Mai Phương	0105251353
2024KH103F	CTY CP GIẢI PHÁP VÀ CÔNG NGHỆ CÂN ĐIỆN TỬ PRO VN	Trần Thị Mai Phương	0109195685
2023HKD01	HỘ KINH DOANH ĐỖ ANH DŨNG	Đỗ Thị Hồng Nhung	0108571778
2023HKD02	HỘ KINH DOANH NGUYỄN THỊ HƯƠNG	Đỗ Thị Hồng Nhung	8071758605
2023HKD03	HỘ KINH DOANH NGUYỄN ANH TUẤN	Đỗ Thị Hồng Nhung	0101218563
2023HKD05	HỘ KINH DOANH PHÙNG THỊ NHUNG	Đã dừng dịch vụ	0108502245
2023KH001	CÔNG TY LUẬT TNHH APRA	Trần Đình Khôi	0108858925
2023KH020	CÔNG TY CỔ PHẦN THƯƠNG MẠI HAVA VIỆT NAM	Hoàng Nhật Minh	0110146393
2023KH019	CÔNG TY TNHH TMH ADS	Đã dừng dịch vụ	4900893988
2023KH012	CÔNG TY TNHH SẢN XUẤT VÀ PHÁT TRIỂN DUY NHẤT	Hoàng Nhật Minh	0109322044
2023KH036AZ	CÔNG TY TNHH VẠN THẠCH ĐẶC VIỆT NAM	Phùng Duy Anh_A to Z	0108152791
2023KH037AZ	CÔNG TY TNHH BẤT ĐỘNG SẢN CÔNG NGHIỆP A TO Z	Phùng Duy Anh_A to Z	3703139547
2023KH038AZ	CÔNG TY TNHH CÔNG NGHỆ ĐIỆN TỬ TEPUER VIỆT NAM	Phùng Duy Anh_A to Z	2301229012
2023KH039AZ	CÔNG TY TNHH THƯƠNG MẠI QUYÊN KÝ VIỆT NAM	Phùng Duy Anh_A to Z	1301122638
2023KH040AZ	CÔNG TY TNHH HENGTAI ENGINEERING	Đã dừng dịch vụ	2301255005
2023KH041AZ	CÔNG TY TNHH THÔNG MINH IDEAL	Đã dừng dịch vụ	2301174892
NOCODE1	CÔNG TY TNHH TRUYỀN THÔNG VÀ THƯƠNG MẠI DỊCH VỤ PHÙNG GIA	Đã dừng dịch vụ	0108048409
2023KH043AZ	CÔNG TY TNHH TẬP ĐOÀN DỊCH VỤ TƯ VẤN A TO Z	Nguyễn Lan Anh	0107494947
NOCODEAZ1	CÔNG TY TNHH HENGWEI ENGINEERING	Đã dừng dịch vụ	2301292102
2023KH030	CÔNG TY CỔ PHẦN DIVUVI VIỆT NAM	Nguyễn Thị Hồng	0108335918
2023KH035	CÔNG TY TNHH CHĂM SÓC SỨC KHỎE 3B SMILE	Đã dừng dịch vụ	0110520347
2023KH028	CÔNG TY TNHH THƯƠNG MẠI S&KV	Nguyễn Thị Hồng	0901031109
2023KH044AZ	CÔNG TY TNHH KHOA HỌC KỸ THUẬT HARMAN VIỆT NAM	Phùng Duy Anh_A to Z	0108924261
2024KH05	CÔNG TY TNHH TRUYỀN THÔNG SỰ KIỆN LYNCHA	Đã dừng dịch vụ	0110586531
2024KH06	CÔNG TY CỔ PHẦN THƯƠNG MẠI DỊCH VỤ DU LỊCH KỲ NGHỈ VIỆT NAM	Đã dừng dịch vụ	0104076130
2024KH48	CÔNG TY CỔ PHẦN TƯ VẤN VÀ QUẢN LÝ GIAO DỤC NORDIC EDU GLOBAL	Đã dừng dịch vụ	0110672477
2024KH97AZ	CÔNG TY TNHH THƯƠNG MẠI QUỐC MẠI QUỐC TẾ XINYING VIỆT NAM	Phùng Duy Anh_A to Z	0318516050
2024KH92	CÔNG TY CỔ PHẦN BẤT ĐỘNG SẢN JOYHOME	Trần Thị Mai Phương	0901152287
NOCODEAZ2	CÔNG TY TNHH XNK VÀ SẢN XUẤT YUNDUOZE	Đã dừng dịch vụ	2301270395
NOCODEAZ3	XƯỞNG SẢN XUẤT BÌNH XỊT MUỖI	Đã dừng dịch vụ	2301270395-001
NOCODE2	CÔNG TY TNHH ONUS STUDIO QUỐC TẾ	Đã dừng dịch vụ	0109190486
2023KH013	CÔNG TY TNHH THƯƠNG MẠI QUỐC TẾ VIỆT LÀO	Đã dừng dịch vụ	0109970510
2023KH016	CÔNG TY CP GUMA GAMES STUDIO	Hoàng Nhật Minh	0110159794
2023KH015	CÔNG TY TNHH HUNGHOMES	Nguyễn Thị Hồng	0110481377
2023KH022TN	CÔNG TY TNHH CÔNG NGHỆ TNP GLOBAL	Nguyễn Lan Anh	0110479956
2023KH023NT	CÔNG TY TNHH HUM HẠNH PHÚC NỘI TÂM	Nguyễn Thị Hồng	0110500710
2023KH027	CÔNG TY TNHH DỊCH VỤ TƯ VẤN SKY ADS	Đã dừng dịch vụ	0110499582
2023KH025	CÔNG TY CỔ PHẦN QUÀ TẶNG SỨC KHỎE 381	Đã dừng dịch vụ	0110485773
2023KH050	CÔNG TY TNHH GIẢI PHÁP DỊCH VỤ GODIVA	Đã dừng dịch vụ	0110473739
NOCODE3	CÔNG TY CỔ PHẦN THƯƠNG MẠI ĐẦU TƯ XÂY DỰNG BẮC Á	Trần Đình Khôi	0901105368
2023KH007	CÔNG TY TNHH THƯƠNG MẠI VÀ DỊCH VỤ WINECOM	Trần Đình Khôi	098 314 1636
2023KH008	CÔNG TY CỔ PHẦN NÔNG NGHIỆP VÀ PHÁT TRIỂN NÔNG THÔN VTH	Nguyễn Thị Hạnh	0110462127
2023KH022CL	CÔNG TY CỔ PHẦN TẬP ĐOÀN CLT	Nguyễn Thị Hạnh	0110486826
2023KH023CO	CÔNG TY CỔ PHẦN ĐÀO TẠO COACH 3S	Đã dừng dịch vụ	0901127587
2023KH024	CHI NHÁNH SỐ 01 THANH HÀ - CÔNG TY CỔ PHẦN ĐÀO TẠO COACH 3S	Đã dừng dịch vụ	0901127587-001
2024KH45	CÔNG TY TNHH GIẢI PHÁP DU LỊCH MEETUP	Đã dừng dịch vụ	0110691254
2024KH54	CÔNG TY TNHH ẨM THỰC DU LỊCH VÀ SỰ KIỆN NAM PHƯƠNG	Nguyễn Thị Hồng	0901160778
2024KH86	CÔNG TY TNHH NEMIN GROUP	Nguyễn Thị Hồng	0110749426
2024KH88	CÔNG TY CỔ PHẦN GIÁO DỤC VÀ CÔNG NGHỆ GROWDEMY	Đã dừng dịch vụ	0110767270
2024KH89	CÔNG TY CỔ PHẦN KINH DOANH VÀ ĐẦU TƯ PHÚC KHANG	Trần Đình Khôi	0110635926
2024KH90	CÔNG TY TNHH TM CÔNG NGHỆ TỔNG HỢP THẨM NAM	Đã dừng dịch vụ	0110779357
2024KH91	CÔNG TY TNHH ĐỨC THÀNH TRƯỜNG PHÁT	Đã dừng dịch vụ	0372229686
2024KH95	CÔNG TY CỔ PHẦN VIỆN DƯỠNG LÃO YÊN BÌNH	Đã dừng dịch vụ	4601619458
2024KH96	CÔNG TY CỔ PHẦN GIAO NHẬN VẬN TẢI QUỐC TẾ HAN	Hoàng Nhật Minh	0110765643
2024KH97	CÔNG TY TNHH DỊCH VỤ TRUYỀN THÔNG DH DIGI	Phùng Duy Anh	0110790953
2024KH98	CÔNG TY TNHH XUẤT NHẬP KHẨU THỦ CÔNG MỸ NGHỆ TRE VIỆT	Trần Đình Khôi	0976718996
2024KH99	CÔNG TY TNHH THƯƠNG MẠI KỸ THUẬT MINH TUỆ	Hoàng Nhật Minh	0110808840
2024KH102	CÔNG TY TNHH TRUYỀN THÔNG CINÉUS	Vương Cẩm Vân	0110786354
2024KH62	CÔNG TY CỔ PHẦN ALAN CAPITAL	Đã dừng dịch vụ	0110283791
2024KH30RA	CÔNG TY TNHH ĐẦU TƯ QUỐC TẾ RAYMOND	Đã dừng dịch vụ	0110325787
2024KH61	CÔNG TY CỔ PHẦN CÔNG NGHỆ M4U	Nguyễn Thị Hồng	0110673671
2024KH46	CÔNG TY TNHH SẢN XUẤT VÀ KINH DOANH DƯỢC PHẨM AN NHIÊN	Đã dừng dịch vụ	0110545528
2024KH42CG	CÔNG TY CỔ PHẦN ĐẦU TƯ VÀ PHÁT TRIỂN CONTRAST GROUP	Đã dừng dịch vụ	0110533226
2024KH31	CÔNG TY TNHH DC GROUP GLOBAL	Đã dừng dịch vụ	0110613520
2024KH47	CÔNG TY TNHH DINOSAURIZED	Đã dừng dịch vụ	3200741184
2024KH50	CÔNG TY TNHH BRANDIA VIETNAM	Nguyễn Lan Anh	0316808403
2024KH77	CÔNG TY TNHH TƯ VẤN BẢO HIỂM CHUYÊN NGHIỆP INSUPRO	Nguyễn Thị Hạnh	0110589620
2024KH76	CÔNG TY LK	Đã dừng dịch vụ	0110730369
2023KH033	CÔNG TY TNHH GIẢI PHÁP TRUYỀN THÔNG ĐẠI DƯƠNG XANH	Nguyễn Lan Anh	0107580219
2024KH23	CÔNG TY TNHH ĐẦU TƯ DU LỊCH HƯƠNG GIANG	Nguyễn Thị Hồng	0110182190
2023KH63	CÔNG TY CỔ PHẦN XUẤT NHẬP KHẨU HOÀNG GIA KHÁNH	Trần Đình Khôi	0107966847
2023KH64	CÔNG TY TNHH CƠ KHÍ TÂN LONG	Nguyễn Thị Hồng	0104130236
2024KH04	CÔNG TY CỔ PHẦN DA GIẦY XUẤT KHẨU HÀ NỘI	Nguyễn Thị Liên	0101698302
2024KH16	Công ty CP Công nghệ giáo dục YouthPlus	Đã dừng dịch vụ	0109890696
2024KH32IZ	CÔNG TY CỔ PHẦN GIẢI PHÁP THÔNG MINH IZZI CHÂU Á	Đã dừng dịch vụ	0107579365
2024KH65	Công ty TNHH dịch vụ ăn uống Miền Tây Bắc	Đã dừng dịch vụ	0109735309
2024KH42TT	CÔNG TY CỔ PHẦN ĐẦU TƯ VÀ PHÁT TRIỂN TỔNG HỢP TRƯỜNG THỊNH	Trần Đình Khôi	
2023KH41	CÔNG TY TNHH SẢN XUẤT ĐẦU TƯ VÀ THƯƠNG MẠI VIỆT ANH	Đã dừng dịch vụ	0110556022
2024KH104	CÔNG TY TNHH REDNET VIỆT NAM	Đã dừng dịch vụ	0110815358
2024KH105	CÔNG TY CỔ PHẦN BỌT KHÍ THỦY ĐỘNG LỰC VIỆT NAM	Trần Đình Khôi	0110807357
2024KTT03	CÔNG TY TNHH LADY ART	Đã dừng dịch vụ	
2024KH15	CÔNG TY CỔ PHẦN MÁY QUỐC TẾ SAVY	Trần Thị Mai Phương	0110625597
2024KH11 +12	CÔNG TY TNHH ĐẦU TƯ VÀ DỊCH VỤ VH LAND	Đã dừng dịch vụ	0110464156
2024KH49	CÔNG TY CỔ PHẦN CÔNG NGHỆ INTERNET CHIẾC Ô XANH	Trần Thị Mai Phương	0109980861
2024KH52	CÔNG TY TNHH ĐẦU TƯ VÀ THƯƠNG MẠI BẢO AN PHÁT	Trần Thị Mai Phương	0901160087
2024KH53	CÔNG TY TNHH ĐÀM HOUSE	Trần Thị Mai Phương	0110709624
2024KH55	CÔNG TY TNHH CƠ KHÍ, XÂY DỰNG, TM&DV HƯNG ĐẠI PHÁT	Trần Thị Mai Phương	2803115153
2024KH59	CÔNG TY TNHH SẢN XUẤT THƯƠNG MẠI VÀ DỊCH VỤ DANTECH	Trần Thị Mai Phương	0110720226
2023KH006	CÔNG TY TNHH GINNY HOUSE	Trần Thị Mai Phương	4601594443
2024KH03	CÔNG TY TNHH THƯƠNG MẠI VÀ DỊCH VỤ PINGALA	Đã dừng dịch vụ	0110591933
2023KH034	CÔNG TY TNHH ĐẦU TƯ XÂY DỰNG HUYỀN NHÀN	Trần Thị Mai Phương	2301263574
2024KH02BP	CÔNG TY CỔ PHẦN THƯƠNG MẠI VIỆT TÍN BPO	Đã dừng dịch vụ	0110014118
2024KH75	CÔNG TY TNHH TƯ VẤN GIÁO DỤC VÀ QL ĐÀO TẠO HÀ NỘI	Đã dừng dịch vụ	0110740173
2024KH71	CÔNG TY TNHH XÂY DỰNG VÀ CÔNG NGHỆ MINH PHÁT	Trần Thị Mai Phương	0109571259
2024KH80	CÔNG TY TNHH TƯ VẤN CHIẾN LƯỢC DELTA	Trần Thị Mai Phương	0110754930
2024KH81	CÔNG TY LUẬT TNHH MINH LANG VÀ CỘNG SỰ	Trần Thị Mai Phương	0109862145
2023KH010	CÔNG TY LUẬT TNHH NLP	Trần Thị Mai Phương	0110433782
2023KH003	CÔNG TY TNHH TRUYỀN THÔNG VÀ SẢN XUẤT ONUS	Trần Thị Mai Phương	0110504634
2023KH031	CÔNG TY TNHH PHÁT TRIỂN PHẦN MỀM FSC	Đã dừng dịch vụ	0110453972
2023KTT049	CÔNG TY TNHH DỊCH VỤ TƯ VẤN VÀ PHÁT TRIỂN TRUYỀN THÔNG	Trần Thị Mai Phương	0109431029
2024KH74	CÔNG TY CỔ PHẦN THIẾT KẾ XÂY DỰNG SƠN HOÀ	Nguyễn Thị Hồng	0110737607
2024KH106	CÔNG TY TNHH DỊCH VỤ KẾT NỐI SỐ QUỐC TẾ	Đỗ Thị Hồng Nhung	0110826102
2024KH108	CÔNG TY CỔ PHẦN VNTECH - VIỆN ĐÀO TẠO CÔNG NGHỆ VIỆT NAM	Nguyễn Lan Anh	0109512976
NOCODE4	CÔNG TY CỔ PHẦN FITNESS LIFE VIỆT NAM	Phùng Duy Anh	0108805497
2024KH100	CÔNG TY TNHH BAO BÌ KIẾN VÀNG	Trần Đình Khôi	0110114031
NOCODE5	VĨNH THỊNH ĐẠT	Phùng Duy Anh	3702757075
2024KH114	CÔNG TY CỔ PHẦN CÔNG NGHỆ SKYBULL VIỆT NAM	Đã dừng dịch vụ	0110162885
2024KH111	CÔNG TY TNHH TAIPEI CSP CHENGFA	Trần Thị Mai Phương	0110831367
2024KH113	CÔNG TY TNHH SẢN XUẤT, THƯƠNG MẠI VÀ DU LỊCH HỒNG KỲ	Đã dừng dịch vụ	0110838468
NOCODE6	CHI NHÁNH CÔNG TY CỔ PHẦN FITNESS LIFE VIỆT NAM TẠI NGHỆ AN	Phùng Duy Anh	0108805497-001
2024KH119	CÔNG TY CỔ PHẦN KIẾN TRÚC VÀ NỘI THẤT NẮNG DESIGN	Nguyễn Lan Anh	0110839817
2024KH120	CÔNG TY TNHH THƯƠNG MẠI DỊCH VỤ VÀ PHÁT TRIỂN TH	Đã dừng dịch vụ	0110844581
2024KH110	CÔNG TY TNHH 3T STONE VIỆT NAM	Đã dừng dịch vụ	0109003986
NOCODE7	CÔNG TY CỔ PHẦN DU LỊCH VÀ THƯƠNG MẠI DỊCH VỤ MINH AN	Nguyễn Thị Hồng	110835040
NOCODE8	CÔNG TY TNHH MTV ĐẦU TƯ ĐẠI HƯNG THỊNH	Phùng Duy Anh	0110843852
2024KH123	CÔNG TY TNHH THIÊN MỘC SAN	Đã dừng dịch vụ	0110844630
2024KH117	CÔNG TY TNHH BOSSX	Đã dừng dịch vụ	0110836319
2024KH124	CÔNG TY TNHH ĐẦU TƯ S.E.N	Vương Cẩm Vân	0110782712
NOCODE9	CÔNG TY TNHH KẾ TOÁN THUẾ VIỆT	Phùng Duy Anh	0107964871
NOCODE10	CÔNG TY CỔ PHẦN TẬP ĐOÀN GOLDEN SUN	Đã dừng dịch vụ	0109832302
NOCODE11	CÔNG TY TNHH THIÊN NHẬT HƯƠNG	Phùng Duy Anh	4601543223
2024KH116	CÔNG TY TNHH NỘI THẤT THĂNG LONG	Đã dừng dịch vụ	0110841157
2024KH127	CÔNG TY TNHH IMIND	Đã dừng dịch vụ	0110860417
2024KH128	CÔNG TY TNHH KHAI PHÓNG VÀ SÁNG TẠO LAC ACADEMY	Vương Cẩm Vân	0110802260
2024KH129	CÔNG TY CỔ PHẦN ĐẦU TƯ VÀ PHÁT TRIỂN DOANH NGHIỆP THANH NIÊN	Đã dừng dịch vụ	0110857862
2024KH130	CÔNG TY CỔ PHẦN DỊCH VỤ VÀ CUNG ỨNG NHÂN LỰC QUỐC TẾ SONA	Đã dừng dịch vụ	0110860953
2024KH131	CÔNG TY CỔ PHẦN TRUNG TÂM KẾT NỐI CỘNG ĐỒNG 3C VINA	Đã dừng dịch vụ	0110820439
2024KH132	CÔNG TY TNHH ĐẦU TƯ VÀ THƯƠNG MẠI NAM THUỶ	Vương Cẩm Vân	0110858827
2024KH133	CÔNG TY TNHH THƯƠNG MẠI VÀ DỊCH VỤ CÔNG NGHIỆP THÊU VI TÍNH QUANG TRUNG	Vương Cẩm Vân	0110865599
2024KH134	CÔNG TY TNHH SƠN SỬA ĐỒ GỖ NỘI THẤT	Vương Cẩm Vân	0110869508
2024KH136 	CÔNG TY TNHH TM&DV CÔNG NGHỆ TRẦN GIA	Đã dừng dịch vụ	0110877241
2024KH137	CÔNG TY TNHH THIẾT KẾ KIẾN TRÚC VÀ NỘI THẤT S SPACE	Đã dừng dịch vụ	0110850049
2024KH140	CÔNG TY TNHH THIẾT BỊ Y TẾ THẠNH PHÁT	Đã dừng dịch vụ	0110885933
2024KH138	CÔNG TY TNHH THƯƠNG MẠI, DỊCH VỤ VÀ ĐẦU TƯ AMG	Đã dừng dịch vụ	0110863231
2024KH139 	CÔNG TY TNHH NỘI THẤT VÀ DỊCH VỤ HÒA PHÁT	Đã dừng dịch vụ	0110872927
2024KH141	CÔNG TY CỔ PHẦN ĐẦU TƯ THƯƠNG MẠI BTP        	Nguyễn Thị Hồng	0110881826
2024KH142	CÔNG TY CỔ PHẦN NGƯỜI VIẾT MÃ	Đỗ Thị Hồng Nhung	0110888966
2024KH143	CÔNG TY CỔ PHẦN THƯƠNG MẠI HƯƠNG GIA PHÁT	Đỗ Thị Hồng Nhung	0110899196
2024KH144	CÔNG TY CỔ PHẦN XÂY DỰNG VÀ TM TIẾN ĐỒNG        	Trần Đình Khôi	0110901085
2024KH145	CÔNG TY TNHH GOH VIỆT NAM	Nguyễn Thị Hồng	0110898467
2024KH146	CÔNG TY CỔ PHẨN DỊCH VỤ TRUYỀN HÌNH TINH HOA VIỆT NAM	Nguyễn Thị Hồng	0110902956
2024KH148	CÔNG TY CỔ PHẦN CÔNG NGHỆ CENPAY	Trần Thị Mai Phương	0110068635
2024KH149	CÔNG TY TNHH HA COSMETICS VIỆT NAM	Đã dừng dịch vụ	0110906735
2024KH147	CÔNG TY TNHH NÔNG NGHIỆP SB VIỆT NAM	Đã dừng dịch vụ	0110904840
2024KH150	CÔNG TY TNHH DỊCH VỤ & THƯƠNG MẠI QUẢNG CÁO MẠNH HÙNG 	Trần Thị Mai Phương	0110906830
2024KH44	Công ty CP đầu tư xây dựng và thương mại HTV hà nội	Đã dừng dịch vụ	0110654439
2024KH58	CÔNG TY TNHH THƯƠNG MẠI LA HOUSE	Đã dừng dịch vụ	0110718883
2024KH66	Công ty cổ phần đào tạo MIS Việt Nam	Đã dừng dịch vụ	0108585643
2024KH67	Công ty cổ phần ứng dụng công nghệ mới An Bình	Đã dừng dịch vụ	0102931079
2024KH09	CÔNG TY TNHH THƯƠNG MẠI DỊCH VỤ CHÍNH HOA	Đã dừng dịch vụ	0110609098
2024KH32CH	CỬA HÀNG VĂN PHÒNG PHẨM CHÍNH HOA	Đã dừng dịch vụ	0103544121
2024KH151	CÔNG TY TNHH TM VÀ XD MINH ĐỨC M.E	Đỗ Thị Hồng Nhung	0110844609
2024KH152	CÔNG TY TNHH DU LỊCH TAHA TRAVEL	Đã dừng dịch vụ	0110902610
2024KH155	CÔNG TY TNHH ĐẦU TƯ GALACTICO	Vương Cẩm Vân	0110915507
2024KH153	CÔNG TY CỔ PHẦN DOANH NGHIỆP XÃ HỘI ƯỚC MƠ VÙNG BIÊN	Nguyễn Lan Anh	0110776155
2025KH001	CÔNG TY CỔ PHẦN DỊCH VỤ CAO THIẾT 	Đã dừng dịch vụ	0110917335
2025KH002	CÔNG TY TNHH HOMESWORLD TRAVEL VIETNAM	Vương Cẩm Vân	0110919389
2024KH156	CÔNG TY TNHH CTV SPARK	Trần Đình Khôi	0110869219
2024KH157	CÔNG TY TNHH ĐẦU TƯ CHIẾN LƯỢC NLP	Trần Thị Mai Phương	0110607693
2025KH003	CÔNG TY TNHH GIẢI PHÁP TRUYỀN THÔNG CYBER	Đã dừng dịch vụ	0110895353
2024KH42MP	CÔNG TY CỔ PHẦN TƯ VẤN VÀ GIẢI PHÁP BẤT ĐỘNG SẢN MINH PHÁT        	Đã dừng dịch vụ	0110890411
2025KH04	Cty Everymatch - GĐ Brain Minh	Trần Thị Mai Phương	0110947869
2025KH05	CÔNG TY CỔ PHẦN GIÁO DỤC VÀ CHĂM SÓC SỨC KHỎE 3 GỐC	Đã dừng dịch vụ	0110946079
2025KH06	CÔNG TY CỔ PHẦN TRUYỀN THÔNG TỔ CHỨC SỰ KIỆN VÀ DU LỊCH KỲ NGHỈ VIỆT	Trần Đình Khôi	0110943649
2025KH07	CÔNG TY CỔ PHẦN CÔNG NGHỆ ĐẠI THÀNH HN	Vương Cẩm Vân	0110991924
2025KH08	CÔNG TY CỔ PHẦN FAS GAMES	Đã dừng dịch vụ	0110984878
2025KH09	CÔNG TY TNHH LIFECORP	Đã dừng dịch vụ	0110984878
2025KH10	CÔNG TY TNHH LIFE PULSE	Đã dừng dịch vụ	0110882851
2025KH11	CÔNG TY TNHH THƯƠNG MẠI VÀ DỊCH VỤ MINH HOÀNG GROUP	Phùng Duy Anh	0110947410
2025KH12	CÔNG TY TNHH MAY XUẤT KHẨU G8	Vương Cẩm Vân	0111005860
2025KH13	HỘ KINH DOANH NHÀ THUỐC GIA HUY NCT	Đỗ Thị Hồng Nhung	0107945413-001
2025KH20	CÔNG TY TNHH DREAM UP	Vương Cẩm Vân	0111040992
2025KH21	CÔNG TY TNHH BỆ PHÓNG AI	Vương Cẩm Vân	0111058245
2025KH22	HỘ KINH DOANH TRẦN MỸ YÊN	Đã dừng dịch vụ	008093008973
2025KH15	CÔNG TY CỔ PHẦN TẬP ĐOÀN ĐẦU TƯ QUỐC TẾ DHT	Đã dừng dịch vụ	0110856058
2025KH23	CÔNG TY CỔ PHẦN THƯƠNG MẠI ĐIỆN TỬ IMSELLA GROUP	Hoàng Nhật Minh	0110844768
2025KH24	CÔNG TY CỔ PHẦN DOANH NGHIỆP XÃ HỘI ƯỚC MƠ VÙNG BIÊN - CN HÀ GIANG	Nguyễn Lan Anh	0110776155-001
2025KH25	CÔNG TY TNHH NADAL VIỆT NAM	Phùng Duy Anh	0107444255
2025KH26	CÔNG TY TNHH RAU CỦ QUẢ SẠCH TRANG NGÂN	Đỗ Thị Hồng Nhung	
2025KH27	CÔNG TY TNHH DREAM E-FULFILLMENT	Nguyễn Thị Hồng	0111157415
2025KH28	CÔNG TY TNHH TM & DV TỐNG GIA PHÁT	Trần Đình Khôi	2803177992
2025KH29BH	CÔNG TY TNHH VINPRINT	Nguyễn Thị Hồng	0319177298
2025KH30	CÔNG TY TNHH HUMOS FULFILLMENT	Nguyễn Thị Hồng	2401044449
2025KH31BH	CÔNG TY CỔ PHẦN CÔNG NGHỆ MATHON	Vương Cẩm Vân	0111233200
2025KH32BH	CÔNG TY TNHH GIẢI PHÁP CÔNG NGHỆ VNEXCO	Nguyễn Lan Anh	0111246344
2025KH33	CÔNG TY TNHH NƯỚC ĐÁ HOÀNG LONG	Hoàng Nhật Minh	0111235007
2025KH34	CÔNG TY CỔ PHẦN GIÁO DỤC QUỐC TẾ IMPACT	Vương Cẩm Vân	0109493681
2025KH35BH	CÔNG TY TNHH TT KẾT NỐI SỐ VCONECT	Nguyễn Thị Hồng	0319236659
2025KH36BH	CÔNG TY TNHH SUTRA LAB	Nguyễn Thị Hồng	0111222713
2025KH37	CÔNG TY CỔ PHẦN TƯ VẤN KẾT NỐI VÀ ĐẦU TƯ M.I.U	Hoàng Nhật Minh	0700876547
2025KH38	Công ty Xây dựng và MT Hoàng Huy	Nguyễn Lan Anh	0108872905
2025KH39	CÔNG TY TNHH IN ẤN DƯƠNG QUÂN	Trần Đình Khôi	0319283218
2025KH40XU	CÔNG TY TNHH EXTRAMILE	Nguyễn Thị Hạnh	0315873329
2025KH41XU	CÔNG TY TNHH TỨ MỸ LONG CÚC	Nguyễn Lan Anh	0319108907
2025KH42XU	CÔNG TY TNHH THƯƠNG MẠI XUẤT NHẬP KHẨU FSF	Hoàng Nhật Minh	0318956686
2025KH43DH	CÔNG TY TNHH MINH ANH KHÔI GIFT	Vương Cẩm Vân	0111287291
2025KH44	CÔNG TNHH QUẢNG CÁO VÀ THƯƠNG MẠI TẤN PHÁT	Trần Đình Khôi	2401048564
2025KH45	CÔNG TY CỔ PHẦN DỊCH VỤ XÂY DỰNG CƠ KHÍ NHƯ THÀNH	Nguyễn Lan Anh	0105808891
2025KH46DH	CÔNG TY TNHH CÁI NÀY HAY ĐẤY	Trần Đình Khôi	0319278916
2025KH47DH	CÔNG TY TNHH CON ONG THỢ	Nguyễn Thị Hạnh	0319270850
2025KH48DH	CÔNG TY TNHH CÔNG NGHỆ ĐIỆN MÁY NAM PHONG	Vương Cẩm Vân	0111297099
2025KH49	CÔNG TY TNHH THIẾT BỊ CÔNG NGHỆ HANC	Hoàng Nhật Minh	2301308947
2025KH50BH	CÔNG TY TNHH TƯ VẤN THIẾT KẾ XÂY DỰNG TRÍ NGUYỄN	Nguyễn Thị Hồng	3901375218
2025KH51	CÔNG TY TNHH THƯƠNG MẠI & VẬN TẢI PHOENIX	Hoàng Nhật Minh	4601656731
2025KH52DH	CÔNG TY TNHH NHẬT VƯỢNG JEANS 	Hoàng Nhật Minh	2301375454
2025KH53	Văn phòng đại diện Union Nifco Company Limited	Đỗ Thị Hồng Nhung	0109510016
2025KH55	Công ty TNHH Tư vấn thiết kế kiến trúc và nội thất Mộc Decor	Nguyễn Lan Anh	0111289531
2025KH56DH	CÔNG TY TNHH HAVENS	Hoàng Nhật Minh	2301376698
"""

folder_repo = FolderRepository()
employee_repo = EmployeeRepository()

# Cache nhân viên để đỡ query nhiều
employee_cache = {}

def get_employee_by_name_approx(name):
    """
    Tìm nhân viên theo tên.
    Logic:
    - Xóa các hậu tố như "_A to Z"
    - Tìm chính xác trước, nếu không thấy thì có thể log ra để check.
    """
    if not name: return None
    
    # Clean name
    clean_name = name.split("_")[0].strip() # Phùng Duy Anh_A to Z -> Phùng Duy Anh
    
    if clean_name in employee_cache:
        return employee_cache[clean_name]
    
    # Tìm trong DB (Giả sử repo có hàm tìm theo tên, hoặc phải get_all rồi lọc)
    # Ở đây tôi dùng cách lấy tất cả rồi lọc cho an toàn
    all_emps = employee_repo.get_all() # Nên tối ưu nếu db lớn
    
    for emp in all_emps:
        if emp['name'].lower() == clean_name.lower():
            employee_cache[clean_name] = emp
            return emp
            
    return None

def process_bulk_update():
    lines = RAW_DATA.strip().split("\n")
    service = get_drive_service()
    
    print(f"Bắt đầu xử lý {len(lines)} dòng dữ liệu...")
    
    for index, line in enumerate(lines):
        parts = line.split("\t")
        if len(parts) < 4:
            print(f"Skipping line {index}: Not enough columns")
            continue
            
        company_code = parts[0].strip()
        company_name = parts[1].strip()
        manager_raw = parts[2].strip()
        mst = parts[3].strip().replace('"', '') # Clean MST
        
        # 1. Tìm folder theo MST
        # Lưu ý: folder_repo cần có hàm tìm theo MST, nếu chưa có thì dùng logic filter
        # Giả sử hàm get_all trả về list dict
        existing_folders = [f for f in folder_repo.get_all() if f.get('mst') == mst]
        
        if not existing_folders:
            print(f"[{index}] Không tìm thấy Folder MST: {mst} - {company_name}")
            continue
            
        folder = existing_folders[0] # Lấy cái đầu tiên tìm thấy
        folder_id = folder['id']
        current_manager_id = folder.get('manager_employee_id')
        root_folder_id = folder.get('root_folder_id')

        # 2. Xử lý logic
        if manager_raw == "Đã dừng dịch vụ":
            if folder.get('status') != 'inactive':
                print(f"[{index}] STOPPING SERVICE: {company_name}")
                # A. Update DB
                folder_repo.update(folder_id, {"status": "inactive"})
                
                # B. Remove Permissions trên Drive (Nếu có folder)
                if root_folder_id:
                    # Cần tìm email nhân viên cũ để xóa quyền
                    if current_manager_id:
                        old_emp = employee_repo.get_by_id(current_manager_id)
                        if old_emp:
                            print(f"   -> Xóa quyền Drive của {old_emp['email']}")
                            remove_permission_by_email(service, root_folder_id, old_emp['email'])
        
        else:
            # Đây là nhân viên cụ thể
            new_emp = get_employee_by_name_approx(manager_raw)
            
            if not new_emp:
                print(f"[{index}] WARNING: Không tìm thấy nhân viên tên '{manager_raw}' trong DB")
                continue
                
            new_manager_id = new_emp['id']
            
            # Kiểm tra xem có cần chuyển quyền không
            if current_manager_id != new_manager_id:
                print(f"[{index}] HANDOVER: {company_name} -> {new_emp['name']}")
                
                # Gọi hàm Handover đã viết trước đó
                try:
                    handover_folders(current_manager_id, new_manager_id)
                    # Cập nhật lại status active nếu lỡ đang inactive
                    folder_repo.update(folder_id, {"status": "active"})
                except Exception as e:
                    print(f"   -> Lỗi Handover: {e}")
            else:
                 # Cùng người quản lý, đảm bảo status active
                 if folder.get('status') != 'active':
                      folder_repo.update(folder_id, {"status": "active"})

if __name__ == "__main__":
    process_bulk_update()