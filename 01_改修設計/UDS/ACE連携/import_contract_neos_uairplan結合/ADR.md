# ADR: import_contractとimport_neos_uairplanの統合（ACE改修）

同フォルダの `改修概要書.md` に対応する設計判断の記録。

---

## 0001. ファイル統合後のLambda/workテーブル分類設計

- ステータス: 承認
- 日付: 2026-10-14
- 対象システム・機能: UDS（各サービスリポジトリ\uds\配下、Node.js Lambda群）
- 決定者: TODO: 要確認（会話内で明示的な決定者名の記載なし）

### コンテキスト

NeOS・UNISのACE統合に伴い、現在別ファイルでUDSへ連携している`contract.tsv`（53列、Lambda: `import_contract`）と`neos_uairplan.tsv`（42列、Lambda: `import_neos_uairplan`）が、1つの新contract.tsv（67項目＋新規カラム）に統合される。新ファイルには「初回取込フラグ(`initial_import_flg`)」が付与され、以下が確定仕様（変更不可の前提）となっている。

- `initial_import_flg=1` かつ `neos_item_cd` がデバイス種別マスタ登録済み → 現行`import_contract`と同様に`contracts`へINSERT
- `initial_import_flg=1` かつ未登録 → 処理スルー
- `initial_import_flg=0` → 旧`import_neos_uairplan`相当のUPDATE処理。対象契約コードが`contracts`に存在しなければ処理スルー

現状アーキテクチャは両ファイルとも「preprocess Lambda（S3イベント起動）→ workテーブルへバルクINSERT → 本体Lambda（EventBridge cron、10分おきポーリング）→ contracts/direct_shipments反映」という2段階構成（コード調査により確認済み）。`import_contract`（1869行）・`import_neos_uairplan`（1964行）は、CPM通知・UX SQS送信・direct_shipments反映・BGM/MDM/MDM2連携・UPhone GPS・serialsステータス遷移等、相互に独立して育った大規模な業務ロジックを持つ。

ファイル統合に伴い、新ファイルをどう振り分け、既存の2系統のworkテーブル・本体Lambdaとどう接続するかの設計判断が必要となった。

### 検討した代替案

#### 案A: 分類Lambda1本化＋work/本体Lambdaは現状2系統維持（採用）

- 内容: `preprocess-contract-tsv`／`preprocess-neos-uairplan-tsv`を1本の分類Lambdaに統合し、`initial_import_flg`とデバイス種別マスタ登録有無で`work_imported_contract`／`work_imported_neos_uairplan`へ振り分ける。workテーブル・本体Lambda（`import_contract`／`import_neos_uairplan`）は現状の2系統をそのまま維持する。
- メリット: 本体Lambdaの巨大な業務ロジックに一切手を入れずに済む。既存の冪等性・リトライ機構を完全に温存できる。実装コストが小さい。
- デメリット: 1バッチ内にflg=1行とflg=0行が混在する場合、分類Lambda側のSELECTが最大2回に増える可能性がある。

#### 案B: workテーブル・本体Lambdaも1本化

- 内容: 新work表を新設し、分類Lambdaは存在チェックなしで全行をバルクINSERT。本体Lambdaも1本に統合し、`initial_import_flg`によりINSERT系／UPDATE系の処理を呼び分ける。
- メリット: 同一契約CDのflg=1/flg=0行が同一work表・同一グループ内でid昇順に処理されるため、処理順序の競合が構造的に解消される。長期的な運用対象が1work表・1Lambdaになり監視がシンプルになる。
- デメリット: `import_contract`（1869行）と`import_neos_uairplan`（1964行）という相互に独立した巨大な業務ロジックの統合が必要になり、今回確定している「分岐ロジックは変更不可・業務ロジック統合は対象外」というスコープを超える大規模リファクタリングになる。新work表へのデータ移行手順も別途必要。テストマトリクスが膨らみデグレリスクが高い。

#### 案C: preprocess層は現状2本維持し、ファイル単位の行振り分けのみ変更

- 内容: 新contract.tsvを既存の2つのpreprocess Lambdaにファンアウトさせ、各Lambda側で自分が処理すべきflgの行だけをフィルタする。
- メリット: 一見コード変更量が少ない。
- デメリット: 現行の各preprocess LambdaはS3オブジェクトのライフサイクル管理（SGSコピー・done/error退避・ソース削除）を自分で完結させる設計のため、同一S3オブジェクトに対し独立起動した2つのLambdaがこのライフサイクル処理を競合して行い、不整合（二重コピー、片方削除後のもう片方の読み込み失敗等）を招く。調停ロジックが別途必要になり、実装コストは実質案Aと同等以上になる。

