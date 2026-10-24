"""BBenCut Step 5: pre-render roll groups (very short BBCut2 sub-cuts, too
short to place as individual Arrangement clips) into real WAV files via
ffmpeg, so `runBbencut` (bridge\\live-actions-bridge.js) can place them like
any other slice instead of skipping them.

Pass-1 policy, confirmed with the user: only render when the source clip is
unwarped. See docs\\plans\\bbencut-step5-roll-rendering.md and the approved
plan ("The one new assumption this pass actually introduces") for why --
`60 / tempo` is the only way this tool converts a beat offset into raw file
seconds, and that conversion assumes the file's own audio is aligned to a
song-tempo grid at sample 0. Getting it wrong grabs the wrong grain of audio,
not a placement failure (Live's own warp engine still corrects the clip's
Arrangement span regardless -- see the plan).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import ffmpeg_util as fu


def render_roll_groups(
    ffmpeg_path: str,
    ffprobe_path: str,
    out_dir: Path,
    sample_file: str,
    tempo: float,
    warping: bool,
    roll_groups: list[dict[str, Any]],
) -> dict[str, Any]:
    """Returns {"rendered": {index: path}, "skipped": [{"index": i, "reason": str}]}.

    index matches slicer.ts's rollGroupIndex -- the group's position in
    roll_groups, which is also embedded in the placeholder slice's filePath
    sentinel "__ROLL_GROUP_<index>__".
    """
    rendered: dict[int, str] = {}
    skipped: list[dict[str, Any]] = []

    if warping:
        reason = "source clip is warped -- Pass 1 only pre-renders roll groups on an unwarped source clip."
        return {"rendered": rendered, "skipped": [{"index": i, "reason": reason} for i in range(len(roll_groups))]}
    if not (tempo and tempo > 0):
        reason = "song tempo unavailable."
        return {"rendered": rendered, "skipped": [{"index": i, "reason": reason} for i in range(len(roll_groups))]}
    src = Path(sample_file) if sample_file else None
    if not src or not src.is_file():
        reason = "source sample file not found on disk."
        return {"rendered": rendered, "skipped": [{"index": i, "reason": reason} for i in range(len(roll_groups))]}

    try:
        sample_length = fu.probe_duration(src, ffprobe_path)
    except fu.FfmpegError as exc:
        reason = "could not read source file duration: %s" % exc
        return {"rendered": rendered, "skipped": [{"index": i, "reason": reason} for i in range(len(roll_groups))]}

    seconds_per_beat = 60.0 / tempo

    for idx, group in enumerate(roll_groups):
        cuts = group.get("cuts") or []
        if not cuts:
            skipped.append({"index": idx, "reason": "roll group has no cuts."})
            continue

        cuts_seconds: list[tuple[float, float]] = []
        bad_cut = None
        for cut_idx, cut in enumerate(cuts):
            start = float(cut.get("sourceOffsetBeat") or 0) * seconds_per_beat
            end = start + float(cut.get("durationBeat") or 0) * seconds_per_beat
            # 1 ms of slack so a cut that lands on the file's last sample is
            # not rejected by floating-point noise; anything further is a
            # real overshoot and is still rejected (not clamped).
            if start < 0 or end > sample_length + 0.001 or end <= start:
                bad_cut = (cut_idx, start, end)
                break
            cuts_seconds.append((start, end))
        if bad_cut is not None:
            cut_idx, start, end = bad_cut
            skipped.append({
                "index": idx,
                "reason": "cut %d extends past end of source file (%.3fs > file is %.3fs)."
                % (cut_idx, end, sample_length) if end > sample_length
                else "cut %d has an invalid range (%.3fs-%.3fs)." % (cut_idx, start, end),
            })
            continue

        out_path = fu.next_output_path(out_dir, "BBenCutRoll", src, ".wav")
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
            skipped.append({"index": idx, "reason": str(exc)})
            continue
        if result.returncode != 0:
            out_path.unlink(missing_ok=True)
            skipped.append({"index": idx, "reason": "ffmpeg failed: %s" % fu.ffmpeg_error(result)})
            continue
        rendered[idx] = str(out_path)

    return {"rendered": rendered, "skipped": skipped}
