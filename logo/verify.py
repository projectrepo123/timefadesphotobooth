"""Assert the shipped SVGs still render like their editable masters.

Why this exists: outlining and svgo are both silent about geometric corruption.
When svgo rewrote the arc baselines to relative form, `outline.py` mis-read the
circle centre and flung the arced text off-canvas -- no error, no warning, and
the broken files shipped. Rendering the master and the final asset and diffing
the pixels is the only check that actually catches that class of bug.

Usage:  python logo/verify.py            # checks every master/outlined pair
        python logo/verify.py a.svg b.svg
Exits non-zero on failure so export-logo.sh can refuse to publish.
"""
import subprocess, sys, tempfile, os
from PIL import Image, ImageChops, ImageFilter

RESVG = ["node", "node_modules/@resvg/resvg-js-cli/bin/resvg-js-cli.mjs"]
WIDTH = 600

# Outlining swaps resvg's glyph rasteriser for filled paths, so every letter edge
# differs by a sub-pixel amount -- a raw pixel diff of a correct pair still reads
# ~8/255 and cannot be told apart from real breakage. Blurring first collapses
# those hairline edge differences while leaving any bodily displacement intact.
#
# Calibrated at this radius against deliberately corrupted controls:
#                                     badge   mark
#   correct outlining ..............   0.51   1.56   <- the mark reads higher only
#   text shifted 8px ...............     --   6.33      because one huge glyph puts
#   arced text shifted 25px ........   3.27  15.37      a lot of edge on empty canvas
#   historical off-centre corruption   9.63     --
# 2.5 clears the worst correct case by 1.6x and still catches the tightest
# failure (badge shifted 25px) by 1.3x.
BLUR_RADIUS = 12
MAX_MEAN_DELTA = 2.5

PAIRS = [
    ("logo/logo-full.svg",          "logo/outlined/logo-full.svg"),
    ("logo/logo-reversed.svg",      "logo/outlined/logo-reversed.svg"),
    ("logo/logo-mark.svg",          "logo/outlined/logo-mark.svg"),
    ("logo/logo-mark-solid.svg",    "logo/outlined/logo-mark-solid.svg"),
    ("logo/logo-mark-brass.svg",    "logo/outlined/logo-mark-brass.svg"),
    ("logo/logo-mark-reversed.svg", "logo/outlined/logo-mark-reversed.svg"),
    ("logo/logo-wordmark.svg",      "logo/outlined/logo-wordmark.svg"),
]


def render(svg, png):
    subprocess.run(RESVG + ["--font-dir", "logo/fonts", "--fit-width", str(WIDTH),
                            "--background", "#ffffff", svg, png],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def compare(master, shipped, tmp):
    a = os.path.join(tmp, "a.png")
    b = os.path.join(tmp, "b.png")
    render(master, a)
    render(shipped, b)
    ia, ib = Image.open(a).convert("L"), Image.open(b).convert("L")
    if ia.size != ib.size:
        return None, f"size mismatch {ia.size} vs {ib.size}"
    blur = ImageFilter.GaussianBlur(BLUR_RADIUS)
    diff = ImageChops.difference(ia.filter(blur), ib.filter(blur))
    mean = sum(c * i for i, c in enumerate(diff.histogram())) / (ia.width * ia.height)
    return mean, None


def main(argv):
    pairs = [(argv[0], argv[1])] if len(argv) == 2 else PAIRS
    failures = []
    with tempfile.TemporaryDirectory() as tmp:
        for master, shipped in pairs:
            if not (os.path.exists(master) and os.path.exists(shipped)):
                print(f"  SKIP  {shipped} (missing)")
                continue
            mean, err = compare(master, shipped, tmp)
            if err:
                print(f"  FAIL  {shipped}: {err}")
                failures.append(shipped)
            elif mean > MAX_MEAN_DELTA:
                print(f"  FAIL  {shipped}: mean delta {mean:.2f} > {MAX_MEAN_DELTA}")
                failures.append(shipped)
            else:
                print(f"  ok    {shipped}  (mean delta {mean:.2f})")
    if failures:
        print(f"\n{len(failures)} file(s) do not match their master -- not safe to ship.")
        return 1
    print("\nAll outlined SVGs match their masters.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
