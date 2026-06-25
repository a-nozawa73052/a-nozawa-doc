# UDS 本番障害インシデント報告書

2026年6月24日

---

## 1. 概要

| 項目 | 内容 |
|------|------|
| 発生日時 | 2026年6月24日 14:51頃〜 |
| 影響範囲 | UDSへのログインで500エラー（全ユーザー影響） |
| 対象DB | UDS Aurora MySQL |
| 対応完了 | KILLコマンド実行により500エラー解消 |
| ステータス | 恒久対応（クエリ修正）は未実施 |

---

## 2. 根本原因

それぞれ異なる画面・サービスから発行される以下3種類のクエリが、インデックスを使わずフルスキャンを引き起こし、DB接続数が上限（max_connections: 135）に到達したことで新規接続が不可能になり500エラーが発生した。

### 問題クエリ① shipping_requests × serials カウントクエリ（最重症）

**発生元：端末回収状況登録画面**（`/manage/branch/device/return`）を開いた際にデフォルトで発行される

```sql
SELECT count(1) FROM shipping_requests
  INNER JOIN device_types ON (shipping_requests.neos_item_cd = device_types.neos_item_cd)
  INNER JOIN serials ON (shipping_requests.contract_cd = serials.contract_cd
                     AND shipping_requests.serial_cd = serials.serial_cd)
WHERE serials.device_status_cd IN ('20', '21');
```

| 項目 | 値 |
|------|-----|
| 最大実行時間 | 434秒（約7分） |
| スキャン行数 | 1,177,917行 |
| 1時間での発生回数 | 126回 |
| PROCESSLIST状態 | Sending data で60本以上が滞留 |

**原因：** `serials.device_status_cd` にはインデックス（`idx_serials_device_status_cd`）が存在するが、対象レコードが全体の約17%（869,234件中147,227件）を占めるため、MySQLオプティマイザがフルスキャンを選択した。

### 問題クエリ② shipping_requests × assign_enable_devices カウントクエリ

**発生元：引き当て画面**（`/manage/center/request`）を開いた際にデフォルトで発行される

```sql
SELECT count(1) FROM shipping_requests
  LEFT JOIN assign_enable_devices ON (
    SELECT ref_neos_item_cd, GROUP_CONCAT(...), MAX(generation)
    FROM assign_enable_devices INNER JOIN device_types ...
    GROUP BY ref_neos_item_cd  -- サブクエリで毎回集計
  ) ...
WHERE shipping_requests.complete_allocation_date IS NULL
  AND request_display_flg = 1 ...
```

| 項目 | 値 |
|------|-----|
| 最大実行時間 | 151秒 |
| 10秒以上の発生回数 | 43回 |
| 1秒以上の発生回数 | 960回 |
| PROCESSLIST状態 | Creating sort index で滞留 |

**原因：** サブクエリ内で `assign_enable_devices` をGROUP BY集計しており、画面を開くたびに毎回全件集計が実行される設計になっている。

### 問題クエリ③ contract_bgm_genres 検索

> ⚠️ **インシデントレポート記載のSQLに誤りがある可能性あり（要調査）**
>
> スローログ・PROCESSLISTから取得したとされる下記SQLは `umusic_sequential_cd` で絞り込んでいるが、
> 発生元として特定された `api_bgms` Lambda（`bgms.js`）の実際のクエリは以下の通りで **`contract_cd` で絞り込んでいる**。
> `umusic_sequential_cd` はコード上で一切使用されておらず、記載SQLとの一致が取れない。
> スローログ取得時に別クエリが混入した可能性がある。

**スローログ記載SQL（正確性に疑義あり）:**
```sql
SELECT * FROM contract_bgm_genres
WHERE deleted_at IS NULL AND umusic_sequential_cd = 48138;
```

**api_bgms Lambda の実際のクエリ:**
```sql
SELECT bgm_genre_large_cd, bgm_genre_large_name, bgm_genre_mid_cd, bgm_genre_mid_name,
       bgm_genre_small_cd, bgm_genre_small_name
FROM contract_bgm_genres
WHERE contract_cd = ? AND deleted_at IS NULL;
```

`contract_cd` には既存インデックス（`KEY contract_cd`）が存在するため、api_bgms Lambda 自体はインデックスを使用できる状態にある。

| 項目 | 値 |
|------|-----|
| 最大実行時間 | 74秒 |
| スキャン行数 | 2,797,587行（約280万行） |
| 発生時刻 | 14:22頃に集中発生 |
| 真の発生元 | **不明（要調査）** |

---

## 3. 波及の仕組み

```
同じ重いクエリが並列で60〜80本同時実行
        ↓
DB接続数が max_connections (135) に到達
        ↓
新規リクエストが接続できず 500エラー
```

---

## 4. 発生タイムライン

| 時刻 (JST) | 状況 |
|------|------|
| 14:00〜 | 通常のスロークエリ（0.01〜0.1秒程度）が断続的に発生 |
| 14:22頃 | contract_bgm_genres の280万行スキャンが多発（発生元・SQL詳細は要調査） |
| 14:51頃 | serials系・shipping_requests系の100秒超クエリが積み上がり始める |
| 14:56〜 | 400〜434秒のクエリが大量に完了（並列実行が詰まって一気に返ってきた） |
| 〜 | DB接続が枯渇 → UDSログインで500エラー発生 |
| 対応 | KILLコマンドで滞留プロセスを全終了 → 500エラー解消 |

---

## 5. 対応内容

### 緊急対応（実施済み）

- KILLコマンドで滞留していた85プロセスを全て終了
- 500エラー解消を確認

---

## 6. 今後の対応（未実施）

### インデックス追加（根本対応）

| テーブル | 追加インデックス | 対象クエリ | ステータス |
|------|------|------|------|
| `serials` | `(device_status_cd, contract_cd, serial_cd, deleted_at)` | クエリ①　端末回収状況登録 | 未対応 |
| `shipping_requests` | `(complete_allocation_date, complete_kitting_date, request_display_flg, deleted_at)` | クエリ②　引き当て | 未対応 |

> **調査済み（追加不要）:**
> - `assign_enable_devices`: EXPLAIN確認済み。既に複数インデックスが存在し使用されている
> - `contract_bgm_genres`: EXPLAIN確認済み。既存インデックスが使用されており rows=1。またクエリ③のSQL自体に誤りがある可能性があるため対象外

DDL: `add_indexes.sql` 参照

### UI連打防止（再発防止）

| 対象画面 | 対応内容 | ステータス |
|------|------|------|
| 端末回収状況登録（`/manage/branch/device/return`） | ページ遷移時にローディングオーバーレイ表示 | 未対応 |
| 引き当て（`/manage/center/request`） | ページ遷移時にローディングオーバーレイ表示 | 未対応 |

### その他

| 対応内容 | 優先度 | ステータス |
|------|------|------|
| 利用者への暫定周知（インデックス追加前の再発防止） | 高 | 未対応 |
| wait_timeout の短縮（現在28800秒=8時間 → 短縮検討） | 中 | 未対応 |
| max_connections の増加検討（現在135） | 中 | 未対応 |
