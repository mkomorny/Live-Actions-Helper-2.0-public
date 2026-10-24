"""BUILD 1 -- the honest Tk baseline.

The Actions screen (sidebar + top nav + tool catalog) built with exactly the
widget approach and design tokens the app uses today: raw tk.Frame / tk.Label /
tk.Button with bg=/fg=/font= arguments. Tokens are imported from app/helper.py
itself (not retyped), and tool cards come from the real tool.json manifests.
The component functions are copies of helper.py's own (line refs in each marker).

Run:  python tk_baseline.py
"""

from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent
sys.path.insert(0, str(REPO / "app"))

import helper as H  # noqa: E402  -- real design tokens + load_tools, not copies

BG, BG_SIDEBAR, SURFACE, SURFACE_RAISED, SURFACE_INPUT = H.BG, H.BG_SIDEBAR, H.SURFACE, H.SURFACE_RAISED, H.SURFACE_INPUT
BORDER, BORDER_SUBTLE, ACCENT, ACCENT_TEXT, ACCENT_HOVER = H.BORDER, H.BORDER_SUBTLE, H.ACCENT, H.ACCENT_TEXT, H.ACCENT_HOVER
ACCENT_VIOLET, ACCENT_AMBER, TEXT, TEXT_MUTED, OK, WARN = H.ACCENT_VIOLET, H.ACCENT_AMBER, H.TEXT, H.TEXT_MUTED, H.OK, H.WARN
FONT_TITLE, FONT_HEADING, FONT_BODY, FONT_BODY_BOLD = H.FONT_TITLE, H.FONT_HEADING, H.FONT_BODY, H.FONT_BODY_BOLD
FONT_SMALL, FONT_SMALL_BOLD, FONT_SECTION, FONT_MONO_BOLD, FONT_TAB = H.FONT_SMALL, H.FONT_SMALL_BOLD, H.FONT_SECTION, H.FONT_MONO_BOLD, H.FONT_TAB

TRACKS = [("Drums", "MIDI"), ("Bass", "MIDI"), ("Chords", "MIDI"), ("Lead", "MIDI"), ("Vox", "AUD"),
          ("Guitar DI", "AUD"), ("FX Risers", "AUD"), ("A  Reverb", "RET"), ("B  Delay", "RET"), ("Master", "MST")]


# >>> COMPONENT button   (helper.py:1309-1346 _primary_btn/_ghost_btn/_pill_toggle_btn)
def primary_btn(parent: Any, text: str, command: Any, accent: str = ACCENT) -> tk.Button:
    return tk.Button(parent, text=text, command=command, bg=accent, fg=ACCENT_TEXT,
                     activebackground=ACCENT_HOVER, activeforeground=ACCENT_TEXT,
                     relief="flat", font=FONT_BODY_BOLD, padx=14, pady=6, bd=0, cursor="hand2")


def pill_btn(parent: Any, text: str, command: Any) -> tk.Button:
    return tk.Button(parent, text=text, command=command, bg=SURFACE_RAISED, fg=TEXT,
                     activebackground=BORDER, activeforeground=ACCENT,
                     relief="flat", font=FONT_SECTION, padx=6, pady=3, bd=0, cursor="hand2")
# <<< COMPONENT button


# >>> COMPONENT chip   (helper.py:1295-1307 _render_metric_chip)
def metric_chip(parent: tk.Frame, label: str, value: str) -> tk.Frame:
    chip = tk.Frame(parent, bg=SURFACE_INPUT, highlightbackground=BORDER_SUBTLE, highlightthickness=1)
    tk.Label(chip, text=label, bg=SURFACE_INPUT, fg=TEXT_MUTED, font=FONT_SECTION).pack(pady=(3, 0))
    tk.Label(chip, text=value, bg=SURFACE_INPUT, fg=TEXT, font=FONT_MONO_BOLD).pack(pady=(0, 4))
    return chip
# <<< COMPONENT chip


# >>> COMPONENT scroll   (helper.py:1348-1381 _create_scrollable_container)
def scrollable(parent: tk.Frame, bg: str) -> tuple[tk.Frame, tk.Frame]:
    outer = tk.Frame(parent, bg=bg)
    canvas = tk.Canvas(outer, bg=bg, highlightthickness=0, bd=0)
    sb = tk.Scrollbar(outer, orient="vertical", command=canvas.yview, bg=SURFACE, troughcolor=bg, width=8)
    canvas.configure(yscrollcommand=sb.set)
    inner = tk.Frame(canvas, bg=bg)
    win = canvas.create_window((0, 0), window=inner, anchor="nw")
    inner.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))

    def wheel(ev: tk.Event) -> None:
        canvas.yview_scroll(int(-1 * (ev.delta / 120)), "units")

    def bind_all(w: tk.Widget) -> None:
        w.bind("<MouseWheel>", wheel, add="+")
        for c in w.winfo_children():
            bind_all(c)

    canvas.bind("<Enter>", lambda _e: bind_all(inner))
    sb.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    return outer, inner