### 決定

案Aを採用する。既存の巨大な業務ロジック・冪等性設計を温存しつつ最小の変更で統合できるため。ただし以下2点を実装の必須条件とする。

1. **`initial_import_flg=0`側の`contracts`存在チェックは分類Lambda（プリプロセス層）では行わない。** 本体Lambda（`import_neos_uairplan`相当）が既に持つ自己修復リトライ機構（存在しなければwork行を残し次回cronで再処理）に一本化して委ねる。これにより、同一ファイル内でflg=1行（新規）が未処理のうちにflg=0行（更新）が先に評価される処理順序競合を、新規実装なしで吸収する。
2. **`initial_import_flg=0`側も、flg=1側と同様に「`neos_item_cd`がデバイス種別マスタに登録済みか」を分類条件に加える**（2026-10-14、ユーザー指摘により追加）。理由：flg=0のみで判定すると、UDSが管理しないSGS専用契約の更新まで`work_imported_neos_uairplan`に取り込んでしまい、当該契約は将来にわたって`contracts`に存在しないため、本体Lambdaが毎回（10分おき）無限にリトライ・エラー通知を発生させ続けるリスクがある。デバイス種別マスタ登録チェックを分類Lambda段階で行うことで、UDS管理外の契約を構造的に除外する。
3. **`import_contract`が現行持っている「`contracts`に契約CDが既に存在する場合のUPDATE処理」は削除する**（2026-10-14、ユーザー指摘により追加）。理由：現行`import_contract`はINSERT/UPDATE両方の分岐を自前で持っているが、統合後は「更新系の処理はflg=0（`import_neos_uairplan`相当）に一本化する」という役割分担にするため、`import_contract`（flg=1経路）側は原則INSERT専用の処理に単純化する。
4. **workテーブル（`work_imported_contract`／`work_imported_neos_uairplan`）のスキーマ改修は必須**（2026-10-14、ユーザー指摘により追加）。統合後のcontract.tsvはカラム構成自体が変わる（新規カラム追加・廃止カラム対応）ため、workテーブルも新カラム構成に追従する改修が必要。あわせて、統合後は`work_imported_neos_uairplan`という名称が実態（neos_uairplan.tsv由来ではなくなる）と合わなくなるため、テーブル名の変更も検討する（具体名称は詳細設計で確定）。
5. **直送対象の区別方法の変更に伴う`import_contract`内のロジック改修が必要**。現行は`neos_item_pac_cd`の特定9値（`import_contract/index.js` L354-361）をキーに直送センターへの振り分け・`direct_shipments`登録判定（L1019-1028）を行っている。統合後は新設カラム「発送先区分」(`ship_to_div`)ベースの判定に置き換えることが決定済み（`neos_item_pac_cd_廃止影響分析.md` 2件目）。**ただし確定しているのはセンター振り分け判定（L354-361相当）のみ**で、`direct_shipments`への登録判定（L1019-1028、NP審査プロセス付き、現状4値ハードコード）が同じ`ship_to_div`で代替できるかは未確認のまま残っている（詳細設計フェーズで要確認）。
6. **`contract_status_name`の自己生成ロジックを新規実装する。本統合対応の初期段階（本体リリース時点）で実装し、暫定措置としての先送りはしない**（2026-10-14、ドキュメント横断レビューで判明。実装タイミングは同日ユーザー指示により確定）。ACEからは`contract_status_name`が連携されなくなり、UDS側で`contract_status_cd`から名称を導出する想定。`api_contractst`が本カラムを外部へ返却するため、空欄期間を作らないよう統合リリースと同時に導入する。
7. **外部API（`api_customerint`／`api_customerupd`）への影響確認（解決済み）**（2026-10-14、ドキュメント横断レビューで判明、同日コード調査で解決）。この2APIは実際に`customer_chain_cd`・`customer_chain_name`・`customer_group_cd`・`customer_group_name`・`customer_group_name_kana`・`customer_group_authority_cd`・`contract_start_date`の7カラムをレスポンスへpass-throughしている（`neos_item_pac_cd/name`・`construction_date`・`digitize_order_branch_cd`は含まれない。レスポンス上の`create_date`フィールドは別のシステム列`created_at`由来で実害なし）。コード調査の結果、required検証・デフォルト値設定・例外処理は無く、UDS側のコード改修は不要と判断。呼び出し元（サイネージ側）は井上さんが確認済みで問題なし。`api_mdminfo`／`api_cominfo`／`api_mdm2info`の`neos_item_pac_cd`/`neos_item_pac_name`についても同日コード確認した結果、同一パターン（コード改修不要、DB制約緩和のみで自動的にnull化）であることを確認済み。
   - **2026-10-14コード調査で判明**: 当初は`api_bgms`／`api_uradioinfo`／`api_devicesignup`も同様に影響すると想定していたが、コード確認の結果、この3APIはSQL発行上`contracts.*`相当を取得するものの、レスポンス構築コードが明示的に特定フィールドのみを抽出しており、**廃止予定13カラムはいずれのレスポンスにも含まれないことを確認した。この3APIは影響対象から除外する**（`api_bgms/bgms.js`・`api_devicesignup/devicesignup.js`・`api_uradioinfo/uradioinfo.js`で確認）。
   - あわせて、`api_uradioinfo`のWHERE抽出条件に使われる`created_at`は、廃止予定の`contracts.create_date`（ACE由来カラム）とは別物で、`import_contract`がINSERT時に`cast(now() as datetime)`で自動設定するシステム列（ACE連携停止の影響を受けない）であることも確認した。
