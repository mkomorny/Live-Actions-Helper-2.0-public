"""Do Breakdowns' OWN theme picker AND the shell's theme picker survive a full restart of the shell?

    python -m shell_dev.check_breakdowns_theme

Three real shell sessions on one isolated instance (LIVE_ACTIONS_INSTANCE=shellbdt) against
shell_dev.mock_live: the first opens Breakdowns and picks Plasma with the dialog's own button, the
second (a fresh process) must open in Plasma and picks Mono, the third must open in Mono.
Nothing in tools/ is touched; the dialog is only READ and its own controls are clicked.
Its %APPDATA% folder is removed afterwards.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

APP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP))
from shell_dev.capture_shell import Cdp, wait_for      # noqa: E402
from shell_dev.mock_live import MockLive               # noqa: E402
import single_instance                                  # noqa: E402

INSTANCE = "shellbdt"
LISTEN, BRIDGE, CDP_PORT = 25925, 25924, 9336
RESULTS: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((bool(ok), name))
    print(("PASS  " if ok else "FAIL  ") + name + (("  [" + detail + "]") if detail else ""), flush=True)


def session(pick: str | None, env: dict, tmp: Path, shell_pick: str | None = None) -> dict:
    """One shell process: open Breakdowns, report what it shows, optionally pick a theme with ITS picker, close."""
    ready = tmp / "ready.txt"
    ready.unlink(missing_ok=True)
    proc = subprocess.Popen([sys.executable, str(APP / "shell.py"), "--cdp-port", str(CDP_PORT), "--ready-file", str(ready)], cwd=str(APP), env=env)
    hwnd = 0
    out: dict = {}
    try:
        wait_for(ready.exists, 40, "window shown")
        hwnd = int(dict(l.split("=") for l in ready.read_text().split())["hwnd"])
        pages = wait_for(lambda: [t for t in json.load(urllib.request.urlopen("http://127.0.0.1:%d/json" % CDP_PORT)) if t.get("type") == "page"], 20, "page target")
        cdp = Cdp(pages[0]["webSocketDebuggerUrl"])
        cdp.call("Runtime.enable")
        ev = cdp.eval
        wait_for(lambda: ev("document.readyState==='complete' && document.body.getAttribute('data-ready')==='1'"), 30, "page ready")
        wait_for(lambda: ev("document.querySelector('.la-pip').dataset.on==='true'"), 10, "online")
        wait_for(lambda: ev("document.querySelectorAll('.la-track').length") == 10, 10, "tracks")
        theme_href = lambda: (ev("document.getElementById('la-theme').getAttribute('href')") or "").rsplit("/", 1)[-1]
        out["shell_opened_as"] = theme_href()
        if shell_pick:                                   # the SHELL's theme, through the real Preferences picker
            ev("document.querySelector('[data-act=\"settings\"]').click()")
            wait_for(lambda: ev("!!document.querySelector('[data-act=\"pf-theme-toggle\"]')"), 5, "appearance row")
            if ev("document.querySelector('[data-act=\"pf-theme-toggle\"]').getAttribute('aria-expanded')") != "true":
                ev("document.querySelector('[data-act=\"pf-theme-toggle\"]').click()")
            wait_for(lambda: ev("!!document.querySelector('[data-act=\"pf-theme\"][data-slug=%s]')" % json.dumps(shell_pick)), 5, "swatch")
            ev("document.querySelector('[data-act=\"pf-theme\"][data-slug=%s]').click()" % json.dumps(shell_pick))
            wait_for(lambda: theme_href() == shell_pick + ".css", 6, "shell theme applied")
            time.sleep(0.5)                              # let the settings write land before the process is closed
            ev("document.querySelector('[data-act=\"close-settings\"]').click()")
            out["shell_after_pick"] = theme_href()
        ev("document.querySelector('.la-card[data-id=\"breakdowns\"]').click()")
        wait_for(lambda: ev("document.querySelector('.A-right h2') && document.querySelector('.A-right h2').textContent") == "Breakdowns", 4, "inspector")
        ev("document.querySelector('[data-act=\"run\"]').click()")

        def dialogs():
            return [t for t in json.load(urllib.request.urlopen("http://127.0.0.1:%d/json" % CDP_PORT)) if t.get("type") == "page" and t.get("url", "").startswith("file:")]

        d = Cdp(wait_for(dialogs, 25, "dialog window")[0]["webSocketDebuggerUrl"])
        d.call("Runtime.enable")
        wait_for(lambda: d.eval("document.readyState") == "complete", 15, "dialog loaded")
        time.sleep(1.0)
        out["url"] = dialogs()[0]["url"]
        out["opened_as"] = d.eval("document.body.dataset.theme || 'ignite'")
        out["stored"] = d.eval("(() => { try { return localStorage.getItem('breakdowns-theme'); } catch (e) { return 'ERR ' + e.name; } })()")
        if pick:
            d.eval("document.getElementById('themeBtn').click()")
            d.eval("(() => { const w = %s; const r=[...document.querySelectorAll('*')].find(e=>e.children.length===0 && e.textContent.trim().toLowerCase()===w); if (r) r.click(); })()" % json.dumps(pick))
            wait_for(lambda: d.eval("document.body.dataset.theme") == pick, 4, "theme " + pick)
            out["after_pick"] = d.eval("document.body.dataset.theme")
            out["stored_after_pick"] = d.eval("(() => { try { return localStorage.getItem('breakdowns-theme'); } catch (e) { return 'ERR ' + e.name; } })()")
        d.eval("document.getElementById('cancel').click()")
        wait_for(lambda: not dialogs(), 8, "dialog closed")
        d.ws.close()
        cdp.ws.close()
    finally:
        if hwnd:
            single_instance.post_close(hwnd)
        try:
            out["exit"] = proc.wait(timeout=25)
        except subprocess.TimeoutExpired:
            proc.kill()
            out["exit"] = "killed"
    return out


def main() -> int:
    appdata = Path(os.environ["APPDATA"]) / ("Live Actions-" + INSTANCE)
    shutil.rmtree(appdata, ignore_errors=True)
    appdata.mkdir(parents=True, exist_ok=True)
    (appdata / "settings.json").write_text(json.dumps({"listen_port": LISTEN, "bridge_port": BRIDGE}), encoding="utf-8")
    tmp = Path(tempfile.mkdtemp(prefix="la-bdt-"))
    env = dict(os.environ, LIVE_ACTIONS_INSTANCE=INSTANCE)
    mock = MockLive(listen_port=BRIDGE, reply_port=LISTEN).start()
    try:
        s1 = session("plasma", env, tmp, shell_pick="amethyst-dusk")
        print("INFO  session 1:", s1)
        check("session 1: Breakdowns opens in its default theme (Ignite)", s1.get("opened_as") == "ignite")
        check("session 1: its own picker switched it to Plasma", s1.get("after_pick") == "plasma")
        check("session 1: the dialog could write its choice to localStorage", s1.get("stored_after_pick") == "plasma", str(s1.get("stored_after_pick")))
        check("session 1: the shell opens in Riso, and the real picker switches it to Amethyst Dusk", s1.get("shell_opened_as") == "risograph-art-studio.css" and s1.get("shell_after_pick") == "amethyst-dusk.css")
        check("session 1: the shell closed cleanly", s1.get("exit") == 0, str(s1.get("exit")))

        s2 = session("mono", env, tmp)
        print("INFO  session 2:", s2)
        check("session 2 (fresh process): Breakdowns opens in Plasma, the theme chosen last time", s2.get("opened_as") == "plasma", "opened as %s, stored=%s" % (s2.get("opened_as"), s2.get("stored")))
        check("session 2: switching to Mono works", s2.get("after_pick") == "mono")
        check("session 2 (fresh process): the SHELL itself opens in Amethyst Dusk, the kit chosen last time", s2.get("shell_opened_as") == "amethyst-dusk.css", str(s2.get("shell_opened_as")))
        check("session 2: the shell closed cleanly", s2.get("exit") == 0, str(s2.get("exit")))

        s3 = session(None, env, tmp)
        print("INFO  session 3:", s3)
        check("session 3 (fresh process): Breakdowns opens in Mono", s3.get("opened_as") == "mono", "opened as %s, stored=%s" % (s3.get("opened_as"), s3.get("stored")))
        check("session 3: the shell still opens in Amethyst Dusk (the two themes are independent)", s3.get("shell_opened_as") == "amethyst-dusk.css", str(s3.get("shell_opened_as")))
        check("session 3: the shell closed cleanly", s3.get("exit") == 0, str(s3.get("exit")))
    finally:
        mock.stop()
        shutil.rmtree(appdata, ignore_errors=True)
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [n for ok, n in RESULTS if not ok]
    print("\n%d/%d checks passed" % (len(RESULTS) - len(bad), len(RESULTS)))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
