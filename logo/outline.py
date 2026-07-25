"""Convert <text> elements in a logo SVG to vector <path> outlines, so the file
renders identically on machines without the fonts. Handles plain <text> (x/y)
and <textPath> (text following an arc path).
Usage: python logo/outline.py in.svg out.svg
"""
import sys, re, math, html
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

FONT_FILES = {
    "Playfair Display|500": "logo/fonts/playfair-display-500.ttf",
    "Playfair Display|600": "logo/fonts/playfair-display-600.ttf",
    "Playfair Display|700": "logo/fonts/playfair-display-700.ttf",
    "Cormorant Garamond|600": "logo/fonts/cormorant-garamond-600.ttf",
    "Cormorant Garamond|700": "logo/fonts/cormorant-garamond-700.ttf",
    "Oswald|400": "logo/fonts/oswald-400.ttf",
    "Oswald|500": "logo/fonts/oswald-500.ttf",
    "Oswald|600": "logo/fonts/oswald-600.ttf",
}
_fonts = {}
def load(fam, weight):
    key = f"{fam}|{weight}"
    if key not in _fonts:
        f = TTFont(FONT_FILES[key])
        _fonts[key] = (f, f["head"].unitsPerEm, f.getBestCmap(), f["hmtx"], f.getGlyphSet())
    return _fonts[key]

def attr(tag, name, default=None):
    m = re.search(rf'{name}="([^"]*)"', tag)
    return m.group(1) if m else default

def glyph_path(gs, glyphname, scale, dx, dy):
    pen = SVGPathPen(gs)
    gs[glyphname].draw(pen)
    d = pen.getCommands()
    if not d:
        return ""
    # transform: flip Y (font up = +y), scale, translate
    return f'<path d="{d}" transform="translate({dx:.3f},{dy:.3f}) scale({scale:.5f},{-scale:.5f})"/>'

def advance(hmtx, upem, cmap, ch, size, tracking):
    gid = cmap.get(ord(ch))
    adv = (hmtx[gid][0] if gid else upem*0.5)
    return adv/upem*size + tracking

def outline_plain(tag, text):
    fam = attr(tag, "font-family")
    weight = attr(tag, "font-weight", "400")
    size = float(attr(tag, "font-size"))
    x = float(attr(tag, "x", "0")); y = float(attr(tag, "y", "0"))
    anchor = attr(tag, "text-anchor", "start")
    tracking = float(attr(tag, "letter-spacing", "0"))
    fill = attr(tag, "fill", "#000")
    f, upem, cmap, hmtx, gs = load(fam, weight)
    total = sum(advance(hmtx, upem, cmap, c, size, tracking) for c in text)
    if anchor == "middle": x -= total/2
    elif anchor == "end": x -= total
    scale = size/upem
    out = [f'<g fill="{fill}">']
    cx = x
    for ch in text:
        gid = cmap.get(ord(ch))
        if gid and gid != '.notdef':
            gname = gid
            p = glyph_path(gs, gname, scale, cx, y)
            if p: out.append(p)
        cx += advance(hmtx, upem, cmap, ch, size, tracking)
    out.append('</g>')
    return "".join(out)

def parse_arc(d):
    """Fallback geometry recovery from a semicircular arc `d`.

    Handles both the absolute (`A`) and relative (`a`) forms. svgo rewrites
    absolute arcs to relative ones, and reading a relative endpoint as absolute
    silently yields a plausible-but-wrong circle centre -- which is what
    corrupted every previously shipped outlined badge. Prefer arc_geometry().
    """
    cmd = re.search(r'[Aa]', d)
    nums = list(map(float, re.findall(r'-?\d*\.?\d+', d)))
    sx, sy, rx, ry, xrot, large, sweep, ex, ey = nums[:9]
    if cmd and cmd.group(0) == 'a':      # relative: endpoint is an offset
        ex, ey = sx + ex, sy + ey
    r = rx
    # both our arcs are semicircles; center is the midpoint of the (diameter) chord
    cx = (sx+ex)/2; cy = (sy+ey)/2
    a0 = math.atan2(sy-cy, sx-cx)
    return cx, cy, r, a0, sweep


