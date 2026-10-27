# UDS WAF 導入手順（uds-web / udsapi）

- 作成日: 2026-10-27
- 背景: PHP の脆弱性（CVE-2026-109618 / 109619、php2shell）を受けて、UDS への WAF 導入の依頼があった
- 対象アカウント: 518125615804（ap-northeast-1）

---

## 0. 現状の構成（2026-10-27 確認）

### uds-web（PHP 5.6 / FuelPHP）

```
[利用者] ─HTTPS:443─▶ NLB: uds-nlb-production（internet-facing、TLS 終端）
                              │ HTTP:80
                              ▼
                     EC2: uds_production（i-012aeee2a89918d39 / 10.203.37.24）
```

| 項目 | 内容 |
|---|---|
| 前段 | **NLB**（`uds-nlb-production`、stg は `uds-nlb-staging`）。**NLB には WAF を付けられない** |
| TLS 終端 | NLB のリスナー（443 / TLS） |
| ターゲットグループ | `uds-routeing-production`（instance / port 80） |
| 接続元の制限 | EC2 のセキュリティグループで実施。NLB 自体にはセキュリティグループなし |
| 80 番の許可 | `10.203.37.0/24`（VPC 内）、`125.63.42.192/26`（社内）、`52.192.182.98/32`（beyond Zabbix） |
| 既存の WAF | なし（`wafv2 list-web-acls --scope REGIONAL` の結果が空） |

### udsapi（API Gateway → Lambda / Node.js）

| 項目 | 内容 |
|---|---|
| API | `prd-udsapi`（1fumack509）、`stg-udsapi`（pp4idv2pn0）、`dev-udsapi`（i2xref1url） |
| エンドポイントの種類 | **REGIONAL**（WAF を付けられる） |
| 接続元の制限 | リソースポリシーで、許可リストの約 40 IP 以外を Deny |
| 既存の WAF | なし |

### 前提として押さえておくこと

- uds-web も udsapi も、**インターネットからの接続はすでに IP で制限済み**。WAF で増える効果は「許可された接続元からのリクエストの中身を検査すること」が中心になる。
- **PHP の脆弱性に関係するのは uds-web だけ**。udsapi の後ろは Lambda（Node.js）なので、udsapi に WAF を付けても PHP の脆弱性への対策にはならない。
- PHP の脆弱性への応急対応は、`session.upload_progress.enabled = Off` で別に実施する。

---

## 1. uds-web に WAF を付ける場合

NLB には WAF を付けられないため、**ALB を新しく作る**必要がある。方式は 2 つ。

### 方式の比較

| | 案A: NLB の後ろに ALB を足す | 案B: NLB を ALB に置き換える |
|---|---|---|
| 構成 | NLB(TCP) → **ALB + WAF**(TLS 終端) → EC2 | **ALB + WAF**(TLS 終端) → EC2 |
| 利用者側の URL・DNS | 変わらない | **DNS の切り替えが必要** |
| NLB の固定 IP（EIP） | そのまま使える | 使えなくなる（ALB は IP が変わる） |
| 費用 | NLB + ALB + WAF | ALB + WAF（NLB の分が減る） |
| 作業量・リスク | 中（NLB のリスナー変更で一瞬切断） | 中〜大（DNS の切り替え） |
| 向いているケース | 連携先が NLB の固定 IP や DNS 名を直接使っている | DNS（Route 53 など）を自分たちで切り替えられる |

**判断材料**: NLB に Elastic IP が付いていて、その IP を連携先に通知している場合は案A。そうでなければ、構成がシンプルな案B。

```bash
# NLB に Elastic IP が付いているか（AllocationId が出れば EIP あり）
AWS_PAGER="" aws elbv2 describe-load-balancers --names uds-nlb-production \
  --query "LoadBalancers[0].AvailabilityZones[].LoadBalancerAddresses[].[IpAddress,AllocationId]" --output table

# uds-web の URL がどこを向いているか（Route 53 で管理している場合）
AWS_PAGER="" aws route53 list-hosted-zones --query "HostedZones[].[Name,Id]" --output table
```

### 共通の事前準備

1. **証明書を確認する**
   - NLB の TLS リスナーで使っている証明書（ACM）を確認する。ALB でも同じ証明書を使う。
   ```bash
   AWS_PAGER="" aws elbv2 describe-listeners --load-balancer-arn <NLB の ARN> \
     --query "Listeners[].Certificates[].CertificateArn" --output text
   ```
2. **stg で先に試す**
   - `uds-nlb-staging` 側で同じ手順を実施し、画面操作・CSV アップロード・PDF 出力などの主要機能を確認してから本番に入る。
3. **作業時間帯を決める**
   - 切り替えの瞬間に接続が切れるため、業務時間外に実施する。

### 1-1. ALB 用のセキュリティグループを作る

