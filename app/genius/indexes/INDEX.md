# Producer Pal Genius — studio library index

Read **this file first**. Do not dump TRAINING DOCS, the Music/Audio database, or `A:\Plugin Documentation_Uninstallers` into context.

Genius is a **music-theory-aware producer**: Live + plugins + hardware, and two knowledge sources —
the **Music/Audio database** (`library_db_search`, real FTS5 search, structured citations — always the
first stop) and **TRAINING DOCS** (`library_read`/`library_search`, raw md/pdf — a **last resort**, used
only when `library_db_search` genuinely has nothing on the ask, checking `topic='?'` first. Named
third-party plugin manuals, the official Live PDF, and the Producer Pal Genius manual are the expected
common case, since none of those are in the database, but anything else the database misses is fair
game here too).

## How to use

1. Match the ask to **Decide first**, then call `library_db_search` with the topic it names.
2. If the ask is a named third-party plugin not in the database, or `library_db_search` (including
   `topic='?'`) came up empty, fall back to the **Third-party plugins** table and TRAINING DOCS
   (`library_read`/`library_search`) — the last resort, not the first stop.
3. Cite product + chapter/section/page (or theory book + topic) either way.
4. If Live work is requested: `live_connect`, then do what Live Actions `live_*` tools can do.
5. `ableton_live_helper` (in `library_db_search`) is a RAG Q&A corpus, not a manual — always carry its
   caveats (inspiration only, verify exact numbers, prefer live Live state) into the answer.

## Decide first

