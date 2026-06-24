# デプロイ手順書：neos_uairplan 取込アーキテクチャ変更（stg / prd 環境）

作成日: 2026-06-23  
対象システム: UDS  
対象環境: **stg / prd**

> **前提**: dev 環境の動作確認が完了してから実施すること。

### 環境別パラメータ一覧

| 項目 | stg | prd |
|-----|-----|-----|
| preprocess ブランチ | `staging` | `main` |
| import ブランチ | `staging` | `master` |
| import function.json | `function-stg.json` | `function-prd.json` |
| preprocess ロール名 | `stg-preprocess-neos-uairplan-tsv-role` | `prd-preprocess-neos-uairplan-tsv-role` |
| preprocess env ファイル | `env/staging.yml` | `env/main.yml` |
| 入力バケット | `stg-udsapi-neos-uairplan` | `prd-udsapi-neos-uairplan` |
| SGS バケット | `stg-sgs-import` | `prd-sgs-import` |
| EventBridge ターゲット Lambda | `stg-import-neos_uairplan` | `prd-import-neos_uairplan` |
| batch-transfer Lambda | `stg-batch-transfer-neos-uairplan-tsv` | `prd-batch-transfer-neos-uairplan-tsv` |

---

## 事前確認

| 確認項目 | 確認方法 |
|---------|---------|
| `batch-transfer-neos-uairplan-tsv` の EventBridge が有効か | EventBridge コンソールで確認（無効化のタイミング調整のため） |

---

## 1. テーブル作成

対象環境の UDS DB（`uds` データベース）に `work_imported_neos_uairplan` テーブルを作成する。stg・prd それぞれで実施する。

1. 対象環境の DB に接続
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

### テーブル作成チェックリスト

| 環境 | 実施 |
|-----|------|
| stg | ☐ |
| prd | ☐ |

---

## 2. preprocess-neos-uairplan-tsv デプロイ

**デプロイ方式**: AWS SAM（GitHub Actions）

### 2-1. デプロイ前作業（インフラ）

stg・prd それぞれでロールを新規作成する。

#### ロール構成（stg・prd 共通）

| ポリシー | 種別 | 内容 |
|---------|------|------|
| `AWSLambdaBasicExecutionRole` | AWS管理 | CloudWatch Logs 書き込み |
| `AWSLambdaVPCAccessExecutionRole` | AWS管理 | VPC 内 ENI 操作 |
| `{env}-preprocess-neos-uairplan-tsv-policy` | カスタムインライン | 入力バケットへの `GetObject` / `PutObject` / `DeleteObject` / `ListBucket` |
| `{env}-uds-sgs-file-relation-policy` | カスタム管理 | SGS バケットへの `PutObject`（既存ポリシーをアタッチ） |

#### `{env}-preprocess-neos-uairplan-tsv-policy` の JSON（stg の例・prd は `stg` を `prd` に読み替え）

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::stg-udsapi-neos-uairplan",
                "arn:aws:s3:::stg-udsapi-neos-uairplan/*"
            ]
        }
    ]
}
```

#### ロール作成チェックリスト

| 環境 | ロール名 | 実施 |
|-----|---------|------|
| stg | `stg-preprocess-neos-uairplan-tsv-role` | ☐ |
| prd | `prd-preprocess-neos-uairplan-tsv-role` | ☐ |

### 2-2. デプロイ前作業（開発者）

`env/staging.yml`・`env/main.yml` を新規作成する（`env/develop.yml` をベースに下記の差分を適用）。

#### `env/staging.yml` の変更箇所

```yaml
FunctionName: stg-preprocess-neos-uairplan-tsv
Role: arn:aws:iam::518125615804:role/stg-preprocess-neos-uairplan-tsv-role
Environment:
  Variables:
    ENV: staging
    DB_HOST: （stg 用 DB エンドポイント）
    DB_PASSWORD: （stg 用パスワード）
    SGS_BUCKET: stg-sgs-import
    WEB_HOOK_URL: （stg 用 Webhook URL）
VpcConfig:
  SecurityGroupIds:
    - （stg 用 SG ID）
  SubnetIds:
    - （stg 用サブネット ID）
```

#### `env/main.yml` の変更箇所

```yaml
FunctionName: prd-preprocess-neos-uairplan-tsv
Role: arn:aws:iam::518125615804:role/prd-preprocess-neos-uairplan-tsv-role
Environment:
  Variables:
    ENV: main
    DB_HOST: （prd 用 DB エンドポイント）
    DB_PASSWORD: （prd 用パスワード）
    SGS_BUCKET: prd-sgs-import
    WEB_HOOK_URL: （prd 用 Webhook URL）
VpcConfig:
  SecurityGroupIds:
    - （prd 用 SG ID）
  SubnetIds:
    - （prd 用サブネット ID）
