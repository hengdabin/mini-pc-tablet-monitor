#!/usr/bin/env bash
# Amazon.co.jp の商品画像を images/<ASIN>.jpg として保存する。
# 使い方: yhbin-jp ディレクトリで ./fetch-images.sh
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p images
while read -r asin id; do
  [ -z "$asin" ] && continue
  curl -fsSL -A "Mozilla/5.0" -o "images/$asin.jpg" \
    "https://m.media-amazon.com/images/I/$id._AC_SL1000_.jpg"
  echo "saved images/$asin.jpg"
done <<'LIST'
B0CKXZ3S1D 61dI0nf6KOL
B0H45CDZS9 71lCWHTi4fL
B0H6CX1BWL 71xOQjDVw-L
B0FKTF3723 71-D8OWZnZL
B0CW9C86BC 81H1QWVS2VL
B0GCZJL488 714zAU1wv5L
LIST
