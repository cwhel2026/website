#!/usr/bin/env bash
# Regenerate WebP/AVIF from verified Geograph sources under public/media/approved/source/.
set -euo pipefail
APPROVED="$(cd "$(dirname "$0")/../public/media/approved" && pwd)"
SRC="$APPROVED/source"
WEBP_Q=82

if ! command -v convert >/dev/null || ! command -v cwebp >/dev/null; then
  echo "Requires ImageMagick (convert) and libwebp (cwebp)." >&2
  exit 1
fi

convert "$SRC/uk-driveway-shoreham.jpg" -auto-orient -crop 100%x78%+0+8% +repage "$SRC/ba-base.jpg"
cp "$SRC/ba-base.jpg" "$SRC/ba-before.jpg"
convert "$SRC/ba-base.jpg" -modulate 100,90,100 -gamma 1.05 "$SRC/ba-after.jpg"
convert "$SRC/uk-tarmac-blackwood.jpg" -auto-orient -crop 100%x62%+0+28% +repage "$SRC/hero-home.jpg"
convert "$SRC/uk-tarmac-coventry.jpg" -gravity South -crop 100%x32%+0+0 +repage "$SRC/commercial-lot.jpg"
convert "$SRC/uk-driveway-yarm.jpg" -resize '1920x1920>' "$SRC/tarmac-wear.jpg"
convert "$SRC/uk-tarmac-blackwood.jpg" -resize '1920x1920>' "$SRC/tarmac-surface.jpg"
convert "$SRC/uk-block-paving-walsal.jpg" -resize '1920x1920>' "$SRC/block-paving.jpg"

for name in hero-home ba-before ba-after tarmac-surface tarmac-wear block-paving commercial-lot; do
  in="$SRC/${name}.jpg"
  cwebp -quiet -q "$WEBP_Q" "$in" -o "$APPROVED/${name}.webp"
  if command -v avifenc >/dev/null; then
    avifenc --min 20 --max 30 "$in" "$APPROVED/${name}.avif" >/dev/null
  else
    convert "$in" -define avif:lossless=false -quality 52 "$APPROVED/${name}.avif"
  fi
done

echo "Wrote optimised assets to $APPROVED"