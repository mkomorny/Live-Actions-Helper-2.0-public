"""BUILD 2 -- Tk pushed as hard as it goes.

Same screen as build 1, but aiming at the kit look: rounded corners, soft glow
shadows and gradient accents, drawn with Pillow onto tk.Canvas, with the palette and
radii read out of a design kit's own tokens.css (default: cyber-neon-pink).

Every custom component is bracketed by  >>> COMPONENT / <<< COMPONENT  markers so
tools/loc_report.py can report exactly what each one cost. What Tk cannot do is
called out inline with  LIMIT:  comments.

Run:  python tk_pushed.py [theme-slug]
"""

from __future__ import annotations

import re
import sys
import tkinter as tk
from pathlib import Path
from tkinter import font as tkfont
from typing import Any, Callable

from PIL import Image, ImageDraw, ImageFilter, ImageTk

HERE = Path(__file__).resolve().parent
ROUND = HERE.parent
REPO = ROUND.parent.parent

TRACKS = [("Drums", "MIDI"), ("Bass", "MIDI"), ("Chords", "MIDI"), ("Lead", "MIDI"), ("Vox", "AUD"),
          ("Guitar DI", "AUD"), ("FX Risers", "AUD"), ("A  Reverb", "RET"), ("B  Delay", "RET"), ("Master", "MST")]


def load_tools() -> list[dict[str, Any]]:
    import json
    return [{**json.loads(p.read_text(encoding="utf-8"))} for p in sorted((REPO / "tools").glob("*/tool.json"))]


# >>> COMPONENT theme_loader   (what a kit file can drive in Tk: colours + radii + font names)
class Theme:
    def __init__(self, slug: str) -> None:
        css = (ROUND / "themes" / f"{slug}.css").read_text(encoding="utf-8")

        def raw(name: str, default: str = "") -> str:
            m = re.search(rf"--kit-{name}:\s*([^;]+);", css)
            return m.group(1).strip() if m else default

        def hexcolor(name: str, default: str) -> str:
            v = raw(name, default)
            # LIMIT: Tk and PIL take hex; a kit written in rgb()/hsl()/color-mix() needs a converter.
            return v if re.fullmatch(r"#[0-9a-fA-F]{6}", v) else default

        px = lambda name, d: int(re.match(r"\d+", raw(name, str(d))).group())  # noqa: E731
        self.bg, self.bg2, self.surface = hexcolor("bg", "#000000"), hexcolor("bg-subtle", "#111111"), hexcolor("surface", "#222222")
        self.text, self.muted, self.border = hexcolor("text", "#ffffff"), hexcolor("text-muted", "#999999"), hexcolor("border", "#333333")
        self.accent, self.accent_text = hexcolor("accent", "#ff00aa"), hexcolor("accent-text", "#ffffff")
        self.r_md, self.r_lg = px("radius-md", 8), px("radius-lg", 16)
        families = set(tkfont.families())
        want = [f.strip().strip("'\"") for f in raw("font-body", "").split(",")] + ["Segoe UI"]
        self.family = next((f for f in want if f in families), "Segoe UI")
        # LIMIT: shadows, motion curves, and Google-Fonts imports in the kit have no Tk equivalent
        # and are ignored; the glow below is hand-tuned, not read from --kit-shadow-md.
# <<< COMPONENT theme_loader


# >>> COMPONENT plate   (rounded rect + glow, as an image -- Tk has no border-radius, alpha or blur)
_CACHE: dict[tuple, ImageTk.PhotoImage] = {}


