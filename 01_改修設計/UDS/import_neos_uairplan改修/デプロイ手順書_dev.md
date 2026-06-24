# デプロイ手順書：neos_uairplan 取込アーキテクチャ変更（dev 環境）

作成日: 2026-06-23  
対象システム: UDS  
対象環境: **dev**

---

## 事前確認

| 確認項目 | 確認方法 |
|---------|---------|
| `batch-transfer-neos-uairplan-tsv` の EventBridge が有効か | EventBridge コンソールで確認（無効化のタイミング調整のため） |

---

## 1. テーブル作成（dev DB）

dev 環境の UDS DB（`uds` データベース）に `work_imported_neos_uairplan` テーブルを作成する。

1. dev DB に接続
2. 以下の DDL を実行する

```sql
CREATE TABLE work_imported_neos_uairplan (
  -- 管理カラム
  id                   BIGINT UNSIGNED  AUTO_INCREMENT PRIMARY KEY COMMENT 'ID',
  source_file_name     VARCHAR(255)     NOT NULL                   COMMENT '連携ファイル名',

  -- TSV カラム（neos_uairplan.tsv の内容そのまま）
  contract_cd          VARCHAR(21)      NOT NULL COMMENT '契約CD',
  contract_status_cd   VARCHAR(1)       NOT NULL COMMENT '契約ステータスCD（1:受注 2:確定 3:キャンセル 4:解約）',
  contract_status_name VARCHAR(10)      NULL     COMMENT '契約ステータス名',
  unis_item_cd         VARCHAR(7)       NOT NULL COMMENT 'UNIS品目CD',
  unis_band_cd         VARCHAR(3)       NULL     COMMENT 'UNISバンドCD',
  unis_customer_cd     VARCHAR(32)      NOT NULL COMMENT 'UNIS顧客CD（設置先CD）',
  customer_name        VARCHAR(50)      NOT NULL COMMENT '顧客設置先名称',
  customer_name_kana   VARCHAR(50)      NOT NULL COMMENT '顧客設置先名称カナ',
  customer_zip_cd      VARCHAR(8)       NULL     COMMENT '顧客郵便番号',
  customer_state_cd    VARCHAR(2)       NULL     COMMENT '顧客都道府県CD',
  customer_state_name  VARCHAR(20)      NULL     COMMENT '顧客都道府県名',
  customer_address1    VARCHAR(100)     NULL     COMMENT '顧客住所1（市区町村）',
  customer_address2    VARCHAR(100)     NULL     COMMENT '顧客住所2（番地）',
  customer_address3    VARCHAR(100)     NULL     COMMENT '顧客住所3（建物等）',
  customer_tel         VARCHAR(20)      NULL     COMMENT '顧客電話番号',
  customer_branch_cd   VARCHAR(50)      NULL     COMMENT '顧客管轄支店CD',
  customer_branch_name VARCHAR(110)     NULL     COMMENT '顧客管轄支店名',
  customer_chain_cd    VARCHAR(11)      NULL     COMMENT '顧客チェーンCD',
  customer_chain_name  VARCHAR(30)      NULL     COMMENT '顧客チェーン名',
  unis_industry_cd     VARCHAR(6)       NOT NULL COMMENT 'UNIS業種CD',
  unis_industry_name   VARCHAR(30)      NULL     COMMENT 'UNIS業種名',
  contract_start_date  DATETIME         NULL     COMMENT '契約開始日',
  sales_person_cd      VARCHAR(50)      NULL     COMMENT '営業担当者CD',
  sales_person_name    VARCHAR(50)      NULL     COMMENT '営業担当者名',
  sales_branch_cd      VARCHAR(50)      NULL     COMMENT '営業支店CD',
  sales_branch_name    VARCHAR(50)      NULL     COMMENT '営業支店名',
  sales_division_cd    VARCHAR(10)      NULL     COMMENT '営業部門CD',
  sales_division_name  VARCHAR(110)     NULL     COMMENT '営業部門名',
  contract_agency_cd   VARCHAR(6)       NULL     COMMENT '代理店CD',
  contract_agency_name VARCHAR(40)      NULL     COMMENT '代理店名',
  create_date          DATETIME         NULL     COMMENT '作成日',
  renewal_date         DATETIME         NULL     COMMENT '更新日',
  customer_update_date DATETIME         NULL     COMMENT '顧客情報更新日',
  detail_billing_month VARCHAR(11)      NULL     COMMENT '明細請求月',
  contract_number      VARCHAR(3)       NULL     COMMENT '契約番号',
  contract_status      VARCHAR(1)       NULL     COMMENT '契約ステータス（出荷用）',
  detail_number        VARCHAR(3)       NULL     COMMENT '明細番号',
  detail_status        VARCHAR(1)       NULL     COMMENT '明細ステータス',
  confirmation_date    DATE             NULL     COMMENT '確定処理日',
  shipping_month       VARCHAR(11)      NULL     COMMENT '出荷月',
  shipping_cycle       TINYINT(1)       NULL     COMMENT '出荷周期',
  transfer_cd          VARCHAR(25)      NULL     COMMENT '移動CD',

  -- 日時管理カラム
  created_at           DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP                            COMMENT '作成日時',
  updated_at           DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  deleted_at           DATETIME         DEFAULT NULL                                                  COMMENT '削除日時'

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='neos_uairplan一時取込情報';
```

3. 作成確認

```sql
SHOW CREATE TABLE work_imported_neos_uairplan\G
```

