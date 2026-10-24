"""End-to-end check of the REAL shell against shell_dev.mock_live.MockLive (real UDP loopback,
real pywebview js_api, real WebView2), driven through the DevTools protocol.

    python -m shell_dev.e2e_shell

Uses its own isolated instance name (LIVE_ACTIONS_INSTANCE=shelle2e) and ports, so it cannot
touch a running app or the user's settings; its %APPDATA% folder is removed afterwards.
Also records startup time and memory of the real shell (HANDOFF §0b #1).
"""

from __future__ import annotations

import ctypes
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
from shell_dev.mock_llm import MockLLM                 # noqa: E402
import agent_registry                                   # noqa: E402
import single_instance                                  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # chips print check marks; the Windows console is cp1252

INSTANCE = "shelle2e"
LISTEN, BRIDGE, CDP_PORT = 24925, 24924, 9334
RESULTS: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((bool(ok), name))
    print(("PASS  " if ok else "FAIL  ") + name + (("  [" + detail + "]") if detail else ""), flush=True)


def tree_private_mb(pid: int) -> tuple[float, int]:
    """Whole-process-tree private bytes (same method as measure_footprint.py)."""
    try:
        import psutil
    except ImportError:
        return (-1.0, 0)
    root = psutil.Process(pid)
    procs = [root] + root.children(recursive=True)
    total = 0
    for p in procs:
        try:
            total += getattr(p.memory_full_info(), "private", p.memory_info().rss)
        except Exception:
            pass
    return (total / 1048576, len(procs))


def soft(fn, timeout, what):
    """wait_for that reports False instead of raising, so one failed check does not hide the rest."""
    try:
        return wait_for(fn, timeout, what)
    except TimeoutError:
        return False


# -- native windows the dialog tools open (a second pywebview window; native OK/Cancel confirms) ------------------------------

def find_window(title: str, cls: str | None = None) -> int:
    """Top-level visible window with exactly `title` (EnumWindows), 0 if none."""
    user32 = ctypes.windll.user32
    found: list[int] = []
    proc_t = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    def cb(hwnd, _lp):
        if not user32.IsWindowVisible(hwnd):
            return True
        buf = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(hwnd, buf, 256)
        if buf.value != title:
            return True
        if cls:
            cbuf = ctypes.create_unicode_buffer(64)
            user32.GetClassNameW(hwnd, cbuf, 64)
            if cbuf.value != cls:
                return True
        found.append(int(hwnd))
        return True

    user32.EnumWindows(proc_t(cb), 0)
    return found[0] if found else 0


def answer_box(title: str, ok: bool, timeout: float = 10.0) -> str:
    """Press OK / Cancel on the native confirm titled `title` (a #32770 MessageBox). Returns "" or why not."""
    end = time.time() + timeout
    while time.time() < end:
        hwnd = find_window(title, "#32770")
        if hwnd:
            ctypes.windll.user32.PostMessageW(hwnd, 0x0111, 1 if ok else 2, 0)     # WM_COMMAND IDOK / IDCANCEL
            return ""
        time.sleep(0.1)
    return "no confirm titled %r appeared" % title


def dialogs_section(ev, click, mock, cdp_port) -> None:
    """Arrangement Helper, BBenCut and Breakdowns: each opens its UNCHANGED dialog HTML in its own window;
    the dialog's own buttons drive the real handlers; the bridge receives exactly what was confirmed."""

    def targets():
        return [t for t in json.load(urllib.request.urlopen("http://127.0.0.1:%d/json" % cdp_port)) if t.get("type") == "page" and t.get("url", "").startswith("file:")]

    def dialog_cdp():
        t = wait_for(targets, 25, "dialog window target")
        c = Cdp(t[0]["webSocketDebuggerUrl"])
        c.call("Runtime.enable")
        wait_for(lambda: c.eval("document.readyState") == "complete", 15, "dialog loaded")
        time.sleep(1.0)                                # the dialogs wire their buttons a moment after `complete`
        return c

    def open_tool(tool_id, name):
        ev("document.querySelector('.la-card[data-id=\"%s\"]').click()" % tool_id)
        wait_for(lambda: ev("document.querySelector('.A-right h2') && document.querySelector('.A-right h2').textContent") == name, 4, "inspector " + name)
        click('[data-act="run"]')

    def result():
        return ev("document.querySelector('[data-result]').textContent"), ev("document.querySelector('[data-result]').dataset.state")

    def close_dialog(c):
        try:
            c.ws.close()
        except Exception:
            pass
        soft(lambda: not targets(), 8, "dialog window gone")

    runs_before = lambda: len(mock.runs)

    # -- Breakdowns ------------------------------------------------------------------------------
    open_tool("breakdowns", "Breakdowns")
    d = dialog_cdp()
    check("Breakdowns opens in its own window (a second page target)", len(targets()) == 1)
    check("the shell's result box says the dialog is open", soft(lambda: "Audition writes nothing" in result()[0], 4, "status"), result()[0][:80])
    ctx = d.eval("JSON.stringify(window.__CTX__)")
    ctx = json.loads(ctx) if ctx else {}
    check("dialog got the live context (ticked tracks, tempo, 4/4)", ctx.get("hasClip") is True and "Bass" in ctx.get("clipName", "") and ctx.get("tempo") == 128.0 and ctx.get("beatsPerBar") == 4, json.dumps(ctx)[:160])
    check("the dialog is the original design (its own Insert / Cancel / theme button present)", d.eval("!!(document.getElementById('insert') && document.getElementById('cancel') && document.getElementById('themeBtn'))") is True)
    check("no shell theme leaked into it (default Ignite: body has no data-theme)", d.eval("document.body.dataset.theme === undefined") is True)
    d.eval("document.getElementById('themeBtn').click()")
    d.eval("(() => { const r=[...document.querySelectorAll('*')].find(e=>e.children.length===0 && e.textContent.trim()==='Plasma'); if (r) r.click(); })()")
    check("its own theme picker works inside the shell's window", soft(lambda: d.eval("document.body.dataset.theme") == "plasma", 4, "theme plasma"))
    d.eval("document.getElementById('insert').click()")
    check("Insert fill reaches the bridge as a breakdowns run", soft(lambda: any(t == "breakdowns" for t, _ in mock.runs), 6, "breakdowns run"))
    br = next(((t, pl) for t, pl in mock.runs if t == "breakdowns"), (None, {}))[1]
    check("run carries generated notes for the ticked tracks", len(br.get("fields", {}).get("notes", [])) > 0 and [t["key"] for t in br.get("tracks", [])] == ["midi:0", "midi:1", "audio:4"], "notes=%d" % len(br.get("fields", {}).get("notes", [])))
    check("the result box turns Done", soft(lambda: result()[1] == "done", 6, "done"), result()[0][:80])
    check("the dialog window closed itself", soft(lambda: not targets(), 8, "window closed"))
    close_dialog(d)

    open_tool("breakdowns", "Breakdowns")
    d = dialog_cdp()
    n = runs_before()
    print("INFO  Breakdowns' own theme choice on a second open in the same session: %s" % d.eval("document.body.dataset.theme || 'ignite (default)'"))
    d.eval("document.getElementById('cancel').click()")
    check("Cancel closes the window and writes nothing", soft(lambda: not targets(), 8, "closed") and runs_before() == n)
    check("...and the result box says so", soft(lambda: "nothing was written" in result()[0], 4, "cancel msg"), result()[0][:80])
    close_dialog(d)

    open_tool("breakdowns", "Breakdowns")
    d = dialog_cdp()
    hw = find_window("Breakdowns")
    check("the dialog window has a real native title", hw != 0)
    if hw:
        single_instance.post_close(hw)
    check("closing the window with its own X is a cancel too", soft(lambda: not targets(), 8, "x closed") and runs_before() == n and soft(lambda: "nothing was written" in result()[0], 4, "x msg"))
    close_dialog(d)

    # -- BBenCut ---------------------------------------------------------------------------------
    open_tool("bbencut", "BBenCut")
    d = dialog_cdp()
    check("BBenCut opens in its own window", len(targets()) == 1)
    n = runs_before()
    d.eval("document.getElementById('apply').click()")
    check("Apply asks a native confirmation first", answer_box("BBenCut — Confirm Placement", ok=False) == "")
    check("declining places nothing and says cancelled", soft(lambda: "Cancelled" in result()[0], 6, "cancelled"), result()[0][:80])
    check("...and nothing was sent", runs_before() == n)
    close_dialog(d)
    open_tool("bbencut", "BBenCut")
    d = dialog_cdp()
    d.eval("document.getElementById('apply').click()")
    check("Apply asks again", answer_box("BBenCut — Confirm Placement", ok=True) == "")
    check("confirming sends the run to the bridge", soft(lambda: any(t == "bbencut" for t, _ in mock.runs), 8, "bbencut run"))
    bb = next(((t, pl) for t, pl in mock.runs if t == "bbencut"), (None, {}))[1]
    check("run carries the algorithm and slices for the ticked track", bool(bb.get("fields", {}).get("algorithm")) and len(bb.get("fields", {}).get("slices", [])) > 0, "algorithm=%s slices=%d" % (bb.get("fields", {}).get("algorithm"), len(bb.get("fields", {}).get("slices", []))))
    check("result box turns Done", soft(lambda: result()[1] == "done", 6, "bb done"), result()[0][:80])
    close_dialog(d)

    # -- Arrangement Helper ----------------------------------------------------------------------
    mock.call_replies["arrangement_scan"] = {"ok": True, "isEditing": False, "sections": [], "scanCount": 0, "nextId": 0, "startBar": 5}
    mock.call_replies["arrangement_plan"] = {"ok": True, "writeCount": 6, "moved": 0, "sectionCount": 2, "undoStepCount": 6, "fingerprint": {"f": 1}, "remapTrackCount": 3}
    open_tool("arrangement-helper", "Arrangement Helper")
    d = dialog_cdp()
    check("Arrangement Helper scans the Set before opening", any(a == "arrangement_scan" for a, _ in mock.calls))
    scan_call = next((p for a, p in mock.calls if a == "arrangement_scan"), {})
    check("...on the first ticked MIDI track", scan_call.get("trackPath") == "live_set tracks 0", json.dumps(scan_call))
    ctx = json.loads(d.eval("JSON.stringify(window.__CTX__)") or "{}")
    check("dialog is seeded from the scan reply and the live tempo / time signature", ctx.get("startBar") == 5 and ctx.get("beatsPerBar") == 4 and ctx.get("tempo") == 128.0 and len(ctx.get("tracks", [])) == 10, json.dumps({k: ctx.get(k) for k in ("startBar", "beatsPerBar", "tempo")}))
    check("Create waits for at least one section", d.eval("document.getElementById('create-btn').disabled") is True)
    d.eval("(() => { for (const n of ['INTRO', 'DROP']) { document.getElementById('custom-name').value = n; addCustom(); } })()")
    enabled = soft(lambda: d.eval("document.getElementById('create-btn') && !document.getElementById('create-btn').disabled"), 4, "create enabled")
    if enabled:
        d.eval("document.getElementById('create-btn').click()")
        check("Create asks the plan-based confirmation", answer_box("Arrangement Helper — Confirm", ok=True) == "")
        check("plan (read-only) was requested before anything was written", soft(lambda: any(a == "arrangement_plan" for a, _ in mock.calls), 6, "plan"))
        plan_call = next((p for a, p in mock.calls if a == "arrangement_plan"), {})
        check("the plan carries the dialog's sections and the ticked tracks", [x.get("name") for x in plan_call.get("sections", [])] == ["INTRO", "DROP"] and plan_call.get("sectionTrackPath") == "live_set tracks 0", json.dumps({k: plan_call.get(k) for k in ("sectionTrackPath", "tickedTrackPaths", "beatsPerBar")}))
        check("confirming sends the execute run with the plan's fingerprint", soft(lambda: any(t == "arrangement-helper" for t, _ in mock.runs), 8, "ah run") and next(pl for t, pl in mock.runs if t == "arrangement-helper")["fields"].get("fingerprint") == {"f": 1})
        check("result box turns Done", soft(lambda: result()[1] == "done", 6, "ah done"), result()[0][:80])
    else:
        check("Create is available with the default sections", False, "the button stayed disabled")
    close_dialog(d)
    open_tool("arrangement-helper", "Arrangement Helper")
    d = dialog_cdp()
    n = runs_before()
    d.eval("cancel()")
    check("Cancel writes nothing", soft(lambda: not targets(), 8, "ah closed") and runs_before() == n and soft(lambda: "nothing was written" in result()[0], 4, "ah cancel msg"))
    close_dialog(d)
    # offline: no window, honest message
    mock.muted = True
    wait_for(lambda: ev("document.querySelector('.la-pip').dataset.on==='false'"), 9, "offline")
    open_tool("arrangement-helper", "Arrangement Helper")
    check("offline: Arrangement Helper refuses without opening a window", soft(lambda: "offline" in result()[0].lower(), 4, "offline msg") and not targets())
    mock.muted = False
    wait_for(lambda: ev("document.querySelector('.la-pip').dataset.on==='true'"), 9, "online again")


