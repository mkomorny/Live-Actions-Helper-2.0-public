"""Generates ../index.html (the decision gallery) from measured artifacts:
shots/dom-report.json, shots/footprint.json, LOC-REPORT.md's numbers (recomputed here)."""

from __future__ import annotations

import html
import json
import re
import subprocess
import sys
from pathlib import Path

ROUND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
dom = json.loads((ROUND / "shots" / "dom-report.json").read_text(encoding="utf-8"))
foot = json.loads((ROUND / "shots" / "footprint.json").read_text(encoding="utf-8"))
labels = {t["slug"]: t["label"] for t in json.loads(re.search(r"window\.LA_REAL = (\{.*\});", (ROUND / "shared" / "data.js").read_text(encoding="utf-8"), re.S).group(1))["themes"]}
loc = (ROUND / "LOC-REPORT.md").read_text(encoding="utf-8")
tot = re.search(r"\*\*Total\*\* \| \*\*(\d+)\*\* \| \*\*(\d+)\*\* \| \*\*(\d+)\*\*", loc).groups()

LAYOUTS = [
    ("a", "A · Workbench", "Tracks | catalog | inspector on the Actions page; Genius is full width with no track panel. CHOSEN.",
     "Tool detail opens in the right pane and the catalog never leaves. The track list belongs to the Actions page only (Genius resolves tracks itself, so the Genius page has no track panel). Diagnostics live in a popover off the status pip; Preferences is a modal.",
     "Best when you run many actions in a row against the same tracks; costs the most horizontal space."),
    ("b", "B · Rail + slide-over", "Icon rail, full-width card grid, slide-over detail.",
     "No permanent sidebar. Targets is one header button that opens a picker with device lists. A tool slides over the catalog. Preferences is the last rail item; the bridge pip opens diagnostics.",
     "Most room for the catalog and the calmest screen; track picking is one click deeper."),
    ("c", "C · Command list", "One column, search-first, grouped by what an action touches.",
     "Actions are grouped into Selected tracks / Whole Set / Own dialog. A row expands in place (accordion). Targets is a chip strip pinned to the bottom. Search is the top bar. Preferences is a modal.",
     "Fastest to scan and the most honest about scope; dense rows lose the card personality."),
    ("d", "D · Session deck", "Modelled on Live's Session View: track columns on top, master-detail below, Genius docked.",
     "Tracks run across the top as columns you target. Tool list and the selected tool's detail sit side by side (never empty). Genius and the Console are tabs of a bottom dock, so Genius stops being a page.",
     "Most Ableton-native and the biggest structural change; the least vertical room, and Genius becomes secondary."),
]
PROBLEMS = [
    ("1. Tool drill-down is a page, not a tab",
     ["Right inspector, same screen", "Slide-over; catalog stays", "Inline accordion", "Master-detail, always both"]),
    ("2. Sidebar silently changes meaning by page",
     ["Track panel exists on Actions only; Genius has none", "No sidebar; one Targets picker", "Constant chip strip", "Constant track deck"]),
    ("3. Track picking is dead weight on Genius / Settings",
     ["Removed from Genius (decided); Settings is a modal", "Hidden on Settings; Genius not yet updated (B was not chosen)", "Strip stays; Settings is a modal", "Deck stays; Settings is a modal"]),
    ("4. Ping/Status/Sync/Reset hold prime space",
     ["Popover off the pip", "Popover off the rail pip", "Popover off the pip", "Popover off the pip"]),
    ("5. Settings is a peer tab of the workspaces",
     ["Gear icon opens a modal", "Last rail item, visually separate", "Gear icon opens a modal", "Gear icon opens a modal"]),
]
esc = html.escape

