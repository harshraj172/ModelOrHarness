"""Figure 1 — the *clean* radial interaction map, as a reproducible script.

WHY THIS EXISTS
    The version of Figure 1 that ships in the paper (light-grey-bordered white
    cards, pastel family bands, Roboto text) was drawn by hand in Inkscape. Only
    the exported PDF was ever checked in -- there is no .svg/.ai source, and the
    only tooling around it was figures/restyle_interaction_flowchart.py in the
    paper repo, which merely re-types the text of that fixed PDF in Roboto and
    cannot change the artwork. So the design could not be edited or extended.

    This script rebuilds that design from measurements taken off the Inkscape
    PDF (commit 1e92d7c of the paper repo, the NimbusSans original), so the
    figure is now generated rather than hand-drawn. Adding or moving a family or
    a component is a data edit in FAMILIES / COMPONENTS below.

    The multi-agent edge attaches to the Harness family: a model can only reach
    another model through its own harness, so the far endpoint (a Model card
    captioned with the role it plays) is a fourth harness component rather than
    a family of its own. Every component sits SLOT = 360/9 degrees apart, so the
    spokes are equidistant everywhere on the ring, at the cost of the three
    family bands no longer spanning equal arcs (Harness, with four components,
    is wider than User or Environment).

    Do not confuse this with build_interaction_flowchart.py -- that is the older,
    unrelated lineage (Lato, saturated borders, coloured spokes).

MEASURED GEOMETRY (points, from the Inkscape PDF; hub centre was (394.5, 339.8)
on a 789x721.5 page). Everything here is expressed relative to the hub centre,
in a y-up frame:
    hub circle           r = 111
    family bands         r = 135 .. 196.5
    spokes               r = 198 .. 246
    component cards      126 x 97.5, corner radius 13.5 (centre radius is solved
                         per card by card_radius(); the original fixed it at 298.5)
    icons                40.5 square, 16.55 above the card centre
    card labels          27.3 below the card centre
    drop shadows         same shape, black at 5%, offset 2.25 downward

Run:  uv run --with matplotlib --with fonttools python experiments/build_fig1_clean.py
Out:  experiments/figures/fig1-clean.{pdf,svg,png}
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from matplotlib.patches import Circle, FancyBboxPatch, Wedge
from fontTools.ttLib import TTFont

HERE = Path(__file__).parent
OUTDIR = HERE / "figures"
ICONS = OUTDIR / "icons"
STEM = "fig1-clean"

ROBOTO = "/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Regular.ttf"

# ── measured palette ────────────────────────────────────────────────────────
INK = "#1d1d1f"  # card labels
GREY = "#86868b"  # role caption
# The hub wordmark is coded with the Harness hue rather than neutral ink: the
# harness is what wraps the focal model, so the two read as one agent. Declared
# once here and reused by the Harness entry in FAMILIES so they cannot drift.
HARNESS_INK = "#1f7c8c"
CARD_EDGE = "#d8d8dc"  # cards + hub circle  (0.847 grey in the PDF)
BAND_EDGE = "#e4e4e8"  # family bands        (0.894)
SPOKE = "#c3c3c8"  # spokes              (0.765)

# ── measured geometry (points, relative to the hub centre, y-up) ────────────
R_HUB = 111.0
R_BAND_IN, R_BAND_OUT = 135.0, 196.5
R_SPOKE_IN, R_SPOKE_OUT = 198.0, 246.0
CARD_W, CARD_H, CARD_R = 126.0, 97.5, 13.5
ICON_SIZE = 40.5
ICON_DY = 16.55  # icon centre above the card centre
LABEL_DY = -27.3  # card label centre below the card centre
SHADOW_DY = -2.25  # shadows fall downward
SHADOW_ALPHA = 0.05

LW_CARD, LW_BAND, LW_SPOKE = 1.2, 0.9, 1.5
# FS_CARD is the outer-ring label size. The Inkscape original set it at 18pt,
# which reads heavy against the band labels once the paper reduces the figure by
# ~0.5x at 0.78\textwidth; 15.5pt (-> ~7.7pt on the page) sits better. FS_BAND is
# one point down from its original 22pt, staying well above FS_CARD so the inner
# ring still reads as the more prominent label.
FS_MODEL, FS_BAND, FS_CARD = 34.5, 21.0, 15.5
FS_ROLE = 12.0  # role caption: ~0.8x the card label, 84pt wide in a 126pt card
# The original hub carried a "LLM policy" sublabel and lifted the wordmark 6.3pt
# to balance against it. The taxonomy is modality-agnostic, so the sublabel is
# gone and the wordmark -- now the hub's only text -- sits dead centre.
MODEL_DY = 0.0
ROLE_DY = -48.0  # role caption, below the card label
ROLE_EXTRA = 15.0  # extra card height to hold it (the card grows downward only)

# Letter tracking of the band labels, solved off the shipped Roboto figure.
# The original spaced all three uniformly: this value reproduces the measured
# User / Harness / Environment sweeps to within 0.15 degrees, so a new band can
# be lettered consistently instead of guessed.
BAND_TRACK = 1.404
R_BAND_BASE = 160.37  # baseline radius of an upper-arc band label
R_BAND_BASE_LOW = 171.27  # ... and of a lower-arc one

BAND_GAP = 2.6  # degrees of white between family bands, so groups read crisply

# ── data: three families; a model reaches another model only through its own
# harness, so the multi-agent edge attaches to the Harness family rather than
# getting a family of its own ─────────────────────────────────────────────
# (key, name, fill, label colour)
FAMILIES = [
    ("human", "User", "#f8f0e3", "#b0721e"),
    ("harness", "Harness", "#e7f2f4", HARNESS_INK),
    ("env", "Environment", "#e8eefa", "#3c6fb2"),
]

# (label, family key, icon name, optional role caption). Order is clockwise
# from the top, contiguous by family, so a single global angular step keeps
# every spoke equidistant regardless of how many components a family holds.
COMPONENTS = [
    ("Owner", "human", "person", None),
    ("Grader", "human", "grader", None),
    ("Third party", "human", "people", None),
    ("Context", "harness", "document", None),
    ("Memory", "harness", "database", None),
    ("Tool", "harness", "wrench", None),
    # The far endpoint of a multi-agent edge is itself a model, reachable only
    # through the focal model's own harness -- so it is a harness component,
    # naming the role it plays and taking the harness tint of the model glyph
    # ("model-harness", not the periwinkle "model" the other figures hub with).
    ("Model", "harness", "model-harness", "peer / subagent"),
    ("External", "env", "cloud", None),
    ("Local", "env", "terminal", None),
]

N = len(COMPONENTS)
SLOT = 360.0 / N  # equal angular step for every component, any family


def slot_angle(i: int) -> float:
    """Standard-math degrees (CCW from +x) for component slot i, clockwise from top."""
    return 90.0 - (i + 0.5) * SLOT


def comp_angle(cid: str) -> float:
    return slot_angle(next(i for i, c in enumerate(COMPONENTS) if c[0] == cid))


def family_arc(key: str, pad: bool = False) -> tuple[float, float]:
    """(lo, hi) degrees spanning a family's contiguous slots."""
    idx = [i for i, c in enumerate(COMPONENTS) if c[1] == key]
    hi = 90.0 - idx[0] * SLOT
    lo = 90.0 - (idx[-1] + 1) * SLOT
    return (lo + BAND_GAP, hi - BAND_GAP) if pad else (lo, hi)


