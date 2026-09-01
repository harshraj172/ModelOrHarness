"""Restyle Figure 1 (figures/interaction-flowchart.pdf): swap the typeface and
fix the font-size hierarchy to

    Model  >  level-2 ring labels  >  level-3 component cards

(the original was inverted: the outer cards were 20.25pt and the ring labels 18pt).

WHY THIS EXISTS
    The figure was redesigned by hand in Inkscape and only the exported PDF is
    checked in -- there is no .svg/.ai source. Re-exporting through Inkscape is
    not an option either: its SVG->PDF export corrupts the 16 masked icon
    images. So this patches the PDF directly -- it strips the text objects and
    redraws them, leaving every non-text object byte-untouched.

    It always runs against the ORIGINAL Nimbus Sans PDF (the constants below
    describe that layout) and refuses to run on an already-restyled file, so
    switching presets means re-running from the original, not chaining edits.

HOW THE TEXT IS ENCODED (both bake in Nimbus Sans advance widths, which is why
the layout is re-derived rather than merely restyled):
  * flat labels  - Model, LLM policy, and the 8 component cards.
  * curved level-2 labels (User / Harness / Environment) - one text object per
    glyph, each rotated onto an arc. Their arc midpoint, the designer's letter
    tracking, and the cap-height centring inside the colour band are preserved.

    python3 figures/restyle_interaction_flowchart.py orig.pdf out.pdf
    python3 figures/restyle_interaction_flowchart.py orig.pdf out.pdf --preset courier
"""

import argparse
import math
import sys

import fitz  # PyMuPDF
from fontTools.ttLib import TTFont

URW = "/usr/share/fonts/opentype/urw-base35/"
ROB = "/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/"

# Level-3 sizing is font-dependent: the cards are 126pt wide and "Third party"
# is the longest label. Roboto Regular is only 86.2pt at 18pt, but Courier is
# monospace at 600/1000 em for every glyph -> 118.8pt at 18pt, leaving just
# 3.6pt a side, so the monospace preset has to run smaller (108.9pt at 16.5pt).
PRESETS = {
    # APPLIED: proportional, everything regular weight (nothing bold).
    "roboto": {"regular": ROB + "Roboto-Regular.ttf",
               "bold": None, "keep_bold": False,
               "model": 34.5, "l2": 22.0, "l3": 18.0, "sub": 18.0},
    # same, but keeping the original bold weights
    "roboto-bold": {"regular": ROB + "Roboto-Regular.ttf",
                    "bold": ROB + "Roboto-Bold.ttf", "keep_bold": True,
                    "model": 34.5, "l2": 22.0, "l3": 18.0, "sub": 18.0},
    # monospace "coding" look, nothing bold
    "courier": {"regular": URW + "NimbusMonoPS-Regular.otf",
                "bold": None, "keep_bold": False,
                "model": 34.5, "l2": 22.0, "l3": 16.5, "sub": 16.5},
}

INK, GREY = "#1d1d1f", "#86868b"
COL = {"User": "#b0721e", "Harness": "#1f7c8c", "Environment": "#3c6fb2"}

# Helvetica-Bold / Helvetica advance widths (per 1000 em) and cap height.
# Nimbus Sans is metrically identical, so these measure the ORIGINAL layout.
HB = {" ": 278, "C": 722, "E": 667, "G": 778, "H": 722, "L": 611, "M": 833,
      "O": 778, "T": 611, "U": 722, "a": 556, "c": 556, "d": 611, "e": 556,
      "h": 611, "i": 278, "l": 278, "m": 889, "n": 611, "o": 611, "p": 611,
      "r": 389, "s": 556, "t": 333, "v": 556, "w": 778, "x": 556, "y": 556}
HR = {" ": 278, "L": 556, "M": 833, "c": 500, "i": 222, "l": 222, "o": 556,
      "p": 556, "y": 500}
OLD_CAP = 0.718

# Level-2 arcs, measured off the original PDF (circle-fit residual < 0.11 px):
#   label -> (text, radius, centre, +1 upper arc / -1 lower arc)
CURVED = {
    "User": ("User", 162.666, (393.475, 339.883), +1),
    "Harness": ("Harness", 171.590, (394.558, 338.098), -1),
    "Environment": ("Environment", 161.412, (394.230, 339.606), +1),
}
ORIG_ROT = {   # original per-glyph rotation angles (deg)
    "User": [56.798623, 61.291026, 65.262656, 68.721014],
    "Harness": [14.365, 9.841, 6.391, 2.775, -1.381, -5.389, -9.386],
    "Environment": [-79.708, -75.282, -71.215, -68.115, -65.523, -61.897,
                    -57.583, -52.397, -47.379, -43.229, -39.774],
}
# (text, original origin, original size, original weight, size key, colour)
FLAT = [("Model", (344.64761, 345.75), 34.5, "bold", "model", INK),
        ("LLM policy", (351.65, 372.75), 18.0, "normal", "sub", GREY),
        ("Owner", (512.22079, 114.975), 20.25, "bold", "l3", INK),
        ("Grader", (624.80, 233.40), 20.25, "bold", "l3", INK),
        ("Third party", (635.28, 425.32), 20.25, "bold", "l3", INK),
        ("Context", (506.33, 632.03), 20.25, "bold", "l3", INK),
        ("Memory", (345.03, 671.85), 20.25, "bold", "l3", INK),
        ("Tool", (206.98, 621.00), 20.25, "bold", "l3", INK),
        ("External", (59.04, 331.95), 20.25, "bold", "l3", INK),
        ("Local", (184.33, 138.30), 20.25, "bold", "l3", INK)]


