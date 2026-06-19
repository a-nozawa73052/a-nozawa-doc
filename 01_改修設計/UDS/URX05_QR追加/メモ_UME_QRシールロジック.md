# UME QRシール ロジックメモ

## ボタン表示判定

```
shipping_requests（セット全行）
  → 各行の option2_neos_item_cd を取得
      ※ contract_mdm2_devices を contract_cd で LEFT JOIN して取得
  → 空値を除去し、1件でも残れば device_types テーブルへ問い合わせ
  → device_types.neos_item_cd IN (option2_neos_item_cd)
     AND device_types.qrcode_flg = '1'
  → 該当すればボタン表示
```

実装: `src/public_html/fuel/app/modules/manage/classes/presenter/center/kitting/view.php` の `ume_flg()`

---

## QRコード生成

```
対象行ごとに以下のURLでQRコード画像を生成:
  https://web.musicvideo.usen.com/?param1={unis_customer_cd}&param2={contract_cd}

ライブラリ: phpqrcode / QRcode::png()
一時画像パス: QRCODE_KEEP_PATH ({id}_{row_id}.png)
```

---

## PDF生成

```
対象行（qrcode_flg=1）をid昇順でソート
  → 1行につき1ページ（8行×5列 = 40個のQR画像を並べるシール面）
  → 各ページ右下に serial_cd を記載
テンプレート: assets/pdf/qrcode.pdf
出力先: QRCODE_LABEL_PATH ({shipping_request_id}_qrcode.pdf)
```

実装: `src/public_html/fuel/app/classes/pdf/creater/qrcode/label.php`、`src/public_html/fuel/app/modules/manage/classes/controller/center/kitting.php` の `action_download_qrcode_label_save()`

---

## データの流れ（テーブル関係）

```
shipping_requests.contract_cd
  └─ contract_mdm2_devices.contract_cd (LEFT JOIN)
       └─ contract_mdm2_devices.option2_neos_item_cd
            └─ device_types.neos_item_cd
                 └─ device_types.qrcode_flg = 1 → UME対象
```
