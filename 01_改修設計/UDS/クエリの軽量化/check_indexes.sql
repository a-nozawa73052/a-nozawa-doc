-- ============================================================
-- インデックス追加前 現状確認クエリ
-- 対象テーブル: serials / assign_enable_devices / contract_bgm_genres
-- ============================================================


-- ------------------------------------------------------------
-- 【1】3テーブルの全インデックス一覧
--   INDEX_NAME・カラム構成・ユニーク有無を確認する
-- ------------------------------------------------------------
SELECT
    TABLE_NAME,
    INDEX_NAME,
    SEQ_IN_INDEX,
    COLUMN_NAME,
    NON_UNIQUE
FROM INFORMATION_SCHEMA.STATISTICS
WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME IN ('serials', 'assign_enable_devices', 'contract_bgm_genres')
ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX;


-- ------------------------------------------------------------
-- 【2】追加予定カラムを含むインデックスが既に存在するか確認
--   各テーブルごとに、追加予定カラムを1つでも含むINDEX_NAMEを列挙する
--   ヒットした場合は追加前に内容を精査すること
-- ------------------------------------------------------------

-- ① serials: (device_status_cd, contract_cd, serial_cd, deleted_at)
SELECT
    'serials' AS TABLE_NAME,
    INDEX_NAME,
    GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) AS columns
FROM INFORMATION_SCHEMA.STATISTICS
WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'serials'
    AND COLUMN_NAME IN ('device_status_cd', 'contract_cd', 'serial_cd', 'deleted_at')
GROUP BY INDEX_NAME
HAVING COUNT(DISTINCT COLUMN_NAME) >= 2  -- 2カラム以上の組み合わせを持つインデックスのみ表示

UNION ALL

-- ② assign_enable_devices: (deleted_at, ref_neos_item_cd, generation)
SELECT
    'assign_enable_devices' AS TABLE_NAME,
    INDEX_NAME,
    GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) AS columns
FROM INFORMATION_SCHEMA.STATISTICS
WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'assign_enable_devices'
    AND COLUMN_NAME IN ('deleted_at', 'ref_neos_item_cd', 'generation')
GROUP BY INDEX_NAME
HAVING COUNT(DISTINCT COLUMN_NAME) >= 2

UNION ALL

-- ③ contract_bgm_genres: (umusic_sequential_cd, deleted_at)
SELECT
    'contract_bgm_genres' AS TABLE_NAME,
    INDEX_NAME,
    GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) AS columns
FROM INFORMATION_SCHEMA.STATISTICS
WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'contract_bgm_genres'
    AND COLUMN_NAME IN ('umusic_sequential_cd', 'deleted_at')
GROUP BY INDEX_NAME
HAVING COUNT(DISTINCT COLUMN_NAME) >= 2;
