"""Parametric generator for the Time Fades badge. Emits editable-text SVGs.

Vintage postmark / rubber-stamp badge with a clock at its centre — the clock is
the concept, since it carries the company name.

Concentric bands (viewBox 0 0 800 800, centre 400,400):

    r 375        dashed outer ring (postmark perforation)
    r 310-353    arced text band; both arcs share one size + tracking
    r 210        inner "clock face" circle + diamond accents at 3 and 9
    r <= 145     clock hands (69% / 50% of the inner radius)

The two arcs deliberately subtend *different angles* (~110 deg top, ~145 deg
bottom): the bottom string is 47% longer, and setting both at one size and one
tracking is what "mathematically consistent" means. Equalising the spans instead
would force two different trackings, which is the flaw this rebuild replaces.
"""
import math
import lib

# --- palette: one warm-brown hue, three values ---
INK   = "#2b211c"   # primary  (rings, arced text, TIME FADES)
BR2   = "#4a3a30"   # secondary (PHOTOBOOTH)
BR3   = "#7d6a5c"   # tertiary  (clock hands, diamonds)
PAPER = "#f0ebe1"

SERIF = {"playfair":  ("Playfair Display",  "playfair-700",  700),
         "cormorant": ("Cormorant Garamond", "cormorant-600", 600)}

# --- geometry (single source of truth for the bands above) ---
SIZE       = 800
C          = SIZE / 2
R_RING     = 375       # dashed outer ring
R_ARC_IN   = 310       # top-arc baseline; its caps grow outward
R_INNER    = 210       # "clock face" circle
R_DIAMOND  = 330       # accents sit in the text band, in the 3/9 o'clock gap
ARC_SIZE   = 55        # shared by BOTH arcs
ARC_TRACK  = 3.3       # shared by BOTH arcs
CAP_RATIO  = 0.708     # Playfair Display cap height, in em

# --- centre wordmark ---
WORDMARK_W = 567       # ink width of TIME+gap+FADES; overflows R_INNER by design
TF_TRACK_K = 0.02      # intra-word tracking, as a fraction of font size
PB_SIZE    = 42
PB_WIDTH   = 370       # ink width of PHOTOBOOTH
PB_GAP     = 20        # TIME FADES baseline -> PHOTOBOOTH cap top

# --- clock ---
HOUR_ANGLE = -50.0     # degrees from 12 o'clock; ~10:10, deliberately asymmetric
MIN_ANGLE  = 54.0
HOUR_LEN   = 105.0
MIN_LEN    = 145.0
HAND_BASE_W = 7.0      # half-width at the pivot; hands taper to a point
PIVOT_R    = 9.0
DIAMOND_R  = 22.0


def dash(r, n, duty=0.55):
    """Dash/gap pair that tiles a circle of radius `r` exactly `n` times, so the
    pattern closes cleanly instead of leaving a seam where it wraps."""
    period = 2 * math.pi * r / n
    return period * duty, period * (1 - duty)


def _arc(pid, cx, cy, r, start_deg, sweep):
    """Semicircular baseline for arced text.

    Also stamps the circle geometry as data-* attributes: outline.py reads those
    instead of re-parsing `d`, which svgo is free to rewrite into relative form
    (that rewrite is exactly what silently broke the previously shipped assets).
    """
    a0 = math.radians(start_deg)
    sx, sy = cx + r * math.cos(a0), cy + r * math.sin(a0)
    ex, ey = cx - r * math.cos(a0), cy - r * math.sin(a0)
    return (f'<path id="{pid}" fill="none" '
            f'data-cx="{cx}" data-cy="{cy}" data-r="{r}" '
            f'data-a0="{start_deg}" data-sweep="{sweep}" '
            f'd="M {sx:.3f},{sy:.3f} A {r},{r} 0 0 {sweep} {ex:.3f},{ey:.3f}"/>')


def _hand(angle_deg, length, base_w, fill):
    """Tapered clock hand from the pivot: a stroked line reads as a stray chevron,
    a silhouette reads as a hand."""
    a = math.radians(angle_deg)
    dx, dy = math.sin(a), -math.cos(a)      # along the hand
    px, py = math.cos(a), math.sin(a)       # across it
    tip = 1.2
    pts = [(C + px * base_w,              C + py * base_w),
           (C + dx * length + px * tip,   C + dy * length + py * tip),
           (C + dx * length - px * tip,   C + dy * length - py * tip),
           (C - px * base_w,              C - py * base_w)]
    return ('<polygon points="' + " ".join(f"{x:.2f},{y:.2f}" for x, y in pts) +
            f'" fill="{fill}"/>')


def _diamond(cx, cy, r, fill):
    """Four-pointed concave star flanking the wordmark."""
    return (f'<path transform="translate({cx},{cy})" fill="{fill}" '
            f'd="M 0,{-r} Q 0,0 {r},0 Q 0,0 0,{r} Q 0,0 {-r},0 Q 0,0 0,{-r} Z"/>')


