# PR #296（顧客直送・代理店直送対応）をSIM管理機能より先にstgへ上げる手順

**関連PR:** https://github.com/u-ds/uds-web/pull/296
**背景:** `develop`にはすでにSIM管理機能（PR #252）がマージ済みだが、`staging`はSIM管理機能マージ前の状態で止まっている。スケジュールの都合上、PR #296をSIM管理機能より先にstgへ反映したい。単純に`develop`を`staging`にマージするとSIM管理機能も一緒に持ち込まれてしまうため、以下の手順で#296の差分だけを選んでstgへ反映する。

---

## 事前調査で確認済みのこと

PR #296とPR #252（SIM管理機能）は、以下5つの既存ファイルを両方とも編集している。

- `config/define.php`
- `config/upload.php`
- `modules/manage/classes/controller/master/other.php`
- `modules/manage/views/master/device/help_dialog.php`
- `modules/manage/views/master/other/index.php`

いずれも、それぞれ別々の既存の目印（既存の定数・既存メソッド・既存マスタセクション等）を基準に離れた場所へ追記しており、SIM側が新規作成したファイルに#296が追記している箇所もない。そのためcherry-pick時に大きな・解消困難なコンフリクトが起きる可能性は低いと判断している（ただし機械的なコンフリクト表示自体は出ることがあるので、手順内で確認する）。

---

## 手順

### 1. PR #296を「Squash and merge」でdevelopにマージする

1. https://github.com/u-ds/uds-web/pull/296 を開く
2. マージボタン右側の▼から **「Squash and merge」** を選択してマージを実行
3. マージ完了後に表示される **squashコミットのハッシュ** を控える
   - GitHub上に「merged commit `XXXXXXX` into `develop`」と表示される、その`XXXXXXX`部分
   - 後からでも以下で取得可能：
     ```bash
     gh pr view 296 --repo u-ds/uds-web --json mergeCommit -q '.mergeCommit.oid'
     ```

> **通常マージではなくSquashにする理由:** #296のブランチ履歴には「developを取り込み、SIM管理機能とのコンフリクトを解消」というマージコミットが含まれている。これを個別にcherry-pickしようとすると、SIM管理機能側の差分まで引き込むリスクがある。Squashで1コミットに集約すれば、そのコミットの中身は「develop（SIM込み）に対する#296の正味差分」だけになり、安全にcherry-pickできる。

### 2. stagingから新しい作業ブランチを作る

```bash
git fetch origin develop staging
git checkout -b staging-agency-direct-shipment origin/staging
```

### 3. squashコミットをcherry-pickする

```bash
git cherry-pick <手順1で控えたハッシュ>
```

### 4. コンフリクトが出た場合の解消

止まった場合は対象ファイルを確認する。

```bash
git status
```

該当ファイルを開き、`<<<<<<<` / `=======` / `>>>>>>>` の3点セットを探す。今回想定される5ファイルはいずれも「両方の追記を残せばよい」ケースのはずなので、マーカー行だけ削除し、両者の追記内容をそのまま残す形で解消する。

解消後：

```bash
git add <解消したファイル>
git cherry-pick --continue
```

万一、明らかに想定外の複雑なコンフリクト（同じ行の奪い合いなど）が出た場合は、そこで一旦立ち止まって内容を確認する。

### 5. 反映内容の確認

```bash
git diff origin/staging
```

- #296の変更（直送カテゴリマスタ・直送案件対象品目マスタ関連の追加、送り状Excel出力の代理店直送対応など）だけが含まれているか
- SIM管理機能のコード（`sim`関連のクラス・画面・設定等）が一切紛れ込んでいないか

の2点を目視で確認する。

### 6. push・PR作成

```bash
git push origin staging-agency-direct-shipment
```

GitHub上で `staging-agency-direct-shipment` → `staging` のPRを作成し、マージする。

---

## 留意事項

- **一時的な二重管理:** #296の変更は、この後「develop経由（squashコミット）」と「staging直接cherry-pick」という2つの異なるコミットとして、それぞれのブランチに別ハッシュで存在することになる。中身は同一なので通常問題ないが、PRやコミットメッセージに「#296のstg先行反映」等の注記を入れておくと後から履歴を追う人が混乱しない
- **将来のSIM機能stg昇格時:** 後日、SIM管理機能を`develop → staging`の通常マージでstgに上げる際、staging側はすでに#296の内容を（別コミットとして）持っている。ファイル内容は同一になるはずなので、Gitは通常問題なくマージできる想定だが、念のためその際もマージ後に軽く差分確認を行う
- **cherry-pick後の検証は必須:** 特に`define.php`の`csv_format_div`のような採番配列は、コンフリクト解消時に手作業でマージするため、番号の重複や記載漏れがないか改めて確認する
