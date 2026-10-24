"""Minimal ffmpeg/ffprobe plumbing for BBenCut roll-group pre-rendering.

Vendored subset of `app\\audio_sample\\ffmpeg_util.py` -- deliberately not
imported from there. That module is itself an untracked, unrelated WIP
feature (its own header notes it's a vendored copy too), and BBenCut roll
rendering must not silently depend on a sibling feature that isn't actually
shipped in this repo yet. Copy only what roll rendering needs; no fades,
pitch, generators, or full stream/format probing.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Any


class FfmpegError(RuntimeError):
    """A failure with a message that is safe to show directly to the user."""


DEFAULT_TIMEOUT = 900  # seconds -- matches app\audio_sample\ffmpeg_util.py's own default.


def resolve_ffmpeg(settings: dict[str, Any]) -> str:
    configured = str(settings.get("ffmpeg_path") or "").strip()
    if configured:
        path = Path(configured)
        if path.is_dir():
            candidate = path / "ffmpeg.exe"
            if candidate.is_file():
                return str(candidate)
        if not path.is_file():
            raise FfmpegError('ffmpeg_path "%s" is not a file. Fix it in Settings.' % configured)
        return configured
    found = shutil.which("ffmpeg")
    if found:
        return found
    raise FfmpegError("ffmpeg not found. Set ffmpeg_path in Settings or add ffmpeg to PATH.")


def resolve_ffprobe(settings: dict[str, Any]) -> str:
    configured = str(settings.get("ffmpeg_path") or "").strip()
    if configured:
        candidate = Path(configured).with_name(Path(configured).name.replace("ffmpeg", "ffprobe"))
        if candidate.is_file():
            return str(candidate)
    found = shutil.which("ffprobe")
    if found:
        return found
    raise FfmpegError("ffprobe not found. Set ffmpeg_path in Settings or add ffmpeg to PATH.")


def run_ffmpeg(ffmpeg_path: str, args: list[str], timeout: int = DEFAULT_TIMEOUT) -> subprocess.CompletedProcess:
    try:
        return subprocess.run([ffmpeg_path, "-y", *args], capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise FfmpegError("ffmpeg timed out after %ds." % timeout)
    except OSError as exc:
        raise FfmpegError("Could not run ffmpeg at %s: %s" % (ffmpeg_path, exc))


def run_ffprobe(ffprobe_path: str, args: list[str], timeout: int = 15) -> subprocess.CompletedProcess:
    try:
        return subprocess.run([ffprobe_path, *args], capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise FfmpegError("ffprobe timed out after %ds." % timeout)
    except OSError as exc:
        raise FfmpegError("Could not run ffprobe at %s: %s" % (ffprobe_path, exc))


def ffmpeg_error(result: subprocess.CompletedProcess) -> str:
    text = (result.stderr or b"").decode("utf-8", "replace").strip()
    return text[-500:] if text else "ffmpeg exited with code %d and no error output." % result.returncode


def build_atrim_concat_filter(cuts_seconds: list[tuple[float, float]]) -> str:
    """One -filter_complex chaining atrim+asetpts per (start, end) range in
    cuts_seconds, then concat'ing them in order into a single [out] stream.

    Shared by roll_render.py (one small group of cuts at a time) and
    bake_render.py (every slice in a run, flattened into one list) -- moved
    here so both call the same tested filter builder instead of two copies.
    """
    stages = []
    labels = []
    for i, (start, end) in enumerate(cuts_seconds):
        label = "a%d" % i
        stages.append("[0:a]atrim=start=%.6f:end=%.6f,asetpts=PTS-STARTPTS[%s]" % (start, end, label))
        labels.append("[%s]" % label)
    concat = "%sconcat=n=%d:v=0:a=1[out]" % ("".join(labels), len(labels))
    return ";".join(stages) + ";" + concat


def probe_duration(path: Path, ffprobe_path: str) -> float:
    """How many real seconds this file contains. Just the duration -- not a
    full stream/format probe, that's more than roll rendering needs."""
    result = run_ffprobe(
        ffprobe_path,
        ["-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
    )
    if result.returncode != 0:
        raise FfmpegError("Could not read %s: %s" % (path.name, ffmpeg_error(result)))
    try:
        data = json.loads(result.stdout.decode("utf-8", "replace"))
    except json.JSONDecodeError as exc:
        raise FfmpegError("Could not parse ffprobe output for %s: %s" % (path.name, exc)) from exc
    duration = (data.get("format") or {}).get("duration")
    if not duration:
        raise FfmpegError("%s has no readable duration." % path.name)
    return float(duration)


_NAME_LOCK = threading.Lock()
_SAFE_RE = re.compile(r"[^A-Za-z0-9]+")


def next_output_path(out_dir: Path, op_label: str, source_path: Path | None, ext: str) -> Path:
    """Friendly numbered output name: <Op>-<SourceStem>-N.ext (or <Op>-Sample-N.ext)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_label = _SAFE_RE.sub("", op_label) or "Output"
    safe_stem = _SAFE_RE.sub("", source_path.stem) if source_path else ""
    stem = safe_stem or "Sample"
    prefix = "%s-%s-" % (safe_label, stem)
    pattern = re.compile(r"^%s(\d+)%s$" % (re.escape(prefix), re.escape(ext)))

    with _NAME_LOCK:
        highest = 0
        for existing in out_dir.glob("%s*%s" % (prefix, ext)):
            m = pattern.match(existing.name)
            if m:
                highest = max(highest, int(m.group(1)))
        path = out_dir / ("%s%d%s" % (prefix, highest + 1, ext))
        path.touch()  # reserve the name so two quick Runs never collide
        return path