def min_word_gap(cap_h):
    """Narrowest TIME/FADES gap that still lets both hands leave the cap band
    without touching a letterform. Derived rather than hardcoded so the guarantee
    survives someone retuning the hand angles."""
    steepest = max(abs(HOUR_ANGLE), abs(MIN_ANGLE))
    return 2 * ((cap_h / 2) * math.tan(math.radians(steepest)) + HAND_BASE_W + 4)


def badge(serif="playfair", clock=True, diamonds=True, reversed=False, bg=False):
    s_family, s_key, s_weight = SERIF[serif]

    # A rubber stamp is struck in a single ink, so the badge is monochrome —
    # hierarchy comes from weight and scale, not from tint.
    c_primary = PAPER if reversed else INK
    c_sec = c_ter = c_primary
    canvas = "#2f2119" if reversed else PAPER

    # --- centre wordmark: TIME and FADES are two runs, not one string with a
    #     space, so the gap the hands pass through is controllable ---
    cap_h = CAP_RATIO * 1.0     # provisional; real cap depends on solved size
    gap = 100.0
    for _ in range(4):          # gap and size are mutually dependent; converge
        base = (lib.text_width(s_key, "TIME", 1.0) +
                lib.text_width(s_key, "FADES", 1.0))
        track_units = (len("TIME") - 1) + (len("FADES") - 1)
        tf_size = (WORDMARK_W - gap) / (base + track_units * TF_TRACK_K)
        tf_track = TF_TRACK_K * tf_size
        cap_h = CAP_RATIO * tf_size
        gap = max(gap, min_word_gap(cap_h))

    tf_baseline = C + cap_h / 2                     # cap band centres on C
    pb_track = lib.solve_letter_spacing_ink(s_key, "PHOTOBOOTH", PB_SIZE, PB_WIDTH)
    pb_baseline = tf_baseline + PB_GAP + CAP_RATIO * PB_SIZE

    arc_cap = CAP_RATIO * ARC_SIZE
    r_arc_out = R_ARC_IN + arc_cap

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}" '
         f'width="{SIZE}" height="{SIZE}">']
    if bg:
        p.append(f'<rect width="{SIZE}" height="{SIZE}" fill="{canvas}"/>')

    # --- rings ---
    d_on, d_off = dash(R_RING, 56)
    p.append(f'<g id="rings">')
    p.append(f'<circle cx="{C}" cy="{C}" r="{R_RING}" fill="none" stroke="{c_primary}" '
             f'stroke-width="10" stroke-dasharray="{d_on:.3f} {d_off:.3f}" stroke-linecap="butt"/>')
    p.append(f'<circle cx="{C}" cy="{C}" r="{R_INNER}" fill="none" stroke="{c_primary}" '
             f'stroke-width="2.5"/>')
    p.append('</g>')

    # --- clock: hands only; the inner circle is the dial. Drawn before the
    #     wordmark, though the derived gap means they never actually collide. ---
    if clock:
        p.append('<g id="clock">')
        p.append(_hand(MIN_ANGLE, MIN_LEN, HAND_BASE_W * 0.8, c_ter))
        p.append(_hand(HOUR_ANGLE, HOUR_LEN, HAND_BASE_W, c_ter))
        p.append(f'<circle cx="{C}" cy="{C}" r="{PIVOT_R}" fill="{c_primary}"/>')
        p.append('</g>')

    # --- arced text: one size, one tracking, both arcs. The top baseline is the
    #     band's inner edge (caps grow outward); the bottom baseline is its outer
    #     edge (caps grow inward), so the two occupy the identical radial band. ---
    p.append('<g id="arcs">')
    p.append(_arc("topArc", C, C, R_ARC_IN, 180, 1))
    p.append(_arc("botArc", C, C, r_arc_out, 180, 0))
    for pid, text in (("topArc", "REMEMBER WHEN"), ("botArc", "BEFORE TIME FADES AWAY")):
        p.append(f'<text fill="{c_primary}" font-family="{s_family}" font-weight="{s_weight}" '
                 f'font-size="{ARC_SIZE}" letter-spacing="{ARC_TRACK}">'
                 f'<textPath href="#{pid}" startOffset="50%" text-anchor="middle">{text}</textPath></text>')
    p.append('</g>')

    if diamonds:
        p.append('<g id="diamonds">')
        p.append(_diamond(C - R_DIAMOND, C, DIAMOND_R, c_ter))
        p.append(_diamond(C + R_DIAMOND, C, DIAMOND_R, c_ter))
        p.append('</g>')

    # --- centre wordmark ---
    half = gap / 2
    p.append('<g id="wordmark">')
    # anchor="end" positions the *advance* end, which includes the trailing
    # letter-space; add it back so the ink lands on the gap edge.
    p.append(f'<text x="{C - half + tf_track:.3f}" y="{tf_baseline:.2f}" text-anchor="end" '
             f'font-family="{s_family}" font-weight="{s_weight}" font-size="{tf_size:.2f}" '
             f'letter-spacing="{tf_track:.3f}" fill="{c_primary}">TIME</text>')
    p.append(f'<text x="{C + half:.3f}" y="{tf_baseline:.2f}" text-anchor="start" '
             f'font-family="{s_family}" font-weight="{s_weight}" font-size="{tf_size:.2f}" '
             f'letter-spacing="{tf_track:.3f}" fill="{c_primary}">FADES</text>')
    p.append(f'<text x="{C + lib.ink_center_shift(pb_track):.3f}" y="{pb_baseline:.2f}" '
             f'text-anchor="middle" font-family="{s_family}" font-weight="500" '
             f'font-size="{PB_SIZE}" letter-spacing="{pb_track:.3f}" fill="{c_sec}">PHOTOBOOTH</text>')
    p.append('</g>')

    p.append('</svg>')
    return "\n".join(p)