def arc_geometry(tag, d):
    """Circle geometry for an arc baseline. generate.py stamps data-* attributes
    carrying the exact values, so no path parsing is involved; parse_arc is only
    a fallback for hand-written SVGs."""
    cx, cy = attr(tag, "data-cx"), attr(tag, "data-cy")
    r, a0, sweep = attr(tag, "data-r"), attr(tag, "data-a0"), attr(tag, "data-sweep")
    if None not in (cx, cy, r, a0, sweep):
        return float(cx), float(cy), float(r), math.radians(float(a0)), float(sweep)
    return parse_arc(d)

def outline_textpath(text_tag, tp_tag, text, arcs):
    fam = attr(text_tag, "font-family")
    weight = attr(text_tag, "font-weight", "400")
    size = float(attr(text_tag, "font-size"))
    tracking = float(attr(text_tag, "letter-spacing", "0"))
    fill = attr(text_tag, "fill") or "#000"
    href = attr(tp_tag, "href").lstrip("#")
    cx, cy, r, a0, sweep = arcs[href]
    f, upem, cmap, hmtx, gs = load(fam, weight)
    total = sum(advance(hmtx, upem, cmap, c, size, tracking) for c in text)
    direction = 1 if sweep == 1 else -1
    # startOffset 50% + text-anchor middle => center the text on the arc midpoint
    arc_mid = a0 + direction * (math.pi/2)
    ang = arc_mid - direction * (total/2)/r
    scale = size/upem
    out = [f'<g fill="{fill}">']
    for ch in text:
        adv = advance(hmtx, upem, cmap, ch, size, tracking)
        a_center = ang + direction*(adv/2)/r
        px = cx + r*math.cos(a_center)
        py = cy + r*math.sin(a_center)
        rot = math.degrees(a_center) + (90 if direction>0 else -90)
        gid = cmap.get(ord(ch))
        if gid and gid != '.notdef' and ch != ' ':
            pen = SVGPathPen(gs); gs[gid].draw(pen); dcmd = pen.getCommands()
            if dcmd:
                # place glyph: translate to point, rotate tangent, flip-y scale, shift left by half glyph adv
                gadv = (hmtx[gid][0]/upem*size)
                out.append(f'<path d="{dcmd}" transform="translate({px:.3f},{py:.3f}) rotate({rot:.3f}) '
                           f'scale({scale:.5f},{-scale:.5f}) translate({-gadv/2/scale:.3f},0)"/>')
        ang += direction*adv/r
    out.append('</g>')
    return "".join(out)

def main(inp, outp):
    svg = open(inp, encoding="utf-8").read()
    # collect arc path definitions
    arcs = {}
    for m in re.finditer(r'<path\b[^>]*\bid="([^"]+)"[^>]*>', svg):
        tag = m.group(0)
        d = attr(tag, "d")
        if not d:
            continue
        try:
            arcs[m.group(1)] = arc_geometry(tag, d)
        except Exception:
            pass
    # Only the badge has arced text; the mark and wordmark legitimately have none.
    # Failing loudly here matters because mis-resolved arc geometry does not error,
    # it silently flings the text off-canvas -- which is how broken assets shipped.
    if "<textPath" in svg and not arcs:
        raise SystemExit(f"{inp}: has <textPath> but no resolvable arc baselines -- "
                         "refusing to emit mis-placed arced text")
    # textPath blocks
    def repl_tp(m):
        return outline_textpath(m.group(0), m.group(1), html.unescape(m.group(2)), arcs)
    svg = re.sub(r'<text\b[^>]*>\s*<textPath\b([^>]*)>(.*?)</textPath>\s*</text>',
                 repl_tp, svg, flags=re.S)
    # plain text
    def repl_txt(m):
        return outline_plain(m.group(0), html.unescape(m.group(1)))
    svg = re.sub(r'<text\b[^>]*>([^<]*)</text>', repl_txt, svg, flags=re.S)
    open(outp, "w", encoding="utf-8").write(svg)
    print("outlined ->", outp)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
