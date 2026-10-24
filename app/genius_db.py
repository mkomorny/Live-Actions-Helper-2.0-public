"""Structured-database search for Genius: B:\\DATABASES\\Music_Audio.

Each topic folder under the DB root ships its own SQLite FTS5 database plus a
`search.py` CLI/module (built outside this repo, by the dataset-builder /
ai-database-browser tooling). We shell out to that CLI with --json rather than
re-implementing the FTS5 query logic here, so a schema change on the database
side doesn't require a matching code change here.

Folder values may be multi-segment relative paths (e.g.
"Ableton_Live/Live_Helper/mixology_db") -- the DB root was reorganized into
nested category folders in the 2026-09-18 rebuild (previously flat, one level
below the root). pathlib joins a "/"-containing string as multiple segments,
so this needs no special handling elsewhere.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

DEFAULT_DB_ROOT = Path(r"B:\DATABASES\Music_Audio")

# key -> (folder path under the DB root, one-line description shown to the model)
TOPICS: dict[str, tuple[str, str]] = {
    # -- Ableton_Live --
    "ableton_training": ("Ableton_Live/Ableton Training", "450 official Ableton Live 12 manuals, Max for Live (LOM), Note, knowledgebase guides"),
    "liveapi": ("Ableton_Live/LiveAPI", "Ableton Live 12.3.6 Python API specification, Boost.Python C++ methods, properties, signatures, and device parameters"),
    "liveapi_lom": ("Ableton_Live/LiveAPI_LOM", "Ableton Live 12.3.6 Live Object Model (LOM) full class reference -- properties, methods, enums, listeners, settability -- for all 43 core classes (Song, Track, Clip, Device, RackDevice, etc.) via runtime introspection"),
    # -- Ableton_Live/Live_Helper (split from the old single "Ableton Live Helper" RAG corpus into 15 real FTS5 datasets in the 2026-09-18 rebuild) --
    "ableton_god_producer": ("Ableton_Live/Live_Helper/ableton_god_producer_dataset", "15k 'god producer' beat-making Q&A dataset (27 modular chapters), direct device/note action blueprints"),
    "ableton_racks_labeled": ("Ableton_Live/Live_Helper/ableton-racks-labeled", "134 labeled Ableton Live XML preset racks with macro controls (135 modular chapters)"),
    "vital_synth_lab": ("Ableton_Live/Live_Helper/vital_synth_headless_lab", "Vital synth headless lab: JSON schema, offline WAV rendering, wavetable extraction, native Drift/Wavetable translation"),
    "mixology_db": ("Ableton_Live/Live_Helper/mixology_db", "Mix engineering DB: 90 multitrack mixes, 2,411 fader/pan ratios, EQ Eight carving curves, listening-critique rules"),
    "ableton_liveapi_tools": ("Ableton_Live/Live_Helper/ableton_liveapi_tools", "Python Remote Script/LiveAPI tooling: 220 cataloged tools, M4L dynamic parameter discovery, CV Tools recipes"),
    "ableton_mcp_extended": ("Ableton_Live/Live_Helper/ableton_mcp_extended", "AbletonMCP v2.0.0+ (jpoindexter): 257 commands, retrospective MIDI capture, arrangement locators, Drum Rack pad muting, algorithmic music generation"),
    "ableton_live_mcp_bschoepke": ("Ableton_Live/Live_Helper/ableton_live_mcp_bschoepke", "bschoepke/ableton-live-mcp: 562MB local Sound Similarity search, arbitrary live_exec/live_eval, Session-to-Arrangement duplication, clip automation curves"),
    "ableton_bridge": ("Ableton_Live/Live_Helper/ableton_bridge_hidingwill", "hidingwill/AbletonBridge: 359 tools, ASCII grid tab compiler, device snapshot LERP morphing, Euclidean/polyrhythm generators, sidechain routing"),
    "abletonosc": ("Ableton_Live/Live_Helper/abletonosc_ideoforms", "ideoforms/AbletonOSC: pure-Python OSC Remote Script, full session JSON dump, bulk track queries, hardware MIDI CC mapping"),
    "pylive": ("Ableton_Live/Live_Helper/pylive_ideoforms", "ideoforms/pylive: OOP Python client SDK, ASCII session tree dump, semantic track lookup, stochastic clip walker, tempo modulation"),
    "live_rpyc": ("Ableton_Live/Live_Helper/live_rpyc_lucianoiam", "lucianoiam/live_rpyc: RPyC direct LOM memory proxy, cross-process event listeners, recursive rack/chain reflection"),
    "ableton_api_stub": ("Ableton_Live/Live_Helper/ableton_api_stub_cylab", "cylab/AbletonLive-API-Stub: pure-Python stub classes, static pre-execution LOM call validation, enum maps (WarpMode, Quantization, DeviceType)"),
    "max9_lom_training": ("Ableton_Live/Live_Helper/ableton_ai_max9_lom_training", "Max 9 LOM + Ableton AI training data: Live 11->12 diff (1,427 added members), Meld/Roar/Drift classes, abl.*/live.* M4L objects"),
    "cycling74_max_reference": ("Ableton_Live/Live_Helper/cycling74_max_reference", "Cycling '74 Max 1,805-object reference: Core/MSP/MC/Gen~/Jitter, abl.*/live.* M4L objects"),
    "live_remote_scripts": ("Ableton_Live/Live_Helper/live_12_remote_scripts_reference", "Live 12 MIDI Remote Scripts reference: Launchkey MK4 architecture/Sysex, Push/Move profiles, 148 controller layouts, LOM hierarchy map"),
    # -- Audio_DSP_Separation --
    "audio_analysis": ("Audio_DSP_Separation/AI Audio Analysis and Editing", "DSP guides, named-effect specs (Bitcrusher, Reverb, Chorus, EQ), phase vocoders, filter design"),
    "audio_splitting": ("Audio_DSP_Separation/Audio Splitting", "Voice separation studies, f0 accuracy benchmarks, SNR sweeps, vibrato modeling"),
    # -- Controllers_Hardware --
    "drum_pads": ("Controllers_Hardware/Drum Pads", "Finger drumming, split-finger technique, MPE, Launchkey pad expression"),
    "novation": ("Controllers_Hardware/Novation", "Launchkey MK4 guides, Components custom modes, SysEx specs, Bass Station II"),
    # -- Controllers_Hardware/Devices_Hardware (new in the 2026-09-18 rebuild: third-party plugin/hardware manuals, 8 family datasets) --
    "hw_native_instruments": ("Controllers_Hardware/Devices_Hardware/Native_Instruments", "Komplete Kontrol, Massive X, Feel It, Utopia, Mod Pack, Phasis, Replika XT, Schema Light, TRK-01 manuals"),
    "hw_producer_pal_studio": ("Controllers_Hardware/Devices_Hardware/Producer_Pal_Studio", "Producer Pal Genius manual, Producer Pal AI-readable guide, Flova AI"),
    "hw_synths_standalone": ("Controllers_Hardware/Devices_Hardware/Synths_Standalone", "Axxess, Novation Bass Station, Helm, Surge XT manuals"),
    "hw_mixing_mastering": ("Controllers_Hardware/Devices_Hardware/Mixing_Mastering", "iZotope Ozone 12, UVI Tape Suite manuals"),
    "hw_oberheim_gforce": ("Controllers_Hardware/Devices_Hardware/Oberheim_GForce", "Oberheim OB-E, Oberheim SEM manuals"),
    "hw_audio_interfaces": ("Controllers_Hardware/Devices_Hardware/Hardware_Audio", "M-Audio M-Track Duo, Dolby Atmos for Windows manuals"),
    "hw_klevgrand": ("Controllers_Hardware/Devices_Hardware/Klevgrand", "Klevgrand LUXE, Røverb, Slammer manuals"),
    "hw_m4l_clipper": ("Controllers_Hardware/Devices_Hardware/Max_for_Live", "Clipper M4L hard-clipper manual"),
    # -- Live_Coding --
    "sonic_pi": ("Live_Coding/Sonic Pi", "Sonic Pi Ruby music DSL, SuperCollider synths, live loops, algorithmic composition, studio FX, MIDI & OSC bridging, MagPi masterclasses"),
    # -- Max_for_Live --
    "m4l_device_info": ("Max_for_Live/M4L Device Info", "Specialized Max for Live devices (ClipCombiner, DmmG, Duckling, SRM-DB002, Sfx, TreeTool), M4L state persistence"),
    "m4l_general": ("Max_for_Live/M4L", "Max for Live best practices, objects/API, troubleshooting, and tutorials/guides (26 docs) -- separate from the m4l_device_info per-device dataset"),
    # -- Music_Theory --
    "music_theory": ("Music_Theory/Music Theory", "Scales, modes, chords, intervals, circle of fifths, 1,492-scale catalog"),
    # -- Production_Mixing --
    "misc": ("Production_Mixing/Misc", "Interactive composition (Ableton/M4L), EDM sound design, frequency balance, studio monitoring, genre frameworks"),
    "music_production": ("Production_Mixing/Music Production", "Large general production knowledgebase (1,776 docs): audio effects, bass music, EDM production, gain staging/modulation/automation, DSP research, dubstep/D&B, sound-design coursework, DJing/EDM guides, drum pads, mastering, layering, plugin manuals"),
    "production_djing": ("Production_Mixing/Production_DJing", "EDM genre guides (House/Techno/Trance/Dubstep/D&B), mixing/mastering, arrangement, DJ performance"),
    # -- Research_Notes --
    "new_research": ("Research_Notes/New Research", "Ableton Live 12 setup, Launchkey MK4, Voicemeeter Banana, VST2/3, beginner sound design, piano technique"),
    "research_results": ("Research_Notes/Research Results", "Grok build research: Ableton Live 12 setup, Launchkey MK4, Voicemeeter Banana, VST2/3, piano technique"),
    # -- Sound_Design_Synthesis --
    "sound_design": ("Sound_Design_Synthesis/Sound Design", "Subtractive synthesis, ADSR, compression, frequency allocation, Surge XT, Live native sound design"),
    "surge": ("Sound_Design_Synthesis/Surge", "Surge XT synthesizer: synthesis, oscillator types, modulation, and the full manual reference"),
    "infinite_crate": ("Sound_Design_Synthesis/Infinite Crate", "The Infinite Crate (Lyria RealTime VST): generative Lyria RealTime foundation model, Gemini API audio streaming, multi-prompt harmonic mixer, Ableton Live resampling routing, jam accompaniment, prompt DJing, stem isolation"),
}

# Not real topics -- on-disk pointers to other topic keys.
TOPIC_ALIASES = {
    "m4l": "m4l_device_info",
    # The old flat "Ableton Live Helper" RAG corpus was split into the 15
    # ableton_*/pylive/live_rpyc/abletonosc/cycling74/vital/mixology topics
    # above in the 2026-09-18 rebuild -- point anyone still asking for the
    # old single topic key at the best general-purpose replacement.
    "ableton_live_helper": "ableton_god_producer",
}


def db_root(settings: dict[str, Any] | None = None) -> Path:
    settings = settings or {}
    return Path(str(settings.get("music_db_dir") or DEFAULT_DB_ROOT))


def resolve_topic(key: str) -> tuple[str, str] | None:
    key = (key or "").strip().lower().replace(" ", "_").replace("-", "_")
    key = TOPIC_ALIASES.get(key, key)
    return TOPICS.get(key)


def list_topics() -> str:
    lines = ["Available library_db_search topics:"]
    for key, (_folder, desc) in TOPICS.items():
        lines.append(f"  - {key}: {desc}")
    return "\n".join(lines)


def db_search(settings: dict[str, Any], topic: str, query: str, limit: int = 5) -> str:
    resolved = resolve_topic(topic)
    if not resolved:
        return "Unknown topic %r.\n\n%s" % (topic, list_topics())
    folder_name, _desc = resolved

    root = db_root(settings)
    script = root / folder_name / "search.py"
    if not script.is_file():
        return "Database search script not found: %s (is the DB root set correctly in Settings?)" % script

    try:
        proc = subprocess.run(
            [sys.executable, str(script), query, "--limit", str(max(1, min(limit, 10))), "--json"],
            cwd=str(script.parent),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
        )
    except Exception as exc:
        return "ERROR running %s: %s" % (script, exc)

    if proc.returncode != 0:
        return "ERROR from %s (exit %d): %s" % (script.name, proc.returncode, (proc.stderr or "").strip()[:2000])

    try:
        results = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError:
        return (proc.stdout or "").strip()[:4000] or "No output from %s." % script.name

    if not results:
        return "No matches for %r in %s." % (query, folder_name)

    lines = ["%d match(es) in %s for %r:" % (len(results), folder_name, query)]
    for r in results:
        if not isinstance(r, dict):
            # A handful of search.py builds emit a bare string (or other
            # non-object row) instead of the usual {doc_title, ...} shape --
            # surface it rather than crashing the whole response.
            lines.append("\n%s" % str(r)[:1200])
            continue
        title = r.get("doc_title") or r.get("title") or "?"
        section = r.get("section_title") or r.get("subcategory") or r.get("category") or ""
        page = r.get("page_number")
        cite = title + (f" — {section}" if section else "") + (f" (p.{page})" if page else "")
        # Field name drifts by dataset build: older topics use "content", newer
        # ones (built since the dataset-builder tooling changed) use "snippet"
        # with >>> highlighted <<< match markers. Without this fallback, every
        # "snippet"-only dataset (Misc, M4L, Music Production, Surge, and
        # LiveAPI's non-"content" rows) silently rendered an empty citation body.
        content = str(r.get("content") or r.get("text") or r.get("snippet") or "").strip()
        if len(content) > 1200:
            content = content[:1200] + "…"
        lines.append("\n[%s]\n%s" % (cite, content))
    return "\n".join(lines)