def band_baseline(mid_deg: float) -> float:
    """Which measured label radius applies, by which half of the ring this is."""
    return R_BAND_BASE if math.sin(math.radians(mid_deg)) >= 0 else R_BAND_BASE_LOW


def _entry_r(ang: float, card_r: float, h: float) -> float:
    """Radius at which a ray from the hub first enters a component card."""
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    cx, cy = card_r * ca, card_r * sa
    top = cy + CARD_H / 2  # cards with a caption grow downward only
    x0, x1, y0, y1 = cx - CARD_W / 2, cx + CARD_W / 2, top - h, top
    hits = []
    if ca:
        hits += [xe / ca for xe in (x0, x1) if xe / ca > 0 and y0 <= xe / ca * sa <= y1]
    if sa:
        hits += [ye / sa for ye in (y0, y1) if ye / sa > 0 and x0 <= ye / sa * ca <= x1]
    return min(hits) if hits else math.nan


def card_radius(ang: float, h: float) -> float:
    """Centre radius that puts this card's inner edge exactly at R_SPOKE_OUT.

    A card is an axis-aligned rectangle, so a spoke meets a diagonal card
    corner-on and a top/bottom card edge-on. Holding every card centre at one
    radius therefore leaves the *visible* spokes ranging over 1.8x, and some
    falling short of their card altogether -- a flaw inherited from the
    hand-drawn original. Solving each card's radius instead makes every spoke
    exactly R_SPOKE_OUT - R_SPOKE_IN long and flush against its card, at the cost
    of the card centres no longer sharing a circle (they span ~13%).
    """
    lo, hi = R_SPOKE_OUT, 3 * R_SPOKE_OUT
    for _ in range(80):
        mid = (lo + hi) / 2
        e = _entry_r(ang, mid, h)
        if math.isnan(e) or e < R_SPOKE_OUT:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def _metrics(text: str, size: float) -> tuple[list[float], float]:
    """Roboto Regular per-glyph advance widths and cap height, in points."""
    f = TTFont(ROBOTO)
    upem, cmap, hmtx = f["head"].unitsPerEm, f.getBestCmap(), f["hmtx"]
    advs = [hmtx[cmap[ord(c)]][0] / upem * size for c in text]
    return advs, f["OS/2"].sCapHeight / upem * size


