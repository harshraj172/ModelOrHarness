# figures_src -- generators for the paper's Figure 1 and Figure 2

Copied 2026-09-02 from the original working tree (`harbor/experiments/`) so
this repo can regenerate the two headline figures. Everything else in the
paper (Tables 1-3, Fig 3) regenerates from `plot/` -- see REPRODUCE.md.

| paper artifact | generator | output | filename in the paper repo |
|---|---|---|---|
| Figure 1 (fig:wheel) | `build_fig1_clean.py` | `figures/fig1-clean.{pdf,svg,png}` | `figures/interaction-flowchart.pdf` (renamed), cropped to `interaction-flowchart-crop.pdf` |
| Figure 2 (fig:tree) | `build_model_component_tree_tikz.py` | `out/model-component-tree.tex` | `figures/model-component-tree.tex` (`\input` into the paper) |
| Figure 2, raster twin | `build_model_component_tree.py` | `figures/model-component-tree.{png,svg,pdf}` | not used by the paper |

Support files: `_figstyle.py` (palette), `figures/icons/` (26 provider/tool
icons -- a hard input for both figures), `make_icons.py` (regenerates the
icons; needs network), `_svg_round.py`, `restyle_interaction_flowchart.py`
(post-processing history of Figure 1 -- see its docstring).

## Reproducibility status (verified 2026-09-02)

- **Figure 2: exact.** `build_model_component_tree_tikz.py` regenerates the
  paper's `model-component-tree.tex` BYTE-IDENTICALLY.
- **Figure 1: environment-sensitive.** The paper's PDF is byte-identical to
  the stored generator output (`reference/fig1-clean.pdf`, kept here as the
  authoritative asset), but a fresh render on a different
  matplotlib/font stack produces visually-equivalent, byte-different output.
  Compare visually against `reference/` if you re-render.
- Toolchain: matplotlib for Fig 1; Graphviz `dot` + Inkscape only for the
  raster Fig 2 twin; a LaTeX install to compile the TikZ Fig 2.
- `build_model_component_tree_tikz.py`'s output dir was a hardcoded absolute
  path into the LaTeX repo; it now writes to `out/` here.
