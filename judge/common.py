"""Shared primitives for the taxonomy_judge package.
Everything the taxonomy-aware agent needs lives here:"""

from __future__ import annotations

import json
import re
import urllib.request
import os
from pathlib import Path


def _norm(s) -> str:
    """Canonicalize a label for comparison: lowercase, alnum-only, single-spaced."""
    s = str(s).lower().replace("lead-agent","orchestrator").replace("lead agent","orchestrator")
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


ENV_FILE = Path(os.environ.get("JUDGE_ENV_FILE", ".env"))


def env_key(name: str) -> str:
    v = os.environ.get(name)
    if v:
        return v
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            if line.startswith(name):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def proxy_key() -> str:
    for name in ("JUDGE_API_KEY",):
        key = env_key(name)
        if key:
            return key
    raise SystemExit(f"No proxy key found in {ENV_FILE}")


PROXY_HOST = os.environ.get("JUDGE_PROXY_HOST", "litellm-proxy.example.com")
PROXY = f"https://{PROXY_HOST}/v1/messages"

ALIASES = {
    "gpt-5.5-xhigh": (
        "gpt-5.5",
        {"allowed_openai_params": ["reasoning"], "reasoning": {"effort": "xhigh"}},
    ),
    "gpt-5.4-xhigh": (
        "gpt-5.4",
        {"allowed_openai_params": ["reasoning"], "reasoning": {"effort": "xhigh"}},
    ),
    "gpt-5.2-xhigh": (
        "gpt-5.2",
        {"allowed_openai_params": ["reasoning"], "reasoning": {"effort": "xhigh"}},
    ),
    "claude-opus-4-8": (
        "claude-opus-4-8",
        {"thinking": {"type": "adaptive"}, "output_config": {"effort": "max"}},
    ),
    "gpt-6-astra-max": (
        "gpt-6-astra",
        {"allowed_openai_params": ["reasoning"], "reasoning": {"effort": "max"}},
    ),
    "grok-4.6-max": (
        "xai/grok-4.6",
        {"reasoning_effort": "max"},
    ),
    "gemini-3.1-pro-max": (
        "gemini/gemini-3.1-pro-preview",
        {"reasoning_effort": "max"},
    ),
    "glm-5.2": (
        "fireworks_ai/glm-5p2",
        {},
    ),
    "glm-5.2-high": (
        "fireworks_ai/glm-5p2",
        {"thinking": {"type": "enabled", "budget_tokens": 64000}},
    ),
}


def call(model_alias: str, system: str, user: str, max_tokens: int = 32000) -> str:
    """One tool-free completion through the proxy. Returns the text."""
    model, extra = ALIASES.get(model_alias, (model_alias, {}))
    body = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user}],
        **extra,
    }
    req = urllib.request.Request(
        PROXY,
        data=json.dumps(body).encode(),
        method="POST",
        headers={
            "content-type": "application/json",
            "Authorization": "Bearer " + proxy_key(),
        },
    )
    d = json.load(urllib.request.urlopen(req, timeout=600))
    text = "".join(
        b.get("text", "") for b in d.get("content", []) if isinstance(b, dict)
    )
    if not text.strip() and max_tokens < 64000:
        return call(model_alias, system, user, max_tokens=64000)
    return text


def _extract_json(text: str) -> dict:
    """Pull the first balanced JSON object out of a model reply."""
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    pos, last_err = 0, None
    while pos < len(text):
        i = text.find("{", pos)
        if i < 0:
            break
        depth, in_str, esc, end = 0, False, False, -1
        for j in range(i, len(text)):
            c = text[j]
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = not in_str
            elif not in_str and c == "{":
                depth += 1
            elif not in_str and c == "}":
                depth -= 1
                if depth == 0:
                    end = j
                    break
        if end < 0:
            break
        try:
            return json.loads(text[i : end + 1])
        except json.JSONDecodeError as e:
            last_err, pos = e, i + 1
    raise ValueError(f"no parseable JSON (last: {last_err}): {text[:200]!r}")


FORBIDDEN_PATTERNS = [
    r"agent-failure-taxonomy\.md",
    r"taxonomy_judge[/\\]experiments",
    r"taxonomy_judge[/\\]judge",
    r"taxonomy_judge[/\\]preds",
    r"taxonomy_judge[/\\]preds-5thjudge",
    r"taxonomy_judge[/\\]runs",
    r"taxonomy_judge[/\\]verified-phase-I",
    r"taxonomy_judge[/\\]verified-phase-II",
    r"taxonomy_judge[/\\]visualizer",
    r"taxonomy_judge[/\\][^/\\]+\.py",
    r"examples\.jsonl",
    r"splits\.json",
    r"predictions[/\\]",
    r"agent_failure_taxonomy-latex",
    r"tmp\.md",
    r"agent.{0,3}failure.{0,3}taxonomy",
]


def detect_leaks(trace: list[dict]) -> list[str]:
    hits = []
    for t_ in trace or []:
        blob = json.dumps(t_)
        for pat in FORBIDDEN_PATTERNS:
            if re.search(pat, blob, re.I):
                hits.append(f"{t_.get('tool')}: {str(t_.get('args'))[:120]}")
                break
    return hits


TOOL_USE_BLOCK = """\
You will be given a REFERENCE to source material about one agent failure: a
blog post, paper section, GitHub issue/PR, HuggingFace dataset row, Docent
trajectory link, system-card section, or a local file path. Open and read it
with your tools (WebFetch, Bash with curl, Read, Grep, Glob, WebSearch) before
deciding anything. If the reference has no URL, use WebSearch to locate the
source first. If a URL is unreachable, try alternatives (curl, the HuggingFace
datasets-server API, raw.githubusercontent, web.archive.org for X/dead links,
or a different mirror) before giving up. For docent.transluce.org trajectory
links, use the Docent REST API with the DOCENT_API_KEY environment variable
(Bash: curl -H "Authorization: Bearer $DOCENT_API_KEY" against
https://api.docent.transluce.org, deriving collection/agent-run ids from the
dashboard URL) instead of scraping the dashboard page."""
