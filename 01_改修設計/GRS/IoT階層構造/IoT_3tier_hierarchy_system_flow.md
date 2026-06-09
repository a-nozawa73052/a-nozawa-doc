# IoT 階層管理機能 システムフロー

作成日: 2026-04-07
対象システム: GRS（usen-grs-mini-web）/ SGS / MEMBERS

---

## 登場するコンポーネント

| 略称 | 正式名 | 役割 |
|------|--------|------|
| **Web** | GRS mini-web (Vue) | フロントエンド画面 |
| **GRS** | GRS API (AWS SAM / Lambda) | バックエンドAPI。SGS・MEMBERSへのブリッジ |
| **GRSDB** | GRS DB (MySQL) | GRS固有テーブル。`t_dx_company_cd_numbering` のみ本機能で更新 |
| **SGS** | SGS API (Hono / Prisma) | データ保存先。RDS + DynamoDB の二重管理 |
| **RDS** | SGS RDS (MySQL) | 正規化マスタデータ（companies / service_groups / service_group_customers 等） |
| **DDB** | SGS DynamoDB | 参照用の非正規化データ。RDS書き込み後に SGS 内部で同期 |
| **MEM** | MEMBERS API | UMIDアカウント管理・ウェルカムメール送信 |

> **書き込みの原則:** GRS は SGS RDB へ直接 POST する（GRS DB には保存しない）。DynamoDB の同期は SGS 内部処理が担う。

---

## SF-1: 本社 / DX企業登録（新規モード）

```mermaid
sequenceDiagram
    actor U as ユーザー
    participant Web as GRS mini-web
    participant GRS as GRS API
    participant GRSDB as GRS DB<br/>(t_dx_company_cd_numbering)
    participant SGS as SGS API
    participant RDS as SGS RDS
    participant DDB as SGS DynamoDB

    U->>Web: ダイアログ入力<br/>・管理用UNISCD<br/>・本社名<br/>・サービスCD<br/>・DX企業名<br/>・支店UNISCD / 支店サービスCD
    U->>Web: [登録実行] クリック

    Web->>GRS: GRS API へリクエスト

    rect rgb(255, 248, 225)
        Note over GRS,GRSDB: ① 本社CD生成（計算のみ・DBへの保存なし）
        GRS->>GRS: company_cd = "C" + unis_customer_cd<br/>（固定ルールで生成、t_dx_company_cd_numberingは使わない）
    end

    rect rgb(232, 245, 233)
        Note over GRS,RDS: ② 本社レコード登録（SGS RDS）
        GRS->>SGS: SGS API へリクエスト<br/>{ company_cd, company_name, unis_customer_cd, service_cd }
        SGS->>RDS: UPSERT companies<br/>（unis_customer_cd がキー）
        RDS-->>SGS: OK
        SGS->>DDB: 非同期同期
        SGS-->>GRS: { company_id }
    end

    rect rgb(255, 248, 225)
        Note over GRS,GRSDB: ③ DX企業CD発番（GRS DB を更新）
        GRS->>GRSDB: SELECT current_value FROM t_dx_company_cd_numbering
        GRSDB-->>GRS: current_value
        GRS->>GRSDB: UPDATE t_dx_company_cd_numbering<br/>SET current_value = current_value + 1
        GRS->>GRS: service_group_cd = current_value + 1
    end

    rect rgb(232, 245, 233)
        Note over GRS,RDS: ④ DX企業レコード登録（service_groups）
        GRS->>SGS: SGS API へリクエスト<br/>{ company_id, service_group_cd, service_group_name }
        SGS->>RDS: INSERT service_groups
        RDS-->>SGS: OK
        SGS->>DDB: 非同期同期
        SGS-->>GRS: { service_group_id }
    end

    rect rgb(232, 245, 233)
        Note over GRS,RDS: ⑤ 支店（設置先）レコード登録（service_group_customers）
        GRS->>SGS: SGS API へリクエスト<br/>{ service_group_id, unis_customer_cd: shiten_unis_cd,<br/>  service_cd: shiten_service_cd }
        SGS->>RDS: UPSERT service_group_customers<br/>（unis_customer_cd + service_cd がキー）
        RDS-->>SGS: OK
        SGS->>DDB: 非同期同期
        SGS-->>GRS: OK
    end

    GRS-->>Web: 完了レスポンス
    Web-->>U: スナックバー「登録を完了しました」
```

