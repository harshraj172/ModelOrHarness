"""Figure 2 — Model-centred component / failure-mode tree.

A left-to-right hierarchy rooted at the Model:
    L0  Model
    L1  family — User · Harness · Environment · Multi-agent
    L2  the component on each interaction edge (family-tinted, with an icon)
    L3  the enumerated failure modes on that component, as a clean card:
        a saturated left **spine** + a ●/▲ glyph + a faint tint encode which
        side is at fault — triple-coded so it survives greyscale and CVD.

Colour language is shared with Figure 1 (see _figstyle.py):
  * periwinkle  = the model (root, and "model fault" spine);
  * family hues = family identity (the L2 component tints);
  * amber + ▲   = non-model fault.
Family identity (hue) and fault (spine/glyph) are therefore two *separate*
visual systems that never collide.

Repeated prefixes ("Context Following Failure — …", "Memory Write Failure — …")
are factored into a faint group sub-header so the reader scans the
*distinguishing* suffix, not the same words seven times.

Multi-agent sits in the component column but has no edge to the model: a
from-the-start multi-agent system is not under any single model's tree.

Renders with Graphviz `dot`, the SVG corner-rounding post-process, then
Inkscape -> PDF/PNG.

Run:  python3 experiments/build_model_component_tree.py
Out:  experiments/figures/model-component-tree.{dot,png,svg,pdf}
"""

import html
import shutil
from pathlib import Path

import _figstyle as S
from _svg_round import render

HERE = Path(__file__).parent
OUTDIR = HERE / "figures"
ICONS = OUTDIR / "icons"
STEM = "model-component-tree"

# Uniform sizing per level.
FAMILY_W, FAMILY_H = 1.9, 0.66
COMP_W, COMP_H = 2.25, 0.86
CELL_W = 330  # leaf label column width (points)

# A leaf item is either a group sub-header ("GROUP", "Prefix") or a row
# (label, fault_side). Numbering runs continuously over the rows; under a group
# the full failure name is <Prefix> — <label>.
# component-id -> (header label, family-group, icon, [items])
COMPONENTS = [
    (
        "Owner",
        "Owner",
        "human",
        "person",
        [
            ("Over-initiative", "model"),
            ("Under-initiative", "model"),
            ("Satisficing", "model"),
            ("Instruction-Following Failure", "model"),
            ("Reasoning Failure", "model"),
            ("Specification Gaming", "model"),
            ("Unauthorized Irreversible Action", "model"),
            ("Sycophancy", "model"),
            ("Domain Knowledge Deficit", "model"),
            ("Value Misalignment", "model"),
            ("Instruction–Grader Mismatch", "owner"),
        ],
    ),
    (
        "Grader",
        "Grader",
        "human",
        "grader",
        [
            ("Specification Gaming", "model"),
            ("Evaluation Awareness", "model"),
        ],
    ),
    (
        "ThirdParty",
        "Third party",
        "human",
        "people",
        [
            ("Indirect Prompt Injection", "model"),
            ("Contextual Sycophancy", "model"),
        ],
    ),
    (
        "Context",
        "Context",
        "harness",
        "document",
        [
            ("GROUP", "Context Following Failure"),
            ("State Tracking Failure", "model"),
            ("Goal Drift", "model"),
            ("Context Rationale Erosion", "context"),
        ],
    ),
    (
        "Memory",
        "Memory",
        "harness",
        "database",
        [
            ("GROUP", "Memory Write Failure"),
            ("Missed Write", "model"),
            ("State Staleness", "model"),
            ("Overgeneralization", "model"),
            ("Memory Rationale Erosion", "model"),
            ("Pollution", "model"),
            ("Redundancy", "model"),
            ("GROUP", "Memory Read Failure"),
            ("Missed Read", "model"),
            ("Memory Following Failure", "model"),
        ],
    ),
    (
        "Tool",
        "Tool",
        "harness",
        "wrench",
        [
            ("Incorrect Tool Selection", "model"),
            ("Tool Hallucination", "model"),
            ("Tool Feedback Neglect", "model"),
            ("Tool Recovery Failure", "model"),
            ("Malformed Arguments", "model"),
            ("Suboptimal Arguments", "model"),
            ("Mistranslation", "tool"),
        ],
    ),
    (
        "EnvExt",
        "External",
        "env",
        "cloud",
        [
            ("Recovery Failure", "model"),
            ("Service Failure", "env"),
            ("Stale State Delivery", "env"),
        ],
    ),
    (
        "EnvLocal",
        "Local",
        "env",
        "terminal",
        [
            ("Observation Failure", "model"),
        ],
    ),
    (
        "Peer",
        "Peer",
        "mas",
        "peers",
        [
            ("Delegation Failure", "agent"),
            ("Communication Failure", "agent"),
        ],
    ),
    (
        "Subagent",
        "Lead–subagent",
        "mas",
        "fork",
        [
            ("Delegation Failure", "lead-agent"),
            ("Communication Failure", "lead-agent"),
            ("Communication Failure", "subagent"),
        ],
    ),
]

