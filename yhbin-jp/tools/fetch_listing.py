#!/usr/bin/env python3
"""Amazon.co.jp の商品ページから画像・タイトル・特徴・仕様・評価を取り込み、data/products.json を更新する。

使い方（yhbin-jp ディレクトリで）:  python3 tools/fetch_listing.py [ASIN ...]
  ASIN を省略すると products.json の全製品を更新する。
  series / category / badge / name / specs / amazon_price は手入力の値をそのまま残す。
  終わったら python3 tools/build.py でページを再生成する。

依存: pip install beautifulsoup4 pillow
"""
import io
import json
import re
import sys
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "products.json"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ja-JP,ja;q=0.9"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def text(el):
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip() if el else ""


def fetch(product):
    asin = product["asin"]
    page = get(f"https://www.amazon.co.jp/dp/{asin}").decode("utf-8", "ignore")
    soup = BeautifulSoup(page, "html.parser")
    if not soup.select_one("#productTitle"):
        raise RuntimeError(f"{asin}: 商品ページを取得できませんでした（認証画面の可能性）")

    product["title"] = text(soup.select_one("#productTitle"))
    product["bullets"] = [t for t in (text(li) for li in soup.select("#feature-bullets li span.a-list-item")) if t]
    details = []
    for tr in soup.select("#productOverview_feature_div tr"):
        cells = tr.find_all(["th", "td"])
        if len(cells) >= 2:
            details.append([text(cells[0]), text(cells[1])])
    if details:
        product["details"] = details
    m = re.search(r"うち([\d.]+)", text(soup.select_one("#acrPopover .a-icon-alt")))
    n = re.search(r"([\d,]+)", text(soup.select_one("#acrCustomerReviewText")))
    if m and n:
        product["rating"], product["reviews"] = float(m.group(1)), int(n.group(1).replace(",", ""))

    urls = list(dict.fromkeys(re.findall(r'"hiRes":"(https://m\.media-amazon\.com/images/I/[^"]+)"', page)))
    folder = ROOT / "images" / asin
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob("*.jpg"):
        old.unlink()
    images = []
    for i, url in enumerate(urls, 1):
        im = Image.open(io.BytesIO(get(url))).convert("RGB")
        im.thumbnail((1000, 1000), Image.LANCZOS)
        im.save(folder / f"{i}.jpg", quality=80, optimize=True, progressive=True)
        images.append(f"images/{asin}/{i}.jpg")
    if images:
        product["images"] = images
    print(f"{asin}: {len(images)} images, {len(product['bullets'])} bullets, ★{product.get('rating')}")


def main():
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    wanted = set(sys.argv[1:])
    for p in data["products"]:
        if not wanted or p["asin"] in wanted:
            fetch(p)
    DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
