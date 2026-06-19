# 交換時引き当てフロー比較（現地ユーザー ・ 新権限ユーザー）

---

## フロー比較

| ステップ | AsIs（現地ユーザー） | ToBe（TACTユーザー） | 差分 |
|---|---|---|---|
| 1 | 端末管理一覧で対象端末の **修理依頼ボタン** を押下 | 同左 | なし |
| 2 | `shipping_requests.request_branch_cd` = **顧客に紐づく支店**（contracts.customer_branch_cd → branch_replacementsテーブルで解決） | `shipping_requests.request_branch_cd` = **ログインユーザーの jurisdiction_branch_cd（オムロン）** | **あり** ★1 |
| 3 | 依頼リストに交換依頼（request_type_cd=5）が表示される | 同左 | なし |
| 4 | 依頼リストから対象依頼を選択 → 引き当て画面へ遷移 | 同左 | なし |
| 5 | **「シリアル登録」ボタン** 押下 → バーコードダイアログが開く（バーコードリーダーモード） | 同左 → バーコードダイアログが開く（**キーボード入力モードがデフォルト表示**） | **あり** ★2 |
| 6 | **物理端末のバーコードをスキャン** → シリアル番号が自動入力される | **オムロンから電話で受け取ったシリアル番号をキーボードで入力** → Enter押下 | **あり**（運用差分） |
| 7 | 引き当てボタン押下 → 引き当て完了 | 同左 | なし |
| 8 | キッティング画面へ遷移 | 同左 | なし |

---

## 差分詳細

### ★1：request_branch_cd の設定ロジック

**現地ユーザー含む全ロール**

```
修理依頼ボタン押下
→ contracts.customer_branch_cd を取得
→ branch_replacements WHERE unis_branch_cd = customer_branch_cd
→ shipping_requests.request_branch_cd = branch_replacements.branch_cd（顧客エリアの担当支店）
→ shipping_requests.request_branch_name = branch_replacements.branch_name
```

**新権限（TACTユーザー：user_div = 7）**

```
修理依頼ボタン押下
→ ログインユーザーの jurisdiction_branch_cd / jurisdiction_branch_name を取得
→ shipping_requests.request_branch_cd = users.jurisdiction_branch_cd（オムロン固定）
→ shipping_requests.request_branch_name = users.jurisdiction_branch_name（オムロン名）
※ center_cd の決定ロジックは変更なし（従来通り branch_replacements から取得）
```

---

### ★2：シリアル登録ダイアログ（案1）

**AsIs（全ロール共通）**

```
「シリアル登録」ボタン押下
→ バーコードダイアログが開く
→ 初期表示：バーコードリーダーモード（「ピッと音が鳴るまでかざしてください」）
→ ※バーコードアイコンを5回クリックするとキーボード入力モードに切り替わる（隠し機能）
```

**ToBe（TACTユーザー：user_div = 7）**

```
「シリアル登録」ボタン押下
→ バーコードダイアログが開く
→ 初期表示：キーボード入力モード（「シリアルコードをキーボードで入力してください」）
→ ※バーコードリーダーモードは非表示
→ シリアル番号を入力 → Enter → ダイアログが閉じ、シリアルが登録される
```

**実装内容（案1）**

`views/dialog/barcode.php` にて、ログインユーザーの `user_div` が 7 のとき表示切り替えを行う。

```php
// barcode.php の表示制御（案1）
<?php $is_tact = \Manage\Common_User::get_user_div() == 7; ?>

<div class="l-dialog-box-desc is-anim u-margin-bottom__3 js-read-barcode <?php echo $is_tact ? 'is-hide' : ''; ?>">
    {{-- バーコードリーダーモード --}}
</div>

<div class="l-dialog-box-desc is-anim u-margin-bottom__3 js-read-key <?php echo $is_tact ? '' : 'is-hide'; ?>">
    {{-- キーボード入力モード --}}
</div>
```

変更ファイル：`src/public_html/fuel/app/modules/manage/views/dialog/barcode.php` のみ（1ファイル）

---

## 背景・前提

| 項目 | 内容 |
|---|---|
| TACTの役割 | ウェルシア通信端末の修理交換一次受け（24H365D） |
| 端末の物理所在 | オムロン拠点（TACTは端末を持たない） |
| シリアル取得方法 | オムロンから電話連絡でシリアル番号を受け取る |
| バーコード利用不可の理由 | TACTがオムロン拠点にいないため物理端末をスキャンできない |
| `jurisdiction_branch_cd` | TACTユーザー全員がオムロンのコードを保持（1拠点統一） |
