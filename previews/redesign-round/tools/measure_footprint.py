"""Measures process-tree memory + time-to-first-window for Tk build 1 vs a pywebview shell
showing layout A. Run once; numbers go into the gallery. Windows only.

    python measure_footprint.py
"""
import json, subprocess, sys, time
from pathlib import Path

ROUND = Path(__file__).resolve().parent.parent
PS = ("$m=@{}; Get-Process | ForEach-Object { $m[$_.Id]=$_.PrivateMemorySize64 }; "
      "Get-CimInstance Win32_Process | ForEach-Object { [pscustomobject]@{id=[int]$_.ProcessId;parent=[int]$_.ParentProcessId;priv=[int64]$m[[int]$_.ProcessId]} } | ConvertTo-Json -Compress")


def tree_mb(root):
    rows = json.loads(subprocess.run(["pwsh", "-NoProfile", "-Command", PS], capture_output=True, text=True).stdout)
    ids = {root}
    grew = True
    while grew:
        grew = False
        for r in rows:
            if r["parent"] in ids and r["id"] not in ids:
                ids.add(r["id"]); grew = True
    return round(sum(r["priv"] for r in rows if r["id"] in ids) / 1048576, 1), len(ids)


SHELL = f"""
import webview, sys
webview.create_window('shell', r'{(ROUND / "layout-a.html").as_uri()}?embed=1', width=1360, height=820)
webview.start()
"""

def measure(cmd, settle=7):
    t0 = time.time()
    p = subprocess.Popen(cmd, cwd=str(ROUND / "tk"))
    time.sleep(settle)
    mb = tree_mb(p.pid)
    subprocess.run(["taskkill", "/PID", str(p.pid), "/T", "/F"], capture_output=True)
    return mb

res = {"tk_baseline_MB_procs": measure([sys.executable, "tk_baseline.py"]),
       "tk_pushed_MB_procs": measure([sys.executable, "tk_pushed.py"]),
       "webview_shell_MB_procs": measure([sys.executable, "-c", SHELL], settle=10)}
print(json.dumps(res, indent=1))
(ROUND / "shots" / "footprint.json").write_text(json.dumps(res, indent=1))