| 方向 | ポート | 接続元 / 宛先 | 説明 |
|---|---|---|---|
| inbound | 443 | 案A: NLB のサブネット（`10.203.37.0/24` など）<br>案B: 社内 `125.63.42.192/26`、beyond `52.192.182.98/32` など | 今の EC2 の許可内容に合わせる |
| outbound | 80 | EC2 のセキュリティグループ（`sg-06d7bf4eb379d481c`） | EC2 への転送 |

### 1-2. ALB を作る

- 種類: Application Load Balancer
- スキーム: 案A は **internal**、案B は **internet-facing**
- サブネット: EC2 と同じ VPC。2 つ以上の AZ を指定する
- リスナー: **HTTPS:443**、証明書は事前準備で確認した ACM 証明書
- ターゲットグループ: instance / **HTTP:80** / `i-012aeee2a89918d39`
- ヘルスチェック: 今の NLB のターゲットグループと同じパスにする

### 1-3. EC2 のセキュリティグループに ALB からの許可を追加する

- `sg-06d7bf4eb379d481c` の inbound に「80 番 / 接続元: ALB のセキュリティグループ」を追加する
- **今のルールはまだ消さない**（切り戻しのため）

### 1-4. WAF（Web ACL）を作って ALB に付ける

1. AWS WAF →「Web ACLs」→「Create web ACL」
   - Resource type: **Regional resources**
   - Region: **Asia Pacific (Tokyo)**
   - Associated resources: 1-2 で作った ALB
2. ルールを追加する（**最初はすべて Count**。ブロックせず記録だけにする）

   | ルール | 目的 |
   |---|---|
   | `AWSManagedRulesCommonRuleSet` | 一般的な攻撃（XSS、パスの悪用など） |
   | `AWSManagedRulesKnownBadInputsRuleSet` | 既知の悪い入力（Log4j など） |
   | `AWSManagedRulesPHPRuleSet` | PHP アプリ向けの攻撃 |
   | `AWSManagedRulesSQLiRuleSet` | SQL インジェクション |
   | （任意）カスタムルール | ボディに `PHP_SESSION_UPLOAD_PROGRESS` を含むリクエストを止める（今回の PHP の脆弱性への仮想パッチ） |

   - カスタムルールの注意: ALB の WAF が検査できるボディは**先頭 8KB まで**。それより後ろにある場合は検査できないため、`session.upload_progress = Off` の緩和策と組み合わせる前提にする。
3. Default action: **Allow**
4. ログを有効にする
   - 送り先: CloudWatch Logs（ロググループ名は `aws-waf-logs-` で始める必要がある。例: `aws-waf-logs-uds-web-prd`）

### 1-5. 切り替える

**案A（NLB → ALB）**

1. NLB に、ターゲットタイプ **alb** のターゲットグループ（TCP:443）を作り、1-2 の ALB を登録する
2. NLB のリスナーを **TLS:443 → TCP:443** に変更し、転送先を新しいターゲットグループにする
   - NLB → ALB の転送は TCP リスナーが前提。TLS 終端は ALB 側に移る
   - **この操作の瞬間に既存の接続が切れる**
3. 社内から画面にアクセスして動作確認する

**案B（ALB に置き換え）**

1. ALB の DNS 名で動作確認する（hosts ファイルで一時的に向ける、など）
2. DNS（Route 53 など）の uds-web のレコードを、NLB から ALB に切り替える
   - 事前に TTL を短くしておく（例: 60 秒）
3. 社内から画面にアクセスして動作確認する
4. 数日様子を見て問題なければ、NLB を削除する

### 1-6. 接続元の IP 制限を確認する

- 案Aの場合、EC2 から見た接続元が ALB の IP になるため、**EC2 のセキュリティグループでの社内 IP 制限が効かなくなる**可能性がある
- 次のどちらかで、社内 IP 以外からアクセスできないことを必ず確認する
  - ALB のセキュリティグループで社内 IP に絞る（案B）
  - WAF の **IP セット**ルールで、社内 IP・beyond 以外をブロックする（案A・案B 共通）
- 社外の回線（スマホのテザリングなど）からアクセスして、**つながらないこと**を確認する

### 1-7. Count から Block に切り替える

1. 1〜2 週間、WAF のログと「Sampled requests」を確認する
2. 正常な操作が検知されていたら（誤検知）、そのルールだけ除外または Count のままにする
   - よくある例: CSV アップロードで `SizeRestrictions_BODY` に引っかかる
3. 誤検知がないことを確認してから、各ルールを **Block** に切り替える

### 1-8. 切り戻し手順

| 状況 | 切り戻し |
|---|---|
| WAF が正常なリクエストを止めた | 該当ルールを Count に戻す。急ぐ場合は Web ACL と ALB の関連付けを外す |
| 案A で ALB 経由がうまく動かない | NLB のリスナーを TLS:443 → 元のターゲットグループ（`uds-routeing-production`）に戻す |
| 案B で ALB 経由がうまく動かない | DNS を NLB に戻す（NLB は削除せずに残しておく） |

