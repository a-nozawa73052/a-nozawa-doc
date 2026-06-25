-- ============================================================
-- インデックス追加 DDL
--
-- EXPLAIN結果（追加前）をもとに対象を見直し済み:
--   ② assign_enable_devices → EXPLAIN で既にインデックスあり・使用中のため不要
--   ③ contract_bgm_genres  → EXPLAIN で既にインデックスあり・rows=1 のため不要
--   ② の真のボトルネットは shipping_requests 側（14万行スキャン）だったため追加
-- ============================================================


-- ------------------------------------------------------------
-- ① serials テーブル
--   クエリ: 端末回収状況登録画面（/manage/branch/device/return）
--
--   現状: オプティマイザが idx_serials_deleted_at を選択し 440,270行スキャン
--         device_status_cd IN ('20','21') は possible_keys に入っているが未使用
--   対策: device_status_cd を先頭にした複合インデックスで
--         IN絞り込み → contract_cd + serial_cd でJOIN をインデックス内で完結させる
-- ------------------------------------------------------------
ALTER TABLE serials
    ADD INDEX idx_serials_status_contract_serial
    (device_status_cd, contract_cd, serial_cd, deleted_at);


-- ------------------------------------------------------------
-- ② shipping_requests テーブル
--   クエリ: 引き当て画面（/manage/center/request）
--
--   現状: complete_kitting_date と deleted_at の index_merge で 143,335行スキャン
--         → filtered=1% のため実質 ~1,400行しか通らない非効率な状態
--         complete_allocation_date / request_display_flg はインデックスなし
--
--   対策: 4条件をまとめた複合インデックスで index_merge を廃止し
--         一発で未引き当て・未キッティング・表示対象のみに絞り込む
--
--   カラム順の根拠:
--     complete_allocation_date → 引き当て済みは多数のはず。IS NULL は選択率が低くなりやすい（先頭に最適）
--     complete_kitting_date    → 同様にキッティング済みを除外
--     request_display_flg     → 等値条件（= 1）はレンジ条件の前に置くのが原則だが
--                               ここでは前2カラムで十分に絞れる想定のため末尾側
--     deleted_at               → 論理削除済みを除外（最後）
-- ------------------------------------------------------------
ALTER TABLE shipping_requests
    ADD INDEX idx_ship_req_allocation_kitting_flg
    (complete_allocation_date, complete_kitting_date, request_display_flg, deleted_at);