def save_as_dialog(timeout: float = 15.0) -> int:
    """The native Save As opened by "Save to PC" (a #32770 titled "Save As"); 0 if it never appeared."""
    end = time.time() + timeout
    while time.time() < end:
        hwnd = find_window("Save As", "#32770")
        if hwnd:
            return hwnd
        time.sleep(0.1)
    return 0


def save_as_edit(hwnd: int) -> int:
    """The file-name edit box inside a Save As dialog (its only visible Edit control)."""
    user32 = ctypes.windll.user32
    found: list[int] = []
    proc_t = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    def cb(child, _lp):
        buf = ctypes.create_unicode_buffer(32)
        user32.GetClassNameW(child, buf, 32)
        if buf.value == "Edit" and user32.IsWindowVisible(child):
            found.append(int(child))
        return True

    user32.EnumChildWindows(hwnd, proc_t(cb), 0)
    return found[0] if found else 0


def placement_section(cdp, ev, click, mock, out_dir: Path) -> None:
    """Host tools' `destination`: "Add to Live Set" asks for a clip slot in an in-page modal (Riso theme, the Preferences modal's parts),
    "Save to PC" opens the native Save As. A real ffmpeg tone is generated by the real audio_sample handler."""
    user32 = ctypes.windll.user32
    calls = lambda action: [p for a, p in mock.calls if a == action]
    result = lambda: (ev("document.querySelector('[data-result]').textContent"), ev("document.querySelector('[data-result]').dataset.state"))
    logtext = lambda: ev("LA.data.log.map(l => l[2]).join('\\n')")
    modal = lambda: ev("!!document.querySelector('#place .la-modal.la-place')")

    def set_field(fid, value=None, contains=None):
        ev("""(() => { const t = document.querySelector('.A-right [data-fid=%s]');
              if (%s) { const o = [...t.options].find(o => o.text.includes(%s)); t.value = o.value; } else t.value = %s;
              t.dispatchEvent(new Event('input', {bubbles: true})); t.dispatchEvent(new Event('change', {bubbles: true})); })()"""
           % (json.dumps(fid), "true" if contains else "false", json.dumps(contains or ""), json.dumps(value or "")))

    def open_and_run(destination):
        ev("document.querySelector('.la-card[data-id=\"audio-sample\"]').click()")
        wait_for(lambda: ev("document.querySelector('.A-right h2') && document.querySelector('.A-right h2').textContent") == "Audio Sample", 4, "inspector")
        set_field("operation", contains="Tone Generator")
        set_field("tone__duration", "0.3")
        set_field("destination", destination)
        click('[data-act="run"]')

    def finish():
        return soft(lambda: result()[1] in ("done", "error"), 20, "run finished")

    def run_and_finish():
        """Click Run and wait for THIS run to end (the box still shows the previous run's `done` until it starts)."""
        click('[data-act="run"]')
        soft(lambda: result()[1] == "running", 5, "run started")
        return finish()

    def key(name):
        ev("document.dispatchEvent(new KeyboardEvent('keydown', {key: %s, bubbles: true}))" % json.dumps(name))

    slots = [{"index": 0, "has_clip": True, "clip": {"name": "Kick loop"}}, {"index": 1, "has_clip": False},
             {"index": 2, "has_clip": False}, {"index": 3, "has_clip": True, "clip": {}}]
    mock.call_replies["read_track"] = {"ok": True, "session_clips": slots}

    # -- Add to Live Set: an empty slot ---------------------------------------------------------
    open_and_run("Add to Live Set")
    check("Add to Live Set opens the slot picker in the page", soft(modal, 25, "slot picker"))
    check("it is titled for the tool and names the audio track (Vox, not the ticked MIDI ones)",
          "Place Audio Sample" in ev("document.querySelector('#place .la-modal-head').textContent") and "Vox" in ev("document.querySelector('#place .la-lede').textContent"))
    check("it lists every slot of that track", ev("document.querySelectorAll('#place .la-keyrow').length") == 4)
    check("it is built from the Preferences modal's own parts (scrim, modal, head, keyrows, primary + ghost buttons)",
          ev("!!(document.querySelector('#place .la-scrim') && document.querySelector('#place .la-modal-head .la-iconbtn') && document.querySelector('#place .la-check') && document.querySelector('#place .la-btn.primary') && document.querySelector('#place .la-btn.ghost'))") is True)
    check("the first empty slot is preselected", ev("document.querySelector('#place .la-keyrow.on').dataset.i") == "1")
    check("occupied slots show their clip name, or 'occupied'", ev("[...document.querySelectorAll('#place .la-slot-name')].map(n => n.textContent).join('|')") == "“Kick loop”|empty|empty|occupied")
    check("the result box says it is waiting for the choice", soft(lambda: "choose a clip slot" in result()[0] and result()[1] == "running", 4, "waiting"), result()[0][:90])
    check("the Run button is disabled meanwhile", ev("document.querySelector('.A-right [data-act=\"run\"]').disabled") is True)
    check("nothing was placed before the choice", not calls("create_clip"))
    shots = os.environ.get("LA_E2E_SHOTS")
    if shots:
        import base64
        Path(shots).mkdir(parents=True, exist_ok=True)
        (Path(shots) / "place-slot-picker.png").write_bytes(base64.b64decode(cdp.call("Page.captureScreenshot", format="png")["data"]))
    ev("document.querySelector('#place .la-scrim').click()")
    time.sleep(0.4)
    check("clicking the dimmed backdrop does not dismiss it", modal() is True)
    click('#place [data-act="place-ok"]')
    check("Place sends create_clip for that track, slot and the generated file", soft(lambda: calls("create_clip"), 8, "create_clip"))
    cc = (calls("create_clip") or [{}])[0]
    check("...track 4 (Vox), slot 1, an existing .wav", cc.get("track_index") == 4 and cc.get("slot_index") == 1 and str(cc.get("sample_file", "")).endswith(".wav") and Path(cc.get("sample_file", "")).exists(), json.dumps(cc)[:160])
    check("the modal goes away", soft(lambda: modal() is False, 4, "modal gone"))
    finish()
    check("the result box is Done and says where it went", "Placed on Vox (slot 2)." in result()[0] and result()[1] == "done", result()[0][:120])
    check("the Run button is enabled again", ev("document.querySelector('.A-right [data-act=\"run\"]').disabled") is False)

    # -- an occupied slot needs a second click ----------------------------------------------------
    n = len(calls("create_clip"))
    click('[data-act="run"]')
    soft(modal, 25, "slot picker 2")
    ev("document.querySelector('#place [data-act=\"place-pick\"][data-i=\"3\"]').click()")
    check("choosing an occupied slot selects it", soft(lambda: ev("document.querySelector('#place .la-keyrow.on').dataset.i") == "3", 4, "picked 3"))
    click('#place [data-act="place-ok"]')
    check("Place on an occupied slot warns instead of writing", soft(lambda: "click Place again" in ev("document.querySelector('#place [data-place-warn]').textContent") and ev("!document.querySelector('#place [data-place-warn]').hidden"), 4, "warn"))
    check("...and nothing was sent", len(calls("create_clip")) == n and modal() is True)
    ev("document.querySelector('#place [data-act=\"place-pick\"][data-i=\"2\"]').click()")
    check("changing the selection clears the warning", soft(lambda: ev("document.querySelector('#place [data-place-warn]').hidden") is True, 4, "warn cleared"))
    ev("document.querySelector('#place [data-act=\"place-pick\"][data-i=\"3\"]').click()")
    click('#place [data-act="place-ok"]')
    soft(lambda: ev("!document.querySelector('#place [data-place-warn]').hidden"), 4, "warn again")
    check("...and the choice must be confirmed again after re-selecting", len(calls("create_clip")) == n)
    click('#place [data-act="place-ok"]')
    check("the second Place replaces the clip (slot 4)", soft(lambda: len(calls("create_clip")) == n + 1 and calls("create_clip")[-1].get("slot_index") == 3, 8, "second create"))
    finish()
    check("...and the result box is Done", result()[1] == "done" and "slot 4" in result()[0], result()[0][:120])

    # -- skipping ---------------------------------------------------------------------------------
    n = len(calls("create_clip"))
    click('[data-act="run"]')
    soft(modal, 25, "slot picker 3")
    ev("document.querySelector('#place .la-keyrow.on').dispatchEvent(new KeyboardEvent('keydown', {key: 'ArrowDown', bubbles: true}))")
    check("Arrow keys move the choice (empty slot 2 -> 3)", soft(lambda: ev("document.querySelector('#place .la-keyrow.on').dataset.i") == "2", 4, "arrow"))
    check("Escape skips the placement", (key("Escape"), soft(lambda: modal() is False, 4, "escaped"))[1])
    finish()
    check("...the file is kept and the box says so", "Placement skipped." in result()[0] and result()[1] == "done" and len(calls("create_clip")) == n, result()[0][:120])
    click('[data-act="run"]')
    soft(modal, 25, "slot picker 4")
    click('#place [data-act="place-cancel"].ghost')
    check("the Cancel button skips it too", soft(lambda: modal() is False, 4, "cancelled") and finish() and "Placement skipped." in result()[0] and len(calls("create_clip")) == n)

    # -- validation before any question -------------------------------------------------------------
    ev("document.querySelectorAll('.la-track')[4].click()")                 # untick Vox: only MIDI tracks left
    wait_for(lambda: ev("document.querySelectorAll('.la-track.on').length") == 2, 4, "vox unticked")
    run_and_finish()
    check("no ticked audio track: file saved, not placed, no question", "No ticked audio track" in result()[0] and modal() is False, result()[0][:120])
    ev("document.querySelectorAll('.la-track')[4].click()")
    wait_for(lambda: ev("document.querySelectorAll('.la-track.on').length") == 3, 4, "vox ticked")
    mock.muted = True
    wait_for(lambda: ev("document.querySelector('.la-pip').dataset.on==='false'"), 9, "offline")
    run_and_finish()
    check("offline: file saved, not placed, no question", "Bridge offline — file saved" in result()[0] and modal() is False, result()[0][:120])
    mock.muted = False
    wait_for(lambda: ev("document.querySelector('.la-pip').dataset.on==='true'"), 9, "online again")

    # -- Save to PC ---------------------------------------------------------------------------------
    set_field("destination", "Save to PC")
    click('[data-act="run"]')
    hwnd = save_as_dialog()
    check("Save to PC opens the native Save As", hwnd != 0)
    if hwnd:
        finish()
        shown_path = result()[0].split("\n")[-1].strip()
        buf = ctypes.create_unicode_buffer(512)
        for _ in range(50):                                                  # the dialog fills in its file name a moment after it appears (a busy PC read '' once)
            edit = save_as_edit(hwnd)
            if edit:
                user32.SendMessageW(edit, 0x000D, 512, buf)                  # WM_GETTEXT
            if buf.value:
                break
            time.sleep(0.1)
        check("it proposes the generated file's own name", buf.value == Path(shown_path).name and shown_path.startswith(str(out_dir)), "%r vs %s" % (buf.value, shown_path))
        check("the run was already Done while the dialog is open", result()[1] == "done")
        user32.PostMessageW(hwnd, 0x0010, 0, 0)                                 # WM_CLOSE = cancel
        check("cancelling keeps the file where it is and says so", soft(lambda: "Save As canceled" in logtext(), 8, "cancel log") and Path(shown_path).exists())
        click('[data-act="run"]')
        hwnd = save_as_dialog()
        finish()
        dest = out_dir / "kept-by-user.wav"
        if hwnd and save_as_edit(hwnd):
            user32.SendMessageW(save_as_edit(hwnd), 0x000C, 0, str(dest))     # WM_SETTEXT
            user32.PostMessageW(hwnd, 0x0111, 1, 0)                           # WM_COMMAND IDOK
        check("saving to a chosen name copies the file there", soft(lambda: dest.exists() and dest.stat().st_size > 1000, 10, "copy"), str(dest))
        check("the result box and log show the new location", soft(lambda: str(dest) in result()[0] and ("Saved copy to: " + str(dest)) in logtext(), 6, "saved log"), result()[0][-120:])
    else:
        check("cancel / save flows", False, "no Save As dialog")


