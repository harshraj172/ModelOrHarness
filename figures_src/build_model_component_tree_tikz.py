"""Figure 2 — Model-centred component/failure-mode tree, emitted as native TikZ.

Mirrors build_model_component_tree.py (the Graphviz version) but emits a
LaTeX/TikZ picture so the per-mode citations are real, clickable \\citet{} in
the paper's format. Layout (model -> family -> component -> card of failure
modes) is computed here in Python, reproducing the Graphviz ranks.

Outputs:
  figures/model-component-tree.tex   (the tikzpicture; \\input into main.tex)
  figures/_mct_preview.tex           (standalone doc to compile/preview)

main.tex needs, in its preamble:
  \\usepackage{tikz}\\usetikzlibrary{shapes.geometric}
and to include it:  \\resizebox{\\textwidth}{!}{\\input{figures/model-component-tree.tex}}
"""

from pathlib import Path

HERE = Path(__file__).parent
OUTDIR = Path(__file__).resolve().parent / "out"  # was a hardcoded absolute path into the LaTeX repo; copy the output to the paper's figures/ yourself
ICONS = HERE / "figures" / "icons"

# ── palette (matches _figstyle.py) ──────────────────────────────────────────
COL = {
    "ink": "1F2329", "charcoal": "343A40", "muted": "8A9099",
    "hairline": "E6E8EE", "citegrey": "9AA0AA",
    "mfill": "E8EAFF", "mborder": "5C5FD6", "mdeep": "4A4DC4", "mink": "3A3DA8",
}
FAM = {
    "human":  {"border": "B0792F", "mid": "CF9D4E", "fill": "F7EDDA", "name": "User"},
    "harness":{"border": "2F8093", "mid": "5AA6BA", "fill": "E2EFF3", "name": "Harness"},
    "env":    {"border": "3C5A98", "mid": "7088C6", "fill": "E7ECF8", "name": "Environment"},
}
FAULT = {
    "model": {"spine": "5C5FD6", "row": "EEEFFF", "ink": "3A3DA8", "glyph": "circle"},
    "other": {"spine": "E07B2E", "row": "FCEFDE", "ink": "9A5A1E", "glyph": "tri"},
}
MODEL_SIDES = {"model", "agent", "subagent", "orchestrator"}