```

#### env ファイル作成チェックリスト

| ファイル | 実施 |
|---------|------|
| `env/staging.yml` | ☐ |
| `env/main.yml` | ☐ |

### 2-3. デプロイ手順（stg）

1. `develop` → `staging` ブランチへマージ
2. GitHub Actions が自動実行され stg 環境へ SAM デプロイ
3. **S3 イベント通知の切り替え**
   - S3 コンソール → `stg-udsapi-neos-uairplan` バケット → プロパティ → イベント通知
   - 旧 Lambda（`stg-split-neos-uairplan-tsv`）への通知を削除
   - 新 Lambda（`stg-preprocess-neos-uairplan-tsv`）への通知を追加（`s3:ObjectCreated:Put`）
4. 動作確認（セクション 4）

### 2-4. デプロイ手順（prd）

1. `staging` → `main` ブランチへマージ
2. GitHub Actions が自動実行され prd 環境へ SAM デプロイ
3. **S3 イベント通知の切り替え**
   - S3 コンソール → `prd-udsapi-neos-uairplan` バケット → プロパティ → イベント通知
   - 旧 Lambda（`prd-split-neos-uairplan-tsv`）への通知を削除
   - 新 Lambda（`prd-preprocess-neos-uairplan-tsv`）への通知を追加（`s3:ObjectCreated:Put`）
4. 動作確認（セクション 4）

---

## 3. import_neos_uairplan デプロイ

**デプロイ方式**: lambroll（GitLab CI）

### 3-1. デプロイ前作業（インフラ）

stg・prd それぞれで確認する。

| # | 作業 | stg | prd |
|---|------|-----|-----|
| 1 | Lambda コンソールで旧 S3 トリガー（`ready/`）が残っていないか確認・削除 | ☐ | ☐ |
| 2 | EventBridge スケジュールが設定されているか確認 | ☐ | ☐ |
| 3 | EventBridge 未設定の場合は作成（`cron(0/10 * * * ? *)`） | ☐ | ☐ |

### 3-2. デプロイ手順（stg）

1. `develop` → `staging` ブランチへマージ
2. GitLab CI が自動実行され lambroll deploy（`function-stg.json` を使用）
3. Lambda コンソールで旧 S3 トリガー（`ready/`）が残っていれば削除
4. EventBridge スケジュールが設定されているか確認（なければ作成）
5. `stg-batch-transfer-neos-uairplan-tsv` の EventBridge スケジュールを**無効化**
6. 動作確認（セクション 4）

### 3-3. デプロイ手順（prd）

1. `staging` → `master` ブランチへマージ
2. GitLab CI が自動実行され lambroll deploy（`function-prd.json` を使用）
3. Lambda コンソールで旧 S3 トリガー（`ready/`）が残っていれば削除
4. EventBridge スケジュールが設定されているか確認（なければ作成）
5. `prd-batch-transfer-neos-uairplan-tsv` の EventBridge スケジュールを**無効化**
6. 動作確認（セクション 4）

---

## 4. 動作確認手順

{env} は実施環境（stg / prd）に読み替えること。

### preprocess 確認

1. テスト用 TSV ファイルを `{env}-udsapi-neos-uairplan` バケットへ PUT
2. CloudWatch Logs（`/aws/lambda/{env}-preprocess-neos-uairplan-tsv`）でエラーがないか確認
3. `work_imported_neos_uairplan` に行が INSERT されているか確認

```sql
SELECT COUNT(*), source_file_name FROM work_imported_neos_uairplan
WHERE deleted_at IS NULL GROUP BY source_file_name;
```

4. `{env}-sgs-import/neos_uairplan/` にファイルがコピーされているか確認
5. 元ファイルが `{env}-udsapi-neos-uairplan` バケットから削除されているか確認

### import 確認

1. work テーブルに処理対象データがある状態で EventBridge を手動実行（テスト）
2. CloudWatch Logs（`/aws/lambda/{env}-import-neos_uairplan`）でエラーがないか確認
3. `contracts` テーブルが更新されているか確認
4. work テーブルの該当行が DELETE されているか確認

```sql
SELECT COUNT(*) FROM work_imported_neos_uairplan WHERE deleted_at IS NULL;
```

---

## 5. ロールバック手順

### preprocess ロールバック

1. S3 イベント通知を旧 Lambda（`{env}-split-neos-uairplan-tsv`）に戻す
2. 旧 Lambda がすでに削除済みの場合は旧コミットから再デプロイが必要

### import ロールバック

1. GitLab CI で改修前のコミットを `staging`（または `master`）ブランチにリバートして push
2. lambroll deploy が自動実行され旧バージョンに戻る
3. EventBridge スケジュールを削除し、旧 S3 トリガー（`ready/`）を再設定
4. `{env}-batch-transfer-neos-uairplan-tsv` の EventBridge を再有効化

---

## 6. 廃止作業（動作確認完了後）

{env} は実施環境（stg / prd）に読み替えること。

| 作業 | タイミング |
|-----|---------|
| 旧 `{env}-split-neos-uairplan-tsv` Lambda 削除 | preprocess 動作確認後 |
| `{env}-batch-transfer-neos-uairplan-tsv` Lambda 削除 | import 動作確認後 |
| S3 バケット `{env}-udsapi-split-neos-uairplan-tsv` 削除 | 未処理ファイルがないことを確認してから |
| IAM ロール `{env}-batch-transfer-neos-uairplan-tsv-role` 削除 | Lambda 削除後 |
