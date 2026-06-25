# EXPLAIN 結果 比較（インデックス追加前後・本番）

---

## クエリ① 端末回収状況登録（serials）

### 実行時間

| | 実行時間 |
|--|---------|
| **追加前** | **11.086s** |
| **追加後** | **1.478s** |
| 改善率 | 約87%削減（約7.5倍高速化） |

### EXPLAIN 比較（serials テーブル）

| 項目 | 追加前 | 追加後 |
|------|--------|--------|
| type | ref | range |
| key | `idx_serials_deleted_at` | **`idx_serials_status_contract_serial`** |
| rows | **440,270** | 299,627 |
| filtered | 31.95% | **100%** |
| Extra | Using index condition; Using where | Using where; **Using index** |

**変化のポイント:**
- 新インデックスが採用され、`device_status_cd IN ('20','21')` がポストフィルターでなくインデックス上で処理されるようになった
- `Using index`（カバリングインデックス）になり、実データ行へのアクセスがゼロになった
- type が `ref` → `range` になったのは `IN` 条件の性質によるもので問題なし

### EXPLAIN 詳細

**追加前:**

| id | table | type | key | rows | filtered | Extra |
|----|-------|------|-----|------|----------|-------|
| 1 | serials | ref | idx_serials_deleted_at | 440,270 | 31.95% | Using index condition; Using where |
| 1 | shipping_requests | ref | contract_cd | 1 | 4.56% | Using where |
| 1 | device_types | ref | neos_item_cd | 1 | 92.56% | Using where |

**追加後:**

| id | table | type | key | rows | filtered | Extra |
|----|-------|------|-----|------|----------|-------|
| 1 | serials | range | idx_serials_status_contract_serial | 299,627 | 100% | Using where; Using index |
| 1 | shipping_requests | ref | contract_cd | 1 | 4.56% | Using where |
| 1 | device_types | ref | neos_item_cd | 1 | 92.56% | Using where |

---

## クエリ② 引き当て（shipping_requests）

### 実行時間

| | 実行時間 |
|--|---------|
| **追加前** | **8.2s** |
| **追加後** | **0.298s** |
| 改善率 | 約96%削減（約27倍高速化） |

### EXPLAIN 比較（shipping_requests テーブル）

| 項目 | 追加前 | 追加後 |
|------|--------|--------|
| type | **index_merge**（2本合成） | ref |
| key | `idx_ship_req_deleted_at` + `idx_ship_req_complete_kitting_date` | **`idx_ship_req_allocation_kitting_flg`** |
| rows | **143,326** | 68,000 |
| filtered | **1%** | 100% |
| Extra | Using intersect(...); Using where | Using index condition |

**変化のポイント:**
- `index_merge` が解消され、新しい複合インデックス1本で処理されるようになった
- filtered=1%（99%が無駄スキャン）の状態が解消された
- STGでは新インデックスが採用されなかったが、本番データ量では採用された

### EXPLAIN 詳細

**追加前:**

| id | select_type | table | type | key | rows | filtered | Extra |
|----|-------------|-------|------|-----|------|----------|-------|
| 1 | PRIMARY | shipping_requests | index_merge | idx_ship_req_complete_kitting_date, idx_ship_req_deleted_at | 143,326 | 1% | Using intersect(...); Using where |
| 1 | PRIMARY | device_types | ref | neos_item_cd | 1 | 100% | Using where |
| 1 | PRIMARY | \<derived2\> | ref | \<auto_key0\> | 7 | 100% | — |
| 2 | DERIVED | \<derived3\> | ALL | — | 66 | 100% | Using temporary; Using filesort |
| 2 | DERIVED | aed | ref | idx_assign_enable_devices_shipping_request | 1 | 100% | Using index condition; Using where |
| 2 | DERIVED | dt | ref | neos_item_cd | 1 | 92.56% | Using where |
| 3 | DERIVED | assign_enable_devices | index | idx_assign_enable_devices_shipping_request | 668 | 10% | Using where; Using index |

**追加後:**

| id | select_type | table | type | key | rows | filtered | Extra |
|----|-------------|-------|------|-----|------|----------|-------|
| 1 | PRIMARY | shipping_requests | ref | idx_ship_req_allocation_kitting_flg | 68,000 | 100% | Using index condition |
| 1 | PRIMARY | device_types | ref | neos_item_cd | 1 | 100% | Using where |
| 1 | PRIMARY | \<derived2\> | ref | \<auto_key0\> | 7 | 100% | — |
| 2 | DERIVED | \<derived3\> | ALL | — | 66 | 100% | Using temporary; Using filesort |
| 2 | DERIVED | aed | ref | idx_assign_enable_devices_shipping_request | 1 | 100% | Using index condition; Using where |
| 2 | DERIVED | dt | ref | neos_item_cd | 1 | 92.56% | Using where |
| 3 | DERIVED | assign_enable_devices | index | idx_assign_enable_devices_shipping_request | 668 | 10% | Using where; Using index |
