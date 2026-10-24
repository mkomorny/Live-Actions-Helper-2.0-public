"""Every kit, every view of the real shell (demo state): load check, contrast and overflow numbers, one screenshot each for review.

    python -m shell_dev.audit_themes [--out DIR] [--only slug,slug]

Views: Actions, Genius, Preferences with Appearance open, the console drawer, and the Add-to-Live-Set slot picker (rendered from
sample data through the page's own LA.placeModal, since a real one needs a run). One shell process per kit. Prints one line per view;
the numbers are what test decisions are made from (a low contrast that is ALSO in the kit's own preview is the kit's design).
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

APP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP))
from shell_dev import theme_audit                      # noqa: E402
from shell_dev.capture_shell import Cdp, wait_for      # noqa: E402
import shell_prefs                                      # noqa: E402
import single_instance                                  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # page text has check marks; the Windows console is cp1252

PORT = 9337
PLACE_SAMPLE = ("({tool:'TTS Vocal', track:'Vox', slots:[{index:0,n:1,has:false},{index:1,n:2,has:true,name:'Kick loop'},{index:2,n:3,has:true},{index:3,n:4,has:false}]},"
                "{sel:0, warn:'Slot 2 already holds a clip - click Place again to replace it.'})")

VIEWS = [
    ("actions", []),
    ("genius", ['[data-act="page"][data-k="genius"]']),
    ("prefs", ['[data-act="settings"]', '[data-act="pf-theme-toggle"]']),
    ("console", ['[data-act="console"]']),
    ("thinking", ['[data-act="page"][data-k="genius"]', '[data-act="thinking"]']),
    ("place", "place"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="")
    ap.add_argument("--only", default="")
    ap.add_argument("--size", default="1360x820", help="viewport WxH, e.g. 720x520")
    args = ap.parse_args()
    size_w, _, size_h = args.size.lower().partition("x")
    size_w, size_h = int(size_w), int(size_h)
    out = Path(args.out) if args.out else Path(tempfile.mkdtemp(prefix="la-audit-"))
    out.mkdir(parents=True, exist_ok=True)
    slugs = [t["slug"] for t in shell_prefs.KNOWN_THEMES if not args.only or t["slug"] in args.only.split(",")]
    tmp = Path(tempfile.mkdtemp(prefix="la-audit-run-"))
    bad = 0
    for slug in slugs:
        ready = tmp / "ready.txt"
        ready.unlink(missing_ok=True)
        env = dict(os.environ, LIVE_ACTIONS_INSTANCE="shellaudit")
        proc = subprocess.Popen([sys.executable, str(APP / "shell.py"), "--demo-state", "--cdp-port", str(PORT), "--ready-file", str(ready), "--dpi-unaware"], cwd=str(APP), env=env)
        hwnd = 0
        try:
            wait_for(ready.exists, 40, "window")
            hwnd = int(dict(l.split("=") for l in ready.read_text().split())["hwnd"])
            page = wait_for(lambda: [t for t in json.load(urllib.request.urlopen("http://127.0.0.1:%d/json" % PORT)) if t.get("type") == "page"], 20, "page")[0]
            cdp = Cdp(page["webSocketDebuggerUrl"])
            cdp.call("Runtime.enable")
            cdp.call("Emulation.setDeviceMetricsOverride", width=size_w, height=size_h, deviceScaleFactor=1, mobile=False)
            cdp.call("Emulation.setScrollbarsHidden", hidden=True)
            wait_for(lambda: cdp.eval("document.readyState==='complete' && document.body.getAttribute('data-ready')==='1'"), 30, "ready")
            theme_audit.apply_theme(cdp, slug)
            for name, steps in VIEWS:
                # back to a clean Actions page, no modal, before every view
                cdp.eval("document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));document.getElementById('place').innerHTML='';")
                cdp.eval("(document.querySelector('[data-act=\"page\"][data-k=\"actions\"]')||{click(){}}).click()")
                time.sleep(0.2)
                if steps == "place":
                    cdp.eval("document.getElementById('place').innerHTML = LA.placeModal%s" % PLACE_SAMPLE)
                else:
                    for sel in steps:
                        wait_for(lambda: cdp.eval("!!document.querySelector(%s)" % json.dumps(sel)), 5, sel)
                        cdp.eval("document.querySelector(%s).click()" % json.dumps(sel))
                        time.sleep(0.15)
                time.sleep(0.4)
                a = theme_audit.audit(cdp)
                (out / ("%s__%s.png" % (slug, name))).write_bytes(base64.b64decode(cdp.call("Page.captureScreenshot", format="png")["data"]))
                flag = "  <-- CHECK" if a["overflowX"] or a["modalOverflow"] or a["unparsed"] else ""
                bad += 1 if flag else 0
                print("%-30s %-8s %s%s" % (slug, name, theme_audit.fmt(a), flag), flush=True)
            cdp.ws.close()
        finally:
            if hwnd:
                single_instance.post_close(hwnd)
            try:
                proc.wait(timeout=15)
            except Exception:
                proc.kill()
    print("screenshots in", out)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
