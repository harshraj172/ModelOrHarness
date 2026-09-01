"""Local pass-through shim: Claude Code -> (strip claude-only params) -> LiteLLM.
Claude Code sends Anthropic-beta request fields (e.g. `context_management`)"""

from __future__ import annotations

import http.client
import http.server
import json
import os
import threading

UPSTREAM_HOST = os.environ.get("JUDGE_PROXY_HOST", "litellm-proxy.example.com")
STRIP_BODY_KEYS = ("context_management",)
_STRIP_MSG_BLOCK_TYPES = {"thinking", "redacted_thinking"}
STRIP_BETA_PREFIXES = ("context-management",)

_HOP = {
    "connection",
    "keep-alive",
    "transfer-encoding",
    "te",
    "trailer",
    "proxy-authorization",
    "proxy-authenticate",
    "upgrade",
    "host",
    "content-length",
    "accept-encoding",
}


class _Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _forward(self) -> None:
        length = int(self.headers.get("content-length") or 0)
        body = self.rfile.read(length) if length else b""
        if body and self.headers.get("content-type", "").startswith("application/json"):
            try:
                payload = json.loads(body)
                for k in STRIP_BODY_KEYS:
                    payload.pop(k, None)
                model_id = payload.get("model", "")
                if model_id and not str(model_id).startswith("claude"):
                    for msg in payload.get("messages", []):
                        if not isinstance(msg, dict):
                            continue
                        msg.pop("thinking_blocks", None)
                        if isinstance(msg.get("content"), list):
                            filtered = [
                                b for b in msg["content"]
                                if not (
                                    isinstance(b, dict)
                                    and b.get("type") in _STRIP_MSG_BLOCK_TYPES
                                )
                            ]
                            if not filtered:
                                filtered = [{"type": "text", "text": ""}]
                            msg["content"] = filtered
                extra = os.environ.get("TAXJUDGE_EXTRA_BODY")
                if extra and isinstance(payload, dict) and "model" in payload:
                    payload.update(json.loads(extra))
                body = json.dumps(payload).encode()
            except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
                pass
        headers = {}
        for k, v in self.headers.items():
            lk = k.lower()
            if lk in _HOP:
                continue
            if lk == "anthropic-beta":
                kept = [
                    b.strip()
                    for b in v.split(",")
                    if not any(b.strip().startswith(p) for p in STRIP_BETA_PREFIXES)
                ]
                if not kept:
                    continue
                v = ",".join(kept)
            headers[k] = v
        headers["host"] = UPSTREAM_HOST
        headers["content-length"] = str(len(body))

        conn = http.client.HTTPSConnection(UPSTREAM_HOST, timeout=600)
        try:
            conn.request(self.command, self.path, body=body or None, headers=headers)
            resp = conn.getresponse()
            self.send_response(resp.status)
            for k, v in resp.getheaders():
                if k.lower() in _HOP | {"content-length"}:
                    continue
                self.send_header(k, v)
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()
            while True:
                chunk = resp.read(8192)
                if not chunk:
                    break
                self.wfile.write(f"{len(chunk):X}\r\n".encode() + chunk + b"\r\n")
            self.wfile.write(b"0\r\n\r\n")
        except Exception:
            try:
                self.send_error(502)
            except Exception:
                pass
        finally:
            conn.close()

    do_POST = do_GET = do_PUT = do_DELETE = _forward


_server: http.server.ThreadingHTTPServer | None = None
_port: int | None = None
_lock = threading.Lock()


def ensure_shim() -> str:
    """Start the shim once per process; return its base URL."""
    global _server, _port
    with _lock:
        if _port is None:
            _server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
            _port = _server.server_address[1]
            threading.Thread(target=_server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{_port}"


if __name__ == "__main__":
    url = ensure_shim()
    print(f"shim on {url} -> https://{UPSTREAM_HOST}")
    threading.Event().wait()
