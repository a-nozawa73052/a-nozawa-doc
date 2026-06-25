# EXPLAIN 結果 — インデックス追加前

インデックス追加後の結果と比較するための記録。

---

## クエリ① 端末回収状況登録（serials）

| id | table | type | key | rows | filtered | Extra |
|----|-------|------|-----|------|----------|-------|
| 1 | serials | ref | idx_serials_deleted_at | **440,270** | 31.95% | Using index condition; Using where |
| 1 | shipping_requests | ref | contract_cd | 1 | 4.56% | Using where |
| 1 | device_types | ref | neos_item_cd | 1 | 92.56% | Using where |

**問題点:**
- `serials` の possible_keys に `idx_serials_device_status_cd` が存在するが選ばれていない
- `idx_serials_deleted_at` を使って **44万行スキャン** → `device_status_cd IN ('20','21')` はポストフィルター扱い
- 追加するインデックス: `(device_status_cd, contract_cd, serial_cd, deleted_at)`
- 期待値: `key=idx_serials_status_contract_serial`、rows が大幅減

---

## クエリ② 引き当て（shipping_requests）

| id | select_type | table | type | key | rows | filtered | Extra |
|----|-------------|-------|------|-----|------|----------|-------|
| 1 | PRIMARY | shipping_requests | index_merge | idx_ship_req_complete_kitting_date, idx_ship_req_deleted_at | **143,326** | **1%** | Using intersect(...); Using where |
| 1 | PRIMARY | device_types | ref | neos_item_cd | 1 | 100% | Using where |
| 1 | PRIMARY | \<derived2\> | ref | \<auto_key0\> | 7 | 100% | — |
| 2 | DERIVED | \<derived3\> | ALL | — | 66 | 100% | Using temporary; Using filesort |
| 2 | DERIVED | aed | ref | idx_assign_enable_devices_shipping_request | 1 | 100% | Using index condition; Using where |
| 2 | DERIVED | dt | ref | neos_item_cd | 1 | 92.56% | Using where |
| 3 | DERIVED | assign_enable_devices | index | idx_assign_enable_devices_shipping_request | 668 | 10% | Using where; Using index |

**問題点:**
- `shipping_requests` が `index_merge` で2本の単独インデックスを組み合わせ **14万行スキャン**
- `filtered=1%` → 実質通過するのは約 1,430行のみ（残り99%が無駄なスキャン）
- `complete_allocation_date` / `request_display_flg` はインデックスなし → ポストフィルター扱い
- `assign_enable_devices` サブクエリ部分は既存インデックスで問題なし（rows=668・1 で軽量）
- 追加するインデックス: `(complete_allocation_date, complete_kitting_date, request_display_flg, deleted_at)`
- 期待値: `type=range` or `ref`、`index_merge` が消える、rows が大幅減