# <<< COMPONENT scroll


# >>> COMPONENT tool_card   (helper.py:1773-1819 _render_tool_card)
def tool_card(parent: tk.Frame, tool: dict[str, Any]) -> None:
    accent = str(tool.get("accent") or ACCENT)
    is_webview = str(tool.get("ui") or "") == "webview"
    scope = str(tool.get("scope") or "track")
    card = tk.Frame(parent, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
    card.pack(fill="x", pady=6, padx=2)
    tk.Frame(card, bg=accent, width=4).pack(side="left", fill="y")
    content = tk.Frame(card, bg=SURFACE)
    content.pack(side="left", fill="both", expand=True, padx=14, pady=12)
    top = tk.Frame(content, bg=SURFACE)
    top.pack(fill="x")
    tk.Label(top, text=str(tool.get("name") or tool["id"]), bg=SURFACE, fg=TEXT, font=FONT_HEADING, anchor="w").pack(side="left")
    tag = "Set-Wide" if scope == "set" else ("Web Dialog" if is_webview else "Selected Tracks")
    color = ACCENT_VIOLET if scope == "set" else (ACCENT_AMBER if is_webview else ACCENT)
    tk.Label(top, text="  " + tag + "  ", bg=SURFACE_INPUT, fg=color, font=FONT_SECTION).pack(side="right")
    tk.Label(content, text=str(tool.get("description") or "Opens its own interactive action screen."),
             bg=SURFACE, fg=TEXT_MUTED, font=FONT_SMALL, anchor="w", wraplength=540, justify="left").pack(fill="x", pady=(4, 10))
    row = tk.Frame(content, bg=SURFACE)
    row.pack(fill="x")
    primary_btn(row, "Open Interactive Dialog ↗" if is_webview else "Open & Configure ▶", lambda: None, accent=accent).pack(side="left")
# <<< COMPONENT tool_card


# >>> COMPONENT sidebar   (helper.py:595-713 _build_sidebar, trimmed to the same visible content)
def build_sidebar(parent: tk.Frame, checked: set[int]) -> None:
    pad = tk.Frame(parent, bg=BG_SIDEBAR)
    pad.pack(fill="both", expand=True, padx=14, pady=14)
    brand = tk.Frame(pad, bg=BG_SIDEBAR)
    brand.pack(fill="x", pady=(0, 14))
    tk.Label(brand, text="LIVE ACTIONS", bg=BG_SIDEBAR, fg=TEXT, font=FONT_TITLE, anchor="w").pack(side="left")
    tk.Label(brand, text="● ONLINE", bg=SURFACE_INPUT, fg=OK, font=FONT_SECTION, padx=8, pady=3).pack(side="right")
    tk.Label(pad, text="LIVE SET TELEMETRY", bg=BG_SIDEBAR, fg=TEXT_MUTED, font=FONT_SECTION, anchor="w").pack(fill="x", pady=(4, 2))
    card = tk.Frame(pad, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
    card.pack(fill="x", pady=(4, 14))
    inner = tk.Frame(card, bg=SURFACE)
    inner.pack(fill="x", padx=12, pady=10)
    tk.Label(inner, text="Neon Nights 128.als", bg=SURFACE, fg=TEXT, font=FONT_BODY_BOLD, anchor="w").pack(fill="x")
    chips = tk.Frame(inner, bg=SURFACE)
    chips.pack(fill="x", pady=(6, 8))
    for i, (k, v) in enumerate((("TEMPO", "128 BPM"), ("SIG", "4/4"), ("TRACKS", "10"))):
        metric_chip(chips, k, v).pack(side="left", fill="x", expand=True, padx=(0 if i == 0 else 3, 0))
    diag = tk.Frame(inner, bg=SURFACE)
    diag.pack(fill="x")
    for name in ("Ping", "Status", "Sync", "Reset"):
        tk.Button(diag, text=name, bg=SURFACE_RAISED, fg=TEXT, activebackground=BORDER, activeforeground=ACCENT,
                  relief="flat", font=FONT_SMALL, padx=8, pady=3, bd=0, cursor="hand2").pack(side="left", fill="x", expand=True, padx=1)
    tk.Label(pad, text="TARGET TRACKS", bg=BG_SIDEBAR, fg=TEXT_MUTED, font=FONT_SECTION, anchor="w").pack(fill="x", pady=(4, 2))
    deck = tk.Frame(pad, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
    deck.pack(fill="both", expand=True)
    di = tk.Frame(deck, bg=SURFACE)
    di.pack(fill="both", expand=True, padx=10, pady=10)
    pills = tk.Frame(di, bg=SURFACE)
    pills.pack(fill="x", pady=(0, 8))
    for i, name in enumerate(("ALL", "NONE", "LIVE SEL")):
        pill_btn(pills, name, lambda: None).pack(side="left", fill="x", expand=True, padx=(0 if i == 0 else 2, 0))
    summary = tk.Label(di, text="", bg=SURFACE, fg=ACCENT, font=FONT_SMALL_BOLD, anchor="w")
    summary.pack(fill="x", pady=(0, 6))
    box, host = scrollable(di, SURFACE)
    box.pack(fill="both", expand=True)
    vars_: list[tk.IntVar] = []

    def refresh() -> None:
        n = sum(v.get() for v in vars_)
        summary.configure(text=f"{n} tracks targeted" if n else "No tracks active")

    for i, (name, kind) in enumerate(TRACKS, 1):
        v = tk.IntVar(value=1 if i in checked else 0)
        vars_.append(v)
        row = tk.Frame(host, bg=SURFACE)
        row.pack(fill="x", pady=1)
        tk.Checkbutton(row, text=f"{i} · {name}", variable=v, command=refresh, bg=SURFACE, fg=TEXT, selectcolor=SURFACE_INPUT,
                       activebackground=SURFACE, activeforeground=TEXT, font=FONT_BODY, anchor="w", bd=0, highlightthickness=0).pack(side="left", fill="x", expand=True)
        tk.Label(row, text=kind, bg=SURFACE_INPUT, fg=ACCENT_VIOLET if kind == "MIDI" else TEXT_MUTED, font=FONT_SECTION, padx=4).pack(side="right")
    refresh()
# <<< COMPONENT sidebar


# >>> COMPONENT nav   (helper.py:759-789 _build_top_nav)
def build_nav(parent: tk.Frame, active: str = "actions") -> None:
    frame = tk.Frame(parent, bg=BG_SIDEBAR, highlightbackground=BORDER, highlightthickness=1)
    frame.pack(fill="x")
    for key, label in (("actions", "⚡  Tools & Actions"), ("genius", "🧠  Genius AI Studio"), ("settings", "⚙  Preferences & Ports")):
        b = tk.Button(frame, text=label, bg=SURFACE_RAISED if key == active else BG_SIDEBAR, fg=TEXT if key == active else TEXT_MUTED,
                      activebackground=SURFACE_RAISED, activeforeground=TEXT, relief="flat", font=FONT_TAB, padx=16, pady=8, bd=0, cursor="hand2")
        b.pack(side="left")
        b.bind("<Enter>", lambda _e, b=b, k=key: k != active and b.configure(bg=SURFACE_RAISED, fg=TEXT))
        b.bind("<Leave>", lambda _e, b=b, k=key: k != active and b.configure(bg=BG_SIDEBAR, fg=TEXT_MUTED))
# <<< COMPONENT nav


def main() -> None:
    root = tk.Tk()
    root.title("Build 1 -- Tk baseline (current style)")
    root.geometry("1360x820")
    root.configure(bg=BG)
    side = tk.Frame(root, bg=BG_SIDEBAR, width=290, highlightbackground=BORDER, highlightthickness=1)
    side.pack(side="left", fill="y")
    side.pack_propagate(False)
    build_sidebar(side, {2, 3, 4})
    main_pane = tk.Frame(root, bg=BG)
    main_pane.pack(side="left", fill="both", expand=True, padx=14, pady=10)
    build_nav(main_pane)
    head = tk.Frame(main_pane, bg=BG)
    head.pack(fill="x", pady=(10, 10))
    tk.Label(head, text="Studio Actions", bg=BG, fg=TEXT, font=FONT_TITLE).pack(side="left")
    tools = H.load_tools(REPO / "tools")
    tk.Label(head, text=f"{len(tools)} studio actions available", bg=BG, fg=TEXT_MUTED, font=FONT_SMALL).pack(side="right")
    box, host = scrollable(main_pane, BG)
    box.pack(fill="both", expand=True)
    for t in tools:
        tool_card(host, t)
    if "--shot" in sys.argv:
        root.after(1200, lambda: (_shot(root, sys.argv[sys.argv.index("--shot") + 1]), root.destroy()))
    root.mainloop()


def _shot(root: tk.Tk, path: str) -> None:
    """Grab the window's real pixels. The app is not DPI-aware (Windows bitmap-scales it),
    so Tk reports logical coordinates while the screen is physical -- scale between them."""
    import ctypes
    from PIL import ImageGrab
    root.geometry("+40+20")
    root.update()
    k = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100.0
    x, y, w, h = root.winfo_rootx(), root.winfo_rooty(), root.winfo_width(), root.winfo_height()
    img = ImageGrab.grab((int(x * k), int(y * k), int((x + w) * k), int((y + h) * k)))
    img.resize((w, h)).save(path)


if __name__ == "__main__":
    main()
