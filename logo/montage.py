"""Compose labeled PNG tiles into a single comparison sheet."""
import sys, subprocess, os, tempfile
from PIL import Image, ImageDraw, ImageFont

# args: out.png W  label1 svg1  label2 svg2 ...
out = sys.argv[1]
tile_w = int(sys.argv[2])
pairs = sys.argv[3:]
items = [(pairs[i], pairs[i+1]) for i in range(0, len(pairs), 2)]

RESVG = ["node", "node_modules/@resvg/resvg-js-cli/bin/resvg-js-cli.mjs"]
pad = 24
label_h = 30
cols = min(len(items), 3)
rows = (len(items) + cols - 1) // cols

def render(svg, w):
    fd, tmp = tempfile.mkstemp(suffix=".png"); os.close(fd)
    subprocess.run(RESVG + ["--font-dir", "logo/fonts", "--fit-width", str(w),
                    "--background", "#ffffff00", svg, tmp], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    im = Image.open(tmp).convert("RGBA")
    return im

tiles = [(lbl, render(svg, tile_w)) for lbl, svg in items]
cell_w = tile_w + pad*2
cell_h = tile_w + pad*2 + label_h
sheet = Image.new("RGBA", (cell_w*cols, cell_h*rows), "#e7ddca")
draw = ImageDraw.Draw(sheet)
try:
    font = ImageFont.truetype("logo/fonts/oswald-500.ttf", 16)
except Exception:
    font = ImageFont.load_default()

for idx, (lbl, im) in enumerate(tiles):
    r, c = divmod(idx, cols)
    x = c*cell_w; y = r*cell_h
    # checker-free flat card
    draw.rectangle([x+8, y+8, x+cell_w-8, y+cell_h-8], fill="#f8f4ec")
    sheet.alpha_composite(im, (x+pad, y+pad+label_h))
    draw.text((x+pad, y+pad-4), lbl, fill="#2b2019", font=font)

sheet.convert("RGB").save(out)
print("wrote", out, sheet.size)
