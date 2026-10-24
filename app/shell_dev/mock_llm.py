"""A stand-in for an OpenAI-compatible /chat/completions endpoint (streaming SSE), so the REAL
genius_client streaming and tool loop can be exercised end to end without a network or a key.

    server = MockLLM().start();  settings["api_base"] = server.base_url

Scenario is chosen by the text of the last user message:
    "slow"   ~10 s of slow content chunks (for Stop)
    "fail"   HTTP 500
    "markdown" a reply with bold, inline code, a code fence and raw HTML (which must render as text)
    "tools"  round 1: some narration + a live_read_set tool call; round 2 (after the tool result): the answer
    anything else: reasoning + a short streamed reply
"""

from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


class MockLLM:
    def __init__(self, port: int = 0) -> None:
        outer = self
        self.requests: list[dict[str, Any]] = []
        self.gets: list[str] = []
        self.disconnects = 0

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.0"      # close after the stream: the client reads until EOF

            def log_message(self, *_a: Any) -> None:
                pass

            def _sse(self, delta: dict[str, Any]) -> bool:
                try:
                    self.wfile.write(("data: %s\n\n" % json.dumps({"choices": [{"delta": delta}]})).encode("utf-8"))
                    self.wfile.flush()
                    return True
                except (BrokenPipeError, ConnectionResetError, OSError):
                    outer.disconnects += 1
                    return False

            def do_GET(self) -> None:
                # ai_providers.list_models: GET {api_base}/models
                outer.gets.append(self.path)
                data = json.dumps({"data": [{"id": "e2e-model"}, {"id": "e2e-model-2"}, {"id": "text-embedding-x"}]}).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_POST(self) -> None:
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
                outer.requests.append(body)
                if not body.get("stream"):
                    # genius_client.test_key: one plain JSON completion
                    data = json.dumps({"choices": [{"message": {"content": "ok"}}]}).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    return
                msgs = body.get("messages") or []
                last_user = next((m for m in reversed(msgs) if m.get("role") == "user"), {})
                text = str(last_user.get("content") or "")
                after_user = msgs[msgs.index(last_user) + 1:] if last_user in msgs else []
                has_tool_result = any(m.get("role") == "tool" for m in after_user)

                if "fail" in text:
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(b"boom from the mock")
                    return
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.end_headers()
                ok = True
                if "slow" in text:
                    for i in range(40):
                        if not self._sse({"content": "word%d " % i}):
                            return
                        time.sleep(0.25)
                elif "markdown" in text:
                    body = ("Here is **bold** and `inline code`.\n\n```python\nprint('<b>hi</b>')\n```\n"
                            "<script>window.__pwned = 1</script> and a <img src=x onerror=\"window.__pwned=1\">")
                    for i in range(0, len(body), 12):
                        ok = ok and self._sse({"content": body[i:i + 12]})
                        time.sleep(0.02)
                elif "vocal" in text and not has_tool_result:
                    # v1.2.0: a paid host tool. The shell must put an approval modal in front
                    # of this before genius_client ever reaches tts_vocal.run.
                    ok = self._sse({"tool_calls": [{"index": 0, "id": "call_v", "function": {
                        "name": "live_tts_vocal",
                        "arguments": json.dumps({"text": "I am King America"}),
                    }}]})
                elif "vocal" in text:
                    tool_msg = next((m for m in reversed(after_user) if m.get("role") == "tool"), {})
                    ok = self._sse({"content": "Tool said: " + str(tool_msg.get("content") or "")[:400]})
                elif "tools" in text and not has_tool_result:
                    ok = self._sse({"content": "Let me check the Set. "})
                    time.sleep(0.05)
                    ok = ok and self._sse({"tool_calls": [{"index": 0, "id": "call_1", "function": {"name": "live_read_set", "arguments": "{}"}}]})
                elif "tools" in text:
                    for chunk in ("The Set ", "has 10 ", "tracks."):
                        ok = ok and self._sse({"content": chunk})
                        time.sleep(0.05)
                else:
                    ok = self._sse({"reasoning_content": "Thinking it over. "})
                    for chunk in ("Hello ", "from ", "the ", "mock."):
                        ok = ok and self._sse({"content": chunk})
                        time.sleep(0.15)
                if ok:
                    try:
                        self.wfile.write(b"data: [DONE]\n\n")
                        self.wfile.flush()
                    except OSError:
                        pass

        self._server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
        self._server.daemon_threads = True
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True, name="mock-llm")

    @property
    def base_url(self) -> str:
        return "http://127.0.0.1:%d/v1" % self._server.server_address[1]

    def start(self) -> "MockLLM":
        self._thread.start()
        return self

    def stop(self) -> None:
        self._server.shutdown()
        self._server.server_close()