8. **CPM通知処理が廃止予定カラムを送信していないかの確認が必要**（2026-10-14、ドキュメント横断レビューで判明）。`import_contract`内のCPM通知ロジックの実装詳細はコードベースで未確認。
9. **本改修とは別に、廃止カラムNULL化が波及する周辺Lambda・業務ロジックへの対応が必要**（2026-10-14、各サービスリポジトリ\uds\配下の網羅的コードベース調査で判明。詳細: `doc/05_改修設計/ace/02_連携カラム定義/廃止カラム一覧.md` 「2026-10-14 網羅調査で判明した追加の影響・要対応事項」セクション）。
   - **（最重要・リリース前必須確認）`batch_maintenance_account`が本番(main)ブランチで`contracts.status_update_date`依存のまま**の可能性がある（`index.ts:280-281`）。staging/developでは`updated_at`ベースへ修正済みだが、mainへのデプロイ有無が未確認。未反映のままACE切替すると保守アカウント削除バッチが静かに機能停止する。ACE切替前に必ずデプロイ状況を確認すること（`タスク一覧.md` C15）。
   - **（業務判断が必要）`customer_group_authority_cd`は`import_contract`の`newUmemberAuthCd`ロジックでUSEN MEMBERSの権限判定（本社/母店/支店/個店）に使用されている**。NULL化後は常に「個店」判定となる。業務上許容できるか判断が必要（`タスク一覧.md` C16）。
   - UDS-web側で新規に判明した対応範囲として、CP検証機管理_契約検索（`neos_item_name`のAND検索不具合）、端末管理リストCSV（div=22）、直送案件一覧の検索・ソート、交換依頼生成時のコピー処理、`assign.php`の書き込み処理がある（詳細は`廃止カラム一覧.md`参照、該当タスクは見積りHTML側のB区分に追加）。
   - 外部要因として`import_device_replace`（入力ファイル発行元確認、`タスク一覧.md` C17）、`export_serials_to_s3`（UNIS受信側影響確認、`タスク一覧.md` C18）、`contracts`本番DDLのNOT NULL制約（`タスク一覧.md` C19）の3点が未確認のまま残っている。
   - これらは本ADRが対象とする「ファイル統合・分類Lambda設計」の直接のスコープ外だが、同じACE廃止カラムに起因する波及影響であり、本改修のリリース判定に先立って解消しておく必要があるためここに記録する。
