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
-- Table structure for table `uploaded_files`
--

DROP TABLE IF EXISTS `uploaded_files`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `uploaded_files` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `div` int(11) DEFAULT NULL COMMENT 'アップロードファイル区分',
  `name` varchar(50) COLLATE utf8mb4_bin DEFAULT NULL COMMENT 'ファイル名',
  `update_user_id` int(11) DEFAULT NULL COMMENT '更新ユーザID',
  `created_at` datetime DEFAULT NULL COMMENT '登録日時',
  `updated_at` datetime NOT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  `deleted_at` datetime DEFAULT NULL COMMENT '削除日時',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=30 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='U∞DSアップロード済ファイルテーブル';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `uploaded_files`
--

LOCK TABLES `uploaded_files` WRITE;
/*!40000 ALTER TABLE `uploaded_files` DISABLE KEYS */;
INSERT INTO `uploaded_files` VALUES (1,32,'user (36)尼崎.csv',1,'2020-07-02 06:59:02','2026-03-05 13:04:59',NULL),(2,31,'HB_regi_modify_26050101_device_type.csv',1,'2020-07-02 07:02:01','2026-05-01 12:05:09',NULL),(3,33,'branch_stock_kasugai_20260501_02.csv',1,'2020-07-02 08:42:21','2026-05-01 15:35:25',NULL),(4,34,'branch_replacement (67)ひこね暫定.csv',1,'2020-08-06 16:09:58','2026-04-06 15:37:08',NULL),(5,35,'NT5_assign_enable_device (26).csv',1,'2020-12-23 18:05:15','2026-04-27 12:57:04',NULL),(6,36,'セットマスタ_本番_20260406.csv',1,'2021-12-06 08:33:52','2026-04-06 13:07:18',NULL),(7,37,'GRT-01B master_model_number (11).csv',1,'2021-12-06 08:34:26','2026-04-09 17:43:33',NULL),(8,25,'管轄センター変更_UT8-M8L(LTE)_template.csv',3,'2021-12-06 11:49:31','2023-01-18 17:50:44',NULL),(9,25,'管轄センター変更_U5G-01TW.csv',406,'2021-12-06 11:59:43','2026-05-01 17:48:55',NULL),(10,25,'管轄センター変更_USPOT-02W.csv',415,'2021-12-06 16:28:11','2025-07-11 16:02:11',NULL),(11,25,'center_device_move.csv',413,'2021-12-10 10:14:18','2021-12-13 19:44:13',NULL),(12,25,'UDS登録_UAU-01B_20260317(管轄センター変更登録) .csv',6,'2021-12-21 17:48:04','2026-03-17 10:24:47',NULL),(13,25,'管轄センター変更.csv',412,'2022-01-13 11:47:18','2022-04-27 16:01:04',NULL),(14,25,'center_device_moveUT8WIFI.csv',411,'2022-01-17 10:10:39','2022-07-26 17:01:14',NULL),(15,25,'center_device_move.csv',408,'2022-01-25 17:35:35','2022-03-04 15:58:12',NULL),(16,25,'center_device_move20260211_1.csv',12,'2022-03-17 09:51:01','2026-02-11 14:30:50',NULL),(17,25,'center_device_move.csv',1,'2022-05-02 15:07:43','2026-01-09 12:09:55',NULL),(18,38,'cp_device (3).csv',1,'2023-03-06 08:36:43','2024-09-12 17:57:08',NULL),(19,25,'center_device_move1025.csv',22,'2023-12-13 10:20:55','2026-04-30 13:31:40',NULL),(20,25,'center_device_move 管轄センター変更フォーマット20260217_PX-M730F',20,'2024-01-19 16:53:00','2026-02-17 18:24:02',NULL),(21,25,'center_device_move 管轄センター変更フォーマット2.csv',15,'2024-01-23 18:21:29','2024-05-13 09:57:11',NULL),(22,25,'center_device_move 管轄センター変更フォーマットURX231213.csv',18,'2024-02-01 15:30:33','2024-02-01 15:30:33',NULL),(23,25,'center_device_move 管轄センター変更フォーマット260424.csv',14,'2024-03-12 14:04:46','2026-04-24 14:40:30',NULL),(24,25,'一次出庫フォーム検品 - 管轄センター変更登録_20250617-03.csv',407,'2025-06-16 10:50:23','2025-06-17 16:04:44',NULL),(25,25,'UDS登録_UT8-4T1_20260414(管轄センター変更登録).csv',592,'2025-11-07 12:08:47','2026-04-14 18:34:57',NULL),(26,25,'UDS登録_UAC-01W_20260119(管轄センター変更登録) .csv',21,'2025-11-13 15:46:46','2026-01-19 15:45:56',NULL),(27,25,'center_device_move 管轄センター変更フォーマット231213 uphone本体.c',19,'2026-02-18 11:41:18','2026-04-14 15:02:35',NULL),(28,25,'UDS変更北海道へ20260501_5.csv',647,'2026-03-12 13:10:56','2026-05-01 15:17:19',NULL),(29,25,'UDS登録_U5G-01TW_20260324(管轄センター変更登録) -.csv',648,'2026-03-24 15:08:37','2026-03-24 15:08:37',NULL);
/*!40000 ALTER TABLE `uploaded_files` ENABLE KEYS */;
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

-- Dump completed on 2026-05-07 11:55:03