# L1 — families. (fid, label, group-key, [component ids])
FAMILIES = [
    ("Human", "User", "human", ["Owner", "Grader", "ThirdParty"]),
    ("Harness", "Harness", "harness", ["Context", "Memory", "Tool"]),
    ("Environment", "Environment", "env", ["EnvExt", "EnvLocal"]),
    ("MultiAgent", "Multi-agent", "mas", ["Peer", "Subagent"]),
]

# Verified literature reference per failure mode, collected from the Failure
# Families section (§4 / sec:families) of main.tex and confirmed by reading each
# cited paper. Keyed by (component-id, mode-label, fault-side); the value is a
# short source label rendered inline (muted) after the mode name. Modes with no
# §4 literature citation are intentionally left unlabeled.
CITES: dict[tuple[str, str, str], str] = {
    ("Owner", "Over-initiative", "model"): "HiL-Bench",
    ("Owner", "Under-initiative", "model"): "XSTest",
    ("Owner", "Satisficing", "model"): "Anthropic '26",
    ("Owner", "Instruction-Following Failure", "model"): "IFEval",
    ("Owner", "Specification Gaming", "model"): "Krakovna '20",
    ("Owner", "Unauthorized Irreversible Action", "model"): "ToolEmu",
    ("Owner", "Sycophancy", "model"): "Sharma '23",
    ("Grader", "Specification Gaming", "model"): "Skalse '22",
    ("Grader", "Evaluation Awareness", "model"): "Needham '25",
    ("ThirdParty", "Indirect Prompt Injection", "model"): "Greshake '23",
    ("Context", "Goal Drift", "model"): "Arike '25",
    ("Tool", "Tool Hallucination", "model"): "Gorilla",
    ("Peer", "Communication Failure", "agent"): "MAST",
}

# Family-level citation rendered on a group sub-header (keyed by component-id +
# group name): the memory family is cited as a whole in §4.
GROUP_CITES: dict[tuple[str, str], str] = {
    ("Memory", "Memory Write Failure"): "MemGPT; Zhang '24",
}


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def icon_path(name: str) -> str:
    return str((ICONS / f"{name}.png").resolve())


# Fault sides that are an LLM policy at fault (the central model, or a peer /
# lead / sub agent — each is itself a model). Everything else (owner, context,
# tool, env) is a non-model *component* fault.
MODEL_SIDES = {"model", "agent", "subagent", "lead-agent"}


def fault_tok(side: str) -> dict:
    return S.FAULT["model"] if side in MODEL_SIDES else S.FAULT["other"]