---

## SF-2: DX企業追加（addGroup モード）

```mermaid
sequenceDiagram
    actor U as ユーザー
    participant Web as GRS mini-web
    participant GRS as GRS API
    participant SGS as SGS API
    participant RDS as SGS RDS
    participant DDB as SGS DynamoDB

    U->>Web: 本社詳細で [DX企業追加] クリック
    Note right of U: 本社情報（unis_customer_cd / company_name）は<br/>画面から自動セット（読取専用）
    U->>Web: DX企業名を入力して [登録実行]

    Web->>GRS: GRS API へリクエスト

    rect rgb(255, 248, 225)
        Note over GRS,GRSDB: ① DX企業CD発番（GRS DB を更新）
        GRS->>GRSDB: SELECT current_value FROM t_dx_company_cd_numbering
        GRSDB-->>GRS: current_value
        GRS->>GRSDB: UPDATE t_dx_company_cd_numbering<br/>SET current_value = current_value + 1
        GRS->>GRS: service_group_cd = current_value + 1
    end

    rect rgb(232, 245, 233)
        Note over GRS,RDS: ② DX企業レコード登録（service_groups）
        GRS->>SGS: SGS API へリクエスト<br/>{ company_id, service_group_cd, service_group_name }
        SGS->>RDS: INSERT service_groups
        RDS-->>SGS: OK
        SGS->>DDB: 非同期同期
        SGS-->>GRS: { service_group_id }
    end

    GRS-->>Web: 完了レスポンス
    Web-->>U: スナックバー「登録を完了しました」

    Note over Web: 本社CDの発番は不要（既存本社に追加するため）
```

---

## SF-3: 店舗追加（upsert）

```mermaid
sequenceDiagram
    actor U as ユーザー
    participant Web as GRS mini-web
    participant GRS as GRS API
    participant SGS as SGS API
    participant RDS as SGS RDS
    participant DDB as SGS DynamoDB

    U->>Web: DX企業詳細で [店舗追加] クリック
    U->>Web: 設置先UNISCD / サービスCD を入力して [追加登録]

    Web->>GRS: POST /iot/service-group-customers<br/>{ service_group_id, unis_customer_cd, service_cd }

    rect rgb(232, 245, 233)
        GRS->>SGS: POST /service-group-customers<br/>{ service_group_id, unis_customer_cd, service_cd }

        alt unis_customer_cd がそのグループに未登録
            SGS->>RDS: INSERT service_group_customers<br/>（新しい店舗レコードを作成）
        else unis_customer_cd がそのグループに既存
            SGS->>RDS: UPDATE service_group_customers<br/>（既存店舗にサービスを追加、店舗レコードは新規作成しない）
        end

        RDS-->>SGS: OK
        SGS->>DDB: 非同期同期
        SGS-->>GRS: OK
    end

    GRS-->>Web: 201 Created
    Web-->>U: スナックバー「店舗を追加登録しました」

    Note over Web,RDS: ⚠ 同一 unis_customer_cd が既存の場合、店舗レコードは作成されず<br/>サービスのみ追加される（upsert）
```

---

## SF-4: UMアカウント作成・紐づけ（共通フロー）

新規作成と既存紐づけを統合した単一フロー。メールアドレスの存在有無によって MEMBERSが自動で処理を分岐する。

