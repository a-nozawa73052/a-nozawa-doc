-- MySQL dump 10.13  Distrib 8.0.44, for Win64 (x86_64)
--
-- Host: localhost    Database: uds
-- ------------------------------------------------------
-- Server version	5.7.12-log

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
SET @MYSQLDUMP_TEMP_LOG_BIN = @@SESSION.SQL_LOG_BIN;
SET @@SESSION.SQL_LOG_BIN= 0;

--
-- GTID state at the beginning of the backup 
--

SET @@GLOBAL.GTID_PURGED=/*!80000 '+'*/ '';

--
-- Table structure for table `online_signup_prices`
--

DROP TABLE IF EXISTS `online_signup_prices`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `online_signup_prices` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `neos_item_cd` varchar(14) NOT NULL COMMENT 'NeOS品目CD',
  `neos_item_price` int(11) NOT NULL COMMENT '金額',
  `start_date` datetime NOT NULL COMMENT '金額適用開始日時',
  `end_date` datetime NOT NULL COMMENT '金額適用終了日時',
  `deleted_at` datetime DEFAULT NULL COMMENT '削除日時',
  `created_at` datetime NOT NULL COMMENT '作成日時',
  `updated_at` datetime NOT NULL COMMENT '更新日時',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `online_signup_prices`
--

LOCK TABLES `online_signup_prices` WRITE;
/*!40000 ALTER TABLE `online_signup_prices` DISABLE KEYS */;
INSERT INTO `online_signup_prices` VALUES (1,'UTVOP30_n01',0,'2023-10-01 00:00:00','9999-12-31 23:59:59',NULL,'2023-11-02 12:50:59','2023-11-02 12:50:59'),(2,'UTVOP30_n02',6000,'2023-10-01 00:00:00','9999-12-31 23:59:59',NULL,'2023-11-02 12:50:59','2023-11-02 12:50:59'),(3,'UTVOP30_n03',0,'2023-10-01 00:00:00','9999-12-31 23:59:59',NULL,'2023-11-02 12:50:59','2023-11-02 12:50:59'),(4,'UTVOP30_n04',0,'2023-10-01 00:00:00','9999-12-31 23:59:59',NULL,'2023-11-02 12:50:59','2023-11-02 12:50:59');
/*!40000 ALTER TABLE `online_signup_prices` ENABLE KEYS */;
UNLOCK TABLES;
SET @@SESSION.SQL_LOG_BIN = @MYSQLDUMP_TEMP_LOG_BIN;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-05-07 11:55:38