def subtype_table(cid: str, items) -> str:
    """A leaf card: faint-hairline rows, each with a fault spine + glyph + label."""
    rows = []
    n = 0
    for kind, val in items:
        if kind == "GROUP":
            if val:  # open a group sub-header (factored-out shared prefix)
                gsrc = GROUP_CITES.get((cid, val))
                gcite = (
                    f'<FONT POINT-SIZE="8" COLOR="{S.MUTED}"><I>  {esc(gsrc)}</I></FONT>'
                    if gsrc
                    else ""
                )
                rows.append(
                    '<TR><TD COLSPAN="3" BGCOLOR="#ffffff" ALIGN="LEFT" '
                    'CELLPADDING="6">'
                    f'<FONT POINT-SIZE="10.5" COLOR="{S.CHARCOAL}"><B>{esc(val.upper())}</B></FONT>{gcite}'
                    "</TD></TR>"
                )
            continue
        n += 1
        label, side = kind, val
        t = fault_tok(side)
        src = CITES.get((cid, label, side))
        cite = (
            f'<FONT POINT-SIZE="8" COLOR="{S.MUTED}"><I>  {esc(src)}</I></FONT>'
            if src
            else ""
        )
        rows.append(
            "<TR>"
            f'<TD BGCOLOR="{t["spine"]}" WIDTH="22" ALIGN="CENTER" CELLPADDING="3">'
            f'<FONT POINT-SIZE="9.5" COLOR="#ffffff"><B>{n}</B></FONT></TD>'
            f'<TD BGCOLOR="{t["row"]}" WIDTH="16" ALIGN="CENTER" CELLPADDING="2">'
            f'<FONT POINT-SIZE="9" COLOR="{t["ink"]}">{t["glyph"]}</FONT></TD>'
            f'<TD BGCOLOR="{t["row"]}" ALIGN="LEFT" WIDTH="{CELL_W}" CELLPADDING="4">'
            f'<FONT POINT-SIZE="11" COLOR="{S.INK}">{esc(label)}</FONT>{cite}</TD>'
            "</TR>"
        )
    table = (
        '<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="1" CELLPADDING="0" '
        f'BGCOLOR="{S.HAIRLINE}">' + "".join(rows) + "</TABLE>"
    )
    return f"  {cid}_subs [shape=plaintext, label=<{table}>];"


def comp_label(label: str, icon: str) -> str:
    """Component box: icon + bold name (no redundant edge sublabel)."""
    return (
        '<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="0"><TR>'
        f'<TD FIXEDSIZE="TRUE" WIDTH="26" HEIGHT="26"><IMG SRC="{icon_path(icon)}" SCALE="TRUE"/></TD>'
        '<TD WIDTH="8"></TD>'
        f'<TD ALIGN="LEFT"><FONT POINT-SIZE="13" COLOR="{S.INK}"><B>{esc(label)}</B></FONT></TD>'
        "</TR></TABLE>>"
    )


def legend() -> str:
    fam_cells = "".join(
        f'<TD BGCOLOR="{S.FAMILIES[g]["fill"]}" BORDER="1" COLOR="{S.FAMILIES[g]["border"]}">'
        f'<FONT POINT-SIZE="10"> {esc(S.FAMILIES[g]["name"])} </FONT></TD><TD WIDTH="8"></TD>'
        for g in ("human", "harness", "env", "mas")
    )
    m, o = S.FAULT["model"], S.FAULT["other"]
    return (
        '<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4"><TR>'
        f'<TD><FONT POINT-SIZE="10" COLOR="{S.CHARCOAL}"><B>Fault&nbsp;side&nbsp;&nbsp;</B></FONT></TD>'
        f'<TD BGCOLOR="{m["spine"]}"><FONT POINT-SIZE="10" COLOR="#ffffff"><B> {m["glyph"]} </B></FONT></TD>'
        f'<TD BGCOLOR="{m["row"]}"><FONT POINT-SIZE="10" COLOR="{S.INK}"> model </FONT></TD>'
        '<TD WIDTH="14"></TD>'
        f'<TD BGCOLOR="{o["spine"]}"><FONT POINT-SIZE="10" COLOR="#ffffff"><B> {o["glyph"]} </B></FONT></TD>'
        f'<TD BGCOLOR="{o["row"]}"><FONT POINT-SIZE="10" COLOR="{S.INK}"> other component </FONT></TD>'
        '<TD WIDTH="34"></TD>'
        f'<TD><FONT POINT-SIZE="10" COLOR="{S.CHARCOAL}"><B>Family&nbsp;&nbsp;</B></FONT></TD>'
        f"{fam_cells}"
        "</TR></TABLE>>"
    )


