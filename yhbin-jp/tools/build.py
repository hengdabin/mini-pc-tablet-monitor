#!/usr/bin/env python3
"""data/products.json から製品詳細ページとトップページの製品一覧を生成する。

使い方（yhbin-jp ディレクトリで）:  python3 tools/build.py

- products/<ASIN>.html を製品ごとに生成
- index.html の /* BUILD:PRODUCTS */ ... /* END:PRODUCTS */ を書き換え
- 販売価格 = amazon_price + markup（products.json の markup、既定 1000円）
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "data" / "products.json").read_text(encoding="utf-8"))
INDEX = ROOT / "index.html"

# 決済サービス接続前は、購入ボタンをAmazonの商品ページへ向ける。
# Stripe などの決済リンクを用意したら、products.json の各製品に "checkout_url" を追加する。
AMAZON_DP = "https://www.amazon.co.jp/dp/{asin}"

e = html.escape


def sale_price(p):
    return p["amazon_price"] + DATA.get("markup", 1000)


def yen(n):
    return f"¥{n:,}"


def shared_css():
    src = INDEX.read_text(encoding="utf-8")
    return src[src.index("<style>") + len("<style>"):src.index("</style>")]


DETAIL_CSS = """
.crumbs { font-size: 12.5px; color: var(--muted); padding-block: 20px 0; display: flex; flex-wrap: wrap; gap: 8px; }
.crumbs a { text-decoration: none; }
.crumbs a:hover { color: var(--fg); }
.pdp { display: grid; grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr); gap: clamp(28px, 4vw, 56px); padding-block: 24px clamp(56px, 7vw, 88px); align-items: start; }
@media (max-width: 900px) { .pdp { grid-template-columns: 1fr; } }
.gallery { display: grid; grid-template-columns: 72px minmax(0, 1fr); gap: 14px; position: sticky; top: calc(env(safe-area-inset-top, 0px) + 84px); }
@media (max-width: 900px) { .gallery { position: static; grid-template-columns: 1fr; } }
.gallery-main { order: 2; aspect-ratio: 1 / 1; max-width: 100%; background: #fff; border: 1px solid var(--line); border-radius: 18px; overflow: hidden; display: grid; place-items: center; }
.gallery-main img { width: 100%; height: 100%; object-fit: contain; }
.thumbs { order: 1; display: flex; flex-direction: column; gap: 10px; }
@media (max-width: 900px) { .thumbs { order: 3; flex-direction: row; overflow-x: auto; padding-bottom: 4px; } }
.thumbs button { flex: none; width: 72px; height: 72px; padding: 0; border-radius: 10px; overflow: hidden; cursor: pointer; background: #fff; border: 1px solid var(--line); }
.thumbs button[aria-current="true"] { border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent); }
.thumbs img { width: 100%; height: 100%; object-fit: contain; }
.buy { display: grid; gap: 20px; min-width: 0; }
.buy h1 { font-size: clamp(24px, 2.8vw, 32px); font-weight: 700; line-height: 1.4; }
.buy .full-title { font-size: 13px; color: var(--muted); line-height: 1.7; }
.buy .rating { font-size: 14px; }
.buy-price { display: grid; gap: 4px; padding-block: 20px; border-block: 1px solid var(--line); }
.buy-price .amount { font: 500 34px/1.1 var(--ff-mono); font-variant-numeric: tabular-nums; }
.buy-price .amount small { font: 400 13px/1 var(--ff-body); color: var(--muted); margin-left: 8px; }
.buy-specs { margin: 0; display: grid; }
.buy-specs div { display: grid; grid-template-columns: 7em minmax(0, 1fr); gap: 12px; padding: 8px 0; border-bottom: 1px dashed var(--line); font-size: 13.5px; }
.buy-specs dt { color: var(--muted); }
.buy-specs dd { margin: 0; font-family: var(--ff-mono); font-size: 13px; overflow-wrap: anywhere; }
.buy-actions { display: grid; gap: 10px; }
.buy-actions .btn { padding: 16px 22px; font-size: 15px; }
.buy-note { font-size: 12px; color: var(--muted); }
.assure { display: grid; gap: 10px; padding: 18px 20px; border: 1px solid var(--line); border-radius: 14px; background: var(--surface); font-size: 13px; }
.assure li { list-style: none; display: flex; gap: 10px; align-items: baseline; }
.assure ul { margin: 0; padding: 0; display: grid; gap: 8px; }
.assure li::before { content: ""; flex: none; width: 6px; height: 6px; border-radius: 50%; background: var(--accent); transform: translateY(-2px); }
.about { display: grid; gap: 0; max-width: 880px; margin: 0; padding: 0; }
.about li { list-style: none; padding: 18px 0; border-bottom: 1px solid var(--line); display: grid; gap: 6px; }
.about strong { font-family: var(--ff-head); font-size: 16px; }
.about span { color: var(--muted); font-size: 14px; max-width: 70ch; }
.spec-table-wrap { overflow-x: auto; max-width: 880px; }
.spec-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.spec-table th, .spec-table td { text-align: left; padding: 12px 16px; border-bottom: 1px solid var(--line); vertical-align: top; }
.spec-table th { width: 34%; font-weight: 500; color: var(--muted); background: var(--surface); }
.spec-table td { font-family: var(--ff-mono); font-size: 13px; }
.long-images { display: grid; gap: 16px; max-width: 880px; margin: 0 auto; }
.long-images img { width: 100%; height: auto; border-radius: 14px; border: 1px solid var(--line); background: #fff; }
.others { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 16px; }
.other { display: grid; gap: 10px; text-decoration: none; padding: 12px; border: 1px solid var(--line); border-radius: 14px; background: var(--surface); min-width: 0; }
.other:hover { border-color: var(--accent); }
.other img { aspect-ratio: 4 / 3; width: 100%; object-fit: contain; background: #fff; border-radius: 8px; }
.other span { font-size: 13px; line-height: 1.5; }
.other b { font: 500 14px/1 var(--ff-mono); }
"""

GALLERY_JS = """
document.querySelectorAll(".thumbs button").forEach(btn => {
  btn.addEventListener("click", () => {
    const main = document.getElementById("mainImage");
    main.src = btn.dataset.src;
    document.querySelectorAll(".thumbs button").forEach(b => b.setAttribute("aria-current", String(b === btn)));
  });
});
document.getElementById("year").textContent = new Date().getFullYear();
"""


def header(prefix):
    store = e(DATA["store_url"])
    return f"""<header class="site-header">
  <div class="wrap">
    <a class="wordmark" href="{prefix}index.html" aria-label="YHBIN ホーム">YHBIN</a>
    <nav class="nav" aria-label="メインメニュー">
      <a href="{prefix}index.html#lineup">製品ラインナップ</a>
      <a href="{prefix}index.html#engineering">設計思想</a>
      <a href="{prefix}index.html#trust">安心の理由</a>
      <a href="{prefix}index.html#faq">よくある質問</a>
      <a href="{prefix}index.html#contact">お問い合わせ</a>
    </nav>
    <a class="btn btn-primary" href="{store}" target="_blank" rel="noopener">Amazonストア</a>
  </div>
</header>"""


def footer():
    return """<footer class="site-footer">
  <div class="wrap">
    <div class="copy" style="margin-top:0;border-top:0;padding-top:0">
      <span>© <span id="year">2026</span> YHBIN. All rights reserved.</span>
      <span>Amazon、Amazon.co.jpおよびそのロゴはAmazon.com, Inc.またはその関連会社の商標です。</span>
    </div>
  </div>
</footer>"""


def bullet(text):
    m = re.match(r"^【([^】]+)】\s*(.*)$", text, re.S)
    if m:
        return f"<li><strong>{e(m.group(1))}</strong><span>{e(m.group(2))}</span></li>"
    return f"<li><span>{e(text)}</span></li>"


def detail_page(p, css):
    asin = p["asin"]
    price = sale_price(p)
    checkout = p.get("checkout_url") or AMAZON_DP.format(asin=asin)
    imgs = [f"../{i}" for i in p["images"]]
    thumbs = "".join(
        f'<button type="button" data-src="{e(src)}" aria-label="画像{n}を表示" aria-current="{str(n == 1).lower()}">'
        f'<img src="{e(src)}" alt="" loading="lazy"></button>'
        for n, src in enumerate(imgs, 1))
    specs = "".join(f"<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>" for k, v in p["specs"].items())
    rows = "".join(f"<tr><th scope=\"row\">{e(k)}</th><td>{e(v)}</td></tr>" for k, v in p["details"])
    about = "".join(bullet(b) for b in p["bullets"])
    long_imgs = "".join(f'<img src="{e(src)}" alt="{e(p["name"])} 商品画像{n}" loading="lazy">'
                        for n, src in enumerate(imgs[1:], 2))
    others = "".join(
        f'<a class="other" href="{o["asin"]}.html"><img src="../{e(o["images"][0])}" alt="" loading="lazy">'
        f'<span>{e(o["name"])}</span><b>{yen(sale_price(o))}</b></a>'
        for o in DATA["products"] if o["asin"] != asin)
    note = ("" if p.get("checkout_url") else
            '<p class="buy-note">※ 現在、ご購入手続きはAmazon.co.jpの商品ページで承っています。'
            'Amazonでの販売価格は当サイトと異なる場合があります。</p>')
    ld = {
        "@context": "https://schema.org", "@type": "Product",
        "name": p["title"], "sku": asin, "brand": {"@type": "Brand", "name": "YHBIN"},
        "image": p["images"][0],
        "offers": {"@type": "Offer", "priceCurrency": "JPY", "price": price,
                   "availability": "https://schema.org/InStock"},
    }
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(p["name"])} | YHBIN Japan</title>
<meta name="claude:viewport-fit-sides" content="cover">
<meta name="description" content="{e(p["title"][:120])}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Michroma&family=Zen+Kaku+Gothic+New:wght@300;500;700&family=Noto+Sans+JP:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500&display=swap">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<style>{css}{DETAIL_CSS}</style>
</head>
<body>
{header("../")}
<main>
  <div class="wrap">
    <nav class="crumbs" aria-label="パンくずリスト">
      <a href="../index.html">ホーム</a><span aria-hidden="true">/</span>
      <a href="../index.html#lineup">製品ラインナップ</a><span aria-hidden="true">/</span>
      <span>{e(p["name"])}</span>
    </nav>

    <div class="pdp">
      <div class="gallery">
        <div class="gallery-main"><img id="mainImage" src="{e(imgs[0])}" alt="{e(p["name"])}" fetchpriority="high"></div>
        <div class="thumbs" aria-label="商品画像">{thumbs}</div>
      </div>

      <div class="buy">
        <p class="eyebrow">{e(p["series"])}</p>
        <h1>{e(p["name"])}</h1>
        <p class="full-title">{e(p["title"])}</p>
        <p class="rating" aria-label="Amazon評価 5つ星のうち{p["rating"]:.1f}"><span class="stars" style="--r:{p["rating"]}"></span>{p["rating"]:.1f}<small>（Amazon.co.jpでの評価 {p["reviews"]}件）</small></p>
        <div class="buy-price">
          <p class="amount">{yen(price)}<small>税込</small></p>
        </div>
        <dl class="buy-specs">{specs}</dl>
        <div class="buy-actions">
          <a class="btn btn-primary" href="{e(checkout)}" target="_blank" rel="noopener">購入する</a>
          {note}
        </div>
        <div class="assure">
          <ul>
            <li>ご購入日から1年間のメーカー保証</li>
            <li>初期設定・使い方のご質問は日本語でサポート</li>
            <li>Windows 11 Pro 搭載、届いてすぐに使えます</li>
          </ul>
        </div>
      </div>
    </div>
  </div>

  <section class="section">
    <div class="wrap">
      <div class="section-head"><p class="eyebrow">Features</p><h2>この商品について</h2></div>
      <ul class="about">{about}</ul>
    </div>
  </section>

  <section class="section">
    <div class="wrap">
      <div class="section-head"><p class="eyebrow">Specifications</p><h2>仕様</h2></div>
      <div class="spec-table-wrap"><table class="spec-table"><tbody>{rows}</tbody></table></div>
    </div>
  </section>

  <section class="section">
    <div class="wrap">
      <div class="section-head"><p class="eyebrow">Gallery</p><h2>商品画像</h2></div>
      <div class="long-images">{long_imgs}</div>
    </div>
  </section>

  <section class="section">
    <div class="wrap">
      <div class="section-head"><p class="eyebrow">Lineup</p><h2>ほかのモデル</h2></div>
      <div class="others">{others}</div>
    </div>
  </section>
</main>
{footer()}
<script>{GALLERY_JS}</script>
</body>
</html>
"""


def card_data(p):
    return {
        "asin": p["asin"], "series": p["series"], "category": p["category"], "badge": p["badge"],
        "name": p["name"], "specs": p["specs"], "price": sale_price(p),
        "rating": p["rating"], "reviews": p["reviews"], "image": p["images"][0],
    }


def main():
    css = shared_css()
    out = ROOT / "products"
    out.mkdir(exist_ok=True)
    for p in DATA["products"]:
        (out / f"{p['asin']}.html").write_text(detail_page(p, css), encoding="utf-8")
        print(f"products/{p['asin']}.html  {yen(sale_price(p))}")

    src = INDEX.read_text(encoding="utf-8")
    cards = json.dumps([card_data(p) for p in DATA["products"]], ensure_ascii=False, indent=1)
    src, n = re.subn(r"/\* BUILD:PRODUCTS \*/.*?/\* END:PRODUCTS \*/",
                     lambda _: f"/* BUILD:PRODUCTS */const PRODUCTS = {cards};/* END:PRODUCTS */",
                     src, flags=re.S)
    assert n == 1, "index.html に BUILD:PRODUCTS マーカーが見つかりません"
    INDEX.write_text(src, encoding="utf-8")
    print("index.html updated")


if __name__ == "__main__":
    main()
