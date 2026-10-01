# 改修概要 — キッティング画面 QRシール印刷機能

**作成日:** 2026-05-25  
**対象ブランチ:** `feature/force_create_headbranch_stocks`

---

## 1. 改修目的

キッティング画面のQRシール印刷機能について、以下2点の改修を行う。

| # | 改修内容 | 概要 |
|---|---------|------|
| ① | セット品（複数依頼）対応 | 1キッティングに複数のQR対象依頼が紐づく場合、依頼件数分のPDFページを生成する |
| ② | URX対応の新規追加 | 既存UMEとは別に、URXを対象としたQRシール印刷ボタンを追加する |

---

## 2. 用語定義

| 用語 | 定義 |
|------|------|
| キッティング | `shipping_requests` テーブルの1レコード = 1キッティング |
| セット品 | 同一 `unis_customer_cd` + `request_date` + `neos_item_pac_cd` を持つ `shipping_requests` の集合（複数レコードになる場合あり） |
| UME | 既存のQR出力対象機種。`device_types.qrcode_flg = 1` |
| URX | 今回追加のQR出力対象機種。`device_types.qrcode_flg = 2` |

---

## 3. 改修① — セット品（複数依頼）対応

### 3-1. 対象範囲

UME・URX の両方に適用する。

### 3-2. 変更仕様

| 項目 | 変更前 | 変更後 |
|------|-------|-------|
| 出力ページ数 | 1ページ固定 | QR対象依頼件数分のページを生成 |
| PDFファイル数 | 1ファイル | 1ファイル（複数ページをまとめる） |
| ページ順序 | — | `shipping_requests.id` 昇順 |
| serial_cd 記載 | なし | 各ページの右上に該当依頼の `serial_cd` を記載 |

### 3-3. 実装箇所

#### `src/public_html/fuel/app/classes/pdf/creater/qrcode/label.php`

`create()` メソッドの引数をページ配列に変更する。

```php
// 変更前
public function create($qrcode_filename)

// 変更後
public function create(array $pages)
// $pages = [
//     ['image' => '{filename}.png', 'serial_cd' => '{serial_cd}'],
//     ...
// ]
```

- `$pages` の各要素に対して1ページを生成する
- QRコードグリッド（8行×5列、既存レイアウト）を描画後、`serial_cd` を右上に追記する
- **serial_cd の座標・フォントサイズは、実際のPDFテンプレート（`qrcode.pdf`）を確認のうえ決定すること**（現在の暫定値: X=155, Y=10, 8pt）

#### `src/public_html/fuel/app/modules/manage/classes/controller/center/kitting.php`

`action_download_qrcode_label_save()` を以下の流れに変更する。

1. `get_set_shipping_request()` でセット全行を取得する
   - `get_set_shipping_request()` 自体は改修しない。デフォルトの並び順（`device_types.device_type` 昇順→
     `created_at` 降順）は変更されないため、id昇順ソートは本アクション内で明示的に行う（後述3.）
2. UME対象行（後述 `get_ume_eligible_rows()`）に絞り込む
3. `usort()` 等で `shipping_requests.id` 昇順に明示的に再ソートする
   - `get_set_shipping_request()` は他アクション（select_list/view/return等）と共有のヘルパーであり、
     そちらの並び順（型番昇順→作成日時降順）は変更しない。id昇順ソートは本アクション内でのみ完結させること
4. 対象行ごとにQR画像を生成し、ページ配列を構築する
   - 一時画像ファイル名は `{行ID}.png`（行単位の一意性のみ）とする
   - リクエスト実行ごとに一意なトークンの付与は当初検討したが、スケジュールの都合により
     本改修では見送る（同フォルダ`ADR.md`のADR 0005参照）
   - 見送りに伴い、同一依頼IDに対する処理が同時に2回実行された場合（ダブルクリック・複数タブ・
     複数端末からの同時押下等）に同一ファイルパスへ競合書き込みが発生し、誤ったQR画像が
     別ページに混入するリスクは未対策のまま残る。現状の運用では発生しにくいと判断し許容する
5. PDFを生成後、一時画像を全件削除する
6. PDFを保存・ダウンロードする

---

## 4. 改修② — URX QRシール印刷の新規追加

### 4-1. ボタン表示仕様

既存の「QRシール印刷」ボタンを以下の2ボタン構成に変更する。

| ボタン名 | 表示条件 |
|---------|---------|
| URX-03 QRシール印刷 | セット内にUME対象依頼が1件以上ある場合 |
| URX-05 QRシール印刷 | セット内にURX対象依頼が1件以上ある場合 |

