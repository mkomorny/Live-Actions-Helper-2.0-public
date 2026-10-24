"""Launch the REAL shell in demo state, screenshot it over CDP, diff against the preview.

    python -m shell_dev.capture_shell [--state actions|filter-setwide] [--net-fonts]

Pins the emulated viewport to 1360x820 @1x (CDP Emulation.setDeviceMetricsOverride) so the
pixel grid matches previews/redesign-round/shots/ regardless of this PC's 144 DPI, then runs
previews/redesign-round/tools/fidelity_diff.py. Exits with fidelity_diff's code.

--net-fonts  DEV ONLY: injects the preview's Google Fonts <link> into the page so the diff can
             be run before the bundled font files exist. A run that needs it is provisional;
             the shipped acceptance run is without it.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import websocket  # websocket-client

APP = Path(__file__).resolve().parent.parent
ROUND = APP.parent / "previews" / "redesign-round"
SHOTS = ROUND / "shots"
STATES = {
    "actions": ("a__risograph-art-studio.png", []),
    "filter-setwide": ("extra__a-filter-setwide.png", ['[data-k="set"]']),
    "genius": ("extra__a-genius.png", ['[data-act="page"][data-k="genius"]']),
    "prefs": ("extra__a-settings.png", ['[data-act="settings"]']),
    "prefs-themes": ("extra__a-settings-themes-open.png", ['[data-act="settings"]', '[data-act="pf-theme-toggle"]']),
}
HOVER = {"prefs-themes": '[data-act="pf-theme-toggle"]'}   # the reference shows this row in its :hover state
NET_FONTS = "https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;700&family=Space+Mono:wght@400;700&display=swap"


class Cdp:
    def __init__(self, url: str) -> None:
        self.ws = websocket.create_connection(url, timeout=20, suppress_origin=True)
        self.n = 0
        self.events: list[dict] = []

    def call(self, method: str, **params):
        self.n += 1
        self.ws.send(json.dumps({"id": self.n, "method": method, "params": params}))
        while True:
            msg = json.loads(self.ws.recv())
            if "method" in msg:
                self.events.append(msg)
                continue
            if msg.get("id") == self.n:
                if "error" in msg:
                    raise RuntimeError("%s: %s" % (method, msg["error"]))
                return msg.get("result", {})

    def sheet_headers(self) -> list[dict]:
        self.call("Runtime.evaluate", expression="1")   # flush queued events
        return [e["params"]["header"] for e in self.events if e.get("method") == "CSS.styleSheetAdded"]

    def eval(self, expr: str):
        r = self.call("Runtime.evaluate", expression=expr, awaitPromise=True, returnByValue=True)
        return r.get("result", {}).get("value")


def wait_for(fn, timeout: float, what: str):
    end = time.time() + timeout
    while time.time() < end:
        try:
            v = fn()
        except (RuntimeError, ConnectionError, websocket.WebSocketException):
            v = None   # e.g. "Execution context was destroyed" while the page is still navigating
        if v:
            return v
        time.sleep(0.2)
    raise TimeoutError("timed out waiting for " + what)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default="actions", choices=sorted(STATES))
    ap.add_argument("--net-fonts", action="store_true")
    ap.add_argument("--dpi-unaware", action="store_true")
    ap.add_argument("--port", type=int, default=9333)
    ap.add_argument("--out", default="")
    ap.add_argument("--max-diff", default="0.02")
    ap.add_argument("--probe", default="", help="JS to evaluate after load; result is printed")
    ap.add_argument("--theme", default="", help="apply this kit through the page's own LA.setTheme hook before capturing (v1.0.64); the reference "
                    "becomes that kit's a__<slug>.png (Actions state only -- other states have a reference for Riso alone; use --no-diff)")
    ap.add_argument("--no-diff", action="store_true", help="capture only (review shots for states that have no reference in this theme)")
    args = ap.parse_args()

    ref_name, clicks = STATES[args.state]
    if args.theme and not args.no_diff:
        if args.state != "actions":
            print("only the actions state has a per-kit reference; pass --no-diff to capture %r in %s" % (args.state, args.theme), file=sys.stderr)
            return 2
        ref_name = "a__%s.png" % args.theme
    tmp = Path(tempfile.mkdtemp(prefix="la-capture-"))
    ready = tmp / "ready.txt"
    out = Path(args.out) if args.out else tmp / ("shell__%s.png" % args.state)
    env = dict(os.environ, LIVE_ACTIONS_INSTANCE="shellcapture")
    proc = subprocess.Popen(
        [sys.executable, str(APP / "shell.py"), "--demo-state", "--cdp-port", str(args.port), "--ready-file", str(ready)] + (["--dpi-unaware"] if args.dpi_unaware else []),
        cwd=str(APP), env=env,
    )
    try:
        wait_for(ready.exists, 40, "the shell window to be shown")
        hwnd = int(dict(l.split("=") for l in ready.read_text().split())["hwnd"])
        targets = wait_for(lambda: [t for t in json.load(urllib.request.urlopen("http://127.0.0.1:%d/json" % args.port)) if t.get("type") == "page"], 20, "a CDP page target")
        cdp = Cdp(targets[0]["webSocketDebuggerUrl"])
        cdp.call("Emulation.setDeviceMetricsOverride", width=1360, height=820, deviceScaleFactor=1, mobile=False)
        wait_for(lambda: cdp.eval("document.readyState==='complete' && document.body && document.body.getAttribute('data-ready')==='1'"), 30, "the page to finish loading")
        cdp.call("Page.bringToFront")
        # The references were captured in headless Chromium, which draws no scrollbars.
        cdp.call("Emulation.setScrollbarsHidden", hidden=True)
        # The override only takes effect on the next style recalc (the --net-fonts path below used to force
        # one as a side effect); force it here so both paths measure the same scrollbar-free layout.
        cdp.eval("(()=>{const d=document.documentElement;d.style.display='none';void d.offsetHeight;d.style.display='';void d.offsetHeight;return 1})()")
        if args.net_fonts:
            # Drop the (not-yet-present) bundled @font-face rules so they cannot shadow the network
            # faces. The theme sheet is file:// (opaque to page JS), so edit it through CDP's CSS domain.
            cdp.call("DOM.enable"); cdp.call("CSS.enable")
            heads = cdp.sheet_headers()
            theme = [h for h in heads if h.get("sourceURL", "").endswith("risograph-art-studio.css")]
            for h in theme:
                text = cdp.call("CSS.getStyleSheetText", styleSheetId=h["styleSheetId"])["text"]
                kept = chr(10).join(l for l in text.splitlines() if not (l.lstrip().startswith("@font-face") and "fonts/" in l))
                cdp.call("CSS.setStyleSheetText", styleSheetId=h["styleSheetId"], text=kept)
            cdp.eval("new Promise((res)=>{const l=document.createElement('link');l.rel='stylesheet';l.href=%s;l.onload=()=>res(1);l.onerror=()=>res(0);document.head.appendChild(l);})" % json.dumps(NET_FONTS))
            cdp.eval("Promise.all(['400 13px \"DM Sans\"','700 13px \"DM Sans\"','400 13px \"Space Mono\"','700 13px \"Space Mono\"'].map(f=>document.fonts.load(f))).then(()=>1)")
        wait_for(lambda: cdp.eval("document.body.getAttribute('data-ready')") == "1", 20, "body[data-ready]")
        if args.theme:
            # The theme loader hook the Preferences picker uses; proves the kit's OWN faces are registered (by name) and loaded.
            from shell_dev import theme_audit                      # here, not at the top: theme_audit imports this module
            try:
                faces = theme_audit.apply_theme(cdp, args.theme)
            except (RuntimeError, TimeoutError) as exc:
                print("FAIL: %s" % exc, file=sys.stderr)
                return 3
            print("theme %s: %d faces loaded -> %s" % (args.theme, len(faces), faces))
        else:
            # Never screenshot mid font-swap: every face the theme uses must report loaded.
            wait_for(lambda: cdp.eval("['400 13px \"DM Sans\"','700 13px \"DM Sans\"','400 13px \"Space Mono\"','700 13px \"Space Mono\"'].every(f=>document.fonts.check(f))"), 20, "fonts to load")
        for sel in clicks:
            cdp.eval("document.querySelector(%s).click()" % json.dumps(sel))
            time.sleep(0.15)
        if args.state in HOVER:
            # A JS .click() never moves the pointer, so :hover would not apply; move the real one over the element.
            box = cdp.eval("(()=>{const r=document.querySelector(%s).getBoundingClientRect();return [r.x+r.width/2, r.y+r.height/2]})()" % json.dumps(HOVER[args.state]))
            cdp.call("Input.dispatchMouseEvent", type="mouseMoved", x=box[0], y=box[1])
            time.sleep(0.2)
        time.sleep(0.5)
        if args.probe:
            print("probe:", json.dumps(cdp.eval(args.probe), indent=1)[:3000])
        import base64
        out.write_bytes(base64.b64decode(cdp.call("Page.captureScreenshot", format="png")["data"]))
        fonts = cdp.eval("[...document.fonts].filter(f=>f.status==='loaded').map(f=>f.family+' '+f.weight)")
        print("captured %s (loaded fonts: %s)" % (out, fonts))
        cdp.ws.close()
    finally:
        try:
            sys.path.insert(0, str(APP))
            import single_instance
            if "hwnd" in locals():
                single_instance.post_close(hwnd)
            proc.wait(timeout=15)
        except Exception:
            proc.kill()
    if args.no_diff:
        return 0
    diff = out.with_name(out.stem + "__diff.png")
    r = subprocess.run([sys.executable, str(ROUND / "tools" / "fidelity_diff.py"), str(SHOTS / ref_name), str(out), "--out", str(diff), "--max-diff", args.max_diff])
    return r.returncode


if __name__ == "__main__":
    raise SystemExit(main())