def fault_counts():
    """Tally enumerated failure modes by fault side (and the 'other' breakdown)."""
    model = other = 0
    other_by_fam: dict[str, int] = {}
    for _cid, _label, group, _icon, items in COMPONENTS:
        for kind, val in items:
            if kind == "GROUP":
                continue
            if val in MODEL_SIDES:
                model += 1
            else:
                other += 1
                other_by_fam[group] = other_by_fam.get(group, 0) + 1
    return model, other, other_by_fam


def summary_node() -> str:
    """A compact stacked-bar panel: how many failure modes are the model's
    fault vs. the other component's. The headline number for frontier labs."""
    model, other, _ = fault_counts()
    total = model + other
    BARW = 280
    mw = round(BARW * model / total)
    ow = BARW - mw
    mp = round(100 * model / total)
    op = 100 - mp
    m, o = S.FAULT["model"], S.FAULT["other"]
    return (
        '<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="2">'
        f'<TR><TD ALIGN="LEFT"><FONT POINT-SIZE="12" COLOR="{S.CHARCOAL}"><B>Where does the fault lie?</B></FONT></TD></TR>'
        f'<TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.5" COLOR="{S.MUTED}">{total} enumerated failure modes</FONT></TD></TR>'
        '<TR><TD CELLPADDING="4">'
        '<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="0"><TR>'
        f'<TD BGCOLOR="{m["spine"]}" WIDTH="{mw}" HEIGHT="24" ALIGN="CENTER">'
        f'<FONT POINT-SIZE="11" COLOR="#ffffff"><B>{m["glyph"]} {model}</B></FONT></TD>'
        f'<TD BGCOLOR="{o["spine"]}" WIDTH="{ow}" HEIGHT="24" ALIGN="CENTER">'
        f'<FONT POINT-SIZE="11" COLOR="#ffffff"><B>{o["glyph"]} {other}</B></FONT></TD>'
        "</TR></TABLE></TD></TR>"
        f'<TR><TD ALIGN="LEFT"><FONT POINT-SIZE="10" COLOR="{m["ink"]}"><B>Model&nbsp;{mp}%</B></FONT>'
        f'<FONT POINT-SIZE="10" COLOR="{S.MUTED}">&nbsp;&nbsp;vs&nbsp;&nbsp;</FONT>'
        f'<FONT POINT-SIZE="10" COLOR="{o["ink"]}"><B>other&nbsp;component&nbsp;{op}%</B></FONT></TD></TR>'
        "</TABLE>>"
    )