- `URX-03`/`URX-05`は本改修の管理番号（チケット番号）に由来する表記であり、キッティング作業者向けの
  画面上もこの名称をそのまま使用する（意図的な仕様であることをレビューで確認済み）

- 両方該当する場合は両ボタンを表示する
- どちらか一方のみ該当する場合は、該当するボタンのみ表示する
- どちらも該当しない場合は両ボタンを非表示にする
- 2つのボタンは独立しており、押下ごとに別々のPDFを出力する

### 4-2. 対象判定ロジック

#### UME（既存ロジックを流用）

```
contract_mdm2_devices.contract_cd = shipping_requests.contract_cd
  → contract_mdm2_devices.option2_neos_item_cd を取得
  → device_types.neos_item_cd で結合
  → device_types.qrcode_flg = 1 であれば UME 対象
```

#### URX（新規ロジック）

```
contracts.contract_cd = shipping_requests.contract_cd
  → contracts.neos_item_cd を取得
  → device_types.neos_item_cd で結合
  → device_types.qrcode_flg = 2 であれば URX 対象
```

> **注意:** URXはUMEのmdm2参照ロジック（`contract_mdm2_devices`）を**使わない**。  
> 既存のUME判定ロジックは変更しないこと。

> **注意:** `qr_flg`/`qr_id`（presenter/center/kitting/view.php）は「セット内に対象が1件でもあるか」の
> 真偽判定＋代表1件のID取得ロジックであり、「対象行を配列で全件返す」ロジックとは実装が異なる。
> 実装では`qr_flg`/`qr_id`を削除・改名せず維持し、ボタン押下時のIDも引き続きこの代表行IDを使用する
> （メイン依頼IDへの統一は行わない）。QR生成対象行の絞り込みは、`get_qr_target_requests()`内の
> `filter_ume_target_requests()`/`filter_urx_target_requests()`が判定条件（qrcode_flg判定）を
> それぞれ個別に実装する。

### 4-3. QRコードURL形式

| 種別 | 環境 | URL |
|------|------|-----|
| UME | 全環境共通・変更なし | `https://web.musicvideo.usen.com/?param1={unis_customer_cd}&param2={contract_cd}` |
| URX | STG | `https://web-stg.requestvision.usen.com/loading?param1={unis_customer_cd}&param2={contract_cd}` |
| URX | PRD | `https://web2.musicvideo.usen.com/loading?param1={unis_customer_cd}&param2={contract_cd}` |

`unis_customer_cd`・`contract_cd` はそれぞれの `shipping_requests` 行の値を使用する。

> **注意（4度にわたり訂正）:**
> - 1回目（2026-09-28）: URXのみ環境依存と判明（UMEは変更なしと誤認していた）
> - 2回目（2026-09-29）: **UMEも環境依存かつパスが`/loading`に変更**されており、さらに
>   URXのSTGドメインも`web-stg2`→`web-stg`に訂正された。`web-stg2`は**UME側のSTG用ドメイン**であり、
>   URXのSTGとは別ドメインなので混同注意
> - 3回目（2026-09-29）: UME PRDは現状のまま変更不要と判明（UME STGのみ変更が必要、と一時判断）
> - 4回目（2026-09-29、本訂正）: **UMEはSTG・PRDとも変更不要**と最終確定。結局、本改修で
>   URL形式が変わるのは**URXのみ**（1回目の判断が結果的に正しかった）
>
> 現時点で判明している最終仕様は上表の2パターン（URXのSTG/PRD）のみ。ローカル/開発環境向けの
> URLは別途確認が必要（8章参照）。

### 4-3b. PDFファイル名

| 種別 | 変更前 | 変更後 |
|------|-------|-------|
| UME | `{依頼ID}_qrcode.pdf` | `{依頼ID}_ume_qrcode.pdf` |
| URX | （新規） | `{依頼ID}_urx_qrcode.pdf` |

- `依頼ID`は、セット内でその種別（UME/URX）の対象と判定された行のうち、`$rows`の並び順
  （型番昇順→作成日時降順）で最初に見つかった行のID（既存`qr_id`/`urx_qr_id`と同じ
  「代表行ID」方式を維持する）。画面URLの依頼ID（`$data['one']['id']`）とは一致しない場合がある

### 4-4. 実装箇所

#### `src/public_html/fuel/app/modules/manage/classes/presenter/center/kitting/view.php`

