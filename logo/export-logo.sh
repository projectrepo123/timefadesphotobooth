#!/usr/bin/env bash
# Generate all production logo assets from the master SVGs.
# Renders from the /outlined SVGs (font-independent) so output never depends
# on installed fonts. Run from the repo root:  bash logo/export-logo.sh
set -e
cd "$(dirname "$0")/.."

RESVG="node node_modules/@resvg/resvg-js-cli/bin/resvg-js-cli.mjs"
SRC=logo/outlined
OUT=logo/export
mkdir -p "$OUT/png" "$OUT/favicon" "$OUT/social" "$OUT/print"

render () { # <svg> <width> <out> [bg]
  local bg="${4:-#ffffff00}"
  $RESVG --font-dir logo/fonts --fit-width "$2" --background "$bg" "$1" "$3" >/dev/null
}

echo "PNG masters (transparent) ..."
for name in logo-full logo-reversed logo-wordmark; do
  for w in 2400 1200 600; do
    render "$SRC/$name.svg" "$w" "$OUT/png/${name}-${w}.png"
  done
done

echo "Favicons ..."
# small sizes use the solid-ring mark (dashes turn to noise <=48px); 180 uses the dashed mark.
# All get the paper background: dark ink on transparent disappears in a dark browser theme.
render "$SRC/logo-mark-solid.svg" 16  "$OUT/favicon/favicon-16.png"  "#f8f4ec"
render "$SRC/logo-mark-solid.svg" 32  "$OUT/favicon/favicon-32.png"  "#f8f4ec"
render "$SRC/logo-mark-solid.svg" 48  "$OUT/favicon/favicon-48.png"  "#f8f4ec"
render "$SRC/logo-mark.svg"       180 "$OUT/favicon/apple-touch-icon.png" "#f8f4ec"

echo "Social avatar + print + .ico ..."
python - <<'PY'
from PIL import Image
import subprocess, os
RESVG = ["node","node_modules/@resvg/resvg-js-cli/bin/resvg-js-cli.mjs"]
def render(svg,w,out,bg="#ffffff00"):
    subprocess.run(RESVG+["--font-dir","logo/fonts","--fit-width",str(w),
        "--background",bg,svg,out],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

# Social avatar: full badge on paper, square-safe padding
render("logo/outlined/logo-full.svg",820,"logo/export/social/_a.png")
badge=Image.open("logo/export/social/_a.png").convert("RGBA")
av=Image.new("RGBA",(1000,1000),"#f8f4ec")
av.alpha_composite(badge,((1000-badge.width)//2,(1000-badge.height)//2))
av.convert("RGB").save("logo/export/social/avatar-1000.png")
os.remove("logo/export/social/_a.png")

# Print-res: 10in @ 300dpi = 3000px, transparent
render("logo/outlined/logo-full.svg",3000,"logo/export/print/logo-full-300dpi.png")

# Multi-size favicon.ico from the solid mark
render("logo/outlined/logo-mark-solid.svg",64,"logo/export/favicon/_ico.png","#f8f4ec")
ico=Image.open("logo/export/favicon/_ico.png").convert("RGBA")
ico.save("logo/export/favicon/favicon.ico",sizes=[(16,16),(32,32),(48,48)])
os.remove("logo/export/favicon/_ico.png")
print("  done")
PY

echo "Publishing to assets/ and site root ..."
# This copy used to be manual, which is exactly how a stale broken badge stayed
# live: logo/ was rebuilt, assets/ was not. Keep it scripted.
mkdir -p assets
cp "$SRC/logo-full.svg"          assets/tf-badge.svg
cp "$SRC/logo-reversed.svg"      assets/tf-badge-reversed.svg
cp "$SRC/logo-mark.svg"          assets/tf-mark.svg
cp "$SRC/logo-mark-brass.svg"    assets/tf-mark-brass.svg
cp "$SRC/logo-mark-reversed.svg" assets/tf-mark-reversed.svg
cp "$SRC/logo-wordmark.svg"      assets/tf-wordmark.svg

# Favicons are referenced from the site root by the <link rel="icon"> tags.
cp "$OUT/favicon/favicon-16.png"       favicon-16.png
cp "$OUT/favicon/favicon-32.png"       favicon-32.png
cp "$OUT/favicon/favicon-48.png"       favicon-48.png
cp "$OUT/favicon/favicon.ico"          favicon.ico
cp "$OUT/favicon/apple-touch-icon.png" apple-touch-icon.png
cp "$OUT/png/logo-full-1200.png"       logo-badge.png

echo "All assets written to $OUT/, assets/ and the site root"
find "$OUT" -type f | sort
