/* Shared component markup + mock session state for the redesign round.
   Tools come from window.LA_REAL (generated from the real tool.json manifests).
   Everything here returns HTML strings; layouts decide WHERE they go.
   Nothing in this file mentions a colour, font or radius -- that is the theme's job. */
(function () {
  const R = window.LA_REAL;
  const LA = (window.LA = {});
  LA.tools = R.tools;
  LA.themes = R.themes;

  LA.esc = (s) => String(s == null ? "" : s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const e = LA.esc;

  /* ---- mock live session (the only non-manifest data) ---------------------- */
  LA.set = { name: "Neon Nights 128.als", bpm: "128.00", sig: "4/4" };
  LA.tracks = [
    { id: 1, name: "Drums", kind: "MIDI", dev: ["Drum Rack", "Glue Compressor"] },
    { id: 2, name: "Bass", kind: "MIDI", dev: ["Wavetable", "Saturator"] },
    { id: 3, name: "Chords", kind: "MIDI", dev: ["Operator", "Chorus-Ensemble"] },
    { id: 4, name: "Lead", kind: "MIDI", dev: ["Drift", "Echo"] },
    { id: 5, name: "Vox", kind: "AUD", dev: ["Compressor", "EQ Eight"] },
    { id: 6, name: "Guitar DI", kind: "AUD", dev: ["Amp", "Cabinet"] },
    { id: 7, name: "FX Risers", kind: "AUD", dev: [] },
    { id: 8, name: "A  Reverb", kind: "RET", dev: ["Hybrid Reverb"] },
    { id: 9, name: "B  Delay", kind: "RET", dev: ["Echo"] },
    { id: 10, name: "Master", kind: "MST", dev: ["Limiter"] },
  ];
  LA.ui = { themesOpen: false };   // Preferences > Appearance is collapsible; collapsed by default (default state is an open question)
  LA.state = { connected: true, targets: new Set([2, 3, 4]) };
  LA.log = [
    ["22:41:07", "→", "/live-actions/ping"],
    ["22:41:07", "←", "/live-actions/pong  host=Bridge · track 1"],
    ["22:41:12", "→", "/live-actions/tracks"],
    ["22:41:12", "←", "10 tracks  (chunked reply reassembled)"],
    ["22:41:31", "→", "live_read_set"],
    ["22:41:31", "←", "ok  Neon Nights 128.als · 128.00 BPM · 4/4"],
  ];

  /* ---- icons --------------------------------------------------------------- */
  const P = {
    bolt: "M13 2 4 14h7l-1 8 9-12h-7z",
    brain: "M9 4a3 3 0 0 0-3 3 3 3 0 0 0-2 5 3 3 0 0 0 2 5 3 3 0 0 0 6 1V4a3 3 0 0 0-3 0zm6 0a3 3 0 0 1 3 3 3 3 0 0 1 2 5 3 3 0 0 1-2 5 3 3 0 0 1-6 1",
    gear: "M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zm7.4-2a1.6 1.6 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.6 1.6 0 0 0-1.8-.3 1.6 1.6 0 0 0-1 1.5V19a2 2 0 1 1-4 0v-.1a1.6 1.6 0 0 0-1-1.5 1.6 1.6 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.6 1.6 0 0 0 .3-1.8 1.6 1.6 0 0 0-1.5-1H5a2 2 0 1 1 0-4h.1a1.6 1.6 0 0 0 1.5-1 1.6 1.6 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.6 1.6 0 0 0 1.8.3h0a1.6 1.6 0 0 0 1-1.5V5a2 2 0 1 1 4 0v.1a1.6 1.6 0 0 0 1 1.5 1.6 1.6 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.6 1.6 0 0 0-.3 1.8v0a1.6 1.6 0 0 0 1.5 1H19a2 2 0 1 1 0 4h-.1a1.6 1.6 0 0 0-1.5 1z",
    pulse: "M3 12h4l3-8 4 16 3-8h4",
    tracks: "M4 6h16M4 12h16M4 18h16",
    search: "M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14zm9 16-4-4",
    right: "m9 6 6 6-6 6",
    down: "m6 9 6 6 6-6",
    x: "M6 6l12 12M18 6 6 18",
    play: "M7 4v16l13-8z",
    term: "m4 6 6 6-6 6M13 18h7",
    plus: "M12 5v14M5 12h14",
    open: "M14 4h6v6M20 4l-9 9M18 14v6H4V6h6",
    dock: "M3 4h18v16H3zM3 14h18",
  };
  LA.icon = (n, s = 16) => `<svg class="la-ic" width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${P[n] || ""}"/></svg>`;

  /* ---- small components ---------------------------------------------------- */
  LA.scopeOf = (t) => (t.scope === "set" ? { key: "set", label: "Set-Wide" } : t.ui === "webview" ? { key: "dialog", label: "Web Dialog" } : { key: "tracks", label: "Selected Tracks" });
  LA.scopePill = (t) => { const s = LA.scopeOf(t); return `<span class="la-pill" data-scope="${s.key}">${s.label}</span>`; };
  LA.toolStripe = (t) => `style="--tool:${e(t.accent || "#888")}"`;

  LA.pip = (label = true) => {
    const on = LA.state.connected;
    return `<span class="la-pip" data-on="${on}"><i></i>${label ? (on ? "Online" : "Offline") : ""}</span>`;
  };
  LA.chip = (k, v) => `<div class="la-chip"><span>${e(k)}</span><b>${e(v)}</b></div>`;
  LA.chips = () => LA.chip("BPM", LA.set.bpm) + LA.chip("Sig", LA.set.sig) + LA.chip("Tracks", LA.tracks.length);
  LA.kind = (k) => `<span class="la-kind" data-kind="${k}">${k}</span>`;

  LA.trackRow = (t, opts = {}) => {
    const on = LA.state.targets.has(t.id);
    return `<label class="la-track${on ? " on" : ""}" data-act="toggle-track" data-id="${t.id}">
      <span class="la-check" data-on="${on}"></span>
      <span class="la-track-n">${t.id}</span><span class="la-track-name">${e(t.name)}</span>${LA.kind(t.kind)}
      ${opts.devices ? `<span class="la-track-dev">${t.dev.length ? e(t.dev.join(" · ")) : "no devices"}</span>` : ""}</label>`;
  };
  LA.trackList = (opts) => LA.tracks.map((t) => LA.trackRow(t, opts)).join("");
  LA.targetSummary = () => { const n = LA.state.targets.size; return n ? `${n} track${n > 1 ? "s" : ""} targeted` : "No tracks targeted"; };
  LA.quickPicks = () => `<div class="la-quick"><button class="la-btn mini" data-act="all">All</button><button class="la-btn mini" data-act="none">None</button><button class="la-btn mini" data-act="livesel">Live Sel</button></div>`;

  LA.toolCard = (t, opts = {}) => `<article class="la-card${opts.active ? " active" : ""}" ${LA.toolStripe(t)} data-act="open-tool" data-id="${e(t.id)}" tabindex="0">
      <i class="la-stripe"></i>
      <div class="la-card-top"><h3>${e(t.name)}</h3>${LA.scopePill(t)}</div>
      <p>${e(t.description || "Opens its own interactive action screen.")}</p>
      <div class="la-card-foot"><span class="la-btn primary sm">${t.ui === "webview" ? "Open Dialog " + LA.icon("open", 13) : "Open &amp; Configure " + LA.icon("right", 13)}</span></div>
    </article>`;

  LA.toolRow = (t, opts = {}) => `<div class="la-row${opts.active ? " active" : ""}" ${LA.toolStripe(t)} data-act="${opts.act || "open-tool"}" data-id="${e(t.id)}" tabindex="0">
      <i class="la-dot"></i><div class="la-row-main"><b>${e(t.name)}</b><span>${e(t.description)}</span></div>${LA.scopePill(t)}<span class="la-row-go">${LA.icon(opts.open ? "down" : "right", 14)}</span></div>`;

  LA.field = (f) => {
    const hint = f.hint ? `<small>${e(f.hint)}</small>` : "";
    let ctl;
    if (f.type === "select" && f.options) ctl = `<select class="la-input">${f.options.map((o) => `<option${o === f.default ? " selected" : ""}>${e(o)}</option>`).join("")}</select>`;
    else if (f.type === "textarea") ctl = `<textarea class="la-input" rows="3">${e(f.default || "")}</textarea>`;
    else if (f.type === "file") ctl = `<div class="la-filepick"><input class="la-input" value="${e(f.default || "")}" placeholder="Choose a file…"><button class="la-btn ghost mini">Browse</button></div>`;
    else ctl = `<input class="la-input" value="${e(f.default == null ? "" : f.default)}">`;
    return `<label class="la-field"><span>${e(f.label)}</span>${ctl}${hint}</label>`;
  };

  /* Body of a tool's detail/run surface (fields + Run), used by every layout. */
  LA.toolBody = (t, o = {}) => {
    const s = LA.scopeOf(t);
    const more = t.fieldCount > t.fields.length ? `<p class="la-more">+ ${t.fieldCount - t.fields.length} more fields in the real tool</p>` : "";
    const scopeNote = s.key === "set" ? "Runs on the whole Live Set — track selection is ignored."
      : s.key === "dialog" ? "Opens its own dialog window. Nothing is written until you confirm inside it."
      : `Runs on the ${LA.state.targets.size} ticked track${LA.state.targets.size === 1 ? "" : "s"} only.`;
    const form = t.ui === "webview" ? "" : t.fields.map(LA.field).join("");
    return `<div class="la-tool-body" ${LA.toolStripe(t)}>
      ${o.head === false ? "" : `<div class="la-tool-head"><i class="la-stripe"></i><div><h2>${e(t.name)}</h2>${LA.scopePill(t)}</div></div>`}
      <p class="la-lede">${e(t.description)}</p>
      <div class="la-note">${e(scopeNote)}</div>
      ${form}${more}
      <div class="la-runrow"><button class="la-btn primary">${t.ui === "webview" ? "Open Interactive Dialog " + LA.icon("open", 14) : LA.icon("play", 13) + " Run Now"}</button>
      ${o.back === false ? "" : `<button class="la-btn ghost" data-act="close-tool">${o.backLabel || "Back"}</button>`}</div>
      <div class="la-result"><span>RESULT</span>Nothing run yet.</div></div>`;
  };

  LA.consoleLines = () => LA.log.map((l) => `<div class="la-logline"><time>${l[0]}</time><em>${l[1]}</em><span>${e(l[2])}</span></div>`).join("");

  LA.chat = () => `<div class="la-chat">
    <div class="la-bubble user"><span class="la-who">You</span>Make a 4-bar bassline in F♯ minor on the Bass track and name the clip “Sub Walk”.</div>
    <div class="la-bubble bot"><span class="la-who">Genius</span>Done — I wrote 16 notes into a new 4-bar clip on <b>2 · Bass</b> and named it “Sub Walk”.
      <div class="la-calls"><span class="la-call ok">live_create_clip ✓</span><span class="la-call ok">live_add_notes ✓</span><span class="la-call ok">live_rename_clip ✓</span></div></div>
    <div class="la-bubble user"><span class="la-who">You</span>Now duplicate it into the next three scenes and mutate each one a little.</div>
    <div class="la-bubble bot"><span class="la-who">Genius</span>Working… <div class="la-calls"><span class="la-call run">live_duplicate_clip …</span></div></div></div>`;
  LA.composer = () => `<div class="la-composer"><div class="la-prompts"><button class="la-btn ghost mini">Name my clips</button><button class="la-btn ghost mini">Build a drum fill</button><button class="la-btn ghost mini">Find the key</button></div>
    <div class="la-compose-row"><input class="la-input" placeholder="Ask Genius to work on your Set…"><button class="la-btn primary">Send</button></div></div>`;
  LA.agentChips = () => `<span class="la-tag">Stock Genius</span><span class="la-tag mono">grok-4.6</span>`;

  LA.settingsBody = () => `<div class="la-settings">
    <section class="la-collapsible" data-open="${LA.ui.themesOpen}"><button class="la-collapse" data-act="toggle-themes" aria-expanded="${LA.ui.themesOpen}">
        <span class="la-collapse-ic">${LA.icon(LA.ui.themesOpen ? "down" : "right", 16)}</span><h4>Appearance</h4>
        <span class="la-tag">${e((LA.themes.find((t) => t.slug === LA.currentTheme) || {}).label || "")}</span><span class="la-muted la-collapse-n">${LA.themes.length} themes</span></button>
      ${LA.ui.themesOpen ? `<p class="la-muted">A theme is one file. Pick any design kit — layout never changes.</p>
      <div class="la-swatches">${LA.themes.map((t) => `<button class="la-swatch${LA.currentTheme === t.slug ? " on" : ""}" data-act="theme" data-slug="${t.slug}"><i style="background:linear-gradient(135deg, ${e(t.bg)} 0 34%, ${e(t.surface)} 34% 62%, ${e(t.accent)} 62% 100%)"></i>${e(t.label)}</button>`).join("")}</div>` : ""}</section>
    <section><h4>Connection</h4><div class="la-two"><label class="la-field"><span>App listen port (UDP)</span><input class="la-input" value="11925"></label>
      <label class="la-field"><span>Bridge send port (UDP)</span><input class="la-input" value="11924"></label></div></section>
    <section><h4>AI provider</h4>
      <div class="la-keyrow on"><span class="la-check" data-on="true"></span><b>xAI · Main key</b><span class="la-tag mono">grok-4.6</span><span class="la-muted">xai-••••••••a91f</span></div>
      <div class="la-keyrow"><span class="la-check" data-on="false"></span><b>OpenAI · Backup</b><span class="la-tag mono">gpt-5</span><span class="la-muted">sk-••••••••7c2d</span></div>
      <div class="la-runrow"><button class="la-btn ghost">Test key</button><button class="la-btn ghost">Add key</button></div></section>
    <section><h4>Agents</h4>
      <div class="la-keyrow on"><span class="la-check" data-on="true"></span><b>Stock Genius</b><span class="la-muted">all tools enabled</span></div>
      <div class="la-keyrow"><span class="la-check" data-on="false"></span><b>Drum Doctor</b><span class="la-muted">7 of 14 tools</span></div></section>
    <section><h4>Folders</h4><label class="la-field"><span>Tools folder</span><input class="la-input" value="…\\Live Actions Helper\\tools"></label>
      <label class="la-field"><span>Knowledge folder</span><input class="la-input" value="B:\\Documents\\TRAINING DOCS"></label></section></div>`;

  /* ---- theme handling (preview chrome only -- never touches #app markup) --- */
  const q = new URLSearchParams(location.search);
  LA.currentTheme = q.get("theme") || "risograph-art-studio";
  LA.setTheme = (slug) => {
    LA.currentTheme = slug;
    document.getElementById("la-theme").href = `themes/${slug}.css`;
    document.querySelectorAll(".la-swatch").forEach((b) => b.classList.toggle("on", b.dataset.slug === slug));
    const sel = document.getElementById("pc-theme"); if (sel) sel.value = slug;
  };
  LA.mountChrome = (layoutId) => {
    if (q.get("embed")) return;
    const layouts = [["a", "A · Workbench"], ["b", "B · Rail + slide-over"], ["c", "C · Command list"], ["d", "D · Session deck"]];
    const c = document.createElement("div"); c.id = "pc";
    c.innerHTML = `<b>PREVIEW</b>${layouts.map(([k, n]) => `<a href="layout-${k}.html?theme=${LA.currentTheme}" data-k="${k}"${k === layoutId ? ' class="on"' : ""}>${n}</a>`).join("")}
      <select id="pc-theme">${LA.themes.map((t) => `<option value="${t.slug}">${e(t.label)}</option>`).join("")}</select>`;
    document.body.appendChild(c);
    const sel = c.querySelector("select"); sel.value = LA.currentTheme;
    sel.onchange = () => { LA.setTheme(sel.value); c.querySelectorAll("a").forEach((a) => (a.href = `layout-${a.dataset.k}.html?theme=${sel.value}`)); };
  };
  /* ---- status bar + console drawer (same parts in every layout) ------------- */
  LA.statusbar = (S, showTargets = true) => `<div class="la-statusbar"><span class="grow">Ready · OSC bridge on 127.0.0.1${showTargets ? " · " + LA.esc(LA.targetSummary()) : ""}</span>
    <button class="la-btn mini ghost" data-act="copy-log">Copy</button>
    <button class="la-btn mini${S.console ? " on" : ""}" data-act="console">${LA.icon("term", 12)} ${S.console ? "Hide log" : "Console log"}</button></div>`;
  LA.consoleDrawer = (S, h = 120) => (S.console ? `<div class="la-console la-scroll" style="height:${h}px;flex:none">${LA.consoleLines()}</div>` : "");
  LA.diagPanel = () => `<span class="la-section-title">Bridge diagnostics</span>
    <p class="la-muted" style="margin:4px 0 10px">Bridge host: track 1 · “Live Actions Bridge”</p>
    <div class="la-quick"><button class="la-btn mini">Ping</button><button class="la-btn mini">Status</button><button class="la-btn mini">Sync</button><button class="la-btn mini">Reset</button></div>`;
  LA.settingsModal = (S) => (S.settings ? `<div class="la-scrim" data-act="close-settings"></div><div class="la-modal"><div class="la-modal-head"><b class="la-title" style="font-size:16px">Preferences</b><button class="la-iconbtn" data-act="close-settings" aria-label="Close">${LA.icon("x")}</button></div><div class="la-modal-body la-scroll">${LA.settingsBody()}</div></div>` : "");

  /* ---- mount: render loop + shared click routing ---------------------------- */
  LA.mount = (S, render, acts = {}) => {
    const app = document.getElementById("app");
    const draw = () => {
      const active = document.activeElement && document.activeElement.dataset ? document.activeElement.dataset.input : null;
      const caret = active ? document.activeElement.selectionStart : 0;
      const sc = [...app.querySelectorAll(".la-scroll")].map((n) => n.scrollTop);
      app.innerHTML = render();
      [...app.querySelectorAll(".la-scroll")].forEach((n, i) => (n.scrollTop = sc[i] || 0));
      if (active) { const n = app.querySelector(`[data-input="${active}"]`); if (n) { n.focus(); try { n.setSelectionRange(caret, caret); } catch (_) {} } }
      LA.paintSwatches();
    };
    const T = LA.state.targets;
    const builtin = {
      "toggle-track": (el) => { const id = +el.dataset.id; T.has(id) ? T.delete(id) : T.add(id); },
      all: () => LA.tracks.forEach((t) => T.add(t.id)),
      none: () => T.clear(),
      livesel: () => { T.clear(); T.add(2); },
      theme: (el) => LA.setTheme(el.dataset.slug),
      "toggle-themes": () => (LA.ui.themesOpen = !LA.ui.themesOpen),
      console: () => (S.console = !S.console),
      settings: () => (S.settings = true),
      "close-settings": () => (S.settings = false),
      "open-tool": (el) => (S.tool = el.dataset.id),
      "close-tool": () => (S.tool = null),
      "copy-log": () => {},
    };
    document.addEventListener("click", (ev) => {
      const prev = S.pop;
      if (!ev.target.closest(".la-pop")) S.pop = null;
      const el = ev.target.closest("[data-act]");
      if (el) { const f = acts[el.dataset.act] || builtin[el.dataset.act]; if (f) f(el, prev); }
      draw();
    });
    document.addEventListener("keydown", (ev) => {
      if ((ev.key === "Enter" || ev.key === " ") && ev.target.matches && ev.target.matches(".la-card,.la-row")) { ev.preventDefault(); ev.target.click(); }
      if (ev.key === "Escape" && (S.settings || S.pop)) { S.settings = false; S.pop = null; draw(); }
    });
    document.addEventListener("input", (ev) => { const k = ev.target.dataset && ev.target.dataset.input; if (k) { S[k] = ev.target.value; draw(); } });
    LA.mountChrome(S.layoutId);
    draw();
    (document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve()).then(() => document.body.setAttribute("data-ready", "1"));
  };

  LA.byId = (id) => LA.tools.find((t) => t.id === id);
  LA.filterTools = (S) => LA.tools.filter((t) => {
    const k = LA.scopeOf(t).key;
    if (S.filter && S.filter !== "all" && k !== S.filter) return false;
    const q = (S.q || "").toLowerCase();
    return !q || (t.name + " " + t.description).toLowerCase().includes(q);
  });
  LA.filterChips = (S) => [["all", "All"], ["tracks", "Selected tracks"], ["set", "Set-wide"], ["dialog", "Dialogs"]]
    .map(([k, l]) => `<button class="la-btn mini ghost${(S.filter || "all") === k ? " on" : ""}" data-act="filter" data-k="${k}">${l}</button>`).join("");

  /* swatches in Settings paint from the kit files themselves (read once, cached) */
  LA.paintSwatches = () => {
    document.querySelectorAll("[data-swatch]").forEach(async (i) => {
      const slug = i.dataset.swatch;
      LA._sw = LA._sw || {};
      if (!LA._sw[slug]) LA._sw[slug] = fetch(`themes/${slug}.css`).then((r) => r.text()).catch(() => "");
      const css = await LA._sw[slug];
      const g = (n) => (css.match(new RegExp(`--kit-${n}:\\s*([^;]+);`)) || [])[1];
      if (g("bg")) i.style.background = `linear-gradient(135deg, ${g("bg")} 0 50%, ${g("accent")} 50% 100%)`;
    });
  };
})();