### 1-9. 費用の目安（月額）

| 項目 | 目安 |
|---|---|
| ALB | 約 $20 + 処理量（LCU）に応じた料金 |
| WAF | Web ACL $5 + ルール 1 つあたり $1 + 100 万リクエストあたり $0.60 |
| WAF ログ（CloudWatch Logs） | 取り込み・保存量に応じた料金 |

※ 正確な金額は AWS の料金ページで確認する。

---

## 2. udsapi に WAF を付ける場合

API Gateway（REGIONAL）には、Web ACL を作って関連付けるだけで WAF を付けられる。構成の変更はない。

### 2-1. 事前準備

- **stg-udsapi で先に試す**。WAF は stg・prd でそれぞれ作る（または同じ Web ACL を両方に付ける）
- 連携先（NeOS、UNIS、GRS など）の主な呼び出しパターンと、リクエストの大きさを把握しておく

### 2-2. Web ACL を作る

1. AWS WAF →「Web ACLs」→「Create web ACL」
   - Resource type: **Regional resources**
   - Region: **Asia Pacific (Tokyo)**
   - Name: 例 `udsapi-stg` / `udsapi-prd`
   - Associated resources: 「Add AWS resources」→ **Amazon API Gateway** → `stg-udsapi` のステージ
2. ルールを追加する（**最初はすべて Count**）

   | ルール | 目的 |
   |---|---|
   | `AWSManagedRulesCommonRuleSet` | 一般的な攻撃 |
   | `AWSManagedRulesKnownBadInputsRuleSet` | 既知の悪い入力 |
   | `AWSManagedRulesSQLiRuleSet` | SQL インジェクション（Lambda から MySQL に接続しているため） |
   | （任意）IP セットルール | リソースポリシーの IP 制限を WAF に移す場合 |

3. Default action: **Allow**
4. ログを有効にする（例: `aws-waf-logs-udsapi-prd`）

### 2-3. API Gateway のステージに関連付ける

- 2-2 の作成画面で関連付けていれば不要
- 後から関連付ける場合: API Gateway → `stg-udsapi` →「ステージ」→ 対象のステージ →「ファイアウォールと証明書の設定」→ ウェブアプリケーションファイアウォールで作成した Web ACL を選ぶ

### 2-4. 動作確認と本番への展開

1. stg で、連携の主なパターン（NeOS → UDS、UNIS → UDS、GRS → UDS など）が正常に動くことを確認する
2. 1〜2 週間、ログと Sampled requests で誤検知を確認する
3. 問題がなければ、prd 用の Web ACL を作り（または同じ Web ACL に追加し）、`prd-udsapi` に関連付ける（Count のまま）
4. prd でも 1〜2 週間様子を見てから、各ルールを **Block** に切り替える

### 2-5. 注意点

- **連携が止まると影響が大きい**: udsapi は契約データ連携の窓口なので、いきなり Block にしない
- **ボディの大きさ**: API Gateway の WAF は、検査するボディの上限を設定できる（既定は 16KB、最大 64KB）。それを超えるリクエストの扱い（検査せず通すか、止めるか）を決めておく
- **IP 制限の二重管理**: 今のリソースポリシーの IP 制限はそのまま残す。WAF に IP セットを作る場合は、どちらで管理するかを決めて、二重管理にならないようにする

### 2-6. 切り戻し手順

- 該当ルールを Count に戻す
- 急ぐ場合は、API Gateway のステージ設定で WAF を「なし」に戻す（関連付けの解除）。すぐに反映され、API 自体は止まらない

### 2-7. 費用の目安（月額）

- Web ACL $5 + ルール 1 つあたり $1 + 100 万リクエストあたり $0.60 + ログの料金
- udsapi のリクエスト数は、API Gateway の CloudWatch メトリクス（`Count`）で確認する

---

## 3. 導入と並行して見直したいこと

| 項目 | 内容 |
|---|---|
| udsapi の許可 IP の棚卸し | 約 40 個の IP のうち、`126.x`（個人向け回線と思われる）3 件、`222.99.48.50`、`222.110.182.226` の持ち主を確認する。`10.x` のプライベート IP は REGIONAL API では意味がないので整理する |
| uds-web の SSH 許可 | `221.188.17.171/32`（mts-inoue）が今も必要か確認する |
| PHP 5.6 の移行 | WAF は入口の対策にすぎない。根本対応は Laravel への移行で進める |

## 4. 依頼者に確認したいこと

- WAF 導入の目的（PHP の脆弱性の応急対応か、常設の対策か）
- 対象（uds-web だけか、udsapi も含むか）
- 社外からアクセスできない前提でも導入が必要か（会社の方針か）
- 費用の負担先
