"""Soft-corner post-processing for Graphviz figures.

Graphviz can route orthogonal edges but draws their bends as sharp corners
(and can't round them). This module rewrites each edge path in a Graphviz SVG
so the corners become small rounded arcs, then rasterises the rounded SVG to
PNG/PDF with Inkscape (Graphviz itself only sees the original sharp paths).

Used by build_interaction_flowchart.py and build_model_component_tree.py.
"""

import math
import re
import shutil
import subprocess
from pathlib import Path

_NUM = r"-?\d+(?:\.\d+)?"


def _anchors(d: str):
    """On-curve anchor points of a Graphviz edge path (handles M/L/C)."""
    anchors = []
    for cmd, args in re.findall(r"([MLC])([^MLCZ]*)", d):
        nums = re.findall(_NUM, args)
        pts = list(zip(nums[0::2], nums[1::2]))
        pts = [(float(x), float(y)) for x, y in pts]
        if cmd == "M":
            anchors.append(pts[0])
        elif cmd == "L":
            anchors.extend(pts)
        elif cmd == "C":
            anchors.extend(pts[2::3])  # every cubic's endpoint
    return anchors


def _round_d(d: str, radius: float) -> str:
    pts = _anchors(d)
    if len(pts) < 3:
        return d  # straight segment — no corner to soften
    out = [f"M{pts[0][0]:.2f},{pts[0][1]:.2f}"]
    for i in range(1, len(pts) - 1):
        p0, p1, p2 = pts[i - 1], pts[i], pts[i + 1]
        v0 = (p1[0] - p0[0], p1[1] - p0[1])
        v1 = (p2[0] - p1[0], p2[1] - p1[1])
        l0, l1 = math.hypot(*v0), math.hypot(*v1)
        if l0 < 1e-6 or l1 < 1e-6:
            out.append(f"L{p1[0]:.2f},{p1[1]:.2f}")
            continue
        r = min(radius, l0 / 2, l1 / 2)
        a = (p1[0] - v0[0] / l0 * r, p1[1] - v0[1] / l0 * r)
        b = (p1[0] + v1[0] / l1 * r, p1[1] + v1[1] / l1 * r)
        out.append(f"L{a[0]:.2f},{a[1]:.2f}")
        out.append(f"Q{p1[0]:.2f},{p1[1]:.2f} {b[0]:.2f},{b[1]:.2f}")
    out.append(f"L{pts[-1][0]:.2f},{pts[-1][1]:.2f}")
    return "".join(out)


def round_edges_svg(svg: str, radius: float = 9.0) -> str:
    """Round the corners of every edge path in a Graphviz SVG."""

    def fix_edge(m):
        return re.sub(
            r'(<path[^>]*\sd=")([^"]*)(")',
            lambda pm: pm.group(1) + _round_d(pm.group(2), radius) + pm.group(3),
            m.group(0),
            count=1,
        )

    return re.sub(
        r'<g id="edge\d+" class="edge">.*?</g>', fix_edge, svg, flags=re.DOTALL
    )


def render(
    dot_path: Path,
    stem: str,
    outdir: Path,
    engine: str,
    dpi: int = 200,
    radius: float = 9.0,
) -> None:
    """Render dot -> rounded SVG, then rasterise PNG + PDF via Inkscape.

    Falls back to plain Graphviz output (sharp corners) if Inkscape is absent.
    """
    svg = subprocess.run(
        [engine, "-Tsvg", str(dot_path)], check=True, capture_output=True, text=True
    ).stdout
    svg_path = outdir / f"{stem}.svg"
    svg_path.write_text(round_edges_svg(svg, radius))
    print(f"wrote {svg_path}  ({svg_path.stat().st_size // 1024} KB)")

    inkscape = shutil.which("inkscape")
    for fmt in ("png", "pdf"):
        out = outdir / f"{stem}.{fmt}"
        if inkscape:
            args = [
                inkscape,
                str(svg_path),
                f"--export-type={fmt}",
                f"--export-filename={out}",
            ]
            if fmt == "png":
                args.append(f"--export-dpi={dpi}")
            subprocess.run(args, check=True, capture_output=True)
        else:  # fallback: sharp corners straight from Graphviz
            args = [engine, f"-T{fmt}", str(dot_path), "-o", str(out)]
            if fmt == "png":
                args.insert(1, f"-Gdpi={dpi}")
            subprocess.run(args, check=True)
        print(f"wrote {out}  ({out.stat().st_size // 1024} KB)")
