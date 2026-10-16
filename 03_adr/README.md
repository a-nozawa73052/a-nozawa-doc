# ADR 一覧

> このファイルはADR自動作成スキルが各ADRのフロントマターから自動生成しています。手で編集しても次回上書きされます。

| No. | タイトル | ステータス | 対象システム | タグ |
|---|---|---|---|---|
| [0001](0001-mdm-mdm2-new-subscription-only.md) | mdm.tsv/mdm2.tsv連携は同時新設申込時のみとし、契約CDが変わる一部取り替えを許可しない | Accepted | ACE, NeOS, UNIS, UDS | 連携ファイル, mdm, mdm2, メニュー変更, 契約CD |
| [0002](0002-no-bulk-backfill-service-detail-code.md) | 既存契約への提供サービス明細コードの一括洗い替えを見送り、都度対応とする | Accepted | ACE, UDS | データ移行, 提供サービス明細, 本番 |
| [0003](0003-stg-split-existing-contracts-by-customer.md) | ステージングでは既存契約を顧客単位でACE検証用に分ける | Accepted | ACE, NeOS, UNIS, UDS | ステージング, テスト, 運用ルール |
| [0004](0004-stg-neos-unis-operation-during-ace-verification.md) | ステージングでのACE検証中のNeOS/UNIS側の扱い | Proposed | ACE, NeOS, UNIS, UDS | ステージング, テスト, 事業部調整, 切り戻し |
| [0005](0005-billing-code-reissue-members-relink.md) | 請求先コードが新しく発番された場合のUMEMBERS側の紐づけ運用 | Proposed | ACE, UNIS, UMEMBERS | 請求先, データ移行, 運用ルール |
| [0006](0006-unify-contract-tsv-initial-import-flag.md) | contract.tsvとneos_uairplan.tsvをcontract.tsvに統合し、初回取り込みフラグで処理を振り分ける | Accepted | ACE, NeOS, UNIS, UDS | 連携ファイル, contract.tsv, neos_uairplan.tsv, 初回取り込みフラグ, ワークテーブル |
| [0007](0007-keep-service-detail-code-in-uds.md) | UDSにも提供サービス明細コードを保持し、contract.tsvのカラムとして連携する | Accepted | ACE, UDS, UMEMBERS | 提供サービス明細, contract.tsv, 問い合わせ, キー変更 |
| [0008](0008-ship-to-div-for-direct-shipment.md) | 直送の判断は、UDS内の判定をやめてcontract.tsvの発送先区分で行う | Accepted | ACE, NeOS, UDS | 直送, 発送先区分, UDS Web, contract.tsv |
| [0009](0009-com-tsv-update-key-contract-cd-only.md) | com.tsvの更新・挿入の判定キーを契約CD（contract_cd）のみに変更する | Accepted | ACE, NeOS, UDS | com.tsv, 更新判定, プラン変更, contract_cd |
| [0010](0010-plan-change-detection-by-neos-item-cd.md) | プラン変更は、DBのNeOS品目CDと連携値の差異で判定して上書きする | Accepted | ACE, UDS | プラン変更, neos_item_cd, バンドコード, 判定ロジック |
| [0011](0011-keep-obsolete-columns-null-fixed.md) | フェーズ1では廃止される項目のカラムを残し、NULL固定で扱う | Accepted | ACE, UDS | フェーズ1, カラム削除, NULL固定, UDS API, エクスポート |
| [0012](0012-new-s3-lambda-github-migration.md) | ACE用のインポート系S3・Lambdaをすべて新規に作り、GitLabからGitHubへ移行する | Accepted | ACE, UDS | S3, Lambda, GitHub, バケット名, インポート |
| [0013](0013-cloudformation-for-bucket-and-trigger.md) | バケットとトリガーはCloudFormationでテンプレート化する | Accepted | UDS | CloudFormation, CDK, S3, トリガー, IaC |
| [0014](0014-typescript-adoption-for-import-lambda.md) | インポート系LambdaをTypeScriptで書くかどうか | Proposed | UDS | TypeScript, JavaScript, インポートLambda, 開発工数 |
| [0015](0015-test-design-and-test-code-policy.md) | インポート系・Web改修のテスト設計・テストコードの進め方 | Proposed | UDS | テスト, テスト設計, テストコード, レビュー, AI |

## メタデータ（各ADR冒頭のYAMLフロントマター）
| 項目 | 内容 |
|---|---|
| status | Proposed / Accepted / Deprecated / Superseded |
| date | 決定（または議論）した日 |
| systems | 対象システム |
| tags | 自由タグ |

## 出典
- 会議: ACE連携まわり（2026-10-16 12:00 JST）: https://docs.google.com/document/d/1sHQ53EJtCansJ1jXd7speqaN4LbIhHJXVEGOEkjrsYc
- 会議: ACEの話（2026-10-16 16:59 JST）: https://docs.google.com/document/d/1n-Av2kjhakuFZvuhaYh-807svACt8pbR069ukM9-Nd4
- 用語集: [UDS_用語集](https://docs.google.com/document/d/1YGHdWa1Y-6_eCtrsfa9Xl9afwtkM9WSFF18RWJcbMOY)

## 作成時の補正方針
- 表記はUDS用語集に合わせた（NeOS、UNIS、契約CD（contract_cd）、NeOS品目CD（neos_item_cd）、mdm.tsv/mdm2.tsv など）。
- 音声認識の誤変換は次のように補正した: 迷彩/明産/面細 → 明細、エース → ACE、ネオス/寝オス → NeOS、ユニス/ニス → UNIS、低下 → 定価、ゼブラコード → ZEBRA Ⅱ（店舗情報管理）の店舗CD、メンバーズ → UMEMBERS（要確認）。
- 提供サービス明細コード・請求先コードなどACE側の用語は、用語集に載っていないため会議での呼び方のままとした。
- 会議途中の地震速報など、議題と関係ないやり取りは除外した。
- 解釈に確信が持てない箇所には「要確認」と記載した。
