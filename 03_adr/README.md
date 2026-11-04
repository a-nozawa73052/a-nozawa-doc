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
| [0010](0010-np-review-narrow-by-sales-department.md) | NP審査の対象は営業所属部署名で絞り込み、直送カテゴリー名は審査に使わない | Accepted | UDS, UNIS, NeOS | NP審査, 営業所属部署, 直送カテゴリー, 検索条件, 運用ルール |
| [0011](0011-department-change-and-np-review-status.md) | 営業担当者の部署移動時に、営業所属部署の反映とNP審査ステータスをどう扱うか | Proposed | UDS, UNIS | NP審査, 部署移動, 営業所属部署, UNIS連携, 審査漏れ |
| [0012](0012-all-fields-csv-export-500-per-page-limit.md) | UDSの全項目CSV出力の1ページ500件の上限を、当面は引き上げず、対応可否を調査する | Proposed | UDS | CSV出力, 件数上限, 全項目出力, システム負荷, 改修要望 |
| [0013](0013-test-on-dev-env-and-uat-only-on-stg.md) | UDSのACE対応テストは開発環境で網羅し、ステージングはUATのみとする | Accepted | UDS, ACE | テスト, 単体テスト, 結合テスト, 開発環境, ステージング, UAT |
| [0014](0014-remove-billing-month-from-all-fields-csv.md) | ACE移行で連携されなくなる「明細課金月」を、直送案件の全項目CSVから削除する | Accepted | ACE, NeOS, UNIS, UDS | 明細課金月, 全項目CSV, ACE移行, 項目削除, 監査報告 |
| [0015](0015-identify-is-alliance-contracts-after-ace.md) | ACE移行後に、NP審査の対象となるISとアライアンス案件を何で判別するか | Proposed | ACE, NeOS, UNIS, UDS | NP審査, 請求先コード, 一括請求, IS案件, アライアンス案件, ACE移行 |
| [0016](0016-failure-replacement-new-purchase-flow.md) | メーカー交換（新規シリアル）になった故障端末の購入契約を、NeOS・UDS・GRSでどう扱うか | Proposed | UDS, NeOS, UNIS Ⅱ, GRS, IDM | 故障交換, 新規購入, 引き当て, サービスコード, キッティング, GRS |
| [0017](0017-ace-contract-mode-add-umembers-consent.md) | ACEの成約モードにUMEMBERSを追加し、顧客がUMEMBERS上で申込書を確認・同意できるようにするか | Proposed | ACE, UMEMBERS, NeOS, UNIS | 成約モード, UMEMBERS, 申込書, 同意, クラウドサイン, 承認フロー |
| [0018](0018-contract-confirmation-docs-issue-timing-and-unit.md) | 契約内容確認書と作業完了報告書は施工完了時に交付し、書類ごとの発行単位を揃える | Accepted | ACE, UMEMBERS, UDS | 契約内容確認書, 作業完了報告書, 申込書, 施工完了, 通信事業法, 書類発行 |
| [0019](0019-defer-toc-shipping-change-and-set-item-split.md) | 残量検知（ロボット巡回）のTOC出荷対応のUDS改修とセットマスター作成は保留し、方針確定後に改めて依頼する | Accepted | UDS, NeOS, UNIS | 残量検知, ロボット巡回, TOC, 出荷先, セット品目, 改修保留 |
| [0020](0020-irregular-shipping-form-entered-by-product-side.md) | 既存顧客向けのロボット残量検知のイレギュラー発送依頼は、営業ではなくプロダクト側がフォームに入力する | Accepted | UDS | イレギュラー発送, 発送依頼フォーム, 残量検知, ロボット巡回, 運用ルール |
| [0021](0021-uau03-default-shipping-destination.md) | 残量検知ロボット巡回のユニット（UAU 03）の出荷先デフォルトをどうするか | Proposed | UDS, NeOS | 出荷先, デフォルト, TOC, セット品目, 残量検知, ロボット巡回 |
| [0022](0022-contract-owner-umid-link-required-for-all.md) | 申込では契約担当者にUMIDを紐付け、原則として全員から取得する | Accepted | ACE, UMEMBERS, NeOS | UMID, 契約担当者, アクティベーション, 包括契約, 営業ルール |
| [0023](0023-email-required-in-principle-exceptions-case-by-case.md) | メールアドレスは原則必須とし、外す必要がある例外は発生した時に検討する | Accepted | ACE, UMEMBERS | メールアドレス, 必須化, 例外対応, インサイドセールス, SMS |
| [0024](0024-ace-applicant-contact-requires-umid-activation.md) | ACEの申込担当者（先方担当者）にUMIDの紐付けと認証を必須とし、未了なら本番データが動く操作に進めない | Accepted | ACE, UMEMBERS | 申込担当者, 先方担当者, UMID, アクティベーション, 申込UI |
| [0025](0025-ace-umid-link-key-email-or-login-id.md) | ACEとUMIDの認証連携で、メールアドレスとログインID（ユーザーID）のどちらをキーにするか | Proposed | ACE, UMEMBERS | UMID, 認証連携, ログインID, メールアドレス, ユーザーID |
| [0026](0026-sub-email-only-accounts-promotion-and-merge.md) | 認証用メールアドレスがなく、サブメールアドレスだけのUMEMBERSアカウントをどう扱うか | Proposed | ACE, UMEMBERS, UNIS | サブメールアドレス, 認証用メールアドレス, アカウント統合, データ移行, UMID |
| [0027](0027-email-validity-check-no-skip-required-auth.md) | メールアドレスの有効性チェックを経ずに進められるスキップをなくし、認証を必須とするか | Proposed | ACE, UMEMBERS | メールアドレス, 有効性チェック, 認証, アカウント作成メール, スキップ廃止 |
| [0028](0028-billing-contact-access-granted-in-umembers-after-application.md) | 請求担当者など別の担当者への閲覧権限は、申込時ではなく申込後にUMEMBERSでお客様自身が付与する | Accepted | ACE, UMEMBERS | 請求担当者, アクセス権限, UMEMBERS, 申込担当者, 案件分割 |
| [0029](0029-add-contract-party-code-and-name-to-shipping-csv.md) | ACE移行後の出荷データ（出荷CSV）に、契約先コードと契約先名称を付与する | Accepted | ACE, UDS | 出荷データ, 出荷CSV, 契約先コード, 契約先名称, 一括案件, 見込み |
| [0030](0030-sales-pre-report-rule-for-bulk-projects.md) | 一括案件は、営業が契約先名称・契約先コードを添えて事前申告するルールを設ける | Accepted | ACE, UDS | 一括案件, 事前申告, 営業ルール, 契約先コード, 見込み精度 |
| [0031](0031-no-billing-month-integration-from-ace-to-uds.md) | 明細課金月はACEからUDSへ連携せず、確認はACE側で行う（運用調整はOM部経由） | Accepted | ACE, UDS | 明細課金月, ACE連携, 連携除外, 提供サービス料金, 運用対応 |
| [0032](0032-uds-fix-undersized-column-lengths-for-ace.md) | ACE連携のデータ項目のうち、UDS側のカラム長が小さい4箇所をUDS側で修正する | Accepted | ACE, UDS | カラム長, DBスキーマ, ACE連携, 物理名, 論理名 |
| [0033](0033-ace-version-up-delay-and-scope-of-product-system-dev.md) | プロダクトシステム開発側のバージョンアップ遅延と対応範囲をどう判断するか | Proposed | ACE, UDS, UMEMBERS | ACE対応, バージョンアップ, スケジュール遅延, 脆弱性対応, 上層部判断 |

## メタデータ（各ADR冒頭のYAMLフロントマター）
| 項目 | 内容 |
|---|---|
| status | Proposed / Accepted / Deprecated / Superseded |
| date | 決定（または議論）した日 |
| systems | 対象システム |
| tags | 自由タグ |
