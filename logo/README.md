# Time Fades Photobooth — Logo System

Vintage postmark / rubber-stamp badge with a clock at its centre. The clock is the
concept, not decoration — it carries the company name.

## Build

```
bash logo/build.sh        # generate -> outline -> svgo -> verify -> export -> assets/
```

That one command rebuilds everything and publishes to `assets/` and the site root.
Nothing else needs running by hand.

## Masters (editable text — edit these)

| File | Use |
|---|---|
| `logo-full.svg` | Primary badge, dark ink on transparent. |
| `logo-reversed.svg` | Cream on dark espresso fill — dark backgrounds & merch. |
| `logo-mark.svg` | TF monogram in the dashed ring — nav and icon use (≥~32px). |
| `logo-mark-solid.svg` | TF in a solid ring — favicons ≤48px (dashes vanish that small). |
| `logo-mark-brass.svg` | Brass `#c69a4c` monogram, for dark bands. |
| `logo-wordmark.svg` | Horizontal lockup, no ring — email signatures, wide spaces. |

`outlined/` holds the same files with all text converted to vector paths (fonttools),
so they render on machines without the fonts. **The outlined files are what ships** —
`assets/` and the favicons are built from them.

## Design system

- **Type:** Playfair Display throughout — 700 for the arcs, `TIME FADES` and the
  monogram; 500 for `PHOTOBOOTH` and the tagline. (This replaced an earlier
  Cormorant Garamond + Oswald pairing.)
- **Ink:** one colour, `#2b211c`. A rubber stamp is struck in a single ink, so
  hierarchy comes from weight and scale, never tint. The reversed variant is
  `#f0ebe1` on `#2f2119`.
- **Both arcs share one font-size and one letter-spacing** (55 / 3.3). They therefore
  subtend *different angles* — ~101° top, ~134° bottom, because the bottom string is
  47% longer. That is the point: matching the type is what makes them look like one
  system, and equalising the spans instead would require two different trackings.
- **The bottom arc reads upright**, left-to-right, not inverted seal-style.
- Both arcs occupy the identical radial band (310–353): the top baseline is the band's
  inner edge with caps growing outward, the bottom baseline is its outer edge with caps
  growing inward.

### Geometry (viewBox `0 0 800 800`, centre 400,400)

| Radius | Content |
|---|---|
| 375 | dashed outer ring, 56 dashes sized to tile the circle exactly |
| 310–353 | arced text band |
| 330 | diamond accents, in the 3/9 o'clock gap between the two arcs |
| 210 | inner "clock face" circle |
| 145 / 105 | minute / hour hand (69% / 50% of the inner radius) |

All of it is named constants at the top of `generate.py` — hand angles, radii, text
sizes and colours are meant to be tweaked there.

### Why `TIME` and `FADES` are two separate text runs

The hands rise from a pivot at the centre of the wordmark, so they have to pass
*between* the two words without touching a letter. `min_word_gap()` derives the
narrowest safe gap from the hand angles and cap height, and the wordmark solve
honours it. Set them as one string with a normal space and the hands clip the
adjacent letterforms.

## Regenerating by hand

Tooling: `resvg-js-cli` + `svgo` (npm, in `node_modules`), `fonttools` + `Pillow`
(pip), fonts in `fonts/`.

```
python logo/generate.py badge clock=true diamonds=true > logo/logo-full.svg
python logo/outline.py logo/logo-full.svg logo/outlined/logo-full.svg
python logo/verify.py                             # outlined still matches master?
bash   logo/render.sh <in.svg> <out.png> <width>   # preview any SVG
```

`export/` (generated, not hand-edited) contains PNGs at 2400/1200/600 for
full/reversed/wordmark, favicons 16/32/48/180 + `favicon.ico`, `social/avatar-1000.png`
and `print/logo-full-300dpi.png`.

## Do not reorder the pipeline

Outlining must run **before** svgo. svgo rewrites arc paths from absolute to relative
form (`A 78,78 0 0 1 178,100` → `a78 78 0 0 1 156 0`). An outliner that reads the
relative endpoint as absolute computes a plausible-but-wrong circle centre and flings
the arced text off-canvas — silently, with no error. That shipped once.

Two guards now prevent a repeat:
- `generate.py` stamps `data-cx/cy/r/a0/sweep` on each arc and `outline.py` reads
  those instead of parsing `d`, so svgo's rewriting cannot mislead it.
- `verify.py` renders each master and its outlined twin, blurs both to collapse
  anti-aliasing noise, and fails the build if they differ. `build.sh` will not export
  or publish unless it passes.
