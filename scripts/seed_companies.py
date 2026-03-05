from app.core.database import SessionLocal

# 👉 DANH SÁCH CÔNG TY THẬT CỦA ANH
COMPANIES = [
    {
      "drive_folder_id": "1BnTLJiyPsSdN0kfRofbdSHhyD6iqTroL",
      "name": "2024KH04_DA-GIAY_0101698302"
    },
    {
      "drive_folder_id": "10rQrWZsj5-1NYj6jxMaxTB4Zsk36e3Ma",
      "name": "2023KH039AZ_QUYEN-KY-VIET-NAM_1301122638"
    },
    {
      "drive_folder_id": "1mm7cslXHJs8_oINKt1Plkzxq03dpsHl7",
      "name": "2024KH102_CINEUS_0110786354"
    },
    {
      "drive_folder_id": "1v8jX5M4rgQskfLmsaOuldS3vAZ-iwpqR",
      "name": "2024KH103_CAN-DIEN-TU-PRO_0105251353"
    },
    {
      "drive_folder_id": "1lX1V60Vrf7qI2ldsfuLT1xLKd9cZM7ci",
      "name": "2024KH124_DAU-TU-S.E.N_0110782712"
    },
    {
      "drive_folder_id": "101BqEzTzlFNy7cxkf_VLOsid43aWat36",
      "name": "2023KH012_DUY-NHAT_0109322044"
    },
    {
      "drive_folder_id": "1YHlO9Z6-tQFZXa-YGxv5OQgaKUUUF7Ax",
      "name": "2023KH006_GINNY-HOUSE_4601594443"
    },
    {
      "drive_folder_id": "19kQihMlXzFfZ-ihAoebQYwm7PACupQs_",
      "name": "2024KH71_MINH-PHAT_0109571259"
    },
    {
      "drive_folder_id": "1XnvwyVl8Ibh_DVwO4ndhhrkjh9YgJ5VS",
      "name": "2024KH105_BOT-KHI-THUY-DONG-LUC_0110807357"
    },
    {
      "drive_folder_id": "1txNKxtgdgdLwJyLbexY5_M30fHMFgZN6",
      "name": "2024KH30FO_FOTECO-HA-NOI_0110222005"
    },
    {
      "drive_folder_id": "1mv-ETqJ4LbPH8tQfdYQcijYIpW3bf5dP",
      "name": "2023KTT049_TU-VAN-PHAT-TRIEN-TRUYEN-THONG_0109431029"
    },
    {
      "drive_folder_id": "1z23b-u90Nqm3yFEWQ5AkVXSiCuFYDXTK",
      "name": "NOCODE8_DAI-HUNG-THINH_0110843852"
    },
    {
      "drive_folder_id": "1slC7x8tc2uEknIQYaBRIZ7Mf7l9oTI5E",
      "name": "2024KH111_TAIPEI-CSP-CHENGFA_0110831367"
    },
    {
      "drive_folder_id": "1A0O3p0O0derNliMNxV_bD0UF9VGXzjqN",
      "name": "2023KH037AZ_CONG-NGHIEP-A-TO-Z_3703139547"
    },
    {
      "drive_folder_id": "1b2BGZ-0fsyYg5LXw8ZqqI-iqB0myyM1i",
      "name": "2023KH016_GUMA-GAMES-STUDIO_0110159794"
    },
    {
      "drive_folder_id": "1Y7_7KPezZg2r1pJ87_jSsQ_Nutsc1gYr",
      "name": "2023KH028_SKV_0901031109"
    },
    {
      "drive_folder_id": "1-h9v88hTC4OBRlvkXgDj6gaoasDeRzGH",
      "name": "2024KH53_DAM-HOUSE_0110709624"
    },
    {
      "drive_folder_id": "1_KHEw0nl4paBSPVK0e5wQ0X1Nr1e_sF9",
      "name": "2023KH033_DAI-DUONG-XANH_0107580219"
    },
    {
      "drive_folder_id": "1Lh9embJn7RMvlE_8UvPzw-AT0Du_FYc6",
      "name": "2023KH64_TAN-LONG_0104130236"
    },
    {
      "drive_folder_id": "1nzOcdAMkqxpMh4LVvGVYu5U12k7FGS-_",
      "name": "2024KH86_NEMIN-GROUP_0110749426"
    },
    {
      "drive_folder_id": "11s0nfIy6dt76pqh6vi0Uvo_HiEclSB_0",
      "name": "2023KH010_LUAT-NLP_0110433782"
    },
    {
      "drive_folder_id": "1Ss_Z_zwVcH-Kg_QEc6Vj9J-yr4_fvi9w",
      "name": "NOCODE11_THIEN-NHAT-HUONG_4601543223"
    },
    {
      "drive_folder_id": "1GlV8ktTuvp6mayHZvXAjGmVR-_vjbYWQ",
      "name": "2024KH134_SON-SUA-DO-GO-NOI-THAT_0110869508"
    },
    {
      "drive_folder_id": "10D8dH4MBZTHPPdR6J6o1x40aaLGBgwrg",
      "name": "2024KH141_DAU-TU-BTP_0110881826"
    },
    {
      "drive_folder_id": "17HIF7xrAadwBoWi_MeJ6EGsivwsZQarg",
      "name": "2023KH034_HUYEN-NHAN_2301263574"
    },
    {
      "drive_folder_id": "1j-2I5VuNY8HoNxo92DmV4anhwRPjPDUn",
      "name": "NOCODE9_KE-TOAN-THUE-VIET_0107964871"
    },
    {
      "drive_folder_id": "1isilcMI3hIDr5G0WnKH4vHsulZY5zoBC",
      "name": "2024KH23_HUONG-GIANG_0110182190"
    },
    {
      "drive_folder_id": "1C3X1pEF_BNGjJDuzTV5eRfWh22jlJBwz",
      "name": "2023KH022TN_TNP-GLOBAL_0110479956"
    },
    {
      "drive_folder_id": "1cL47zieWrAh_eSUuR8484B_I4fB4aUhy",
      "name": "NOCODE4_FITNESS-LIFE_0108805497"
    },
    {
      "drive_folder_id": "1srDU0UyH3QLlTzdiIYfT3SCHPuUpVpEH",
      "name": "2024KH52_BAO-AN-PHAT_0901160087"
    },
    {
      "drive_folder_id": "1hR_ypGG810qLVf5NzwkHBQK2l9kmMDPc",
      "name": "2024KH119_NANG-DESIGN_0110839817"
    },
    {
      "drive_folder_id": "1W7wUil_tYV3n5tiUTna5xqnZtB-Yy6c_",
      "name": "NOCODE7_DU-LICH-MINH-AN_110835040"
    },
    {
      "drive_folder_id": "1hLhrZW8yd0HQJgaShNgLvgBoT_DxsKlB",
      "name": "NOCODE3_BAC-A_0901105368"
    },
    {
      "drive_folder_id": "1fAhXIx7Pul3Ga0P16zlkAtajTetiZLtk",
      "name": "2024KH49_CHIEC-O-XANH_0109980861"
    },
    {
      "drive_folder_id": "1mmo3RpYftQd-KdakPRBtum1pYcaDD-Q9",
      "name": "2024KH93_PILATES-STATION_0109768294"
    },
    {
      "drive_folder_id": "12CCvIiheQ5D8aufwj5bGdcUqEoY_aykJ",
      "name": "2024KH13-VA-14_HANAMI-GROUP_0110622589"
    },
    {
      "drive_folder_id": "1_NiAXPX_qsyEYc0DFTEd2bs5Ukn-m3lQ",
      "name": "2024KH106_KET-NOI-SO-QUOC-TE_0110826102"
    },
    {
      "drive_folder_id": "1wwJvbr4YiX6V2WWCBILuuc4Qb1MN6L8i",
      "name": "2024KH55_HUNG-DAI-PHAT_2803115153"
    },
    {
      "drive_folder_id": "1ks-7KbMVcyJV1FGVVu6xxIC6aamwM-BZ",
      "name": "2024KH81_LUAT-MINH-LANG-VA-CONG-SU_0109862145"
    },
    {
      "drive_folder_id": "1AI-HMmrouDFKw-w-0VCNF_KWyF4kKrBY",
      "name": "2024KH42TT_TRUONG-THINH_0107966847"
    },
    {
      "drive_folder_id": "1HiDvIjQIM6NhzTitPdD8sh43GiTP-Zm0",
      "name": "2024KH54_NAM-PHUONG_0901160778"
    },
    {
      "drive_folder_id": "1AYyBs8nSIK5Z0zIvJVeJ-dRZX8kvthIZ",
      "name": "2024KH96_QUOC-TE-HAN_0110765643"
    },
    {
      "drive_folder_id": "1vbxo9b2Fx50cHp8wPYovAOJSl3d-iL-V",
      "name": "2024KH74_SON-HOA_0110737607"
    },
    {
      "drive_folder_id": "1PFGZXDB2cwKvdMAWkUjkPxNU8wYIvRSF",
      "name": "2023KH043AZ_TAP-DOAN-TU-VAN-A-TO-Z_0107494947"
    },
    {
      "drive_folder_id": "1WJMasIS5f6fbxKk_62DKz8kcz8d_FwBC",
      "name": "2024KH02BM_CHUYEN-PHAT-NHANH-BINH-MINH_0103068169"
    },
    {
      "drive_folder_id": "1RtCnVSpPWJeR5kkdfP3Ln8hSInavDw4l",
      "name": "2024KH133_THEU-VI-TINH-QUANG-TRUNG_0110865599"
    },
    {
      "drive_folder_id": "1SkplVfK9h7QWL43LpnyPADBK00U6ZQaH",
      "name": "2024KH103F_CONG-NGHE-CAN-DIEN-TU-PRO-VN_0109195685"
    },
    {
      "drive_folder_id": "1W0rB7hzcqnwOxla9CnjWXXiyO63dqTiN",
      "name": "2024KH41_MASTERY-GROUP_0110426584"
    },
    {
      "drive_folder_id": "1m6e9xT9rJMu-MUJJ3TZSvChxSQ6gqA1C",
      "name": "2024KH98_TRE-VIET_0110795278"
    },
    {
      "drive_folder_id": "1Sv-2Y7P4a_CDo9g5HPw4dKcCRtg2_dJJ",
      "name": "2023KH023NT_HUM-HANH-PHUC-NOI-TAM_0110500710"
    },
    {
      "drive_folder_id": "1ut-e5IoJRZv03HNuhVDx3TIGAK48lzsF",
      "name": "2024KH89_PHUC-KHANG_0110635926"
    },
    {
      "drive_folder_id": "1sWzYprLh2wbETE_ahS9NGHmfPB3CqaWU",
      "name": "NOCODE5_VINH-THINH-DAT_3702757075"
    },
    {
      "drive_folder_id": "18RJ6WsE9nSJj8E8RhD3ByNjjVicA4xtb",
      "name": "NOCODE6_FITNESS-LIFE-NGHE-AN_0108805497-001"
    },
    {
      "drive_folder_id": "1iLUTBY_nda96KWzpsKmubTAVufsD6Nm9",
      "name": "2024KH97_DH-DIGI_0110790953"
    },
    {
      "drive_folder_id": "18lfrMzqgPSlR2JOyKP-DmNRa1OKkJZAt",
      "name": "2024KH132_NAM-THUY_0110858827"
    },
    {
      "drive_folder_id": "1wQGb3sLO4pHNzL57_nhge0Erw6sSrK-n",
      "name": "2024KH128_LAC-ACADEMY_0110802260"
    },
    {
      "drive_folder_id": "1NXGqL25xpKH0vEHZaJ92oDjuv7GV7E-f",
      "name": "2024KH83_NAM-VIET_0110760268"
    },
    {
      "drive_folder_id": "1rATWtL_AKy6lTiA9E7yWBQfxL9KNe__L",
      "name": "2024KH99_MINH-TUE_0110808840"
    },
    {
      "drive_folder_id": "1hw1vZmXeHKFAty9Nk7Sb2Bx9M2QM-BpP",
      "name": "2024KH20_CV-MEDIA_0110296832"
    },
    {
      "drive_folder_id": "1U2GTELSGqNW35GWbuS5pukwtoXNao9vB",
      "name": "2023KH036AZ_VAN-THACH-DAC_0108152791"
    },
    {
      "drive_folder_id": "1EcY0UVmYwPO-ioOAPIepliIKJQpvejq7",
      "name": "2023KH63_HOANG-GIA-KHANH_0104079974"
    },
    {
      "drive_folder_id": "1UX25nSvEuJ7_6khtUfqnm6ZrZWx68Kzq",
      "name": "2024KH100_BAO-BI-KIEN-VANG_0110114031"
    },
    {
      "drive_folder_id": "10WYKkxlDZWJvtesvZzlpuGCldQzIVI1_",
      "name": "2023KH001_LUAT-APRA_0108858925"
    },
    {
      "drive_folder_id": "1soThSAAicIGN9KT4f1g4ctEtsg8ah0Q0",
      "name": "2025KH002_HOMESWORLD-TRAVEL_0110919389"
    },
    {
      "drive_folder_id": "16yh-0rqJdBfCnCP7d8PuhUhF-FCOY5NC",
      "name": "2024KH95_DUONG-LAO-YEN-BINH_4601619458"
    },
    {
      "drive_folder_id": "1XvtL0bmv9xJNr4PYFOfLngJbAxc91MkH",
      "name": "2025KH26_RAU-CU-QUA-SACH-TRANG-NGAN_0111092976"
    },
    {
      "drive_folder_id": "1UbJ0wKR5WccX6flHmEOpoYyWx5YuKmBU",
      "name": "2025KH28_TONG-GIA-PHAT_2803177992"
    },
    {
      "drive_folder_id": "10ZudRScZwhDEmIc3bFKXJg9QNJq29l5v",
      "name": "2023KH031_PHAN-MEM-FSC_110453972"
    },
    {
      "drive_folder_id": "1eAS22RQe5oq__9HbBHT1FwIp4opYXgqk",
      "name": "2025KH34_GIAO-DUC-QUOC-TE-IMPACT_0109493681"
    },
    {
      "drive_folder_id": "16Xv7kWlPXVIfIBJGSyuq_3s0Ma7F5Zmg",
      "name": "2024KH06_KY-NGHI-VIET-NAM_104076130"
    },
    {
      "drive_folder_id": "1mrB2wPLsa84o0333pZagDlE_cfbzd850",
      "name": "2024KH110_3T-STONE_109003986"
    },
    {
      "drive_folder_id": "1zpfdcjE_zGB9t_adpEdtxcMjB4VhYg-2",
      "name": "2025KH48DH_DIEN-MAY-NAM-PHONG_0111297099"
    },
    {
      "drive_folder_id": "1WnjXIu7QR_8mUvd6fPNLikBCTiRIuinF",
      "name": "NOCODE1_PHUNG-GIA_108048409"
    },
    {
      "drive_folder_id": "1jB3I0A2wagY55S1Ic_jb6hSziiGBp-Z7",
      "name": "2024KH16_YOUTHPLUS_109890696"
    },
    {
      "drive_folder_id": "1SmUSFTNAPxucS09EdW0Zt0ig5iiZNmEg",
      "name": "2023KH041AZ_THONG-MINH-IDEAL_2301174892"
    },
    {
      "drive_folder_id": "1xVU0gejYHXZLJpGbu00BqQI6rh-8fqiT",
      "name": "2025KH21_BE-PHONG-AI_0111058245"
    },
    {
      "drive_folder_id": "12zmkAkJW7ApERmFIkKqpXAgIzc8mXtvK",
      "name": "2024KH114_SKYBULL-VIET-NAM_110162885"
    },
    {
      "drive_folder_id": "1qU8Xep5qumio3JXSAdLVRZ3TfwvKU8xw",
      "name": "2023KH035_3B-SMILE_110520347"
    },
    {
      "drive_folder_id": "1gbQQlpTl9cHlpPw2sC5VUcvCR2H3nu-U",
      "name": "2025KH38_MT-HOANG-HUY_0108872905"
    },
    {
      "drive_folder_id": "1N2rU2cp_Yp-xchbtMWJUNau1ZYE31dFt",
      "name": "2025KH24_UOC-MO-VUNG-BIEN-CN-HA-GIANG_0110776155-001"
    },
    {
      "drive_folder_id": "1hgOqZI9reTT4bG2KKBDsKI9tdKtrdfwH",
      "name": "2024KH90_THAM-NAM_110779357"
    },
    {
      "drive_folder_id": "1zg3jg3mSkV4LNU-kSxSO6lYcG3qHpzXi",
      "name": "2024KH42CG_CONTRAST-GROUP_110533226"
    },
    {
      "drive_folder_id": "1qSA97jNNcaiiWGrwyyvLlavyXLO5LOCC",
      "name": "2024KH46_AN-NHIEN_110545528"
    },
    {
      "drive_folder_id": "1lZyzK4TXPWm-n2Hnud4v2yXQRBLIs0gq",
      "name": "2024KH151_MINH-DUC-M.E_0110844609"
    },
    {
      "drive_folder_id": "1IaWGdCS8eavZetIQXCn-7l-_PqvExGjl",
      "name": "2023KH023CO_COACH-3S_901127587"
    },
    {
      "drive_folder_id": "1EsR5M5Ign4d5mV8qyyOavcvQ7O5nITUP",
      "name": "2023KH019_TMH-ADS_4900893988"
    },
    {
      "drive_folder_id": "1cGntKfwYQ79o6wz-TUJd1Sm4awcmTd9W",
      "name": "2024KH150_DICH-VU-QUANG-CAO-MANH-HUNG_0110906830"
    },
    {
      "drive_folder_id": "1QPeYt3wngDPgsot-p5eqBMjBJ8y_UYWr",
      "name": "2025KH44_QUANG-CAO-TAN-PHAT_2401048564"
    },
    {
      "drive_folder_id": "1LoUp-ztq8uvdy09hWGePZyMNkiazN7GV",
      "name": "2023KH41_VIET-ANH_110556022"
    },
    {
      "drive_folder_id": "1POl2hEy7SJJbt0FbsHwKLOzqVBnyYRs4",
      "name": "NOCODEAZ1_HENGWEI-ENGINEERING_2301292102"
    },
    {
      "drive_folder_id": "1owr9ozLFeunMmA_i-MNeOZSSVHnH0DVn",
      "name": "2024KH11-VA-12_VH-LAND_110464156"
    },
    {
      "drive_folder_id": "1AVvkBzGOKf0V7X8_uLluksW_4cYGLOP6",
      "name": "2024KH84_VIET-ADS_110761624"
    },
    {
      "drive_folder_id": "1IHJrISuA7khhnZdptSEGsr6vr-8nNcyN",
      "name": "2025KH42XU_XUAT-NHAP-KHAU-FSF_0318956686"
    },
    {
      "drive_folder_id": "195tQw6FOuZ9jZxCwZJfJaDTl9-E1RYTn",
      "name": "2024KH91_DUC-THANH-TRUONG-PHAT_372229686"
    },
    {
      "drive_folder_id": "1g9pM4tkYLv71k3V3qnPoU9pmD3jt1R4b",
      "name": "2024KH143_HUONG-GIA-PHAT_0110899196"
    },
    {
      "drive_folder_id": "1cKggH3_sHpkkLdLPJDh7RBtsV-TUrDha",
      "name": "2024KH142_NGUOI-VIET-MA_0110888966"
    },
    {
      "drive_folder_id": "1zUgjowb7WJG0-RQrYfStyAlo3bH_u5BL",
      "name": "2024KH65_MIEN-TAY-BAC_109735309"
    },
    {
      "drive_folder_id": "1lmuyU2cPGyfd7CfDWbDlbpC9g6AhNC2q",
      "name": "2024KH146_TRUYEN-HINH-TINH-HOA_0110902956"
    },
    {
      "drive_folder_id": "15saEA1Y7wbMDbVbiapqHlhQ7OUTOhIBI",
      "name": "2023KH013_QUOC-TE-VIET-LAO_109970510"
    },
    {
      "drive_folder_id": "1vxbBH0mw3O9X9GbCt4TiAO3-ilr0uGF3",
      "name": "2025KH30_HUMOS-FULFILLMENT_2401044449"
    },
    {
      "drive_folder_id": "1l9HTkzJUwE8lLfvou16ICXihYqkFxujl",
      "name": "2024KH104_REDNET-VIET-NAM_110815358"
    },
    {
      "drive_folder_id": "1UFGd1tNuht-7G4Cz_gznYN4LQGiPIQvp",
      "name": "2024KH153_UOC-MO-VUNG-BIEN_0110776155"
    },
    {
      "drive_folder_id": "1aeqTQi6TGxKEtVQ5kbaPRlKkrIQdpnk9",
      "name": "2025KH37_TU-VAN-KET-NOI-VA-DAU-TU-M.I.U_0700876547"
    },
    {
      "drive_folder_id": "1OGLDH6Fz18GHnM13vEnyODnQ6avdAv1Q",
      "name": "2024KH156_CTV-SPARK_0110869219"
    },
    {
      "drive_folder_id": "1u2uLWJCUqrwy3OU3q-R7VxNxU8_v3Ebc",
      "name": "2023KH040AZ_HENGTAI-ENGINEERING_2301255005"
    },
    {
      "drive_folder_id": "1LyB9jBLuSV-h_qbSDR_jrEFjLq4MRyzm",
      "name": "2025KH33_NUOC-DA-HOANG-LONG_0111235007"
    },
    {
      "drive_folder_id": "1ogXRSiysztA-_HpVmZOCyqk4CNAtfxdO",
      "name": "2024KH144_TIEN-DONG_0110901085"
    },
    {
      "drive_folder_id": "1Mv6PE1NVW8yO5pMESvzIiTjbNrkcHJzX",
      "name": "2025KH49_THIET-BI-CONG-NGHE-HANC_2301308947"
    },
    {
      "drive_folder_id": "1QYbfTXGI1fAUZbnwejazgpQpoB2EeklY",
      "name": "2025KH46DH_CAI-NAY-HAY-DAY_0319278916"
    },
    {
      "drive_folder_id": "1PzbmMY02XRXX6CJ_MLIwbMo-ufpWy5Ob",
      "name": "2024KH31_GROUP-GLOBAL_110613520"
    },
    {
      "drive_folder_id": "1M1shAf3h1d2x0DHAql4sah7PMeX64-xE",
      "name": "2024KTT03_LADY-ART_TAMNGUNGKDTU22-01-2025-21-01-2026"
    },
    {
      "drive_folder_id": "12A8hm-N5QLYDv3bSg_oO-fhCK6NCqFMk",
      "name": "2025KH39_TUAN-TANG_4601654043"
    },
    {
      "drive_folder_id": "1X7cgczriKHhmi0s8hl8dnC7IkNd6jWaE",
      "name": "2024KH62_ALAN-CAPITAL_110283791"
    },
    {
      "drive_folder_id": "1wuJb53qEus7Y0DV94eJJwm3ekigncLTu",
      "name": "2025KH43DH_MINH-ANH-KHOI-GIFT_0111287291"
    },
    {
      "drive_folder_id": "1XATDVhT4oWFoRQ7x0eIWPm49oeLKHF3x",
      "name": "2025KH36BH_SUTRA-LAB_0111222713"
    },
    {
      "drive_folder_id": "1Ay2yK_c_bLK56XTu-qjKHIHlLNDu-ExW",
      "name": "2023KH027_SKY-ADS_110499582"
    },
    {
      "drive_folder_id": "1-SWpvt9PHaZSBET-Eq7vFGRQ9W0trs7K",
      "name": "2025KH12_MAY-XUAT-KHAU-G8_0111005860"
    },
    {
      "drive_folder_id": "1ntPW1bgJ7U-g6PPkI3CIRGNqv3NNgRLL",
      "name": "2024KH113_HONG-KY_110838468"
    },
    {
      "drive_folder_id": "1tdHX02vnIBVGrNYqtwH62wSZwyDFLYsa",
      "name": "NOCODEAZ3_XNK-VA-SAN-XUAT-YUNDUOZE_2301270395-001"
    },
    {
      "drive_folder_id": "1zrF6cy9bky_kmQBWmlUTp7dqWFsJATop",
      "name": "2024KH148_CONG-NGHE-CENPAY_0110068635"
    },
    {
      "drive_folder_id": "1vvjV-fcARbZOiIkRBcunHO3qDFAaD3Yk",
      "name": "2023KH024_DAO-TAO-COACH-3S_0901127587-001"
    },
    {
      "drive_folder_id": "1C7CmlHh8bXpEnz8oxK6OM05azR63sZ2m",
      "name": "2025KH06_KY-NGHI-VIET_0110943649"
    },
    {
      "drive_folder_id": "1D0ZYxaAdC4Wh8VPjYhLSbN4Ipq6YU3va",
      "name": "2025KH45_XAY-DUNG-CO-KHI-NHU-THANH_0105808891"
    },
    {
      "drive_folder_id": "1OcST8XvNkY16eU8RjIADRBBEPzGkyF-m",
      "name": "2024KH02BP_VIET-TIN-BPO_110014118"
    },
    {
      "drive_folder_id": "150R_rTq0KGydF3_HZo7vRn4vrqYdTGtt",
      "name": "2024KH75_TU-VAN-GIAO-DUC-VA-QL-DAO-TAO_110740173"
    },
    {
      "drive_folder_id": "1hISkXMrry60LknQMSAh1KYmYVaKzgAOT",
      "name": "2024KH48_NORDIC-EDU-GLOBAL_110672477"
    },
    {
      "drive_folder_id": "1CfKFJA1bpeJSVhZavjZ8ptyrR_F-sjTS",
      "name": "2025KH07_CONG-NGHE-DAI-THANH_0110991924"
    },
    {
      "drive_folder_id": "15WXtLnlNEzdwqLiDZxX73r9apKqQYTBZ",
      "name": "2024KH145_GOH-VIET-NAM_0110898467"
    },
    {
      "drive_folder_id": "1jPoM4ghOQJ3Jb38fV2nC094A7Phm08mZ",
      "name": "NOCODE10_GOLDEN-SUN_109832302"
    },
    {
      "drive_folder_id": "1ojBnlzgBJD8TddITauXksDzPvvOmHHYS",
      "name": "2025KH10_LIFE-PULSE_0110882851"
    },
    {
      "drive_folder_id": "1ECMy357BVw_3PR5kTektHGSCuGepjYJr",
      "name": "2024KH123_THIEN-MOC-SAN_110844630"
    },
    {
      "drive_folder_id": "1AnSu5jmqMEGx_gipKz0DUZmU1yEqjCJb",
      "name": "2024KH155_DAU-TU-GALACTICO_0110915507"
    },
    {
      "drive_folder_id": "1Cdz1RZa_AjmIgercR20I1SYIZdvXKwcN",
      "name": "2025KH11_MINH-HOANG-GROUP_0110947410"
    },
    {
      "drive_folder_id": "1XaI04Db6St0DgCsSvu9judCzNtonLzPI",
      "name": "2024KH32IZ_IZZI-CHAU-A_107579365"
    },
    {
      "drive_folder_id": "1cInSZpExc33ycjPl-_sHjdYvGp5g6Y0B",
      "name": "2024KH72_LUAT-MINH-LANG_110722294"
    },
    {
      "drive_folder_id": "1Isam1YKWz48DKB45bndnC3N_bmIIE32j",
      "name": "2025KH23_DIEN-TU-IMSELLA-GROUP_0110844768"
    },
    {
      "drive_folder_id": "1ozu78XDxEkuS4a8u-TcuO0gnBx3uzxZ_",
      "name": "2025KH41XU_TU-MY-LONG-CUC_0319108907"
    },
    {
      "drive_folder_id": "1fTNyFbcw6MPxf89l49P1lOaUfLQYllAd",
      "name": "2025KH27_DREAM-E-FULFILLMENT_0111157415"
    },
    {
      "drive_folder_id": "1MC5-3w-oW8518JyJMuCmEH25YJkveca2",
      "name": "2025KH20_DREAM-UP_0111040992"
    },
    {
      "drive_folder_id": "1CCOKCrboro6DHqcqXoEHxk1aSQX8k7AJ",
      "name": "2024KH157_DAU-TU-CHIEN-LUOC-NLP_0110607693"
    },
    {
      "drive_folder_id": "1SMFHzH2VkbOslLhaFpC5qzFuYqfaMtJA",
      "name": "NOCODE2_ONUS-STUDIO-QUOC-TE_109190486"
    },
    {
      "drive_folder_id": "1wYgovMJ_4uwGYlyA6xGgv__OHxCeqQa3",
      "name": "2025KH47BH_CON-ONG-THO_0319270850"
    },
    {
      "drive_folder_id": "1nRBSvbwDeWqUjSD8HLTf9b0DHhxJKfRd",
      "name": "2024KH131_3C-VINA_110820439"
    },
    {
      "drive_folder_id": "1jllbY6kFqP1CYZ5-N953djwPpRvWhFhb",
      "name": "2024KH44_HTV-HA-NOI_110654439"
    },
    {
      "drive_folder_id": "1XCPiy4sSt-xoUSjuSK1hgqfz2qgxkLNj",
      "name": "2024KH32CH_VAN-PHONG-PHAM-CHINH-HOA_103544121"
    },
    {
      "drive_folder_id": "1GCuGGljVTvX2SmUnItMpq22ktqYXQ8N0",
      "name": "2024KH136_TRAN-GIA_110877241"
    },
    {
      "drive_folder_id": "1-UH6BmzgOUvCTW6klb4XziE_aZ--kUNj",
      "name": "2024KH137_S-SPACE_110850049"
    },
    {
      "drive_folder_id": "1BERT5Vb8_bt4zLlOrOAozzQrd1hec_Qe",
      "name": "2024KH09_CHINH-HOA_110609098"
    },
    {
      "drive_folder_id": "1TESVZbkTnt1t8Vf2BlNCuH4DNuarGami",
      "name": "2025KH05_SUC-KHOE-3-GOC_110946079"
    },
    {
      "drive_folder_id": "13fE_uQZXNSW12kwrq4dCaAmTTc_iMeqs",
      "name": "2024KH147_NONG-NGHIEP-SB_110904840"
    },
    {
      "drive_folder_id": "1NQGlSorZMler3CWV2Up8p8ZUwNX-rArf",
      "name": "2025KH08_FAS-GAMES_110984878"
    },
    {
      "drive_folder_id": "1CjJUpJkftNwdQy5fTh0VqUdLZufj4ql-",
      "name": "2024KH130_QUOC-TE-SONA_110860953"
    },
    {
      "drive_folder_id": "1XMbdvl3SUaOCSAmO7tdEA5VNeP7IMhuw",
      "name": "2025KH15_QUOC-TE-DHT_110856058"
    },
    {
      "drive_folder_id": "1ZFHoFjAFN_lvyAavY3UkaFft7gVNdJKG",
      "name": "2024KH129_DOANH-NGHIEP-THANH-NIEN_110857862"
    },
    {
      "drive_folder_id": "1a3fWUOW8r5WhLh9wVBnIfpG7Blci0xUz",
      "name": "2024KH42MP_BAT-DONG-SAN-MINH-PHAT_110890411"
    },
    {
      "drive_folder_id": "1cXJa6iF4P6UG95jT9kqJe-_DUtjPm365",
      "name": "2024KH58_LA-HOUSE_110718883"
    },
    {
      "drive_folder_id": "1KfHfraDd5TiviG9nhBpo0ZFNCBmsht8s",
      "name": "2024KH116_NOI-THAT-THANG-LONG_110841157"
    },
    {
      "drive_folder_id": "1ZTG7qz1WePEyc1FWtXUvzWcWU5T-NNKu",
      "name": "2024KH67_AN-BINH_102931079"
    },
    {
      "drive_folder_id": "1iNLo2qnn4EF3caMy5kjyy8FM2rSO1hF6",
      "name": "2024KH152_TAHA-TRAVEL_110902610"
    },
    {
      "drive_folder_id": "1xBjENm9jEFF3j2Sb8P0ew5OLUMaO4HtZ",
      "name": "2025KH22_TRAN-MY-YEN_8093008973"
    },
    {
      "drive_folder_id": "1zlivpeurNDNmnshrLx6Myw1IZZQb2_Ci",
      "name": "2024KH149_HA-COSMETICS_110906735"
    },
    {
      "drive_folder_id": "1WVFeyxEGhhfTb6gIvXeUmqhj42UJ4hbv",
      "name": "2024KH140_THANH-PHAT_110885933"
    },
    {
      "drive_folder_id": "1qQLA_ImaokwJB1Wt7NTuzIBOrNOBmK2T",
      "name": "2024KH139_HOA-PHAT_110872927"
    },
    {
      "drive_folder_id": "1GNMJguAaq6S1Y2J4fCha7mLni9d3yTLo",
      "name": "2025KH001_CAO-THIET_110917335"
    },
    {
      "drive_folder_id": "1khSruVOSAkq3ftCdedTfF26QN6qq8BUh",
      "name": "2024KH66_MIS-VIET-NAM_108585643"
    },
    {
      "drive_folder_id": "1VrhSLy9ocApyU_mu0Q6pskKM1iZ2AzPA",
      "name": "20XXKHYYY_TEN-VIET-TAT_MST"
    },
    {
      "drive_folder_id": "1BpVarGrJbzaC9rkG6aqEa8ERgel7TNdM",
      "name": "2025KH35BH_VCONNECT_0319236659"
    },
    {
      "drive_folder_id": "1n_KIimyWUi467tjpgnO6luBE_EMXVDfy",
      "name": "2025KH003_CYBER_110895353"
    },
    {
      "drive_folder_id": "1l-QbGhcY9GnDc511cQPRkG6PFy-3nrql",
      "name": "2024KH138_AMG_110863231"
    },
    {
      "drive_folder_id": "17QCk-M7MM-kn4crRRUlwlYKeaTFAEc-7",
      "name": "2024KH127_IMIND_110860417"
    },
    {
      "drive_folder_id": "1Rf0vWeErHg5etmuo06IFEep2zhxHG_wQ",
      "name": "2024KH117_BOSSX_110836319"
    },
    {
      "drive_folder_id": "19VYP91-eWxBiB6mTfx1EVLda4SppMlmB",
      "name": "2024KH120_TH_110844581"
    },
    {
      "drive_folder_id": "1TlHzD_beakX5ShmLGG95JsPY4QhCiMyi",
      "name": "2024KH03_PINGALA_110591933"
    },
    {
      "drive_folder_id": "1uoFh7y2gRG3fk9zuKq_4sSRecdW5Epxc",
      "name": "2024KH76_LK_110730369"
    },
    {
      "drive_folder_id": "1Y7yHI_gQpW7YWUr3GFwuGIF2SHVtog7l",
      "name": "2024KH47_DINOSAURIZED_3200741184"
    },
    {
      "drive_folder_id": "1WLT6yF6rmfgG_nT7O-llT_re6d_hEnba",
      "name": "2024KH30RA_RAYMOND_110325787"
    },
    {
      "drive_folder_id": "1btlzTi0NWp1yk1XcC2Gl5X214u-hxfz4",
      "name": "2024KH88_GROWDEMY_110767270"
    },
    {
      "drive_folder_id": "1FEho9_YD6262DhiVzTb1VAptkp5_uSEr",
      "name": "2024KH45_MEETUP_110691254"
    },
    {
      "drive_folder_id": "1fCpB0MbtvVfqu4hqS_tJLi18zqMeyQUz",
      "name": "2023KH050_GODIVA_110473739"
    },
    {
      "drive_folder_id": "1_i_5ia0CCNW2LMcUaGWGghvc6ca2rAnq",
      "name": "2023KH025_381_110485773"
    },
    {
      "drive_folder_id": "1agBOMfPvk-Kx5hZAuw7HNM4cgeUqMLSc",
      "name": "NOCODEAZ2_YUNDUOZE_2301270395"
    },
    {
      "drive_folder_id": "19GEMqr6kjOydVUqjxh9JZr27cSvc3nIM",
      "name": "2024KH05_LYNCHA_110586531"
    },
    {
      "drive_folder_id": "1o6lWKBmiMOnIjQ31nuOA71wmaHB7sEBO",
      "name": "2024KH109_VHTECH_110789919"
    },
    {
      "drive_folder_id": "1egrOZwqQcZs7s3b4-UZ_D3ZlenHQDLvV",
      "name": "2024KH32AI_AIBOX_109481848"
    },
    {
      "drive_folder_id": "1xU4pZO_-l92yECDjgQnJWgIrYC4ssbH2",
      "name": "2024KH11_UPLAND_110064398"
    },
    {
      "drive_folder_id": "1jeNs42qwaeg5PNB33LVIEJ72v_KcCrnm",
      "name": "2025KH40XU_EXTRAMILE_0315873329"
    },
    {
      "drive_folder_id": "17ZPJp2kmLW_rBjvX7n3OOKxuSGju4c7F",
      "name": "2025KH32BH_VNEXCO_0111246344"
    },
    {
      "drive_folder_id": "15V962zvKw8q7axFdliLesCJwooxsmzN2",
      "name": "2025KH31BH_MATHON_0111233200"
    },
    {
      "drive_folder_id": "1Gxcgiw3Yn44xTIUY7G26a_C6vWlEjI6-",
      "name": "2025KH29BH_VINPRINT_0319177298"
    },
    {
      "drive_folder_id": "1eU6NKxU1eC41zncXYORWja3fs4bn7oek",
      "name": "2025KH25_NADAL_0107444255"
    },
    {
      "drive_folder_id": "1RtVTNGCruqN5BLujbkPO6KRa0uURVoRY",
      "name": "2025KH09_LIFECORP_0108170543"
    },
    {
      "drive_folder_id": "1cBD7TdGNKmI-Q2nTulQ5aMAZI1wrlumy",
      "name": "2025KH04_EVERYMATCH_0110947869"
    },
    {
      "drive_folder_id": "1pJlrUW6dwye5VPDkmE1eDywvWkW563OD",
      "name": "2024KH108_VNTECH_0109512976"
    },
    {
      "drive_folder_id": "1U-MCEU820WZnrU8WF1f4jzo4c81YrAw2",
      "name": "2023KH003_ONUS_0110504634"
    },
    {
      "drive_folder_id": "107QFzTAZsJeTSYq1gebF4na_upC9BWU_",
      "name": "2024KH80_DELTA_0110754930"
    },
    {
      "drive_folder_id": "1uvi4KCA88KgMd24LImMpotWE4VdGP0Jk",
      "name": "2024KH59_DANTECH_0110720226"
    },
    {
      "drive_folder_id": "1r1HcEAj5VE120vWodLMs_hDY86UpLGUB",
      "name": "2024KH15_SAVY_0110625597"
    },
    {
      "drive_folder_id": "1ILqiFuqGSiuJJwxqSR4PbsOzav6HbGgf",
      "name": "2024KH77_INSUPRO_0110589620"
    },
    {
      "drive_folder_id": "1JmFFxxxun6_Wo1znsEs2ObJ2mu2bmbl7",
      "name": "2024KH50_BRANDIA_0316808403"
    },
    {
      "drive_folder_id": "1kdXpHNihk3EZne9lX4p_5QCTQf9gkT6m",
      "name": "2024KH61_M4U_0110673671"
    },
    {
      "drive_folder_id": "1mr1Xp9cU9VBZjH4Yo5D7rLWUu37DFrhz",
      "name": "2023KH022CL_CLT_0110486826"
    },
    {
      "drive_folder_id": "1Om1CE27XIdZWvshS_HEX7LQEOTcR9eQs",
      "name": "2023KH008_VTH_0110462127"
    },
    {
      "drive_folder_id": "10jclGMU_wMO0vmZ4g4o5qmOx4PhMu_fl",
      "name": "2023KH007_WINECOM_0983141636"
    },
    {
      "drive_folder_id": "1XOwJt--ikNPQuw9a32F3bJ65gizqOrH8",
      "name": "2023KH015_HUNGHOMES_0110481377"
    },
    {
      "drive_folder_id": "1vYHwhWlSqiSkLI1p9uiBHzd5b8D4MNqS",
      "name": "2024KH92_JOYHOME_0901152287"
    },
    {
      "drive_folder_id": "17Xr-u-xIEyk6CVt4Xqu0vgpS3ziRpEbx",
      "name": "2024KH97AZ_XINYING_0318516050"
    },
    {
      "drive_folder_id": "1tw5wY3yTTtzrj5f_Nea9IVUQFTVCz4po",
      "name": "2023KH044AZ_HARMAN_0108924261"
    },
    {
      "drive_folder_id": "1FjBHdxNc2VG3ieLyGyiGsjdmeA1aZk78",
      "name": "2023KH030_DIVUVI_0108335918"
    },
    {
      "drive_folder_id": "1YZ840a2gYW3JbuHakAClWgLeKgENZMWn",
      "name": "2023KH038AZ_TEPUER_2301229012"
    },
    {
      "drive_folder_id": "1cGMw46jW61ACynTatA3lFcKDfJ6p5qlM",
      "name": "2023KH020_HAVA_0110146393"
    },
    {
      "drive_folder_id": "1H6Dcjm1cRiBmyYu8QYMmoozBLLJWI0ML",
      "name": "2024KH94_Q.F.S_0109376522"
    },
    {
      "drive_folder_id": "1ub9qfaM1EoXhm1gaW6XX74yOAz-iJ1LT",
      "name": "2024KH51_ASAHIKO_0110699006"
    },
    {
      "drive_folder_id": "12Dym7t0Mw45HdYIAPSxtDYNT92unmml2",
      "name": "2024KH69_THG_0109563064"
    },
    {
      "drive_folder_id": "1r3Vk8KbxeWb4DOdEwECi2kLJgIOkOUR9",
      "name": "2024KH68_ASANA_0109394497"
    }
  ]

db = SessionLocal()

for c in COMPANIES:
    exists = db.query(Company).filter_by(
        drive_folder_id=c["drive_folder_id"]
    ).first()

    if exists:
        print(f"⏩ Skip (exists): {c['name']}")
        continue

    db.add(Company(
        name=c["name"],
        drive_folder_id=c["drive_folder_id"]
    ))
    print(f"✅ Added company: {c['name']}")

db.commit()
db.close()

print("🎉 Seed companies DONE")
