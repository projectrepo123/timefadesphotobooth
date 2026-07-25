#!/usr/bin/env bash
# Rebuild the whole logo system from generate.py.
#   generate -> outline -> svgo -> verify -> export -> assets/
# Run from the repo root:  bash logo/build.sh
#
# Ordering matters: outlining happens BEFORE svgo. svgo rewrites arc paths into
# relative form, and an outliner that mis-reads that produces silently broken
# text. outline.py now reads data-* geometry so it is immune either way, but the
# ordering plus verify.py is the belt-and-braces that keeps it that way.
set -e
cd "$(dirname "$0")/.."

SVGO="node node_modules/svgo/bin/svgo --config logo/svgo.config.mjs"
mkdir -p logo/outlined

echo "1/5  Generating masters ..."
python logo/generate.py badge                                  > logo/logo-full.svg
python logo/generate.py badge reversed=true bg=true            > logo/logo-reversed.svg
python logo/generate.py mark  bg=false                         > logo/logo-mark.svg
python logo/generate.py mark  bg=false solid_ring=true         > logo/logo-mark-solid.svg
python logo/generate.py mark  bg=false color='#c69a4c'         > logo/logo-mark-brass.svg
python logo/generate.py mark  bg=false reversed=true           > logo/logo-mark-reversed.svg
python logo/generate.py wordmark                               > logo/logo-wordmark.svg

echo "2/5  Outlining text -> paths ..."
for f in logo/logo-*.svg; do
  python logo/outline.py "$f" "logo/outlined/$(basename "$f")" >/dev/null
done

echo "3/5  Optimising with svgo ..."
for f in logo/logo-*.svg logo/outlined/*.svg; do
  $SVGO -i "$f" -o "$f" >/dev/null
done

echo "4/5  Verifying outlined == master ..."
python logo/verify.py

echo "5/5  Exporting PNG / favicon / print assets ..."
bash logo/export-logo.sh
