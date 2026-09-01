# Worked-example source material

Evidence for five appendix examples whose sources are not on a public site, bundled so
each can be inspected without following an external link.

| Dir | Contents | Upstream |
|-----|----------|----------|
| `E6/`  | task definition, agent trace, jury label | SWE-Bench Pro, `instance_ansible__ansible-83909bfa` |
| `E19/` | full trial: trajectory, session files, verifier output | Harbor-Index, task `aa-lcr-18` |
| `E24/` | task definition and the failing trial | AutoClaw Feishu context-failure task |
| `E31/` | raw session transcript | authors' own session, 2026-06-08 |
| `E40/` | agent trajectory | Harbor-Index, GAIA2/ARE `adaptability` |

Each example is described, and its label given, in the paper's appendix; that is not
repeated here.

Paths were rewritten for anonymous review, so a path reading `/workspace/...` was a local
working directory and `anon-org` replaced a repository owner. Traces, verifier output and
labels are otherwise the originals.

`appendix_examples/` is on the judge's leak blocklist, so re-running the judge cannot read
these files.
