# UDS 画面テスト仕様書 HTML 生成
# 使い方: python gen_screen_test.py <jsonフォルダ> <参照スタイルcss> <出力html>
import html
import json
import re
import sys
from pathlib import Path

json_dir, style_path, out_path = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
# 画面ID → [画面名, URL]（画面定義書の画面一覧から作成）
URL_MAP = json.loads(Path(sys.argv[4]).read_text(encoding="utf-8")) if len(sys.argv) > 4 else {}

# 章の並び（common-items は参照フォーマットに合わせて最後）
GROUP_ORDER = ["common", "center-kitting", "center-device", "center-sim", "branch",
               "local-diff", "mirroring", "jimu", "master"]
LAST_GROUP = "common-items"

ROLES = [
    ("ROLE-ADM", "admin（user_div=1）", "ログイン後 /manage/master/device。全メニュー＋CP検証機管理・マスター管理"),
    ("ROLE-CEN", "center（user_div=2）。所属センター＝センター南港", "ログイン後 /manage/center/request?cecd[]=所属センター"),
    ("ROLE-BRA", "branch（user_div=3）。管轄＝支店A", "現地。ログイン後 /manage/branch/request"),
    ("ROLE-EXT", "external（user_div=4）。管轄＝支店A", "外部委託。ログイン後 /manage/external/request"),
    ("ROLE-CP", "cp（user_div=5）。管轄＝支店A", "CP。ログイン後 /manage/cp/mirroring/device"),
    ("ROLE-JIM", "jimu（user_div=6）", "事務・受付C。ログイン後 /manage/jimu/shipment/list"),
    ("ROLE-HSU", "hoshu_itaku（user_div=7）。管轄＝支店A", "保守委託。ログイン後 /manage/hoshu/device/list"),
    ("ROLE-GUEST", "未ログイン（Cookie なし）", "ログイン画面へのリダイレクト確認"),
    ("ROLE-OTHER", "同じロールの別ユーザー", "他ユーザー作業中（ロック10分）の確認"),
]

KNOWN = [
    ("Z-1", "CP検証機管理の4画面がログインチェック・権限チェックなしで開ける", "MIR-01〜04"),
    ("Z-2", "パスワードが平文で保存・照合され、ユーザーマスタCSVにも平文で出る", "COM-01, MST"),
    ("Z-3", "出力履歴の再ダウンロードがユーザーで絞り込まれていない", "JIM-09"),
    ("Z-4", "SIM情報変更系の処理に区分チェックがなく、center でも POST で実行できる", "SIM"),
    ("Z-5", "現地系の一部画面で自管轄の絞り込みがない", "BRA/CPK/HSU"),
    ("Z-6", "NP審査CSVの出力で、選択していない行も「NP審査完了」になる", "JIM-04"),
    ("Z-7", "引き当て確定の UME(TV) 向け SQS 送信が redirect の後ろにあり実行されない", "CEN-08"),
    ("Z-8", "キッティング完了時に device_check_id が空で登録される可能性", "CEN-20"),
    ("Z-9", "新規端末CSVの4列目が本番 csv_formats とコードで食い違う", "DEV-02"),
    ("Z-10", "SIM管理用の csv_formats（51/52/55）が本番にあるか未確認", "SIM"),
    ("Z-11", "404・不正データ画面が実際には403になる可能性", "COM-05, 06"),
    ("Z-12", "紛失報告の「差し戻しする」ボタンが押せない可能性", "DEV-14"),
    ("Z-13", "工事予定日を表示しているが、どのクエリも取得していない", "CPK/EXT/XX-06"),
    ("Z-14", "使われていない、または到達できない画面・権限キーがある", "—"),
    ("Z-15", "直送・CP検証機などのCSV列構成が csv_formats 次第で本番未確認", "JIM, MST"),
]

KIND_CLASS = {"正常": "", "バリデーション": "validation", "異常": "error"}


def esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def fmt(s):
    t = esc(s)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    return t.replace("\n", "<br>")


