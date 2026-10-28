# ADR: import_u1システムのSGS移管アーキテクチャ（ACE改修）

同フォルダの `改修概要書.md` に対応する設計判断の記録。

---

## 0001. import_u1パイプラインのSGS移管方式

- ステータス: 承認
- 日付: 2026-10-15
- 対象システム・機能: UDS（`import_u1`・`u1_file_split`・`u1_ecs_start`）
- 決定者: TODO: 要確認（会話内で明示的な決定者名の記載なし）

### コンテキスト

ACE統合に伴い、日次U1連携（ADL-133）の送信元がUDSからSGSに変更され、ファイル形式もcsv→tsvに変更される。現行のUDS側パイプラインは以下の3コンポーネント構成（コード調査により確認済み）。

```
S3(U1.csv) → u1_ecs_start（Lambda、S3トリガー）→ ECS Fargate起動
  → u1_file_split（Fargate、クラスタprd-u1-filesplit）：CSV分割＋Zebraバケットへコピー
  → import_u1（Lambda、S3トリガー）：u1_datasへINSERT/UPDATE＋unis_customer_brands副次更新
```

`u1_datas`は以下の既存機能から参照・更新されている（コード調査済み）。
- `api_customerinfo`：外部向け「U1情報取得API」として現役稼働中（UNIS_DB経由でu1_datasをSELECT）
- `import_contract`：契約取込時に`u1_datas`を`areas`とLEFT JOINしてarea_cd等を取得し、`unis_customer_brands`/`unis_customer_brand_confirms`へ反映

当初（2026年4月）の方針は「SGS側リポジトリに新規Lambdaとして実装、UDS側の`import_u1`は撤去」だったが、この場合SGS側新Lambdaが上記2機能向けの同等のデータ供給・副次更新ロジックを再実装しないと機能不全になるリスクが2026-10-14のコード確認で判明した（`改修タスク_コード確認結果.md` A11参照）。

### 検討した代替案

#### 案A: SGS側で新規Lambdaとしてゼロから再実装（当初方針）

- 内容: SGS側リポジトリに新規Lambda/バッチを実装し、UDS側の`import_u1`・関連処理は撤去する。
- メリット: UDS側のコード・インフラが完全に無くなり、長期的な保守対象がシンプルになる。
- デメリット: `api_customerinfo`・`import_contract`・`unis_customer_brands`への依存を含め、現行ロジックをSGS側が完全に把握・再実装する必要があり、引き継ぎ漏れによる機能不全リスクが高い。開発コストも高い（ゼロからの実装）。

#### 案B: Lambda/ECS Fargate・DBは現行UDS環境のまま、GitHubリポジトリのみSGS側へ移設（採用、2026-10-15決定）

- 内容: `import_u1`・`u1_file_split`・`u1_ecs_start`の3コンポーネントを改修対象とし、入力ファイル形式のcsv→tsv対応のみ行う。S3バケットは新規作成するが、Lambda・ECS Fargate・VPC・DB接続は現行UDSのAWS環境（アカウント518125615804）のまま変更しない。GitHubリポジトリのみSGS側のGitHub組織へ移設し、コードの保守・デプロイ主体をSGS側に移す。
- メリット: 同一コード・同一DBがそのまま動き続けるため、`api_customerinfo`・`import_contract`・`unis_customer_brands`への依存を無改修で維持できる。開発コストはファイル形式対応のみで済み、ゼロからの再実装より大幅に小さい。
- デメリット: UDSのAWSインフラにSGS側メンバーがデプロイ・運用できるようIAM権限整備が必要。中長期的にSGSが「UDSのAWS環境内のLambda」を保守し続ける形になり、将来的なインフラ統合（SGS自身のAWS環境への移設）を検討する余地は残る。

### 決定

案Bを採用する。既存機能への影響をゼロに抑えつつ、開発コストを最小化できるため。

1. **対象範囲を`import_u1`単体から3コンポーネントに拡大する**：`u1_ecs_start`・`u1_file_split`・`import_u1`のいずれもcsv→tsv対応のための改修が必要
2. **S3バケットは完全に新規作成する**：ACE後の新ファイル受け口として新バケットを用意し、`u1_ecs_start`のS3イベントトリガーをこの新バケットへ付け替える
3. **Lambda/ECS Fargate・VPC・DB接続は現行UDSのAWS環境のまま変更しない**：アカウント518125615804、VPC/サブネット、`unis_export`DB（`u1_datas`テーブル）を継続利用する
4. **GitHubリポジトリのみSGS側へ移設する**：コード自体の実行環境は変わらないため、`api_customerinfo`・`import_contract`・`unis_customer_brands`への依存は引き続き無改修で機能する