def genius_section(cdp, ev, click, mock, llm, agent, appdata) -> None:
    """The Genius page against the REAL genius_client, streaming from shell_dev.mock_llm and calling tools
    through the real BridgeClient into shell_dev.mock_live."""
    def js(expr):
        return ev(expr)

    def bots():
        return js("[...document.querySelectorAll('.A-genius .la-bubble.bot')].map(b=>b.textContent)")

    def last_bot(field="textContent"):
        return js("(()=>{const b=[...document.querySelectorAll('.A-genius .la-bubble.bot')].pop();return b?b.%s:null})()" % field)

    def ask(text):
        js("(()=>{const t=document.querySelector('[data-genius-input]');t.focus();t.value=%s;t.dispatchEvent(new Event('input',{bubbles:true}));"
           "t.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true,cancelable:true}));})()" % json.dumps(text))

    def idle():
        return js("!!document.querySelector('[data-genius-btn]') && document.querySelector('[data-genius-btn]').dataset.act==='genius-send'")

    click('[data-act="page"][data-k="genius"]')
    check("Genius page opens with no track panel", soft(lambda: js("!!document.querySelector('.A-genius') && !document.querySelector('.A-left')"), 4, "genius page"))
    check("greeting bubble is shown", "Genius" in (last_bot() or ""))
    check("header shows the model and an agent switcher", soft(lambda: js("(document.querySelector('select.la-model-select')||{}).value")=="e2e-model", 4, "model picker") and js("!!document.querySelector('select.la-agent-select')"))
    check("the key picker lists key names only, grouped by provider, beside a models-only picker",
          js("(()=>{const k=document.querySelector('select.la-key-select'),m=document.querySelector('select.la-model-select');"
             "return !!k && k.querySelectorAll('optgroup').length===1 && k.options.length===1 && !k.options[0].textContent.includes('e2e-model')"
             " && !m.querySelector('optgroup') && [...m.options].filter(o=>!o.disabled).every(o=>o.value.startsWith('e2e-model'))})()"))
    # -- "Show thinking": offered only for a reasoning model (or once reasoning has streamed), and it hides think parts --
    check("no Show thinking box for a model that does not think", js("!document.querySelector('.la-think-toggle') && window.LA.data.prefs.modelThinks===false && window.LA.data.prefs.showThinking===true"))
    check("a reasoning model, or reasoning already in the chat, gets the box",
          js("(()=>{const L=window.LA,P=L.data.prefs,G=L.data.genius;P.modelThinks=true;const a=L.thinkToggle();P.modelThinks=false;"
             "G.messages.push({id:'t-e2e',role:'bot',state:'done',parts:[{kind:'think',text:'x'}]});const b=L.thinkToggle();G.messages.pop();"
             "return a.includes('data-change=\"genius-think\"') && a.includes(' checked') && b.includes('genius-think') && L.thinkToggle()===''})()"))
    check("unticking it drops the reasoning from a reply and keeps the answer",
          js("(()=>{const L=window.LA,P=L.data.prefs,m={id:'t',role:'bot',state:'done',parts:[{kind:'think',text:'SECRET-THOUGHT'},{kind:'text',text:'the answer'}]};"
             "const on=L.botParts(m);P.showThinking=false;const off=L.botParts(m);"
             "const wait=L.botParts({id:'t',role:'bot',state:'streaming',parts:[{kind:'think',text:'SECRET-THOUGHT'}]});P.showThinking=true;"
             "return on.includes('SECRET-THOUGHT') && !off.includes('SECRET-THOUGHT') && off.includes('the answer') && !wait.includes('SECRET-THOUGHT') && wait.includes('Thinking')})()"))
    # -- "New Custom Instructions" lives at the bottom of the preset dropdown and saves from a dialog --
    pick_ci = lambda v: js("(()=>{const s=document.querySelector('select.la-ci-select');s.value=%s;s.dispatchEvent(new Event('change',{bubbles:true}))})()" % json.dumps(v))
    def presets():
        for _ in range(40):                                   # the app may be mid-write (same retry as prefs_section's cfg)
            try:
                return json.loads((appdata / "settings.json").read_text(encoding="utf-8")).get("custom_instructions", [])
            except (OSError, json.JSONDecodeError):
                time.sleep(0.05)
        return []
    check("the preset dropdown is there before any preset exists, ending in New Custom Instructions",
          js("(()=>{const o=document.querySelector('select.la-ci-select').options;return o[0].textContent==='No custom instructions' && o[o.length-1].value==='__new__'})()"))
    pick_ci("__new__")
    check("picking it opens the dialog and leaves the dropdown on the real choice",
          soft(lambda: js("!!document.querySelector('#cinew .la-modal') && document.querySelector('select.la-ci-select').value===''"), 4, "ci dialog"))
    click('[data-act="ci-new-save"]')
    check("a nameless preset is refused in the dialog", soft(lambda: js("(document.querySelector('#cinew .la-err')||{}).textContent")=="Give it a name first.", 4, "ci name") and presets() == [])
    js("(()=>{for (const [k,v] of [['name','E2E rules'],['body','Keep replies short.']]){const t=document.querySelector('#cinew [data-ci-new=\"'+k+'\"]');t.value=v;t.dispatchEvent(new Event('input',{bubbles:true}));}})()")
    click('[data-act="ci-new-save"]')
    check("saving closes the dialog, selects the new preset and persists it",
          soft(lambda: js("!document.querySelector('#cinew .la-modal') && document.querySelector('select.la-ci-select').selectedOptions[0].textContent==='E2E rules'"), 6, "ci saved")
          and [(p.get("name"), p.get("body")) for p in presets()] == [("E2E rules", "Keep replies short.")])
    pick_ci("")
    check("switching back to none keeps the saved preset in the list",
          soft(lambda: js("document.querySelector('select.la-ci-select').value===''"), 4, "ci none") and js("document.querySelector('select.la-ci-select').options.length")==4 and len(presets()) == 1)
    check("no API-key warning when a key is configured", js("!document.querySelector('.A-gnote .la-note')"))

    # -- plain streamed reply (reasoning + content) --------------------------------------
    ask("hello")
    check("your message appears as a bubble", soft(lambda: js("[...document.querySelectorAll('.A-genius .la-bubble.user .la-msg-text')].some(n=>n.textContent==='hello')"), 4, "user bubble"))
    check("Send becomes Stop while Genius is answering", soft(lambda: js("document.querySelector('[data-genius-btn]').dataset.act==='genius-stop'"), 4, "busy button"))
    # Sample fast: the mock streams 4 chunks 0.15 s apart, so a 30 ms sampler must catch partial text.
    seen: list[str] = []
    end_at = time.time() + 8
    final = "Hello from the mock."
    while time.time() < end_at:
        t = js("(()=>{const b=[...document.querySelectorAll('.A-genius .la-bubble.bot')].pop();const n=b&&[...b.querySelectorAll(':scope > .la-msg-text')].pop();return n?n.textContent:''})()") or ""
        if t and (not seen or seen[-1] != t):
            seen.append(t)
        if t == final:
            break
        time.sleep(0.03)
    check("the reply streams in piece by piece and ends as the full text",
          bool(seen) and seen[-1] == final and any(0 < len(t) < len(final) for t in seen), "states seen: %s" % seen)
    check("Stop turns back into Send when done", soft(idle, 4, "idle"))
    # -- the user's report (v1.0.69): chat text must be selectable so it can be copied ---------------------------
    # pywebview's text_select=False injects `body{user-select:none}`; app.css opts the reading surfaces back in.
    check("chat text is selectable (computed user-select: text)", js("(()=>{const n=[...document.querySelectorAll('.A-genius .la-bubble.bot .la-msg-text')].pop();return !!n && getComputedStyle(n).userSelect==='text'})()"))
    check("buttons stay unselectable (user-select: none)", js("getComputedStyle(document.querySelector('.A-genius .la-btn')).userSelect==='none'"))
    box = js("(()=>{const n=[...document.querySelectorAll('.A-genius .la-bubble.bot > .la-msg-text')].pop();const r=n.getBoundingClientRect();return {x:r.left+Math.min(40,r.width/2),y:r.top+r.height/2}})()")
    for n in (1, 2, 3):                                       # a real mouse triple-click, the gesture that selects a paragraph
        for typ in ("mousePressed", "mouseReleased"):
            cdp.call("Input.dispatchMouseEvent", type=typ, x=box["x"], y=box["y"], button="left", clickCount=n)
    picked = soft(lambda: (js("String(getSelection())") or "").strip() == final, 4, "selection")
    check("a real triple-click on a reply selects exactly that reply's text, ready to copy", picked, "selected: %r" % js("String(getSelection())"))
    js("getSelection().removeAllRanges()")
    check("reasoning is kept in a collapsed Thinking block", js("(()=>{const d=[...document.querySelectorAll('.A-genius .la-bubble.bot')].pop().querySelector('details.la-think');return !!d && !d.open && d.textContent.includes('Thinking it over.')})()"))
    check("the composer was cleared after sending", js("document.querySelector('[data-genius-input]').value")=="")

    # -- tool calls through the real bridge ---------------------------------------------------
    ask("please use the tools")
    check("tool-call chip goes running -> done", soft(lambda: js("[...document.querySelectorAll('.A-genius .la-call')].some(c=>c.textContent==='live_read_set ✓')"), 10, "chip ok"))
    check("the tool call reached the (mock) Live device", bool(mock.calls), str([c[0] for c in mock.calls]))
    check("narration before the tool call and the final answer are both kept",
          soft(lambda: "The Set has 10 tracks." in (last_bot() or "") and "Let me check the Set." in (last_bot() or ""), 8, "tool answer"), (last_bot() or "")[:120])
    soft(idle, 4, "idle after tools")

    # -- Thinking log drawer (v1.9.0): the session's reasoning + actions, beside Console log ------
    tlog = "(document.querySelector('.la-thinklog')||{textContent:''}).textContent"
    check("status bar offers Copy, Console log and Thinking log, in that order",
          js("[...document.querySelectorAll('.la-statusbar .la-btn')].map(b=>b.dataset.act).join('|')")=="copy-log|console|thinking"
          and js("document.querySelector('[data-act=\"thinking\"]').textContent.trim()")=="Thinking log")
    click('[data-act="thinking"]')
    check("Thinking log opens and its button turns into Hide thinking", soft(lambda: js("!!document.querySelector('.la-thinklog') && document.querySelector('[data-act=\"thinking\"]').textContent.trim()==='Hide thinking'"), 4, "thinking drawer"))
    check("Thinking log lists the prompt, the reasoning and the action taken, in order",
          js("(()=>{const t=%s;const a=t.indexOf('hello'),b=t.indexOf('Thinking it over.'),c=t.indexOf('live_read_set ✓');return a>=0&&b>a&&c>b})()" % tlog), (js(tlog) or "")[:200])
    check("Thinking log leaves the replies to the chat", "Hello from the mock." not in (js(tlog) or ""))
    ask("please use the tools")
    check("Thinking log updates live while it is open", soft(lambda: (js(tlog) or "").count("live_read_set ✓")==2, 10, "live thinking log"), (js(tlog) or "")[-200:])
    soft(idle, 4, "idle after tools (thinking log open)")
    click('[data-act="console"]')
    check("opening Console log closes the Thinking log", soft(lambda: js("!document.querySelector('.la-thinklog') && !!document.querySelector('.la-console')"), 4, "drawers swap"))
    click('[data-act="console"]')
    check("both drawers closed again", soft(lambda: js("!document.querySelector('.la-console')"), 4, "drawers closed"))

    # -- model output is untrusted: markdown renders, HTML never runs -----------------------------
    ask("show me markdown")
    check("markdown reply: bold, inline code and a fenced block render",
          soft(lambda: js("(()=>{const b=[...document.querySelectorAll('.A-genius .la-bubble.bot')].pop();return !!b && !!b.querySelector('b') && !!b.querySelector('code') && !!b.querySelector('pre.la-code')})()"), 8, "markdown"))
    soft(idle, 4, "idle after markdown")
    check("raw HTML in a reply is shown as text, never executed",
          js("(()=>{const b=[...document.querySelectorAll('.A-genius .la-bubble.bot')].pop();return !b.querySelector('script') && !b.querySelector('img') && !window.__pwned && b.querySelector('pre.la-code').textContent.includes(\"print('<b>hi</b>')\") && !b.querySelector('pre b') && b.textContent.includes('<script>')})()"))
    shots = os.environ.get("LA_E2E_SHOTS")
    if shots:
        import base64
        Path(shots).mkdir(parents=True, exist_ok=True)
        (Path(shots) / "genius-markdown.png").write_bytes(base64.b64decode(cdp.call("Page.captureScreenshot", format="png")["data"]))

    # -- error path -----------------------------------------------------------------------------
    ask("this will fail")
    check("a provider error is shown in the bubble and the chat stays usable",
          soft(lambda: "Error: API 500" in (last_bot() or ""), 8, "error shown") and soft(idle, 4, "idle after error"))

    # -- Stop ------------------------------------------------------------------------------------
    n_req = len(llm.requests)
    ask("go slow please")
    soft(lambda: "word2" in (last_bot() or ""), 8, "slow stream")
    click('[data-act="genius-stop"]')
    check("Stop ends the turn at once and says so", soft(idle, 3, "stop") and soft(lambda: "■ Stopped" in (last_bot() or ""), 3, "stopped label"))
    frozen = last_bot()
    time.sleep(1.0)
    check("nothing more is appended after Stop", last_bot() == frozen)
    ask("hello again")
    check("a new question works right after Stop", soft(lambda: "Hello from the mock." in (last_bot() or ""), 8, "post-stop reply"))
    soft(idle, 4, "idle")

    # -- typing survives pushes; drafts survive page switches ------------------------------------
    ask("go slow please")
    soft(lambda: "word1" in (last_bot() or ""), 8, "streaming again")
    js("(()=>{const t=document.querySelector('[data-genius-input]');t.value='half-typed draft';t.dispatchEvent(new Event('input',{bubbles:true}));})()")
    time.sleep(0.8)
    check("a half-typed draft survives streaming pushes", js("document.querySelector('[data-genius-input]').value")=="half-typed draft")
    click('[data-act="genius-stop"]')
    soft(idle, 3, "stopped")
    click('[data-act="page"][data-k="actions"]')
    click('[data-act="page"][data-k="genius"]')
    check("the draft survives switching pages", soft(lambda: js("(document.querySelector('[data-genius-input]')||{}).value")=="half-typed draft", 4, "draft restored"))
    js("(()=>{const t=document.querySelector('[data-genius-input]');t.value='';t.dispatchEvent(new Event('input',{bubbles:true}));})()")

    # -- prompt pill -------------------------------------------------------------------------------
    before = len(llm.requests)
    click('[data-act="genius-pill"][data-i="2"]')
    check("a prompt pill sends its prompt", soft(lambda: len(llm.requests) > before, 6, "pill request")
          and "What key and mode is my Set in?" in json.dumps(llm.requests[-1]["messages"][-1]))
    soft(idle, 8, "idle after pill")

    # -- agent switcher ------------------------------------------------------------------------------
    js("(()=>{const s=document.querySelector('select.la-agent-select');s.value=%s;s.dispatchEvent(new Event('change',{bubbles:true}));})()" % json.dumps(agent["slug"]))
    check("switching agent posts a note and persists the choice",
          soft(lambda: js("[...document.querySelectorAll('.A-genius .la-sys')].some(n=>n.textContent===%s)" % json.dumps("Switched to %s." % agent["title"])), 4, "switch note")
          and json.loads((appdata / "settings.json").read_text(encoding="utf-8")).get("active_agent") == agent["slug"])

    # -- reload = a fresh snapshot rebuilds the same conversation --------------------------------------
    count = js("document.querySelectorAll('.A-genius .la-bubble, .A-genius .la-sys').length")
    js("location.reload()")
    time.sleep(0.5)
    soft(lambda: js("document.readyState==='complete' && document.body.getAttribute('data-ready')==='1'"), 30, "reload ready")
    click('[data-act="page"][data-k="genius"]')
    check("after a page reload the conversation comes back from Python", soft(lambda: js("document.querySelectorAll('.A-genius .la-bubble, .A-genius .la-sys').length")==count, 6, "restored"), "%s bubbles" % count)

    # -- clear ------------------------------------------------------------------------------------------
    click('[data-act="genius-clear"]')
    check("Clear chat leaves just the greeting", soft(lambda: js("document.querySelectorAll('.A-genius .la-bubble').length")==1, 4, "cleared"))
    click('[data-act="page"][data-k="actions"]')


