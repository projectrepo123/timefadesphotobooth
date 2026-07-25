#!/usr/bin/env bash
# Render an SVG to PNG at a given width using resvg-js with the local logo fonts.
# Usage: ./render.sh <input.svg> <output.png> <width>
set -e
cd "$(dirname "$0")/.."
IN="$1"; OUT="$2"; W="${3:-800}"
node node_modules/@resvg/resvg-js-cli/bin/resvg-js-cli.mjs \
  --font-dir logo/fonts \
  --fit-width "$W" \
  --background "#ffffff00" \
  "$IN" "$OUT"
