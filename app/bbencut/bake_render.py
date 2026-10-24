"""BBenCut Step 6: bake an entire cut sequence into one WAV, for a run whose
placed-clip count exceeds BAKE_THRESHOLD -- avoids a large synchronous
create_audio_clip loop in `runBbencut` (bridge\\live-actions-bridge.js) by
placing one Arrangement clip (one undo step) instead of dozens.

Same Pass-1 policy as roll_render.py, and for the same reason: only bakes
when the source clip is unwarped. See docs\\plans\\bbencut-step6-bake-and-
safety.md and bbencut-step5-roll-rendering.md ("The one new assumption this
pass introduces") for why -- `60 / tempo` is the only way this tool converts
a beat offset into raw file seconds, and that assumes the unwarped file's
audio is aligned to a song-tempo grid at sample 0.

Unlike render_roll_groups (one WAV per small group, bad cuts skip just that
group), a bake produces a single WAV for the whole run -- a single bad
segment fails the whole bake, not a partial/guessed result.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import ffmpeg_util as fu

BAKE_THRESHOLD = 80  # from the master plan's own suggestion ("start around 80"), not yet
                      # live-measured against this machine/Live build -- runBbencut's own
                      # elapsed-ms logging (bridge\live-actions-bridge.js) is how that
                      # number gets checked against reality later.


def _segment_for_slice(slice_: dict[str, Any]) -> tuple[float, float] | None:
    """(sourceOffsetBeat, durationBeat) for one non-roll slice, matching the
    same startMarker/loopStart fallback runBbencut itself uses for loopStart
    (bridge\\live-actions-bridge.js) so baked audio matches per-slice placement."""
    duration = float(slice_.get("duration") or 0)
    if duration <= 0:
        return None
    loop_settings = slice_.get("loopSettings") or {}
    start = loop_settings.get("startMarker")
    if start is None:
        start = loop_settings.get("loopStart")
    if start is None:
        start = 0
    return (float(start), duration)


def render_full_bake(
    ffmpeg_path: str,
    ffprobe_path: str,
    out_dir: Path,
    sample_file: str,
    tempo: float,
    warping: bool,
    slices: list[dict[str, Any]],
    roll_groups: list[dict[str, Any]],
) -> dict[str, Any]:
    """Returns {"ok": True, "path": str} or {"ok": False, "reason": str}."""
    if warping:
        return {"ok": False, "reason": "source clip is warped -- baking requires an unwarped source clip."}
    if not (tempo and tempo > 0):
        return {"ok": False, "reason": "song tempo unavailable."}
    src = Path(sample_file) if sample_file else None
    if not src or not src.is_file():
        return {"ok": False, "reason": "source sample file not found on disk."}

    try:
        sample_length = fu.probe_duration(src, ffprobe_path)
    except fu.FfmpegError as exc:
        return {"ok": False, "reason": "could not read source file duration: %s" % exc}

    seconds_per_beat = 60.0 / tempo

    # Flatten the run into (sourceOffsetBeat, durationBeat) segments, in
    # Arrangement order. slicer.ts already makes slices contiguous (it closes
    # gaps by extending the previous clip's duration) and gives one slices[]
    # entry per placement, real or roll placeholder -- so walking slices in
    # order and expanding roll placeholders is the whole job, no separate
    # gap-filling here.
    segments_beats: list[tuple[float, float]] = []
    for slice_ in slices:
        file_path = str(slice_.get("filePath") or "")
        if file_path.startswith("__ROLL_GROUP_"):
            try:
                idx = int(file_path[len("__ROLL_GROUP_"):-2])
            except ValueError:
                return {"ok": False, "reason": "malformed roll-group placeholder %r." % file_path}
            if idx < 0 or idx >= len(roll_groups):
                return {"ok": False, "reason": "roll-group index %d out of range." % idx}
            for cut in roll_groups[idx].get("cuts") or []:
                segments_beats.append((
                    float(cut.get("sourceOffsetBeat") or 0),
                    float(cut.get("durationBeat") or 0),
                ))
        else:
            segment = _segment_for_slice(slice_)
            if segment is not None:
                segments_beats.append(segment)

    if not segments_beats:
        return {"ok": False, "reason": "no placeable content in this run."}

    cuts_seconds: list[tuple[float, float]] = []
    for seg_idx, (offset_beat, duration_beat) in enumerate(segments_beats):
        start = offset_beat * seconds_per_beat
        end = start + duration_beat * seconds_per_beat
        # 1 ms slack, same reasoning as render_roll_groups: a cut landing on
        # the file's last sample shouldn't be rejected by float noise.
        if start < 0 or end > sample_length + 0.001 or end <= start:
            reason = (
                "segment %d extends past end of source file (%.3fs > file is %.3fs)."
                % (seg_idx, end, sample_length) if end > sample_length
                else "segment %d has an invalid range (%.3fs-%.3fs)." % (seg_idx, start, end)
            )
            return {"ok": False, "reason": reason}
        cuts_seconds.append((start, end))

    out_path = fu.next_output_path(out_dir, "BBenCutBake", src, ".wav")
    args = [
        "-i", str(src),
        "-filter_complex", fu.build_atrim_concat_filter(cuts_seconds),
        "-map", "[out]",
        "-c:a", "pcm_s24le",
        str(out_path),
    ]
    try:
        result = fu.run_ffmpeg(ffmpeg_path, args)
    except fu.FfmpegError as exc:
        out_path.unlink(missing_ok=True)
        return {"ok": False, "reason": str(exc)}
    if result.returncode != 0:
        out_path.unlink(missing_ok=True)
        return {"ok": False, "reason": "ffmpeg failed: %s" % fu.ffmpeg_error(result)}

    return {"ok": True, "path": str(out_path)}