def build_dot() -> str:
    lines = [
        "digraph taxonomy {",
        "  rankdir=LR;",
        f'  bgcolor="{S.PAPER}";',
        "  splines=ortho;",
        "  nodesep=0.34;",
        "  ranksep=0.95;",
        '  labelloc="t";',
        f"  label={legend()};",
        f'  fontname="{S.FONT}";',
        f'  node [fontname="{S.FONT}"];',
        f'  edge [color="{S.HAIRLINE}", penwidth=1.3, arrowhead=none];',
        "",
        "  // L0 — root",
        '  Model [label=<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0"><TR>'
        f'<TD FIXEDSIZE="TRUE" WIDTH="34" HEIGHT="34"><IMG SRC="{icon_path("model")}" SCALE="TRUE"/></TD>'
        '<TD WIDTH="6"></TD>'
        f'<TD ALIGN="LEFT"><FONT POINT-SIZE="24" COLOR="{S.MODEL["ink"]}"><B>Model</B></FONT>'
        f'<BR ALIGN="LEFT"/><FONT POINT-SIZE="11" COLOR="{S.MODEL["border"]}">LLM policy</FONT></TD>'
        "</TR></TABLE>>, "
        'shape=box, style="rounded,filled", '
        f'fillcolor="{S.MODEL["fill"]}", color="{S.MODEL["deep"]}", penwidth=3.0, '
        'margin="0.30,0.26"];',
        "",
        "  // fault-side distribution panel (sits under Model in the left margin)",
        f'  Summary [shape=box, style="rounded,filled", fillcolor="#fbfbfd", '
        f'color="{S.HAIRLINE}", penwidth=1.3, margin="0.20,0.16", label={summary_node()}];',
        "",
        "  // L1 — families (white box, family-coloured border) ",
    ]
    for fid, label, group, _ in FAMILIES:
        tok = S.FAMILIES[group]
        inner = f'<FONT POINT-SIZE="15" COLOR="{S.INK}"><B>{esc(label)}</B></FONT>'
        # Multi-agent is a parallel, model-independent branch: dashed box (and
        # dashed edges below) keep it visually detached from the model-rooted tree.
        style = '"rounded,filled,dashed"' if fid == "MultiAgent" else '"rounded,filled"'
        lines.append(
            f"  {fid} [label=<{inner}>, shape=box, style={style}, "
            f'fillcolor="{S.PAPER}", color="{tok["border"]}", penwidth=2.2, '
            f"fixedsize=true, width={FAMILY_W}, height={FAMILY_H}];"
        )
    lines.append("")
    lines.append("  // L2 — components (family-tinted = identity, never fault)")
    for cid, label, group, icon, _ in COMPONENTS:
        tok = S.FAMILIES[group]
        lines.append(
            f"  {cid} [label={comp_label(label, icon)}, shape=box, "
            f'style="rounded,filled", fillcolor="{tok["fill"]}", '
            f'color="{tok["border"]}", penwidth=1.7, '
            f"fixedsize=true, width={COMP_W}, height={COMP_H}];"
        )
    lines.append("")
    lines.append("  // L3 — failure-mode cards")
    for cid, _, _, _, items in COMPONENTS:
        lines.append(subtype_table(cid, items))
    lines.append("")
    lines.append("  // component -> its card")
    for cid, *_ in COMPONENTS:
        tok = S.FAMILIES[COMPONENTS[[c[0] for c in COMPONENTS].index(cid)][2]]
        lines.append(f'  {cid} -> {cid}_subs [color="{tok["border"]}", penwidth=1.4];')
    lines.append("")
    lines.append("  // hierarchy: root -> family -> component")
    for fid, _, group, members in FAMILIES:
        tok = S.FAMILIES[group]
        # Multi-agent is a parallel, model-independent branch: no Model edge and
        # dashed connectors so it cannot be misread as rooted at the model.
        estyle = ", style=dashed" if fid == "MultiAgent" else ""
        if fid != "MultiAgent":
            lines.append(f'  Model -> {fid} [color="{S.MUTED}", penwidth=2.0];')
        for cid in members:
            lines.append(
                f'  {fid} -> {cid} [color="{tok["mid"]}", penwidth=1.6{estyle}];'
            )
    # pin the distribution panel into the Model column, just below Model
    lines.append("  { rank=same; Model; Summary; }")
    lines.append("  Model -> Summary [style=invis];")
    comp_ids = "; ".join(c[0] for c in COMPONENTS)
    lines.append(f"  {{ rank=same; {comp_ids}; }}")
    fam_ids = [fid for fid, *_ in FAMILIES]
    lines.append(f"  {{ rank=same; {'; '.join(fam_ids)}; }}")
    lines.append(f"  {' -> '.join(fam_ids)} [style=invis];")
    lines.append("}")
    return "\n".join(lines) + "\n"


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    dot_path = OUTDIR / f"{STEM}.dot"
    dot_path.write_text(build_dot())

    engine = shutil.which("dot")
    if engine is None:
        raise SystemExit("Graphviz `dot` not found on PATH.")
    render(dot_path, STEM, OUTDIR, engine, dpi=200, radius=7.0)


if __name__ == "__main__":
    main()
