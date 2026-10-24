"""Start the REAL shell with one network call faked: Cartesia's POST /tts/bytes.

    python shell_dev/run_shell_fake_tts.py [any shell.py arguments]

Test-only. It replaces `urllib.request.urlopen` for exactly that one URL (everything else goes to the
original) and then calls `shell.main()` -- no production file is edited or patched on disk. The faked reply
is a valid mono float32 WAV like the real endpoint's `wav / pcm_f32le`, so the shell's real ffmpeg step runs.
Every intercepted request is appended as one JSON line to the file named by LA_FAKE_TTS_LOG (headers with
the key masked), so a test can prove what the shell would have sent.
"""

from __future__ import annotations

import json
import math
import os
import struct
import sys
import urllib.request
from pathlib import Path

APP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP))

FAKE_URL = "https://api.cartesia.ai/tts/bytes"
_real_urlopen = urllib.request.urlopen


def float_wav(seconds: float = 0.6, rate: int = 48000) -> bytes:
    n = int(seconds * rate)
    data = b"".join(struct.pack("<f", 0.3 * math.sin(2 * math.pi * 220 * i / rate)) for i in range(n))
    fmt = struct.pack("<HHIIHH", 3, 1, rate, rate * 4, 4, 32)
    body = b"WAVE" + b"fmt " + struct.pack("<I", len(fmt)) + fmt + b"data" + struct.pack("<I", len(data)) + data
    return b"RIFF" + struct.pack("<I", len(body)) + body


class _Reply:
    status = 200

    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> None:
        return None


def _urlopen(req, *args, **kwargs):
    url = getattr(req, "full_url", req)
    if url != FAKE_URL:
        return _real_urlopen(req, *args, **kwargs)
    log = os.environ.get("LA_FAKE_TTS_LOG")
    if log:
        headers = {k.lower(): ("Bearer ***" if k.lower() == "authorization" else v) for k, v in req.header_items()}
        with open(log, "a", encoding="utf-8") as f:
            f.write(json.dumps({"url": url, "method": req.get_method(), "headers": headers, "body": json.loads(req.data.decode("utf-8")),
                                "auth_len": len(dict((k.lower(), v) for k, v in req.header_items()).get("authorization", ""))}) + "\n")
    return _Reply(float_wav())


urllib.request.urlopen = _urlopen

import shell  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(shell.main())
