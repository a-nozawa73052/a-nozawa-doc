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
2. UME対象行（後述 `get_ume_eligible_rows()`）に絞り込む
3. `shipping_requests.id` 昇順でソートする
4. 対象行ごとにQR画像を生成し、ページ配列を構築する
5. PDFを生成後、一時画像を全件削除する
6. PDFを保存・ダウンロードする

---

## 4. 改修② — URX QRシール印刷の新規追加

### 4-1. ボタン表示仕様

既存の「QRシール印刷」ボタンを以下の2ボタン構成に変更する。

| ボタン名 | 表示条件 |
|---------|---------|
| UME QRシール印刷 | セット内にUME対象依頼が1件以上ある場合 |
| URX QRシール印刷 | セット内にURX対象依頼が1件以上ある場合 |

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

### 4-3. QRコードURL形式

| 種別 | URL |
|------|-----|
| UME | `https://web.musicvideo.usen.com/?param1={unis_customer_cd}&param2={contract_cd}` |
| URX | `https://web.musicvideo.usen.com/v2/?param1={unis_customer_cd}&param2={contract_cd}` |

`unis_customer_cd`・`contract_cd` はそれぞれの `shipping_requests` 行の値を使用する。

### 4-4. 実装箇所

#### `src/public_html/fuel/app/modules/manage/classes/presenter/center/kitting/view.php`

- 既存 `qr_flg` を `ume_flg` に改名する（判定ロジックは流用）
- `urx_flg` を新規追加する（URX判定ロジックを実装）
- 既存 `qr_id` は削除する（ボタン押下時のIDはメイン依頼IDに統一するため不要）

#### `src/public_html/fuel/app/modules/manage/views/center/kitting/view.php`

- 既存の `$qr_flg` / `$qr_id` を使った1ボタン構成を、`$ume_flg` / `$urx_flg` を使った2ボタン構成に変更する
- ボタン押下時のIDには `$data['one']['id']`（メイン依頼ID）を使用する

#### `src/public_html/fuel/app/modules/manage/classes/controller/center/kitting.php`

- `action_download_urx_qrcode_label_save($shipping_request_id)` を新規追加する
  - 処理フローはUMEと同じ（判定ロジックとQR URLのみ異なる）
  - PDFファイル名: `{shipping_request_id}_urx_qrcode.pdf`
- ヘルパーメソッドを追加する
  - `get_ume_eligible_rows($rows)`: UME対象行を返す
  - `get_urx_eligible_rows($rows)`: URX対象行を返す

#### `src/public_html/public/assets/js/script.js`

- `output_urx_qr_label(ajax_url, id)` を新規追加する
  - 処理内容は既存 `output_qr_label()` と同様
  - PDFパス: `/contents/pdf/qrcode/{id}_urx_qrcode.pdf`

---

## 5. 影響範囲

| ファイル | 種別 | 内容 |
|---------|------|------|
| `pdf/creater/qrcode/label.php` | 改修 | create() インターフェース変更 |
| `presenter/center/kitting/view.php` | 改修 | ume_flg/urx_flg への変更 |
| `views/center/kitting/view.php` | 改修 | ボタン2本化 |
| `controller/center/kitting.php` | 改修・追加 | UMEアクション改修、URXアクション追加 |
| `assets/js/script.js` | 追加 | output_urx_qr_label() 追加 |

---

## 6. スコープ外

- `device_types` マスタへの `qrcode_flg = 2` データ投入は本改修のスコープ外。別途データ投入を依頼すること
- 既存UMEのQRコードURL形式は変更しない
- 既存PDFテンプレート（`qrcode.pdf`）のレイアウトは変更しない

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
| QRコードURL（UME） | `https://web.musicvideo.usen.com/?param1=...&param2=...` | — |
| QRコードURL（URX） | — | `https://web.musicvideo.usen.com/v2/?param1=...&param2=...` |
| 既存UME動作（単一依頼） | 既存と同等の動作であること | — |

---

## 8. 確認事項

- [ ] serial_cd の記載座標・フォントサイズをPDFテンプレート上で確認し確定する（現在の暫定値: X=155, Y=10, 8pt）
- [ ] `device_types.qrcode_flg = 2` のマスタデータ投入タイミングをデータ担当者と調整する
