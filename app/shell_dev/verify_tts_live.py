"""The ONE real Cartesia call: proves a saved Cartesia profile produces a real WAV through the app's own pipeline.

    python -m shell_dev.verify_tts_live [--profile NAME] [--text "..."] [--keep]

Reads the profile from your real settings.json (Preferences -> Audio tools -> TTS profiles), never prints the key,
sends ONE short phrase (default 24 characters, roughly 24 Cartesia credits by the README's estimate) through
tts_vocal.run(), then checks the file: RIFF/WAVE header, 48 kHz mono 24-bit, a non-zero duration, and audible samples
(not silence). The WAV goes to a temp folder that is deleted afterwards unless --keep. Exit 0 = the live call worked.

Refuses to run (exit 2, sends nothing) if there is no Cartesia profile.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import struct
import sys
import tempfile
import wave
from pathlib import Path

APP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP))
import settings_store   # noqa: E402
import tts_vocal        # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="", help="profile name (default: the first Cartesia profile)")
    ap.add_argument("--text", default="Testing one, two, three.")
    ap.add_argument("--keep", action="store_true", help="keep the generated WAV and print its path")
    args = ap.parse_args()

    settings = settings_store.load_settings()
    profiles = [p for p in (settings.get("tts_profiles") or []) if str(p.get("provider", "")).lower() == "cartesia"]
    if args.profile:
        profiles = [p for p in profiles if p.get("name") == args.profile]
    if not profiles:
        print("No Cartesia TTS profile found in settings.json -- nothing was sent.\n"
              "Add one in Preferences -> Audio tools -> TTS profiles (provider cartesia, your key, a voice ID), then run this again.")
        return 2
    prof = profiles[0]
    if not str(prof.get("api_key") or "").strip() or not str(prof.get("voice_id") or "").strip():
        print("Profile %r has no API key or no voice ID -- nothing was sent." % prof.get("name"))
        return 2
    print("Profile %r (model %s, voice %s, key %s) -- sending %d characters to Cartesia..." % (
        prof.get("name"), prof.get("model") or tts_vocal._CARTESIA_DEFAULT_MODEL, prof.get("voice_id"), "set", len(args.text)))

    out = Path(tempfile.mkdtemp(prefix="la-tts-live-"))
    try:
        cfg = dict(settings, tts_output_dir=str(out), tts_profiles=[prof])
        r = tts_vocal.run({"text": args.text, "profile": prof.get("name", "")}, cfg)
        if not r.get("ok"):
            print("FAIL: %s" % r.get("message"))
            return 1
        path = Path(r["path"])
        with wave.open(str(path), "rb") as w:
            ch, rate, width, frames = w.getnchannels(), w.getframerate(), w.getsampwidth(), w.getnframes()
            raw = w.readframes(frames)
        dur = frames / rate if rate else 0
        peak = 0
        if width == 3 and raw:
            step = max(1, frames // 4000)
            for i in range(0, frames, step):
                v = int.from_bytes(raw[i * 3:i * 3 + 3], "little", signed=True)
                peak = max(peak, abs(v))
        peak_db = 20 * math.log10(peak / 8388608) if peak else float("-inf")
        checks = [
            ("WAV, 48 kHz mono 24-bit", (ch, rate, width) == (1, 48000, 3), "%d ch, %d Hz, %d-bit" % (ch, rate, width * 8)),
            ("non-zero duration", dur > 0.3, "%.2f s" % dur),
            ("audible (peak above -60 dBFS, not silence)", peak_db > -60, "peak %.1f dBFS" % peak_db),
        ]
        ok = True
        for name, good, detail in checks:
            print(("PASS  " if good else "FAIL  ") + name + "  [" + detail + "]")
            ok = ok and good
        print("generated %r, cache hit: %s" % (r.get("message"), r.get("cacheHit")))
        if args.keep:
            keep = Path(tempfile.gettempdir()) / path.name
            shutil.copyfile(path, keep)
            print("kept:", keep)
        return 0 if ok else 1
    finally:
        shutil.rmtree(out, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
