# Producer Pal Genius

Pair official [Producer Pal](https://producer-pal.org) with the local studio library so Grok opens the right Live chapter, plugin book, Launchkey guide, or music-theory / production book before it acts in Ableton.

This is **not** official Producer Pal. Pal itself stays GPL and is not shipped here. This repo is the Grok skill, agent, library indexes, and the Main-tab **Genius Live API** device patch.

Companion: [producer-pal-local](https://github.com/mkomorny/producer-pal-local) (Open Chat UI → local Grok / Claude).

## What you get

| Piece | Role |
| --- | --- |
| `skills/producer-pal-genius/SKILL.md` | Grok skill (`/producer-pal-genius`) — open `INDEX.md`, then 1–3 books, then Pal |
| `agents/producer-pal-genius.md` | Grok agent for Genius sessions |
| `indexes/INDEX.md` | Master map of this studio’s manuals + theory/production routing |
| `indexes/live-12/INDEX.md` | Live 12 chapter → Pal can/cannot |
| `indexes/launchkey-mk4-61/INDEX.md` | Launchkey MK4 61 chapters |
| `indexes/music-production/INDEX.md` | Hub for the Music Production tree |
| `indexes/music-theory/INDEX.md` | Scales, chords, modes, keys, rhythm |
| `indexes/production-djing/INDEX.md` | Arrangement, mix, genre, DJ |
| `indexes/sound-design/INDEX.md` | Synthesis, compression, frequency map |
| `indexes/drum-course/INDEX.md` | Finger drumming, drum MIDI, MPE |
| `indexes/audio-analysis/INDEX.md` | How effects work (DSP) |
| `indexes/user-manuals/INDEX.md` | Music/music-software manuals only |
| `scripts/patch-genius-live-api.py` | Adds a **Genius Live API** toggle on the device Main tab |
| `scripts/build-user-manual.py` | Rebuilds the studio how-to PDF |
| `docs/Producer Pal Genius User Manual.pdf` | How Pal + Genius + the library work on this PC |

The indexes point at manuals on this machine (`B:\Documents\TRAINING DOCS`, `A:\Plugin Documentation_Uninstallers`). They do not include the PDFs.

## Install on this PC

Copy the skill and agent into Grok:

```powershell
Copy-Item -Recurse .\skills\producer-pal-genius $env:USERPROFILE\.grok\skills\producer-pal-genius
Copy-Item .\agents\producer-pal-genius.md $env:USERPROFILE\.grok\agents\producer-pal-genius.md
```

Copy the indexes next to the books (paths the skill already names):

```powershell
Copy-Item .\indexes\INDEX.md "B:\Documents\TRAINING DOCS\INDEX.md"
Copy-Item .\indexes\live-12\INDEX.md "B:\Documents\TRAINING DOCS\User Manuals\Ableton\Ableton Live 12 Standard Manual\INDEX.md"
New-Item -ItemType Directory -Force -Path "B:\Documents\TRAINING DOCS\User Manuals\Novation\Novation LaunchKey 61" | Out-Null
Copy-Item .\indexes\launchkey-mk4-61\INDEX.md "B:\Documents\TRAINING DOCS\User Manuals\Novation\INDEX.md"
Copy-Item .\indexes\launchkey-mk4-61\INDEX.md "B:\Documents\TRAINING DOCS\User Manuals\Novation\Novation LaunchKey 61\INDEX.md"
Copy-Item .\indexes\music-production\INDEX.md "B:\Documents\TRAINING DOCS\Music Production\INDEX.md"
Copy-Item .\indexes\music-theory\INDEX.md "B:\Documents\TRAINING DOCS\Music Production\Music Theory\INDEX.md"
Copy-Item .\indexes\production-djing\INDEX.md "B:\Documents\TRAINING DOCS\Music Production\Production_DJing\INDEX.md"
Copy-Item .\indexes\sound-design\INDEX.md "B:\Documents\TRAINING DOCS\Music Production\Sound Design\INDEX.md"
Copy-Item .\indexes\drum-course\INDEX.md "B:\Documents\TRAINING DOCS\Music Production\Drum course\INDEX.md"
Copy-Item .\indexes\audio-analysis\INDEX.md "B:\Documents\TRAINING DOCS\Music Production\Audio Analysis_Editing\INDEX.md"
Copy-Item .\indexes\user-manuals\INDEX.md "B:\Documents\TRAINING DOCS\User Manuals\INDEX.md"
```

Add the Main-tab toggle (after official Pal is installed):

```powershell
python .\scripts\patch-genius-live-api.py
```

Then in Live: remove Producer Pal from the track and drop it on again. **Genius Live API** sits on the Main tab. It is the same flag as Setup → Direct Live API (`ppal-live-api`). Off by default.

After a Pal update overwrites the device, run the patch script again.

## How Genius answers

1. Connect Pal if the Live Set is involved.
2. Read `B:\Documents\TRAINING DOCS\INDEX.md` and follow **Decide first**.
3. Open only the matching book(s). Cite product + chapter (or theory book + topic).
4. Pal does native Live work — including MIDI in a named key/scale. VST instantiate, unmapped VST knobs, stem split, and automation stay a cited handoff unless **Genius Live API** is on.

The library is why Genius beats Pal alone: Pal is the hands, the books are the theory and the real knob names. Rebuild the how-to with `python .\scripts\build-user-manual.py`.

## License

MIT for this repository. Official Producer Pal remains GPL-3.0 and is not included.