10. **`import_contract`の`unis_customer_brands`/`unis_customer_brand_confirms`更新処理（`UnisCustomerBrandsProcess`/`newUmemberAuthCd`）を削除する**（2026-10-14、決定9の調査結果を受けたユーザー決定）。`customer_group_authority_cd`のNULL化により`newUmemberAuthCd`の権限判定（本社/母店/支店/個店）が信頼できなくなるため、判定ロジックごと削除する方針とした。
    - 対象: `U90`/`U91`/`U92`サービスの契約について、`unis_customer_brands`（新規時）・`unis_customer_brand_confirms`（既存時）へUMEMBER権限コードを書き込む一連の処理（`import_contract/index.js`の`UnisCustomerBrandsProcess`・`newUmemberAuthCd`・`insertUnisCustomerBrands`・`insertUnisCustomerBrandConfirms`）
    - **削除前提の追加調査（2026-10-14）**：`unis_customer_brands`/`unis_customer_brand_confirms`を更新する処理は、各サービスリポジトリ\uds配下全体（uds-web＋全Lambda）を横断検索した結果、`import_contract`以外には`import_u1`のみ存在する。ただし`import_u1`の更新対象は`area_cd`/`pref_name`/`area_name`（郵便番号→エリアマスタ引き当て）のみで、`customer_group_authority_cd`由来の`brand_cd`/`company_cd`/`umembers_grant_cd`列は対象外（新規INSERT時にNULL/0初期化するのみ）。そのため今回の削除で`unis_customer_brands`テーブル自体への更新が完全に止まるわけではなく、`umembers_grant_cd`列の更新と`unis_customer_brand_confirms`への書き込みのみが止まる。`import_u1`は別タスク（タスク一覧#17）でSGS側へ移管予定のため、移管後は`unis_customer_brands`の更新主体が実質的にSGS側Lambdaのみになる見込み
    - **未解決のまま残るリスク**：書き込み先の`unis_customer_brands`/`unis_customer_brand_confirms`の値を最終的にどのシステム（USEN MEMBERS本体等）が参照しているかは今回の調査でも特定できていない。削除後は該当カラムの値が更新時点のまま凍結されるため、参照先システムがこの値を定期的に使っているかどうかは別途確認が望ましい（ただし本決定の前提・実装方針には影響しない）

### 2026-10-23 追記（訂正）

本ADRの決定内容は人が確定したものとして書き換えず、以下の訂正・解決状況を追記する。

- **命名（決定4の補足）**：Lambda名・workテーブル名は2026-10-21に確定済み（正：`doc/05_改修設計/ace/04_設計/uds_ace_import_s3_folders.md`）。分類Lambda＝`ace-preprocess_contract-tsv`（トリガーS3 `ace-udsapi-contract`、Prefix=`contract`／Suffix=`.tsv`、`done/`・`error/`あり）、新規契約＝`ace-import_contract_new`（旧`import_contract`）、契約更新＝`ace-import_contract_update`（旧`import_neos_uairplan`）、workテーブル＝`work_imported_contract_new`（旧`work_imported_contract`）／`work_imported_contract_update`（旧`work_imported_neos_uairplan`）。本体2Lambdaは S3 バケットを持たない。本文中の旧名は新名に読み替える。
- **決定5の訂正・解決**：「`neos_item_pac_cd`の特定9値（L354-361）」は誤りで、正しくはセンター振り分けL357の**11値**。`direct_shipments`登録判定も「L1019-1028、4値」は誤りで、正しくは`DIRECT_SHIPMENT_TYPE_CDS`（L127-134）の**6値**（判定L1046-1063）。未確認としていた`direct_shipments`登録判定の`ship_to_div`代替は**2026-10-15に確定済み**（02=顧客直送／03=代理店直送でINSERT。`ship_to_div`は`contracts`に格納せず、workテーブルにのみ保持）。詳細：`neos_item_pac_cd_廃止影響分析.md` 2件目、`a-nozawa-doc/01_改修設計/ACE統合/neos_item_pac_cd廃止対応/ADR.md` NP-0005追記。
- **決定8（CPM通知）は解決済み**：台帳C13（2026-10-14）で、`requestCpmApi`（`import_contract/index.js:1211-1245`）は`umusic_sequential_cd`と`contract_cd`のみを送信しており、廃止予定カラムは含まれないことを確認済み。
- **決定9の未確認事項は解決済み**：
  - `batch_maintenance_account`：台帳C15（2026-10-14）で**本番(main)に反映済み**（`updated_at`ベース）と確認。追加対応不要。
  - `import_device_replace`：台帳C17で廃止済み機能と確認。対象外。
  - `export_serials_to_s3`：台帳C18で解決（`neos_item_name`はマスタ値設定、`customer_group_name`はnull連携で問題なしとACE側回答）。
  - `contracts`本番DDL：台帳C19で解決（`neos_item_name`はNOT NULL維持＋マスタ値設定、`contract_start_date`・`create_date`はNULL許容に緩和）。
  - UDS-web側スコープのうち「リワーク再入庫リストCSV（div=24）の空欄化」は誤り（div=24は`customer_group`系を含まない）。企業名（`customer_group_name`）は全画面で空欄許容・列は残す（2026-10-23 決定②、台帳C7・C34で値連携の可否を検討中）。
