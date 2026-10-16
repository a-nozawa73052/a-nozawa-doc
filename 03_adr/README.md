# ADR 一覧（ACE連携まわり）

| No. | タイトル | ステータス | 対象システム | タグ |
|---|---|---|---|---|
| [0001](0001-mdm-mdm2-new-subscription-only.md) | mdm.tsv/mdm2.tsv連携は同時新設申込時のみとし、契約CDが変わる一部取り替えを許可しない | Accepted | ACE, NeOS, UDS | 連携ファイル, mdm, mdm2, メニュー変更, 契約CD |
| [0002](0002-no-bulk-backfill-service-detail-code.md) | 既存契約への提供サービス明細コードの一括洗い替えを見送り、都度対応とする | Accepted | ACE, UDS | データ移行, 提供サービス明細, 本番 |
| [0003](0003-stg-split-existing-contracts-by-customer.md) | ステージングでは既存契約を顧客単位でACE検証用に分ける | Accepted | ACE, NeOS, UNIS, UDS | ステージング, テスト, 運用ルール |
| [0004](0004-stg-neos-unis-operation-during-ace-verification.md) | ステージングでのACE検証中のNeOS/UNIS側の扱い | Proposed | ACE, NeOS, UNIS, UDS | ステージング, テスト, 事業部調整, 切り戻し |
| [0005](0005-billing-code-reissue-members-relink.md) | 請求先コードが新しく発番された場合のUMEMBERS側の紐づけ運用 | Proposed | ACE, UNIS, UMEMBERS | 請求先, データ移行, 運用ルール |

## メタデータ（各ADR冒頭のYAMLフロントマター）
| 項目 | 内容 |
|---|---|
| status | Proposed / Accepted / Deprecated / Superseded |
| date | 決定（または議論）した日 |
| systems | 対象システム |
| tags | 自由タグ |

## 出典
- 会議: ACE連携まわり（2026-10-16 12:00 JST）
- Geminiによるメモと文字起こし: https://docs.google.com/document/d/1sHQ53EJtCansJ1jXd7speqaN4LbIhHJXVEGOEkjrsYc
- 用語集: [UDS_用語集](https://docs.google.com/document/d/1YGHdWa1Y-6_eCtrsfa9Xl9afwtkM9WSFF18RWJcbMOY)

## 作成時の補正方針
- 表記はUDS用語集に合わせた（NeOS、UNIS、契約CD（contract_cd）、NeOS品目CD（neos_item_cd）、mdm.tsv/mdm2.tsv など）。
- 音声認識の誤変換は次のように補正した: 迷彩/明産/面細 → 明細、エース → ACE、ネオス/寝オス → NeOS、ユニス/ニス → UNIS、低下 → 定価、ゼブラコード → ZEBRA Ⅱ（店舗情報管理）の店舗CD、メンバーズ → UMEMBERS（要確認）。
- 提供サービス明細コード・請求先コードなどACE側の用語は、用語集に載っていないため会議での呼び方のままとした。
- 会議途中の地震速報など、議題と関係ないやり取りは除外した。
- 解釈に確信が持てない箇所には「要確認」と記載した。