```mermaid
sequenceDiagram
    actor U as ユーザー
    participant Web as GRS mini-web
    participant GRS as GRS API
    participant SGS as SGS API
    participant RDS as SGS RDS
    participant DDB as SGS DynamoDB
    participant MEM as MEMBERS API

    U->>Web: [UMアカウント作成] クリック
    Note right of U: level（本社 or 支店）と service_cd は<br/>呼び出し元から自動セット
    U->>Web: 認証用メールアドレス / アカウント名 を入力
    U->>Web: [作成・紐づけ] クリック

    Web->>GRS: POST /iot/um-accounts<br/>{ email, username, unis_customer_cd,<br/>  service_cd, level }

    rect rgb(227, 242, 253)
        Note over GRS,MEM: ① MEMBERS API でアカウント確認・作成
        GRS->>MEM: POST /accounts/find-or-create<br/>{ email, username }

        alt メールアドレスが MEMBERS に未登録
            MEM->>MEM: 新規UMIDを発行
            MEM->>MEM: ウェルカムメール（ご利用案内）を送信
            MEM-->>GRS: { umid, is_new: true }
        else メールアドレスが既存アカウントに紐づき済み
            MEM-->>GRS: { umid, is_new: false }
            Note over MEM: 既存の場合はメール送信なし
        end
    end

    rect rgb(232, 245, 233)
        Note over GRS,RDS: ② SGS に UMID と権限を登録
        GRS->>SGS: POST /service-group-customers/umid<br/>{ unis_customer_cd, service_cd, umid,<br/>  grant_cd: level=honsha ? 20 : 30 }
        SGS->>RDS: UPSERT service_group_customers<br/>（umid / grant_cd を設定）
        RDS-->>SGS: OK
        SGS->>DDB: 非同期同期
        SGS-->>GRS: OK
    end

    GRS-->>Web: 201 Created<br/>{ umid, is_registered: false }
    Web-->>U: スナックバー「UMアカウントを作成・紐づけしました」

    Note over Web: アカウント一覧に「仮登録」バッジで表示される<br/>（is_registered = false）
```

**権限CDの自動設定:**

| level | 権限CD | 権限名 |
|-------|--------|--------|
| honsha（本社） | 20 | 本社管理 |
| store（支店） | 30 | 支店管理 |

> シェア権限（21: 本社シェア / 31: 支店シェア）は廃止のため選択肢なし。

---

## SF-5: 仮登録 → 本登録の状態遷移

UMアカウント作成直後は `is_registered = false`（仮登録）。ユーザーがウェルカムメールのリンクから初回ログインすると、MEMBERS 側が `is_registered = true` に更新する。

```mermaid
stateDiagram-v2
    [*] --> 仮登録: UMアカウント作成・紐づけ直後<br/>（is_registered = false）
    仮登録 --> 本登録: ユーザーがウェルカムメールの<br/>リンクから初回ログイン<br/>（MEMBERS が is_registered = true に更新）
    本登録 --> [*]

    note right of 仮登録
        GRS画面: オレンジバッジ「仮登録」
    end note
    note right of 本登録
        GRS画面: 緑バッジ「本登録」
    end note
```

---

## SF-6: 検索フロー

```mermaid
sequenceDiagram
    actor U as ユーザー
    participant Web as GRS mini-web
    participant GRS as GRS API
    participant SGS as SGS API
    participant DDB as SGS DynamoDB

    U->>Web: 検索タブを選択 / キーワード入力 / [検索] クリック

    Web->>GRS: GET /iot/companies?mode={searchMode}&q={query}

    rect rgb(227, 242, 253)
        GRS->>SGS: GET /companies?{searchMode}={query}
        SGS->>DDB: Query（DynamoDB の GSI を使用）
        Note right of DDB: 本社CD / DX企業CD / 設置先CD<br/>→ GSI で完全一致<br/>本社名 / DX企業名 / 設置名<br/>→ LIKE 相当（フィルタ）
        DDB-->>SGS: マッチした本社一覧（+ 配下DX企業・店舗を含むフルツリー）
        SGS-->>GRS: companies[]（各社フルツリー）
    end

    GRS-->>Web: 200 OK<br/>companies[]

    alt ヒット件数 = 0
        Web-->>U: スナックバー「該当データなし」
    else ヒット件数 = 1
        Web->>Web: setTree(company, searchMode, query)<br/>検索キーに一致したノードを自動ハイライト
        Web-->>U: フルツリー表示 + 該当ノード選択状態
    else ヒット件数 > 1
        Web-->>U: 候補一覧を表示
        U->>Web: 候補から1社を選択
        Web->>Web: setTree(company, searchMode, query)
        Web-->>U: フルツリー表示 + 該当ノード選択状態
    end
```

