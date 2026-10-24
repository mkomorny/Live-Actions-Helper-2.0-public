"""Launch a tool's dialog HTML in its own WebView2 window."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any


def webview_available() -> tuple[bool, str]:
    try:
        import webview  # noqa: F401
    except Exception as exc:
        return False, str(exc)
    return True, ""


class WebViewPane:
    """Child-process dialog. Helper polls `poll()` and gets one Insert/Cancel payload."""

    def __init__(
        self,
        tk_host,
        on_message: Callable[[Any], None],
        cache_dir: Path,
        html: str,
        title: str = "Live Actions",
        tool_id: str = "webview",
    ) -> None:
        self.tk_host = tk_host
        self.on_message = on_message
        self._closed = False
        self._delivered = False
        handle, html_name = tempfile.mkstemp(prefix=f"{tool_id}-", suffix=".html")
        os.close(handle)
        handle, out_name = tempfile.mkstemp(prefix=f"{tool_id}-", suffix=".json")
        os.close(handle)
        self._html_path = Path(html_name)
        self._out_path = Path(out_name)
        self._html_path.write_text(html, encoding="utf-8")
        self._out_path.write_text("", encoding="utf-8")
        script = Path(__file__).with_name("breakdowns_window.py")
        log_dir = Path(os.environ.get("APPDATA", str(Path.home()))) / "Live Actions"
        log_dir.mkdir(parents=True, exist_ok=True)
        self._log_path = log_dir / f"{tool_id}-window.log"
        self._log_file = self._log_path.open("w", encoding="utf-8")
        startupinfo = None
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        self._proc = subprocess.Popen(
            [
                sys.executable, str(script),
                "--html", str(self._html_path),
                "--out", str(self._out_path),
                "--title", title,
            ],
            cwd=str(script.parent),
            startupinfo=startupinfo,
            stdout=self._log_file,
            stderr=subprocess.STDOUT,
        )
        if os.name == "nt":
            # Windows' foreground-lock policy blocks a background process from
            # bringing its own new window to front. This process just handled
            # a real click, so it has standing to grant that right to the
            # child it's spawning -- otherwise the dialog opens invisibly
            # stacked behind Live/this window until the user alt-tabs to it.
            try:
                import ctypes
                ctypes.windll.user32.AllowSetForegroundWindow(self._proc.pid)
            except Exception:
                pass
        self._poll()

    def destroy(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._proc.poll() is None:
            try:
                self._proc.terminate()
            except OSError:
                pass
        try:
            self._log_file.close()
        except Exception:
            pass
        self._cleanup_files()

    def _poll(self) -> None:
        if self._closed:
            return
        if not self._delivered:
            payload = self._read_result()
            if payload is not _MISSING:
                self._delivered = True
                self.on_message(payload)
                self.destroy()
                return
        if self._proc.poll() is not None and not self._delivered:
            self._delivered = True
            self.on_message(None)
            self.destroy()
            return
        try:
            self.tk_host.after(200, self._poll)
        except Exception:
            pass

    def _read_result(self):
        try:
            raw = self._out_path.read_text(encoding="utf-8").strip()
        except OSError:
            return _MISSING
        if not raw:
            return _MISSING
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return _MISSING
        if isinstance(data, dict) and "payload" in data:
            return data.get("payload")
        return _MISSING

    def _cleanup_files(self) -> None:
        for path in (self._html_path, self._out_path):
            try:
                path.unlink()
            except OSError:
                pass


_MISSING = object()
