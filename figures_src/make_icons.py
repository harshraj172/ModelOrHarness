"""Generate the monoline icon set shared by both taxonomy figures.

Each icon is authored as a single-weight (monoline) 24x24 SVG, stroked in its
family colour, then rasterised to a high-resolution PNG (Graphviz 2.43 on this
box cannot embed SVG *images*, and matplotlib places PNGs crisply via
AnnotationBbox). Icons are tinted to the family palette so they read as part of
the colour system, not as stickers — and they double as a redundant,
greyscale-safe family marker.

Run:  python3 experiments/make_icons.py
Out:  experiments/figures/icons/<name>.png   (+ .svg sources)
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from _figstyle import FAMILIES, MODEL

OUTDIR = Path(__file__).parent / "figures" / "icons"
PX = 512  # raster size — large so the icons stay sharp when scaled down

# Each entry: name -> (stroke colour, inner SVG markup on a 24x24 canvas).
# Monoline: fill="none", stroke set on the group, round caps/joins.

# The model glyph ships in two tints, so it is authored once here.
#   "model"         — periwinkle, the model's own identity colour. The hub of the
#                     component tree and of fig1 variant C.
#   "model-harness" — harness teal, for the peer/subagent card on fig1-clean's
#                     outer ring: there the glyph is one component card among
#                     Context / Memory / Tool, so it takes the family tint like
#                     every other card rather than staying the lone off-hue mark.
MODEL_GLYPH = (
    '<circle cx="12" cy="12" r="2.7"/>'
    '<circle cx="12" cy="4.3" r="1.8"/>'
    '<circle cx="5" cy="18.4" r="1.8"/>'
    '<circle cx="19" cy="18.4" r="1.8"/>'
    '<path d="M12 9.3V6.1M10.3 13.5l-3.6 3.3M13.7 13.5l3.6 3.3"/>'
)


def _icons() -> dict[str, tuple[str, str]]:
    human = FAMILIES["human"]["border"]
    harness = FAMILIES["harness"]["border"]
    env = FAMILIES["env"]["border"]
    mas = FAMILIES["mas"]["border"]
    model = MODEL["border"]

    return {
        # model — a small network hub (centre node + three satellites)
        "model": (model, MODEL_GLYPH),
        # ... the same glyph tinted as a harness component (see MODEL_GLYPH)
        "model-harness": (harness, MODEL_GLYPH),
        # owner / user — a single person
        "person": (
            human,
            '<circle cx="12" cy="8" r="3.4"/><path d="M5.5 19.5a6.5 6.5 0 0 1 13 0"/>',
        ),
        # owner (grader) — clipboard with a check
        "grader": (
            human,
            '<rect x="5.5" y="4.5" width="13" height="16" rx="2"/>'
            '<rect x="9" y="2.8" width="6" height="3.2" rx="1"/>'
            '<path d="M8.8 13.2l2.4 2.4 4.2-4.6"/>',
        ),
        # third party — two people
        "people": (
            human,
            '<circle cx="9" cy="9" r="3"/>'
            '<path d="M3.8 19.5a5.2 5.2 0 0 1 10.4 0"/>'
            '<circle cx="16.6" cy="7.6" r="2.4"/>'
            '<path d="M15 12.2a4.4 4.4 0 0 1 5.3 4.1"/>',
        ),
        # context — a document with text lines
        "document": (
            harness,
            '<path d="M7 3h6.5l4.5 4.5V21H7z"/>'
            '<path d="M13.3 3.2V7.6H17.8"/>'
            '<path d="M9.4 12h6M9.4 15h6M9.4 18h3.6"/>',
        ),
        # memory — a database cylinder
        "database": (
            harness,
            '<ellipse cx="12" cy="6" rx="6.6" ry="2.5"/>'
            '<path d="M5.4 6v12c0 1.38 2.96 2.5 6.6 2.5s6.6-1.12 6.6-2.5V6"/>'
            '<path d="M5.4 12c0 1.38 2.96 2.5 6.6 2.5s6.6-1.12 6.6-2.5"/>',
        ),
        # tool — a wrench (Lucide)
        "wrench": (
            harness,
            '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77'
            "a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91"
            'a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>',
        ),
        # external env — a cloud
        "cloud": (
            env,
            '<path d="M7.2 18h9.4a3.7 3.7 0 0 0 .5-7.37 5.2 5.2 0 0 0-9.95-1.1'
            'A4.05 4.05 0 0 0 7.2 18z"/>',
        ),
        # local env — a terminal window
        "terminal": (
            env,
            '<rect x="3.2" y="5" width="17.6" height="14" rx="2"/>'
            '<path d="M3.2 9h17.6"/>'
            '<path d="M7 12.5l2.3 2.2-2.3 2.2M11.6 16.7h4"/>',
        ),
        # peer agents — two linked nodes, bidirectional
        "peers": (
            mas,
            '<circle cx="6.6" cy="12" r="2.7"/>'
            '<circle cx="17.4" cy="12" r="2.7"/>'
            '<path d="M9.3 12h5.4M10.6 10.4 9 12l1.6 1.6M13.4 10.4 15 12l-1.6 1.6"/>',
        ),
        # lead -> subagents — an org fork (one over two)
        "fork": (
            mas,
            '<circle cx="12" cy="5" r="2.4"/>'
            '<circle cx="6" cy="18.5" r="2.4"/>'
            '<circle cx="18" cy="18.5" r="2.4"/>'
            '<path d="M12 7.4v3.6M6 16.1v-2.1h12v2.1M12 11v3"/>',
        ),
    }


def svg_doc(stroke: str, inner: str) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" '
        'viewBox="0 0 24 24" fill="none" '
        f'stroke="{stroke}" stroke-width="1.7" stroke-linecap="round" '
        'stroke-linejoin="round">'
        f"{inner}</svg>"
    )


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    inkscape = shutil.which("inkscape")
    if inkscape is None:
        raise SystemExit("Inkscape not found on PATH (needed to rasterise icons).")
    for name, (stroke, inner) in _icons().items():
        svg_path = OUTDIR / f"{name}.svg"
        png_path = OUTDIR / f"{name}.png"
        svg_path.write_text(svg_doc(stroke, inner))
        subprocess.run(
            [
                inkscape,
                str(svg_path),
                "--export-type=png",
                f"--export-filename={png_path}",
                f"--export-width={PX}",
                f"--export-height={PX}",
            ],
            check=True,
            capture_output=True,
        )
    print(f"wrote {len(_icons())} icons to {OUTDIR}")


if __name__ == "__main__":
    main()
