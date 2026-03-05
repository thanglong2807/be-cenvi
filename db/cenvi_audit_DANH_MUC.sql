-- MySQL dump 10.13  Distrib 8.0.45, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: cenvi_audit
-- ------------------------------------------------------
-- Server version	8.4.8

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `DANH_MUC`
--

DROP TABLE IF EXISTS `DANH_MUC`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `DANH_MUC` (
  `DM_ID` int NOT NULL AUTO_INCREMENT,
  `Ten_Danh_Muc` varchar(255) DEFAULT NULL,
  `Share_Drive_Folder_ID` varchar(255) DEFAULT NULL,
  `Metadata` json DEFAULT NULL,
  PRIMARY KEY (`DM_ID`),
  KEY `ix_DANH_MUC_Ten_Danh_Muc` (`Ten_Danh_Muc`),
  KEY `ix_DANH_MUC_DM_ID` (`DM_ID`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `DANH_MUC`
--

LOCK TABLES `DANH_MUC` WRITE;
/*!40000 ALTER TABLE `DANH_MUC` DISABLE KEYS */;
INSERT INTO `DANH_MUC` VALUES (2,'Ban hành','1Dx4wtrHlgEN7xN3azQa0MxM_dhjOQD5i','\"{\\\"ma_mau_hex\\\": \\\"#ef4444\\\", \\\"icon_code\\\": \\\"Folder\\\", \\\"phong_ban\\\": \\\"C\\\\u00f4ng ty\\\", \\\"phu_trach\\\": \\\"Ph\\\\u00f9ng Duy Anh\\\", \\\"ngay_ban_hanh\\\": \\\"2026-02-05\\\"}\"'),(3,'Than khảo','1vqSywrl2DxIvdB6zDPx4sScUBQoVR8xC','\"{\\\"ma_mau_hex\\\": \\\"#10b981\\\", \\\"icon_code\\\": \\\"Folder\\\", \\\"phong_ban\\\": \\\"C\\\\u00f4ng ty\\\", \\\"phu_trach\\\": \\\"Ph\\\\u00f9ng Duy Anh\\\", \\\"ngay_ban_hanh\\\": \\\"2026-02-05\\\"}\"'),(4,'Đào tạo','1WPn4CyLmOJzvSQ5Q13DjDVFCmJv1jA7Q','\"{\\\"ma_mau_hex\\\": \\\"#10b981\\\", \\\"icon_code\\\": \\\"Folder\\\", \\\"phong_ban\\\": \\\"C\\\\u00f4ng ty\\\", \\\"phu_trach\\\": \\\"Ph\\\\u00f9ng Duy Anh\\\", \\\"ngay_ban_hanh\\\": \\\"2026-02-05\\\"}\"');
/*!40000 ALTER TABLE `DANH_MUC` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-02-25  9:55:35