def plate(w: int, h: int, r: int, fill: str, outline: str | None = None, glow: str | None = None, glow_r: int = 0,
          gradient: tuple[str, str] | None = None) -> ImageTk.PhotoImage:
    key = (w, h, r, fill, outline, glow, glow_r, gradient)
    if key in _CACHE:
        return _CACHE[key]
    S, pad = 3, glow_r * 2 if glow else 0                      # 3x supersample: Pillow's shapes are not anti-aliased
    W, H = (w + 2 * pad) * S, (h + 2 * pad) * S
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    box = (pad * S, pad * S, (pad + w) * S - 1, (pad + h) * S - 1)
    if glow:
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(g).rounded_rectangle(box, r * S, fill=glow + "aa")
        im = Image.alpha_composite(im, g.filter(ImageFilter.GaussianBlur(glow_r * S / 2)))
    body = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(body).rounded_rectangle(box, r * S, fill=fill, outline=outline, width=S if outline else 0)
    if gradient:                                                # fake a linear gradient: paint columns, mask by the plate
        strip = Image.new("RGBA", (W, H))
        a, b = [tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) for c in gradient]
        d = ImageDraw.Draw(strip)
        for x in range(W):
            t = x / max(W - 1, 1)
            d.line([(x, 0), (x, H)], fill=tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3)) + (255,))
        body = Image.composite(strip, body, body.split()[3])
    im = Image.alpha_composite(im, body).resize((W // S, H // S), Image.LANCZOS)
    _CACHE[key] = ImageTk.PhotoImage(im)
    return _CACHE[key]
# <<< COMPONENT plate


# >>> COMPONENT button   (Canvas-drawn: hover / press / focus ring / disabled / keyboard, all hand-written)
class RoundButton(tk.Canvas):
    def __init__(self, parent: tk.Misc, th: Theme, text: str, command: Callable[[], None], kind: str = "primary",
                 mini: bool = False, canvas_bg: str | None = None) -> None:
        self.th, self.text, self.command, self.kind = th, text, command, kind
        self.font = tkfont.Font(family=th.family, size=8 if mini else 10, weight="bold")
        self.pad = 3 if kind == "primary" else 0                # room for the glow -- Canvas cannot draw outside itself
        w, h = self.font.measure(text) + (22 if not mini else 16) + 2 * self.pad * 2, (30 if not mini else 22) + 2 * self.pad * 2
        super().__init__(parent, width=w, height=h, bg=canvas_bg or parent.cget("bg"), highlightthickness=0, bd=0, takefocus=1)
        self.hover = self.down = self.focus = self.disabled = False
        for ev, fn in (("<Enter>", self._on_enter), ("<Leave>", self._on_leave), ("<ButtonPress-1>", self._on_down),
                       ("<ButtonRelease-1>", self._on_up), ("<FocusIn>", self._on_focus), ("<FocusOut>", self._on_blur),
                       ("<Return>", lambda e: self._fire()), ("<space>", lambda e: self._fire())):
            self.bind(ev, fn)
        self.bind("<Configure>", lambda e: self.paint())        # repaint-on-resize is not free either
        self.paint()

    def set_disabled(self, disabled: bool) -> None:
        self.disabled = disabled
        self.configure(cursor="arrow" if disabled else "hand2")
        self.paint()

    def paint(self) -> None:
        th, w, h = self.th, self.winfo_reqwidth(), self.winfo_reqheight()
        self.delete("all")
        if self.kind == "primary":
            fill, fg = ("#555555", "#999999") if self.disabled else (th.accent, th.accent_text)
            fill = self._shade(fill, 0.85) if self.down else (self._shade(fill, 1.12) if self.hover else fill)
            self.img = plate(w - 2 * self.pad * 2, h - 2 * self.pad * 2, th.r_md, fill, glow=None if self.disabled else th.accent,
                             glow_r=self.pad)
        else:
            fill, fg = (th.surface, th.text)
            fill = self._shade(fill, 1.35 if self.hover else 1.0)
            self.img = plate(w, h, th.r_md, fill, outline=th.accent if self.focus else th.border)
        self.create_image(w // 2, h // 2, image=self.img)
        self.create_text(w // 2, h // 2, text=self.text, fill=fg, font=self.font)
        if self.focus and self.kind == "primary":
            self.create_rectangle(2, 2, w - 3, h - 3, outline=th.text, dash=(2, 2))   # LIMIT: focus ring is a rectangle, not rounded

    @staticmethod
    def _shade(c: str, k: float) -> str:
        r, g, b = (int(c[i:i + 2], 16) for i in (1, 3, 5))
        return "#%02x%02x%02x" % tuple(min(255, int(v * k)) for v in (r, g, b))

    def _fire(self) -> None:
        if not self.disabled:
            self.command()

    def _on_enter(self, _e: tk.Event) -> None: self.hover = True; self.paint()
    def _on_leave(self, _e: tk.Event) -> None: self.hover = self.down = False; self.paint()
    def _on_down(self, _e: tk.Event) -> None: self.focus_set(); self.down = not self.disabled; self.paint()
    def _on_up(self, _e: tk.Event) -> None:
        was = self.down; self.down = False; self.paint()
        if was and self.hover: self._fire()
    def _on_focus(self, _e: tk.Event) -> None: self.focus = True; self.paint()
    def _on_blur(self, _e: tk.Event) -> None: self.focus = False; self.paint()
# <<< COMPONENT button


# >>> COMPONENT pill   (scope pill / kind tag / metric chip -- static rounded label)
def pill(parent: tk.Misc, th: Theme, text: str, color: str, size: int = 8, bg: str | None = None) -> tk.Canvas:
    f = tkfont.Font(family=th.family, size=size, weight="bold")
    w, h = f.measure(text) + 18, f.metrics("linespace") + 8
    c = tk.Canvas(parent, width=w, height=h, bg=bg or parent.cget("bg"), highlightthickness=0, bd=0)
    c.img = plate(w, h, h // 2, th.bg2, outline=color)  # type: ignore[attr-defined]
    c.create_image(w // 2, h // 2, image=c.img)
    c.create_text(w // 2, h // 2, text=text, fill=color, font=f)
    return c


def chip(parent: tk.Misc, th: Theme, label: str, value: str, bg: str) -> tk.Canvas:
    fl, fv = tkfont.Font(family=th.family, size=7, weight="bold"), tkfont.Font(family="Consolas", size=10, weight="bold")
    c = tk.Canvas(parent, width=10, height=46, bg=bg, highlightthickness=0, bd=0)   # width=10: Canvas requests 378px by default

    def draw(_e: Any = None) -> None:
        w = max(c.winfo_width(), 40)
        c.delete("all")
        c.img = plate(w, 44, th.r_md, th.bg, outline=th.border)  # type: ignore[attr-defined]
        c.create_image(w // 2, 23, image=c.img)
        c.create_text(w // 2, 14, text=label, fill=th.muted, font=fl)
        c.create_text(w // 2, 31, text=value, fill=th.text, font=fv)

    c.bind("<Configure>", draw)
    return c
# <<< COMPONENT pill


# >>> COMPONENT card   (tool card: shadow plate + gradient stripe + wrapped text + pill + button, laid out by hand)
class ToolCard(tk.Canvas):
    def __init__(self, parent: tk.Misc, th: Theme, tool: dict[str, Any], canvas_bg: str) -> None:
        super().__init__(parent, height=150, bg=canvas_bg, highlightthickness=0, bd=0)
        self.th, self.tool, self.hover = th, tool, False
        self.font_h = tkfont.Font(family=th.family, size=11, weight="bold")
        self.font_d = tkfont.Font(family=th.family, size=9)
        is_web, scope = tool.get("ui") == "webview", tool.get("scope")
        self.scope_txt = "SET-WIDE" if scope == "set" else ("WEB DIALOG" if is_web else "SELECTED TRACKS")
        self.scope_col = "#c084fc" if scope == "set" else ("#fbbf24" if is_web else th.accent)
        self.btn = RoundButton(self, th, "Open Dialog ↗" if is_web else "Open & Configure ▶", lambda: None, canvas_bg=th.surface)
        self.pill = pill(self, th, self.scope_txt, self.scope_col, bg=th.surface)
        self.bind("<Configure>", self.layout)
        self.bind("<Enter>", lambda e: self._hov(True))
        self.bind("<Leave>", lambda e: self._hov(False))

    def _hov(self, on: bool) -> None:
        self.hover = on
        self.layout()

    def layout(self, _e: Any = None) -> None:
        th, w = self.th, max(self.winfo_width(), 200)
        m = 8                                                    # margin for the glow
        self.delete("all")
        self.img = plate(w - 2 * m, 150 - 2 * m, th.r_lg, th.surface, outline=th.accent if self.hover else th.border,
                         glow=th.accent if self.hover else "#000000", glow_r=m // 2)
        self.create_image(w // 2, 75, image=self.img)
        self.stripe = plate(5, 150 - 2 * m - 24, 2, th.accent, gradient=(str(self.tool.get("accent") or th.accent), th.accent))
        self.create_image(m + 10, 75, image=self.stripe)
        self.create_text(m + 24, m + 20, anchor="w", text=self.tool.get("name", ""), fill=th.text, font=self.font_h)
        self.create_window(w - m - 12, m + 20, anchor="e", window=self.pill)
        # LIMIT: Canvas text has no line clamp / ellipsis -- clip by measuring, by hand.
        desc, lines, cur = str(self.tool.get("description", "")), [], ""
        for word in desc.split():
            if self.font_d.measure((cur + " " + word).strip()) > w - 2 * m - 44 and cur:
                lines.append(cur); cur = word
            else:
                cur = (cur + " " + word).strip()
        lines.append(cur)
        lines = lines[:3]
        if len(lines) == 3 and self.font_d.measure(lines[2] + "…") < w - 2 * m - 44:
            lines[2] += "…"
        self.create_text(m + 24, m + 40, anchor="nw", text="\n".join(lines), fill=th.muted, font=self.font_d)
        self.create_window(m + 24, 150 - m - 8, anchor="sw", window=self.btn)
# <<< COMPONENT card


# >>> COMPONENT track_row   (checkbox drawn by hand -- ttk/tk checkbuttons cannot be rounded or recoloured properly)
class TrackRow(tk.Canvas):
    def __init__(self, parent: tk.Misc, th: Theme, n: int, name: str, kind: str, on: bool, on_toggle: Callable[[], None]) -> None:
        super().__init__(parent, height=28, bg=th.surface, highlightthickness=0, bd=0, cursor="hand2", takefocus=1)
        self.th, self.n, self.name, self.kind, self.on, self.cb = th, n, name, kind, on, on_toggle
        self.font = tkfont.Font(family=th.family, size=10, weight="bold")
        self.bind("<Configure>", lambda e: self.paint())
        self.bind("<Button-1>", lambda e: self.toggle())
        self.bind("<space>", lambda e: self.toggle())
        self.bind("<Enter>", lambda e: self.paint(True))
        self.bind("<Leave>", lambda e: self.paint(False))

    def toggle(self) -> None:
        self.on = not self.on
        self.paint()
        self.cb()

    def paint(self, hover: bool = False) -> None:
        th, w = self.th, max(self.winfo_width(), 100)
        self.delete("all")
        if self.on or hover:
            self.bg_img = plate(w - 2, 26, th.r_md // 2, "#3a1030" if self.on else th.bg2)
            self.create_image(w // 2, 14, image=self.bg_img)
        self.box = plate(16, 16, 4, th.accent if self.on else th.bg, outline=th.accent if self.on else th.border)
        self.create_image(16, 14, image=self.box)
        if self.on:
            self.create_line(11, 14, 15, 18, 22, 10, fill=th.accent_text, width=2)
        self.create_text(34, 14, anchor="w", text=f"{self.n}  {self.name}", fill=th.text, font=self.font)
        self.create_text(w - 12, 14, anchor="e", text=self.kind, fill=th.accent if self.kind == "MIDI" else th.muted, font=("Consolas", 8, "bold"))
# <<< COMPONENT track_row


# >>> COMPONENT scroll   (scrollable region: same wheel routing as build 1; Canvas children must also be rebound)
def scrollable(parent: tk.Misc, bg: str) -> tuple[tk.Frame, tk.Frame]:
    outer = tk.Frame(parent, bg=bg)
    canvas = tk.Canvas(outer, bg=bg, highlightthickness=0, bd=0)
    inner = tk.Frame(canvas, bg=bg)
    win = canvas.create_window((0, 0), window=inner, anchor="nw")
    inner.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))
    canvas.bind("<Enter>", lambda _e: canvas.bind_all("<MouseWheel>", lambda ev: canvas.yview_scroll(int(-ev.delta / 120), "units")))
    canvas.bind("<Leave>", lambda _e: canvas.unbind_all("<MouseWheel>"))
    canvas.pack(fill="both", expand=True)                       # LIMIT: no themeable scrollbar -- a drawn one is another ~40 lines; omitted
    return outer, inner
# <<< COMPONENT scroll


# >>> COMPONENT nav   (pill tabs)
def nav_tabs(parent: tk.Misc, th: Theme, active: str) -> tk.Frame:
    row = tk.Frame(parent, bg=th.bg)
    for key, label in (("actions", "⚡ Actions"), ("genius", "Genius"), ("settings", "Preferences")):
        RoundButton(row, th, label, lambda: None, kind="primary" if key == active else "ghost", canvas_bg=th.bg).pack(side="left", padx=3, pady=6)
    return row
# <<< COMPONENT nav


def build_sidebar(parent: tk.Frame, th: Theme) -> None:
    pad = tk.Frame(parent, bg=th.bg2)
    pad.pack(fill="both", expand=True, padx=14, pady=14)
    tk.Label(pad, text="LIVE ACTIONS", bg=th.bg2, fg=th.text, font=(th.family, 14, "bold"), anchor="w").pack(fill="x", pady=(0, 12))
    tk.Label(pad, text="LIVE SET", bg=th.bg2, fg=th.muted, font=(th.family, 8, "bold"), anchor="w").pack(fill="x")
    tk.Label(pad, text="Neon Nights 128.als", bg=th.bg2, fg=th.text, font=(th.family, 10, "bold"), anchor="w").pack(fill="x", pady=(2, 6))
    chips = tk.Frame(pad, bg=th.bg2)
    chips.pack(fill="x", pady=(0, 10))
    for i, (k, v) in enumerate((("BPM", "128.00"), ("SIG", "4/4"), ("TRACKS", "10"))):
        chip(chips, th, k, v, th.bg2).pack(side="left", fill="x", expand=True, padx=(0 if i == 0 else 3, 0))
    tk.Label(pad, text="TARGET TRACKS", bg=th.bg2, fg=th.muted, font=(th.family, 8, "bold"), anchor="w").pack(fill="x", pady=(4, 4))
    q = tk.Frame(pad, bg=th.bg2)
    q.pack(fill="x", pady=(0, 6))
    for name in ("All", "None", "Live Sel"):
        RoundButton(q, th, name, lambda: None, kind="ghost", mini=True).pack(side="left", padx=(0, 5))
    box, host = scrollable(pad, th.bg2)
    box.pack(fill="both", expand=True)
    for i, (name, kind) in enumerate(TRACKS, 1):
        TrackRow(host, th, i, name, kind, i in (2, 3, 4), lambda: None).pack(fill="x", pady=1)


def main() -> None:
    slug = next((a for a in sys.argv[1:] if not a.startswith("--") and not a.endswith(".png")), "cyber-neon-pink")
    root = tk.Tk()                                                # font.families() needs a live root
    th = Theme(slug)
    root.title(f"Build 2 -- Tk pushed hard ({slug})")
    root.geometry("1360x820")
    root.configure(bg=th.bg)
    side = tk.Frame(root, bg=th.bg2, width=290)
    side.pack(side="left", fill="y")
    side.pack_propagate(False)
    build_sidebar(side, th)
    mainp = tk.Frame(root, bg=th.bg)
    mainp.pack(side="left", fill="both", expand=True, padx=18, pady=12)
    head = tk.Frame(mainp, bg=th.bg)
    head.pack(fill="x", pady=(0, 10))
    tk.Label(head, text="Studio Actions", bg=th.bg, fg=th.text, font=(th.family, 16, "bold")).pack(side="left")
    nav_tabs(head, th, "actions").pack(side="right")
    box, host = scrollable(mainp, th.bg)
    box.pack(fill="both", expand=True)
    tools = load_tools()
    for i, t in enumerate(tools):                                # two columns
        ToolCard(host, th, t, th.bg).grid(row=i // 2, column=i % 2, sticky="ew", padx=4, pady=4)
    host.grid_columnconfigure(0, weight=1, uniform="c")
    host.grid_columnconfigure(1, weight=1, uniform="c")
    if "--shot" in sys.argv:
        out = sys.argv[sys.argv.index("--shot") + 1]
        root.after(1500, lambda: (_shot(root, out), root.destroy()))
    root.mainloop()


def _shot(root: tk.Tk, path: str) -> None:
    import ctypes
    from PIL import ImageGrab
    root.geometry("+40+20")
    root.update()
    k = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100.0
    x, y, w, h = root.winfo_rootx(), root.winfo_rooty(), root.winfo_width(), root.winfo_height()
    ImageGrab.grab((int(x * k), int(y * k), int((x + w) * k), int((y + h) * k))).resize((w, h)).save(path)


if __name__ == "__main__":
    main()