# ── data: components, rows, citations (citekeys from §4, verified) ───────────
# row = (label, fault_side, citekey|None); ("GROUP", name) or ("GROUP", name, citekey)
COMPONENTS = [
    ("Owner", "Owner", "human", "person", [
        ("Over-initiative", "model", "hilbench"),
        ("Under-initiative", "model", "rottger2023xstest"),
        ("Satisficing", "model", "anthropic_longrunning"),
        ("Instruction-Following Failure", "model", "zhou2023ifeval"),
        ("Reasoning Failure", "model", "mirzadeh2024gsmsymbolic"),
        ("Unauthorized Irreversible Action", "model", "ruan2024toolemu"),
        ("Sycophancy", "model", "perez2022sycophancy"),
        ("Domain Knowledge Deficit", "model", "huang2024hallucinationsurvey"),
        ("Value Misalignment", "model", "morebench"),
        ("Instruction–Grader Mismatch", "owner", "bercovich2026terminal,zhu2025rigorous"),
    ]),
    ("Grader", "Grader", "human", "grader", [
        ("Specification Gaming", "model", "skalse2022rewardhacking"),
        ("Evaluation Awareness", "model", "needham2025evalawareness"),
    ]),
    ("ThirdParty", "Third party", "human", "people", [
        ("Indirect Prompt Injection", "model", "greshake2023injection"),
        ("Contextual Sycophancy", "model", "sharma2023sycophancy"),
    ]),
    ("Context", "Context", "harness", "document", [
        # MAST's Step Repetition is the same failure: an agent repeating already
        # executed steps without progress. Observed in multi-agent traces, but the
        # behaviour is not multi-agent-specific, and the fault is model-side in both.
        ("State Tracking Failure", "model", "cemri2025mast"),
        ("Goal Drift", "model", "arike2025goaldrift"),
        ("Context Rationale Erosion", "context", "selfcompact"),
    ]),
    ("Memory", "Memory", "harness", "database", [
        # MemFail's summary/storage/retrieval/reasoning modes map onto these:
        # storage -> Missed Write, summary -> Rationale Erosion,
        # retrieval -> Missed Read, reasoning -> Memory Following.
        ("Missed Write", "model", "garg2026memfail"),
        ("State Staleness", "model", "chao2026stale"),
        ("Overgeneralization", "model", "lam2026governing"),
        ("Memory Rationale Erosion", "model", "garg2026memfail"),
        ("Pollution", "model", "xiong2025memory"),
        ("Redundancy", "model", "kim2026memrefine"),
        ("Missed Read", "model", "garg2026memfail"),
        ("Memory Following Failure", "model", "garg2026memfail"),
    ]),
    ("Tool", "Tool", "harness", "wrench", [
        ("Incorrect Tool Selection", "model", "huang2023metatool"),
        ("Tool Hallucination", "model", "patil2023gorilla"),
        ("Tool Feedback Neglect", "model", "zhou2024webarena"),
        ("Tool Recovery Failure", "model", "kokane2024toolscan"),
        ("Malformed Arguments", "model", "li2023apibank"),
        ("Suboptimal Arguments", "model", "xiong2025butterfly"),
        ("Mistranslation", "tool", "taraghi2026mcp"),
    ]),
    # A model reaches another model only through its own harness, so the
    # multi-agent edge is a harness component, not a family of its own: the far
    # endpoint is itself a model, playing either role. Peer and subagent share
    # the same two failure modes, so each mode is listed once with both roles'
    # sources clubbed together rather than splitting into two components.
    ("PeerSubagent", "Model (peer/subagent)", "harness", "model", [
        # MAST is the peer-to-peer failure taxonomy; CooperBench is peer-to-peer
        # by construction and names communication as one of its three headline
        # failure causes. ClawArena-Team measures managers delegating with the
        # wrong scope; AOrchestra is about the orchestrator curating each
        # subagent's context.
        ("Delegation Failure", "model", "cemri2025mast,clawarenateam"),
        ("Communication Failure", "model", "cooperbench,aorchestra"),
    ]),
    ("EnvExt", "External", "env", "cloud", [
        # ToolMaze's transient-vs-permanent split is the recoverability rule
        # that decides the fault side here. PlanBench-XL injects explicit
        # "endpoint unavailable" blocks; WAREX injects HTTP 5xx/timeouts.
        # AgentCheck injects stale-but-well-formed records (its Category B).
        ("Recovery Failure", "model", "toolmaze"),
        ("Service Failure", "env", "liu2026planbench,kara2025warex"),
        ("Stale State Delivery", "env", "mazumder2026agentcheck"),
    ]),
    ("EnvLocal", "Local", "env", "terminal", [
        ("Observation Failure", "model", "zhou2024webarena"),
        ("Recovery Failure", "model", "arora2025setupbench"),
    ]),
]
FAMILIES = [
    ("human", ["Owner", "Grader", "ThirdParty"]),
    ("harness", ["Context", "Memory", "Tool", "PeerSubagent"]),
    ("env", ["EnvExt", "EnvLocal"]),
]

# ── geometry (cm) ───────────────────────────────────────────────────────────
ROWH = 0.55
CARDPAD = 0.12
CARDGAP = 0.42
CARDW = 10.2
SPINEW = 0.44
CARD_X = 12.9
COMP_X, COMP_W, COMP_H = 8.2, 4.5, 0.74
FAM_X, FAM_W, FAM_H = 4.9, 2.6, 0.74
MODEL_X, MODEL_W, MODEL_H = 0.0, 2.6, 1.25


def esc(s: str) -> str:
    return s.replace("–", "--").replace("&", "\\&").replace("#", "\\#")