---

## 2. preprocess-neos-uairplan-tsv デプロイ

**デプロイ方式**: AWS SAM（GitHub Actions）  
**対象ブランチ**: `develop` → dev 環境

### 2-1. デプロイ前作業（開発者）

以下がすべて完了していることを確認してからマージすること。

| # | 作業 | 確認 |
|---|------|------|
| 1 | SGS コピー処理のコメントアウト解除 | `fileCopyToSGS` 関数本体と handler 内の呼び出しブロックの両方を解除 | ☐ |
| 2 | `processLine` line 338 の `bucket` 引数追加バグ修正 | `await processLine(state, connection, bucket, sourceFileName, ...)` に修正 | ☐ |

### 2-2. デプロイ前作業（インフラ）

**dev ロールはすでに作成済み**のため、追加のインフラ作業は不要。

> ロール: `arn:aws:iam::518125615804:role/dev-preprocess-neos-uairplan-tsv-role`

### 2-3. デプロイ手順

1. `feature/ueda` → `develop` ブランチへマージ
2. GitHub Actions が自動実行され dev 環境へ SAM デプロイ
3. **S3 イベント通知の切り替え**
   - S3 コンソール → `dev-udsapi-neos-uairplan` バケット → プロパティ → イベント通知
   - 旧 Lambda（`dev-split-neos-uairplan-tsv`）への通知を削除
   - 新 Lambda（`dev-preprocess-neos-uairplan-tsv`）への通知を追加（`s3:ObjectCreated:Put`）
4. 動作確認（セクション 4）

---

## 3. import_neos_uairplan デプロイ

**デプロイ方式**: lambroll（GitLab CI）  
**対象ブランチ**: `develop` → dev 環境 / 設定ファイル: `function-dev.json`

### 3-1. デプロイ前作業（開発者）

| # | 作業 | 確認 |
|---|------|------|
| 1 | contracts 未存在エラー処理の実装 | `isExistData` が false の場合に Google Chat 通知 + 残り全行スキップ（`continue`）に変更 | ☐ |

### 3-2. デプロイ前作業（インフラ）

| # | 作業 | 確認 |
|---|------|------|
| 1 | Lambda コンソールで旧 S3 トリガー（`ready/`）が残っていないか確認 | 残っていれば削除 | ☐ |
| 2 | EventBridge スケジュールが設定されているか確認 | Lambda コンソール → トリガー | ☐ |
| 3 | EventBridge 未設定の場合は作成 | スケジュール式: `cron(0/10 * * * ? *)`、ターゲット: `dev-import-neos_uairplan` | ☐ |

### 3-3. デプロイ手順

1. `feature/ueda` → `develop` ブランチへマージ
2. GitLab CI が自動実行され lambroll deploy（`function-dev.json` を使用）
3. Lambda コンソールで旧 S3 トリガー（`ready/`）が残っていれば削除
4. EventBridge スケジュールが設定されているか確認（なければ作成）
5. `dev-batch-transfer-neos-uairplan-tsv` の EventBridge スケジュールを**無効化**
6. 動作確認（セクション 4）

---

## 4. 動作確認手順

### preprocess 確認

1. テスト用 TSV ファイルを `dev-udsapi-neos-uairplan` バケットへ PUT
2. CloudWatch Logs（`/aws/lambda/dev-preprocess-neos-uairplan-tsv`）でエラーがないか確認
3. `work_imported_neos_uairplan` に行が INSERT されているか確認

```sql
SELECT COUNT(*), source_file_name FROM work_imported_neos_uairplan
WHERE deleted_at IS NULL GROUP BY source_file_name;
```

4. `dev-sgs-import/neos_uairplan/` にファイルがコピーされているか確認
5. 元ファイルが `dev-udsapi-neos-uairplan` バケットから削除されているか確認

### import 確認

1. work テーブルに処理対象データがある状態で EventBridge を手動実行（テスト）
2. CloudWatch Logs（`/aws/lambda/dev-import-neos_uairplan`）でエラーがないか確認
3. `contracts` テーブルが更新されているか確認
4. work テーブルの該当行が DELETE されているか確認

```sql
SELECT COUNT(*) FROM work_imported_neos_uairplan WHERE deleted_at IS NULL;
```

---

## 5. ロールバック手順

### preprocess ロールバック

1. S3 イベント通知を旧 Lambda（`dev-split-neos-uairplan-tsv`）に戻す
2. 旧 Lambda がすでに削除済みの場合は旧コミットから再デプロイが必要

### import ロールバック

1. GitLab CI で改修前のコミットを `develop` ブランチにリバートして push
2. lambroll deploy が自動実行され旧バージョンに戻る
3. EventBridge スケジュールを削除し、旧 S3 トリガー（`ready/`）を再設定
4. `dev-batch-transfer-neos-uairplan-tsv` の EventBridge を再有効化

---

## 6. 廃止作業（動作確認完了後）

| 作業 | タイミング |
|-----|---------|
| 旧 `dev-split-neos-uairplan-tsv` Lambda 削除 | preprocess 動作確認後 |
| `dev-batch-transfer-neos-uairplan-tsv` Lambda 削除 | import 動作確認後 |
| S3 バケット `dev-udsapi-split-neos-uairplan-tsv` 削除 | 未処理ファイルがないことを確認してから |
| IAM ロール `dev-batch-transfer-neos-uairplan-tsv-role` 削除 | Lambda 削除後 |