- 既存 `qr_flg` は改名せず維持する。判定ロジックは、`get_one()`に`qrcode_flg='1'`条件を追加し、
  「代表1件がたまたま非対象だと誤ってfalseになる」既存の不具合を修正する
- 既存 `qr_id` も維持する（「セット内でUME対象と判定された最初の行のID」を返す代表行ID方式のまま。
  メイン依頼IDへの統一は行わない）
- `urx_qr_flg` / `urx_qr_id` を新規追加する（`qr_flg` / `qr_id` とロジック・命名を対称にする）

#### `src/public_html/fuel/app/modules/manage/views/center/kitting/view.php`

- 既存の `$qr_flg` / `$qr_id` を使ったUMEボタンは維持し、`$urx_qr_flg` / `$urx_qr_id` を使った
  URXボタンを追加する2ボタン構成に変更する
- ボタン押下時のIDは、UME・URXそれぞれ `$qr_id($data['rows'])` / `$urx_qr_id($data['rows'])`
  （セット内の代表行ID）を使用する。画面URLの依頼ID（`$data['one']['id']`）とは一致しない場合がある
  （4-3b節参照）

#### `src/public_html/fuel/app/modules/manage/classes/controller/center/kitting.php`

- `action_download_qrcode_label_save($shipping_request_id)`（UME）のPDFファイル名を
  `{shipping_request_id}_qrcode.pdf` → `{shipping_request_id}_ume_qrcode.pdf` に変更する
- `action_download_urx_qrcode_label_save($shipping_request_id)` を新規追加する
  - 処理フローはUMEと同じ（判定ロジックとQR URLのみ異なる）
  - PDFファイル名: `{shipping_request_id}_urx_qrcode.pdf`
  - id昇順ソート・一時ファイル名のトークン化もUME側と同様に適用する
- ヘルパーメソッドを追加する
  - `get_qr_target_requests($shipping_request, $qrcode_flg)`: セット単位でQR対象依頼をid昇順で取得する
    - 内部で`Common_Shipping_Request::get_set_common_part_query()`を直接使用する（`get_set_shipping_request()`は
      呼ばない）。既存`get_set_shipping_request()`が課している `serials.id != null`（引き当て済みのみ対象）
      という条件を、本メソッドにも必ず含めること（既存の対象行の考え方と揃える）
  - `filter_ume_target_requests($rows)`: UME対象行を返す
  - `filter_urx_target_requests($rows)`: URX対象行を返す
    - `contracts.contract_cd`をキーに、`device_types`と`contracts`をINNER JOIN
      （`device_types.neos_item_cd = contracts.neos_item_cd`）した独立クエリで
      `qrcode_flg = '2'`のcontract_cd集合を取得し、`$rows`をこの集合でフィルタする
    - 当初案（`Common_Shipping_Request::get_set_common_part_query()`のSELECT句に
      `contracts.neos_item_cd`を追加する方式）ではなく、共通クエリに手を入れない本方式を
      採用する。他の呼び出し元（select_list/view/return等）への影響がなく、当初案より安全である

#### `src/public_html/public/assets/js/script.js`

- `output_qr_label(ajax_url, id, suffix)` に第3引数`suffix`を追加し、UME/URX共通の関数にする
  - `suffix`未指定時は従来通り`_qrcode`（今回`_ume_qrcode`に変更、4-3b節参照）
  - PDFパス: `/contents/pdf/qrcode/{id}{suffix}.pdf`
- URXボタンからは `output_qr_label(ajax_url, id, '_urx_qrcode')` として呼び出す
  （`output_urx_qr_label`という別関数は追加しない）

#### `src/public_html/fuel/app/classes/upload/csv/master/device.php`

- `validate_qrcode_flg()` を '0'・'1'・'2' を許容するよう修正する
  - 現状は '0'/'1' 以外をエラーとするため、URX機種（qrcode_flg=2）のマスタ情報を
    通常のCSVマスタアップロード画面から将来更新できなくなる
  - エラーメッセージ「は0、または、1で入力してください」も「0、1、または、2で」に修正する

---

## 5. 影響範囲

| ファイル | 種別 | 内容 |
|---------|------|------|
| `pdf/creater/qrcode/label.php` | 改修 | create() インターフェース変更 |
| `presenter/center/kitting/view.php` | 改修 | ume_flg/urx_flg への変更 |
| `views/center/kitting/view.php` | 改修 | ボタン2本化 |
| `controller/center/kitting.php` | 改修・追加 | UMEアクション改修、URXアクション追加 |
| `assets/js/script.js` | 追加 | output_urx_qr_label() 追加 |
| `upload/csv/master/device.php` | 改修 | validate_qrcode_flg()を0/1/2許容に修正 |

