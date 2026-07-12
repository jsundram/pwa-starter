#!/usr/bin/env bash
# Rasterize the share-card SVG -> PNG (1200x630). The OG image MUST be a raster served at an
# ABSOLUTE https URL (iMessage/WhatsApp/Slack reject relative paths and won't render SVG), and
# should be compressed (keep it well under ~1 MB or some scrapers skip it). Edit assets/og.svg,
# rerun this. If the card has live <text>, the font must be installed locally or it falls back to a
# stock serif in the render.
set -euo pipefail
cd "$(dirname "$0")/../assets"
svg="${1:-og.svg}"
png="${svg%.svg}.png"
if command -v rsvg-convert >/dev/null; then
  rsvg-convert -w 1200 -h 630 "$svg" -o "$png"
else
  for c in chromium chromium-browser "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"; do
    command -v "$c" >/dev/null 2>&1 || [ -x "$c" ] || continue
    "$c" --headless --no-sandbox --hide-scrollbars --force-device-scale-factor=1 \
         --window-size=1200,630 --screenshot="$png" "file://$PWD/$svg" 2>/dev/null
    break
  done
fi
# optional: compress if you have pngquant / oxipng installed
command -v pngquant >/dev/null && pngquant --force --skip-if-larger --output "$png" "$png" 2>/dev/null || true
echo "wrote assets/$png ($(wc -c < "$png" | tr -d ' ') bytes)"
