"""Live Actions — Obsidian Emerald Studio DAW Companion.

Desktop host for Ableton Live 12 Standard + Max for Live.
"""

from __future__ import annotations

import ctypes
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import tkinter as tk
import uuid
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import agent_registry
import ai_providers
import audio_sample
import genius_client
import host_tools
import settings_store
import tool_manifests
import tts_vocal
import webview_pane
from bbencut import bake_render as bbencut_bake_render
from bbencut import ffmpeg_util as bbencut_ffmpeg_util
from bbencut import roll_render as bbencut_roll_render
from bridge_client import BridgeClient

PING_EVERY_S = 1.0
OFFLINE_AFTER_S = 4.0

# ── Obsidian Emerald Studio Design Tokens ───────────────────────────────────────
BG             = "#0B0E14"   # Deep studio canvas ground
BG_SIDEBAR     = "#10141E"   # Recessed sidebar panel
SURFACE        = "#161D2B"   # Primary card surface
SURFACE_RAISED = "#1E273A"   # Interactive hover surface
SURFACE_INPUT  = "#121722"   # Input field surface
BORDER         = "#232F45"   # 1px structural container border
BORDER_SUBTLE  = "#1A2334"   # Nested divider hairplane
BORDER_FOCUS   = "#00F59B"   # Focus highlight border

ACCENT         = "#00F59B"   # Electric Ableton neon emerald
ACCENT_TEXT    = "#0B0E14"   # Dark high-contrast label over accent
ACCENT_HOVER   = "#1CFFAD"   # Brighter emerald on hover
ACCENT_VIOLET  = "#A855F7"   # Max for Live electric violet
ACCENT_AMBER   = "#FACC15"   # Warm amber accent

TEXT           = "#F1F5F9"   # Crisp primary text / headings
TEXT_MUTED     = "#7E8B9F"   # Secondary metadata / unit labels
TEXT_DIM       = "#4D5768"   # Subtle placeholder text

OK             = "#00F59B"   # Live / Connected / Success
WARN           = "#FACC15"   # Warning / Pending state
ERR            = "#FF4D4F"   # Error / Disconnected state

# Typography scale
FONT_TITLE     = ("Segoe UI Variable", 14, "bold")
FONT_TAB       = ("Segoe UI Variable", 10, "bold")
FONT_HEADING   = ("Segoe UI Variable", 11, "bold")
FONT_BODY      = ("Segoe UI Variable", 10)
FONT_BODY_BOLD = ("Segoe UI Variable", 10, "bold")
FONT_SMALL     = ("Segoe UI Variable", 9)
FONT_SMALL_BOLD= ("Segoe UI Variable", 9, "bold")
FONT_SECTION   = ("Segoe UI Variable", 8, "bold")
FONT_MONO      = ("Consolas", 9)
FONT_MONO_BOLD = ("Consolas", 9, "bold")

ROOT = Path(__file__).resolve().parent.parent


# ── Tool manifests + host-runtime tools ──────────────────────────────────────────
# Both live in tk-free modules now (tool_manifests.py, host_tools.py) so the
# WebView2 shell shares them; re-exported here under the same names.
load_tools = tool_manifests.load_tools
HOST_TOOLS = host_tools.HOST_TOOLS

# File-picker label for the Save As dialog, keyed by lowercase extension — used so a
# non-WAV result (Convert can emit these) doesn't get offered a WAV-only filter that
# would let the user save real MP3/FLAC/OGG bytes under a misleading ".wav" name.
_SAVE_FILE_LABELS: dict[str, str] = {
    ".wav": "WAV audio",
    ".aiff": "AIFF audio",
    ".aif": "AIFF audio",
    ".mp3": "MP3 audio",
    ".flac": "FLAC audio",
    ".ogg": "Ogg Vorbis",
}


def find_pal_local(configured: str) -> Path | None:
    candidates = []
    if configured:
        candidates.append(Path(configured))
    desktop = Path.home() / "Desktop"
    candidates.extend(
        [
            desktop / "Producer Pal Local.lnk",
            Path.home() / "Producer Pal Local" / "launcher" / "Launch.ps1",
            Path(r"C:\Users\<you>\My Apps\producer-pal-local\launcher\Launch.ps1"),
        ]
    )
    for path in candidates:
        if path.is_file():
            return path
    return None