def load():
    groups, prep, questions = {}, [], []
    for p in sorted(json_dir.glob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8-sig"))
        for g in d["groups"]:
            groups[g["id"]] = g
        for x in d.get("prepData", []):
            prep.append((p.stem, x))
        for q in d.get("openQuestions", []):
            questions.append((d.get("source", p.name), q))
    return groups, prep, questions


def check(groups):
    errors, seen = [], set()
    for g in groups.values():
        for c in g["concepts"]:
            if c["id"] in seen:
                errors.append(f"観点IDの重複: {c['id']}")
            seen.add(c["id"])
            nc, ne = len(c["conditionColumns"]), len(c["expectColumns"])
            for i, k in enumerate(c["cases"], 1):
                if k["kind"] not in KIND_CLASS:
                    errors.append(f"{c['id']}#{i} 区分不正: {k['kind']}")
                if len(k["conditions"]) != nc or len(k["expected"]) != ne:
                    errors.append(f"{c['id']}#{i} 列数不一致")
    return errors


def screen_urls(c):
    """観点の対象画面を「ID 画面名 URL」の行にする。同じURLは1回だけ出す"""
    lines, seen = [], set()
    for s in c.get("screens", []):
        name, url = URL_MAP.get(s, ["", "（URL未定義）"])
        url = re.sub(r"`([^`]*)`", r"\1", url).replace("\\|", "|")
        if url in seen:
            lines.append(f'<span class="sc-id">{esc(s)}</span> {esc(name)}（同上）')
            continue
        seen.add(url)
        lines.append(f'<span class="sc-id">{esc(s)}</span> {esc(name)} <code>{link_paths(url)}</code>')
    return lines


PATH_RE = re.compile(r"/manage/(?:[A-Za-z0-9_/.\-\[\]?=&]|\{[^}\s]*\})*")
ENVS = [("dev", "18.181.121.4", "http://18.181.121.4"),
        ("stg", "STG", "https://web-stg.uds.usen.co.jp"),
        ("prd", "PRD", "https://web.uds.usen.co.jp")]


def link_paths(text):
    """URL文字列中の /manage/... をリンクにする。接続先は画面上部の環境選択で JS が差し替える"""
    out, pos = [], 0
    for mt in PATH_RE.finditer(text):
        out.append(esc(text[pos:mt.start()]))
        path = mt.group(0)
        out.append(f'<a class="env-link" href="{esc(ENVS[0][2] + path)}" data-path="{esc(path)}" target="_blank" rel="noopener">{esc(path)}</a>')
        pos = mt.end()
    out.append(esc(text[pos:]))
    return "".join(out)


def case_row(c, k, i, gid):
    cid = f"{c['id']}-{i:02d}"
    cls = KIND_CLASS.get(k["kind"], "")
    known = ""
    if k.get("known"):
        known = f'<span class="known">既知の問題 {esc(k["known"])}</span>'
    role = f'<span class="role-tag">{esc(k["role"])}</span>' if k.get("role") else ""
    detail = [f"<p><strong>準備：</strong>{fmt(k.get('prep') or '前提どおり')}</p>",
              f"<p><strong>操作：</strong>{fmt(k.get('op') or '条件どおりに操作する。')}</p>"]
    if k.get("detail"):
        detail.append(f"<p><strong>詳細な期待結果：</strong>{fmt(k['detail'])}</p>")
    if k.get("should"):
        detail.append(f"<p class=\"should\"><strong>本来あるべき動き：</strong>{fmt(k['should'])}</p>")
    cells = [f'<td data-label="{esc(h)}">{fmt(v)}</td>' for h, v in zip(c["conditionColumns"], k["conditions"])]
    for j, (h, v) in enumerate(zip(c["expectColumns"], k["expected"])):
        cells.append(f'<td class="expected{" expect-start" if j == 0 else ""}" data-label="{esc(h)}">{fmt(v)}</td>')
    return (
        f'<tr id="{cid}" data-test-id="{cid}" data-group="{gid}" data-kind="{esc(k["kind"])}"{" data-known=\"1\"" if k.get("known") else ""}>'
        f'<th scope="row" class="case-number">{i:02d}</th>'
        f'<td data-label="区分"><span class="kind {cls}">{esc(k["kind"])}</span></td>'
        f'<td class="case-title" data-label="ケース名"><strong class="case-name">{fmt(k["name"])}</strong>{role}{known}'
        f'<small class="case-id">{cid.upper()}</small>'
        f'<details class="case-detail"><summary>準備・操作の詳細</summary>{"".join(detail)}</details></td>'
        + "".join(cells) +
        f'<td class="result-cell" data-label="実施結果"><select class="test-result" aria-label="{cid}の結果">'
        '<option value="">未実施</option><option value="OK">OK</option><option value="NG">NG</option><option value="HOLD">保留</option></select>'
        f'<details class="case-note"><summary>実績・メモ</summary><textarea class="test-note" rows="3" aria-label="{cid}の実績・メモ" placeholder="実際の結果・証跡・不具合ID"></textarea></details></td></tr>'
    )


def concept_html(c, gid):
    heads = "".join(f'<th scope="col">{esc(h)}</th>' for h in c["conditionColumns"])
    heads += "".join(f'<th scope="col" class="expect-heading">{esc(h)}</th>' for h in c["expectColumns"])
    rows = "".join(case_row(c, k, i, gid) for i, k in enumerate(c["cases"], 1))
    defs = ""
    if c.get("conditionDefs"):
        drows = "".join(f'<tr><th scope="row">{fmt(d["item"])}</th><td>{fmt(d["values"])}</td><td>{fmt(d["meaning"])}</td></tr>'
                        for d in c["conditionDefs"])
        defs = ('<details class="concept-reference"><summary>条件の意味・設定値を詳しく見る</summary><div>'
                '<div class="table-wrap" role="region" aria-label="条件の項目一覧" tabindex="0"><table class="condition-definition">'
                '<thead><tr><th scope="col">条件項目</th><th scope="col">設定値・確認する状態</th><th scope="col">意味・確認すること</th></tr></thead>'
                f'<tbody>{drows}</tbody></table></div></div></details>')
    urls = screen_urls(c)
    return (
        f'<article class="concept" id="{c["id"]}" aria-labelledby="{c["id"]}-title">'
        f'<h3 id="{c["id"]}-title">{fmt(c["title"])}</h3>'
        + (f'<div class="screens"><strong>対象画面・URL</strong><ul>{"".join(f"<li>{u}</li>" for u in urls)}</ul></div>' if urls else "") +
        f'<p class="purpose"><strong>確認すること：</strong>{fmt(c["purpose"])}</p>'
        f'<p class="precondition"><strong>前提：</strong>{fmt(c["precondition"])}</p>'
        f'<div class="table-wrap" role="region" aria-label="{esc(c["title"])}のケース表" tabindex="0"><table class="case-table">'
        '<caption>左側に条件、緑の見出しから右側に期待結果（現行の動き）を記載しています。</caption>'
        '<thead><tr><th scope="col" class="number-col">No.</th><th scope="col" class="kind-col">区分</th>'
        f'<th scope="col" class="name-col">ケース名</th>{heads}<th scope="col" class="result-col">実施結果</th></tr></thead>'
        f'<tbody>{rows}</tbody></table></div>{defs}</article>'
    )


def section(num, g):
    body = "".join(concept_html(c, g["id"]) for c in g["concepts"])
    return (f'<section id="{g["id"]}" aria-labelledby="{g["id"]}-title"><div class="section-heading">'
            f'<span class="section-number">{num:02d} /</span><h2 id="{g["id"]}-title">{esc(g["title"])}</h2></div>'
            f'<p>{fmt(g.get("lead", ""))}</p><p class="group-progress" data-summary="{g["id"]}"></p>{body}</section>')


def main():
    groups, prep, questions = load()
    errs = check(groups)
    if errs:
        print("\n".join(errs))
        sys.exit(1)
    order = [g for g in GROUP_ORDER if g in groups] + [g for g in groups if g not in GROUP_ORDER + [LAST_GROUP]]
    has_last = LAST_GROUP in groups

    all_concepts = [c for gid in order + ([LAST_GROUP] if has_last else []) for c in groups[gid]["concepts"]]
    n_cases = sum(len(c["cases"]) for c in all_concepts)
    screens = {s for c in all_concepts for s in c.get("screens", [])}
    kinds = {k: sum(1 for c in all_concepts for x in c["cases"] if x["kind"] == k) for k in KIND_CLASS}
    n_known = sum(1 for c in all_concepts for x in c["cases"] if x.get("known"))

    # 目次・番号
    nums, toc, n = {}, [], 4
    for gid in order:
        nums[gid] = n
        n += 1
    rec_num = n
    if has_last:
        nums[LAST_GROUP] = n + 1

    def toc_item(num, anchor, title, subs):
        sub = "".join(f'<li><a href="#{c["id"]}">{esc(c["title"])}</a></li>' for c in subs)
        return (f'<li><a href="#{anchor}"><span class="toc-number">{num:02d}</span>{esc(title)}</a>'
                + (f'<ol class="toc-sub">{sub}</ol>' if sub else "") + "</li>")

    toc.append(toc_item(1, "overview", "この資料の使い方", []))
    toc.append(toc_item(2, "preparation", "準備データ", []))
    toc.append(toc_item(3, "coverage", "テスト観点・ケース一覧", []))
    for gid in order:
        toc.append(toc_item(nums[gid], gid, groups[gid]["title"], groups[gid]["concepts"]))
    toc.append(toc_item(rec_num, "record", "実施記録・出力", []))
    if has_last:
        toc.append(toc_item(nums[LAST_GROUP], LAST_GROUP, groups[LAST_GROUP]["title"], groups[LAST_GROUP]["concepts"]))

    # 同じ画面グループの行はグループ名セルを rowspan でまとめる
    cov_rows = []
    for gid in order + ([LAST_GROUP] if has_last else []):
        cs = groups[gid]["concepts"]
        for j, c in enumerate(cs):
            head = f'<th scope="rowgroup" rowspan="{len(cs)}" class="cov-group">{esc(groups[gid]["title"])}</th>' if j == 0 else ""
            cov_rows.append(f'<tr>{head}<td><a href="#{c["id"]}">{esc(c["title"])}</a></td>'
                            f'<td class="url-cell">{"<br>".join(screen_urls(c))}</td><td class="cov-count">{len(c["cases"])}件</td></tr>')
    cov = "".join(cov_rows)

    role_rows = "".join(f'<tr><th scope="row">{a}</th><td>{esc(b)}</td><td>{esc(c)}</td></tr>' for a, b, c in ROLES)
    prep_rows = "".join(f'<tr><th scope="row">{esc(x["id"])}</th><td>{fmt(x.get("content",""))}</td><td>{fmt(x.get("value",""))}</td></tr>'
                        for _, x in prep)
    known_rows = "".join(
        f'<tr><th scope="row">{a}</th><td>{esc(b)}</td><td>{esc(c)}</td><td>{sum(1 for cc in all_concepts for x in cc["cases"] if x.get("known","").startswith(a) and not x.get("known","")[len(a):len(a)+1].isdigit())}件</td></tr>'
        for a, b, c in KNOWN)
    q_html = ""
    if questions:
        q_html = ('<details class="concept-reference"><summary>ケース作成時に判断できなかった点（' + str(len(questions)) + '件）</summary><div><ul>'
                  + "".join(f"<li>{fmt(q)} <span class=\"muted\">（{esc(src)}）</span></li>" for src, q in questions) + "</ul></div></details>")

    style = style_path.read_text(encoding="utf-8")
    style = style.replace("</style>", EXTRA_CSS + "</style>").replace("</head>", "")

    sections = "".join(section(nums[gid], groups[gid]) for gid in order)
    last = section(nums[LAST_GROUP], groups[LAST_GROUP]) if has_last else ""

    page = f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="UDS（uds-web）管理画面の画面テスト仕様書。画面定義書（現行仕様）をもとに、Laravel 移行後の回帰確認に使う。">
<title>UDS 画面テスト仕様書</title>{style}</head>
<body id="top"><a class="skip-link" href="#main-content">本文へスキップ</a><div class="layout">
<aside class="sidebar" aria-label="テスト資料の目次"><div class="brand"><span class="mark" aria-hidden="true"></span>DOCUMENT NOTE</div>
<p class="sidebar-description">UDS（uds-web）<br>画面テスト仕様書</p>
<div class="side-search" role="search"><label class="toc-label" for="page-search">SEARCH / 検索</label>
<input id="page-search" type="search" placeholder="ページ内を検索" autocomplete="off">
<p class="search-status" id="search-status" aria-live="polite">Enter：次へ　Shift+Enter：前へ</p></div>
<nav aria-labelledby="toc-title"><p class="toc-label" id="toc-title">CONTENTS / 目次</p><ol class="toc">{"".join(toc)}</ol></nav>
<div class="sidebar-note">出典：doc/04_現仕様/UDS/画面定義書<br>目的 → 前提 → ケース表</div></aside>
<main id="main-content" tabindex="-1">
<header class="document-header"><p class="breadcrumb">UDS / PHP8.5移行（Laravel 移行） / 画面テスト</p>
<p class="eyebrow">UDS MANAGE / SCREEN TEST CASES</p>
<h1>UDS 画面テスト仕様書<br>ケース一覧・実施記録</h1>
<p class="lead">現行の uds-web 管理画面（manage モジュール）の動きを期待結果とし、移行後の環境で同じ表示・操作・データ更新になるかを確かめるためのテストケースです。</p>
<dl class="metadata"><div><dt>対象</dt><dd>{len(screens)}画面 / {len(all_concepts)}観点</dd></div><div><dt>ケース数</dt><dd>{n_cases}件（正常{kinds['正常']}・バリデーション{kinds['バリデーション']}・異常{kinds['異常']}）</dd></div>
<div><dt>既知の問題</dt><dd>{n_known}件</dd></div><div><dt>実施状況</dt><dd id="execution-status">全{n_cases}件未実施</dd></div><div><dt>作成日</dt><dd>2026-10-30</dd></div></dl>
<fieldset class="env-select"><legend>テストする環境（URLのリンク先が切り替わります）</legend>
{"".join(f'<label><input type="radio" name="env" value="{k}" data-base="{esc(b)}"{" checked" if i == 0 else ""}> <strong>{esc(n)}</strong> <span class="muted">{esc(b)}</span></label>' for i, (k, n, b) in enumerate(ENVS))}
<p class="env-warn" id="env-warn" hidden>本番環境（PRD）が選ばれています。データを更新する操作（登録・取込・確定など）は行わないでください。</p>
<p class="caption">{{id}} などを含むURLは、クリックすると値の入力を求めます。リンクは新しいタブで開きます。</p></fieldset></header>

<section id="overview" aria-labelledby="overview-title"><div class="section-heading"><span class="section-number">01 /</span><h2 id="overview-title">この資料の使い方</h2></div>
<p>画面グループごとに、確認する目的・共通の前提・ケース表をまとめています。条件を設定し、期待する画面表示と操作を確認してOK／NGを記録します。</p>
<div class="reader-note"><strong>読む順番：</strong>確認すること → 前提 → ケース名と条件 → 期待結果 → 実施結果。ケースごとの詳しい準備・操作は「準備・操作の詳細」、条件の設定値は表の下から開けます。</div>
<div class="matrix-legend"><span><span class="kind">正常</span> 想定する利用・状態の確認</span><span><span class="kind validation">バリデーション</span> 入力チェック・業務条件の不成立を確認</span><span><span class="kind error">異常</span> 権限拒否・ロック・不正データなどを確認</span><span><span class="known">既知の問題</span> 現行の不具合・懸念に関わるケース</span></div>
<p class="caption">期待結果は<strong>現行の動き</strong>です。バリデーションや異常でも、期待どおりに案内・操作抑止ができれば実施結果はOKです。「既知の問題」の印があるケースは、現行の動きを期待結果にし、「準備・操作の詳細」に本来あるべき動きを併記しています。移行で直すかどうかは別途判断します。</p>
<details class="concept-reference"><summary>テスト範囲・前提の考え方</summary><div>
<p>対象は uds-web の管理画面（/manage 配下）です。PHPの設定・拡張、性能、切替手順、バッチ・Lambda は対象外で、別の資料で扱います。</p>
<p>現地系の4グループ（branch / cp / hoshu / external）は、branch で全ケースを確認し、cp・保守委託・外部委託は branch との差分だけをケースにしています。</p>
<p>画面定義書で「要確認」になっている挙動は、期待結果に「（要確認）」を付けています。実施時に現行環境での結果を記録し、期待結果を確定させてください。</p>
<p>実施結果とメモはブラウザ内へ自動保存し、JSON・CSVにも書き出せます。</p></div></details>
<details class="concept-reference"><summary>既知の問題（画面定義書 索引 Z-1〜Z-15）と該当ケース数</summary><div>
<div class="table-wrap" role="region" aria-label="既知の問題" tabindex="0"><table><thead><tr><th scope="col">No</th><th scope="col">内容</th><th scope="col">該当画面</th><th scope="col">ケース</th></tr></thead><tbody>{known_rows}</tbody></table></div>
<p class="caption">索引にない各ファイル固有の要確認は「02要確認-3」のように、ファイル番号と要確認表の番号で示しています。</p></div></details>
{q_html}
</section>

<section id="preparation" aria-labelledby="preparation-title"><div class="section-heading"><span class="section-number">02 /</span><h2 id="preparation-title">準備データ</h2></div>
<p>各ケースは独立して実施し、毎回基準データへ戻してから、ケースの「準備」で指定したデータだけを用意します。</p>
<h3>ロール・アカウント</h3>
<div class="table-wrap" role="region" aria-label="ロール・アカウント" tabindex="0"><table><thead><tr><th scope="col">データID</th><th scope="col">設定</th><th scope="col">用途</th></tr></thead><tbody>{role_rows}</tbody></table></div>
<details class="concept-reference"><summary>依頼・端末・SIM・CSVファイルなどの準備データを開く（{len(prep)}件）</summary><div>
<div class="table-wrap" role="region" aria-label="準備データ" tabindex="0"><table><thead><tr><th scope="col">データID</th><th scope="col">内容</th><th scope="col">基本値・状態</th></tr></thead><tbody>{prep_rows}</tbody></table></div></div></details>
<h3>実行前の準備</h3>
<ol><li>現行環境（PHP 5.6 / FuelPHP）と移行後の環境の両方に、同じ準備データを投入できるようにします。現行環境の結果が正解です。</li>
<li>前ケースのセッション・ロック（shipping_requests.lock_user_id / lock_date）・アップロードファイルをリセットします。</li>
<li>CSV・Excel・PDF・ZIP の出力は、現行環境で出したファイルを保存して、移行後のファイルと比較します（文字コード CP932・改行・列順まで）。</li>
<li>外部連携（S3・SQS・UIDM など）はテスト用の宛先に向け、送信内容を記録できるようにします。</li>
<li>実施情報（環境・ブラウザ・実施者・実施日）を「実施記録・出力」に記録します。</li></ol>
<aside class="callout"><strong>ロックの取り決め</strong>依頼のロックは「他ユーザーが10分以内にロックしている」ときに作業中扱いになります。境界（ちょうど10分）を確認するケースは、lock_date を直接書き換えて確認してください。</aside>
</section>

<section id="coverage" aria-labelledby="coverage-title"><div class="section-heading"><span class="section-number">03 /</span><h2 id="coverage-title">テスト観点・ケース一覧</h2></div>
<div class="filter-bar" role="group" aria-label="ケースの絞り込み">
<label>区分 <select id="f-kind"><option value="">すべて</option><option>正常</option><option>バリデーション</option><option>異常</option></select></label>
<label>結果 <select id="f-result"><option value="all">すべて</option><option value="">未実施</option><option value="OK">OK</option><option value="NG">NG</option><option value="HOLD">保留</option></select></label>
<label><input type="checkbox" id="f-known"> 既知の問題だけ</label>
<span id="f-count" class="muted"></span></div>
<div class="table-wrap" role="region" aria-label="観点別ケース数" tabindex="0"><table class="coverage-table"><colgroup><col style="width:150px"><col style="width:240px"><col><col style="width:64px"></colgroup><thead><tr><th scope="col">画面グループ</th><th scope="col">確認する観点</th><th scope="col">対象画面・URL</th><th scope="col">件数</th></tr></thead><tbody>{cov}</tbody></table></div>
</section>
{sections}
<section id="record" aria-labelledby="record-title"><div class="section-heading"><span class="section-number">{rec_num:02d} /</span><h2 id="record-title">実施記録・出力</h2></div>
<div class="result-tools"><button type="button" id="export-results">結果をJSONで保存</button><button type="button" id="export-csv">結果をCSVで保存</button><span id="save-status" role="status" aria-live="polite">このブラウザ内に自動保存します。</span></div>
<p class="caption">保存先はこのブラウザ・このファイルの場所に紐付きます。別の端末へ記録を渡す場合はJSONかCSVを書き出してください。</p>
<div class="table-wrap" role="region" aria-label="実施情報" tabindex="0"><table><caption>実施情報</caption><thead><tr><th scope="col">項目</th><th scope="col">記録欄</th></tr></thead><tbody>
<tr><th scope="row">対象環境・ブランチ</th><td>［現行 / 移行後、ブランチ・コミット］</td></tr>
<tr><th scope="row">テスト環境・ブラウザ</th><td>［URL・ブラウザ・バージョン・OS］</td></tr>
<tr><th scope="row">実施者・実施日</th><td>［担当者・YYYY-MM-DD］</td></tr>
<tr><th scope="row">準備データの版</th><td>［投入したデータ・CSVファイルの識別子］</td></tr>
<tr><th scope="row">実施状況</th><td><span data-summary="all">対象{n_cases}件</span></td></tr>
<tr><th scope="row">不具合・再テスト</th><td>［不具合番号・対象テストID・再実施日・結果］</td></tr></tbody></table></div>
<p class="caption">印刷はA3横向きを想定しています。</p></section>
{last}
<footer><span>UDS 画面テスト仕様書 / 出典：doc/04_現仕様/UDS/画面定義書（2026-10-30 版）</span><a href="#top">ページの先頭へ ↑</a></footer>
</main></div>
<script>{SCRIPT}</script></body></html>"""
    out_path.write_text(page, encoding="utf-8")
    print(f"groups={len(order) + has_last} concepts={len(all_concepts)} cases={n_cases} kinds={kinds} known={n_known} screens={len(screens)} prep={len(prep)} questions={len(questions)} size={out_path.stat().st_size}")


EXTRA_CSS = """
    .known { display:inline-block; margin:6px 4px 0 0; padding:2px 6px; border-radius:4px; font-size:10px; background:#efe6f7; color:#5b3a84; }
    .role-tag { display:inline-block; margin:6px 4px 0 0; padding:2px 6px; border-radius:4px; font:10px ui-monospace,monospace; background:#eef0f3; color:#4b5563; }
    .case-detail .should { color:#5b3a84; }
    .screens { font-size:12px; color:var(--muted); margin:-6px 0 12px; }
    .screens ul { list-style:none; padding:0; margin:4px 0 0; font-size:12px; }
    .screens li + li { margin-top:2px; }
    .sc-id { font:11px ui-monospace,monospace; color:var(--brown); }
    .url-cell { font-size:11px; line-height:1.7; }
    .coverage-table { table-layout:fixed; min-width:820px; }
    .coverage-table th, .coverage-table td { padding:10px 14px; }
    .coverage-table thead th { white-space:nowrap; }
    .coverage-table .cov-group { background:#f7f8f3; border-right:1px solid var(--line); font-weight:700; font-size:12px; }
    .coverage-table .cov-count { white-space:nowrap; text-align:right; }
    .toc-number { flex-shrink:0; white-space:nowrap; }
    .layout { width:min(1760px,calc(100% - 48px)); gap:44px; }
    @media(max-width:900px) { .layout { width:calc(100% - 40px); gap:32px; } }
    @media(max-width:680px) { .layout { width:calc(100% - 32px); gap:0; } }
    .url-cell code, .screens code { font-size:11px; color:var(--ink); }
    .env-link { color:var(--green); }
    .env-select { margin:24px 0 0; padding:14px 18px; border:1px solid var(--line); border-radius:8px; background:var(--surface); display:flex; flex-wrap:wrap; gap:8px 24px; align-items:center; font-size:13px; }
    .env-select legend { padding:0 6px; font-size:12px; color:var(--brown); font-weight:700; }
    .env-select label { display:flex; gap:6px; align-items:center; cursor:pointer; }
    .env-select .caption { flex-basis:100%; margin:0; }
    .env-warn { flex-basis:100%; margin:0; padding:8px 12px; border-radius:6px; background:#fae4df; color:#8b3529; font-size:12px; font-weight:700; }
    .filter-bar { display:flex; flex-wrap:wrap; gap:10px 18px; align-items:center; margin:0 0 16px; padding:12px 16px; background:var(--surface); border:1px solid var(--line); border-radius:8px; font-size:12px; }
    .filter-bar select { font:inherit; padding:4px 6px; border:1px solid var(--line); border-radius:5px; background:white; color:var(--ink); }
    tr.is-hidden { display:none !important; }
    .result-tools button + button { background:var(--brown); }
    .side-search { position:sticky; top:0; z-index:1; margin:0 0 24px; padding:8px 0 4px; background:var(--paper); }
    .side-search .toc-label { display:block; margin-bottom:8px; }
    .side-search input { width:100%; padding:7px 10px; border:1px solid var(--line); border-radius:6px; font:inherit; font-size:13px; background:var(--surface); color:var(--ink); }
    .side-search input:focus { outline:none; border-color:var(--green); box-shadow:inset 0 0 0 1px var(--green); }
    .search-status { margin:6px 0 0; font-size:11px; color:var(--muted); }
    mark.search-hit { background:#fff3b0; color:inherit; padding:0; }
    mark.search-hit.is-current { background:#f7c948; outline:2px solid #b7791f; }
    @media(max-width:680px) { .side-search { position:static; } }
"""

SCRIPT = r"""
(() => {
  'use strict';
  const storageKey = 'uds-screen-test:v1:' + location.pathname;
  const rows = Array.from(document.querySelectorAll('[data-test-id]'));
  const validResults = new Set(['', 'OK', 'NG', 'HOLD']);
  const status = document.getElementById('save-status');
  let restored = {};
  try {
    const raw = localStorage.getItem(storageKey);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (parsed && parsed.version === 1 && parsed.tests && typeof parsed.tests === 'object') {
        restored = parsed.tests;
        status.textContent = '保存済みの結果を復元しました。';
      }
    }
  } catch (e) {
    status.textContent = '保存済みの結果を読み込めませんでした。必要に応じてJSONを書き出してください。';
  }
  rows.forEach(row => {
    const saved = restored[row.dataset.testId];
    if (!saved || typeof saved !== 'object') return;
    if (validResults.has(saved.result)) row.querySelector('.test-result').value = saved.result;
    if (typeof saved.note === 'string') row.querySelector('.test-note').value = saved.note;
  });
  function summarize(subset) {
    const counts = { '': 0, OK: 0, NG: 0, HOLD: 0 };
    subset.forEach(row => { counts[row.querySelector('.test-result').value]++; });
    return `対象${subset.length}件 / OK ${counts.OK}・NG ${counts.NG}・保留${counts.HOLD}・未実施${counts['']}`;
  }
  function refresh() {
    rows.forEach(row => { row.dataset.result = row.querySelector('.test-result').value; });
    document.querySelectorAll('[data-summary]').forEach(node => {
      const group = node.dataset.summary;
      node.textContent = summarize(group === 'all' ? rows : rows.filter(row => row.dataset.group === group));
    });
    document.getElementById('execution-status').textContent = summarize(rows);
  }
  function collect() {
    const tests = { ...restored };
    rows.forEach(row => {
      tests[row.dataset.testId] = {
        group: row.dataset.group,
        result: row.querySelector('.test-result').value,
        note: row.querySelector('.test-note').value
      };
    });
    return { version: 1, document: 'UDS 画面テスト仕様書', tests };
  }
  function save() {
    refresh();
    applyFilter();
    try {
      localStorage.setItem(storageKey, JSON.stringify(collect()));
      status.textContent = 'このブラウザ内に保存しました。';
    } catch (e) {
      status.textContent = 'ブラウザ内に保存できません。ページを閉じる前にJSONを書き出してください。';
    }
  }
  rows.forEach(row => {
    row.querySelector('.test-result').addEventListener('change', save);
    row.querySelector('.test-note').addEventListener('input', save);
  });
  function download(name, blob) {
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = name;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  document.getElementById('export-results').addEventListener('click', () => {
    const data = { ...collect(), exportedAt: new Date().toISOString() };
    download('uds_screen_test_results.json', new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }));
  });
  document.getElementById('export-csv').addEventListener('click', () => {
    const q = v => '"' + String(v).replace(/"/g, '""') + '"';
    const label = { '': '未実施', OK: 'OK', NG: 'NG', HOLD: '保留' };
    const head = ['テストID', 'グループ', '区分', 'ケース名', '既知の問題', '結果', 'メモ'];
    const body = rows.map(row => [row.dataset.testId.toUpperCase(), row.dataset.group, row.dataset.kind,
      row.querySelector('.case-name').textContent, (row.querySelector('.known') || {}).textContent || '',
      label[row.querySelector('.test-result').value], row.querySelector('.test-note').value].map(q).join(','));
    download('uds_screen_test_results.csv', new Blob(['﻿' + [head.map(q).join(','), ...body].join('\r\n')], { type: 'text/csv' }));
  });
  const fKind = document.getElementById('f-kind'), fResult = document.getElementById('f-result'), fKnown = document.getElementById('f-known');
  function applyFilter() {
    let shown = 0;
    rows.forEach(row => {
      const ok = (!fKind.value || row.dataset.kind === fKind.value) &&
        (fResult.value === 'all' || row.dataset.result === fResult.value) &&
        (!fKnown.checked || row.dataset.known === '1');
      row.classList.toggle('is-hidden', !ok);
      if (ok) shown++;
    });
    document.getElementById('f-count').textContent = (fKind.value || fResult.value !== 'all' || fKnown.checked) ? `${shown} / ${rows.length} 件を表示中` : '';
  }
  [fKind, fResult, fKnown].forEach(el => el.addEventListener('change', applyFilter));
  function revealLinkedTest() {
    const id = location.hash.slice(1);
    const target = document.getElementById(id);
    const details = target && target.closest('details');
    if (details) {
      details.open = true;
      target.scrollIntoView();
    }
  }
  // 環境選択: リンク先の接続先を差し替える
  const envKey = 'uds-screen-test:env';
  const envRadios = Array.from(document.querySelectorAll('input[name="env"]'));
  const envLinks = Array.from(document.querySelectorAll('a.env-link'));
  function currentBase() {
    const r = envRadios.find(x => x.checked) || envRadios[0];
    return r.dataset.base;
  }
  function applyEnv() {
    const base = currentBase();
    envLinks.forEach(a => { a.href = base + a.dataset.path; });
    document.getElementById('env-warn').hidden = !(envRadios.find(x => x.checked) || {}).value || envRadios.find(x => x.checked).value !== 'prd';
  }
  try {
    const savedEnv = localStorage.getItem(envKey);
    const r = envRadios.find(x => x.value === savedEnv);
    if (r) r.checked = true;
  } catch (e) {}
  envRadios.forEach(r => r.addEventListener('change', () => {
    try { localStorage.setItem(envKey, r.value); } catch (e) {}
    applyEnv();
  }));
  // {id} などの差し込み値があるリンクは、クリック時に値を入力させる
  document.addEventListener('click', e => {
    const a = e.target.closest('a.env-link');
    if (!a || !/\{[^}]+\}/.test(a.dataset.path)) return;
    e.preventDefault();
    let path = a.dataset.path;
    for (const name of (path.match(/\{[^}]+\}/g) || [])) {
      const v = window.prompt(`${name} に入れる値を入力してください`, '');
      if (v === null || v.trim() === '') return;
      path = path.replace(name, encodeURIComponent(v.trim()));
    }
    window.open(currentBase() + path, '_blank', 'noopener');
  });
  applyEnv();

  // ページ内検索（Enterで次、Shift+Enterで前のヒットへ）
  const main = document.getElementById('main-content');
  const searchBox = document.getElementById('page-search');
  const searchStatus = document.getElementById('search-status');
  const searchHint = searchStatus.textContent;
  const lower = s => s.replace(/[A-Z]/g, c => c.toLowerCase());
  let hits = [], hitIdx = -1, lastQ = '', searchStale = false;
  function clearHits() {
    const parents = new Set();
    main.querySelectorAll('mark.search-hit').forEach(m => { parents.add(m.parentNode); m.replaceWith(document.createTextNode(m.textContent)); });
    parents.forEach(p => p.normalize());
    hits = []; hitIdx = -1;
  }
  function runSearch(q) {
    clearHits();
    lastQ = q; searchStale = false;
    if (!q) { searchStatus.textContent = searchHint; return; }
    const lq = lower(q);
    const walker = document.createTreeWalker(main, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) {
      const n = walker.currentNode;
      if (lower(n.nodeValue).includes(lq) && !n.parentElement.closest('select, textarea, script, style, .is-hidden')) nodes.push(n);
    }
    nodes.forEach(n => {
      const text = n.nodeValue, lt = lower(text), frag = document.createDocumentFragment();
      let pos = 0, at;
      while ((at = lt.indexOf(lq, pos)) !== -1) {
        frag.appendChild(document.createTextNode(text.slice(pos, at)));
        const m = document.createElement('mark');
        m.className = 'search-hit';
        m.textContent = text.slice(at, at + q.length);
        frag.appendChild(m);
        hits.push(m);
        pos = at + q.length;
      }
      frag.appendChild(document.createTextNode(text.slice(pos)));
      n.replaceWith(frag);
    });
  }
  function goTo(i) {
    if (!hits.length) { searchStatus.textContent = '見つかりませんでした'; return; }
    if (hitIdx >= 0) hits[hitIdx].classList.remove('is-current');
    hitIdx = (i + hits.length) % hits.length;
    const m = hits[hitIdx];
    // 折りたたみの中にあるヒットは、その折りたたみを開いてから移動する
    for (let d = m.closest('details'); d; d = d.parentElement.closest('details')) d.open = true;
    m.classList.add('is-current');
    m.scrollIntoView({ block: 'center' });
    searchStatus.textContent = `${hitIdx + 1} / ${hits.length} 件`;
  }
  searchBox.addEventListener('keydown', e => {
    if (e.key !== 'Enter' || e.isComposing) return;
    e.preventDefault();
    const q = searchBox.value.trim();
    if (q && q === lastQ && !searchStale && hits.length && hits[0].isConnected) { goTo(hitIdx + (e.shiftKey ? -1 : 1)); return; }
    runSearch(q);
    if (q) goTo(e.shiftKey ? -1 : 0);
  });
  searchBox.addEventListener('input', () => { if (!searchBox.value.trim()) runSearch(''); });
  [fKind, fResult, fKnown].forEach(el => el.addEventListener('change', () => { searchStale = true; }));

  window.addEventListener('hashchange', revealLinkedTest);
  revealLinkedTest();
  refresh();
})();
"""

if __name__ == "__main__":
    main()