def confirm_section(ev, click, appdata: Path, tmp: Path) -> None:
    """v1.2.0: Genius asks before it spends the user's API credit.

    Runs here, not inside tts_section, for two reasons: prefs_section deletes the last API key
    (so no Genius turn can run after it) and activates an agent (whose tool filter would refuse
    the call before the spend guard was ever reached). The TTS profile is created and removed
    through the real save_tts prefs op, so the later sections still start from none.

    The mock LLM answers anything containing "vocal" with a real live_tts_vocal tool call, and
    run_shell_fake_tts.py answers Cartesia's endpoint itself -- so an APPROVED run is a real trip
    through tts_vocal.run and ffmpeg with nothing sent to Cartesia."""
    reqs_file = tmp / "tts-requests.jsonl"
    reqs = lambda: reqs_file.read_text(encoding="utf-8").splitlines() if reqs_file.exists() else []
    cmodal = lambda: ev("!!document.querySelector('#confirm .la-modal.la-confirm')")
    rows = lambda: ev("(()=>{const n=document.querySelector('#confirm .la-crows');return n?n.textContent:''})()")
    last_bot = lambda: ev("(()=>{const b=[...document.querySelectorAll('.A-genius .la-bubble.bot')].pop();return b?b.textContent:''})()") or ""
    idle = lambda: ev("!!document.querySelector('[data-genius-btn]') && document.querySelector('[data-genius-btn]').dataset.act==='genius-send'")

    def ask(text):
        ev("(()=>{const t=document.querySelector('[data-genius-input]');t.focus();t.value=%s;"
           "t.dispatchEvent(new Event('input',{bubbles:true}));"
           "t.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true,cancelable:true}));})()" % json.dumps(text))

    def cfg():
        for _ in range(40):
            try:
                return json.loads((appdata / "settings.json").read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                time.sleep(0.05)
        return json.loads((appdata / "settings.json").read_text(encoding="utf-8"))

    def set_profiles(profiles):
        # save_tts fires the catalog hook, which re-renders and drops the page back to Actions --
        # so this has to happen BEFORE navigating to Genius, not after.
        ev("window.pywebview.api.prefs('save_tts', {profiles: %s})" % json.dumps(profiles))

    # genius_section left an agent active. Persona filtering refuses a tool that agent does not
    # have BEFORE the spend guard is reached, so this section would be testing the wrong gate.
    ev("window.pywebview.api.genius_set_agent('')")
    soft(lambda: (ev("(window.LA.data.genius.agent||{}).slug") or "") == "", 6, "stock genius")

    set_profiles([{"name": "Approval e2e", "provider": "cartesia", "key_mode": "typed",
                   "api_key": "cart-e2e-approval-key", "voice_id": "e2e-voice-approve"}])
    check("a TTS profile is what makes the vocal tool available at all",
          soft(lambda: len(cfg().get("tts_profiles") or []) == 1, 8, "profile saved"),
          json.dumps(cfg().get("tts_profiles"))[:120])

    click('[data-act="page"][data-k="genius"]')
    soft(lambda: ev("!!document.querySelector('[data-genius-input]')"), 6, "genius composer")

    before = len(reqs())
    ask("make me a vocal")
    opened = soft(cmodal, 25, "confirm modal")
    check("a paid TTS tool call puts an approval modal in front of the user", opened,
          "" if opened else "agent=%r page=%r input=%r msgs=%r busy=%r tts=%r bot=%r log=%r" % (
              ev("(window.LA.data.genius.agent||{}).slug"),
              ev("document.querySelector('.la-nav .on') && document.querySelector('.la-nav .on').dataset.k"),
              ev("!!document.querySelector('[data-genius-input]')"),
              ev("(window.LA.data.genius.messages||[]).length"),
              ev("window.LA.data.genius.busy"),
              ev("JSON.stringify((window.LA.data.prefs||{}).tts||null)"),
              last_bot()[-120:],
              ev("window.LA.data.log.slice(-4).map(l=>l[2]).join(' | ')")))
    check("the modal shows the exact text, profile and provider being paid for",
          "I am King America" in rows() and "cartesia" in rows(), rows()[:160])
    check("it is built from the same modal parts as the slot picker",
          ev("!!(document.querySelector('#confirm .la-scrim') && document.querySelector('#confirm .la-modal-head .la-iconbtn')"
             " && document.querySelector('#confirm .la-check') && document.querySelector('#confirm .la-btn.primary')"
             " && document.querySelector('#confirm .la-btn.ghost'))") is True)
    check("nothing is generated while the question is still open", len(reqs()) == before)

    click('[data-act="confirm-cancel"]')
    check("declining generates nothing at all",
          soft(lambda: idle() and len(reqs()) == before, 20, "declined"), "%d request(s)" % (len(reqs()) - before))
    check("...and Genius is told the user declined, so it reports instead of retrying",
          "declined" in last_bot(), last_bot()[-160:])

    ask("another vocal please")
    soft(cmodal, 25, "confirm modal again")
    click('[data-act="confirm-remember"]')
    check("the session checkbox can be ticked",
          ev("document.querySelector('#confirm .la-keyrow').classList.contains('on')"))
    click('[data-act="confirm-ok"]')
    check("approving runs the real pipeline: one request, through ffmpeg to a WAV",
          soft(lambda: idle() and len(reqs()) == before + 1, 40, "approved run"),
          "%d request(s)" % (len(reqs()) - before))
    check("Genius is handed the real path and the REAL duration, not a claimed one",
          "TTS-Sample" in last_bot() and "actual duration" in last_bot(), last_bot()[-200:])

    ask("one more vocal")
    check("\"don't ask again this session\" lets the next one straight through",
          soft(lambda: idle() and "TTS-Sample" in last_bot(), 40, "suppressed run"), last_bot()[-120:])
    check("...and it really was suppressed, not answered quickly", ev("!document.querySelector('#confirm .la-modal')"))
    check("...and it cost nothing: the identical text came back from tts_vocal's cache",
          len(reqs()) == before + 1, "%d request(s) for 2 approved generations" % (len(reqs()) - before))

    # -- put it back the way the later sections expect ------------------------------------------
    ev("window.pywebview.api.genius_clear()")
    set_profiles([])
    soft(lambda: (cfg().get("tts_profiles") or []) == [], 8, "profile removed")
    reqs_file.write_text("", encoding="utf-8")   # tts_section counts requests from an empty log
    click('[data-act="page"][data-k="actions"]')


def prefs_section(cdp, ev, click, llm, agent, appdata) -> None:
    """Preferences against the real shell: every control is a real js_api round trip, and settings.json on disk is
    the source of truth for what was persisted. Provider detection and TTS probes hit fixed public endpoints, so
    they are covered by test_shell_prefs with fakes; the key test and model list follow api_base (the mock LLM)."""
    js = ev
    def cfg():
        # The app replaces settings.json atomically; a read can land in that instant (and, on Windows, a read can in turn
        # make the app's rename wait -- settings_store retries that), so retry briefly rather than crash the run.
        for _ in range(40):
            try:
                return json.loads((appdata / "settings.json").read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                time.sleep(0.05)
        return json.loads((appdata / "settings.json").read_text(encoding="utf-8"))

    def setv(sel, value, event="change"):
        # Regions re-render on the next animation frame; a missing element would otherwise fail silently (eval swallows the error).
        soft(lambda: js("!!document.querySelector(%s)" % json.dumps(sel)), 4, "element " + sel)
        js("(()=>{const t=document.querySelector(%s);t.focus();t.value=%s;t.dispatchEvent(new Event('input',{bubbles:true}));%s})()"
           % (json.dumps(sel), json.dumps(value), "t.dispatchEvent(new Event('change',{bubbles:true}));" if event == "change" else ""))

    def text(sel):
        return js("(document.querySelector(%s)||{textContent:''}).textContent" % json.dumps(sel))

    def has(sel):
        return js("!!document.querySelector(%s)" % json.dumps(sel))

    def shot(name, scroll_to=None):
        d = os.environ.get("LA_E2E_SHOTS")
        if not d:
            return
        import base64
        if scroll_to:
            js("document.querySelector(%s).scrollIntoView({block:'start'})" % json.dumps(scroll_to))
            time.sleep(0.3)
        Path(d).mkdir(parents=True, exist_ok=True)
        (Path(d) / (name + ".png")).write_bytes(base64.b64decode(cdp.call("Page.captureScreenshot", format="png")["data"]))

    click('[data-act="settings"]')
    check("gear opens the Preferences modal", soft(lambda: has(".la-modal .la-settings"), 4, "modal"))
    check("Appearance starts collapsed and names the current theme", js("(()=>{const c=document.querySelector('.la-collapsible');return c.dataset.open==='false' && !c.querySelector('.la-swatches') && c.querySelector('.la-tag').textContent==='Riso Art Studio' && c.querySelector('.la-collapse-n').textContent==='11 themes'})()"))
    click('[data-act="pf-theme-toggle"]')
    check("expanding shows all eleven kits, Riso selected", soft(lambda: js("document.querySelectorAll('.la-swatch').length")==11 and js("[...document.querySelectorAll('.la-swatch.on')].map(b=>b.dataset.slug).join()")=="risograph-art-studio", 4, "swatches"))
    click('[data-act="pf-theme"][data-slug="risograph-art-studio"]')
    check("picking a theme is saved to settings.json", soft(lambda: cfg().get("theme") == "risograph-art-studio", 4, "theme saved"))
    click('[data-act="pf-theme-toggle"]')

    # -- ports: validated in Python, restart flagged -------------------------------------------------
    setv('[data-pf="listen"]', "abc")
    check("a bad port is refused with a message and nothing is saved", soft(lambda: "whole numbers" in text(".la-settings .la-field small.la-err"), 4, "port error") and cfg()["listen_port"] == LISTEN)
    setv('[data-pf="listen"]', str(LISTEN + 7))
    check("a good port is saved and a restart is asked for", soft(lambda: cfg()["listen_port"] == LISTEN + 7 and has(".la-restart"), 4, "port saved"))
    setv('[data-pf="listen"]', str(LISTEN))
    check("putting it back clears the restart note", soft(lambda: not has(".la-restart"), 4, "restart cleared"))

    # -- key vault ---------------------------------------------------------------------------------------
    check("the saved key is shown masked, never in full", js("document.querySelector('.la-keyrow.on .la-muted').textContent")=="••••••••" and "e2e-key" not in js("document.documentElement.outerHTML"))
    click('[data-act="pf-add-toggle"]')
    check("Add key opens the form", soft(lambda: has('[data-pf="nk.key"]'), 4, "add form"))
    shot("prefs-addkey", ".la-subpanel")
    second = "sk-e2e-second-key-123456"
    setv('[data-pf="nk.key"]', second, event="input")
    setv('[data-pf="nk.label"]', '<img src=x onerror="window.__pwned=1"> Second', event="input")
    setv('[data-pf="nk.provider"]', "openai")
    setv('[data-pf="nk.base"]', llm.base_url, event="input")
    setv('[data-pf="nk.model"]', "e2e-model-2", event="input")
    click('[data-act="pf-save-key"]')
    check("Save key adds a row, makes it active and persists it", soft(lambda: js("[...document.querySelectorAll('.la-keygroup .la-collapse-n')].reduce((n,x)=>n+parseInt(x.textContent),0)")==2 and has('.la-keygroup[data-open="true"] .la-keyrow.on'), 4, "second key")   # keys sit in per-provider groups; the active key's group is open
          and cfg()["api_key"] == second and cfg()["model"] == "e2e-model-2" and cfg()["api_base"] == llm.base_url)
    check("the new key is masked in the page and a hostile label is only text",
          second not in js("document.documentElement.outerHTML") and not has(".la-keyrow img") and not js("window.__pwned") and "<img" in text(".la-keyrow.on b"))

    click('.la-keyrow.on [data-act="pf-del-key"]')
    check("delete asks first (a key cannot be recovered)", soft(lambda: has('.la-keyrow.on .la-row-x.warn'), 3, "confirm state") and len(cfg()["api_keys"]) == 2)   # regions re-render on the next frame
    click('.la-keyrow.on [data-act="pf-del-key"]')
    check("confirming removes it, and the deleted key stops being used", soft(lambda: len(cfg()["api_keys"]) == 1 and cfg()["api_key"] == "", 4, "deleted"))
    click('.la-keyrow[data-act="pf-use-key"]')
    check("clicking a saved key makes it the active one", soft(lambda: cfg()["api_key"] == "e2e-key", 4, "reactivated"))
    check("Test key succeeds through the real request path", (click('[data-act="pf-test"]') or True) and soft(lambda: "Success: ok" in text('.la-result[data-state="done"]'), 8, "key test"))

    # -- rename: the pencil swaps the name for a box; the row is not clickable meanwhile --
    kid = cfg()["api_keys"][0]["id"]
    click('.la-keyrow.on [data-act="pf-rename-key"]')
    check("the pencil opens a name box in the row", soft(lambda: has('[data-pf="keyname:%s"]' % kid) and not has('.la-keygroup .la-keyrow.on[data-act]'), 4, "rename box"))
    setv('[data-pf="keyname:%s"]' % kid, "   ")
    check("an empty name is refused and nothing is saved", soft(lambda: "Give the key a name." in text(".la-keyrow.on small.la-err"), 4, "rename error") and cfg()["api_keys"][0]["label"] != "")
    setv('[data-pf="keyname:%s"]' % kid, "Renamed e2e key")
    check("a new name is saved, shown in the row and in the chat's key picker, and the key itself is untouched",
          soft(lambda: cfg()["api_keys"][0]["label"] == "Renamed e2e key" and text(".la-keyrow.on b") == "Renamed e2e key", 4, "renamed")
          and cfg()["api_keys"][0]["api_key"] == "e2e-key" and cfg()["api_key"] == "e2e-key" and not has('[data-pf^="keyname:"]')
          and js("window.LA.keySelect().includes('Renamed e2e key')"))
    check("a key row carries no model tag", not has(".la-keyrow[data-act=\"pf-use-key\"] .la-tag"))
    click('[data-act="pf-refresh-models"]')
    check("Refresh models lists the endpoint's chat models", soft(lambda: js("[...document.querySelectorAll('[data-pf=\"model\"] option')].map(o=>o.value).join(',')")=="e2e-model,e2e-model-2", 8, "models"),
          js("[...document.querySelectorAll('[data-pf=\"model\"] option')].map(o=>o.value).join(',')"))
    setv('[data-pf="model"]', "e2e-model-2")
    check("choosing a model saves it for the active key", soft(lambda: cfg()["model"] == "e2e-model-2" and cfg()["api_keys"][0]["model"] == "e2e-model-2", 4, "model saved"))
    check("the Genius header is told about the new model", soft(lambda: js("window.LA.data.genius.model")=="e2e-model-2", 4, "genius model"))

    # -- agents --------------------------------------------------------------------------------------------
    check("Agents lists Stock Genius and the enabled agent", js("document.querySelectorAll('.la-keyrow[data-act=\"pf-pick-agent\"]').length")==2)
    click('[data-act="pf-agent-open"]')
    check("expanding an agent loads its tool groups", soft(lambda: js("document.querySelectorAll('.la-tool input').length")>20, 6, "tool list"))
    shot("prefs-agent", ".la-toolgroup")
    row = '.la-keyrow[data-slug="%s"] .la-muted' % agent["slug"]
    on0 = int(text(row).split(" of ")[0])
    first = js("(()=>{const i=document.querySelector('.la-tool input');return {name:i.dataset.name,on:i.checked}})()")
    js("document.querySelector('.la-tool input').click()")
    check("toggling one tool is saved for that agent and moves the count by one",
          soft(lambda: cfg()["agent_tool_prefs"].get(agent["slug"], {}).get(first["name"]) == (not first["on"]), 4, "tool saved")
          and soft(lambda: int(text(row).split(" of ")[0]) == on0 + (-1 if first["on"] else 1), 4, "count"), "%s -> %s" % (first, text(row)))
    click('[data-act="pf-agent-group"][data-on="0"]')
    check("a group's None switches all its tools off", soft(lambda: js("[...document.querySelectorAll('.la-toolgroup')][0].querySelectorAll('input:checked').length")==0, 4, "group none"))
    click('.la-keyrow[data-act="pf-pick-agent"][data-slug="%s"]' % agent["slug"])
    check("picking an agent row makes it the active one (and Genius follows)", soft(lambda: cfg().get("active_agent") == agent["slug"], 4, "agent active"))
    click('[data-act="pf-agent-remove"]')
    check("Remove takes the agent out and falls back to stock Genius", soft(lambda: cfg()["enabled_agents"] == [] and cfg().get("active_agent") == "", 4, "agent removed"))
    check("a removed agent is offered again in the picker", soft(lambda: has('select[data-pf="agentPick"]'), 4, "picker"))
    click('[data-act="pf-agent-enable"]')
    defaults = agent_registry.default_tool_map(agent_registry.load_agent({}, agent["slug"]))
    check("Enable agent adds it back with the agent's own default tool set", soft(lambda: cfg()["enabled_agents"] == [agent["slug"]] and cfg()["agent_tool_prefs"].get(agent["slug"]) == defaults, 4, "enabled"))

    # -- folders: drafts survive re-renders, paths persist, the catalog reloads ------------------------------
    setv('[data-pf="path:samples_dir"]', "Z:\\draft-not-committed", event="input")
    click('[data-act="pf-theme-toggle"]'); click('[data-act="pf-theme-toggle"]')
    check("half-typed folder text survives a re-render", js("document.querySelector('[data-pf=\"path:samples_dir\"]').value")=="Z:\\draft-not-committed")
    setv('[data-pf="path:samples_dir"]', "Z:\\no\\such\\place")
    check("a folder that does not exist is saved with a warning", soft(lambda: cfg()["samples_dir"] == "Z:\\no\\such\\place" and "does not exist" in (js("(document.querySelector('[data-pf=\"path:samples_dir\"]').closest('.la-field').querySelector('small')||{}).textContent") or ""), 4, "path saved"))
    empty = tempfile.mkdtemp(prefix="la-e2e-tools-")
    n_before = js("document.querySelectorAll('.A-grid .la-card').length")
    setv('[data-pf="path:tools_dir"]', empty)
    click('[data-act="close-settings"]')
    check("changing the tools folder reloads the catalog", soft(lambda: js("document.querySelectorAll('.A-grid .la-card').length")==0, 6, "catalog empty"), "%s cards before" % n_before)
    click('[data-act="settings"]')
    setv('[data-pf="path:tools_dir"]', str(APP.parent / "tools"))
    click('[data-act="close-settings"]')
    check("...and pointing it back restores the tools", soft(lambda: js("document.querySelectorAll('.A-grid .la-card').length")==n_before, 6, "catalog back"))
    shutil.rmtree(empty, ignore_errors=True)

    # -- TTS profiles -----------------------------------------------------------------------------------------
    click('[data-act="settings"]')
    click('[data-act="pf-tts-add"]')
    setv('[data-pfc="name"]', "Narrator")
    setv('[data-pfc="api_key"]', "cart-e2e-secret-0123456789", event="input")
    setv('[data-pfc="voiceId"]', "voice-42")
    setv('[data-pfc="speed"]', "1.25")
    check("a TTS profile is saved with its key and settings", soft(lambda: cfg()["tts_profiles"] and cfg()["tts_profiles"][0]["api_key"] == "cart-e2e-secret-0123456789" and cfg()["tts_profiles"][0]["settings"] == {"speed": 1.25}, 6, "tts saved"),
          "stored=%s; page error=%r; working=%s" % (cfg()["tts_profiles"], text(".la-ttscard small"), js("JSON.stringify(window.LA.prefsUi.tts)")))
    check("the profile key is never sent back to the page", "cart-e2e-secret-0123456789" not in js("document.documentElement.outerHTML") or js("document.querySelector('[data-pfc=\"api_key\"]').value")=="")
    click('[data-act="pf-tts-pin"]')
    check("checking the pin box locks Genius/the Tool screen to this one voice", soft(lambda: cfg().get("active_tts_profile") == "Narrator", 4, "pinned"),
          "active=%r" % cfg().get("active_tts_profile"))
    check("...and the checkbox + tag reflect it", has('.la-check[data-act="pf-tts-pin"][data-on="true"]') and "only voice used" in text(".la-ttscard"))
    click('[data-act="pf-tts-pin"]')
    check("clicking it again unpins", soft(lambda: cfg().get("active_tts_profile") == "", 4, "unpinned"))
    setv('[data-pfc="speed"]', "fast")
    check("an invalid speed is refused and the stored profile is untouched", soft(lambda: "must be a number" in text(".la-settings small.la-err"), 4, "speed error") and (cfg()["tts_profiles"] or [{}])[0].get("settings") == {"speed": 1.25})
    shot("prefs-tts", ".la-ttscard")
    setv('[data-pfc="speed"]', "1.5")
    soft(lambda: (cfg()["tts_profiles"] or [{}])[0].get("settings") == {"speed": 1.5}, 4, "speed fixed")
    click('[data-act="pf-tts-remove"]')
    check("removing a profile deletes it from settings.json", soft(lambda: cfg()["tts_profiles"] == [], 4, "tts removed"))

    # -- persistence and closing ------------------------------------------------------------------------------
    js("document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}))")
    check("Escape closes the modal", soft(lambda: not has(".la-modal"), 3, "closed"))
    js("location.reload()")
    time.sleep(0.5)
    soft(lambda: js("document.readyState==='complete' && document.body.getAttribute('data-ready')==='1'"), 30, "reload ready")
    click('[data-act="settings"]')
    check("after a reload the saved settings come back (masked)", soft(lambda: js("document.querySelector('[data-pf=\"listen\"]').value")==str(LISTEN) and has(".la-keyrow.on"), 6, "reloaded")
          and "e2e-key" not in js("document.documentElement.outerHTML"))
    click('[data-act="close-settings"]')

    # -- no key: Genius says so and points at Preferences ---------------------------------------------------
    click('[data-act="settings"]')
    click('.la-keyrow.on [data-act="pf-del-key"]'); click('.la-keyrow.on [data-act="pf-del-key"]')
    check("deleting the last key leaves Genius without one", soft(lambda: cfg()["api_key"] == "" and cfg()["api_keys"] == [], 4, "last key gone"))
    click('[data-act="close-settings"]')
    click('[data-act="page"][data-k="genius"]')
    check("Genius explains the missing key", soft(lambda: "no API key yet" in text(".A-gnote .la-note"), 4, "no-key note"))
    click('.A-gnote [data-act="settings"]')
    check("...and its button opens Preferences", soft(lambda: has(".la-modal .la-settings"), 4, "modal from note"))
    click('[data-act="close-settings"]')
    click('[data-act="page"][data-k="actions"]')


def tts_section(ev, click, mock, out_dir: Path, appdata: Path, tmp: Path) -> None:
    """TTS Vocal with a Cartesia profile, through the real shell. The profile is made with the real Preferences controls; the
    single network call (POST api.cartesia.ai/tts/bytes) is answered by shell_dev/run_shell_fake_tts.py with a valid float WAV,
    so the real request builder, the real ffmpeg step, the real slot picker and the real bridge placement all run.
    Nothing is sent to Cartesia. See verify_tts_live.py for the one real call."""
    import wave
    KEY = "cart-e2e-secret-0123456789"
    reqs_file = tmp / "tts-requests.jsonl"
    reqs = lambda: [json.loads(l) for l in reqs_file.read_text(encoding="utf-8").splitlines()] if reqs_file.exists() else []
    calls = lambda action: [p for a, p in mock.calls if a == action]
    result = lambda: (ev("document.querySelector('[data-result]').textContent"), ev("document.querySelector('[data-result]').dataset.state"))
    logtext = lambda: ev("LA.data.log.map(l => l[2]).join('\\n')")
    modal = lambda: ev("!!document.querySelector('#place .la-modal.la-place')")
    user32 = ctypes.windll.user32

    def cfg():
        for _ in range(40):
            try:
                return json.loads((appdata / "settings.json").read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                time.sleep(0.05)
        return json.loads((appdata / "settings.json").read_text(encoding="utf-8"))

    def setv(sel, value, event="change"):
        soft(lambda: ev("!!document.querySelector(%s)" % json.dumps(sel)), 4, "element " + sel)
        ev("(()=>{const t=document.querySelector(%s);t.focus();t.value=%s;t.dispatchEvent(new Event('input',{bubbles:true}));%s})()"
           % (json.dumps(sel), json.dumps(value), "t.dispatchEvent(new Event('change',{bubbles:true}));" if event == "change" else ""))

    def field(fid, value):
        setv('.A-right [data-fid="%s"]' % fid, value)

    def finish():
        return soft(lambda: result()[1] in ("done", "error"), 25, "run finished")

    def run_and_finish():
        click('[data-act="run"]')
        soft(lambda: result()[1] == "running", 5, "run started")
        return finish()

    # -- the tool is open BEFORE any profile exists, then a Cartesia profile is made in Preferences ---------------
    click('.la-card[data-id="tts-vocal"]')                     # click() waits for the card: regions redraw on the next frame
    soft(lambda: ev("document.querySelector('.A-right h2') && document.querySelector('.A-right h2').textContent") == "TTS Vocal", 6, "tts inspector (no profile yet)")
    check("with no profile yet the Profile field is a plain text box", ev("document.querySelector('.A-right [data-fid=\"profile\"]').tagName") == "INPUT")
    click('[data-act="settings"]')
    click('[data-act="pf-tts-add"]')
    setv('[data-pfc="name"]', "Cartesia e2e")
    setv('[data-pfc="provider"]', "cartesia")
    setv('[data-pfc="api_key"]', KEY, event="input")
    setv('[data-pfc="voiceId"]', "e2e-voice-1")
    check("a Cartesia profile is saved with its key and voice", soft(lambda: (cfg()["tts_profiles"] or [{}])[0].get("provider") == "cartesia" and cfg()["tts_profiles"][0].get("api_key") == KEY and cfg()["tts_profiles"][0].get("voice_id") == "e2e-voice-1", 6, "profile saved"), str(cfg()["tts_profiles"])[:200])
    click('[data-act="close-settings"]')
    check("the open TTS Vocal form now offers the profile in a dropdown, without a restart",
          soft(lambda: ev("document.querySelector('.A-right [data-fid=\"profile\"]').tagName") == "SELECT"
               and "Cartesia e2e" in ev("[...document.querySelectorAll('.A-right [data-fid=\"profile\"] option')].map(o => o.textContent).join('|')"), 6, "profile dropdown"))

    # -- Add to Live Set: request, real WAV, placement ---------------------------------------------------
    slots = [{"index": 0, "has_clip": False}, {"index": 1, "has_clip": False}]
    mock.call_replies["read_track"] = {"ok": True, "session_clips": slots}
    field("text", "Hello from the shell")
    field("destination", "Add to Live Set")
    n_clips = len(calls("create_clip"))
    click('[data-act="run"]')
    check("the run opens the slot picker (the WAV was generated first)", soft(modal, 30, "slot picker"))
    check("exactly one request went to Cartesia", len(reqs()) == 1, str(len(reqs())))
    r0 = (reqs() or [{}])[0]
    check("it is POST https://api.cartesia.ai/tts/bytes", (r0.get("method"), r0.get("url")) == ("POST", "https://api.cartesia.ai/tts/bytes"), str((r0.get("method"), r0.get("url"))))
    check("with the documented version header and the profile's key as a Bearer token", r0.get("headers", {}).get("cartesia-version") == "2026-08-14" and r0.get("auth_len") == len("Bearer " + KEY), str(r0.get("headers")))
    check("and the documented body: model, the typed text, the profile's voice, wav / pcm_f32le / 48000",
          r0.get("body") == {"model_id": "sonic-3.6", "transcript": "Hello from the shell", "voice": "e2e-voice-1", "output_format": {"container": "wav", "encoding": "pcm_f32le", "sample_rate": 48000}}, json.dumps(r0.get("body"))[:240])
    check("the place picker is titled for TTS Vocal", "Place TTS Vocal" in ev("document.querySelector('#place .la-modal-head').textContent"))
    click('#place [data-act="place-ok"]')
    check("Place sends a NEW create_clip", soft(lambda: len(calls("create_clip")) == n_clips + 1, 8, "create_clip"))
    cc = (calls("create_clip") or [{}])[-1]
    wav = Path(cc.get("sample_file", ""))
    ok_wav = False
    dur = 0.0
    if wav.is_file():
        with wave.open(str(wav), "rb") as w:
            dur = w.getnframes() / w.getframerate()
            ok_wav = (w.getnchannels(), w.getframerate(), w.getsampwidth()) == (1, 48000, 3)
    check("...a real 48 kHz mono 24-bit WAV of the faked reply's length, inside the TTS output folder", ok_wav and abs(dur - 0.6) < 0.03 and str(wav).startswith(str(out_dir / "tts")), "%s %.3fs" % (wav, dur))
    finish()
    check("the result box is Done and says where it went", result()[1] == "done" and "Placed on" in result()[0], result()[0][:120])

    # -- the same request again is a cache hit; changed settings are a new request ---------------------------
    click('[data-act="run"]')
    soft(modal, 30, "slot picker 2")
    click('#place [data-act="place-cancel"].ghost')
    finish()
    check("the identical run is answered from the cache: no second request", len(reqs()) == 1, str(len(reqs())))
    field("voice", "other-voice")
    field("speed", "1.25")
    field("language", "en")
    field("destination", "Save to PC")
    click('[data-act="run"]')
    hwnd = save_as_dialog()
    check("Save to PC opens the native Save As for the new file", hwnd != 0)
    if hwnd:
        user32.PostMessageW(hwnd, 0x0010, 0, 0)                     # WM_CLOSE = cancel
    finish()
    r1 = (reqs() + [{}, {}])[1]
    check("overrides reach Cartesia: voice, language and generation_config.speed", len(reqs()) == 2 and r1.get("body", {}).get("voice") == "other-voice" and r1["body"].get("language") == "en" and r1["body"].get("generation_config") == {"speed": 1.25}, json.dumps(r1.get("body"))[:240])
    check("cancelling Save As keeps the file and says so", soft(lambda: "Save As canceled" in logtext(), 8, "save-as cancel log"))

    # -- refused locally, no request ---------------------------------------------------------------------
    field("speed", "3")
    run_and_finish()
    check("a speed outside Cartesia's 0.6-1.5 is refused without any request", "between 0.6 and 1.5" in result()[0] and result()[1] == "error" and len(reqs()) == 2, result()[0][:120])
    field("speed", "")
    field("voice", "")
    field("language", "")
    check("the profile's key never reaches the page", KEY not in ev("document.documentElement.outerHTML"))

    # -- put the settings back the way the later sections expect ---------------------------------------------
    click('[data-act="settings"]')
    click('[data-act="pf-tts-remove"]')
    check("removing the profile clears it from settings.json", soft(lambda: cfg()["tts_profiles"] == [], 4, "profile removed"))
    click('[data-act="close-settings"]')
    check("...and the Profile field goes back to a text box", soft(lambda: ev("document.querySelector('.A-right [data-fid=\"profile\"]').tagName") == "INPUT", 6, "profile field back to text"))
    ev("document.querySelector('.la-card[data-id=\"clip-namer\"]').click()")


def themes_section(cdp, ev, click, appdata: Path) -> None:
    """v1.0.64: all eleven design kits through the REAL Preferences picker. Per kit: the choice is saved to settings.json, the page loads
    that kit's stylesheet and EXACTLY its own bundled font faces (loaded, by name), the kit's tokens are what the page computes, and no view
    overflows (Preferences, Actions, Genius, the slot picker). Then: nothing was fetched from off this machine, Breakdowns' own window is
    unaffected by the shell theme, and Riso is restored. The pixel proof per kit is capture_shell --theme; contrast numbers: audit_themes."""
    from shell_dev import theme_audit
    import shell_prefs
    known = {t["slug"]: t for t in shell_prefs.KNOWN_THEMES}

    def cfg():
        for _ in range(40):
            try:
                return json.loads((appdata / "settings.json").read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                time.sleep(0.05)
        return json.loads((appdata / "settings.json").read_text(encoding="utf-8"))

    place_sample = ("({tool:'TTS Vocal', track:'Vox', slots:[{index:0,n:1,has:false},{index:1,n:2,has:true,name:'Kick loop'},{index:2,n:3,has:true}]},"
                    "{sel:0, warn:'Slot 2 already holds a clip - click Place again to replace it.'})")

    def flags(a):
        return not a["overflowX"] and not a["modalOverflow"] and not a["unparsed"]

    click('[data-act="settings"]')
    if ev("document.querySelector('[data-act=\"pf-theme-toggle\"]').getAttribute('aria-expanded')") != "true":
        click('[data-act="pf-theme-toggle"]')
    soft(lambda: ev("document.querySelectorAll('[data-act=\"pf-theme\"]').length") == len(known), 4, "swatches")
    offered = ev("[...document.querySelectorAll('[data-act=\"pf-theme\"]')].map(b => b.dataset.slug)") or []
    check("Preferences offers all eleven kits", sorted(offered) == sorted(known) and len(known) == 11, "%d offered" % len(offered))

    for slug, meta in known.items():
        click('[data-act="pf-theme"][data-slug="%s"]' % slug)
        saved = soft(lambda: cfg().get("theme") == slug, 6, "theme saved " + slug)
        try:
            faces = theme_audit.apply_theme(cdp, slug, use_hook=False)      # the page itself did the switch; this only waits and proves the faces
            faces_ok, detail = True, "%d faces" % len(faces)
        except Exception as exc:                                             # a timeout or a face that failed to load
            faces_ok, detail = False, str(exc)[:160]
        accent = (ev("getComputedStyle(document.documentElement).getPropertyValue('--kit-accent')") or "").strip().lower()
        picked = ev("(document.querySelector('.la-swatch.on') || {dataset: {}}).dataset.slug")
        views = {"prefs": theme_audit.audit(cdp)}
        click('[data-act="close-settings"]')
        soft(lambda: not ev("!!document.querySelector('.la-modal')"), 4, "modal closed")
        views["actions"] = theme_audit.audit(cdp)
        click('[data-act="page"][data-k="genius"]')
        time.sleep(0.25)
        views["genius"] = theme_audit.audit(cdp)
        click('[data-act="page"][data-k="actions"]')
        ev("document.getElementById('place').innerHTML = LA.placeModal%s" % place_sample)
        time.sleep(0.2)
        views["place"] = theme_audit.audit(cdp)
        ev("document.getElementById('place').innerHTML = ''")
        check("kit %s: saved, its own fonts loaded (%s), its tokens applied, picker shows it, no view overflows" % (slug, detail),
              saved and faces_ok and accent == meta["accent"].lower() and picked == slug and all(flags(a) for a in views.values()),
              "saved=%s accent=%s want %s picked=%s %s" % (saved, accent, meta["accent"].lower(), picked, {k: (a["overflowX"], a["modalOverflow"], a["unparsed"]) for k, a in views.items()}))
        click('[data-act="settings"]')

    off = ev("performance.getEntriesByType('resource').map(r => r.name).filter(n => !['file:', 'http://127.0.0.1', 'http://localhost', 'data:', 'blob:'].some(p => n.startsWith(p)))")
    check("nothing was fetched from off this machine while switching kits (fonts are local)", off == [], str(off)[:200])

    # Breakdowns keeps its own look, whatever the shell's theme (the user's standing decision)
    target_theme = "cyber-neon-pink"
    click('[data-act="pf-theme"][data-slug="%s"]' % target_theme)
    soft(lambda: cfg().get("theme") == target_theme, 6, "theme saved")
    click('[data-act="close-settings"]')
    click('.la-card[data-id="breakdowns"]')
    soft(lambda: ev("document.querySelector('.A-right h2') && document.querySelector('.A-right h2').textContent") == "Breakdowns", 4, "breakdowns inspector")
    click('[data-act="run"]')
    dlg = lambda: [t for t in json.load(urllib.request.urlopen("http://127.0.0.1:%d/json" % CDP_PORT)) if t.get("type") == "page" and t.get("url", "").startswith("file:")]
    d = Cdp(wait_for(dlg, 25, "dialog window")[0]["webSocketDebuggerUrl"])
    d.call("Runtime.enable")
    wait_for(lambda: d.eval("document.readyState") == "complete", 15, "dialog loaded")
    time.sleep(1.0)
    check("Breakdowns opens untouched while the shell wears %s (no shell stylesheet, no --la tokens, only its OWN theme ids -- it remembers the Plasma an earlier section picked)" % target_theme,
          d.eval("!document.getElementById('la-theme') && getComputedStyle(document.documentElement).getPropertyValue('--la-bg') === '' && !!document.getElementById('themeBtn') && [undefined, 'plasma', 'acid', 'ember', 'mono'].includes(document.body.dataset.theme)") is True)
    d.eval("document.getElementById('cancel').click()")
    soft(lambda: not dlg(), 8, "dialog closed")
    try:
        d.ws.close()
    except Exception:
        pass

    click('[data-act="settings"]')
    click('[data-act="pf-theme"][data-slug="risograph-art-studio"]')
    check("Riso Art Studio is restored (the opening theme)", soft(lambda: cfg().get("theme") == "risograph-art-studio" and ev("document.getElementById('la-theme').getAttribute('href')").endswith("/risograph-art-studio.css"), 6, "riso back"))
    click('[data-act="close-settings"]')
    ev("document.querySelector('.la-card[data-id=\"clip-namer\"]').click()")


def main() -> int:
    appdata = Path(os.environ["APPDATA"]) / ("Live Actions-" + INSTANCE)
    appdata.mkdir(parents=True, exist_ok=True)
    out_dir = Path(tempfile.mkdtemp(prefix="la-e2e-samples-"))
    llm = MockLLM().start()
    agents = agent_registry.list_agents({})
    agent = agents[0]
    (appdata / "settings.json").write_text(json.dumps({
        "listen_port": LISTEN, "bridge_port": BRIDGE,
        "api_key": "e2e-key", "api_base": llm.base_url, "model": "e2e-model",
        "enabled_agents": [agent["slug"]], "active_agent": "", "audio_sample_output_dir": str(out_dir),
        "tts_output_dir": str(out_dir / "tts"),          # never the user's real Samples folder
    }), encoding="utf-8")

    mock = MockLive(listen_port=BRIDGE, reply_port=LISTEN).start()
    tmp = Path(tempfile.mkdtemp(prefix="la-e2e-"))
    ready = tmp / "ready.txt"
    env = dict(os.environ, LIVE_ACTIONS_INSTANCE=INSTANCE, LA_FAKE_TTS_LOG=str(tmp / "tts-requests.jsonl"))
    t0 = time.time()
    # The real shell, started through a wrapper that answers ONE url (Cartesia's TTS endpoint) itself; see run_shell_fake_tts.py.
    proc = subprocess.Popen([sys.executable, str(APP / "shell_dev" / "run_shell_fake_tts.py"), "--cdp-port", str(CDP_PORT), "--ready-file", str(ready)], cwd=str(APP), env=env)
    hwnd = 0
    try:
        wait_for(ready.exists, 40, "window shown")
        t_shown = time.time() - t0
        hwnd = int(dict(l.split("=") for l in ready.read_text().split())["hwnd"])
        targets = wait_for(lambda: [t for t in json.load(urllib.request.urlopen("http://127.0.0.1:%d/json" % CDP_PORT)) if t.get("type") == "page"], 20, "page target")
        cdp = Cdp(targets[0]["webSocketDebuggerUrl"])
        cdp.call("Runtime.enable")
        cdp.call("Log.enable")
        cdp.call("Emulation.setDeviceMetricsOverride", width=1360, height=820, deviceScaleFactor=1, mobile=False)
        ev = cdp.eval
        wait_for(lambda: ev("document.readyState==='complete' && document.body.getAttribute('data-ready')==='1'"), 30, "page ready")
        t_ready = time.time() - t0
        check("window shown and page ready", True, "window %.2fs, page %.2fs after launch" % (t_shown, t_ready))

        # -- live connection through the real bridge_client + UiBus + evaluate_js -----------
        check("pip goes Online via a pushed event", wait_for(lambda: ev("document.querySelector('.la-pip').dataset.on==='true'"), 8, "pip online"))
        # The shell opens on Genius since v1.6.0; the checks below are about the Tools page.
        ev("document.querySelector('[data-act=\"page\"][data-k=\"actions\"]').click()")
        check("Live set name arrives", wait_for(lambda: ev("document.querySelector('.A-left .set b').textContent")=="Neon Nights 128.als", 8, "set name"))
        check("chips show BPM 128.00 / 4/4 / 10 tracks", ev("[...document.querySelectorAll('.la-chip b')].map(b=>b.textContent).join('|')")=="128.00|4/4|10")
        check("10 tracks listed", wait_for(lambda: ev("document.querySelectorAll('.la-track').length")==10, 8, "tracks"))
        check("Live's selection (Bass) is the initial target", ev("[...document.querySelectorAll('.la-track.on .la-track-name')].map(n=>n.textContent).join(',')")=="Bass")
        check("status bar says 1 track targeted", "1 track targeted" in ev("document.querySelector('.la-statusbar .grow').textContent"))

        # -- target tracks: every click is a real js_api round trip --------------------------
        def click(sel):
            # Regions re-render on the next animation frame, so wait for the target to exist.
            wait_for(lambda: ev("!!document.querySelector(%s)" % json.dumps(sel)), 4, "element " + sel)
            ev("document.querySelector(%s).click()" % json.dumps(sel))
        def on_count(): return ev("document.querySelectorAll('.la-track.on').length")
        click('[data-act="all"]');  check("All ticks all 10", wait_for(lambda: on_count()==10, 4, "all"))
        click('[data-act="none"]'); check("None clears", wait_for(lambda: on_count()==0, 4, "none"))
        check("summary reads 'No tracks targeted'", "No tracks targeted" in ev("document.querySelector('.A-tracks .sum').textContent"))
        ev("document.querySelectorAll('.la-track')[0].click()"); ev("document.querySelectorAll('.la-track')[4].click()")
        check("clicking two rows ticks exactly those two", wait_for(lambda: ev("[...document.querySelectorAll('.la-track.on .la-track-name')].map(n=>n.textContent).join(',')")=="Drums,Vox", 4, "two rows"))
        click('[data-act="livesel"]'); check("Live Sel returns to Live's selection", wait_for(lambda: ev("[...document.querySelectorAll('.la-track.on .la-track-name')].map(n=>n.textContent).join(',')")=="Bass", 4, "livesel"))
        ev("document.querySelectorAll('.la-track')[0].click()"); ev("document.querySelectorAll('.la-track')[4].click()")
        wait_for(lambda: on_count()==3, 4, "three ticked")

        # -- open a tool, type, and prove a pushed event does not wipe the typing -------------
        ev("document.querySelector('.la-card[data-id=\"clip-namer\"]').click()")
        check("inspector opens Clip Namer", wait_for(lambda: ev("document.querySelector('.A-right h2') && document.querySelector('.A-right h2').textContent")=="Clip Namer", 4, "inspector"))
        check("scope note counts ticked tracks", "3 ticked tracks" in ev("document.querySelector('[data-scope-note]').textContent"))
        ev("(()=>{const i=document.querySelector('.A-right input[data-fid=\"pattern\"]'); i.focus(); i.value='{track} typed'; i.dispatchEvent(new Event('input',{bubbles:true}));})()")
        click('[data-act="console"]')
        click('[data-act="diag"]'); click('[data-act="diag-ping"]'); click('[data-act="diag-sync"]')
        check("console shows the pushed log lines", wait_for(lambda: "OSC Ping sent" in ev("(document.querySelector('.la-console')||{textContent:''}).textContent"), 4, "console lines"))
        check("typed field value survives bridge pushes (region rendering)", ev("document.querySelector('.A-right input[data-fid=\"pattern\"]').value")=="{track} typed")

        # -- run: only ticked tracks go over OSC, result comes back --------------------------
        click('[data-act="run"]')
        check("Run sends /live-actions/run to the device", wait_for(lambda: mock.runs, 4, "run received"))
        tool_id, payload = mock.runs[0]
        check("payload carries exactly the 3 ticked tracks", [t["key"] for t in payload["tracks"]]==["midi:0","midi:1","audio:4"], str([t["key"] for t in payload["tracks"]]))
        check("payload carries the typed field", payload["fields"]=={"pattern": "{track} typed"}, str(payload["fields"]))
        check("result box shows Done", wait_for(lambda: "Done" in ev("document.querySelector('[data-result]').textContent"), 4, "result"))
        mock.fail_runs = True
        click('[data-act="run"]')
        check("a tool error is shown as an error, not Done", wait_for(lambda: ev("document.querySelector('[data-result]').dataset.state")=="error", 4, "error state"))
        mock.fail_runs = False

        dialogs_section(ev, click, mock, CDP_PORT)
        placement_section(cdp, ev, click, mock, out_dir)

        genius_section(cdp, ev, click, mock, llm, agent, appdata)
        confirm_section(ev, click, appdata, tmp)
        prefs_section(cdp, ev, click, llm, agent, appdata)
        tts_section(ev, click, mock, out_dir, appdata, tmp)
        themes_section(cdp, ev, click, appdata)

        # -- offline / recovery ---------------------------------------------------------------
        mock.muted = True
        check("pip flips Offline after the bridge goes silent (~4s)", wait_for(lambda: ev("document.querySelector('.la-pip').dataset.on==='false'"), 9, "offline"))
        check("set panel shows the waiting state", "Waiting" in ev("document.querySelector('.A-left .set b').textContent"))
        mock.muted = False
        check("pip recovers by itself when the bridge returns", wait_for(lambda: ev("document.querySelector('.la-pip').dataset.on==='true'"), 8, "online again"))

        errs = [e for e in cdp.events if e.get("method") == "Runtime.exceptionThrown" or (e.get("method") == "Log.entryAdded" and e["params"]["entry"]["level"] == "error")]
        check("no JS exceptions or console errors", not errs, json.dumps(errs)[:300] if errs else "")

        # a dialog left open must not keep the app alive: the WM_CLOSE in `finally` has to end everything
        ev("document.querySelector('.la-card[data-id=\"breakdowns\"]').click()")
        soft(lambda: ev("document.querySelector('.A-right h2').textContent") == "Breakdowns", 4, "breakdowns")
        click('[data-act="run"]')
        soft(lambda: find_window("Breakdowns"), 15, "dialog window for shutdown test")
        time.sleep(1.5)
        mb, n = tree_private_mb(proc.pid)
        print("FOOTPRINT  startup: window %.2fs, page ready %.2fs;  memory: %.0f MB private across %d processes" % (t_shown, t_ready, mb, n))
        cdp.ws.close()
    finally:
        t_close = time.time()
        if hwnd:
            single_instance.post_close(hwnd)
        try:
            code = proc.wait(timeout=20)
            check("shutdown via WM_CLOSE: process exits cleanly", code == 0, "exit code %s in %.2fs" % (code, time.time() - t_close))
        except subprocess.TimeoutExpired:
            proc.kill()
            check("shutdown via WM_CLOSE: process exits cleanly", False, "did not exit within 20s")
        mock.stop()
        llm.stop()
        shutil.rmtree(appdata, ignore_errors=True)
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(out_dir, ignore_errors=True)
    bad = [n for ok, n in RESULTS if not ok]
    print("\n%d/%d checks passed" % (len(RESULTS) - len(bad), len(RESULTS)))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
