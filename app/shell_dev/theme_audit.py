"""Shared by capture_shell.py, audit_themes.py and e2e_shell.py: apply a kit and prove its fonts loaded; audit what is on screen.

`apply_theme` waits until the page has registered EXACTLY the font faces the kit's own file declares (compared by name: two kits can
declare the same number of faces, so a count would be satisfied by the previous kit's) and then loads every one of them.
`AUDIT_JS` measures, for the visible text inside the top layer (the open modal, else the page): the WCAG contrast of each text run
against the colour actually painted behind it, and whether the page overflows sideways. It reports numbers; whether a low one is a
leak or the kit's own design is decided by comparing with the kit's preview (the Actions view is pixel-identical to it).
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

from shell_dev.capture_shell import wait_for

APP = Path(__file__).resolve().parent.parent
THEMES = APP / "web" / "css" / "themes"
FACE_RE = re.compile(r'@font-face\s*\{\s*font-family:\s*"([^"]+)";[^}]*?font-weight:\s*(\d+);')


def declared_faces(slug: str) -> list[str]:
    return sorted("%s %s" % (m.group(1), m.group(2)) for m in FACE_RE.finditer((THEMES / (slug + ".css")).read_text(encoding="utf-8")))


def apply_theme(cdp, slug: str, use_hook: bool = True) -> list[str]:
    """Switch to `slug` (through the page's own LA.setTheme unless the caller already clicked the real picker) and return the loaded faces."""
    if use_hook:
        cdp.eval("LA.setTheme(%s)" % json.dumps(slug))
    wait_for(lambda: cdp.eval("(()=>{const l=document.getElementById('la-theme');return !!l && l.getAttribute('href').endsWith(%s) && !!l.sheet})()" % json.dumps("/" + slug + ".css")), 15, "the %s stylesheet" % slug)
    expected = declared_faces(slug)
    registered = lambda: sorted(json.loads(cdp.eval("JSON.stringify([...document.fonts].map(f=>f.family.replace(/\"/g,'')+' '+f.weight))") or "[]"))
    wait_for(lambda: registered() == expected, 15, "%s's own font faces to be registered (%s)" % (slug, expected))
    faces = json.loads(cdp.eval("Promise.all([...document.fonts].map(f=>f.load().then(()=>f.family.replace(/\"/g,'')+' '+f.weight+' '+f.status,()=>f.family+' '+f.weight+' error'))).then(s=>JSON.stringify(s))") or "[]")
    if not expected or any(not s.endswith(" loaded") for s in faces):
        raise RuntimeError("%s: a declared font face did not load: %s" % (slug, faces))
    time.sleep(0.3)
    return faces


AUDIT_JS = r"""
(() => {
  const nums = (s) => s.split(/[\s,\/]+/).filter(Boolean).map(Number);
  const parse = (s) => {
    let m = s.match(/^rgba?\(([^)]+)\)/);
    if (m) { const p = nums(m[1]); return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1]; }
    m = s.match(/^color\(srgb ([^)]+)\)/);
    if (m) { const p = nums(m[1]); return [p[0] * 255, p[1] * 255, p[2] * 255, p.length > 3 ? p[3] : 1]; }
    return null;
  };
  let unparsed = 0;
  const over = (t, b) => [t[0] * t[3] + b[0] * (1 - t[3]), t[1] * t[3] + b[1] * (1 - t[3]), t[2] * t[3] + b[2] * (1 - t[3]), 1];
  const bgOf = (el) => {
    const layers = [];
    for (let e = el; e; e = e.parentElement) {
      const c = parse(getComputedStyle(e).backgroundColor);
      if (c === null) { unparsed++; continue; }
      if (c[3] > 0) layers.push(c);
      if (c[3] >= 1) break;
    }
    let base = [255, 255, 255, 1];
    for (const c of layers.reverse()) base = over(c, base);
    return base;
  };
  const lin = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
  const lum = (c) => 0.2126 * lin(c[0]) + 0.7152 * lin(c[1]) + 0.0722 * lin(c[2]);
  const root = document.querySelector('.la-modal') || document.body;
  const out = [], seen = new Set();
  const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  while (w.nextNode()) {
    const t = w.currentNode, txt = t.textContent.trim();
    if (!txt) continue;
    const el = t.parentElement;
    if (!el || seen.has(el) || el.closest('script,style,[hidden],[disabled],[aria-hidden="true"]')) continue;
    seen.add(el);
    const cs = getComputedStyle(el), r = el.getBoundingClientRect();
    if (cs.visibility === 'hidden' || cs.display === 'none' || r.width < 2 || r.height < 2 || +cs.opacity === 0) continue;
    let fg = parse(cs.color);
    if (fg === null) { unparsed++; continue; }
    const bg = bgOf(el);
    if (fg[3] < 1) fg = over(fg, bg);
    const a = lum(fg), b = lum(bg);
    const ratio = (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
    out.push({ ratio: +ratio.toFixed(2), text: txt.slice(0, 26), el: el.tagName.toLowerCase() + (el.className && typeof el.className === 'string' ? '.' + el.className.split(' ')[0] : '') });
  }
  out.sort((x, y) => x.ratio - y.ratio);
  return {
    runs: out.length, below3: out.filter((x) => x.ratio < 3).length, below45: out.filter((x) => x.ratio < 4.5).length,
    worst: out.slice(0, 3), unparsed,
    overflowX: document.documentElement.scrollWidth > window.innerWidth + 1,
    modalOverflow: (() => { const m = document.querySelector('.la-modal'); if (!m) return false; const r = m.getBoundingClientRect(); return r.left < -1 || r.top < -1 || r.right > innerWidth + 1 || r.bottom > innerHeight + 1; })(),
  };
})()
"""


def audit(cdp) -> dict:
    return cdp.eval(AUDIT_JS)


def fmt(a: dict) -> str:
    w = "; ".join("%.2f %s %r" % (x["ratio"], x["el"], x["text"]) for x in a["worst"])
    return "%3d runs, <3:1 %2d, <4.5:1 %3d%s%s%s | worst: %s" % (
        a["runs"], a["below3"], a["below45"], ", OVERFLOW-X" if a["overflowX"] else "", ", MODAL-OFF-SCREEN" if a["modalOverflow"] else "",
        (", %d unparsed colours" % a["unparsed"]) if a["unparsed"] else "", w)
