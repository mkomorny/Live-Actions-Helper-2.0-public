"""Regenerates the two generated inputs of the redesign round.

    shared/data.js        <- the app's real tools/*/tool.json manifests (not fixtures)
    themes/<slug>.css     <- the design kit's own tokens.css, verbatim, plus a Google
                             Fonts import and a short "adapter" block (status colours
                             and a few character tokens the kits do not define)

Run from anywhere:  python build_round.py
"""

from __future__ import annotations

import json
import re
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROUND = HERE.parent
REPO = ROUND.parent.parent
KITS = Path(r"B:\Documents\Claude Data\Design Kits\Design_Templates")

# slug -> (label, adapter). Adapter = the tokens a kit does not define but the app
# needs: semantic status colours and a few "character" switches. Everything else
# (palette, fonts, radius, shadow, motion) comes straight from the kit's tokens.css.
THEMES: dict[str, tuple[str, dict[str, str]]] = {
    "theatre-lighting-plot": ("Theatre Lighting Plot", {
        "ok": "#4fbf8a", "warn": "#f2b872", "err": "#d8232a",
        "label-case": "uppercase", "label-track": ".14em", "heading-scale": "1.25"}),
    "studio-patchbay": ("Studio Patchbay", {
        "ok": "#6fbf73", "warn": "#f2c14e", "err": "#d6503c",
        "label-case": "uppercase", "label-track": ".12em", "heading-scale": "1.2"}),
    "risograph-art-studio": ("Riso Art Studio", {
        "ok": "#1f9d55", "warn": "#d99100", "err": "#d62839",
        "border-w": "2px", "label-case": "uppercase", "label-track": ".08em"}),
    "max-msp-patcher": ("Max/MSP Patcher", {
        "ok": "#2f9e44", "warn": "#f1c400", "err": "#c8321e",
        "border-w": "1px", "label-case": "none", "label-track": "0"}),
    "cyber-neon-pink": ("Cyber Neon Pink", {
        "ok": "#34d399", "warn": "#fbbf24", "err": "#f87171",
        "label-case": "uppercase", "label-track": ".1em"}),
    "charcoal-lime-pastel-cards": ("Charcoal Lime Pastel", {
        "ok": "var(--kit-success)", "warn": "var(--kit-warning)", "err": "var(--kit-danger)",
        "label-case": "uppercase", "label-track": ".08em"}),
    "charcoal-amber-capsule": ("Charcoal Amber Pastel", {
        "ok": "var(--kit-success)", "warn": "var(--kit-warning)", "err": "var(--kit-danger)",
        "label-case": "uppercase", "label-track": ".08em"}),
    "broadcast-on-air": ("Broadcast On Air", {
        "ok": "var(--kit-accent-alt)", "warn": "var(--kit-warn)", "err": "var(--kit-accent)",
        "label-case": "uppercase", "label-track": ".14em", "heading-scale": "1.2"}),
    "aurora-borealis-geomagnetic": ("Aurora Borealis", {
        "ok": "var(--kit-accent)", "warn": "#fbbf24", "err": "var(--kit-warn)",
        "label-case": "uppercase", "label-track": ".1em"}),
    "amethyst-dusk": ("Amethyst Dusk", {
        "ok": "#34d399", "warn": "#fbbf24", "err": "#f87171",
        "label-case": "uppercase", "label-track": ".08em"}),
    "acetate-dubplate": ("Acetate Dubplate", {
        "ok": "#7dae5f", "warn": "#d9a441", "err": "var(--kit-warn)",
        "label-case": "uppercase", "label-track": ".1em", "heading-scale": ".95"}),
}

# Families whose Google Fonts CSS2 request must not ask for a bold weight.
SINGLE_WEIGHT = {"Alfa Slab One"}


def families(css: str) -> list[str]:
    seen: list[str] = []
    for m in re.finditer(r"--kit-font-[a-z]+:\s*([^;]+);", css):
        first = m.group(1).split(",")[0].strip().strip("'\"")
        if first and first not in seen and first.lower() not in {"system-ui", "sans-serif", "georgia"}:
            seen.append(first)
    return seen


def fonts_import(css: str) -> str:
    parts = []
    for fam in families(css):
        q = urllib.parse.quote_plus(fam)
        parts.append(f"family={q}" if fam in SINGLE_WEIGHT else f"family={q}:wght@400;700")
    if not parts:
        return ""
    return "@import url('https://fonts.googleapis.com/css2?" + "&".join(parts) + "&display=swap');\n"


def build_theme(slug: str, label: str, adapter: dict[str, str]) -> None:
    src = (KITS / slug / "tokens.css").read_text(encoding="utf-8")
    lines = [f"{fonts_import(src)}/* Theme: {label}  --  kit '{slug}'.",
             "   Section 1 is the kit's tokens.css, verbatim. Section 2 is the adapter. */",
             "", "/* ---- 1. kit tokens.css (verbatim) ---- */", src.strip(), "",
             "/* ---- 2. adapter: what the app needs that the kit does not define ---- */",
             ":root {"]
    for k, v in adapter.items():
        lines.append(f"  --ad-{k}: {v};")
    lines.append("}\n")
    (ROUND / "themes" / f"{slug}.css").write_text("\n".join(lines), encoding="utf-8")


def build_data() -> None:
    tools = []
    for manifest in sorted((REPO / "tools").glob("*/tool.json")):
        d = json.loads(manifest.read_text(encoding="utf-8"))
        tools.append({
            "id": d["id"], "name": d.get("name", d["id"]), "description": d.get("description", ""),
            "accent": d.get("accent", ""), "scope": d.get("scope", "track"),
            "ui": d.get("ui", ""), "runtime": d.get("runtime", ""),
            "fields": [{k: f.get(k) for k in ("id", "label", "type", "default", "hint", "options")}
                       for f in d.get("fields", [])][:8],
            "fieldCount": len(d.get("fields", [])),
        })
    def tok(slug: str, name: str) -> str:
        m = re.search(rf"--kit-{name}:\s*([^;]+);", (KITS / slug / "tokens.css").read_text(encoding="utf-8"))
        return m.group(1).strip() if m else ""

    meta = [{"slug": s, "label": lab, "bg": tok(s, "bg"), "surface": tok(s, "surface"), "accent": tok(s, "accent")} for s, (lab, _a) in THEMES.items()]
    payload = {"tools": tools, "themes": meta}
    (ROUND / "shared" / "data.js").write_text(
        "/* GENERATED by tools/build_round.py from the tool.json manifests -- do not edit. */\n"
        "window.LA_REAL = " + json.dumps(payload, indent=1, ensure_ascii=False) + ";\n",
        encoding="utf-8")
    print(f"data.js: {len(tools)} real tools")


if __name__ == "__main__":
    for slug, (label, adapter) in THEMES.items():
        build_theme(slug, label, adapter)
    print(f"themes: {len(THEMES)} written")
    build_data()