| Ask is about | `library_db_search` topic |
| --- | --- |
| Scales, keys, modes, chords, intervals, harmony, rhythm, form, “what notes” | `music_theory` |
| Arrangement, mix, genre, EDM, DJ, finishing, songwriting | `production_djing` |
| Oscillators, filters, ADSR, synthesis, frequency map | `sound_design` |
| Finger drumming, drum pads, drum MIDI, MPE | `drum_pads` |
| How an effect *works* (pitch shift, vocoder, BBD, phase vocoder), DSP, named effect specs | `audio_analysis` |
| Vocal/stem separation, f0 tracking, SNR | `audio_splitting` |
| Live how-to (Live 12, Note, Max for Live, LOM) | `ableton_training` |
| Launchkey MK4, Novation Components, SysEx | `novation` |
| Specific Max for Live device (ClipCombiner, DmmG, Duckling, SRM-DB002, Sfx, TreeTool) | `m4l_device_info` |
| Max for Live general (best practices, objects/API, troubleshooting, tutorials) | `m4l_general` |
| General production grab-bag (effects, gain staging, layering, mastering, plugin how-tos) not covered above | `music_production` |
| Surge / Surge XT synthesis, oscillators, manual | `surge` |
| Sonic Pi Ruby DSL, live coding, live loops, SuperCollider synths, algorithmic composition | `sonic_pi` |
| The Infinite Crate (Lyria RealTime VST), generative Lyria, Gemini API audio streaming, prompt DJing, stem isolation | `infinite_crate` |
| Ableton Live 12.3.6 LOM full class reference (properties/methods/enums/listeners/settability, 43 core classes) | `liveapi_lom` |
| Interactive composition, generative M4L, studio monitoring, genre frameworks (grab-bag) | `misc` |
| Setup/routing research (Voicemeeter, ASIO, VST2/3 hosting) not covered above | `new_research` or `research_results` |
| Producer-style Q&A, workflow inspiration, mix engineering, preset racks, or an Ableton community tool/Remote Script (AbletonOSC, PyLive, AbletonMCP, AbletonBridge, LiveRPyC, Cycling '74 Max objects, Max 9 LOM training, Vital synth lab — ~15 datasets total) | `ableton_god_producer`, `mixology_db`, `ableton_racks_labeled`, `abletonosc`, `pylive`, `ableton_mcp_extended`, `ableton_bridge`, `live_rpyc`, `ableton_api_stub`, `cycling74_max_reference`, `max9_lom_training`, `vital_synth_lab`, `live_remote_scripts`, `ableton_liveapi_tools`, `ableton_live_mcp_bschoepke` — or topic='?' |
| Named plugin/hardware manual, check the database first (Native Instruments, Ozone, Surge/Helm/Bass Station/Axxess, Oberheim, Klevgrand, M-Track/Dolby Atmos, Clipper M4L — ~8 datasets) before assuming TRAINING DOCS-only | `hw_native_instruments`, `hw_mixing_mastering`, `hw_synths_standalone`, `hw_oberheim_gforce`, `hw_klevgrand`, `hw_audio_interfaces`, `hw_m4l_clipper`, `hw_producer_pal_studio` — or topic='?' |
| Named plugin genuinely not in the database | **Third-party plugins** table (TRAINING DOCS) |
| Music software manuals (what to open / skip) | `User Manuals\INDEX.md` (TRAINING DOCS) |

## Pal capability (all third-party plugins)

| Pal can | Pal cannot |
| --- | --- |
| `listPlugins`; open a plugin window if it is already on a track; build tracks, returns, sends, **native** Live devices; **Live Actions Genius:** `live_inspect_plugin` / `live_read_device` / `live_update_device` on an already-present VST/AU (LOM-visible knobs only); write automation / clip envelopes (`live_set_clip_automation`, `live_add_shaped_automation`, and related tools); add a VST/AU, Max for Live device, or browser preset via `live_load_browser_item` **when the browser engine (LiveActionsRS) is online** — check the system prompt's status line | Run stem separation; claim a full plugin patch (wavetable/mod-matrix leftover state); add a VST/AU / M4L device / browser preset while the browser engine is offline |

**Question** → open the book, answer, cite it.  
**Directive** → open the book + Live chapters. Native half + Live-visible knobs on plugins already in the Set; write automation directly. Hand off stems, leftover plugin state, and insert only while the browser engine is offline.

Producer Pal + Genius how-to: `B:\Documents\TRAINING DOCS\User Manuals\Other Manuals\Producer Pal Genius User Manual.pdf`  
Official Pal site capture: `User Manuals\Other Manuals\producer-pal-ai-readable-guide.pdf`

**Genius Live API** is the toggle on the device **Main** tab (same flag as Setup → Direct Live API). Off by default. On exposes `ppal-live-api`.

---

## Live 12

Start with `library_db_search(topic="ableton_training", ...)` — full-text search across all 450 official
Ableton manuals (Live 12, Max for Live/LOM, Note, knowledgebase), not just the one Standard Manual PDF.

Full official PDF fallback (page-exact citation, TRAINING DOCS): `B:\Documents\TRAINING DOCS\Music Production\Ableton Training Docs\Ableton\live12-manual-en.pdf`

Native devices Pal can create: Live ch. **28** audio FX, **29** MIDI FX, **32** Max devices, **30** instruments (full PDF).

Example: “separate the vocal and put it on a return with Ozone-style limiting” → ch. 22 + 17 + 18 + Ozone 12 + Limiter in ch. 28.

---

## Third-party plugins

**Check `library_db_search` first** (see the Devices_Hardware row above) — Ozone, Massive X/Komplete Kontrol,
Surge, Helm, Bass Station, Axxess, Oberheim, Klevgrand, M-Track/Dolby Atmos, and Clipper are now real FTS5
datasets there, not just TRAINING DOCS PDFs. This table is the TRAINING DOCS fallback for everything else
Live actually sees on this PC (2026-07-31; Ozone Elements / Trash were **disabled**):  
`B:\Documents\TRAINING DOCS\Grok Build Research Results\Ableton-Live-12-Complete-Plugin-Hardware-Knowledge-Base.md`

| Aliases | Book |
| --- | --- |
| Ozone, Ozone 12, iZotope limiting | `User Manuals\Other Manuals\Ozone 12 user guide.pdf` |
| Massive X | `User Manuals\Other Manuals\Massive X Synth User Guide.pdf` |
| Helm | `User Manuals\Other Manuals\Helm User Manual.pdf` |
| Surge, Surge XT | `User Manuals\Other Manuals\Surge-XT-Manual.pdf` |
| Komplete Kontrol, NKS | `User Manuals\Other Manuals\KOMPLETE KONTROL 1.8 Manual.pdf` |
| Kontakt, Guitar Rig, Reaktor | inventory file (no standalone book in Other Manuals) |
| SPAN | `Music Production\plugin manuals_guides\Voxengo SPAN User Guide en.pdf` |
| Overtone GEQ | `Music Production\plugin manuals_guides\Voxengo Overtone GEQ User Guide en.pdf` |
| Voxengo Primary | `Music Production\plugin manuals_guides\Voxengo Primary User Guide en.pdf` |
| Wider, Polyverse Wider | `Music Production\plugin manuals_guides\Wider Manual.pdf` |
| Panagement | `Music Production\plugin manuals_guides\Panagement 2 User's Guide.pdf` |
| Graillon | `Music Production\plugin manuals_guides\Graillon 3 User's Guide.pdf` |
| Inner Pitch | `Music Production\plugin manuals_guides\Inner Pitch 2 User's Guide.pdf` |
| Vital | `Music Production\plugin manuals_guides\Vital Manual_Version 1.pdf` |
| Filterstep | `Music Production\plugin manuals_guides\Filterstep_Basic_Manual.pdf` |
| Ribs | `Music Production\plugin manuals_guides\Ribs manual v1.2.3.pdf` |
| SUPER.7, CFA | `Music Production\plugin manuals_guides\CFA-Sound SUPER.7 v1.1 Manual.pdf` |
| HZ Delay | `Music Production\plugin manuals_guides\HZ Delay Manual.pdf` |
| HZ Multiplier | `Music Production\plugin manuals_guides\HZ Multiplier Manual.pdf` |
| La Voz Cantante | `Music Production\plugin manuals_guides\La Voz Cantante 6.4 User Manual.pdf` |
| Synsonic BD-909 | `Music Production\plugin manuals_guides\Synsonic BD-909_User Manual_pluginboutique.pdf` |
| tonespace | `Music Production\plugin manuals_guides\tonespace_user_guide.pdf` |
| Audible Planets | `Music Production\plugin manuals_guides\Audible Planets Guide.pdf` |
| BC Phaser | `Music Production\plugin manuals_guides\BC Phaser 3 VST(Stereo) data manual.pdf` |
| Evouyn, Noisebud | `Music Production\plugin manuals_guides\Noisebud Evouyn User Manual.pdf` |
| Poly 2106 | `Music Production\plugin manuals_guides\Poly 2106 Operation Manual.pdf` |
| Prodigious | `Music Production\plugin manuals_guides\Prodigious Synthesizer Operation Manual.pdf` |
| VST Speek | `Music Production\plugin manuals_guides\VST Speek documentation.pdf` |
| EXD80, EXD-80 | `Music Production\plugin manuals_guides\EXD80 User Guide.pdf` |
| 1984 piano | `Music Production\plugin manuals_guides\1984_USER_MANUAL.pdf` |
| Axxess | `User Manuals\Other Manuals\Axxess User Manual.pdf` |
| Bass Station, Bass Station II | `User Manuals\Other Manuals\Bass Station Manual Download.pdf` + Launchkey BSII custom-mode PDFs |
| Oberheim OB-E | `User Manuals\Other Manuals\Oberheim OB-E User Manual.pdf` |
| Oberheim SEM | `User Manuals\Other Manuals\Oberheim SEM User Manual.pdf` |
| Phasis | `User Manuals\Other Manuals\Phasis Manual.pdf` |
| Replika | `User Manuals\Other Manuals\Replika XT Manual.pdf` |
| Røverb, Roverb | `User Manuals\Other Manuals\Røverb User Manual.pdf` |
| Schema Light | `User Manuals\Other Manuals\Schema Light User Manual.pdf` |
| Slammer | `User Manuals\Other Manuals\Slammer User Manual.pdf` |
| Tape Suite | `User Manuals\Other Manuals\Tape Suite User Manual.pdf` |
| TRK-01 | `User Manuals\Other Manuals\TRK-01 User Manual.pdf` |
| LUXE | `User Manuals\Other Manuals\LUXE User Manual.pdf` |
| FEEL IT | `User Manuals\Other Manuals\FEEL IT User Manual.pdf` |
| Clipper | `User Manuals\Other Manuals\Clipper manual.pdf` |
| MOD PACK | `User Manuals\Other Manuals\EFFECTS SERIES – MOD PACK User Manual.pdf` |
| Komplete Utopia | `User Manuals\Other Manuals\Komplete Utopia User Manual.pdf` |
| Plugin chart (what I own) | `Music Production\plugin manuals_guides\Plugins I have_Chart and Guide.pdf` |
| 36db (transient shaper/saturator) | `Music Production\plugin manuals_guides\36db-transient-shaper-saturator-device-content.pdf` |
| Dub Assistant | `Music Production\plugin manuals_guides\Dub-Assistant-USER-GUIDE.pdf` |
| Flowfal | `Music Production\plugin manuals_guides\flowfal-getstarted.pdf` |
| Live Scratcher | `Music Production\plugin manuals_guides\live-scratcher-1.0.5-manual.pdf` |
| Maxhead, Aqusmatiq | `Music Production\plugin manuals_guides\Maxhead-Manual-1.0-Aqusmatiq.pdf` |
| Meyer Devices MIDI Tools | `Music Production\plugin manuals_guides\Meyer-Devices-MIDI-Tools-Manual.pdf` |
| Pong Deluxe | `Music Production\plugin manuals_guides\PongDeluxe_Manual.pdf` |
| SwingMaster | `Music Production\plugin manuals_guides\SwingMaster.pdf` |

A: install-folder PDFs (fallback): `A:\Plugin Documentation_Uninstallers\` — same titles, mixed with uninstallers.

---

## Ableton stack (everything else used in Live)

### Launchkey MK4 61

Start with `library_db_search(topic="novation", ...)` (Components custom modes, SysEx specs, Bass Station II).  
Official PDF fallback (TRAINING DOCS): `Music Production\Novation\launchkey_Guide.pdf`

### Ableton Note

`Music Production\Ableton Training Docs\Note\` — manual, Capture, samples, presets, Link, sharing, screen recording.

### Max for Live + Producer Pal

`Music Production\Ableton Training Docs\Max for Live\` — Max9 User Guide, LOM, JS API, Node for Max, production guidelines.  
Pal + Genius how-to: `User Manuals\Other Manuals\Producer Pal Genius User Manual.pdf`  
Official Pal site capture: `User Manuals\Other Manuals\producer-pal-ai-readable-guide.pdf`  
Live ch. 31–32.

### Link / Cloud / sync

Live ch. 36. Split articles: `Music Production\Ableton Training Docs\Split Versions\Link and Cloud Knowledgebase - Ableton.com Split\`

### Push / Move

Live ch. 34–35. ASIO entries exist on this PC.

### Novation around Live

`Music Production\Novation\` — `STACKS - Browser.pdf` · `STACKS - Sound Editor.pdf` · `GLAZE - Snapshots.pdf` · `novation-play-guide.pdf` · Bass Station (Other Manuals + Launchkey custom modes).

### Session I/O

Voicemeeter Banana + Launchkey ports: inventory file above.  
M-Track Duo: `User Manuals\Other Manuals\M-Track Duo - User Guide - v1.5.pdf`  
Dolby Atmos: `User Manuals\Other Manuals\Dolby Atmos for Win Config Guide.pdf`  
Windows MIDI Services: `User Manuals\Windows\MIDI Services\`

### Library / packs / skins

Packs: `A:\Samples_Packs`. Live ch. 4–5.  
Skins: `Music Production\Ableton Training Docs\Ableton\Guide for Creating Ableton Live Skins.pdf`

### Remote / shortcuts

Live ch. 33, 40, 41.

---

## Sound design / mix coaches

Child index: `Music Production\Sound Design\INDEX.md`  
PML compression 1–5, synthesis 1–5, frequency cheat sheet, beginner knowledgebase.  
Ozone 12 + Live ch. 18.

---

## Music theory / production / DJ

These are first-class Genius books, not leftovers.

| Child index | Use for |
| --- | --- |
| `Music Production\Music Theory\INDEX.md` | keys, scales, modes, chords, intervals, rhythm, form |
| `Music Production\Production_DJing\INDEX.md` | arrangement, mix, genre, EDM, DJ, finishing |
| `Music Production\Drum Pads\INDEX.md` | finger drumming, drum MIDI, MPE |
| `Music Production\Audio Analysis_Editing\INDEX.md` | how effects work |
| `Music Production\INDEX.md` | hub for the whole Music Production tree |

Syllabus (teach-in-order): `Music Production\Course Syllabus - Complete Piano & Music Theory.md`  
Launchkey theory course: `Music Production\more knowledgebase sources\Music_Theory_Beginner_Launchkey_MK4.md`

Example: “8-bar D Dorian progression in a MIDI clip” → Music Theory (Dorian + progressions) + Live ch. 10 / 15. Pal writes the clip.

---

## User Manuals (music / music software only)

Child index: `User Manuals\INDEX.md`

**In:** `Music Production\Ableton Training Docs\`, `Music Production\Novation\`, `Other Manuals\`, `Windows\MIDI Services\`, `AI Model_API Docs\Google\google-flow-music-guide.pdf`.  
**Out for a music ask:** the rest of `AI Model_API Docs\` (moved out of the old User Manuals AI folder, which no longer exists) and `User Manuals\Windows\`.

---

## Windows (non-music)

`User Manuals\Windows\` — sandbox, PowerShell, client docs. Not first for a music ask. MIDI Services is in scope (see User Manuals index).

---

## AI APIs

`TRAINING DOCS\AI Model_API Docs\` — not first for a music ask. Flow music guide is listed on the User Manuals index.

---

## NotebookLM exports

Use when the official PDF is missing or the extract is easier to search.

`NotebookLMs - Source Exports\Ableton Live 12\`  
`NotebookLMs - Source Exports\Launchkey\`  
`NotebookLMs - Source Exports\Music Production\`  
`NotebookLMs - Source Exports\Music Theory\`  
Also: AI Models, Applications, Astrology, LLM Creativity Training — only if the ask is actually those topics.

---

## Roots

- `B:\Documents\TRAINING DOCS`
- `A:\Plugin Documentation_Uninstallers` (manuals only)
- `User Manuals\Other Manuals\producer-pal-ai-readable-guide.pdf`