def curved_label(ax, text, color, size, baseline_r, mid_deg, track=BAND_TRACK):
    """Lay TEXT along an arc at ``baseline_r``, centred on ``mid_deg``.

    Spacing is driven by real Roboto advance widths plus a uniform ``track``,
    which is how the hand-drawn original was lettered -- so any word, including
    one the original never contained, comes out consistently spaced. Letters are
    rotated individually so the word follows the ring and still reads
    left-to-right on the lower half.
    """
    advs, cap = _metrics(text, size)
    n = len(text)
    # origin-to-origin distance is (advance + tracking); the last glyph's own
    # advance falls outside the first-to-last sweep
    arc = sum(advs[:-1]) + track * (n - 1)

    upper = math.sin(math.radians(mid_deg)) >= 0
    s = -1 if upper else 1  # an upper arc runs clockwise (decreasing angle)
    # glyphs grow away from the baseline: outward on the upper arc, inward below
    r = baseline_r + (cap / 2 if upper else -cap / 2)
    total = math.degrees(arc / r)
    cur = mid_deg - s * total / 2  # first glyph's origin
    for ch, a in zip(text, advs):
        theta = cur + s * math.degrees(a / 2 / r)  # origin -> glyph centre
        rad = math.radians(theta)
        ax.text(
            r * math.cos(rad),
            r * math.sin(rad),
            ch,
            ha="center",
            va="center",
            rotation=theta - 90 if upper else theta + 90,
            rotation_mode="anchor",
            fontsize=size,
            color=color,
            zorder=5,
        )
        cur += s * math.degrees((a + track) / r)


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    fm.fontManager.addfont(ROBOTO)
    plt.rcParams.update(
        {"font.family": "Roboto", "svg.fonttype": "none", "pdf.fonttype": 42}
    )

    # keep the original page proportions; bbox_inches="tight" crops the margin
    LIM = 420.0
    fig, ax = plt.subplots(figsize=(789 / 72, 721.5 / 72))
    ax.set_aspect("equal")
    ax.set_xlim(-LIM, LIM)
    ax.set_ylim(-LIM, LIM)
    ax.axis("off")

    dupi = (LIM * 2) / (789 / 72)  # data units per inch, for icon scaling
    icon_zoom = (ICON_SIZE / dupi) * 100 / 512  # icon PNGs are 512 px

    def rounded(xy, w, h, **kw):
        return FancyBboxPatch(
            xy,
            w,
            h,
            boxstyle=f"round,pad=0,rounding_size={CARD_R}",
            **kw,
        )

    # every component's angle comes from its fixed slot, then its centre radius
    # from the card size, so every spoke ends flush on it despite unequal bands
    placed = []
    for label, key, icon, role in COMPONENTS:
        ang = comp_angle(label)
        h = CARD_H + (ROLE_EXTRA if role else 0.0)
        placed.append((label, key, icon, role, ang, card_radius(ang, h), h))

    # ── family bands ──
    for key, name, fill, col in FAMILIES:
        lo, hi = family_arc(key, pad=True)
        ax.add_patch(
            Wedge(
                (0, 0),
                R_BAND_OUT,
                lo,
                hi,
                width=R_BAND_OUT - R_BAND_IN,
                facecolor=fill,
                edgecolor=BAND_EDGE,
                lw=LW_BAND,
                zorder=1,
                joinstyle="round",
            )
        )
        mid = sum(family_arc(key)) / 2
        curved_label(ax, name, col, FS_BAND, band_baseline(mid), mid)

    # ── spokes ──
    for label, key, icon, role, ang, card_r, h in placed:
        a = math.radians(ang)
        ax.plot(
            [R_SPOKE_IN * math.cos(a), R_SPOKE_OUT * math.cos(a)],
            [R_SPOKE_IN * math.sin(a), R_SPOKE_OUT * math.sin(a)],
            color=SPOKE,
            lw=LW_SPOKE,
            solid_capstyle="butt",
            zorder=2,
        )

    # ── hub: shadow, circle, wordmark ──
    ax.add_patch(
        Circle(
            (0, SHADOW_DY),
            R_HUB,
            facecolor="black",
            ec="none",
            alpha=SHADOW_ALPHA,
            zorder=2,
        )
    )
    ax.add_patch(
        Circle(
            (0, 0), R_HUB, facecolor="white", edgecolor=CARD_EDGE, lw=LW_CARD, zorder=3
        )
    )
    ax.text(
        0,
        MODEL_DY,
        "Model",
        ha="center",
        va="center",
        fontsize=FS_MODEL,
        color=HARNESS_INK,
        zorder=6,
    )

    # ── component cards ──
    for label, key, icon, role, ang, card_r, h in placed:
        a = math.radians(ang)
        cx, cy = card_r * math.cos(a), card_r * math.sin(a)
        # a card carrying a role caption grows downward only, so its top edge,
        # icon and label stay aligned with every other card
        x0, y0 = cx - CARD_W / 2, cy + CARD_H / 2 - h
        ax.add_patch(
            rounded(
                (x0, y0 + SHADOW_DY),
                CARD_W,
                h,
                facecolor="black",
                ec="none",
                alpha=SHADOW_ALPHA,
                zorder=3,
            )
        )
        ax.add_patch(
            rounded(
                (x0, y0),
                CARD_W,
                h,
                facecolor="white",
                edgecolor=CARD_EDGE,
                lw=LW_CARD,
                zorder=4,
            )
        )
        ax.add_artist(
            AnnotationBbox(
                OffsetImage(plt.imread(ICONS / f"{icon}.png"), zoom=icon_zoom),
                (cx, cy + ICON_DY),
                frameon=False,
                zorder=6,
            )
        )
        ax.text(
            cx,
            cy + LABEL_DY,
            label,
            ha="center",
            va="center",
            fontsize=FS_CARD,
            color=INK,
            zorder=6,
        )
        if role:
            ax.text(
                cx,
                cy + ROLE_DY,
                role,
                ha="center",
                va="center",
                fontsize=FS_ROLE,
                color=GREY,
                zorder=6,
            )

    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    for ext in ("pdf", "svg", "png"):
        fig.savefig(
            OUTDIR / f"{STEM}.{ext}",
            bbox_inches="tight",
            dpi=300 if ext == "png" else None,
        )
        print(f"wrote {OUTDIR / f'{STEM}.{ext}'}")
    plt.close(fig)


if __name__ == "__main__":
    main()
