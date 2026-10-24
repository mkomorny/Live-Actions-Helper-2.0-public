"""Single-instance + LIVE_ACTIONS_INSTANCE isolation, on the REAL shell.

    python -m shell_dev.check_instances

  1. instance A starts and shows a window
  2. a second launch of A exits at once (it raises A instead of opening a duplicate)
  3. instance B (a different LIVE_ACTIONS_INSTANCE) starts alongside A -- two windows, two processes
  4. both close cleanly via WM_CLOSE
  5. (slice 4c) the duplicate launch carries the `liveactions://open` argument the Max device's protocol handler passes
  6. (slice 4c) the real `Launch Live Actions.bat` starts the shell (not the Tk app) and it closes via WM_CLOSE
Checks 1-4 use the demo state, so no ports are opened; check 6 is a normal run on the isolated instance's own ports.
"""

from __future__ import annotations

import ctypes
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

APP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP))
import single_instance  # noqa: E402

R: list[bool] = []


def check(name, ok, detail=""):
    R.append(bool(ok))
    print(("PASS  " if ok else "FAIL  ") + name + (("  [" + detail + "]") if detail else ""), flush=True)


def launch(instance: str, tmp: Path, extra=()):
    ready = tmp / (instance + ".txt")
    env = dict(os.environ, LIVE_ACTIONS_INSTANCE=instance)
    p = subprocess.Popen([sys.executable, str(APP / "shell.py"), "--demo-state", "--ready-file", str(ready), *extra], cwd=str(APP), env=env)
    return p, ready


def wait(pred, timeout):
    end = time.time() + timeout
    while time.time() < end:
        if pred():
            return True
        time.sleep(0.2)
    return False


def bat_launch_check(user32) -> None:
    """The shipped launcher, end to end: `Launch Live Actions.bat` -> pyw/pythonw -> shell.py."""
    import psutil

    instance = "instBat"
    title = "Live Actions — DAW Studio Host [%s]" % instance
    env = dict(os.environ, LIVE_ACTIONS_INSTANCE=instance)
    bat = APP.parent / "Launch Live Actions.bat"
    subprocess.run(["cmd", "/c", str(bat)], cwd=str(APP.parent), env=env, timeout=30)
    hwnd = 0
    try:
        found = wait(lambda: bool(user32.FindWindowW(None, title)), 40)
        check("Launch Live Actions.bat opens the window", found)
        hwnd = user32.FindWindowW(None, title)
        pid = ctypes.c_ulong(0)
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        try:
            cmd = " ".join(psutil.Process(pid.value).cmdline()) if pid.value else ""
        except psutil.Error:
            cmd = ""
        check("...and that window is the WebView2 shell, not the Tk app", "shell.py" in cmd and "helper.py" not in cmd, cmd[-80:])
    finally:
        if hwnd:
            single_instance.post_close(hwnd)
            check("...and it closes via WM_CLOSE", wait(lambda: not user32.FindWindowW(None, title), 20))
        shutil.rmtree(Path(os.environ["APPDATA"]) / ("Live Actions-" + instance), ignore_errors=True)


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="la-inst-"))
    user32 = ctypes.windll.user32
    a, ra = launch("instA", tmp)
    b = None
    try:
        check("instance A shows its window", wait(ra.exists, 40))
        title_a = "Live Actions — DAW Studio Host [instA]"
        check("A's window is findable by its instance-suffixed title", bool(user32.FindWindowW(None, title_a)))

        dup, _ = launch("instA", tmp, ("liveactions://open",))
        try:
            code = dup.wait(timeout=15)
            check("second launch of A, with the liveactions:// argument, exits immediately (raises A instead)", code == 0, "exit %s" % code)
        except subprocess.TimeoutExpired:
            dup.kill()
            check("second launch of A, with the liveactions:// argument, exits immediately (raises A instead)", False, "still running after 15s")
        check("A is still running after the duplicate launch", a.poll() is None)

        b, rb = launch("instB", tmp)
        check("instance B starts alongside A", wait(rb.exists, 40))
        check("two distinct windows exist", bool(user32.FindWindowW(None, title_a)) and bool(user32.FindWindowW(None, "Live Actions — DAW Studio Host [instB]")))
        check("two live processes", a.poll() is None and b.poll() is None)
    finally:
        for name, proc in (("instA", a), ("instB", b)):
            if proc is None:
                continue
            h = user32.FindWindowW(None, "Live Actions — DAW Studio Host [%s]" % name)
            if h:
                single_instance.post_close(h)
            try:
                code = proc.wait(timeout=20)
                check("%s closes cleanly via WM_CLOSE" % name, code == 0, "exit %s" % code)
            except subprocess.TimeoutExpired:
                proc.kill()
                check("%s closes cleanly via WM_CLOSE" % name, False, "did not exit")
        for name in ("instA", "instB"):
            shutil.rmtree(Path(os.environ["APPDATA"]) / ("Live Actions-" + name), ignore_errors=True)
        shutil.rmtree(tmp, ignore_errors=True)
    bat_launch_check(user32)
    print("\n%d/%d checks passed" % (sum(R), len(R)))
    return 0 if all(R) else 1


if __name__ == "__main__":
    raise SystemExit(main())
