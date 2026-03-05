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
-- Table structure for table `employees`
--

DROP TABLE IF EXISTS `employees`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `employees` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `title` varchar(255) DEFAULT NULL,
  `email` varchar(255) DEFAULT NULL,
  `status` varchar(50) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `employees`
--

LOCK TABLES `employees` WRITE;
/*!40000 ALTER TABLE `employees` DISABLE KEYS */;
INSERT INTO `employees` VALUES (1,'Phùng Duy Anh','Giám đốc','nhan.phan@cenvi.vn','active','2025-12-23 10:39:15','2025-12-23 10:39:15'),(2,'Nguyễn Thị Liên','Giám đốc','lien.nguyen@cenvi.vn','active','2025-12-23 10:39:15','2025-12-23 10:39:15'),(3,'Trần Thị Mai Phương','Nhân viên','phuong.tran.cenvi@gmail.com','active','2025-12-23 10:39:15','2025-12-23 10:39:15'),(4,'Vương Cẩm Vân','Nhân viên','van.vuong.cenvi@gmail.com','active','2025-12-23 10:39:15','2025-12-23 10:39:15'),(5,'Đỗ Thị Hồng Nhung','Nhân viên','nhungdo.cenvi@gmail.com','active','2025-12-23 10:39:15','2025-12-23 10:39:15'),(6,'Hoàng Nhật Minh','Nhân viên','minh66tk@gmail.com','active','2025-12-23 10:39:15','2025-12-23 10:39:15'),(7,'Nguyễn Quỳnh Anh','Nhân viên','qanh110603@gmail.com','active','2025-12-23 10:39:15','2025-12-23 10:39:15'),(8,'Trần Đình Khôi','Nhân viên','trankhoi.forwork@gmail.com','active','2025-12-23 10:39:15','2025-12-23 10:39:15'),(9,'Nguyễn Thị Hồng','Nhân viên','hongnt901@gmail.com','active','2025-12-23 10:39:15','2025-12-23 10:39:15'),(10,'Nguyễn Lan Anh','Kế toán nội bộ','nguyenlananh2974@gmail.com','active','2025-12-23 10:39:15','2025-12-23 10:39:15'),(11,'Nguyễn Thị Hạnh','Kế toán nội bộ','nghanh1904@gmail.com','active','2025-12-23 10:39:15','2025-12-23 10:39:15'),(12,'Phùng Thị Hiền','Kế toán nội bộ','phunghien0101@gmail.com','active','2025-12-23 10:39:15','2025-12-23 10:39:15'),(13,'Nguyễn Thị Hoa','Kế toán nội bộ','hoanguyen.cenvi@gmail.com','active','2025-12-23 10:39:15','2025-12-23 10:39:15');
/*!40000 ALTER TABLE `employees` ENABLE KEYS */;
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