# ── Main Studio Application Window ─────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(WINDOW_TITLE)
        self.geometry("1020x720")
        self.minsize(860, 580)
        self.configure(bg=BG)

        self.settings = settings_store.load_settings()
        self._connected = False
        # Step 3b of the arrangement-helper plan: one-shot cache of the most
        # recent arrangement_scan reply, consumed by _arrangement_helper_context()
        # the next time it runs -- see _open_arrangement_helper.
        self._arrangement_scan_result: dict[str, Any] | None = None
        self._current_page: str | None = None
        self._key_save_after: str | None = None
        self._last_saved_key = ""
        if settings_store.SETTINGS_PATH.is_file():
            self._last_saved_key = str(self.settings.get("api_key") or "")
        elif str(self.settings.get("api_key") or "").strip():
            try:
                settings_store.save_settings(self.settings)
                self._last_saved_key = str(self.settings.get("api_key") or "")
            except OSError:
                self._last_saved_key = ""

        self._log_lines: list[str] = []
        self._set_summary = "Not connected"
        self._genius_messages: list[dict[str, str]] = []
        self._busy = False
        self._tracks: list[dict[str, Any]] = []
        self._track_vars: dict[str, tk.BooleanVar] = {}
        self._open_tool: dict[str, Any] | None = None
        self._tool_field_vars: dict[str, tk.Variable] = {}
        self._tool_field_rows: list[dict[str, Any]] = []
        self._tool_form_gen = 0
        self._host_tool_running = False
        self._last_status: dict[str, Any] = {}
        self._webview: webview_pane.WebViewPane | None = None
        self._prev_geometry = ""
        self._webview_host: tk.Frame | None = None
        self._webview_tool_id = ""

        self._result_wait_id = 0
        self._result_wait_ids_seen: set[int] = set()
        self._host_track = ""
        self._log_expanded = False
        self._cancel_event: threading.Event | None = None

        self.bridge = BridgeClient(
            int(self.settings["listen_port"]),
            int(self.settings["bridge_port"]),
            self._on_osc,
        )

        self._build_style()
        self._build_studio_layout()
        self.bridge.start()
        self.after(200, self._tick)
        self.protocol("WM_DELETE_WINDOW", self._quit)
        self._start_raise_watcher()
        self.log("Studio Host initialized. Drop 'Live Actions Bridge.amxd' on an audio track in Live.")

    # ── Style Configurations ───────────────────────────────────────────────────

    def _build_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background=BG)
        style.configure("Sidebar.TFrame", background=BG_SIDEBAR)
        style.configure("Surface.TFrame", background=SURFACE)
        style.configure("TLabel", background=BG, foreground=TEXT, font=FONT_BODY)

        style.configure(
            "TCombobox",
            fieldbackground=SURFACE_INPUT, background=SURFACE_INPUT, foreground=TEXT,
            arrowcolor=TEXT, bordercolor=BORDER, lightcolor=SURFACE_INPUT, darkcolor=SURFACE_INPUT,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", SURFACE_INPUT)],
            foreground=[("readonly", TEXT)],
            selectbackground=[("readonly", SURFACE_INPUT)],
            selectforeground=[("readonly", TEXT)],
        )
        self.option_add("*TCombobox*Listbox.background", SURFACE_INPUT)
        self.option_add("*TCombobox*Listbox.foreground", TEXT)
        self.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
        self.option_add("*TCombobox*Listbox.selectForeground", ACCENT_TEXT)

        # Native menubar
        menubar = tk.Menu(
            self, bg=SURFACE, fg=TEXT,
            activebackground=ACCENT, activeforeground=ACCENT_TEXT,
            borderwidth=0, relief="flat",
        )
        tools_menu = tk.Menu(
            menubar, bg=SURFACE, fg=TEXT,
            activebackground=ACCENT, activeforeground=ACCENT_TEXT,
            tearoff=0,
        )
        tools_menu.add_command(label="Tools Catalog", command=lambda: self._show_page("actions"))
        tools_menu.add_command(label="Refresh Tools", command=self._refresh_tools)
        menubar.add_cascade(label="Actions", menu=tools_menu)

        genius_menu = tk.Menu(
            menubar, bg=SURFACE, fg=TEXT,
            activebackground=ACCENT, activeforeground=ACCENT_TEXT,
            tearoff=0,
        )
        genius_menu.add_command(label="Open Genius AI", command=lambda: self._show_page("genius"))
        genius_menu.add_command(label="Open Producer Pal Local…", command=self._open_pal_local)
        menubar.add_cascade(label="Genius", menu=genius_menu)

        settings_menu = tk.Menu(
            menubar, bg=SURFACE, fg=TEXT,
            activebackground=ACCENT, activeforeground=ACCENT_TEXT,
            tearoff=0,
        )
        settings_menu.add_command(label="Preferences & Settings", command=lambda: self._show_page("settings"))
        settings_menu.add_command(label="Open AppData Folder", command=self._open_settings_folder)
        menubar.add_cascade(label="Settings", menu=settings_menu)

        self.config(menu=menubar)

    # ── UI Construction: 2-Column DAW Studio Layout ────────────────────────────

    def _build_studio_layout(self) -> None:
        # Pinned Bottom Status / Drawer Bar
        self.bottom_bar = tk.Frame(self, bg=BG_SIDEBAR, height=32, highlightbackground=BORDER, highlightthickness=1)
        self.bottom_bar.pack(side="bottom", fill="x")
        self.bottom_bar.pack_propagate(False)

        self.console_drawer = tk.Frame(self, bg=SURFACE_INPUT, height=130, highlightbackground=BORDER, highlightthickness=1)
        # Hidden by default

        self._build_bottom_bar()

        # Workspace Container (Columns: Left Sidebar + Right Main Panel)
        workspace = tk.Frame(self, bg=BG)
        workspace.pack(side="top", fill="both", expand=True)

        # ── LEFT SIDEBAR (290px fixed width) ───────────────────────────────────
        sidebar = tk.Frame(workspace, bg=BG_SIDEBAR, width=290, highlightbackground=BORDER, highlightthickness=1)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        self._build_sidebar(sidebar)

        # ── RIGHT MAIN PANEL (Flexible expand) ─────────────────────────────────
        main_pane = tk.Frame(workspace, bg=BG)
        main_pane.pack(side="left", fill="both", expand=True, padx=(12, 16), pady=(12, 10))

        # Top Navigation Bar (Segmented Tab Selector)
        self._build_top_nav(main_pane)

        # Main Page Views
        self.pages_container = tk.Frame(main_pane, bg=BG)
        self.pages_container.pack(fill="both", expand=True, pady=(10, 0))

        self.pages: dict[str, tk.Frame] = {}
        self.pages["actions"] = self._build_actions_view(self.pages_container)
        self.pages["tool"] = self._build_tool_view(self.pages_container)
        self.pages["genius"] = self._build_genius_view(self.pages_container)
        self.pages["settings"] = self._build_settings_view(self.pages_container)

        self._show_page("actions")

    # ── Sidebar Construction ───────────────────────────────────────────────────

    def _build_sidebar(self, parent: tk.Frame) -> None:
        pad = tk.Frame(parent, bg=BG_SIDEBAR)
        pad.pack(fill="both", expand=True, padx=14, pady=14)

        # App Brand & Status Pip
        brand_row = tk.Frame(pad, bg=BG_SIDEBAR)
        brand_row.pack(fill="x", pady=(0, 14))

        tk.Label(
            brand_row, text="LIVE ACTIONS",
            bg=BG_SIDEBAR, fg=TEXT, font=FONT_TITLE, anchor="w",
        ).pack(side="left")

        self.badge = tk.Label(
            brand_row, text="● OFFLINE",
            bg=SURFACE_INPUT, fg=TEXT_MUTED,
            font=FONT_SECTION, padx=8, pady=3,
        )
        self.badge.pack(side="right")

        # ── Section 1: Live Set Telemetry Card ─────────────────────────────────
        self._render_section_title(pad, "LIVE SET TELEMETRY")
        
        set_card = tk.Frame(pad, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
        set_card.pack(fill="x", pady=(4, 14))

        set_inner = tk.Frame(set_card, bg=SURFACE)
        set_inner.pack(fill="x", padx=12, pady=10)

        self.set_name_label = tk.Label(
            set_inner, text="(Waiting for Live Set...)",
            bg=SURFACE, fg=TEXT, font=FONT_BODY_BOLD, anchor="w",
        )
        self.set_name_label.pack(fill="x")

        # Metric Chips (BPM, Sig, Tracks)
        chips_row = tk.Frame(set_inner, bg=SURFACE)
        chips_row.pack(fill="x", pady=(6, 8))

        self.chip_tempo = self._render_metric_chip(chips_row, "TEMPO", "— BPM")
        self.chip_sig = self._render_metric_chip(chips_row, "SIG", "—")
        self.chip_tracks = self._render_metric_chip(chips_row, "TRACKS", "0")

        self.chip_tempo.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.chip_sig.pack(side="left", fill="x", expand=True, padx=2)
        self.chip_tracks.pack(side="left", fill="x", expand=True, padx=(4, 0))

        # Host track readout
        self.host_track_label = tk.Label(
            set_inner, text="Bridge: Not active on a track",
            bg=SURFACE, fg=TEXT_MUTED, font=FONT_SMALL, anchor="w",
        )
        self.host_track_label.pack(fill="x", pady=(0, 8))

        # Bridge Diagnostics Action Row
        diag_row = tk.Frame(set_inner, bg=SURFACE)
        diag_row.pack(fill="x")
        self._ghost_btn(diag_row, "Ping", self._ping, mini=True).pack(side="left", fill="x", expand=True, padx=(0, 2))
        self._ghost_btn(diag_row, "Status", self._status, mini=True).pack(side="left", fill="x", expand=True, padx=2)
        self._ghost_btn(diag_row, "Sync", self._request_tracks, mini=True).pack(side="left", fill="x", expand=True, padx=2)
        self._ghost_btn(diag_row, "Reset", self._reset_bridge, mini=True).pack(side="left", fill="x", expand=True, padx=(2, 0))

        # ── Section 2: Target Track Selector ───────────────────────────────────
        # Two mutually-exclusive frames share this slot: TARGET TRACKS (the
        # checkbox picker the Actions tab reads via self._track_vars) and
        # SESSION TRACKS (a read-only list for Genius, which has no picker
        # state -- it resolves tracks itself from live_read_set/track_name).
        # _show_page swaps which one is packed based on the active page.
        self.target_tracks_frame = tk.Frame(pad, bg=BG_SIDEBAR)
        self.target_tracks_frame.pack(fill="both", expand=True)

        self._render_section_title(self.target_tracks_frame, "TARGET TRACKS")

        track_deck = tk.Frame(self.target_tracks_frame, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
        track_deck.pack(fill="both", expand=True, pady=(4, 0))

        deck_inner = tk.Frame(track_deck, bg=SURFACE)
        deck_inner.pack(fill="both", expand=True, padx=10, pady=10)

        # Quick Select Pills Row
        pill_row = tk.Frame(deck_inner, bg=SURFACE)
        pill_row.pack(fill="x", pady=(0, 8))

        self._pill_toggle_btn(pill_row, "ALL", lambda: self._set_all_tracks(True)).pack(side="left", fill="x", expand=True, padx=(0, 2))
        self._pill_toggle_btn(pill_row, "NONE", lambda: self._set_all_tracks(False)).pack(side="left", fill="x", expand=True, padx=2)
        self._pill_toggle_btn(pill_row, "LIVE SEL", self._use_live_selection).pack(side="left", fill="x", expand=True, padx=(2, 0))

        # Track Summary Counter
        self.sidebar_track_summary = tk.Label(
            deck_inner, text="No tracks active",
            bg=SURFACE, fg=ACCENT, font=FONT_SMALL_BOLD, anchor="w",
        )
        self.sidebar_track_summary.pack(fill="x", pady=(0, 6))

        # Scrollable Track Items Container
        track_scroll_box, self.track_list_sidebar = self._create_scrollable_container(deck_inner, bg=SURFACE)
        track_scroll_box.pack(fill="both", expand=True)

        # ── Section 2b: Session Tracks (Genius, read-only) ─────────────────────
        self.session_tracks_frame = tk.Frame(pad, bg=BG_SIDEBAR)
        # Not packed here -- _show_page packs this instead of
        # target_tracks_frame when the Genius page is active.

        self._render_section_title(self.session_tracks_frame, "SESSION TRACKS")

        session_deck = tk.Frame(self.session_tracks_frame, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
        session_deck.pack(fill="both", expand=True, pady=(4, 0))

        session_deck_inner = tk.Frame(session_deck, bg=SURFACE)
        session_deck_inner.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Label(
            session_deck_inner,
            text="Genius resolves tracks itself (by number or name) -- nothing to tick here.",
            bg=SURFACE, fg=TEXT_MUTED, font=FONT_SMALL, anchor="w", justify="left", wraplength=220,
        ).pack(fill="x", pady=(0, 8))

        session_scroll_box, self.session_track_list = self._create_scrollable_container(session_deck_inner, bg=SURFACE)
        session_scroll_box.pack(fill="both", expand=True)

    def _fill_session_track_list(self) -> None:
        host = getattr(self, "session_track_list", None)
        if host is None:
            return
        for child in host.winfo_children():
            child.destroy()

        if not self._tracks:
            tk.Label(
                host, text="No tracks detected.\nConnect to Live to list tracks.",
                bg=SURFACE, fg=TEXT_MUTED, font=FONT_SMALL, justify="left",
            ).pack(anchor="w", padx=6, pady=8)
            return

        for i, track in enumerate(self._tracks):
            kind = str(track.get("kind") or "audio").lower()
            name = str(track.get("name") or track.get("key") or "")
            mixer_n = track.get("index")
            mixer_n = (mixer_n + 1) if isinstance(mixer_n, int) else (i + 1)
            devices = track.get("devices") or []
            dev_str = ", ".join(str(d) for d in devices) if devices else "(none)"
            kind_tag = "MIDI" if kind == "midi" else ("RET" if kind == "return" else ("MST" if kind == "master" else "AUD"))

            row = tk.Frame(host, bg=SURFACE)
            row.pack(fill="x", pady=2)

            tk.Label(
                row, text=f"{mixer_n} · {name}",
                bg=SURFACE, fg=TEXT, font=FONT_BODY, anchor="w",
            ).pack(side="left", fill="x", expand=True)

            tk.Label(
                row, text=kind_tag,
                bg=SURFACE_INPUT, fg=ACCENT_VIOLET if kind == "midi" else TEXT_MUTED,
                font=FONT_SECTION, padx=4, pady=1,
            ).pack(side="right", padx=(2, 2))

            tk.Label(
                host, text=dev_str,
                bg=SURFACE, fg=TEXT_MUTED, font=FONT_SMALL, anchor="w", justify="left", wraplength=220,
            ).pack(fill="x", padx=(2, 0), pady=(0, 4))

    # ── Top Navigation Bar ─────────────────────────────────────────────────────

    def _build_top_nav(self, parent: tk.Frame) -> None:
        nav_frame = tk.Frame(parent, bg=BG_SIDEBAR, highlightbackground=BORDER, highlightthickness=1)
        nav_frame.pack(fill="x")

        self.nav_buttons: dict[str, tk.Button] = {}

        tabs = [
            ("actions", "⚡  Tools & Actions"),
            ("genius", "🧠  Genius AI Studio"),
            ("settings", "⚙  Preferences & Ports"),
        ]

        for key, label in tabs:
            btn = tk.Button(
                nav_frame, text=label,
                command=lambda k=key: self._show_page(k),
                bg=BG_SIDEBAR, fg=TEXT_MUTED,
                activebackground=SURFACE_RAISED, activeforeground=TEXT,
                relief="flat", font=FONT_TAB,
                padx=16, pady=8, bd=0, cursor="hand2",
            )
            btn.pack(side="left")
            btn.bind("<Enter>", lambda e, b=btn, k=key: self._on_nav_hover(b, k, True))
            btn.bind("<Leave>", lambda e, b=btn, k=key: self._on_nav_hover(b, k, False))
            self.nav_buttons[key] = btn

    def _on_nav_hover(self, btn: tk.Button, key: str, entering: bool) -> None:
        active = "actions" if self._current_page == "tool" else self._current_page
        if key == active:
            return
        btn.configure(bg=SURFACE_RAISED if entering else BG_SIDEBAR, fg=TEXT if entering else TEXT_MUTED)

    # ── Bottom Status Bar & Expandable Console Drawer ──────────────────────────

    def _build_bottom_bar(self) -> None:
        bar = self.bottom_bar

        # Left ticker
        self.status_ticker = tk.Label(
            bar, text="Ready. Live Actions OSC Bridge listening on localhost.",
            bg=BG_SIDEBAR, fg=TEXT_MUTED, font=FONT_MONO, anchor="w",
        )
        self.status_ticker.pack(side="left", padx=12)

        # Right Actions: Toggle Console Log + Copy
        right_actions = tk.Frame(bar, bg=BG_SIDEBAR)
        right_actions.pack(side="right", padx=8)

        self.console_toggle_btn = tk.Button(
            right_actions, text="▲ Console Log",
            command=self._toggle_console_drawer,
            bg=SURFACE, fg=TEXT, activebackground=SURFACE_RAISED, activeforeground=TEXT,
            relief="flat", font=FONT_SECTION, padx=8, pady=2, bd=0, cursor="hand2",
        )
        self.console_toggle_btn.pack(side="right", padx=(4, 0))

        tk.Button(
            right_actions, text="Copy",
            command=self._copy_log,
            bg=SURFACE, fg=TEXT_MUTED, activebackground=SURFACE_RAISED, activeforeground=TEXT,
            relief="flat", font=FONT_SECTION, padx=6, pady=2, bd=0, cursor="hand2",
        ).pack(side="right")

        # ── Setup the Drawer Contents ──────────────────────────────────────────
        drawer = self.console_drawer
        drawer_pad = tk.Frame(drawer, bg=SURFACE_INPUT)
        drawer_pad.pack(fill="both", expand=True, padx=8, pady=6)

        self.log_widget = tk.Text(
            drawer_pad, height=5,
            bg=SURFACE_INPUT, fg=TEXT, insertbackground=ACCENT,
            relief="flat", font=FONT_MONO, wrap="word",
            state="disabled", bd=0,
        )
        log_sb = tk.Scrollbar(
            drawer_pad, orient="vertical", command=self.log_widget.yview,
            bg=SURFACE, troughcolor=SURFACE_INPUT, width=8,
        )
        self.log_widget.configure(yscrollcommand=log_sb.set)
        log_sb.pack(side="right", fill="y")
        self.log_widget.pack(side="left", fill="both", expand=True)

    def _toggle_console_drawer(self) -> None:
        self._log_expanded = not self._log_expanded
        if self._log_expanded:
            self.console_drawer.pack(side="bottom", fill="x", before=self.bottom_bar)
            self.console_toggle_btn.configure(text="▼ Hide Log")
        else:
            self.console_drawer.pack_forget()
            self.console_toggle_btn.configure(text="▲ Console Log")

    # ── View 1: Tools Catalog View ─────────────────────────────────────────────

    def _build_actions_view(self, parent: tk.Frame) -> tk.Frame:
        view = tk.Frame(parent, bg=BG)

        # Header Info Banner
        header = tk.Frame(view, bg=BG)
        header.pack(fill="x", pady=(4, 10))

        tk.Label(
            header, text="Studio Actions",
            bg=BG, fg=TEXT, font=FONT_TITLE, anchor="w",
        ).pack(side="left")

        self.tools_count_label = tk.Label(
            header, text="Loading tools...",
            bg=BG, fg=TEXT_MUTED, font=FONT_SMALL, anchor="e",
        )
        self.tools_count_label.pack(side="right")

        # How-to-use setup guide banner (always shown)
        self.setup_banner = tk.Frame(
            view, bg=SURFACE_INPUT,
            highlightbackground=BORDER, highlightthickness=1,
        )
        self.setup_banner.pack(fill="x", pady=(0, 10))

        banner_inner = tk.Frame(self.setup_banner, bg=SURFACE_INPUT)
        banner_inner.pack(fill="x", padx=14, pady=10)

        tk.Label(
            banner_inner, text="HOW TO USE",
            bg=SURFACE_INPUT, fg=ACCENT, font=FONT_SECTION, anchor="w",
        ).pack(fill="x")

        steps = [
            "① Drop  'Live Actions Bridge.amxd'  onto any audio track in Ableton Live.",
            "② Tick the tracks you want to affect in the TARGET TRACKS list on the left.",
            "③ Click a tool card below → fill in any fields → press  ▶ Run Now.",
        ]
        for step in steps:
            tk.Label(
                banner_inner, text=step,
                bg=SURFACE_INPUT, fg=TEXT_MUTED, font=FONT_SMALL,
                anchor="w", justify="left",
            ).pack(fill="x", pady=1)

        self.offline_hint = tk.Label(
            banner_inner,
            text="⚠  Bridge is OFFLINE — start Ableton Live and load the bridge device.",
            bg=SURFACE_INPUT, fg=WARN, font=FONT_SMALL_BOLD, anchor="w",
        )
        self.offline_hint.pack(fill="x", pady=(6, 0))

        # Tools Grid Container
        tools_scroll_box, self.tools_catalog_frame = self._create_scrollable_container(view, bg=BG)
        tools_scroll_box.pack(fill="both", expand=True)

        self._refresh_tools()
        return view

    # ── View 2: Active Tool Detail & Execution View ────────────────────────────

    def _build_tool_view(self, parent: tk.Frame) -> tk.Frame:
        view = tk.Frame(parent, bg=BG)

        # Sticky run footer (always at bottom of tool view)
        self.run_footer = tk.Frame(view, bg=BG_SIDEBAR, highlightbackground=BORDER, highlightthickness=1)
        self.run_footer.pack(side="bottom", fill="x")

        run_footer_inner = tk.Frame(self.run_footer, bg=BG_SIDEBAR)
        run_footer_inner.pack(fill="x", padx=14, pady=10)

        self.run_btn = tk.Button(
            run_footer_inner, text="▶  Run Now",
            command=self._run_open_tool,
            bg=ACCENT, fg=ACCENT_TEXT,
            activebackground=ACCENT_HOVER, activeforeground=ACCENT_TEXT,
            relief="flat", font=("Segoe UI Variable", 12, "bold"),
            padx=24, pady=8, bd=0, cursor="hand2",
        )
        self.run_btn.pack(side="left")

        self.run_status_label = tk.Label(
            run_footer_inner, text="",
            bg=BG_SIDEBAR, fg=TEXT_MUTED, font=FONT_SMALL,
        )
        self.run_status_label.pack(side="left", padx=14)

        self._ghost_btn(
            run_footer_inner, "← Back to Actions",
            lambda: self._show_page("actions"), mini=True,
        ).pack(side="right")

        self._ghost_btn(
            run_footer_inner, "Reset Preferences",
            self._reset_tool_prefs, mini=True,
        ).pack(side="right", padx=(0, 8))

        self.run_result_frame = tk.Frame(self.run_footer, bg=BG_SIDEBAR)
        result_inner = tk.Frame(self.run_result_frame, bg=BG_SIDEBAR)
        result_inner.pack(fill="x", padx=14, pady=(0, 10))
        self.run_result_label = tk.Label(
            result_inner, text="",
            bg=BG_SIDEBAR, fg=TEXT, font=FONT_SMALL, anchor="w", justify="left",
        )
        self.run_result_label.pack(side="left", fill="x", expand=True)
        self._ghost_btn(
            result_inner, "Open Folder ↗", self._open_last_result_folder, mini=True,
        ).pack(side="right")
        self._last_result_path: str | None = None

        self.tool_body = tk.Frame(view, bg=BG)
        self.tool_body.pack(fill="both", expand=True)
        return view

    # ── View 3: Genius AI Studio View ──────────────────────────────────────────

    def _build_genius_view(self, parent: tk.Frame) -> tk.Frame:
        view = tk.Frame(parent, bg=BG)

        # Top Bar with Library Status & Shortcuts
        top_bar = tk.Frame(view, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
        top_bar.pack(fill="x", pady=(4, 10))

        top_inner = tk.Frame(top_bar, bg=SURFACE)
        top_inner.pack(fill="x", padx=12, pady=8)

        self.genius_status = tk.Label(
            top_inner, text="Checking Genius index...",
            bg=SURFACE, fg=TEXT_MUTED, font=FONT_SMALL, anchor="w",
        )
        self.genius_status.pack(side="left")

        actions_right = tk.Frame(top_inner, bg=SURFACE)
        actions_right.pack(side="right")

        self.genius_top_stop_btn = tk.Button(
            actions_right, text="⏹ Stop",
            command=self._stop_genius,
            bg=ERR, fg="#FFFFFF", activebackground="#D32F2F", activeforeground="#FFFFFF",
            font=FONT_SECTION, relief="flat", padx=8, pady=2, cursor="hand2", bd=0,
        )

        tk.Label(actions_right, text="Agent:", bg=SURFACE, fg=TEXT_MUTED, font=FONT_SMALL).pack(side="left", padx=(0, 4))
        self.genius_agent_switch_var = tk.StringVar(value="(none)")
        self.genius_agent_switch = ttk.Combobox(
            actions_right, textvariable=self.genius_agent_switch_var,
            values=["(none)"], state="readonly", font=FONT_SMALL, width=20,
        )
        self.genius_agent_switch.pack(side="left", padx=(0, 10))
        self.genius_agent_switch.bind("<<ComboboxSelected>>", self._on_agent_switch_selected)

        self._ghost_btn(actions_right, "Clear Chat", self._clear_genius, mini=True).pack(side="left", padx=(0, 8))

        # Live Actions Bridge status indicator
        self.live_bridge_status_label = tk.Label(
            actions_right,
            text="● Live Bridge: Offline",
            bg=SURFACE, fg=TEXT_DIM, font=FONT_SECTION,
        )
        self.live_bridge_status_label.pack(side="left")

        # Chat Conversation Card
        chat_card = tk.Frame(view, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
        chat_card.pack(fill="both", expand=True)

        self.genius_chat = tk.Text(
            chat_card,
            bg=SURFACE, fg=TEXT, insertbackground=ACCENT,
            relief="flat", font=FONT_BODY, wrap="word",
            state="disabled", padx=14, pady=12, bd=0,
        )
        chat_sb = tk.Scrollbar(
            chat_card, orient="vertical", command=self.genius_chat.yview,
            bg=SURFACE_INPUT, troughcolor=SURFACE, width=8,
        )
        self.genius_chat.configure(yscrollcommand=chat_sb.set)
        chat_sb.pack(side="right", fill="y")
        self.genius_chat.pack(side="left", fill="both", expand=True)

        # Configure chat styling tags
        self.genius_chat.tag_configure("you",     foreground=ACCENT,        font=FONT_BODY_BOLD)
        self.genius_chat.tag_configure("genius",  foreground=ACCENT_VIOLET, font=FONT_BODY_BOLD)
        self.genius_chat.tag_configure("meta",    foreground=TEXT_MUTED,    font=FONT_SMALL)
        self.genius_chat.tag_configure("tool",    foreground=ACCENT_AMBER,  font=FONT_MONO)
        self.genius_chat.tag_configure("thinking", foreground="#94A3B8",    font=("Segoe UI", 9, "italic"))
        self.genius_chat.tag_configure("bubble_meta", foreground=TEXT_DIM,  font=FONT_SMALL)

        # Quick Prompt Chips Bar
        chips_bar = tk.Frame(view, bg=BG)
        chips_bar.pack(fill="x", pady=(8, 6))

        prompts = [
            "Create a 4-bar drum loop on an empty track",
            "Generate an 8-bar house beat with kick and hats",
            "How do I sidechain in Live?",
            "Explain Dorian vs Aeolian mode",
        ]
        for p in prompts:
            self._prompt_pill_btn(chips_bar, p, lambda text=p: self._fill_and_send_genius(text)).pack(side="left", padx=(0, 6))

        # Bottom Chat Input Deck
        entry_deck = tk.Frame(view, bg=SURFACE_INPUT, highlightbackground=BORDER, highlightthickness=1)
        entry_deck.pack(fill="x")

        self.genius_entry = tk.Text(
            entry_deck, height=3,
            bg=SURFACE_INPUT, fg=TEXT, insertbackground=ACCENT,
            relief="flat", font=FONT_BODY, wrap="word",
            padx=10, pady=8, bd=0,
        )
        self.genius_entry.pack(side="left", fill="both", expand=True)

        def _on_return(_e=None):
            # "break" unconditionally, even on _send_genius's early returns
            # (busy / empty text) -- otherwise tkinter's class binding still
            # inserts the newline Enter just typed, leaving a stray blank line.
            self._send_genius()
            return "break"

        self.genius_entry.bind("<Return>", _on_return)
        self.genius_entry.bind("<Shift-Return>", lambda _e: None)
        self.genius_entry.bind("<Control-Return>", _on_return)

        send_box = tk.Frame(entry_deck, bg=SURFACE_INPUT)
        send_box.pack(side="right", padx=10, pady=8)

        btn_row = tk.Frame(send_box, bg=SURFACE_INPUT)
        btn_row.pack(fill="x")

        self.genius_send_btn = self._primary_btn(btn_row, "Send ↵", self._send_genius)
        self.genius_send_btn.pack(side="left")

        self.genius_stop_btn = tk.Button(
            btn_row, text="⏹ Stop",
            command=self._stop_genius,
            bg=ERR, fg="#FFFFFF", activebackground="#D32F2F", activeforeground="#FFFFFF",
            font=FONT_BODY_BOLD, relief="flat", padx=12, pady=6, cursor="hand2", bd=0,
        )

        tk.Label(
            send_box, text="Enter to send · Shift+Enter = newline",
            bg=SURFACE_INPUT, fg=TEXT_DIM, font=FONT_SECTION,
        ).pack(pady=(4, 0))

        self._append_genius(
            "Genius",
            "I'm Producer Pal Genius — studio library plus full Pal-parity Live control through the Live Actions Bridge.\n"
            "Ask how-to from the books, or tell me to build tracks, native devices, clips, routing, and MIDI.",
            "meta",
        )
        self._refresh_genius_status()
        self.after(500, self._refresh_ppal_status)
        self._refresh_agent_switcher()
        return view

    def _fill_and_send_genius(self, text: str) -> None:
        self.genius_entry.delete("1.0", "end")
        self.genius_entry.insert("1.0", text)
        self._send_genius()

    # ── View 4: Settings & Configuration View ──────────────────────────────────

    def _build_settings_view(self, parent: tk.Frame) -> tk.Frame:
        view = tk.Frame(parent, bg=BG)

        # Scrolled Form Container
        scroll_outer, form_inner = self._create_scrollable_container(view, bg=BG)
        scroll_outer.pack(fill="both", expand=True, pady=(4, 10))

        self.fields: dict[str, tk.Entry] = {}

        # Group 1: AI Provider & Genius Configuration
        self._render_card_header(form_inner, "1. AI PROVIDER & GENIUS CONFIGURATION")
        card_ai = tk.Frame(form_inner, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
        card_ai.pack(fill="x", pady=(4, 14))
        inner_ai = tk.Frame(card_ai, bg=SURFACE)
        inner_ai.pack(fill="x", padx=14, pady=12)

        tk.Label(
            inner_ai, text="Saved API keys — paste any provider's key below (xAI, OpenAI, Gemini), "
            "detect it, then save it here to switch between keys later.",
            bg=SURFACE, fg=TEXT_MUTED, font=FONT_SMALL, anchor="w", justify="left", wraplength=760,
        ).pack(fill="x", pady=(0, 6))

        self._saved_keys_list = tk.Frame(inner_ai, bg=SURFACE)
        self._saved_keys_list.pack(fill="x", pady=(0, 10))
        self._fill_saved_keys_list()

        self._add_entry_field(inner_ai, "api_key", "API Key (any provider)", show="*")

        key_actions = tk.Frame(inner_ai, bg=SURFACE)
        key_actions.pack(fill="x", pady=(0, 8))

        self.show_key = tk.BooleanVar(value=False)
        tk.Checkbutton(
            key_actions, text="Show plain key",
            variable=self.show_key, command=self._toggle_key,
            bg=SURFACE, fg=TEXT_MUTED, selectcolor=SURFACE_INPUT,
            activebackground=SURFACE, activeforeground=TEXT,
            font=FONT_SMALL, bd=0,
        ).pack(side="left")

        self._ghost_btn(key_actions, "Detect provider", self._detect_provider_for_active_key, mini=True).pack(side="left", padx=(10, 0))
        self._ghost_btn(key_actions, "Test Connection", self._test_key, mini=True).pack(side="left", padx=10)

        self.key_save_status = tk.Label(
            key_actions, text="", bg=SURFACE, fg=OK, font=FONT_SMALL_BOLD,
        )
        self.key_save_status.pack(side="left", padx=6)

        provider_row = tk.Frame(inner_ai, bg=SURFACE)
        provider_row.pack(fill="x", pady=(0, 10))
        active_provider = ""
        for entry in (self.settings.get("api_keys") or []):
            if entry.get("id") == self.settings.get("active_api_key_id"):
                active_provider = str(entry.get("provider") or "")
                break
        self._active_provider_var = tk.StringVar(value=active_provider)
        tk.Label(provider_row, text="Provider:", bg=SURFACE, fg=TEXT_MUTED, font=FONT_SMALL).pack(side="left")
        self._provider_label = tk.Label(
            provider_row, textvariable=self._active_provider_var, bg=SURFACE, fg=TEXT, font=FONT_SMALL_BOLD,
        )
        self._provider_label.pack(side="left", padx=(6, 20))
        self._new_key_label_var = tk.StringVar()
        tk.Entry(
            provider_row, textvariable=self._new_key_label_var, width=18,
            bg=SURFACE_INPUT, fg=TEXT, insertbackground=ACCENT, relief="flat", font=FONT_BODY,
            highlightbackground=BORDER, highlightthickness=1,
        ).pack(side="left", ipady=3)
        self._ghost_btn(provider_row, "💾 Save as new key", self._save_current_key_as_new, mini=True).pack(side="left", padx=(6, 0))

        self._add_combobox_field(inner_ai, "model", "AI Model")
        self._ghost_btn(inner_ai, "↻ Refresh models", self._refresh_models_for_active_key, mini=True).pack(anchor="w", pady=(0, 10))
        self._add_entry_field(inner_ai, "api_base", "API Base Endpoint URL")

        self._add_combobox_field(inner_ai, "agent_picker", "Agent", readonly=True)
        self._ghost_btn(inner_ai, "➕ Enable agent", self._enable_picked_agent, mini=True).pack(anchor="w", pady=(0, 10))
        self._refresh_agent_picker()

        self._agent_cards_container = tk.Frame(inner_ai, bg=SURFACE)
        self._agent_cards_container.pack(fill="x", pady=(0, 4))
        self._render_agent_cards()

        # Group 2: Paths & Studio Directories
        self._render_card_header(form_inner, "2. LOCAL STUDIO DIRECTORIES & KNOWLEDGE")
        card_paths = tk.Frame(form_inner, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
        card_paths.pack(fill="x", pady=(4, 14))
        inner_paths = tk.Frame(card_paths, bg=SURFACE)
        inner_paths.pack(fill="x", padx=14, pady=12)

        self._add_path_field(inner_paths, "tools_dir", "Tools Folder (contains tool.json folders)", folder=True)
        self._add_path_field(inner_paths, "knowledge_dir", "Knowledgebase Library (contains INDEX.md)", folder=True)
        self._add_path_field(inner_paths, "music_db_dir", "Music/Audio Database (FTS5 search, per-topic)", folder=True)
        self._add_path_field(inner_paths, "samples_dir", "Ableton Samples Folder", folder=True)

        # Group 3: OSC Ports & Shortcuts
        self._render_card_header(form_inner, "3. LIVE OSC BRIDGE & PORTS")
        card_osc = tk.Frame(form_inner, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
        card_osc.pack(fill="x", pady=(4, 14))
        inner_osc = tk.Frame(card_osc, bg=SURFACE)
        inner_osc.pack(fill="x", padx=14, pady=12)

        ports_row = tk.Frame(inner_osc, bg=SURFACE)
        ports_row.pack(fill="x")
        self._add_entry_field(ports_row, "listen_port", f"App Listen Port (default {settings_store.DEFAULTS['listen_port']})", parent_side="left")
        self._add_entry_field(ports_row, "bridge_port", f"Bridge Send Port (default {settings_store.DEFAULTS['bridge_port']})", parent_side="left")

        self._add_path_field(inner_osc, "pal_local_shortcut", "Producer Pal Local Shortcut / Script (.lnk / .ps1)", folder=False)

        # Group 4: Audio Tools (TTS Vocal + Audio Sample) + TTS Profiles
        self._render_card_header(form_inner, "4. AUDIO TOOLS (TTS + SAMPLES)")
        card_tts = tk.Frame(form_inner, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
        card_tts.pack(fill="x", pady=(4, 14))
        inner_tts = tk.Frame(card_tts, bg=SURFACE)
        inner_tts.pack(fill="x", padx=14, pady=12)

        self._add_path_field(inner_tts, "tts_output_dir", "TTS Output Folder (blank = Samples Folder\\TTS)", folder=True)
        self._add_path_field(
            inner_tts, "audio_sample_output_dir",
            "Audio Sample Output Folder (blank = Samples Folder\\Audio Samples)", folder=True,
        )
        self._add_path_field(
            inner_tts, "ffmpeg_path", "ffmpeg.exe Path (blank = use PATH) — used by TTS Vocal and Audio Sample", folder=False,
        )

        tk.Label(
            inner_tts, text="Profiles (provider + API key + voice) used by the TTS Vocal tool.",
            bg=SURFACE, fg=TEXT_MUTED, font=FONT_SMALL, anchor="w",
        ).pack(fill="x", pady=(10, 4))

        self._tts_profiles_list = tk.Frame(inner_tts, bg=SURFACE)
        self._tts_profiles_list.pack(fill="x")

        self._tts_profile_rows: list[dict[str, Any]] = []
        for profile in (self.settings.get("tts_profiles") or []):
            self._add_tts_profile_row(dict(profile))
        if not self._tts_profile_rows:
            self._add_tts_profile_row({})

        self._ghost_btn(
            inner_tts, "+ Add Profile", lambda: self._add_tts_profile_row({}), mini=True,
        ).pack(anchor="w", pady=(8, 0))

        tk.Label(
            inner_tts,
            text=(
                "Voice cloning (xAI): create a custom voice for free in the xAI console "
                "(console.x.ai — up to 30 voices, via a short live recording), then paste "
                "the returned Voice ID above, or use “↻ Refresh voices” to "
                "pick it from the list. Only clone a voice you own or have permission to "
                "use. In-app upload isn't available — creating a custom voice through the "
                "API requires an Enterprise plan."
            ),
            bg=SURFACE, fg=TEXT_DIM, font=FONT_SMALL, anchor="w", justify="left", wraplength=760,
        ).pack(fill="x", pady=(10, 0))

        # Pinned Sticky Save Bar
        save_bar = tk.Frame(view, bg=BG)
        save_bar.pack(fill="x", pady=(6, 0))

        self._primary_btn(save_bar, "Save All Preferences", self._save_settings_ui).pack(side="left")
        tk.Label(
            save_bar, text="Settings are saved locally to %APPDATA%/Live Actions/settings.json",
            bg=BG, fg=TEXT_MUTED, font=FONT_SMALL,
        ).pack(side="left", padx=14)

        self._update_key_save_status()
        return view

    # ── Custom Component Helpers ───────────────────────────────────────────────

    def _render_section_title(self, parent: tk.Frame, title: str) -> None:
        tk.Label(
            parent, text=title,
            bg=parent.cget("bg"), fg=TEXT_MUTED, font=FONT_SECTION, anchor="w",
        ).pack(fill="x", pady=(4, 2))

    def _render_card_header(self, parent: tk.Frame, title: str) -> None:
        tk.Label(
            parent, text=title,
            bg=parent.cget("bg"), fg=ACCENT, font=FONT_SECTION, anchor="w",
        ).pack(fill="x", pady=(8, 2))

    def _render_metric_chip(self, parent: tk.Frame, label: str, value: str) -> tk.Frame:
        chip = tk.Frame(parent, bg=SURFACE_INPUT, highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        tk.Label(
            chip, text=label,
            bg=SURFACE_INPUT, fg=TEXT_MUTED, font=FONT_SECTION,
        ).pack(pady=(3, 0))
        val_label = tk.Label(
            chip, text=value,
            bg=SURFACE_INPUT, fg=TEXT, font=FONT_MONO_BOLD,
        )
        val_label.pack(pady=(0, 4))
        chip._val_label = val_label  # type: ignore[attr-defined]
        return chip

    def _primary_btn(self, parent: Any, text: str, command: Any, accent: str = ACCENT) -> tk.Button:
        btn = tk.Button(
            parent, text=text, command=command,
            bg=accent, fg=ACCENT_TEXT,
            activebackground=ACCENT_HOVER, activeforeground=ACCENT_TEXT,
            relief="flat", font=FONT_BODY_BOLD,
            padx=14, pady=6, bd=0, cursor="hand2",
        )
        return btn

    def _ghost_btn(self, parent: Any, text: str, command: Any, mini: bool = False) -> tk.Button:
        btn = tk.Button(
            parent, text=text, command=command,
            bg=SURFACE_RAISED, fg=TEXT,
            activebackground=BORDER, activeforeground=ACCENT,
            relief="flat", font=FONT_SMALL if mini else FONT_BODY,
            padx=8 if mini else 12, pady=3 if mini else 5, bd=0, cursor="hand2",
        )
        return btn

    def _pill_toggle_btn(self, parent: Any, text: str, command: Any) -> tk.Button:
        return tk.Button(
            parent, text=text, command=command,
            bg=SURFACE_RAISED, fg=TEXT,
            activebackground=BORDER, activeforeground=ACCENT,
            relief="flat", font=FONT_SECTION,
            padx=6, pady=3, bd=0, cursor="hand2",
        )

    def _prompt_pill_btn(self, parent: Any, text: str, command: Any) -> tk.Button:
        return tk.Button(
            parent, text=text, command=command,
            bg=SURFACE, fg=TEXT_MUTED,
            activebackground=SURFACE_RAISED, activeforeground=TEXT,
            relief="flat", font=FONT_SMALL,
            padx=10, pady=4, bd=0, cursor="hand2",
            highlightbackground=BORDER_SUBTLE, highlightthickness=1,
        )

    def _create_scrollable_container(self, parent: tk.Frame, bg: str = BG) -> tuple[tk.Frame, tk.Frame]:
        """Creates a smooth scrollable canvas with proper mousewheel routing."""
        outer = tk.Frame(parent, bg=bg)
        canvas = tk.Canvas(outer, bg=bg, highlightthickness=0, bd=0)
        sb = tk.Scrollbar(
            outer, orient="vertical", command=canvas.yview,
            bg=SURFACE, troughcolor=bg, width=8,
        )
        canvas.configure(yscrollcommand=sb.set)
        inner = tk.Frame(canvas, bg=bg)
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_configure(_e: tk.Event) -> None:
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas_resize(e: tk.Event) -> None:
            canvas.itemconfig(win_id, width=e.width)

        inner.bind("<Configure>", _on_configure)
        canvas.bind("<Configure>", _on_canvas_resize)

        # Localized Wheel Handling (No global bind_all pollution!)
        def _on_mousewheel(event: tk.Event) -> None:
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_wheel_recursive(w: tk.Widget) -> None:
            w.bind("<MouseWheel>", _on_mousewheel, add="+")
            for child in w.winfo_children():
                _bind_wheel_recursive(child)

        canvas.bind("<Enter>", lambda _e: _bind_wheel_recursive(inner))
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        return outer, inner

    def _add_entry_field(self, parent: tk.Frame, key: str, label: str, show: str | None = None, parent_side: str = "top") -> None:
        container = tk.Frame(parent, bg=SURFACE)
        if parent_side == "left":
            container.pack(side="left", fill="x", expand=True, padx=4, pady=(0, 10))
        else:
            container.pack(fill="x", pady=(0, 10))

        tk.Label(container, text=label, bg=SURFACE, fg=TEXT_MUTED, font=FONT_SMALL, anchor="w").pack(anchor="w")

        entry = tk.Entry(
            container, bg=SURFACE_INPUT, fg=TEXT, insertbackground=ACCENT, relief="flat",
            show=show or "", font=FONT_BODY,
            highlightbackground=BORDER, highlightthickness=1, highlightcolor=BORDER_FOCUS,
        )
        entry.insert(0, str(self.settings.get(key) or ""))
        entry.pack(fill="x", pady=(3, 0), ipady=5)
        self.fields[key] = entry

        if key == "api_key":
            entry.bind("<FocusOut>", lambda _e: self._persist_settings())
            entry.bind("<Return>", lambda _e: self._persist_settings())
            entry.bind("<KeyRelease>", self._on_api_key_typed)
            entry.bind("<<Paste>>", lambda _e: self.after_idle(self._persist_settings))
            entry.bind("<Control-v>", lambda _e: self.after_idle(self._persist_settings))

    def _add_combobox_field(self, parent: tk.Frame, key: str, label: str, readonly: bool = False) -> None:
        """Like _add_entry_field but an editable combobox -- values are populated
        later (e.g. by _refresh_models_for_active_key), typing a value by hand
        always works since state stays "normal", not "readonly". Pass
        readonly=True for a picker whose values come only from a fixed list
        (e.g. available agents), where free text would never resolve to anything."""
        container = tk.Frame(parent, bg=SURFACE)
        container.pack(fill="x", pady=(0, 10))

        tk.Label(container, text=label, bg=SURFACE, fg=TEXT_MUTED, font=FONT_SMALL, anchor="w").pack(anchor="w")

        var = tk.StringVar(value=str(self.settings.get(key) or ""))
        combo = ttk.Combobox(container, textvariable=var, values=[], state="readonly" if readonly else "normal", font=FONT_BODY)
        combo.pack(fill="x", pady=(3, 0), ipady=3)
        self.fields[key] = combo
        if key == "model":
            self.model_combo = combo

    def _add_path_field(self, parent: tk.Frame, key: str, label: str, folder: bool) -> None:
        container = tk.Frame(parent, bg=SURFACE)
        container.pack(fill="x", pady=(0, 10))

        tk.Label(container, text=label, bg=SURFACE, fg=TEXT_MUTED, font=FONT_SMALL, anchor="w").pack(anchor="w")

        row = tk.Frame(container, bg=SURFACE)
        row.pack(fill="x", pady=(3, 0))

        entry = tk.Entry(
            row, bg=SURFACE_INPUT, fg=TEXT, insertbackground=ACCENT, relief="flat",
            font=FONT_BODY,
            highlightbackground=BORDER, highlightthickness=1, highlightcolor=BORDER_FOCUS,
        )
        entry.insert(0, str(self.settings.get(key) or ""))
        entry.pack(side="left", fill="x", expand=True, ipady=5)
        self.fields[key] = entry

        def browse() -> None:
            if folder:
                picked = filedialog.askdirectory(initialdir=entry.get() or str(ROOT))
            else:
                picked = filedialog.askopenfilename(
                    initialdir=str(Path(entry.get()).parent if entry.get() else ROOT)
                )
            if picked:
                entry.delete(0, "end")
                entry.insert(0, picked)
                self._persist_settings()

        self._ghost_btn(row, "Browse", browse, mini=True).pack(side="left", padx=(6, 0))

    def _add_tts_profile_row(self, profile: dict[str, Any]) -> None:
        flat = {
            "name": str(profile.get("name") or ""),
            "provider": str(profile.get("provider") or "xai"),
            "api_key": str(profile.get("api_key") or ""),
            "voice_id": str(profile.get("voice_id") or ""),
            "model": str(profile.get("model") or ""),
            "speed": str((profile.get("settings") or {}).get("speed") or ""),
            "language": str((profile.get("settings") or {}).get("language") or ""),
        }

        row_card = tk.Frame(self._tts_profiles_list, bg=SURFACE_INPUT, highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        row_card.pack(fill="x", pady=4)

        # Collapsible: a saved (already-named) profile starts collapsed to keep
        # the list scannable; a freshly-added blank one starts expanded so it
        # can be filled in immediately. The header row (toggle + name summary +
        # Remove) stays visible either way.
        header = tk.Frame(row_card, bg=SURFACE_INPUT)
        header.pack(fill="x", padx=10, pady=(6, 0))
        expanded_var = tk.BooleanVar(value=not bool(flat["name"]))
        toggle_lbl = tk.Label(
            header, text=("▾" if expanded_var.get() else "▸"),
            bg=SURFACE_INPUT, fg=TEXT_MUTED, font=FONT_SECTION, cursor="hand2", width=2,
        )
        toggle_lbl.pack(side="left")
        summary_var = tk.StringVar(value=flat["name"] or "(unnamed profile)")
        summary_lbl = tk.Label(
            header, textvariable=summary_var, bg=SURFACE_INPUT, fg=TEXT, font=FONT_BODY_BOLD,
            cursor="hand2", anchor="w",
        )
        summary_lbl.pack(side="left", fill="x", expand=True, padx=(4, 0))

        grid = tk.Frame(row_card, bg=SURFACE_INPUT)
        if expanded_var.get():
            grid.pack(fill="x", padx=10, pady=8)

        def toggle_row(_e: Any = None) -> None:
            if expanded_var.get():
                grid.pack_forget()
                expanded_var.set(False)
                toggle_lbl.configure(text="▸")
            else:
                grid.pack(fill="x", padx=10, pady=8)
                expanded_var.set(True)
                toggle_lbl.configure(text="▾")

        toggle_lbl.bind("<Button-1>", toggle_row)
        summary_lbl.bind("<Button-1>", toggle_row)

        self._ghost_btn(header, "✕ Remove", lambda: self._remove_tts_profile_row(entry_ref), mini=True).pack(side="right")

        def mini(col: int, key: str, label: str, width: int, values: list[str] | None = None, show: str | None = None) -> tk.StringVar:
            cell = tk.Frame(grid, bg=SURFACE_INPUT)
            cell.grid(row=0, column=col, padx=(0, 8), sticky="w")
            tk.Label(cell, text=label, bg=SURFACE_INPUT, fg=TEXT_MUTED, font=FONT_SECTION, anchor="w").pack(anchor="w")
            var = tk.StringVar(value=flat[key])
            if values is not None:
                widget: tk.Widget = ttk.Combobox(
                    cell, textvariable=var, values=values, state="readonly", width=width, font=FONT_BODY,
                )
            else:
                widget = tk.Entry(
                    cell, textvariable=var, bg=SURFACE, fg=TEXT, insertbackground=ACCENT,
                    relief="flat", font=FONT_BODY, width=width, show=show or "",
                    highlightbackground=BORDER, highlightthickness=1,
                )
            widget.pack(pady=(2, 0), ipady=3)
            return var

        # API key gets its own cell so a "Detect" button can sit under it — auto-fills the
        # provider dropdown from a live probe, but never locks it (still a free selection).
        key_cell = tk.Frame(grid, bg=SURFACE_INPUT)
        key_cell.grid(row=0, column=2, padx=(0, 8), sticky="w")
        tk.Label(key_cell, text="API key", bg=SURFACE_INPUT, fg=TEXT_MUTED, font=FONT_SECTION, anchor="w").pack(anchor="w")
        api_key_var = tk.StringVar(value=flat["api_key"])
        tk.Entry(
            key_cell, textvariable=api_key_var, bg=SURFACE, fg=TEXT, insertbackground=ACCENT,
            relief="flat", font=FONT_BODY, width=20, show="*",
            highlightbackground=BORDER, highlightthickness=1,
        ).pack(pady=(2, 0), ipady=3)

        # Pick from the shared Saved API Keys vault (Section 1) instead of
        # re-pasting a key already saved there. Purely a fill-in convenience --
        # this profile still stores its own api_key copy, same schema as before.
        saved_key_var = tk.StringVar()
        saved_key_combo = ttk.Combobox(
            key_cell, textvariable=saved_key_var,
            values=[str(e.get("label") or "") for e in (self.settings.get("api_keys") or [])],
            state="readonly", width=20, font=FONT_SMALL,
        )
        saved_key_combo.set("or use saved key…")
        saved_key_combo.pack(pady=(2, 0))

        def on_saved_key_picked(_e: Any = None) -> None:
            picked = saved_key_var.get()
            for saved in (self.settings.get("api_keys") or []):
                if str(saved.get("label") or "") == picked:
                    api_key_var.set(str(saved.get("api_key") or ""))
                    saved_provider = str(saved.get("provider") or "")
                    if saved_provider in ("xai", "openai", "cartesia"):
                        row_vars["provider"].set(saved_provider)
                    self._persist_settings()
                    break

        saved_key_combo.bind("<<ComboboxSelected>>", on_saved_key_picked)

        # Voice ID stays free-text-enterable (a console-cloned ID must be pasteable before
        # any refresh) but doubles as a combobox once list_voices populates it.
        voice_cell = tk.Frame(grid, bg=SURFACE_INPUT)
        voice_cell.grid(row=0, column=3, padx=(0, 8), sticky="w")
        tk.Label(voice_cell, text="Voice ID", bg=SURFACE_INPUT, fg=TEXT_MUTED, font=FONT_SECTION, anchor="w").pack(anchor="w")
        voice_var = tk.StringVar(value=flat["voice_id"])
        voice_combo = ttk.Combobox(voice_cell, textvariable=voice_var, values=[], state="normal", width=10, font=FONT_BODY)
        voice_combo.pack(pady=(2, 0), ipady=3)

        row_vars: dict[str, tk.Variable] = {
            "name": mini(0, "name", "Profile name", 12),
            "provider": mini(1, "provider", "Provider", 10, values=["xai", "openai", "cartesia"]),
            "api_key": api_key_var,
            "voice_id": voice_var,
            "model": mini(4, "model", "Model", 12),
            "speed": mini(5, "speed", "Speed", 6),
            "language": mini(6, "language", "Language", 10),
        }

        entry_ref: dict[str, Any] = {
            "frame": row_card, "vars": row_vars, "voice_combo": voice_combo, "saved_key_combo": saved_key_combo,
        }

        # Pin: only one profile at a time, enforced by unchecking every other row's
        # BooleanVar on click rather than a Tk Radiobutton group, since a Radiobutton
        # can't be clicked again to turn itself off and this needs an "unpin" path too.
        # `command=` (not trace_add) fires only on the user's own click, never on the
        # programmatic .set(False) this does to the other rows -- no update cascade.
        pin_var = tk.BooleanVar(value=bool(flat["name"]) and str(self.settings.get("active_tts_profile") or "") == flat["name"])
        entry_ref["pin_var"] = pin_var

        def on_pin_click() -> None:
            if pin_var.get():
                for other in self._tts_profile_rows:
                    if other is not entry_ref:
                        other["pin_var"].set(False)
            self._persist_settings()

        pin_chk = tk.Checkbutton(
            header, text="Pin as only voice", variable=pin_var, command=on_pin_click,
            bg=SURFACE_INPUT, activebackground=SURFACE_INPUT, selectcolor=SURFACE,
            fg=TEXT_MUTED, highlightthickness=0, bd=0, font=FONT_SMALL, cursor="hand2",
        )
        pin_chk.pack(side="right", padx=(0, 8))

        def on_name_changed(*_args: Any) -> None:
            summary_var.set(row_vars["name"].get().strip() or "(unnamed profile)")

        row_vars["name"].trace_add("write", on_name_changed)

        def on_voice_selected(_event: Any = None) -> None:
            # The dropdown shows a decorated label ("★ Miranda (beubktirxxn9)") for custom
            # voices, but the field must hold the raw voice_id — translate the selection
            # back via the lookup built in _refresh_voices_for_row before it lands in var.
            label = voice_var.get()
            lookup = entry_ref.get("voice_lookup") or {}
            if label in lookup:
                voice_var.set(lookup[label])

        voice_combo.bind("<<ComboboxSelected>>", on_voice_selected)

        # Small action buttons row, under the key/voice cells — Detect and Refresh both hit
        # the network on a worker thread (never block Tk), reusing the after(0) hop pattern
        # from _place_generated_file.
        actions_cell = tk.Frame(grid, bg=SURFACE_INPUT)
        actions_cell.grid(row=1, column=2, columnspan=2, sticky="w", pady=(4, 0))
        self._ghost_btn(
            actions_cell, "Detect provider", lambda: self._detect_provider_for_row(entry_ref), mini=True,
        ).pack(side="left", padx=(0, 6))
        self._ghost_btn(
            actions_cell, "↻ Refresh voices", lambda: self._refresh_voices_for_row(entry_ref), mini=True,
        ).pack(side="left")

        self._tts_profile_rows.append(entry_ref)

    def _detect_provider_for_row(self, entry_ref: dict[str, Any]) -> None:
        """Detect provider from the row's API key on a worker thread, then auto-fill it."""
        row_vars = entry_ref["vars"]
        api_key = row_vars["api_key"].get().strip()
        if not api_key:
            self.log("Detect provider: no API key entered.")
            return
        self.log("Detecting provider…")

        def worker() -> None:
            provider, message = tts_vocal.detect_provider(api_key)

            def apply() -> None:
                if entry_ref not in self._tts_profile_rows:
                    return  # row was removed while the probe was in flight
                self.log(message)
                if provider:
                    row_vars["provider"].set(provider)
                    self._refresh_voices_for_row(entry_ref)

            self.after(0, apply)

        threading.Thread(target=worker, daemon=True).start()

    def _refresh_voices_for_row(self, entry_ref: dict[str, Any]) -> None:
        """Repopulate a row's voice combobox from list_voices, without disturbing the typed value."""
        row_vars = entry_ref["vars"]
        provider = row_vars["provider"].get().strip()
        api_key = row_vars["api_key"].get().strip()
        if not provider or not api_key:
            self.log("Refresh voices: need a provider and API key first.")
            return
        if provider not in ("xai", "openai", "cartesia"):
            self.log("Refresh voices: no voice list available for provider \"%s\"." % provider)
            return
        self.log("Fetching voices for %s…" % provider)

        def worker() -> None:
            voices = tts_vocal.list_voices(provider, api_key)

            def apply() -> None:
                combo = entry_ref.get("voice_combo")
                if combo is None or not combo.winfo_exists():
                    return  # row was removed while the fetch was in flight
                labels = [
                    ("★ " + v["name"] + " (" + v["voice_id"] + ")") if v.get("custom") else v["name"]
                    for v in voices
                ]
                combo["values"] = labels
                combo_lookup = {label: v["voice_id"] for label, v in zip(labels, voices)}
                entry_ref["voice_lookup"] = combo_lookup
                custom_count = sum(1 for v in voices if v.get("custom"))
                self.log("Found %d voice(s) for %s (%d custom)." % (len(voices), provider, custom_count))

            self.after(0, apply)

        threading.Thread(target=worker, daemon=True).start()

    def _remove_tts_profile_row(self, entry_ref: dict[str, Any]) -> None:
        entry_ref["frame"].destroy()
        self._tts_profile_rows.remove(entry_ref)
        self._persist_settings()

    def _collect_tts_profiles(self) -> list[dict[str, Any]]:
        profiles: list[dict[str, Any]] = []
        for entry in getattr(self, "_tts_profile_rows", []):
            row_vars = entry["vars"]
            try:
                name = row_vars["name"].get().strip()
            except tk.TclError:
                continue
            if not name:
                continue
            profile: dict[str, Any] = {
                "name": name,
                "provider": row_vars["provider"].get().strip() or "xai",
                "api_key": row_vars["api_key"].get().strip(),
                "voice_id": row_vars["voice_id"].get().strip(),
                "model": row_vars["model"].get().strip(),
                "settings": {},
            }
            speed = row_vars["speed"].get().strip()
            if speed:
                try:
                    profile["settings"]["speed"] = float(speed)
                except ValueError:
                    pass
            language = row_vars["language"].get().strip()
            if language:
                profile["settings"]["language"] = language
            profiles.append(profile)
        return profiles

    def _collect_active_tts_profile(self) -> str:
        """The name of whichever row's "Pin as only voice" box is checked, or "" for
        none -- empty/unnamed rows are treated the same as _collect_tts_profiles does
        (a pin on a blank row pins nothing, same as a blank row saves no profile)."""
        for entry in getattr(self, "_tts_profile_rows", []):
            pin_var = entry.get("pin_var")
            if pin_var is None:
                continue
            try:
                if not pin_var.get():
                    continue
                name = entry["vars"]["name"].get().strip()
            except tk.TclError:
                continue
            if name:
                return name
        return ""

    # ── Page Switching ─────────────────────────────────────────────────────────

    def _show_page(self, name: str) -> None:
        leaving = self._current_page
        if leaving == "settings" and name != "settings":
            self._persist_settings()

        if name in ("actions", "genius", "settings"):
            self._open_tool = None
            self._close_webview()
            self._restore_window()

        for key, frame in self.pages.items():
            frame.pack_forget()

        self.pages[name].pack(fill="both", expand=True)

        if name == "genius":
            self.target_tracks_frame.pack_forget()
            self.session_tracks_frame.pack(fill="both", expand=True)
        else:
            self.session_tracks_frame.pack_forget()
            self.target_tracks_frame.pack(fill="both", expand=True)

        nav_name = "actions" if name == "tool" else name
        for key, btn in self.nav_buttons.items():
            if key == nav_name:
                btn.configure(bg=ACCENT, fg=ACCENT_TEXT)
            else:
                btn.configure(bg=BG_SIDEBAR, fg=TEXT_MUTED)

        self._current_page = name

    # ── Tools Catalog Grid Rendering ───────────────────────────────────────────

    def _refresh_tools(self) -> None:
        folder = settings_store.tools_dir(self.settings)
        tools = load_tools(folder)

        for child in self.tools_catalog_frame.winfo_children():
            child.destroy()

        if not tools:
            self.tools_count_label.configure(text="0 tools found")
            empty = tk.Frame(self.tools_catalog_frame, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
            empty.pack(fill="x", pady=12, padx=4)
            tk.Label(
                empty, text="No Tools Found",
                bg=SURFACE, fg=TEXT, font=FONT_HEADING, anchor="w",
            ).pack(anchor="w", padx=16, pady=(14, 4))
            tk.Label(
                empty, text="Add tool folders with manifest under: " + str(folder),
                bg=SURFACE, fg=TEXT_MUTED, font=FONT_SMALL, anchor="w",
            ).pack(anchor="w", padx=16, pady=(0, 14))
            return

        self.tools_count_label.configure(text="%d studio actions available" % len(tools))

        # Render Tool Cards
        for tool in tools:
            self._render_tool_card(self.tools_catalog_frame, tool)

    def _render_tool_card(self, parent: tk.Frame, tool: dict[str, Any]) -> None:
        accent = str(tool.get("accent") or ACCENT)
        is_webview = str(tool.get("ui") or "") == "webview"
        scope = str(tool.get("scope") or "track")

        card = tk.Frame(parent, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="x", pady=6, padx=2)

        # Left Accent Indicator Bar
        tk.Frame(card, bg=accent, width=4).pack(side="left", fill="y")

        card_content = tk.Frame(card, bg=SURFACE)
        card_content.pack(side="left", fill="both", expand=True, padx=14, pady=12)

        # Header Row (Title + Scope Badge)
        top_row = tk.Frame(card_content, bg=SURFACE)
        top_row.pack(fill="x")

        tk.Label(
            top_row, text=str(tool.get("name") or tool["id"]),
            bg=SURFACE, fg=TEXT, font=FONT_HEADING, anchor="w",
        ).pack(side="left")

        scope_tag = "Set-Wide" if scope == "set" else ("Web Dialog" if is_webview else "Selected Tracks")
        scope_color = ACCENT_VIOLET if scope == "set" else (ACCENT_AMBER if is_webview else ACCENT)

        tk.Label(
            top_row, text="  " + scope_tag + "  ",
            bg=SURFACE_INPUT, fg=scope_color, font=FONT_SECTION,
        ).pack(side="right")

        # Description
        tk.Label(
            card_content,
            text=str(tool.get("description") or "Opens its own interactive action screen."),
            bg=SURFACE, fg=TEXT_MUTED, font=FONT_SMALL, anchor="w",
            wraplength=540, justify="left",
        ).pack(fill="x", pady=(4, 10))

        # Launch Button
        btn_row = tk.Frame(card_content, bg=SURFACE)
        btn_row.pack(fill="x")

        btn_label = "Open Interactive Dialog ↗" if is_webview else "Open & Configure ▶"
        self._primary_btn(
            btn_row, btn_label, lambda t=tool: self._open_tool_screen(t), accent=accent
        ).pack(side="left")

    # ── Tool Screen & Execution ────────────────────────────────────────────────

    def _open_tool_screen(self, tool: dict[str, Any]) -> None:
        self._close_webview()
        self._open_tool = tool

        for child in self.tool_body.winfo_children():
            child.destroy()

        accent = str(tool.get("accent") or ACCENT)
        is_webview = str(tool.get("ui") or "") == "webview"
        set_scope = str(tool.get("scope") or "") == "set"
        self._show_run_result(None)

        # Tool Header Card
        header_card = tk.Frame(self.tool_body, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
        header_card.pack(fill="x", pady=(0, 10))

        tk.Frame(header_card, bg=accent, width=4).pack(side="left", fill="y")
        h_inner = tk.Frame(header_card, bg=SURFACE)
        h_inner.pack(fill="both", expand=True, padx=14, pady=12)

        tk.Label(
            h_inner, text=str(tool.get("name") or tool["id"]),
            bg=SURFACE, fg=TEXT, font=FONT_TITLE, anchor="w",
        ).pack(fill="x")

        tk.Label(
            h_inner, text=str(tool.get("description") or ""),
            bg=SURFACE, fg=TEXT_MUTED, font=FONT_SMALL, anchor="w",
            wraplength=600, justify="left",
        ).pack(fill="x", pady=(4, 0))

        # Target Summary Chip
        if not set_scope:
            target_banner = tk.Frame(self.tool_body, bg=SURFACE_INPUT, highlightbackground=BORDER, highlightthickness=1)
            target_banner.pack(fill="x", pady=(0, 10))
            self.tool_target_summary = tk.Label(
                target_banner, text="Applying to: " + self._selection_summary(),
                bg=SURFACE_INPUT, fg=ACCENT, font=FONT_SMALL_BOLD, anchor="w",
                padx=12, pady=6,
            )
            self.tool_target_summary.pack(fill="x")

        if is_webview:
            self._open_webview_tool(tool)
            return

        # Update run footer accent and label
        run_label = str(tool.get("runLabel") or ("▶  Run on Set" if set_scope else "▶  Run Now"))
        self.run_btn.configure(text=run_label, bg=accent,
                               activebackground=accent)
        self.run_status_label.configure(text="Fill in the fields below, then click Run Now.", fg=TEXT_MUTED)

        # Fields Scroll Container
        fields_scroll_box, f_inner = self._create_scrollable_container(self.tool_body, bg=BG)
        fields_scroll_box.pack(fill="both", expand=True)

        self._tool_field_vars = {}
        self._tool_field_rows = []
        self._tool_form_gen += 1
        gen = self._tool_form_gen
        fields = tool.get("fields") or []
        stored_prefs = (self.settings.get("tool_prefs") or {}).get(str(tool.get("id") or ""), {})

        if not fields:
            no_fields_card = tk.Frame(f_inner, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
            no_fields_card.pack(fill="x", pady=(0, 10))
            tk.Label(
                no_fields_card,
                text="No extra parameters needed.",
                bg=SURFACE, fg=TEXT, font=FONT_BODY_BOLD, anchor="w",
            ).pack(anchor="w", padx=14, pady=(12, 4))
            tk.Label(
                no_fields_card,
                text="Just make sure your target tracks are ticked on the left, then click  ▶ Run Now.",
                bg=SURFACE, fg=TEXT_MUTED, font=FONT_SMALL, anchor="w",
            ).pack(anchor="w", padx=14, pady=(0, 12))
        else:
            fields_card = tk.Frame(f_inner, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
            fields_card.pack(fill="x", pady=(0, 10))

            fields_inner = tk.Frame(fields_card, bg=SURFACE)
            fields_inner.pack(fill="x", padx=16, pady=14)

            for field in fields:
                if not isinstance(field, dict) or not field.get("id"):
                    continue

                # Row container for this one field (label + hint + widget). Not packed here —
                # _apply_field_visibility() packs only the rows whose showIf currently matches,
                # in declaration order, so a field can be hidden/shown without losing its value,
                # focus, or scroll position.
                row = tk.Frame(fields_inner, bg=SURFACE)
                self._tool_field_rows.append({"id": str(field["id"]), "row": row, "showIf": field.get("showIf")})

                lbl_row = tk.Frame(row, bg=SURFACE)
                lbl_row.pack(fill="x")

                tk.Label(
                    lbl_row, text=str(field.get("label") or field["id"]),
                    bg=SURFACE, fg=TEXT, font=FONT_BODY_BOLD, anchor="w",
                ).pack(side="left")

                field_type = str(field.get("type") or "text")
                options: list[str] = []
                if field_type == "select":
                    options_source = str(field.get("optionsSource") or "")
                    if options_source == "tts_profiles":
                        options = [
                            str(p.get("name") or "")
                            for p in (self.settings.get("tts_profiles") or [])
                            if p.get("name")
                        ]
                    else:
                        options = [str(o) for o in (field.get("options") or [])]
                    if not options:
                        field_type = "text"  # nothing to pick from — fall back to a plain entry

                default_val = field.get("default")
                if str(field["id"]) in stored_prefs:
                    default_val = stored_prefs[str(field["id"])]
                if field_type == "select" and not (default_val and str(default_val) in options):
                    default_val = options[0] if options else ""

                # Show default value as a muted badge (the widget itself shows it for selects)
                if field_type not in ("select", "textarea", "file") and default_val is not None and str(default_val).strip():
                    tk.Label(
                        lbl_row, text="default: %s" % default_val,
                        bg=SURFACE_INPUT, fg=TEXT_DIM, font=FONT_SECTION,
                        padx=6, pady=1,
                    ).pack(side="right")

                # Hint text if present
                hint = str(field.get("hint") or "")
                if hint:
                    tk.Label(
                        row, text=hint,
                        bg=SURFACE, fg=TEXT_MUTED, font=FONT_SMALL,
                        anchor="w", justify="left",
                    ).pack(fill="x", pady=(1, 0))

                var = tk.StringVar(value=str(default_val if default_val is not None else ""))
                self._tool_field_vars[str(field["id"])] = var

                if field_type == "select":
                    combo = ttk.Combobox(
                        row, textvariable=var, values=options, state="readonly",
                        font=FONT_BODY,
                    )
                    combo.pack(fill="x", pady=(3, 0), ipady=3)
                elif field_type == "textarea":
                    text_box = tk.Text(
                        row, height=6, bg=SURFACE_INPUT, fg=TEXT, insertbackground=ACCENT,
                        relief="flat", font=FONT_BODY, wrap="word",
                        highlightbackground=BORDER, highlightthickness=1, highlightcolor=BORDER_FOCUS,
                    )
                    text_box.pack(fill="x", pady=(3, 0))
                    if default_val:
                        text_box.insert("1.0", str(default_val))

                    def _sync_textarea(_e: tk.Event | None = None, w: tk.Text = text_box, v: tk.StringVar = var) -> None:
                        v.set(w.get("1.0", "end-1c"))

                    text_box.bind("<KeyRelease>", _sync_textarea)
                    text_box.bind("<FocusOut>", _sync_textarea)
                elif field_type == "file":
                    file_row = tk.Frame(row, bg=SURFACE)
                    file_row.pack(fill="x", pady=(3, 0))
                    entry = tk.Entry(
                        file_row, textvariable=var,
                        bg=SURFACE_INPUT, fg=TEXT, insertbackground=ACCENT, relief="flat",
                        font=FONT_BODY,
                        highlightbackground=BORDER, highlightthickness=1, highlightcolor=BORDER_FOCUS,
                    )
                    entry.pack(side="left", fill="x", expand=True, ipady=6)
                    entry.bind("<Return>", lambda _e: self._run_open_tool())

                    filetypes_raw = field.get("filetypes") or [["All files", "*.*"]]
                    filetypes = [tuple(t) for t in filetypes_raw]  # JSON gives lists; Tk needs tuples

                    def _browse(v: tk.StringVar = var, ft: list[tuple[str, str]] = filetypes) -> None:
                        current = v.get().strip()
                        if current:
                            start_dir = str(Path(current).parent)
                        else:
                            start_dir = str(settings_store.samples_dir(self.settings))
                        picked = filedialog.askopenfilename(title="Choose a file", initialdir=start_dir, filetypes=ft)
                        if picked:
                            v.set(picked)

                    self._ghost_btn(file_row, "Browse…", _browse, mini=True).pack(side="left", padx=(6, 0))
                else:
                    entry = tk.Entry(
                        row, textvariable=var,
                        bg=SURFACE_INPUT, fg=TEXT, insertbackground=ACCENT, relief="flat",
                        font=FONT_BODY,
                        highlightbackground=BORDER, highlightthickness=1, highlightcolor=BORDER_FOCUS,
                    )
                    entry.pack(fill="x", pady=(3, 0), ipady=6)
                    # Bind Enter key to run
                    entry.bind("<Return>", lambda _e: self._run_open_tool())

            # Trace only the field(s) that actually control a showIf — not every field var —
            # so typing in an ordinary text box never re-runs the visibility pass. The `gen`
            # guard means a trace left over from a previously-opened tool screen (its Vars are
            # kept alive by the trace itself) can't fire against this screen's rows.
            controller_ids = {
                str((row_spec["showIf"] or {}).get("field") or "")
                for row_spec in self._tool_field_rows
                if isinstance(row_spec["showIf"], dict) and row_spec["showIf"].get("field")
            }
            for controller_id in controller_ids:
                controller_var = self._tool_field_vars.get(controller_id)
                if controller_var is not None:
                    controller_var.trace_add("write", lambda *_a, g=gen: self._on_tool_field_changed(g))
            self._apply_field_visibility()

        self._show_page("tool")

    def _matches_show_if(self, cond: Any) -> bool:
        if not isinstance(cond, dict):
            return True
        field_id = str(cond.get("field") or "")
        var = self._tool_field_vars.get(field_id)
        if var is None:
            self.log('Tool field showIf references unknown field "%s".' % field_id)
            return False
        value = var.get().strip()
        allowed = cond.get("in")
        if isinstance(allowed, list) and value not in [str(a) for a in allowed]:
            return False
        denied = cond.get("notIn")
        if isinstance(denied, list) and value in [str(d) for d in denied]:
            return False
        return True

    def _apply_field_visibility(self) -> None:
        for row_spec in self._tool_field_rows:
            row_spec["row"].pack_forget()
        shown = 0
        for row_spec in self._tool_field_rows:
            if self._matches_show_if(row_spec["showIf"]):
                row_spec["row"].pack(fill="x", pady=(8 if shown else 0, 0))
                shown += 1

    def _on_tool_field_changed(self, gen: int) -> None:
        if gen != self._tool_form_gen:  # a trace surviving from a previous tool screen
            return
        self._apply_field_visibility()

    # ── WebView Dialog (Breakdowns, BBenCut, ...) ───────────────────────────────
    # Each webview tool is addressed by tool.json's "id"; _webview_context() and
    # _on_webview_message() dispatch to that tool's own context-builder and
    # run-handler. Adding a tool here means adding one branch in each, not a
    # new copy of _open_webview_tool/_webview_tool_html/WebViewPane wiring.

    def _open_webview_tool(self, tool: dict[str, Any]) -> None:
        if str(tool.get("id") or "") == "arrangement-helper":
            self._open_arrangement_helper(tool)
            return
        self._open_webview_tool_now(tool)

    def _open_arrangement_helper(self, tool: dict[str, Any]) -> None:
        # Step 3b of the arrangement-helper plan (§3b): arrangement_scan needs
        # a live round-trip, so this tool can't reuse the generic synchronous
        # open path -- it scans on a worker thread first, then opens the
        # dialog from self.after(0, …) once a real isEditing/sections/
        # scanCount/nextId seed is in hand (or a create-mode fallback, if
        # there's no MIDI track to scan or the scan itself fails).
        self._close_webview()
        if not self._connected:
            messagebox.showwarning(
                "Live Actions — Not Connected",
                "The Live Actions Bridge is not connected.\n\n"
                "Make sure Ableton Live is running and that 'Live Actions Bridge.amxd' "
                "is dropped onto an audio track.",
            )
            self._show_page("actions")
            return

        base_ctx = self._arrangement_helper_context()
        candidate_path = self._arrangement_helper_default_track(base_ctx)

        host = tk.Frame(self.tool_body, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
        host.pack(fill="both", expand=True)
        self._webview_host = host
        self._show_page("tool")
        self._grow_window()
        self.update_idletasks()
        tk.Label(
            host, text="Scanning the Set for an existing arrangement…",
            bg=SURFACE, fg=TEXT_MUTED, font=FONT_BODY,
        ).pack(anchor="w", padx=16, pady=16)

        def worker() -> None:
            scan: dict[str, Any] = {}
            if candidate_path:
                result = self.bridge.call_live("arrangement_scan", {"trackPath": candidate_path})
                if result.get("ok"):
                    scan = result
                else:
                    reason = str(result.get("message") or result.get("error") or "scan failed")
                    self.after(0, lambda r=reason: self.log(
                        "Arrangement Helper: scan failed (%s) -- opening in create mode." % r))
            self.after(0, lambda: self._finish_arrangement_helper_open(tool, candidate_path, scan, host))

        threading.Thread(target=worker, daemon=True).start()

    def _finish_arrangement_helper_open(
        self, tool: dict[str, Any], candidate_path: str, scan: dict[str, Any], placeholder_host: tk.Frame,
    ) -> None:
        if str((self._open_tool or {}).get("id") or "") != "arrangement-helper":
            return  # user navigated away while the scan was in flight
        # _open_webview_tool_now's own _close_webview() only clears the
        # WebViewPane reference, not this placeholder frame -- destroy it
        # explicitly or it'd be left stacked behind the real dialog.
        try:
            if placeholder_host.winfo_exists():
                placeholder_host.destroy()
        except tk.TclError:
            pass
        self._webview_host = None
        # Consumed once by the next _arrangement_helper_context() call, which
        # _open_webview_tool_now triggers via _webview_context -- see that
        # method for how isEditing/sections/scanCount/nextId get seeded from it.
        self._arrangement_scan_result = {"trackPath": candidate_path, "scan": scan}
        self._open_webview_tool_now(tool)

    def _arrangement_helper_default_track(self, ctx: dict[str, Any]) -> str:
        # Mirrors dialog.html's own defaultSectionTrackPath() exactly (plan
        # §2b.3) so the pre-open scan targets the same track the dialog would
        # show selected by default: last persisted (if still a valid MIDI
        # track) -> a track literally named "Arrangement" -> the first ticked
        # MIDI track -> the first MIDI track. Keep both in sync if either
        # changes.
        midi_tracks = [t for t in (ctx.get("tracks") or []) if t.get("kind") == "midi"]
        if not midi_tracks:
            return ""
        last = str(ctx.get("lastSectionTrackPath") or "")
        if last and any(t.get("path") == last for t in midi_tracks):
            return last
        for t in midi_tracks:
            if str(t.get("name") or "").strip().lower() == "arrangement":
                return str(t["path"])
        for t in midi_tracks:
            if t.get("ticked"):
                return str(t["path"])
        return str(midi_tracks[0]["path"])

    def _open_webview_tool_now(self, tool: dict[str, Any]) -> None:
        self._close_webview()
        ok, err = webview_pane.webview_available()
        tool_name = str(tool.get("name") or tool.get("id") or "Tool")
        self._webview_tool_id = str(tool.get("id") or "")

        host = tk.Frame(self.tool_body, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
        host.pack(fill="both", expand=True)
        self._webview_host = host

        self._show_page("tool")
        self._grow_window()
        self.update_idletasks()

        if not ok:
            tk.Label(
                host, text="Edge WebView2 is required on this PC.\n" + (err or ""),
                bg=SURFACE, fg=ERR, font=FONT_BODY, anchor="w",
            ).pack(anchor="w", padx=16, pady=16)
            return

        html = self._webview_tool_html(tool)
        if not html:
            tk.Label(
                host, text=f"Could not load the {tool_name} dialog HTML file.",
                bg=SURFACE, fg=ERR, font=FONT_BODY,
            ).pack(anchor="w", padx=16, pady=16)
            return

        status_text = str(tool.get("dialogStatus") or f"{tool_name} is open in its own dialog window.")
        self._dialog_status = tk.Label(
            host, text=status_text,
            bg=SURFACE, fg=TEXT_MUTED, font=FONT_BODY, justify="left",
        )
        self._dialog_status.pack(anchor="w", padx=16, pady=16)

        cache = Path(os.environ.get("APPDATA", str(Path.home()))) / "Live Actions" / "webview2"
        try:
            self._webview = webview_pane.WebViewPane(
                host, self._on_webview_message, cache, html,
                title=tool_name, tool_id=self._webview_tool_id or "webview",
            )
            self.log(f"{tool_name} dialog opened.")
        except Exception as exc:
            tk.Label(
                host, text=f"Could not open the {tool_name} dialog:\n" + str(exc),
                bg=SURFACE, fg=ERR, font=FONT_BODY,
            ).pack(anchor="w", padx=16, pady=16)
            self.log(f"{tool_name} webview error: " + str(exc))

    def _webview_tool_html(self, tool: dict[str, Any]) -> str:
        folder = Path(str(tool.get("_path") or ""))
        rel = str(tool.get("dialog") or "ui/dialog.html")
        path = folder / rel
        if not path.is_file():
            return ""
        html = path.read_text(encoding="utf-8")
        ctx = self._webview_context(tool)
        return html.replace("__CTX_JSON__", json.dumps(ctx))

    def _webview_context(self, tool: dict[str, Any]) -> dict[str, Any]:
        tool_id = str(tool.get("id") or "")
        if tool_id == "breakdowns":
            return self._breakdowns_context()
        if tool_id == "bbencut":
            return self._bbencut_context()
        if tool_id == "arrangement-helper":
            return self._arrangement_helper_context()
        return {}

    def _arrangement_helper_context(self) -> dict[str, Any]:
        # Step 3b of the arrangement-helper plan: isEditing/sections/
        # scanCount/nextId are seeded from a real arrangement_scan reply when
        # one is cached (see _open_arrangement_helper) -- otherwise this
        # falls back to the same honest create-mode defaults Steps 2-4
        # shipped with (no MIDI track to scan, or the scan itself failed).
        # The cache is consumed here so a later call without a fresh scan
        # (e.g. from _run_arrangement_helper, which only wants beatsPerBar)
        # can't accidentally reuse stale edit-mode data.
        cache = self._arrangement_scan_result
        self._arrangement_scan_result = None
        scan = (cache or {}).get("scan") or {}
        scan_ok = bool(scan.get("ok"))
        sig = str(self._last_status.get("time_signature") or "4/4")
        beats = 4
        if "/" in sig:
            try:
                beats = max(1, int(sig.split("/", 1)[0]))
            except ValueError:
                beats = 4
        tempo = self._last_status.get("tempo")
        try:
            tempo_n = float(tempo) if tempo not in (None, "") else None
        except (TypeError, ValueError):
            tempo_n = None
        tracks = []
        for t in self._tracks:
            var = self._track_vars.get(t.get("key"))
            tracks.append({
                "path": str(t.get("path") or ""),
                "name": str(t.get("name") or t.get("key") or "track"),
                "kind": str(t.get("kind") or "audio").lower(),
                "ticked": bool(var is not None and var.get()),
            })
        stored = (self.settings.get("tool_prefs") or {}).get("arrangement-helper", {})
        last_path = str((cache or {}).get("trackPath") or "") or str(stored.get("sectionTrackPath") or "")
        ctx: dict[str, Any] = {
            "isEditing": bool(scan_ok and scan.get("isEditing")),
            "sections": (scan.get("sections") or []) if scan_ok else [],
            "nextId": int(scan.get("nextId") or 0) if scan_ok else 0,
            "scanCount": int(scan.get("scanCount") or 0) if scan_ok else 0,
            "beatsPerBar": beats,
            "tempo": tempo_n,
            "tracks": tracks,
            "lastSectionTrackPath": last_path,
        }
        if scan_ok and scan.get("startBar") is not None:
            ctx["startBar"] = scan.get("startBar")
        if scan_ok and scan.get("truncated"):
            ctx["truncated"] = True
        return ctx

    def _bbencut_context(self) -> dict[str, Any]:
        # No Arrangement-clip read support yet (Step 4 of the BBenCut plan)
        # -- honest static defaults, not a fake "selected clip" read.
        tempo = self._last_status.get("tempo")
        try:
            tempo_n = float(tempo) if tempo not in (None, "") else None
        except (TypeError, ValueError):
            tempo_n = None
        return {
            "hasClip": False,
            "totalLengthBeats": 16.0,
            "loopLengthBeats": 4.0,
            "tempo": tempo_n,
        }

    def _breakdowns_context(self) -> dict[str, Any]:
        picked = self.selected_tracks()
        names = [str(t.get("name") or t.get("key") or "track") for t in picked]
        sig = str(self._last_status.get("time_signature") or "4/4")
        beats = 4
        if "/" in sig:
            try:
                beats = max(1, int(sig.split("/", 1)[0]))
            except ValueError:
                beats = 4
        tempo = self._last_status.get("tempo")
        try:
            tempo_n = float(tempo) if tempo not in (None, "") else None
        except (TypeError, ValueError):
            tempo_n = None
        return {
            "source": "MidiTrack",
            "hasClip": bool(names),
            "clipName": ", ".join(names) if names else "tick a MIDI track",
            "beatsPerBar": beats,
            "tempo": tempo_n,
            "spec": {
                "genre": "melodicHouse",
                "technique": "ghostGroove",
                "context": "groove",
                "lengthBars": 1,
                "beatsPerBar": beats,
                "intensity": 0.6,
                "density": 0.6,
                "swing": 0,
                "humTiming": 0.3,
                "humVel": 0.3,
                "seed": 1,
            },
            "availableTargets": ["newClip", "replace", "append", "newTrack", "playhead"],
            "noteCount": 0,
        }

    def _on_webview_message(self, payload: Any) -> None:
        if payload is None or payload == "":
            self._show_page("actions")
            return
        raw = payload if isinstance(payload, str) else json.dumps(payload)
        try:
            data = json.loads(raw) if isinstance(payload, str) else payload
        except json.JSONDecodeError:
            self.log("Webview tool sent invalid payload.")
            return
        if not isinstance(data, dict):
            self._show_page("actions")
            return
        tool_id = self._webview_tool_id
        if tool_id == "breakdowns":
            self._run_breakdowns(data)
        elif tool_id == "bbencut":
            self._run_bbencut(data)
        elif tool_id == "arrangement-helper":
            self._run_arrangement_helper(data)
        else:
            self.log(f"No run handler registered for webview tool '{tool_id}'.")
            self._show_page("actions")

    def _run_breakdowns(self, request: dict[str, Any]) -> None:
        targets = self.selected_tracks()
        if not targets:
            messagebox.showinfo("Live Actions", "Select at least one track in the sidebar first.")
            return
        notes = request.get("notes") or []
        if not notes:
            messagebox.showinfo("Live Actions", "No notes generated to insert.")
            return
        payload = {
            "tracks": [
                {"key": t.get("key"), "index": t.get("index"), "kind": t.get("kind"), "path": t.get("path")}
                for t in targets
            ],
            "fields": {
                "target": str(request.get("target") or "newClip"),
                "lengthBeats": request.get("lengthBeats") or 4,
                "name": str(request.get("name") or "Breakdowns"),
                "notes": notes,
            },
        }
        self.bridge.send("/live-actions/run", "breakdowns", json.dumps(payload))
        self.log(
            "Inserted fill '%s' (%d notes) as %s on %d track(s)."
            % (payload["fields"]["name"], len(notes), payload["fields"]["target"], len(targets))
        )

    def _run_bbencut(self, request: dict[str, Any]) -> None:
        # Step 4/5/6 of the BBenCut plan: send the computed cut sequence to
        # the bridge's runBbencut job, which resolves the real source clip
        # (file path + Arrangement position) from Live's Detail View
        # selection and places non-roll slices as real Arrangement clips.
        # Roll groups (Step 5) get pre-rendered to real WAVs here, on a
        # worker thread, before the payload is sent -- but only when the
        # source clip is unwarped (see docs\plans\bbencut-step5-roll-
        # rendering.md for why). Step 6 adds two safety gates before any of
        # that: a blocking "N individual undo steps" confirmation (this app
        # has no transaction wrap), and a hard BAKE_THRESHOLD -- above it the
        # whole run gets baked into one WAV and placed as a single clip
        # instead of flooding runBbencut's placement loop, or refused
        # outright if the source is warped (baking needs the same unwarped-
        # only beats-to-seconds conversion roll rendering already requires).
        # See docs\plans\bbencut-step6-bake-and-safety.md for the full
        # reasoning, including why Task-based chunking was deliberately
        # deferred rather than built this pass.
        targets = self.selected_tracks()
        if not targets:
            messagebox.showinfo("Live Actions", "Tick the source audio track in the sidebar first.")
            return
        fields = {
            "algorithm": request.get("algorithm"),
            "params": request.get("params") or {},
            "totalLengthBeats": request.get("totalLengthBeats"),
            "loopLengthBeats": request.get("loopLengthBeats"),
            "slices": request.get("slices") or [],
            "rollGroups": request.get("rollGroups") or [],
        }
        payload = {
            "tracks": [
                {"key": t.get("key"), "index": t.get("index"), "kind": t.get("kind"), "path": t.get("path")}
                for t in targets
            ],
            "fields": fields,
        }
        track_name = str(targets[0].get("name") or targets[0].get("key") or "the ticked track")
        track_path = str(targets[0].get("path") or "")
        roll_groups = fields["rollGroups"]
        total_count = len(fields["slices"])  # slicer.ts gives one entry per placement,
                                              # real clip or roll placeholder -- already the true total.
        threshold = bbencut_bake_render.BAKE_THRESHOLD

        def send_and_log() -> None:
            self.bridge.send("/live-actions/run", "bbencut", json.dumps(payload))
            self.log(
                "BBenCut: sent %d slice(s) for %s to the bridge for placement."
                % (len(fields["slices"]), fields["algorithm"])
            )

        def placement_message(count: int, roll_count: int) -> str:
            roll_clause = ", including %d rendered roll group(s)" % roll_count if roll_count else ""
            return (
                "This will place %d Arrangement clip(s) on %s%s.\n\n"
                "Each clip is a separate action — this is %d individual undo steps, "
                "not one atomic action.\n\nContinue?" % (count, track_name, roll_clause, count)
            )

        def confirm_on_main(title: str, message: str) -> bool:
            picked = {"ok": False}
            done = threading.Event()

            def ask() -> None:
                picked["ok"] = messagebox.askyesno(title, message)
                done.set()

            self.after(0, ask)
            done.wait()
            return picked["ok"]

        def error_on_main(title: str, message: str) -> None:
            done = threading.Event()

            def show() -> None:
                messagebox.showerror(title, message)
                done.set()

            self.after(0, show)
            done.wait()

        self._show_page("actions")

        if total_count <= threshold and not roll_groups:
            # No worker thread needed -- nothing to fetch, and _run_bbencut
            # already runs on the Tk main thread here.
            if not messagebox.askyesno("BBenCut — Confirm Placement", placement_message(total_count, 0)):
                self.log("BBenCut: cancelled by user.")
                return
            send_and_log()
            return

        # Everything past here needs warping/tempo/sampleFile off the source
        # clip -- either to decide bake-vs-refuse, or to render roll groups --
        # so fetch it once on a worker thread (bbencut_source is a blocking
        # OSC call; this method runs on the Tk main thread and can't block it).
        self.log("BBenCut: checking source clip…")

        def worker() -> None:
            info = self.bridge.call_live("bbencut_source", {"trackPath": track_path})
            if not info.get("ok"):
                err = str(info.get("error") or "unknown error")
                self.after(0, lambda err=err: self.log("✗ BBenCut: could not read source clip (%s)." % err))
                error_on_main(
                    "BBenCut — Run Refused",
                    "Could not read the source clip (%s). Nothing was placed." % err,
                )
                return

            sample_file = str(info.get("sampleFile") or "")
            tempo = float(info.get("tempo") or 0)
            warping = bool(info.get("warping"))

            if total_count > threshold:
                if warping:
                    self.after(0, lambda: self.log(
                        "✗ BBenCut: refused -- %d clips exceeds the %d-clip safety threshold on a warped source."
                        % (total_count, threshold)
                    ))
                    error_on_main(
                        "BBenCut — Run Refused",
                        "This run would place %d clips, above the %d-clip safety threshold. Baking to a "
                        "single file requires an unwarped source clip, and the source clip loaded in "
                        "Detail View is warped. Turn off warping on the source clip, or reduce the run "
                        "below %d clips, and try again." % (total_count, threshold, threshold),
                    )
                    return
                confirmed = confirm_on_main(
                    "BBenCut — Confirm Bake",
                    "This run would place %d clips, above the %d-clip safety threshold. BBenCut will "
                    "bake the full sequence into one audio file instead and place it as a single "
                    "Arrangement clip — one undo step, not %d.\n\nContinue?" % (total_count, threshold, total_count),
                )
                if not confirmed:
                    self.after(0, lambda: self.log("BBenCut: cancelled by user."))
                    return
                self.after(0, lambda: self.log("BBenCut: baking %d clips into one file…" % total_count))
                bake = bbencut_bake_render.render_full_bake(
                    bbencut_ffmpeg_util.resolve_ffmpeg(self.settings),
                    bbencut_ffmpeg_util.resolve_ffprobe(self.settings),
                    settings_store.samples_dir(self.settings) / "BBenCut Bakes",
                    sample_file,
                    tempo,
                    warping,
                    fields["slices"],
                    roll_groups,
                )
                if not bake.get("ok"):
                    reason = bake.get("reason")
                    self.after(0, lambda reason=reason: self.log("✗ BBenCut: bake failed (%s)." % reason))
                    error_on_main("BBenCut — Bake Failed", "Could not bake this run: %s" % reason)
                    return
                total_length = fields.get("totalLengthBeats") or 0
                fields["slices"] = [{
                    "arrangementStartTime": 0,
                    "duration": total_length,
                    "filePath": bake["path"],
                    "loopSettings": {
                        "looping": False,
                        "startMarker": 0,
                        "endMarker": total_length,
                        "loopStart": 0,
                        "loopEnd": total_length,
                    },
                }]
                fields["rollGroups"] = []
                self.after(0, send_and_log)
                return

            # Under threshold, with roll groups: dry-run confirm, then render
            # as Step 5 did.
            if not confirm_on_main("BBenCut — Confirm Placement", placement_message(total_count, len(roll_groups))):
                self.after(0, lambda: self.log("BBenCut: cancelled by user."))
                return

            self.after(0, lambda: self.log("BBenCut: rendering %d roll group(s)…" % len(roll_groups)))
            try:
                result = bbencut_roll_render.render_roll_groups(
                    bbencut_ffmpeg_util.resolve_ffmpeg(self.settings),
                    bbencut_ffmpeg_util.resolve_ffprobe(self.settings),
                    settings_store.samples_dir(self.settings) / "BBenCut Rolls",
                    sample_file,
                    tempo,
                    warping,
                    roll_groups,
                )
                for idx, path in result["rendered"].items():
                    sentinel = "__ROLL_GROUP_%d__" % idx
                    for slice_ in fields["slices"]:
                        if slice_.get("filePath") == sentinel:
                            slice_["filePath"] = path

                rendered_count = len(result["rendered"])
                skipped = result["skipped"]
                if skipped:
                    reasons = "; ".join("#%s: %s" % (s["index"], s["reason"]) for s in skipped)
                    summary = "BBenCut: rendered %d roll group(s), %d not rendered -- %s" % (
                        rendered_count, len(skipped), reasons,
                    )
                else:
                    summary = "BBenCut: rendered %d roll group(s)." % rendered_count
                self.after(0, lambda summary=summary: self.log(summary))
            except Exception as exc:  # never take the window down for a render failure
                self.after(0, lambda exc=exc: self.log("✗ BBenCut: roll rendering failed unexpectedly (%s)." % exc))
            self.after(0, send_and_log)

        threading.Thread(target=worker, daemon=True).start()

    def _run_arrangement_helper(self, request: dict[str, Any]) -> None:
        # Steps 4-5 of the arrangement-helper plan (§3c): the two-call plan,
        # confirm, execute sequence. arrangement_plan (Step 3) computes real
        # numbers read-only; Step 4 added the Python-side cap check and the
        # real-numbers confirm dialog(s); Step 5 (the parking-lane move
        # algorithm, "the test the first draft would have failed") is now
        # implemented in the bridge's arrangement_execute, so a plan with
        # moved > 0 is no longer refused here -- it's sent through with the
        # rest of the fields and the bridge parks, rebuilds, and lands.
        section_track_path = str(request.get("sectionTrackPath") or "")
        if section_track_path:
            self._save_tool_prefs({"id": "arrangement-helper"}, {"sectionTrackPath": section_track_path})
        self._show_page("actions")

        if not section_track_path:
            self.log("Arrangement Helper: no section track chosen -- nothing to plan.")
            return

        ticked_paths: list[str] = []
        for t in self._tracks:
            path = str(t.get("path") or "")
            if not path or path == section_track_path:
                continue
            var = self._track_vars.get(t.get("key"))
            if var is not None and var.get():
                ticked_paths.append(path)

        remap_all_tracks = bool(request.get("remapAllTracks"))
        plan_fields = {
            "sections": request.get("sections") or [],
            "createLocators": bool(request.get("createLocators")),
            "remapAllTracks": remap_all_tracks,
            "renameTrack": bool(request.get("renameTrack")),
            "sectionTrackPath": section_track_path,
            "scanCount": int(request.get("scanCount") or 0),
            # Real as of Step 3b: the dialog echoes back the isEditing flag
            # arrangement_scan seeded it with at open time.
            "isEditing": bool(request.get("isEditing")),
            "beatsPerBar": self._arrangement_helper_context().get("beatsPerBar"),
            "tickedTrackPaths": ticked_paths,
        }
        CAP = 80  # matches the bridge's own redundant check inside computeArrangementPlan

        def confirm_on_main(title: str, message: str) -> bool:
            picked = {"ok": False}
            done = threading.Event()

            def ask() -> None:
                picked["ok"] = messagebox.askyesno(title, message)
                done.set()

            self.after(0, ask)
            done.wait()
            return picked["ok"]

        def error_on_main(title: str, message: str) -> None:
            done = threading.Event()

            def show() -> None:
                messagebox.showerror(title, message)
                done.set()

            self.after(0, show)
            done.wait()

        def worker() -> None:
            plan = self.bridge.call_live("arrangement_plan", plan_fields)
            if not plan.get("ok"):
                reason = str(plan.get("message") or plan.get("error") or "unknown error")
                self.after(0, lambda reason=reason: self.log("✗ Arrangement Helper: plan refused -- %s" % reason))
                return

            write_count = int(plan.get("writeCount") or 0)
            moved = int(plan.get("moved") or 0)
            section_count = int(plan.get("sectionCount") or 0)

            # Cap check, using the plan's own numbers, before any confirm is
            # shown -- earlier than a check made inside the write job would
            # be, i.e. before the user has already said yes.
            if write_count > CAP:
                self.after(0, lambda: self.log(
                    "✗ Arrangement Helper: refused -- %d write operations exceeds the %d-operation "
                    "safety cap." % (write_count, CAP)
                ))
                error_on_main(
                    "Arrangement Helper — Run Refused",
                    "This run would take %d write operations, above the %d-operation safety cap. "
                    "Nothing was written." % (write_count, CAP),
                )
                return

            undo_steps = int(plan.get("undoStepCount") or 0)
            move_line = (
                " and moves %d existing clip(s) on remap track(s)" % moved if moved > 0 else ""
            )
            confirmed = confirm_on_main(
                "Arrangement Helper — Confirm",
                "This creates %d section clip(s)%s, as %d individual undo step(s).\n\n"
                "This cannot be undone in one step -- save your Set first. A failure partway "
                "through this run can leave temporary clips behind that won't be auto-removed."
                "\n\nContinue?" % (section_count, move_line, undo_steps),
            )
            if not confirmed:
                self.after(0, lambda: self.log("Arrangement Helper: cancelled by user."))
                return

            if remap_all_tracks:
                remap_count = int(plan.get("remapTrackCount") or 0)
                confirmed = confirm_on_main(
                    "Arrangement Helper — Whole Project",
                    "Whole Project is on -- this also affects all %d eligible track(s), not just "
                    "ticked ones.\n\nContinue?" % remap_count,
                )
                if not confirmed:
                    self.after(0, lambda: self.log("Arrangement Helper: cancelled by user."))
                    return

            exec_fields = dict(plan_fields)
            exec_fields["fingerprint"] = plan.get("fingerprint") or {}
            exec_payload = {"fields": exec_fields}

            def send_and_log() -> None:
                self.bridge.send("/live-actions/run", "arrangement-helper", json.dumps(exec_payload))
                self.log(
                    "Arrangement Helper: sent %d section(s)%s to the bridge for execution."
                    % (section_count, move_line)
                )
                self._await_tool_result("Arrangement Helper", timeout_ms=20000)

            self.after(0, send_and_log)

        threading.Thread(target=worker, daemon=True).start()

    def _close_webview(self) -> None:
        if self._webview is not None:
            try:
                self._webview.destroy()
            except Exception:
                pass
            self._webview = None
        self._webview_host = None

    def _grow_window(self) -> None:
        if not self._prev_geometry:
            self._prev_geometry = self.geometry()
        self.geometry("1280x880")
        self.minsize(1100, 760)

    def _restore_window(self) -> None:
        if self._prev_geometry:
            self.geometry(self._prev_geometry)
            self._prev_geometry = ""
        self.minsize(860, 580)

    # ── Track Selection & Custom Toggle Rows ───────────────────────────────────

    def selected_tracks(self) -> list[dict[str, Any]]:
        picked = []
        for track in self._tracks:
            var = self._track_vars.get(track["key"])
            if var is not None and var.get():
                picked.append(track)
        return picked

    def _selection_summary(self) -> str:
        picked = self.selected_tracks()
        if not picked:
            return "No tracks selected"
        names = [str(t.get("name") or t["key"]) for t in picked]
        if len(names) <= 3:
            return ", ".join(names)
        return "%d tracks (%s…)" % (len(names), ", ".join(names[:2]))

    def _update_track_summaries(self) -> None:
        picked_count = len(self.selected_tracks())
        total_count = len(self._tracks)

        summary_text = (
            "No tracks selected"
            if picked_count == 0
            else ("All %d tracks active" % total_count if picked_count == total_count else "%d of %d tracks active" % (picked_count, total_count))
        )

        if hasattr(self, "sidebar_track_summary"):
            try:
                self.sidebar_track_summary.configure(
                    text=summary_text,
                    fg=ACCENT if picked_count > 0 else TEXT_MUTED,
                )
            except tk.TclError:
                pass

        if hasattr(self, "tool_target_summary"):
            try:
                self.tool_target_summary.configure(text="Applying to: " + self._selection_summary())
            except tk.TclError:
                pass

    def _fill_track_list(self) -> None:
        host = self.track_list_sidebar
        for child in host.winfo_children():
            child.destroy()

        if not self._tracks:
            tk.Label(
                host, text="No tracks detected.\nConnect to Live to list tracks.",
                bg=SURFACE, fg=TEXT_MUTED, font=FONT_SMALL, justify="left",
            ).pack(anchor="w", padx=6, pady=8)
            return

        for track in self._tracks:
            key = track["key"]
            if key not in self._track_vars:
                self._track_vars[key] = tk.BooleanVar(value=bool(track.get("selected_in_live")))

            var = self._track_vars[key]
            kind = str(track.get("kind") or "audio").lower()
            name = str(track.get("name") or key)

            # Custom styled track row item
            row = tk.Frame(host, bg=SURFACE)
            row.pack(fill="x", pady=2)

            # Indicator box: [ ✓ ] or [   ]
            ind_btn = tk.Label(
                row,
                text=" ✓ " if var.get() else "   ",
                bg=ACCENT if var.get() else SURFACE_INPUT,
                fg=ACCENT_TEXT if var.get() else TEXT_MUTED,
                font=FONT_SECTION, cursor="hand2",
                highlightbackground=BORDER, highlightthickness=1,
            )
            ind_btn.pack(side="left", padx=(2, 6))

            # Track Label
            lbl = tk.Label(
                row, text=name,
                bg=SURFACE, fg=TEXT if var.get() else TEXT_MUTED,
                font=FONT_BODY_BOLD if var.get() else FONT_BODY,
                cursor="hand2", anchor="w",
            )
            lbl.pack(side="left", fill="x", expand=True)

            # Kind Badge
            kind_tag = "MIDI" if kind == "midi" else ("RET" if kind == "return" else ("MST" if kind == "master" else "AUD"))
            tk.Label(
                row, text=kind_tag,
                bg=SURFACE_INPUT, fg=ACCENT_VIOLET if kind == "midi" else TEXT_MUTED,
                font=FONT_SECTION, padx=4, pady=1,
            ).pack(side="right", padx=(2, 2))

            def _toggle(_e=None, v=var, b=ind_btn, l=lbl):
                new_state = not v.get()
                v.set(new_state)
                b.configure(
                    text=" ✓ " if new_state else "   ",
                    bg=ACCENT if new_state else SURFACE_INPUT,
                    fg=ACCENT_TEXT if new_state else TEXT_MUTED,
                )
                l.configure(
                    fg=TEXT if new_state else TEXT_MUTED,
                    font=FONT_BODY_BOLD if new_state else FONT_BODY,
                )
                self._update_track_summaries()

            ind_btn.bind("<Button-1>", _toggle)
            lbl.bind("<Button-1>", _toggle)
            row.bind("<Button-1>", _toggle)

        self._update_track_summaries()

    def _set_all_tracks(self, value: bool) -> None:
        for var in self._track_vars.values():
            var.set(value)
        self._fill_track_list()

    def _use_live_selection(self) -> None:
        if not self._tracks:
            self._request_tracks()
            return
        for track in self._tracks:
            var = self._track_vars.get(track["key"])
            if var is not None:
                var.set(bool(track.get("selected_in_live")))
        self._fill_track_list()

    # ── OSC Bridge Handler & Heartbeat ─────────────────────────────────────────

    def _ping(self) -> None:
        self.bridge.send("/live-actions/ping")
        self.log("OSC Ping sent to bridge (127.0.0.1:%s)." % self.settings.get("bridge_port"))

    def _status(self) -> None:
        self.bridge.send("/live-actions/status")
        self.log("Requested Live Set status.")

    def _request_tracks(self) -> None:
        self.bridge.send("/live-actions/tracks")
        self.log("Requested track hierarchy from Live.")

    def _reset_bridge(self) -> None:
        # The recovery path that doesn't require re-adding the device in
        # Live: rebuild the app's own listener socket/thread (in case that's
        # what died) and ask the Max-side js to clear any stranded job and
        # re-arm itself (in case that's what died instead). Either half can
        # fail independently -- run both every time rather than guessing
        # which one is actually broken.
        self.log("Resetting Live Actions Bridge connection…")
        try:
            self.bridge.restart()
        except OSError as exc:
            self.log("✗ Bridge reset failed: %s" % exc)
            messagebox.showerror(
                "Live Actions — Reset Failed",
                "Could not rebuild the bridge socket:\n\n%s\n\n"
                "Check that port %s isn't already in use by another copy of "
                "this app." % (exc, self.settings.get("listen_port")),
            )
            return
        self.bridge.send("/live-actions/reset")
        self.log("Bridge socket rebuilt; sent reset to the Max device.")

    def _save_tool_prefs(self, tool: dict[str, Any], fields: dict[str, Any]) -> None:
        tool_id = str(tool.get("id") or "")
        if not tool_id:
            return
        prefs = dict(self.settings.get("tool_prefs") or {})
        prefs[tool_id] = dict(fields)
        self.settings["tool_prefs"] = prefs
        try:
            settings_store.save_settings(self.settings)
        except OSError as exc:
            self.log("Could not save tool preferences: %s" % exc)

    def _reset_tool_prefs(self) -> None:
        tool = self._open_tool
        if not tool:
            return
        tool_id = str(tool.get("id") or "")
        prefs = dict(self.settings.get("tool_prefs") or {})
        if tool_id in prefs:
            del prefs[tool_id]
            self.settings["tool_prefs"] = prefs
            try:
                settings_store.save_settings(self.settings)
            except OSError as exc:
                self.log("Could not reset tool preferences: %s" % exc)
        self.log("Reset preferences for %s." % (tool.get("name") or tool_id))
        self._open_tool_screen(tool)

    def _run_open_tool(self) -> None:
        tool = self._open_tool
        if not tool:
            return
        if str(tool.get("runtime") or "live") == "host":
            self._run_host_tool(tool)
            return
        if not self._connected:
            self._set_run_status("⚠  Bridge offline — start Live and drop the bridge device.", WARN)
            messagebox.showwarning(
                "Live Actions — Not Connected",
                "The Live Actions Bridge is not connected.\n\n"
                "Make sure Ableton Live is running and that 'Live Actions Bridge.amxd' "
                "is dropped onto an audio track.",
            )
            return
        set_scope = str(tool.get("scope") or "") == "set"
        targets = self.selected_tracks()
        if not set_scope and not targets:
            self._set_run_status("⚠  No tracks selected — tick tracks on the left first.", WARN)
            messagebox.showinfo(
                "Live Actions — No Tracks Selected",
                "Please tick at least one track in the TARGET TRACKS panel on the left "
                "before running this action.",
            )
            return

        payload = {
            "tracks": [
                {"key": t.get("key"), "index": t.get("index"), "kind": t.get("kind"), "path": t.get("path")}
                for t in targets
            ],
            "fields": {key: var.get() for key, var in self._tool_field_vars.items()},
        }
        self._save_tool_prefs(tool, payload["fields"])
        self.bridge.send("/live-actions/run", str(tool.get("id") or ""), json.dumps(payload))
        name = str(tool.get("name") or tool.get("id") or "tool")
        if set_scope:
            self.log("Executing %s across the entire Set." % name)
            self._set_run_status("Running %s on full set…" % name, TEXT_MUTED)
        else:
            self.log("Executing %s on %d track(s)." % (name, len(targets)))
            self._set_run_status("Running %s on %d track(s)…" % (name, len(targets)), TEXT_MUTED)
        self._await_tool_result(name)

    def _run_host_tool(self, tool: dict[str, Any]) -> None:
        """Run a runtime:"host" tool on a worker thread — no Live/bridge required."""
        handler = HOST_TOOLS.get(str(tool.get("id") or ""))
        name = str(tool.get("name") or tool.get("id") or "tool")
        if handler is None:
            self._set_run_status("⚠  No host handler registered for this tool.", ERR)
            self.log("✗ %s: no host handler registered." % name)
            return
        if self._host_tool_running:
            self._set_run_status("Already running — wait for the current run to finish.", WARN)
            return
        self._host_tool_running = True
        try:
            self.run_btn.configure(state="disabled")
        except tk.TclError:
            pass

        fields = {key: var.get() for key, var in self._tool_field_vars.items()}
        settings = dict(self.settings)
        self._save_tool_prefs(tool, fields)

        destination = str(fields.get("destination") or "").strip().lower()
        wants_live_placement = destination == "add to live set"
        wants_pc_dialog = destination == "save to pc"
        connected = self._connected
        targets = self.selected_tracks() if wants_live_placement else []

        self._set_run_status("Running %s…" % name, TEXT_MUTED)
        self.log("Running %s (host)." % name)

        def worker() -> None:
            try:
                result = handler(fields, settings)
            except Exception as exc:  # host handlers must never take the app down
                result = {"ok": False, "message": "Unexpected error: %s" % exc}
            if result.get("ok") and wants_live_placement:
                result = self._place_generated_file(result, targets, connected, name)
            self.after(0, lambda: self._finish_host_tool(name, result, wants_pc_dialog))

        threading.Thread(target=worker, daemon=True).start()

    def _place_generated_file(
        self, result: dict[str, Any], targets: list[dict[str, Any]], connected: bool, tool_name: str = "File"
    ) -> dict[str, Any]:
        """Place an already-generated file onto a ticked audio track (worker thread).

        Validation (offline / no audio track) happens before any dialog is shown —
        the slot picker only ever appears for a confirmed-valid target.
        """
        path = result.get("path")
        base_message = str(result.get("message") or "Generated.")
        if not path:
            return result
        if not connected:
            result["message"] = base_message + " Bridge offline — file saved, not placed in Live."
            result["placed"] = False
            return result
        audio_targets = [t for t in targets if str(t.get("kind") or "audio") == "audio"]
        if not audio_targets:
            result["message"] = base_message + " No ticked audio track — file saved, not placed."
            result["placed"] = False
            return result
        track = audio_targets[0]
        track_index = track.get("index")

        slots_resp = self.bridge.call_live("read_track", {"track_index": track_index})
        if not slots_resp.get("ok"):
            reason = str(slots_resp.get("error") or slots_resp.get("message") or "unknown error")
            result["message"] = base_message + " Could not read clip slots: " + reason
            result["placed"] = False
            return result
        slots = slots_resp.get("session_clips") or []
        if not slots:
            result["message"] = base_message + " Track has no clip slots — file saved, not placed."
            result["placed"] = False
            return result

        picked = {"slot": None}
        done = threading.Event()

        def ask_on_main() -> None:
            picked["slot"] = self._ask_placement_slot(track, slots, tool_name)
            done.set()

        self.after(0, ask_on_main)
        done.wait()
        slot_index = picked["slot"]

        if slot_index is None:
            result["message"] = base_message + " Placement skipped."
            result["placed"] = False
            return result

        resp = self.bridge.call_live(
            "create_clip", {"track_index": track_index, "slot_index": slot_index, "sample_file": path}
        )
        if resp.get("ok"):
            track_name = str(track.get("name") or track.get("key") or "track")
            result["message"] = base_message + " Placed on " + track_name + " (slot %d)." % (slot_index + 1)
            result["placed"] = True
        else:
            reason = str(resp.get("error") or resp.get("message") or "unknown error")
            result["message"] = base_message + " Placement failed: " + reason
            result["placed"] = False
        return result

    def _ask_placement_slot(
        self, track: dict[str, Any], slots: list[dict[str, Any]], tool_name: str = "File"
    ) -> int | None:
        """Modal slot picker. Must run on the main thread — called via self.after from the worker."""
        track_name = str(track.get("name") or track.get("key") or "Track")

        dialog = tk.Toplevel(self)
        dialog.title("Place %s" % tool_name)
        dialog.configure(bg=SURFACE)
        dialog.transient(self)
        dialog.resizable(False, False)

        tk.Label(
            dialog, text='Choose a clip slot on "%s":' % track_name,
            bg=SURFACE, fg=TEXT, font=FONT_BODY_BOLD, anchor="w",
        ).pack(fill="x", padx=16, pady=(14, 6))

        list_frame = tk.Frame(dialog, bg=SURFACE)
        list_frame.pack(fill="both", expand=True, padx=16)

        result_box: dict[str, Any] = {"slot": None}
        confirmed_overwrite = {"value": False}
        selected = tk.IntVar(value=-1)
        first_empty: int | None = None

        warn_label = tk.Label(
            dialog, text="", bg=SURFACE, fg=WARN, font=FONT_SMALL,
            anchor="w", wraplength=340, justify="left",
        )

        def on_slot_change() -> None:
            confirmed_overwrite["value"] = False
            warn_label.configure(text="")

        for slot in slots:
            idx = int(slot.get("index"))
            has_clip = bool(slot.get("has_clip"))
            clip_name = str((slot.get("clip") or {}).get("name") or "") if has_clip else ""
            if has_clip:
                label = "%d — \"%s\"" % (idx + 1, clip_name) if clip_name else "%d — occupied" % (idx + 1)
            else:
                label = "%d — empty" % (idx + 1)
                if first_empty is None:
                    first_empty = idx
            tk.Radiobutton(
                list_frame, text=label, value=idx, variable=selected, command=on_slot_change,
                bg=SURFACE, fg=TEXT, selectcolor=SURFACE_INPUT,
                activebackground=SURFACE, activeforeground=ACCENT,
                font=FONT_BODY, anchor="w", justify="left",
            ).pack(fill="x", anchor="w", pady=1)

        if first_empty is not None:
            selected.set(first_empty)

        warn_label.pack(fill="x", padx=16, pady=(6, 0))

        def confirm() -> None:
            pick = selected.get()
            if pick < 0:
                warn_label.configure(text="Pick a slot first.")
                return
            chosen = next((s for s in slots if int(s.get("index")) == pick), None)
            if chosen and chosen.get("has_clip") and not confirmed_overwrite["value"]:
                confirmed_overwrite["value"] = True
                warn_label.configure(text="That slot has a clip — click Place again to replace it.")
                return
            result_box["slot"] = pick
            dialog.destroy()

        def cancel() -> None:
            result_box["slot"] = None
            dialog.destroy()

        btn_row = tk.Frame(dialog, bg=SURFACE)
        btn_row.pack(fill="x", padx=16, pady=14)
        self._primary_btn(btn_row, "Place", confirm).pack(side="left")
        self._ghost_btn(btn_row, "Cancel", cancel, mini=True).pack(side="left", padx=8)

        dialog.protocol("WM_DELETE_WINDOW", cancel)
        dialog.update_idletasks()
        dialog.geometry("+%d+%d" % (self.winfo_rootx() + 80, self.winfo_rooty() + 80))
        dialog.grab_set()
        self.wait_window(dialog)
        return result_box["slot"]

    def _finish_host_tool(self, name: str, result: dict[str, Any], wants_pc_dialog: bool = False) -> None:
        self._host_tool_running = False
        try:
            self.run_btn.configure(state="normal")
        except tk.TclError:
            pass
        ok = bool(result.get("ok"))
        message = str(result.get("message") or ("Done." if ok else "Failed."))
        path = result.get("path")
        if ok:
            self._set_run_status("✓ " + message, OK)
            self.log("✓ %s: %s" % (name, message))
            if path:
                self.log("Saved: %s" % path)
        else:
            self._set_run_status("⚠  " + message, ERR)
            self.log("✗ %s: %s" % (name, message))

        self._show_run_result(path)

        if ok and path and wants_pc_dialog:
            self._offer_save_as(path, name)

    def _show_run_result(self, path: str | None) -> None:
        if not hasattr(self, "run_result_frame"):
            return
        if path:
            self._last_result_path = path
            self.run_result_label.configure(text="📄  " + path)
            self.run_result_frame.pack(fill="x")
        else:
            self._last_result_path = None
            self.run_result_frame.pack_forget()

    def _offer_save_as(self, path: str, tool_name: str = "File") -> None:
        src = Path(path)
        ext = src.suffix or ".wav"
        label = _SAVE_FILE_LABELS.get(ext.lower(), "%s file" % ext.lstrip(".").upper())
        picked = filedialog.asksaveasfilename(
            title="Save %s As" % tool_name,
            initialdir=str(src.parent),
            initialfile=src.name,
            defaultextension=ext,
            filetypes=[(label, "*" + ext), ("All files", "*.*")],
        )
        if not picked:
            self.log("Save As canceled — file remains at " + str(src))
            return
        dest = Path(picked)
        try:
            if dest.resolve() != src.resolve():
                shutil.copyfile(src, dest)
        except OSError as exc:
            messagebox.showerror("Save %s" % tool_name, "Could not save to that location:\n%s" % exc)
            return
        self._show_run_result(str(dest))
        self.log("Saved copy to: %s" % dest)

    def _open_last_result_folder(self) -> None:
        path = getattr(self, "_last_result_path", None)
        if not path:
            return
        try:
            subprocess.run(["explorer", "/select," + path])
        except OSError as exc:
            self.log("Could not open folder: %s" % exc)

    def _set_run_status(self, msg: str, color: str = TEXT_MUTED) -> None:
        if hasattr(self, "run_status_label"):
            try:
                self.run_status_label.configure(text=msg, fg=color)
            except tk.TclError:
                pass

    def _await_tool_result(self, name: str, timeout_ms: int = 1800) -> None:
        self._result_wait_id += 1
        wait_id = self._result_wait_id

        def check() -> None:
            if wait_id != self._result_wait_id:
                return
            if wait_id in self._result_wait_ids_seen:
                return
            if not self._connected:
                self._set_run_status("⚠  Bridge offline — no reply received.", ERR)
                self.log("No response from %s — Live Actions Bridge is offline." % name)
            else:
                self._set_run_status("⚠  No reply from Live — try re-dropping the bridge device.", WARN)
                self.log("No reply from %s. Re-drop the bridge device in Live if needed." % name)

        self.after(timeout_ms, check)

    def _set_connected(self, connected: bool) -> None:
        if connected == self._connected:
            return
        self._connected = connected
        if connected:
            badge_text = "● ON: " + self._host_track.upper() if self._host_track else "● ONLINE"
            self.badge.configure(text=badge_text, bg=OK, fg=ACCENT_TEXT)
            self.host_track_label.configure(
                text="Host: " + (self._host_track if self._host_track else "Audio track"),
                fg=TEXT,
            )
            self.status_ticker.configure(
                text="Connected to Live. Bridge is active on " + (self._host_track or "track") + ".",
                fg=OK,
            )
            self.log("Connected to Live Actions Bridge in Ableton.")
            # Hide offline warning in setup banner
            if hasattr(self, "offline_hint"):
                try:
                    self.offline_hint.pack_forget()
                except tk.TclError:
                    pass
            self.bridge.send("/live-actions/status")
            self.bridge.send("/live-actions/tracks")
            self._refresh_live_status()
        else:
            self._host_track = ""
            self.badge.configure(text="● OFFLINE", bg=SURFACE_INPUT, fg=TEXT_MUTED)
            self.set_name_label.configure(text="(Waiting for Live Set...)")
            self.host_track_label.configure(text="Bridge: Offline", fg=TEXT_MUTED)
            self.chip_tempo._val_label.configure(text="— BPM")  # type: ignore[attr-defined]
            self.chip_sig._val_label.configure(text="—")  # type: ignore[attr-defined]
            self.chip_tracks._val_label.configure(text="0")  # type: ignore[attr-defined]
            self.status_ticker.configure(
                text="Bridge offline — drop 'Live Actions Bridge.amxd' on an audio track in Live.",
                fg=WARN,
            )
            # Show offline warning in setup banner
            if hasattr(self, "offline_hint"):
                try:
                    self.offline_hint.pack(fill="x", pady=(6, 0))
                except tk.TclError:
                    pass
            self._refresh_live_status()
            self.log("Bridge connection lost.")

    def _on_osc(self, address: str, args: list[Any]) -> None:
        self.after(0, lambda: self._handle_osc(address, args))

    def _handle_osc(self, address: str, args: list[Any]) -> None:
        if address == "__error__":
            # Not a real OSC address -- BridgeClient's own transport-layer
            # events (dropped/oversized packets, a chunked reply timing out,
            # the listener thread restarting). Surfacing these is the whole
            # point of the fix: this used to fail completely silently.
            self.log("⚠ Bridge transport: " + " ".join(str(a) for a in args))
            return

        if address in ("/live-actions/pong", "/live-actions/hello"):
            payload = self._parse_osc_json(args)
            if payload:
                self._remember_host(payload)
            self._set_connected(True)
            return

        if address == "/live-actions/status":
            self._apply_status(args)
            return

        if address == "/live-actions/tracks":
            self._apply_tracks(args)
            return

        if address == "/live-actions/result":
            self._result_wait_ids_seen.add(self._result_wait_id)
            msg = " ".join(str(a) for a in args)
            self.log("✓ Done: " + msg)
            self.status_ticker.configure(text="✓ Action completed: " + msg[:60], fg=OK)
            self._set_run_status("✓ Done! " + msg[:80], OK)
            return

        if address == "/live-actions/api/reply":
            self.log("API Reply: " + " ".join(str(a) for a in args))

    def _remember_host(self, data: dict[str, Any]) -> None:
        if data.get("on_track") and data.get("track"):
            self._host_track = str(data.get("track") or "")
        elif data.get("host_track"):
            self._host_track = str(data.get("host_track") or "")
        if self._connected and self._host_track:
            try:
                self.badge.configure(text="● ON: " + self._host_track.upper(), bg=OK, fg=ACCENT_TEXT)
                self.host_track_label.configure(text="Host: " + self._host_track, fg=TEXT)
            except tk.TclError:
                pass

    def _parse_osc_json(self, args: list[Any]) -> dict[str, Any] | None:
        if not args:
            return None
        raw = args[0]
        if isinstance(raw, dict):
            return raw
        try:
            data = json.loads(str(raw))
        except (TypeError, json.JSONDecodeError):
            return None
        return data if isinstance(data, dict) else None

    def _apply_status(self, args: list[Any]) -> None:
        raw = args[0] if args else ""
        try:
            data = json.loads(str(raw))
        except json.JSONDecodeError:
            return

        if not data.get("ok"):
            self._last_status = {}
            err = str(data.get("error") or "Live API initializing")
            self.set_name_label.configure(text=err)
            return

        self._last_status = data
        self._remember_host(data)

        name = str(data.get("name") or "Untitled Live Set")
        tempo = data.get("tempo")
        tracks = data.get("tracks")
        sig = str(data.get("time_signature") or "4/4")

        tempo_str = ("%.1f" % float(tempo)) if tempo is not None else "—"

        self.set_name_label.configure(text=name)
        # Genius binds custom instructions per Live Set -- report the name the
        # moment Live gives us one, same as the WebView2 shell does.
        try:
            genius_client.remember_live_set(name)
        except Exception:
            pass
        self.chip_tempo._val_label.configure(text=tempo_str + " BPM")  # type: ignore[attr-defined]
        self.chip_sig._val_label.configure(text=sig)  # type: ignore[attr-defined]
        self.chip_tracks._val_label.configure(text=str(tracks if tracks is not None else "0"))  # type: ignore[attr-defined]

        self.status_ticker.configure(
            text="Live: %s | %s BPM | %s | %s Tracks" % (name, tempo_str, sig, tracks),
            fg=TEXT,
        )
        self.log("Set Status: %s @ %s BPM (%s tracks)." % (name, tempo_str, tracks))

    def _apply_tracks(self, args: list[Any]) -> None:
        raw = args[0] if args else ""
        try:
            data = json.loads(str(raw))
        except json.JSONDecodeError:
            return
        if not data.get("ok"):
            return

        tracks = data.get("tracks") or []
        self._tracks = [t for t in tracks if isinstance(t, dict) and t.get("key")]

        known = {t["key"] for t in self._tracks}
        for key in list(self._track_vars):
            if key not in known:
                del self._track_vars[key]

        had_any = any(var.get() for var in self._track_vars.values())
        for track in self._tracks:
            key = track["key"]
            if key not in self._track_vars:
                default = bool(track.get("selected_in_live")) if not had_any else False
                self._track_vars[key] = tk.BooleanVar(value=default)

        self._fill_track_list()
        self._fill_session_track_list()
        self.log("Synchronized %d tracks from Live." % len(self._tracks))

    def _tick(self) -> None:
        try:
            self.bridge.send("/live-actions/ping")
        except OSError:
            pass

        silent = (time.time() - self.bridge.last_pong) > OFFLINE_AFTER_S
        if silent and self.bridge.has_pending_calls():
            # A call_live() is still in flight -- the bridge may just be
            # busy building a large synchronous reply (a Genius read_set
            # against a real Set can legitimately take several seconds),
            # not actually gone. Let that call's own timeout decide instead
            # of flipping the badge mid-action.
            silent = False
        if silent and self._connected:
            self._set_connected(False)

        self.after(int(PING_EVERY_S * 1000), self._tick)

    # ── Log & Diagnostics ──────────────────────────────────────────────────────

    def log(self, line: str) -> None:
        stamp = time.strftime("%H:%M:%S")
        text = stamp + "  " + line
        self._log_lines.append(text)
        if hasattr(self, "log_widget"):
            try:
                self.log_widget.configure(state="normal")
                self.log_widget.insert("end", text + "\n")
                self.log_widget.see("end")
                self.log_widget.configure(state="disabled")
            except tk.TclError:
                pass

    def _copy_log(self) -> None:
        text = "\n".join(self._log_lines)
        self.clipboard_clear()
        self.clipboard_append(text)
        self.log("Console log copied to clipboard.")

    # ── Genius AI Chat ─────────────────────────────────────────────────────────

    def _refresh_genius_status(self) -> None:
        key_ok       = bool(str(self.settings.get("api_key") or "").strip())
        knowledge_ok = settings_store.knowledge_dir(self.settings).is_dir()
        samples_ok   = settings_store.samples_dir(self.settings).is_dir()

        parts = [
            "API Key: OK" if key_ok else "API Key: Missing",
            "Library: Ready" if knowledge_ok else "Library: Not found",
            "Samples: Ready" if samples_ok else "Samples: Not set",
        ]
        if hasattr(self, "genius_status"):
            try:
                self.genius_status.configure(text="  •  ".join(parts))
            except tk.TclError:
                pass

    def _refresh_live_status(self) -> None:
        if not hasattr(self, "live_bridge_status_label"):
            return
        try:
            if self._connected:
                self.live_bridge_status_label.configure(
                    text="● Live Bridge: Ready", fg=OK,
                )
            else:
                self.live_bridge_status_label.configure(
                    text="● Live Bridge: Offline", fg=TEXT_DIM,
                )
        except tk.TclError:
            pass

    def _refresh_ppal_status(self) -> None:
        self._refresh_live_status()

    def _append_genius(self, who: str, text: str, tag: str) -> None:
        try:
            self.genius_chat.configure(state="normal")
            self.genius_chat.insert("end", who + "\n", tag)
            self.genius_chat.insert("end", text.strip() + "\n\n")
            self.genius_chat.see("end")
            self.genius_chat.configure(state="disabled")
        except tk.TclError:
            pass

    def _clear_genius(self) -> None:
        self._genius_messages = []
        try:
            self.genius_chat.configure(state="normal")
            self.genius_chat.delete("1.0", "end")
            self.genius_chat.configure(state="disabled")
        except tk.TclError:
            pass

    def _send_genius(self) -> None:
        if self._busy:
            return
        text = self.genius_entry.get("1.0", "end").strip()
        if not text:
            return
        self.genius_entry.delete("1.0", "end")
        self._genius_messages.append({"role": "user", "content": text})
        self._append_genius("You", text, "you")
        self._busy = True
        self._thinking_active = False
        self._cancel_event = threading.Event()
        self._append_genius("Genius", "Thinking…", "meta")

        # Show Stop buttons and disable Send button
        if hasattr(self, "genius_send_btn"):
            try:
                self.genius_send_btn.configure(state="disabled")
            except tk.TclError:
                pass
        if hasattr(self, "genius_stop_btn"):
            try:
                self.genius_stop_btn.pack(side="left", padx=(6, 0))
            except tk.TclError:
                pass
        if hasattr(self, "genius_top_stop_btn"):
            try:
                self.genius_top_stop_btn.pack(side="left", padx=(0, 8))
            except tk.TclError:
                pass

        live_line = (
            "Live connected: %s @ %s" % (self.set_name_label.cget("text"), self.chip_tempo._val_label.cget("text"))  # type: ignore[attr-defined]
            if self._connected else "Live offline"
        )
        settings = dict(self.settings)
        history  = list(self._genius_messages)
        cancel_evt = self._cancel_event

        def on_tool_call(fn_name: str, status: str) -> None:
            """Called from worker thread — schedule UI update on main thread."""
            self.after(0, lambda s=status: self._on_genius_tool_call(s))

        def on_thinking(chunk: str) -> None:
            """Called from worker thread — stream thinking text in real-time."""
            self.after(0, lambda c=chunk: self._on_genius_thinking(c))

        def confirm(kind: str, detail: dict) -> bool:
            """Called from the worker thread — a Tk dialog can only be built on the main
            thread, so the request is marshalled there and the worker waits for the answer."""
            answer: dict[str, bool] = {"ok": False}
            done = threading.Event()
            self.after(0, lambda: self._ask_genius_confirm(kind, detail, answer, done))
            done.wait()
            return bool(answer["ok"])

        def work() -> None:
            try:
                reply = genius_client.ask_genius(
                    settings, history, live_line,
                    bridge=self.bridge,
                    cancel_event=cancel_evt,
                    on_tool_call=on_tool_call,
                    on_thinking=on_thinking,
                    confirm=confirm,
                )
                err = ""
            except Exception as exc:
                reply = ""
                err = str(exc)
            self.after(0, lambda: self._finish_genius(reply, err))

        threading.Thread(target=work, daemon=True).start()

    def _ask_genius_confirm(self, kind: str, detail: dict, answer: dict, done: threading.Event) -> None:
        """The spend-approval dialog (main thread). Every path that is not an explicit Yes
        leaves answer["ok"] False, and `done` is always set so the worker can never hang.

        messagebox has no checkbox, so this is a small Toplevel. The "don't ask again" flag
        is held in memory on this window for the session only -- the user asked for session
        scope, so it must never reach settings.json.
        """
        try:
            if getattr(self, "_genius_confirm_skip", None) is None:
                self._genius_confirm_skip = set()
            if str(kind) in self._genius_confirm_skip:
                answer["ok"] = True
                done.set()
                return
            win = tk.Toplevel(self)
            win.title(str(detail.get("title") or "Confirm"))
            win.transient(self)
            win.resizable(False, False)
            frame = ttk.Frame(win, padding=14)
            frame.pack(fill="both", expand=True)
            body = str(detail.get("body") or "")
            if body:
                ttk.Label(frame, text=body, wraplength=460, justify="left").pack(anchor="w", pady=(0, 8))
            for row in detail.get("rows") or []:
                line = ttk.Frame(frame)
                line.pack(fill="x", pady=1)
                ttk.Label(line, text=str(row[0]) + ":", width=10).pack(side="left", anchor="nw")
                ttk.Label(line, text=str(row[1]), wraplength=380, justify="left").pack(side="left", anchor="w")
            remember = tk.BooleanVar(value=False)
            ttk.Checkbutton(
                frame,
                text=str(detail.get("rememberLabel") or "Don't ask again this session"),
                variable=remember,
            ).pack(anchor="w", pady=(10, 4))

            def close(ok: bool) -> None:
                if ok and remember.get():
                    self._genius_confirm_skip.add(str(kind))
                answer["ok"] = ok
                try:
                    win.destroy()
                finally:
                    done.set()

            buttons = ttk.Frame(frame)
            buttons.pack(fill="x", pady=(6, 0))
            ttk.Button(buttons, text="Cancel", command=lambda: close(False)).pack(side="right")
            ttk.Button(
                buttons, text=str(detail.get("confirmLabel") or "Continue"), command=lambda: close(True)
            ).pack(side="right", padx=(0, 6))
            win.protocol("WM_DELETE_WINDOW", lambda: close(False))     # the X means no
            win.bind("<Escape>", lambda _e: close(False))
            win.grab_set()
        except Exception as exc:                                       # noqa: BLE001 -- never strand the worker
            self.log("Could not show the approval dialog: %s" % exc)
            done.set()

    def _stop_genius(self) -> None:
        """Immediately abort active Genius thinking and tool execution."""
        if self._cancel_event is not None:
            self._cancel_event.set()
        self._finish_genius("", "[Stopped by user]")

    def _on_genius_thinking(self, chunk: str) -> None:
        """Stream model's live thoughts directly into the chat widget."""
        try:
            self.genius_chat.configure(state="normal")
            if not getattr(self, "_thinking_active", False):
                self._thinking_active = True
                # Replace the placeholder "Thinking…" with live thought stream header
                found = self.genius_chat.search("Thinking…", "end", backwards=True)
                if found:
                    self.genius_chat.delete(found, f"{found}+9c")
                    self.genius_chat.insert(found, "💭 Thinking:\n", "meta")
                else:
                    self.genius_chat.insert("end", "💭 Thinking:\n", "meta")
            self.genius_chat.insert("end", chunk, "thinking")
            self.genius_chat.see("end")
            self.genius_chat.configure(state="disabled")
        except tk.TclError:
            pass

    def _on_genius_tool_call(self, status: str) -> None:
        """Show inline tool-call progress in the chat widget."""
        try:
            self.genius_chat.configure(state="normal")
            if getattr(self, "_thinking_active", False):
                self._thinking_active = False
                self.genius_chat.insert("end", "\n\n")
            self.genius_chat.insert("end", status + "\n", "tool")
            self.genius_chat.see("end")
            self.genius_chat.configure(state="disabled")
        except tk.TclError:
            pass

    def _finish_genius(self, reply: str, err: str) -> None:
        self._busy = False
        self._thinking_active = False
        # Hide Stop buttons and re-enable Send button
        if hasattr(self, "genius_stop_btn"):
            try:
                self.genius_stop_btn.pack_forget()
            except tk.TclError:
                pass
        if hasattr(self, "genius_top_stop_btn"):
            try:
                self.genius_top_stop_btn.pack_forget()
            except tk.TclError:
                pass
        if hasattr(self, "genius_send_btn"):
            try:
                self.genius_send_btn.configure(state="normal")
            except tk.TclError:
                pass

        # Clean up any trailing thinking placeholder
        try:
            self.genius_chat.configure(state="normal")
            found = self.genius_chat.search("Thinking…", "end", backwards=True)
            if found:
                start = self.genius_chat.search("Genius", found, backwards=True)
                if start:
                    self.genius_chat.delete(start, "end")
            self.genius_chat.configure(state="disabled")
        except tk.TclError:
            pass

        if err:
            self._append_genius("Genius", err if err.startswith("[") else ("Error: " + err), "meta")
            # Keep _genius_messages a valid, alternating conversation -- a
            # request error must not leave the just-appended user message
            # dangling with no reply. Some providers (Anthropic) reject a
            # history with two consecutive user turns outright, and even
            # where it's tolerated the model loses track of what happened
            # to the unanswered message on the next send.
            #
            # Stored as a neutral session note, not the bracketed banner text
            # verbatim -- that text read back on a later turn as the model's own
            # prior words taught it to narrate itself as a serial quitter rather
            # than report what actually happened (see shell_genius.py's STOPPED
            # for the WebView2 shell's version of the same fix).
            note = "the user stopped generation" if err == "[Stopped by user]" else err
            self._genius_messages.append({
                "role": "assistant",
                "content": "(Session note: this turn ended without a reply -- %s.)" % note,
            })
            return
        if reply:
            self._genius_messages.append({"role": "assistant", "content": reply})
            self._append_genius("Genius", reply, "genius")
        # Refresh status after a reply (Live state may have changed)
        self.after(200, self._refresh_live_status)

    def _open_pal_local(self) -> None:
        path = find_pal_local(str(self.settings.get("pal_local_shortcut") or ""))
        if path is None:
            messagebox.showinfo(
                "Producer Pal Local",
                "No Producer Pal Local shortcut found on desktop or configured in Settings.\n"
                "Please configure its path in Preferences.",
            )
            return
        try:
            if path.suffix.lower() == ".ps1":
                subprocess.Popen(
                    ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(path)],
                    cwd=str(path.parent),
                )
            else:
                os.startfile(path)  # type: ignore[attr-defined]
            self.log("Launched Producer Pal Local from " + str(path))
        except OSError as exc:
            messagebox.showerror("Producer Pal Local", str(exc))

    # ── Settings Persistence ───────────────────────────────────────────────────

    # ── Saved API Keys (multi-provider vault) ──────────────────────────────────

    def _fill_saved_keys_list(self) -> None:
        host = getattr(self, "_saved_keys_list", None)
        if host is None or not host.winfo_exists():
            return
        for child in host.winfo_children():
            child.destroy()

        keys = self.settings.get("api_keys") or []
        if not keys:
            tk.Label(
                host, text="No saved keys yet — paste a key below, detect its provider, then save it.",
                bg=SURFACE, fg=TEXT_MUTED, font=FONT_SMALL, anchor="w",
            ).pack(fill="x")
            return

        active_id = self.settings.get("active_api_key_id")
        for entry in keys:
            row = tk.Frame(host, bg=SURFACE_INPUT, highlightbackground=BORDER_SUBTLE, highlightthickness=1)
            row.pack(fill="x", pady=2)
            is_active = entry.get("id") == active_id
            dot = "● " if is_active else "○ "
            tk.Label(
                row, text=dot + str(entry.get("label") or "(unlabeled)"),
                bg=SURFACE_INPUT, fg=TEXT if is_active else TEXT_MUTED, font=FONT_BODY_BOLD if is_active else FONT_BODY,
                anchor="w",
            ).pack(side="left", padx=(8, 6), pady=5)
            tk.Label(
                row, text=str(entry.get("provider") or "unknown"),
                bg=SURFACE, fg=ACCENT_VIOLET, font=FONT_SECTION, padx=5, pady=1,
            ).pack(side="left", padx=(0, 8))
            masked = str(entry.get("api_key") or "")
            masked = (masked[:4] + "…" + masked[-4:]) if len(masked) > 10 else "****"
            tk.Label(row, text=masked, bg=SURFACE_INPUT, fg=TEXT_DIM, font=FONT_MONO_BOLD).pack(side="left", padx=(0, 10))
            self._ghost_btn(row, "Use", lambda e=entry: self._use_saved_key(e), mini=True).pack(side="right", padx=(0, 6), pady=3)
            self._ghost_btn(row, "✕", lambda e=entry: self._delete_saved_key(e.get("id", "")), mini=True).pack(side="right", padx=(0, 4), pady=3)

    def _use_saved_key(self, entry: dict[str, Any]) -> None:
        self.fields["api_key"].delete(0, "end")
        self.fields["api_key"].insert(0, str(entry.get("api_key") or ""))
        provider = str(entry.get("provider") or "")
        api_base = str(entry.get("api_base") or ai_providers.PROVIDER_DEFAULTS.get(provider, ""))
        self.fields["api_base"].delete(0, "end")
        self.fields["api_base"].insert(0, api_base)
        self.model_combo.set(str(entry.get("model") or ""))
        self._active_provider_var.set(provider)
        self.settings["active_api_key_id"] = str(entry.get("id") or "")
        self._persist_settings()
        self._fill_saved_keys_list()
        self._refresh_models_for_active_key()
        self.log("Using saved key '%s'." % entry.get("label"))

    def _delete_saved_key(self, entry_id: str) -> None:
        if not entry_id:
            return
        self.settings["api_keys"] = [e for e in (self.settings.get("api_keys") or []) if e.get("id") != entry_id]
        if self.settings.get("active_api_key_id") == entry_id:
            self.settings["active_api_key_id"] = ""
        self._persist_settings()
        self._fill_saved_keys_list()
        self._refresh_all_tts_key_pickers()

    def _save_current_key_as_new(self) -> None:
        api_key = self.fields["api_key"].get().strip()
        if not api_key:
            self.log("Save key: paste an API key first.")
            return
        label = self._new_key_label_var.get().strip() or ("Key %d" % (len(self.settings.get("api_keys") or []) + 1))
        entry = {
            "id": "k_" + uuid.uuid4().hex[:10],
            "label": label,
            "provider": self._active_provider_var.get().strip(),
            "api_key": api_key,
            "api_base": self.fields["api_base"].get().strip(),
            "model": self.model_combo.get().strip(),
        }
        keys = list(self.settings.get("api_keys") or [])
        keys.append(entry)
        self.settings["api_keys"] = keys
        self.settings["active_api_key_id"] = entry["id"]
        self._new_key_label_var.set("")
        self._persist_settings()
        self._fill_saved_keys_list()
        self._refresh_all_tts_key_pickers()
        self.log("Saved key '%s'." % label)

    def _detect_provider_for_active_key(self) -> None:
        api_key = self.fields["api_key"].get().strip()
        if not api_key:
            self.log("Detect provider: no API key entered.")
            return
        self.log("Detecting provider…")

        def worker() -> None:
            provider, api_base, message = ai_providers.detect_provider(api_key)

            def apply() -> None:
                self.log(message)
                if provider:
                    self._active_provider_var.set(provider)
                    self.fields["api_base"].delete(0, "end")
                    self.fields["api_base"].insert(0, api_base)
                    self._refresh_models_for_active_key()

            self.after(0, apply)

        threading.Thread(target=worker, daemon=True).start()

    def _refresh_models_for_active_key(self) -> None:
        api_key = self.fields["api_key"].get().strip()
        provider = self._active_provider_var.get().strip()
        api_base = self.fields["api_base"].get().strip()
        if not api_key:
            self.log("Refresh models: no API key entered.")
            return
        self.log("Fetching models…")

        def worker() -> None:
            models = ai_providers.list_models(provider, api_key, api_base)

            def apply() -> None:
                if not hasattr(self, "model_combo") or not self.model_combo.winfo_exists():
                    return
                self.model_combo["values"] = models
                self.log("Found %d model(s)." % len(models) if models else "No models returned — check the key/provider, or type a model name by hand.")

            self.after(0, apply)

        threading.Thread(target=worker, daemon=True).start()

    def _refresh_all_tts_key_pickers(self) -> None:
        labels = [str(e.get("label") or "") for e in (self.settings.get("api_keys") or [])]
        for entry_ref in getattr(self, "_tts_profile_rows", []):
            combo = entry_ref.get("saved_key_combo")
            if combo is not None and combo.winfo_exists():
                combo["values"] = labels

    # ── Genius Agents (Settings: Agent picker + per-agent tool cards) ─────────

    def _refresh_agent_picker(self) -> None:
        """Populate the Settings 'Agent' combobox with agents not yet enabled."""
        if not hasattr(self, "fields") or "agent_picker" not in self.fields:
            return
        combo = self.fields["agent_picker"]
        if not combo.winfo_exists():
            return
        enabled = set(self.settings.get("enabled_agents") or [])
        available = [a for a in agent_registry.list_agents(self.settings) if a["slug"] not in enabled]
        self._agent_picker_by_title = {a["title"]: a["slug"] for a in available}
        combo["values"] = list(self._agent_picker_by_title.keys())
        combo.set(available[0]["title"] if available else "")

    def _enable_picked_agent(self) -> None:
        if not hasattr(self, "fields") or "agent_picker" not in self.fields:
            return
        title = self.fields["agent_picker"].get().strip()
        slug = getattr(self, "_agent_picker_by_title", {}).get(title)
        if not slug:
            return
        enabled = list(self.settings.get("enabled_agents") or [])
        if slug in enabled:
            return
        agent = agent_registry.load_agent(self.settings, slug)
        if agent is None:
            return
        enabled.append(slug)
        self.settings["enabled_agents"] = enabled
        prefs = dict(self.settings.get("agent_tool_prefs") or {})
        prefs[slug] = agent_registry.default_tool_map(agent)
        self.settings["agent_tool_prefs"] = prefs
        self._persist_settings()
        self._agent_card_expanded = getattr(self, "_agent_card_expanded", {})
        self._agent_card_expanded[slug] = True
        self._refresh_agent_picker()
        self._render_agent_cards()
        self._refresh_agent_switcher()

    def _remove_agent(self, slug: str) -> None:
        self.settings["enabled_agents"] = [s for s in (self.settings.get("enabled_agents") or []) if s != slug]
        prefs = dict(self.settings.get("agent_tool_prefs") or {})
        prefs.pop(slug, None)
        self.settings["agent_tool_prefs"] = prefs
        if self.settings.get("active_agent") == slug:
            self.settings["active_agent"] = ""
        self._persist_settings()
        self._refresh_agent_picker()
        self._render_agent_cards()
        self._refresh_agent_switcher()

    def _toggle_agent_card(self, slug: str) -> None:
        self._agent_card_expanded = getattr(self, "_agent_card_expanded", {})
        self._agent_card_expanded[slug] = not self._agent_card_expanded.get(slug, False)
        self._render_agent_cards()

    def _render_agent_cards(self) -> None:
        if not hasattr(self, "_agent_cards_container") or not self._agent_cards_container.winfo_exists():
            return
        for child in self._agent_cards_container.winfo_children():
            child.destroy()
        self._agent_card_expanded = getattr(self, "_agent_card_expanded", {})
        self._agent_tool_vars = {}

        for slug in (self.settings.get("enabled_agents") or []):
            agent = agent_registry.load_agent(self.settings, slug)
            if agent is not None:
                self._render_one_agent_card(agent)

    def _render_one_agent_card(self, agent: dict[str, Any]) -> None:
        slug = agent["slug"]
        card = tk.Frame(self._agent_cards_container, bg=SURFACE, highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        card.pack(fill="x", pady=(0, 8))

        header = tk.Frame(card, bg=SURFACE)
        header.pack(fill="x", padx=10, pady=6)

        expanded = self._agent_card_expanded.get(slug, False)
        tk.Button(
            header, text=("▾ " if expanded else "▸ ") + agent["title"],
            command=lambda: self._toggle_agent_card(slug),
            bg=SURFACE, fg=TEXT, activebackground=SURFACE, activeforeground=ACCENT,
            relief="flat", font=FONT_BODY_BOLD, bd=0, cursor="hand2", anchor="w",
        ).pack(side="left", fill="x", expand=True)
        self._ghost_btn(header, "Remove", lambda: self._remove_agent(slug), mini=True).pack(side="right")

        if not expanded:
            return

        body = tk.Frame(card, bg=SURFACE)
        body.pack(fill="x", padx=10, pady=(0, 10))

        default_map = agent_registry.default_tool_map(agent)
        stored = (self.settings.get("agent_tool_prefs") or {}).get(slug) or {}
        self._agent_tool_vars[slug] = {}

        for group, names in agent_registry.TOOL_GROUPS.items():
            names_here = [n for n in names if n in default_map]
            if not names_here:
                continue
            group_row = tk.Frame(body, bg=SURFACE)
            group_row.pack(fill="x", pady=(6, 2))
            tk.Label(group_row, text=group, bg=SURFACE, fg=ACCENT, font=FONT_SECTION, anchor="w").pack(side="left")
            self._ghost_btn(
                group_row, "All", lambda ns=names_here: self._set_agent_group(slug, ns, True), mini=True,
            ).pack(side="right", padx=(4, 0))
            self._ghost_btn(
                group_row, "None", lambda ns=names_here: self._set_agent_group(slug, ns, False), mini=True,
            ).pack(side="right")

            for name in names_here:
                var = tk.BooleanVar(value=bool(stored.get(name, default_map[name])))
                self._agent_tool_vars[slug][name] = var
                tk.Checkbutton(
                    body, text=name, variable=var,
                    command=lambda n=name: self._on_agent_tool_toggle(slug, n),
                    bg=SURFACE, fg=TEXT, selectcolor=SURFACE_INPUT,
                    activebackground=SURFACE, activeforeground=TEXT,
                    font=FONT_SMALL, anchor="w",
                ).pack(fill="x", padx=(8, 0))

    def _on_agent_tool_toggle(self, slug: str, tool_name: str) -> None:
        var = self._agent_tool_vars.get(slug, {}).get(tool_name)
        if var is None:
            return
        prefs = dict(self.settings.get("agent_tool_prefs") or {})
        agent_map = dict(prefs.get(slug) or {})
        agent_map[tool_name] = bool(var.get())
        prefs[slug] = agent_map
        self.settings["agent_tool_prefs"] = prefs
        self._persist_settings()

    def _set_agent_group(self, slug: str, names: list[str], value: bool) -> None:
        prefs = dict(self.settings.get("agent_tool_prefs") or {})
        agent_map = dict(prefs.get(slug) or {})
        for name in names:
            agent_map[name] = value
        prefs[slug] = agent_map
        self.settings["agent_tool_prefs"] = prefs
        self._persist_settings()
        self._render_agent_cards()

    def _refresh_agent_switcher(self) -> None:
        """Populate the chat top-bar agent switcher from enabled_agents. Called
        after Settings enables/removes an agent so the switcher updates without
        a restart, and once at startup."""
        if not hasattr(self, "genius_agent_switch") or not self.genius_agent_switch.winfo_exists():
            return
        enabled = list(self.settings.get("enabled_agents") or [])
        self._agent_switch_slug_by_title = {"(none)": ""}
        values = ["(none)"]
        current_title = "(none)"
        active_slug = str(self.settings.get("active_agent") or "")
        for slug in enabled:
            agent = agent_registry.load_agent(self.settings, slug)
            if agent is None:
                continue
            values.append(agent["title"])
            self._agent_switch_slug_by_title[agent["title"]] = slug
            if slug == active_slug:
                current_title = agent["title"]
        self.genius_agent_switch["values"] = values
        self.genius_agent_switch_var.set(current_title)

    def _on_agent_switch_selected(self, _event: tk.Event | None = None) -> None:
        title = self.genius_agent_switch_var.get()
        slug = getattr(self, "_agent_switch_slug_by_title", {}).get(title, "")
        self.settings["active_agent"] = slug
        self._persist_settings()
        if slug:
            agent = agent_registry.load_agent(self.settings, slug)
            self._append_genius("System", f"Switched to {agent['title'] if agent else slug}.", "meta")
        else:
            self._append_genius("System", "Switched back to stock Genius.", "meta")

    def _toggle_key(self) -> None:
        self.fields["api_key"].configure(show="" if self.show_key.get() else "*")

    def _on_api_key_typed(self, _event: tk.Event | None = None) -> None:
        if not hasattr(self, "fields") or "api_key" not in self.fields:
            return
        try:
            self.settings["api_key"] = self.fields["api_key"].get().strip()
        except tk.TclError:
            return
        self._refresh_genius_status()
        self._update_key_save_status()
        if self._key_save_after is not None:
            try:
                self.after_cancel(self._key_save_after)
            except tk.TclError:
                pass
        self._key_save_after = self.after(350, self._persist_settings)

    def _update_key_save_status(self) -> None:
        if not hasattr(self, "key_save_status"):
            return
        typed = ""
        if hasattr(self, "fields") and "api_key" in self.fields:
            try:
                typed = self.fields["api_key"].get().strip()
            except tk.TclError:
                pass
        else:
            typed = str(self.settings.get("api_key") or "").strip()
        saved = str(self._last_saved_key or "").strip()
        try:
            if typed and typed == saved:
                self.key_save_status.configure(text="✓ Key saved", fg=OK)
            elif typed and typed != saved:
                self.key_save_status.configure(text="Saving…", fg=TEXT_MUTED)
            else:
                self.key_save_status.configure(text="No key configured", fg=TEXT_MUTED)
        except tk.TclError:
            pass

    def _collect_fields(self) -> dict[str, Any]:
        data = dict(self.settings)
        if not hasattr(self, "fields"):
            return data
        for key, entry in self.fields.items():
            try:
                value: Any = entry.get().strip()
            except tk.TclError:
                continue
            if key in ("listen_port", "bridge_port"):
                try:
                    value = int(value)
                except ValueError:
                    value = self.settings.get(key)
            data[key] = value
        if hasattr(self, "_tts_profile_rows"):
            data["tts_profiles"] = self._collect_tts_profiles()
            data["active_tts_profile"] = self._collect_active_tts_profile()
        return data

    def _persist_settings(self, *, announce: bool = False, refresh_tools: bool = False) -> bool:
        if not hasattr(self, "fields"):
            return False
        if self._key_save_after is not None:
            try:
                self.after_cancel(self._key_save_after)
            except tk.TclError:
                pass
            self._key_save_after = None
        data = self._collect_fields()
        try:
            settings_store.save_settings(data)
        except OSError as exc:
            self.log("Could not save settings: " + str(exc))
            if announce:
                messagebox.showerror("Settings", "Could not save settings:\n" + str(exc))
            return False

        self.settings = data
        self._last_saved_key = str(data.get("api_key") or "")
        self._refresh_genius_status()
        self._update_key_save_status()
        if refresh_tools:
            self._refresh_tools()
        if announce:
            self.log("Preferences saved successfully.")
        return True

    def _save_settings_ui(self) -> None:
        self._persist_settings(announce=True, refresh_tools=True)

    def _test_key(self) -> None:
        self._persist_settings()
        data = self._collect_fields()

        def work() -> None:
            try:
                result = genius_client.test_key(data)
                self.after(0, lambda: messagebox.showinfo("API Key Test", "Success: " + result[:400]))
            except Exception as exc:
                self.after(0, lambda: messagebox.showerror("API Key Test", "Connection Failed:\n" + str(exc)))

        threading.Thread(target=work, daemon=True).start()

    def _open_settings_folder(self) -> None:
        settings_store.APP_DATA.mkdir(parents=True, exist_ok=True)
        os.startfile(settings_store.APP_DATA)  # type: ignore[attr-defined]

    # ── Single Instance & Raise Watcher ────────────────────────────────────────

    def _start_raise_watcher(self) -> None:
        global _RAISE_EVENT_HANDLE
        kernel32 = ctypes.windll.kernel32
        _RAISE_EVENT_HANDLE = kernel32.CreateEventW(None, False, False, RAISE_EVENT_NAME)
        handle = _RAISE_EVENT_HANDLE

        def watch() -> None:
            while True:
                if kernel32.WaitForSingleObject(handle, 0xFFFFFFFF) != 0:
                    return
                try:
                    self.after(0, self._bring_to_front)
                except Exception:
                    return

        threading.Thread(target=watch, daemon=True).start()

    def _bring_to_front(self) -> None:
        try:
            self.deiconify()
            self.state("normal")
        except tk.TclError:
            return
        self.lift()
        self.attributes("-topmost", True)
        self.after(250, lambda: self.attributes("-topmost", False))
        self.focus_force()
        hwnd = 0
        try:
            hwnd = int(str(self.wm_frame()), 16)
        except (TypeError, ValueError, tk.TclError):
            try:
                hwnd = int(self.winfo_id())
            except (TypeError, ValueError, tk.TclError):
                hwnd = 0
        if hwnd:
            _force_foreground(hwnd)

    def _quit(self) -> None:
        try:
            self._persist_settings()
        except Exception:
            pass
        self._close_webview()
        self.bridge.close()
        self.destroy()


_MUTEX_HANDLE = None
_RAISE_EVENT_HANDLE = None
ERROR_ALREADY_EXISTS = 183
_SUFFIX = settings_store.instance_suffix()
RAISE_EVENT_NAME = "Local\\LiveActionsRaiseHost" + _SUFFIX
MUTEX_NAME = "Local\\LiveActionsDesktopHost" + _SUFFIX
WINDOW_TITLE = "Live Actions — DAW Studio Host" + (f" [{settings_store.INSTANCE}]" if _SUFFIX else "")
SW_RESTORE = 9


def _claim_single_instance() -> bool:
    global _MUTEX_HANDLE
    kernel32 = ctypes.windll.kernel32
    _MUTEX_HANDLE = kernel32.CreateMutexW(None, False, MUTEX_NAME)
    return int(kernel32.GetLastError()) != ERROR_ALREADY_EXISTS


def _force_foreground(hwnd: int) -> None:
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    user32.ShowWindow(hwnd, SW_RESTORE)
    fg = user32.GetForegroundWindow()
    fg_tid = user32.GetWindowThreadProcessId(fg, None)
    this_tid = kernel32.GetCurrentThreadId()
    user32.AttachThreadInput(this_tid, fg_tid, True)
    user32.BringWindowToTop(hwnd)
    user32.SetForegroundWindow(hwnd)
    user32.AttachThreadInput(this_tid, fg_tid, False)


def _raise_existing() -> None:
    user32 = ctypes.windll.user32
    hwnd = user32.FindWindowW(None, WINDOW_TITLE)
    if not hwnd and not _SUFFIX:
        hwnd = user32.FindWindowW(None, "Live Actions")
    if hwnd:
        _force_foreground(hwnd)
    kernel32 = ctypes.windll.kernel32
    EVENT_MODIFY_STATE = 0x0002
    handle = kernel32.OpenEventW(EVENT_MODIFY_STATE, False, RAISE_EVENT_NAME)
    if handle:
        kernel32.SetEvent(handle)
        kernel32.CloseHandle(handle)


def main() -> None:
    if not _claim_single_instance():
        _raise_existing()
        return
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