def old_adv(ch, size, weight):
    return (HB if weight == "bold" else HR)[ch] / 1000 * size


def rgb(h):
    return tuple(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))


def main(src, dst, preset):
    cfg = PRESETS[preset]
    paths = {"normal": cfg["regular"],
             "bold": cfg["bold"] if cfg["keep_bold"] else cfg["regular"]}
    metrics = {}
    for w, p in paths.items():
        f = TTFont(p)
        metrics[w] = (f["head"].unitsPerEm, f.getBestCmap(), f["hmtx"],
                      f["OS/2"].sCapHeight / f["head"].unitsPerEm)

    def adv(ch, size, w):
        upem, cmap, hmtx, _ = metrics[w]
        return hmtx[cmap[ord(ch)]][0] / upem * size

    def cap(size, w):
        return metrics[w][3] * size

    doc = fitz.open(src)
    page = doc[0]
    if "NimbusSans" not in "".join(f[3] for f in page.get_fonts()):
        sys.exit("refusing to run: %s is not the original Nimbus Sans figure "
                 "(already restyled?) -- always restyle from the original" % src)

    # 1. strip every text object; keep the line art and the 16 icon images
    page.add_redact_annot(page.rect)
    page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE,
                          graphics=fitz.PDF_REDACT_LINE_ART_NONE,
                          text=fitz.PDF_REDACT_TEXT_REMOVE)

    fonts = {w: fitz.Font(fontfile=p) for w, p in paths.items()}

    def put(point, text, size, w, color, morph=None):
        tw = fitz.TextWriter(page.rect)
        tw.append(point, text, font=fonts[w], fontsize=size)
        tw.write_text(page, color=rgb(color), morph=morph)

    # 2. flat labels, kept optically centred on their original position
    for txt, (x, y), osz, ow, key, col in FLAT:
        nsz = cfg[key]
        w = ow if cfg["keep_bold"] else "normal"
        x += (sum(old_adv(c, osz, ow) for c in txt)
              - sum(adv(c, nsz, w) for c in txt)) / 2
        y -= (OLD_CAP * osz - cap(nsz, w)) / 2
        put((x, y), txt, nsz, w, col)

    # 3. curved level-2 labels, re-laid along their arc with the new metrics
    l2 = cfg["l2"]
    w = "bold" if cfg["keep_bold"] else "normal"
    for name, (txt, R, (cx, cy), ud) in CURVED.items():
        phis = [r - 90 * ud for r in ORIG_ROT[name]]
        s = 1 if ud > 0 else -1
        gaps = [math.radians(abs(phis[i + 1] - phis[i])) * R
                - (old_adv(txt[i], 18, "bold") + old_adv(txt[i + 1], 18, "bold")) / 2
                for i in range(len(txt) - 1)]
        track = (sum(gaps) / len(gaps) / 18) if gaps else 0.0   # em

        e0 = phis[0] - s * math.degrees(old_adv(txt[0], 18, "bold") / 2 / R)
        e1 = phis[-1] + s * math.degrees(old_adv(txt[-1], 18, "bold") / 2 / R)
        mid = (e0 + e1) / 2                       # pin the arc midpoint
        Rn = R + ud * (OLD_CAP * 18 - cap(l2, w)) / 2

        advs = [adv(c, l2, w) for c in txt]
        tr = track * l2
        total = sum(advs) + tr * (len(txt) - 1)
        cur = mid - s * math.degrees(total / Rn) / 2
        for ch, a in zip(txt, advs):
            rot = cur + s * math.degrees(a / 2 / Rn) + 90 * ud
            th = math.radians(cur)
            pt = fitz.Point(cx + Rn * math.cos(th), cy + Rn * math.sin(th))
            put(pt, ch, l2, w, COL[name], morph=(pt, fitz.Matrix(-rot)))
            cur += s * math.degrees((a + tr) / Rn)

    doc.subset_fonts()
    doc.save(dst, garbage=4, deflate=True, clean=True)
    print("wrote %s (preset: %s)" % (dst, preset))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--preset", choices=sorted(PRESETS), default="roboto")
    a = ap.parse_args()
    main(a.src, a.dst, a.preset)