def cite(key):
    return "" if not key else ",\\,{\\scriptsize\\color{ccitegrey}\\citet{%s}}" % key


def main() -> None:
    # 1) vertical layout: stack cards, record y-spans
    cur = 0.0
    card = {}  # cid -> dict(top, bot, cy, items)
    for cid, label, grp, icon, items in COMPONENTS:
        h = len(items) * ROWH + 2 * CARDPAD
        top = cur
        bot = cur - h
        card[cid] = {"top": top, "bot": bot, "cy": (top + bot) / 2, "items": items,
                     "label": label, "grp": grp, "icon": icon}
        cur = bot - CARDGAP
    total_bot = cur

    fam_cy = {}
    for grp, members in FAMILIES:
        # centre each family node on the mean of its components' centres
        fam_cy[grp] = sum(card[m]["cy"] for m in members) / len(members)
    # model centered on the full span of components -- every family now hangs
    # off the model, so there is no separate branch to exclude
    model_cy = (max(c["top"] for c in card.values()) + min(c["bot"] for c in card.values())) / 2

    L = []
    A = L.append

    # 2) colour defs + open picture
    for k, v in COL.items():
        A("\\definecolor{c%s}{HTML}{%s}" % (k, v))
    for g, t in FAM.items():
        A("\\definecolor{f%sB}{HTML}{%s}\\definecolor{f%sM}{HTML}{%s}\\definecolor{f%sF}{HTML}{%s}"
          % (g, t["border"], g, t["mid"], g, t["fill"]))
    for s in ("model", "other"):
        A("\\definecolor{ft%sS}{HTML}{%s}\\definecolor{ft%sR}{HTML}{%s}\\definecolor{ft%sI}{HTML}{%s}"
          % (s, FAULT[s]["spine"], s, FAULT[s]["row"], s, FAULT[s]["ink"]))
    A("\\begin{tikzpicture}[x=1cm,y=1cm,font=\\sffamily]")

    def icon_node(name, x, y, sz=0.5):
        # relative path so the figure is portable (Overleaf/repo): icons live in figures/icons/
        A("\\node at (%.3f,%.3f) {\\includegraphics[width=%.2fcm]{figures/icons/%s.png}};" % (x, y, sz, name))

    def fault_of(side):
        return "model" if side in MODEL_SIDES else "other"

    # 3) edges first (behind boxes)
    def elbow(x1, y1, x2, y2, color, dashed=False):
        mx = (x1 + x2) / 2
        d = "dash pattern=on 3.2pt off 2.2pt,line width=1.5pt," if dashed else "line width=1.4pt,"
        A("\\draw[rounded corners=4pt,%scolor=%s] (%.3f,%.3f) -- (%.3f,%.3f) -- (%.3f,%.3f) -- (%.3f,%.3f);"
          % (d, color, x1, y1, mx, y1, mx, y2, x2, y2))

    for grp, members in FAMILIES:
        # every family, multi-agent included, hangs off the model: the multi-agent
        # edges are model--model, so there is no longer a disconnected branch.
        elbow(MODEL_X + MODEL_W, model_cy, FAM_X, fam_cy[grp], "cmuted")
        for m in members:
            elbow(FAM_X + FAM_W, fam_cy[grp], COMP_X, card[m]["cy"], "f%sM" % grp)
        # component -> card (short straight)
    for cid, c in card.items():
        A("\\draw[line width=1.0pt,color=chairline] (%.3f,%.3f) -- (%.3f,%.3f);"
          % (COMP_X + COMP_W, c["cy"], CARD_X, c["cy"]))

    # 4) model root + summary
    A("\\node[anchor=center,rounded corners=5pt,fill=cmfill,draw=cmdeep,line width=2pt,"
      "minimum width=%.2fcm,minimum height=%.2fcm] (model) at (%.3f,%.3f) {};"
      % (MODEL_W, MODEL_H, MODEL_X + MODEL_W / 2, model_cy))
    icon_node("model", MODEL_X + 0.52, model_cy, 0.58)
    A("\\node[anchor=west,text=cmink,font=\\large\\bfseries] at (%.3f,%.3f) {Model};"
      % (MODEL_X + 0.92, model_cy + 0.20))
    A("\\node[anchor=west,text=cmborder,font=\\scriptsize] at (%.3f,%.3f) {LLM policy};"
      % (MODEL_X + 0.92, model_cy - 0.30))
    # summary panel "Where does the fault lie?" removed per request:
    # it protruded ~4cm left of the model (cL = MODEL_X - 4.05), shrinking the
    # whole figure under \resizebox{\textwidth}. Dropping it tightens the left
    # edge to the model at x=0 so the tree scales up and reads more clearly.

    # 5) family + component boxes
    for grp, members in FAMILIES:
        A("\\node[anchor=center,rounded corners=4pt,fill=f%sF,draw=f%sB,line width=1.8pt,"
          "minimum width=%.2fcm,minimum height=%.2fcm,text=cink,font=\\bfseries] at (%.3f,%.3f) {%s};"
          % (grp, grp, FAM_W, FAM_H, FAM_X + FAM_W / 2, fam_cy[grp], FAM[grp]["name"]))
    for cid, c in card.items():
        grp = c["grp"]
        icon_node(c["icon"], COMP_X + 0.42, c["cy"], 0.46)
        A("\\node[anchor=center,rounded corners=4pt,fill=f%sF,draw=f%sB,line width=1.3pt,"
          "minimum width=%.2fcm,minimum height=%.2fcm] at (%.3f,%.3f) {};"
          % (grp, grp, COMP_W, COMP_H, COMP_X + COMP_W / 2, c["cy"]))
        icon_node(c["icon"], COMP_X + 0.42, c["cy"], 0.46)
        A("\\node[anchor=west,text=cink,font=\\footnotesize\\bfseries] at (%.3f,%.3f) {%s};"
          % (COMP_X + 0.80, c["cy"], esc(c["label"])))

    # 6) cards (rows)
    for cid, c in card.items():
        cx0 = CARD_X
        # card background (hairline) so inter-row gaps read as separators
        A("\\fill[chairline] (%.3f,%.3f) rectangle (%.3f,%.3f);"
          % (cx0, c["top"], cx0 + CARDW, c["bot"]))
        y = c["top"] - CARDPAD
        n = 0
        for it in c["items"]:
            ry0, ry1 = y, y - ROWH + 0.045
            mid = (ry0 + ry1) / 2
            if it[0] == "GROUP":
                gkey = it[2] if len(it) > 2 else None
                A("\\fill[white] (%.3f,%.3f) rectangle (%.3f,%.3f);" % (cx0, ry0, cx0 + CARDW, ry1))
                A("\\draw[chairline,line width=0.6pt] (%.3f,%.3f) -- (%.3f,%.3f);" % (cx0 + 0.12, ry1, cx0 + CARDW - 0.12, ry1))
                A("\\node[anchor=west,text=ccharcoal,font=\\footnotesize\\bfseries] at (%.3f,%.3f) {%s%s};"
                  % (cx0 + 0.12, mid, esc(it[1].upper()), cite(gkey)))
                y -= ROWH
                continue
            n += 1
            label, side, key = it
            ft = fault_of(side)
            A("\\fill[ft%sR] (%.3f,%.3f) rectangle (%.3f,%.3f);" % (ft, cx0, ry0, cx0 + CARDW, ry1))
            A("\\fill[ft%sS] (%.3f,%.3f) rectangle (%.3f,%.3f);" % (ft, cx0, ry0, cx0 + SPINEW, ry1))
            A("\\node[text=white,font=\\footnotesize\\bfseries] at (%.3f,%.3f) {%d};"
              % (cx0 + SPINEW / 2, mid, n))
            gx = cx0 + SPINEW + 0.22
            if FAULT[ft]["glyph"] == "circle":
                A("\\node[circle,fill=ft%sI,inner sep=1.2pt] at (%.3f,%.3f) {};" % (ft, gx, mid))
            else:
                A("\\node[regular polygon,regular polygon sides=3,fill=ft%sI,inner sep=1.1pt] at (%.3f,%.3f) {};" % (ft, gx, mid))
            A("\\node[anchor=west,text=cink,font=\\small] at (%.3f,%.3f) {\\emph{%s}%s};"
              % (cx0 + SPINEW + 0.42, mid, esc(label), cite(key)))
            y -= ROWH

    # 7) legend (top-left, above the tree)
    ly = 1.05
    A("\\node[anchor=west,font=\\scriptsize,text=ccharcoal] at (%.3f,%.3f) {\\textbf{Fault side}};" % (1.54, ly))
    # model chip: filled square (white glyph) + tinted label pill
    A("\\node[anchor=west,minimum size=0.30cm,inner sep=0pt,rounded corners=1.5pt,fill=ftmodelS,text=white,font=\\scriptsize] at (%.3f,%.3f) {$\\bullet$};" % (3.45, ly))
    A("\\node[anchor=west,rounded corners=2pt,fill=ftmodelR,inner sep=2.4pt,font=\\scriptsize,text=cink] at (%.3f,%.3f) {model};" % (3.82, ly))
    A("\\node[anchor=west,minimum size=0.30cm,inner sep=0pt,rounded corners=1.5pt,fill=ftotherS,text=white,font=\\scriptsize] at (%.3f,%.3f) {$\\blacktriangle$};" % (4.95, ly))
    A("\\node[anchor=west,rounded corners=2pt,fill=ftotherR,inner sep=2.4pt,font=\\scriptsize,text=cink] at (%.3f,%.3f) {other component};" % (5.32, ly))
    # family chips: tinted fill + coloured border
    A("\\node[anchor=west,font=\\scriptsize,text=ccharcoal] at (%.3f,%.3f) {\\textbf{Family}};" % (9.9, ly))
    fam_x = {"human": 11.4, "harness": 13.35, "env": 15.3}
    for grp in ("human", "harness", "env"):
        A("\\node[anchor=west,minimum width=1.75cm,rounded corners=2.5pt,fill=f%sF,draw=f%sB,line width=1pt,inner sep=3pt,font=\\scriptsize,text=cink] at (%.3f,%.3f) {%s};"
          % (grp, grp, fam_x[grp], ly, FAM[grp]["name"]))

    A("\\end{tikzpicture}")

    tex = "\n".join(L) + "\n"
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / "model-component-tree.tex").write_text(tex)

    preview = (
        "\\documentclass{article}\n"
        "\\usepackage[paperwidth=25cm,paperheight=28cm,margin=0.5cm]{geometry}\n"
        "\\usepackage[T1]{fontenc}\\usepackage[utf8]{inputenc}\n"
        "\\usepackage{lato}\\renewcommand{\\familydefault}{\\sfdefault}\n"
        "\\usepackage{natbib}\\usepackage{xcolor}\\usepackage{graphicx}\\usepackage{amssymb}\n"
        "\\usepackage{tikz}\\usetikzlibrary{shapes.geometric}\n"
        "\\usepackage[hidelinks]{hyperref}\\hypersetup{colorlinks=true,citecolor=black!55}\n"
        "\\pagestyle{empty}\n"
        "\\begin{document}\n\\noindent\\input{model-component-tree.tex}\n"
        "\\clearpage\n\\bibliographystyle{acl_natbib}\\bibliography{custom}\n"
        "\\end{document}\n"
    )
    (OUTDIR / "_mct_preview.tex").write_text(preview)
    print("wrote", OUTDIR / "model-component-tree.tex")
    print("total height (cm):", round(-total_bot, 2), " width (cm):", round(CARD_X + CARDW, 2))


if __name__ == "__main__":
    main()
