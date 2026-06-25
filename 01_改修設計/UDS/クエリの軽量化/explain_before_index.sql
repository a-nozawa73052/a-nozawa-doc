-- ============================================================
-- インデックス追加前 実行計画確認クエリ
-- 対象: add_indexes.sql で追加する2インデックスに対応するクエリ
--
-- 確認ポイント:
--   type  : ALL/index = フルスキャン（問題）、ref/range = インデックス使用（期待値）
--   key   : 使用インデックス名（NULL = 未使用）
--   rows  : スキャン推定行数（少ないほど良い）
--   Extra : Using where / Using index など
-- ============================================================


-- ------------------------------------------------------------
-- ① serials テーブル
--   対象インデックス: idx_serials_status_contract_serial
--                     (device_status_cd, contract_cd, serial_cd, deleted_at)
--
--   現状: key=idx_serials_deleted_at, rows=440,270
--   期待: key=idx_serials_status_contract_serial, rows が大幅減
-- ------------------------------------------------------------
EXPLAIN
SELECT count(1)
FROM shipping_requests
INNER JOIN device_types
    ON  shipping_requests.neos_item_cd = device_types.neos_item_cd
    AND device_types.deleted_at IS NULL
INNER JOIN serials
    ON  shipping_requests.contract_cd = serials.contract_cd
    AND shipping_requests.serial_cd   = serials.serial_cd
    AND serials.deleted_at IS NULL
WHERE serials.device_status_cd IN ('20', '21');


-- ------------------------------------------------------------
-- ② shipping_requests テーブル
--   対象インデックス: idx_ship_req_allocation_kitting_flg
--                     (complete_allocation_date, complete_kitting_date,
--                      request_display_flg, deleted_at)
--
--   現状: type=index_merge, rows=143,335, filtered=1%
--   期待: type=ref or range, rows が大幅減, index_merge が消える
-- ------------------------------------------------------------
EXPLAIN
SELECT count(1)
FROM shipping_requests
LEFT JOIN device_types
    ON  shipping_requests.neos_item_cd = device_types.neos_item_cd
    AND device_types.deleted_at IS NULL
LEFT JOIN (
    SELECT
        aed.ref_neos_item_cd,
        GROUP_CONCAT(dt.device_type) AS assign_enable_device_type,
        MAX(aed.generation)          AS generation
    FROM assign_enable_devices aed
    INNER JOIN device_types dt
        ON  aed.neos_item_cd = dt.neos_item_cd
        AND dt.deleted_at IS NULL
    INNER JOIN (
        SELECT
            ref_neos_item_cd,
            MAX(generation) AS max_generation
        FROM assign_enable_devices
        WHERE deleted_at IS NULL
        GROUP BY ref_neos_item_cd
    ) tmp
        ON  aed.ref_neos_item_cd = tmp.ref_neos_item_cd
        AND aed.generation       = tmp.max_generation
    WHERE aed.deleted_at IS NULL
    GROUP BY aed.ref_neos_item_cd
) assign_enable_devices
    ON shipping_requests.neos_item_cd = assign_enable_devices.ref_neos_item_cd
WHERE shipping_requests.complete_allocation_date IS NULL
  AND shipping_requests.complete_kitting_date    IS NULL
  AND shipping_requests.request_display_flg      = 1
  AND shipping_requests.deleted_at               IS NULL;