### 2026-10-23 追記（訂正）

本ADRの決定内容は書き換えず、以下を追記する。

- **ACE後のコンポーネント名（決定1〜3の補足）**：全て新名で作成する（正：`doc/05_改修設計/ace/04_設計/uds_ace_import_s3_folders.md`、台帳#13 2026-10-22追記）。`ace-u1_ecs_start`（Lambda）／`ace-u1_file_split`（ECS Fargate、クラスタ`ace-u1-filesplit`／タスク定義`ace-u1_fargate`）／SQS`ace-sqs_import_u1.fifo`／`ace-import_u1`（Lambda）／削除時`ace-api_unis_copy_file`。決定2の新規S3バケットは`ace-udsapi-u1`（`/`・`error/`・`error/split/`・`split/`、Prefix=`nehan_`／`U1`、Suffix=`.tsv`、各環境プレフィックス`dev-`/`stg-`/`prd-`付き）。Lambda・DBはUDSのAWS環境に残り、GitHubリポジトリのみSGS側へ移設する点（決定3・4）は変わらない。
- **u1のファイル名・Prefixは暫定**：ACE後のファイル名（`U1_`／`nehan_U1_`の踏襲有無）と拡張子は台帳C32でACE側の回答待ち。回答後にトリガーを確定する。
- **csv→tsv対応の具体箇所（見積りA11の訂正）**：「`import_u1`のヘッダー行スキップ処理のコメント解除」は**誤り**であり実施しない。`u1_file_split`が`checkHeader`（正規表現`^"\d\d\d\d`）→`processFile`のfirstLineで先頭ヘッダー行を除去してから分割しているため、分割後ファイルにヘッダーは無く、解除すると分割ファイルごとに先頭データ行が欠落する。正しい対応箇所は、`u1_file_split`の`EXTENSION='.csv'`（L15）・`'\r\n'`のみの行分割（L83、ACE仕様はLF）・ヘッダー判定正規表現（L68、クォート付きCSV前提）、`import_u1`のfast-csv既定デリミタ＝カンマ（L243付近）・`replace(/\\/g,"")`で`\N`が`N`になる箇所（L245。`\N`はNULLで登録＝2026-10-23決定①）。copyToZebra・SGSへのコピーもtsvになる影響の確認が必要。
- **コンテキストの補足**：`import_contract`から`unis_customer_brands`/`unis_customer_brand_confirms`への反映は、master でも 2022-11-25（commit 73979ab）以降コメントアウトされており現本番では動いていない（見積りA14でデッドコード削除）。`import_u1`の依存維持という本決定の結論には影響しない。
- **改修概要書「影響範囲・リスク」の未確認事項の解決**：tsv仕様（区切り文字・文字コード等）は台帳#13（スプレッドシート【ACE後】・S3設計）で、並用期間の切り分けは台帳#13（`ace-`専用バケットで分離）・#14（連携元の運用で二重送信を防止、UDS側対応不要）で解決済み。

### 影響・トレードオフ

- 性能・データ量急増時への影響: 現行のECS Fargate分割処理をそのまま流用するため、想定データ量に対する処理能力面の変化は無い。
- 他システムへの影響: `api_customerinfo`・`import_contract`は無改修で動作継続するため影響なし。SGS側はGitHubリポジトリの保守・デプロイ主体になるが、実行環境（AWSアカウント）はUDS側のまま残る点に留意。
- 運用・保守への影響: **リポジトリの保守主体とAWSインフラの管理主体が分離する**（コードはSGS、インフラはUDS/USENのAWSアカウント）。SGS側メンバーがデプロイ・ログ確認・障害対応を行うためのIAM権限・アクセス経路の整備が必要（未確認、要検討）。
- 今後変更する場合の制約: 将来的にSGS自身のAWS環境へインフラごと移設したくなった場合は、本決定とは別に改めて移設設計が必要になる（本決定はその前段階として「まずはリポジトリ移設のみ」を選んだもの）。

### 関連

- 関連Issue/PR: TODO: 要確認
- 関連ドキュメント: `改修概要書.md`（同フォルダ）、`doc/05_改修設計/ace/02_連携カラム定義/UDS連携ファイル_カラム定義.md`（ADL-133）、`doc/05_改修設計/ace/02_連携カラム定義/改修タスク_コード確認結果.md`（A11、当初の依存関係調査の原典）、`doc/05_改修設計/ace/01_要求事項_進捗管理/タスク一覧.md`（タスク#17）