**ハイライト対象ノードの決定ロジック:**

| 検索タブ | ハイライト対象 | 展開動作 |
|---------|--------------|---------|
| 本社CD / 本社名 | 本社ノード | そのまま表示 |
| DX企業CD / DX企業名 | 一致した DX企業ノード | 親本社を自動展開 |
| 設置先CD / 設置名 | 一致した 店舗×サービス行 | 親本社・DX企業を自動展開 |

---

## SF-7: 本社登録時の neos_contracts 確認（フロントエンド）

本社情報のサービスCD入力に反応して、リアルタイムで既存UMIDを確認する。

```mermaid
sequenceDiagram
    actor U as ユーザー
    participant Web as GRS mini-web
    participant GRS as GRS API
    participant SGS as SGS API
    participant RDS as SGS RDS

    U->>Web: 管理用UNISCD を入力
    U->>Web: サービスCD を入力（リアルタイム）

    rect rgb(255, 248, 225)
        Note over Web,RDS: フロントエンドの computed が反応（入力値が両方揃った瞬間）
        Web->>GRS: GET /iot/neos-contracts?unis_customer_cd={cd}&service_cd={svc}
        GRS->>SGS: GET /neos-contracts?unis_customer_cd={cd}&service_cd={svc}
        SGS->>RDS: SELECT * FROM neos_contracts<br/>WHERE unis_customer_cd = ? AND service_cd = ?
        RDS-->>SGS: レコード（0件 or 1件）
        SGS-->>GRS: { umid, account_name } or null
        GRS-->>Web: { umid, account_name } or null
    end

    alt neos_contracts にUMIDが存在する
        Web-->>U: ⓘ アラート表示<br/>「neos_contracts に既存UMIDが見つかりました」<br/>UMID: {umid}<br/>（登録後、このサービスのUMIDは自動表示される）
    else 存在しない
        Web-->>U: アラートなし（通常入力状態）
    end

    Note over Web: モック実装では NEOS_CONTRACTS 定数で代替
```

---

## SF-8: データ整合性の保証（SGS DynamoDB 同期）

```mermaid
sequenceDiagram
    participant GRS as GRS API
    participant SGS as SGS API
    participant RDS as SGS RDS
    participant DDB as SGS DynamoDB

    GRS->>SGS: POST / UPSERT リクエスト
    SGS->>RDS: トランザクション書き込み
    RDS-->>SGS: コミット完了

    Note over SGS,DDB: SGS 内部で RDS → DynamoDB 同期
    SGS->>DDB: UPSERT（非正規化データ）
    DDB-->>SGS: OK

    SGS-->>GRS: レスポンス返却

    Note over RDS,DDB: RDS が正: 書き込み / 正規化データ<br/>DDB が正: 読み取り / 非正規化データ（高速参照用）
```

---

## まとめ: 各フローが更新するテーブル

| 操作 | GRS DB | SGS RDS | SGS DynamoDB | MEMBERS |
|------|--------|---------|--------------|---------|
| 本社/DX企業登録（新規） | `t_dx_company_cd_numbering`（DX企業CD発番） | `companies` `service_groups` `service_group_customers` | ◎（SGS内部で同期） | - |
| DX企業追加 | `t_dx_company_cd_numbering`（DX企業CD発番） | `service_groups` | ◎ | - |
| 店舗追加 | - | `service_group_customers` | ◎ | - |
| UMアカウント作成（新規） | - | `service_group_customers`（umid/grant_cd） | ◎ | アカウント作成・メール送信 |
| UMアカウント紐づけ（既存） | - | `service_group_customers`（umid/grant_cd） | ◎ | - |
| 仮→本登録遷移 | - | `service_group_customers`（is_registered） | ◎ | is_registered 更新 |
| 検索 | - | - | 参照のみ | - |