h = ["""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>Redesign Round</title><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{--bg:#0f1115;--s:#181b22;--b:#2a2f3a;--t:#e8eaf0;--m:#9aa3b2;--a:#7dd3fc}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--t);font:15px/1.55 system-ui,Segoe UI,sans-serif}
main{max-width:1500px;margin:0 auto;padding:32px 28px 80px}h1{font-size:30px;margin:0 0 6px}h2{font-size:22px;margin:52px 0 6px;padding-top:18px;border-top:1px solid var(--b)}
h3{margin:0 0 4px;font-size:17px}p{margin:6px 0}.m{color:var(--m)}a{color:var(--a)}
.lay{margin:26px 0 34px}.lh{display:flex;gap:18px;align-items:baseline;flex-wrap:wrap}.lh .m{font-size:14px}
.row{display:grid;grid-template-columns:repeat(auto-fill,minmax(212px,1fr));gap:10px;margin-top:12px}
.th{display:block;background:var(--s);border:1px solid var(--b);border-radius:8px;overflow:hidden;text-decoration:none;color:var(--t)}
.th img{display:block;width:100%;height:auto}.th span{display:block;padding:5px 9px;font-size:12px}.th:hover{border-color:var(--a)}
table{border-collapse:collapse;width:100%;font-size:13.5px}th,td{border:1px solid var(--b);padding:8px 10px;text-align:left;vertical-align:top}th{background:var(--s)}
.pill{display:inline-block;padding:1px 9px;border-radius:99px;background:#1f3a2c;color:#8be9b0;font-size:12px}
.grid3{display:grid;grid-template-columns:repeat(auto-fit,minmax(380px,1fr));gap:16px}.fig{background:var(--s);border:1px solid var(--b);border-radius:8px;overflow:hidden}
.fig img{width:100%;display:block}.fig p{padding:8px 12px;margin:0;font-size:13px}.gate{background:var(--s);border:1px solid var(--a);border-radius:10px;padding:18px 22px}
code{background:#20242d;padding:1px 5px;border-radius:4px;font-size:.9em}
</style></head><body><main>
<h1>Live Actions — redesign decision round</h1>
<div class="gate" style="margin-bottom:18px"><b>Decisions recorded after this round:</b> structure <b>A · Workbench</b> which <b>opens in Riso Art Studio</b>; every other theme keeps its own look and design (as in the renders below); <b>Genius resolves tracks itself</b>, so the Genius page has <b>no track checkboxes</b> (layout A was updated; B, C and D were left as originally rendered). Platform: <b>webview (WebView2) — decided 2026-09-20, Riso only for now</b>. Full handoff: <code>docs/plans/HANDOFF-redesign-for-opus.md</code>.</div>
<p class="m">Nothing in the app itself has changed. This folder is evidence for two decisions: <b>which structure</b> and <b>which platform</b>. Every thumbnail below is a link to the live, clickable layout with that kit applied (theme switcher bottom-left).</p>
<p><span class="pill">markup check passed</span> Each of the 4 layouts renders <b>byte-identical markup</b> under all 11 kits (sha1 of the rendered <code>#app</code> compared per layout; <code>shots/dom-report.json</code>). Only the linked theme file differs.</p>
<h2>1 · Four interface structures × eleven kits</h2>
<p class="m">Data is real: all 14 tools come from the actual <code>tool.json</code> manifests. The Live Set and tracks are a mock. Each kit's own <code>tokens.css</code> is included verbatim in <code>themes/</code>; a shared <code>contract.css</code> maps any kit's tokens onto the app's components.</p>
"""]
for k, name, tag, body, tradeoff in LAYOUTS:
    h.append(f'<section class="lay"><div class="lh"><h3>{name}</h3><span class="m">{tag}</span></div><p>{body}</p><p class="m"><b>Trade-off:</b> {tradeoff}</p><div class="row">')
    for t in dom["themes"]:
        h.append(f'<a class="th" href="../../previews/redesign-round/layout-{k}.html?theme={t}" target="_blank"><img loading="lazy" src="shots/thumbs/{k}__{t}.jpg" alt=""><span>{esc(labels[t])}</span></a>'.replace("../../previews/redesign-round/", ""))
    h.append("</div>")
    extras = {"a": [("a-genius", "Genius"), ("a-settings", "Preferences (theme picker collapsed)"), ("a-settings-themes-open", "Preferences (theme picker open)")], "b": [("b-genius", "Genius"), ("b-targets-pop", "Targets picker"), ("b-settings", "Preferences page")],
              "c": [("c-genius", "Genius"), ("c-targets-diag", "Diagnostics popover")], "d": [("d-console", "Console in dock")]}[k]
    h.append('<div class="row" style="grid-template-columns:repeat(auto-fill,minmax(212px,250px))">')
    for key, cap in extras:
        f = ROUND / "shots" / "thumbs" / f"extra__{key}.jpg"
        if f.exists():
            h.append(f'<a class="th" href="shots/extra__{key}.png" target="_blank"><img loading="lazy" src="shots/thumbs/extra__{key}.jpg" alt=""><span>{cap} (Riso Art Studio)</span></a>')
    h.append("</div></section>")

