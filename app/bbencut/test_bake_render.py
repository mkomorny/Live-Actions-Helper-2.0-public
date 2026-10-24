"""Unit tests for BBenCut full-run baking (Step 6).

Run from app\\:  python -m unittest bbencut.test_bake_render
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
import wave
from pathlib import Path

from bbencut import bake_render
from bbencut import ffmpeg_util as fu


def _write_silence_wav(path: Path, seconds: float, rate: int = 44100) -> None:
    n = int(seconds * rate)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(b"\x00\x00" * n)


def _real_slice(offset_beat: float, duration_beat: float) -> dict:
    return {
        "arrangementStartTime": 0,
        "duration": duration_beat,
        "filePath": "unused.wav",
        "loopSettings": {
            "looping": True,
            "startMarker": offset_beat,
            "endMarker": offset_beat + duration_beat,
            "loopStart": offset_beat,
            "loopEnd": offset_beat + duration_beat,
        },
    }


def _roll_placeholder(idx: int, duration_beat: float) -> dict:
    return {
        "arrangementStartTime": 0,
        "duration": duration_beat,
        "filePath": "__ROLL_GROUP_%d__" % idx,
        "loopSettings": {"looping": False, "startMarker": 0, "endMarker": duration_beat, "loopStart": 0, "loopEnd": duration_beat},
    }


class RenderFullBakeGatesTest(unittest.TestCase):
    def test_warped_source_refuses_whole_bake(self) -> None:
        result = bake_render.render_full_bake(
            "ffmpeg", "ffprobe", Path("."), "unused.wav", 120.0, True, [_real_slice(0, 0.1)], [],
        )
        self.assertFalse(result["ok"])
        self.assertIn("warped", result["reason"])

    def test_missing_tempo_refuses_whole_bake(self) -> None:
        result = bake_render.render_full_bake(
            "ffmpeg", "ffprobe", Path("."), "unused.wav", 0, False, [_real_slice(0, 0.1)], [],
        )
        self.assertFalse(result["ok"])
        self.assertIn("tempo", result["reason"])

    def test_missing_file_refuses_whole_bake(self) -> None:
        result = bake_render.render_full_bake(
            "ffmpeg", "ffprobe", Path("."), "C:\\no-such-bbencut-file.wav", 120.0, False,
            [_real_slice(0, 0.1)], [],
        )
        self.assertFalse(result["ok"])
        self.assertIn("not found", result["reason"])

    def test_bad_ffmpeg_path_raises_clear_error(self) -> None:
        with self.assertRaises(fu.FfmpegError) as ctx:
            fu.resolve_ffmpeg({"ffmpeg_path": "C:\\no-such-ffmpeg.exe"})
        self.assertIn("not a file", str(ctx.exception))

    def test_no_placeable_content_refuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src.wav"
            _write_silence_wav(src, 1.0)
            ffmpeg = shutil.which("ffmpeg")
            ffprobe = shutil.which("ffprobe")
            if not ffmpeg or not ffprobe:
                self.skipTest("ffmpeg/ffprobe not on PATH")
            result = bake_render.render_full_bake(ffmpeg, ffprobe, Path(tmp), str(src), 120.0, False, [], [])
            self.assertFalse(result["ok"])
            self.assertIn("no placeable content", result["reason"])


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg/ffprobe not on PATH")
class RenderFullBakeFfmpegTest(unittest.TestCase):
    def test_segment_past_end_is_rejected_not_clamped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src.wav"
            _write_silence_wav(src, 1.0)
            slices = [
                _real_slice(0, 0.1),
                _real_slice(4.0, 0.1),  # 4 beats at 120 BPM = 2s > 1s file
            ]
            result = bake_render.render_full_bake(
                shutil.which("ffmpeg"), shutil.which("ffprobe"),
                Path(tmp) / "out", str(src), 120.0, False, slices, [],
            )
            self.assertFalse(result["ok"])
            self.assertIn("extends past end", result["reason"])
            self.assertFalse(list((Path(tmp) / "out").glob("*.wav")) if (Path(tmp) / "out").exists() else [])

    def test_mixed_real_and_roll_slices_writes_expected_duration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src.wav"
            _write_silence_wav(src, 4.0)
            out_dir = Path(tmp) / "out"
            # Two real 0.1-beat slices + one roll placeholder expanding to two
            # 0.1-beat cuts, all at 120 BPM (0.05s per 0.1 beat) -> 0.20s total.
            slices = [
                _real_slice(0.0, 0.1),
                _roll_placeholder(0, 0.2),
                _real_slice(3.0, 0.1),
            ]
            roll_groups = [{"cuts": [
                {"sourceOffsetBeat": 1.0, "durationBeat": 0.1},
                {"sourceOffsetBeat": 2.0, "durationBeat": 0.1},
            ]}]
            result = bake_render.render_full_bake(
                shutil.which("ffmpeg"), shutil.which("ffprobe"),
                out_dir, str(src), 120.0, False, slices, roll_groups,
            )
            self.assertTrue(result["ok"], msg=result)
            rendered = Path(result["path"])
            self.assertTrue(rendered.is_file())
            duration = fu.probe_duration(rendered, shutil.which("ffprobe"))
            self.assertAlmostEqual(duration, 0.2, places=2)


if __name__ == "__main__":
    unittest.main()
