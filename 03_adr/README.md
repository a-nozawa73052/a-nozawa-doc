# ADR 一覧

> このファイルはADR自動作成スキルが各ADRのフロントマターから自動生成しています。手で編集しても次回上書きされます。

| No. | タイトル | ステータス | 対象システム | タグ |
|---|---|---|---|---|
| [0001](0001-mdm-mdm2-new-subscription-only.md) | mdm.tsv/mdm2.tsv連携は同時新設申込時のみとし、契約CDが変わる一部取り替えを許可しない | Accepted | ACE, NeOS, UNIS, UDS | 連携ファイル, mdm, mdm2, メニュー変更, 契約CD |
| [0002](0002-no-bulk-backfill-service-detail-code.md) | 既存契約への提供サービス明細コードの一括洗い替えを見送り、都度対応とする | Accepted | ACE, UDS | データ移行, 提供サービス明細, 本番 |
| [0003](0003-stg-split-existing-contracts-by-customer.md) | ステージングでは既存契約を顧客単位でACE検証用に分ける | Accepted | ACE, NeOS, UNIS, UDS | ステージング, テスト, 運用ルール |
| [0004](0004-stg-neos-unis-operation-during-ace-verification.md) | ステージングでのACE検証中のNeOS/UNIS側の扱い | Proposed | ACE, NeOS, UNIS, UDS | ステージング, テスト, 事業部調整, 切り戻し |
| [0005](0005-billing-code-reissue-members-relink.md) | 請求先コードが新しく発番された場合のUMEMBERS側の紐づけ運用 | Proposed | ACE, UNIS, UMEMBERS | 請求先, データ移行, 運用ルール |
| [0006](0006-test-code-verification-and-markdown-result-review.md) | UDSのLambda（インポート系）はテストコードで検証し、結果をMarkdown/CSVに出力して実装者以外がレビューする | Accepted | UDS | テスト, テストコード, Lambda, インポート, レビュー |
| [0007](0007-test-scope-by-environment.md) | ローカルは変更点の単体テストのみとし、統合テストは開発環境（正常系）とステージングで行う | Superseded | UDS | テスト, 単体テスト, 統合テスト, ステージング, 開発環境 |
| [0008](0008-no-test-code-for-web.md) | UDSのWeb側はテストコードを作成せず、画面での手動確認とする | Accepted | UDS | テスト, Web, 画面, 手動検証 |
| [0009](0009-lambda-implementation-approach-and-tech-stack.md) | UDSのLambdaは言語をJavaScript（Node.js）のままとする | Accepted | UDS | Lambda, JavaScript, Node.js, 実装方針, 意思決定 |
| [0010](0010-test-on-dev-env-and-uat-only-on-stg.md) | UDSのACE対応テストは開発環境で網羅し、ステージングはUATのみとする | Accepted | UDS, ACE | テスト, 単体テスト, 結合テスト, 開発環境, ステージング, UAT |

## メタデータ（各ADR冒頭のYAMLフロントマター）
| 項目 | 内容 |
|---|---|
| status | Proposed / Accepted / Deprecated / Superseded |
| date | 決定（または議論）した日 |
| systems | 対象システム |
| tags | 自由タグ |