- **決定10の訂正（重要）**：決定10は「`customer_group_authority_cd`のNULL化により権限判定が信頼できなくなるため削除」としていたが、コード照合の結果、`UnisCustomerBrandsProcess`/`newUmemberAuthCd`の呼び出しは master でも 2022-11-25（commit 73979ab「unis_customer_brand対応を抜く」）以降 `//await UnisCustomerBrandsProcess(...)` とコメントアウトされており、develop では呼び出し自体が無い。すなわち**現本番は`import_contract`から`unis_customer_brands`/`unis_customer_brand_confirms`へ書き込んでいない**。したがって削除の根拠は「既に本番で呼ばれていないため、残置コード（デッドコード）を削除する」に訂正する（見積りA14、工数0.25〜0.5日）。決定10内の「今回の削除で`umembers_grant_cd`列の更新と`unis_customer_brand_confirms`への書き込みが止まる」「削除後は値が凍結される」という影響記述も、実際には2022-11以降すでに止まっている状態であり、本改修による挙動変化は無い。
- **追加（決定①、2026-10-23）**：ACEのTSVの`\N`はDBに**NULLで登録する**（`''`ではない）。分類Lambdaの`toNull`（`''`と`'NULL'`のみ変換）に`\N`→NULL変換を追加する（見積りA1）。
- **追加（A3）**：`ace-import_contract_new`の`shipping_requests`INSERT（現行L405-445）は、TSVから無くなる`neos_item_pac_cd`/`neos_item_pac_name`・`customer_group_cd`/`customer_group_name`をNULLでINSERTする（`neos_item_name`はC19によりマスタ値）。
- **追加（A4）**：`ace-import_contract_update`（旧`import_neos_uairplan`）は「業務ロジックに手を入れない」前提を超え、`COLUMN_LIST`の67列レイアウトへの全面再構築、`neos_item_cd`逆引き（`getNeosItems`）廃止、`direct_shipments`11列UPDATE（`updateDirectShipments`）削除、連鎖更新の整理等が必要と判明（見積りA4、3〜4日。詳細は改修概要書2章）。本ADRの案A（2系統維持）の採用判断自体は変わらない。
- **要確認（`status_update_date`）**：`import_contract`に`status_update_date`へ`now()`を設定する実装は存在しない。ACE後に`contract_status_cd`が変化した際の`status_update_date`の扱いは要確認。

### 影響・トレードオフ

- 性能・データ量急増時への影響: 分類Lambdaにおいて、1バッチ内にflg=1/flg=0が混在する場合のDB SELECT回数が最大2倍になりうる。想定データ量（日次・ピーク件数）は未確認（TODO: 要確認、`タスク一覧.md` C10）。※2026-10-23追記：C10は台帳上解決済み。
- 他システムへの影響: SGS側が独自に持つ`contract`インポート処理が新カラム構成・`initial_import_flg`に対応可能かは別途確認が必要（※2026-10-23追記：旧記載の参照先C8は台帳から削除済み（SGS側対応前提）のため参照を削除）。また、`api_customerint`等の外部API経由で廃止予定カラムを受け取っている外部連携先への影響も別途確認が必要（TODO: 要確認、`タスク一覧.md` C11）。
- 運用・保守への影響: 既存2系統のログ・アラート運用がそのまま使えるため大きな変化はない。ただし1ファイルの処理結果を追うには分類Lambda＋2本の本体Lambdaのログを横断して確認する必要がある。
- 今後変更する場合の制約: `initial_import_flg=0`のUPDATE専用パスは確定仕様上恒久機能であり、本決定のどの案を選んでも`import_neos_uairplan`相当のロジック自体を完全に廃止することはできない（ファイルの統合はできるが、ロジックの統合・廃止は別論点）。将来的に業務ロジックそのものを統合したくなった場合は、案Bを次フェーズの選択肢として検討する。

### 関連

- 関連Issue/PR: TODO: 要確認
- 関連ドキュメント: `改修概要書.md`（同フォルダ）、`doc/05_改修設計/ace/02_連携カラム定義/UDS連携ファイル_カラム定義.md`（確定仕様の原典）、`doc/05_改修設計/ace/01_要求事項_進捗管理/タスク一覧.md`（C9〜C10: 関連確認事項、C15〜C19: 網羅調査で判明した周辺影響の確認事項。いずれも解決済み、C8は台帳から削除済み）、`doc/05_改修設計/ace/04_設計/uds_ace_import_s3_folders.md`（命名の正）