---

## 6. スコープ外

- `device_types` マスタへの `qrcode_flg = 2` の**初回データ投入**は本改修のスコープ外。別途データ投入を依頼すること
  （CSVマスタアップロードのバリデーション改修は本改修に含む。初回投入時点でバリデーション改修が
  　未リリースの場合は、直接DB投入等の代替手段を検討すること）
- 既存UMEのQRコードURL形式は変更しない
- 既存PDFテンプレート（`qrcode.pdf`）のレイアウトは変更しない
- 同一依頼IDに対する同時実行（ダブルクリック・複数タブ・複数端末からの同時押下）自体の防止
  （DB Advisory Lock等の排他制御）は本改修のスコープ外とする
- 一時ファイル名のトークン化（同時実行時のファイル衝突・QR誤混入対策）についても、
  スケジュールの都合により本改修では見送る。現状の運用では同一依頼IDへの同時実行が
  実質的に起こりにくいと判断し、当面のリスクとして許容する
  （詳細は同フォルダ`ADR.md`のADR 0005参照）

---

## 7. テスト観点

| パターン | UMEボタン | URXボタン |
|---------|----------|----------|
| UMEのみ対象あり（単一依頼） | 表示・1ページPDF生成 | 非表示 |
| URXのみ対象あり（単一依頼） | 非表示 | 表示・1ページPDF生成 |
| UME・URX両方対象あり | 表示 | 表示（それぞれ独立してPDF生成） |
| どちらも対象なし | 非表示 | 非表示 |
| UMEセット品（複数依頼） | 表示・依頼件数分のページを持つPDF生成 | — |
| URXセット品（複数依頼） | — | 表示・依頼件数分のページを持つPDF生成 |
| 各PDFページの右上 | 該当依頼の `serial_cd` が記載されていること | 同左 |
| ページ順序 | `shipping_requests.id` 昇順であること | 同左 |
| QRコードURL（UME・STG） | `https://web-stg2.requestvision.usen.com/loading?param1=...&param2=...` | — |
| QRコードURL（UME） | `https://web.musicvideo.usen.com/?param1=...&param2=...`（変更なし） | — |
| QRコードURL（URX・STG） | — | `https://web-stg.requestvision.usen.com/loading?param1=...&param2=...` |
| QRコードURL（URX・PRD） | — | `https://web2.musicvideo.usen.com/loading?param1=...&param2=...` |
| 既存UME動作（単一依頼） | 既存と同等の動作であること | — |
| PDFファイル名（UME） | `{依頼ID}_ume_qrcode.pdf` であること | — |
| PDFファイル名（URX） | — | `{依頼ID}_urx_qrcode.pdf` であること |

---

## 8. 確認事項

- [ ] serial_cd の記載座標・フォントサイズをPDFテンプレート上で確認し確定する（現在の暫定値: X=155, Y=10, 8pt）
- [ ] `device_types.qrcode_flg = 2` のマスタデータ投入タイミングをデータ担当者と調整する
- [ ] `validate_qrcode_flg()` 改修のリリースタイミングと、`qrcode_flg = 2` 初回データ投入のタイミングの前後関係を確認する
- [x] 同一依頼IDへの同時押下時に二重処理・二重ダウンロードが発生し得ることについて、現場運用上許容できるか確認する
  → スケジュールの都合により今回は許容する判断とした（ADR 0005参照）
- [ ] `get_qr_target_requests()` に `serials.id != null`（引き当て済みのみ対象）条件が抜けている実装上の
  誤りを修正し、`get_set_shipping_request()` と対象行の考え方を揃える
- [ ] URX QRコードURLについて、ローカル/開発環境向けの値を確認する（STG/PRDのみ判明）
- [ ] 既にdevelop・staging双方にマージ済みのコードは、URXのみ環境分岐のない誤ったURLの
  ままであり、修正が必要（PR #306で対応中。UMEは変更不要と確定したため対応対象外）
- [ ] 開発環境テストマトリクスのNo.24（QRコードURL_URX）は誤ったURLに対して実施・OK済みのため、
  修正後に再テストが必要（No.23のUMEは変更がないため再テスト不要）
- [ ] URXのSTGドメインが`web-stg2`（誤）→`web-stg`（正）に訂正された点を実装・テスト双方で
  確実に反映する（`web-stg2`はUME用ドメインであり混同しやすい）
