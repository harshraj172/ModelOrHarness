"""Shared design tokens for the two taxonomy figures.

Both figures (the radial "wheel", build_interaction_flowchart.py, and the
component/failure-mode tree, build_model_component_tree.py) import this module
so the pair reads as one designed set: one font, one palette, one colour
*language*.

Colour language (consistent across both figures)
------------------------------------------------
* periwinkle  = **the model**            — hub, model node, and "model fault".
* family hues = **family identity**      — User (ochre), Harness (teal),
                                            Environment (indigo), Multi-agent (plum).
* amber       = **non-model fault**       — only where a fault side is shown
                                            (the tree's leaf cards), always paired
                                            with a ▲ glyph so it survives greyscale
                                            and colour-vision deficiency.

The fault encoding is the paper's load-bearing signal, so it is *redundantly*
coded: colour **and** a glyph (● model · ▲ other), never colour alone.
"""

from __future__ import annotations

FONT = "Lato"  # available to both matplotlib and fontconfig (Graphviz/Inkscape)

# ── neutrals ──────────────────────────────────────────────────────────────
INK = "#1f2329"  # near-black for primary text
CHARCOAL = "#343a40"
MUTED = "#8a9099"  # tertiary / sublabels
HAIRLINE = "#e6e8ee"
PAPER = "#ffffff"
CANVAS = "#ffffff"

# ── the model (periwinkle) ──────────────────────────────────────────────────
MODEL = {
    "fill": "#e8eaff",
    "halo": "#dfe2fb",
    "border": "#5c5fd6",
    "deep": "#4a4dc4",
    "ink": "#3a3da8",
}

# ── families: identity hue (border), a mid tone (spoke/rail), a wash (fill) ──
# Chosen for hue *and* luminance separation (greyscale- and CVD-friendlier than
# the previous near-isoluminant pastels).
FAMILIES = {
    "human": {"border": "#b0792f", "mid": "#cf9d4e", "fill": "#f7edda", "name": "User"},
    "harness": {
        "border": "#2f8093",
        "mid": "#5aa6ba",
        "fill": "#e2eff3",
        "name": "Harness",
    },
    "env": {
        "border": "#3c5a98",
        "mid": "#7088c6",
        "fill": "#e7ecf8",
        "name": "Environment",
    },
    "mas": {
        "border": "#8a5286",
        "mid": "#b181ac",
        "fill": "#f3e8f1",
        "name": "Multi-agent",
    },
}

# ── fault encoding (tree leaves) ────────────────────────────────────────────
FAULT = {
    "model": {"spine": "#5c5fd6", "row": "#eeefff", "ink": "#3a3da8", "glyph": "●"},
    "other": {"spine": "#e07b2e", "row": "#fcefde", "ink": "#9a5a1e", "glyph": "▲"},
}


def family_of(group: str) -> dict:
    """Map a component 'group' key to its family token dict."""
    return FAMILIES.get(group, FAMILIES["harness"])
