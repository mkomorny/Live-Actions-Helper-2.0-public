"""Standalone webview dialog host, shared by all webview tools. One HTML file in, one JSON result out."""

from __future__ import annotations

import argparse
import ctypes
import json
import sys
from pathlib import Path

import webview

if sys.platform == "win32":
    # Without this, a non-DPI-aware process is told every monitor is 96 DPI,
    # so on a scaled display the WinForms host window Windows creates at its
    # (-32000, -32000) "minimized" placeholder never gets moved back to real
    # screen coordinates -- it opens thousands of pixels off-screen instead.
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass


class Bridge:
    def __init__(self, out_path: Path) -> None:
        self.out_path = out_path
        self._wrote = False

    def receive(self, raw: str) -> None:
        payload = _payload_from_raw(raw)
        self._write(payload)
        window = webview.active_window()
        if window is not None:
            window.destroy()

    def _write(self, payload) -> None:
        if self._wrote:
            return
        self._wrote = True
        self.out_path.write_text(json.dumps({"payload": payload}), encoding="utf-8")


def _payload_from_raw(raw: str):
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    if isinstance(data, dict) and data.get("method") == "close_and_send":
        params = data.get("params") or []
        return params[0] if params else None
    return data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--html", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--title", default="Live Actions")
    args = parser.parse_args()
    html = Path(args.html)
    out = Path(args.out)
    if not html.is_file():
        raise SystemExit("dialog HTML missing")

    bridge = Bridge(out)
    window = webview.create_window(
        args.title,
        html.as_uri(),
        width=1180,
        height=780,
        min_size=(980, 640),
        background_color="#08090C",
        text_select=False,
        on_top=True,
        js_api=bridge,
    )

    def on_loaded() -> None:
        # A dedicated property, NOT window.chrome.webview: on the Windows
        # edgechromium backend, window.chrome.webview.postMessage is the real
        # native WebView2 channel pywebview's own js_api plumbing uses
        # internally (on_script_notify in pywebview/platforms/edgechromium.py
        # expects postMessage payloads shaped as its own internal
        # [func_name, func_param, value_id] protocol). Overwriting it here
        # used to work only until a dialog's send() called
        # window.pywebview.api.receive(raw) from inside that same override --
        # pywebview's generated api.receive() proxy itself calls
        # window.chrome.webview.postMessage(...) to reach Python, which
        # re-entered our override and corrupted pywebview's own envelope
        # ("not enough values to unpack (expected 3, got 2)" in
        # on_script_notify, silently swallowed there -- the dialog never
        # closed on Cancel/Apply). Exposing a separate, non-colliding
        # property sidesteps this entirely.
        window.evaluate_js(
            """
            window.liveActionsSend = function (raw) {
              if (window.pywebview && window.pywebview.api && window.pywebview.api.receive) {
                window.pywebview.api.receive(raw);
              }
            };
            """
        )

    def on_closed() -> None:
        if not bridge._wrote:
            bridge._write(None)

    def on_shown() -> None:
        # The parent granted this process foreground rights via
        # AllowSetForegroundWindow right after spawning it; claim them now,
        # or the window opens correctly-positioned but stacked invisibly
        # behind Live/the host window until the user alt-tabs to it.
        if sys.platform == "win32":
            try:
                hwnd = window.native.Handle.ToInt32()
                ctypes.windll.user32.ShowWindow(hwnd, 5)  # SW_SHOW
                ctypes.windll.user32.SetForegroundWindow(hwnd)
                ctypes.windll.user32.BringWindowToTop(hwnd)
            except Exception:
                pass

    window.events.loaded += on_loaded
    window.events.closed += on_closed
    window.events.shown += on_shown
    webview.start()


if __name__ == "__main__":
    main()