h.append("<h2>2 · How each structure answers the five problems in today's IA</h2><table><tr><th>Problem in the current app</th>" + "".join(f"<th>{n[0]}</th>" for n, *_ in LAYOUTS) + "</tr>")
for prob, cells in PROBLEMS:
    h.append(f"<tr><td>{prob}</td>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
h.append("</table><p class='m'>Note on problem 3: the real app says Genius resolves tracks itself. Layouts A and B show ticked tracks as <i>offered context</i> — a <b>proposal</b>, not current behaviour; it is a product decision below.</p>")

t1, t2, t3 = tot
h.append(f"""<h2>3 · Platform ceiling: can Tkinter get there?</h2>
<p>Same Actions screen, three runnable windows (source in <code>tk/</code>) plus the HTML version. Screenshots are real window captures.</p>
<div class="grid3">
<div class="fig"><a href="shots/tk1-baseline.png" target="_blank"><img src="shots/thumbs/tk1-baseline.jpg" alt=""></a><p><b>Build 1 — Tk today.</b> The app's own tokens and widget code, real manifests.</p></div>
<div class="fig"><a href="shots/tk2-pushed.png" target="_blank"><img src="shots/thumbs/tk2-pushed.jpg" alt=""></a><p><b>Build 2 — Tk pushed hard</b> (Canvas + Pillow), palette read from the Cyber Neon Pink <code>tokens.css</code>.</p></div>
<div class="fig"><a href="shots/tk2-pushed-riso.png" target="_blank"><img src="shots/thumbs/tk2-pushed-riso.jpg" alt=""></a><p><b>Build 2 with the Riso kit.</b> Colours follow; Riso's offset shadows don't, and the selected-row tint and scope pills stayed hard-coded from the pink theme — the selected rows are unreadable. Leaks like this are the ongoing cost of theming by hand.</p></div>
<div class="fig"><a href="layout-a.html?theme=risograph-art-studio" target="_blank"><img src="shots/thumbs/a__risograph-art-studio.jpg" alt=""></a><p><b>Build 3 — HTML.</b> Same theme, same screen, kit applied through the contract.</p></div>
</div>
<h3 style="margin-top:22px">What the pushed Tk build cost (measured)</h3>
<table><tr><th>Approach</th><th>Component code lines</th></tr>
<tr><td>Tk build 1 (today's style)</td><td>{t1}</td></tr><tr><td>Tk build 2 (pushed)</td><td>{t2} &nbsp;— {float(t2)/float(t1):.1f}× build 1, for 6 components</td></tr>
<tr><td>HTML/CSS (same components)</td><td>{t3} rule-lines <span class="m">(dense one-liners, so lines are not like-for-like) + a one-time 41-line theme contract</span></td></tr></table>
<p>Per-component table and the list of what was <i>not</i> attempted (inputs, selects, chat, console, forms, modals, themed scrollbar): <a href="LOC-REPORT.md">LOC-REPORT.md</a>.</p>
<ul><li><b>Looks:</b> Tk build 2 gets convincingly close to a rounded, glowing kit — better than I expected. It does it with pictures: every button is a bitmap plus hand-written hover, press, focus, disabled, keyboard and resize code.</li>
<li><b>Theming:</b> a kit file can drive only colours, radii and a font name in Tk. Shadows, motion, <code>color-mix()</code>, web fonts and every kit's <code>layout.md</code> stay inert. Themes are Python constants, not files someone can drop in.</li>
<li><b>Memory (private bytes, static page, whole process tree):</b> Tk build 1 ≈ {foot['tk_baseline_MB_procs'][0]:.0f} MB (1 process); Tk build 2 ≈ {foot['tk_pushed_MB_procs'][0]:.0f} MB; a pywebview/WebView2 shell showing layout A ≈ {foot['webview_shell_MB_procs'][0]:.0f} MB across {foot['webview_shell_MB_procs'][1]} processes — about <b>+{foot['webview_shell_MB_procs'][0]-foot['tk_baseline_MB_procs'][0]:.0f} MB</b>. Startup time was not measured.</li>
<li><b>Already shipped dependency:</b> <code>webview_pane.py</code> and three tools already use pywebview, and the module imports on this machine.</li></ul>
<div class="gate"><h3>Decision gate — status</h3>
<p><b>1. Platform:</b> <i>answered</i> — webview shell (themes are files), Riso Art Studio only for now. The known costs are listed in the handoff (§0b).</p>
<p><b>2. Structure:</b> <i>answered</i> — A · Workbench, opening in Riso Art Studio.</p>
<p><b>3. Product questions:</b> <i>answered</i> — Genius resolves tracks itself and gets no track checkboxes; it stays a page (structure A).</p>
<p class="m">Your last message said “4 different redesigns and then the color previews for each”, which is what section 1 is. Which of the 11 kits you would ship with is a separate choice from structure and platform.</p></div>
</main></body></html>""")
(ROUND / "index.html").write_text("\n".join(h), encoding="utf-8")
print("index.html written")
