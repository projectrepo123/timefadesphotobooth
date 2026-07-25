"""Shared helpers: glyph measurement + letterspacing solving for the logo work."""
from fontTools.ttLib import TTFont

FONTS = {
    "cormorant-600": "logo/fonts/cormorant-garamond-600.ttf",
    "cormorant-700": "logo/fonts/cormorant-garamond-700.ttf",
    "playfair-500": "logo/fonts/playfair-display-500.ttf",
    "playfair-600": "logo/fonts/playfair-display-600.ttf",
    "playfair-700": "logo/fonts/playfair-display-700.ttf",
    "oswald-400": "logo/fonts/oswald-400.ttf",
    "oswald-500": "logo/fonts/oswald-500.ttf",
    "oswald-600": "logo/fonts/oswald-600.ttf",
}

_cache = {}

def _font(key):
    if key not in _cache:
        f = TTFont(FONTS[key])
        upem = f["head"].unitsPerEm
        cmap = f.getBestCmap()
        hmtx = f["hmtx"]
        _cache[key] = (f, upem, cmap, hmtx)
    return _cache[key]

def text_width(key, text, font_size, letter_spacing=0.0):
    """Width in user units of `text` at font_size, with letter_spacing (user units) between glyphs.
    Matches SVG behaviour: letter-spacing is added after every glyph advance."""
    f, upem, cmap, hmtx = _font(key)
    total = 0.0
    for ch in text:
        gid = cmap.get(ord(ch))
        if gid is None:
            adv = upem * 0.5
        else:
            adv = hmtx[gid][0]
        total += adv / upem * font_size + letter_spacing
    return total

def solve_letter_spacing(key, text, font_size, target_width):
    """Find the per-glyph letter-spacing (user units) that makes `text` exactly target_width wide."""
    n = len(text)
    base = text_width(key, text, font_size, 0.0)
    # each glyph contributes one letter_spacing; SVG adds it after each glyph incl last
    return (target_width - base) / n


def ink_width(key, text, font_size, letter_spacing=0.0):
    """Visible width of the set text: SVG adds letter-spacing after the *last* glyph too,
    so the advance width overstates the ink by one tracking unit. Optical alignment of two
    lines (e.g. TIME FADES over PHOTOBOOTH) has to compare ink, not advance."""
    return text_width(key, text, font_size, letter_spacing) - letter_spacing


def solve_letter_spacing_ink(key, text, font_size, target_ink):
    """Per-glyph letter-spacing that makes the *ink* of `text` exactly target_ink wide."""
    base = text_width(key, text, font_size, 0.0)
    return (target_ink - base) / (len(text) - 1)


def ink_center_shift(letter_spacing):
    """x-nudge that recentres a text-anchor="middle" run on its ink rather than its advance
    (the trailing letter-space otherwise drags the ink half a tracking unit left)."""
    return letter_spacing / 2.0

if __name__ == "__main__":
    # quick sanity dump
    for k in ["cormorant-600", "playfair-600", "oswald-500"]:
        w_tf = text_width(k, "TIME FADES", 24)
        w_pb = text_width(k, "PHOTOBOOTH", 17)
        print(f"{k:16} TIME FADES@24={w_tf:6.2f}  PHOTOBOOTH@17={w_pb:6.2f}")