def mark(reversed=False, bg=True, solid_ring=False, color=None):
    """TF monogram inside the dashed ring, for nav and favicon use. No clock: at
    32px dial detail turns to noise, so the full badge carries that idea and this
    stays a legible silhouette."""
    if reversed:
        c_primary, canvas = PAPER, "#2f2119"
    else:
        c_primary, canvas = INK, PAPER
    if color:
        c_primary = color
    s_family, s_key, s_weight = SERIF["playfair"]
    d_on, d_off = dash(372, 46)
    ring_dash = '' if solid_ring else f' stroke-dasharray="{d_on:.3f} {d_off:.3f}"'
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}" '
         f'width="{SIZE}" height="{SIZE}">']
    if bg:
        p.append(f'<rect width="{SIZE}" height="{SIZE}" fill="{canvas}"/>')
    p.append(f'<circle cx="{C}" cy="{C}" r="372" fill="none" stroke="{c_primary}" '
             f'stroke-width="16"{ring_dash} stroke-linecap="butt"/>')
    p.append(f'<text x="{C + 4}" y="520" text-anchor="middle" font-family="{s_family}" '
             f'font-weight="{s_weight}" font-size="368" letter-spacing="-8" '
             f'fill="{c_primary}">TF</text>')
    p.append('</svg>')
    return "\n".join(p)


def wordmark(reversed=False, bg=False, tagline=True):
    """Horizontal lockup: no badge ring. TIME FADES / PHOTOBOOTH + optional tagline."""
    if reversed:
        c_primary, c_sec, c_ter, canvas = PAPER, "#d9ccb8", "#a89680", "#2f2119"
    else:
        c_primary, c_sec, c_ter, canvas = INK, BR2, BR3, PAPER
    s_family, s_key, s_weight = SERIF["playfair"]
    W, H = 520, 200
    tf_size, tf_track = 54, 1.2
    tf_ink = lib.ink_width(s_key, "TIME FADES", tf_size, tf_track)
    pb_size = 20
    pb_track = lib.solve_letter_spacing_ink(s_key, "PHOTOBOOTH", pb_size, tf_ink)
    cx = W / 2
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">']
    if bg:
        p.append(f'<rect width="{W}" height="{H}" fill="{canvas}"/>')
    p.append(f'<text x="{cx + lib.ink_center_shift(tf_track):.3f}" y="96" text-anchor="middle" '
             f'font-family="{s_family}" font-weight="{s_weight}" '
             f'font-size="{tf_size}" letter-spacing="{tf_track}" fill="{c_primary}">TIME FADES</text>')
    p.append(f'<text x="{cx + lib.ink_center_shift(pb_track):.3f}" y="128" text-anchor="middle" '
             f'font-family="{s_family}" font-weight="500" '
             f'font-size="{pb_size}" letter-spacing="{pb_track:.3f}" fill="{c_sec}">PHOTOBOOTH</text>')
    if tagline:
        p.append(f'<text x="{cx}" y="156" text-anchor="middle" font-family="{s_family}" '
                 f'font-weight="500" font-size="11" letter-spacing="2.5" fill="{c_ter}">'
                 f'REMEMBER WHEN · BEFORE TIME FADES AWAY</text>')
    p.append('</svg>')
    return "\n".join(p)


if __name__ == "__main__":
    import sys
    # SVG has no encoding declaration, so it must be UTF-8. Windows would
    # otherwise write the tagline's middot in the console codepage.
    sys.stdout.reconfigure(encoding="utf-8")
    fn = badge
    args = sys.argv[1:]
    if args and args[0] in ("badge", "mark", "wordmark"):
        fn = {"badge": badge, "mark": mark, "wordmark": wordmark}[args[0]]
        args = args[1:]
    kw = dict(a.split("=") for a in args if "=" in a)
    for k in ("reversed", "bg", "solid_ring", "tagline", "clock", "diamonds"):
        if k in kw and kw[k].lower() in ("1", "true", "yes", "0", "false", "no"):
            kw[k] = kw[k].lower() in ("1", "true", "yes")
    sys.stdout.write(fn(**kw))
