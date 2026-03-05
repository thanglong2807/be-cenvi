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
-- Table structure for table `WORK_LINKS`
--

DROP TABLE IF EXISTS `WORK_LINKS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `WORK_LINKS` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(255) NOT NULL,
  `des` varchar(1000) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_WORK_LINKS_id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `WORK_LINKS`
--

LOCK TABLES `WORK_LINKS` WRITE;
/*!40000 ALTER TABLE `WORK_LINKS` DISABLE KEYS */;
INSERT INTO `WORK_LINKS` VALUES (1,'Trang chủ','https://cenvi.vn/','2026-02-05 15:10:32','2026-02-05 15:10:32'),(2,'Kênh giao tiếp với khách hàng','https://pancake.vn/dashboard','2026-02-05 15:10:58','2026-02-05 15:10:58'),(3,'Phần mềm kế toán TT133','https://erp.sivip.vn/SIVIPTT133_25A/Main/Login.aspx','2026-02-05 15:11:24','2026-02-05 15:11:24'),(4,'Phần mềm kế toán thông tư 200','https://erp.sivip.vn/SIVIPTT200_25A/Main/Login.aspx','2026-02-05 15:11:55','2026-02-05 15:11:55'),(5,'File thông tin','https://docs.google.com/spreadsheets/d/1KF68El6c5-_2QwybKa2k-3N149L-xYU2-h6SsSAUXno/edit?gid=1072061154#gid=1072061154','2026-02-05 15:12:26','2026-02-05 15:12:26'),(6,'Cơ sở dữ liệu','https://drive.google.com/drive/u/7/folders/0AIxlO0tI8hPBUk9PVA','2026-02-05 15:12:40','2026-02-05 15:12:40'),(7,'Cenvi workspace','https://tools.cenvi.vn/','2026-02-05 15:12:57','2026-02-05 15:12:57');
/*!40000 ALTER TABLE `WORK_LINKS` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-02-25  9:55:36
