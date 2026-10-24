"""Unit tests for BBenCut roll-group pre-rendering.

Run from app\\:  python -m unittest bbencut.test_roll_render
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
import wave
from pathlib import Path

from bbencut import ffmpeg_util as fu
from bbencut import roll_render


def _write_silence_wav(path: Path, seconds: float, rate: int = 44100) -> None:
    n = int(seconds * rate)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(b"\x00\x00" * n)


class RenderRollGroupsGatesTest(unittest.TestCase):
    def test_warped_source_skips_every_group(self) -> None:
        groups = [{"cuts": [{"sourceOffsetBeat": 0, "durationBeat": 0.1}]}]
        result = roll_render.render_roll_groups(
            "ffmpeg", "ffprobe", Path("."), "unused.wav", 120.0, True, groups,
        )
        self.assertEqual(result["rendered"], {})
        self.assertEqual(len(result["skipped"]), 1)
        self.assertIn("warped", result["skipped"][0]["reason"])

    def test_missing_tempo_skips_every_group(self) -> None:
        groups = [{"cuts": [{"sourceOffsetBeat": 0, "durationBeat": 0.1}]}]
        result = roll_render.render_roll_groups(
            "ffmpeg", "ffprobe", Path("."), "unused.wav", 0, False, groups,
        )
        self.assertEqual(result["rendered"], {})
        self.assertIn("tempo", result["skipped"][0]["reason"])

    def test_missing_file_skips_every_group(self) -> None:
        groups = [{"cuts": [{"sourceOffsetBeat": 0, "durationBeat": 0.1}]}]
        result = roll_render.render_roll_groups(
            "ffmpeg", "ffprobe", Path("."), "C:\\no-such-bbencut-file.wav", 120.0, False, groups,
        )
        self.assertEqual(result["rendered"], {})
        self.assertIn("not found", result["skipped"][0]["reason"])

    def test_bad_ffmpeg_path_raises_clear_error(self) -> None:
        with self.assertRaises(fu.FfmpegError) as ctx:
            fu.resolve_ffmpeg({"ffmpeg_path": "C:\\no-such-ffmpeg.exe"})
        self.assertIn("not a file", str(ctx.exception))

    def test_empty_cuts_skips_that_group(self) -> None:
        # Need a real file so we get past the whole-batch gates; ffmpeg is
        # never invoked because the group has no cuts.
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src.wav"
            _write_silence_wav(src, 1.0)
            ffmpeg = shutil.which("ffmpeg")
            ffprobe = shutil.which("ffprobe")
            if not ffmpeg or not ffprobe:
                self.skipTest("ffmpeg/ffprobe not on PATH")
            result = roll_render.render_roll_groups(
                ffmpeg, ffprobe, Path(tmp), str(src), 120.0, False, [{"cuts": []}],
            )
            self.assertEqual(result["rendered"], {})
            self.assertIn("no cuts", result["skipped"][0]["reason"])


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg/ffprobe not on PATH")
class RenderRollGroupsFfmpegTest(unittest.TestCase):
    def test_cut_past_end_is_rejected_not_clamped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src.wav"
            _write_silence_wav(src, 1.0)
            groups = [{
                "cuts": [
                    {"sourceOffsetBeat": 0, "durationBeat": 0.1},
                    {"sourceOffsetBeat": 4.0, "durationBeat": 0.1},  # 4 beats at 120 BPM = 2s > 1s file
                ],
            }]
            result = roll_render.render_roll_groups(
                shutil.which("ffmpeg"), shutil.which("ffprobe"),
                Path(tmp) / "out", str(src), 120.0, False, groups,
            )
            self.assertEqual(result["rendered"], {})
            self.assertEqual(len(result["skipped"]), 1)
            self.assertIn("extends past end", result["skipped"][0]["reason"])
            self.assertFalse(list((Path(tmp) / "out").glob("*.wav")) if (Path(tmp) / "out").exists() else [])

    def test_atrim_concat_writes_expected_duration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src.wav"
            _write_silence_wav(src, 4.0)
            out_dir = Path(tmp) / "out"
            # Two 0.1-beat cuts at 120 BPM = 0.05s each → 0.10s concatenated.
            groups = [{
                "cuts": [
                    {"sourceOffsetBeat": 0.0, "durationBeat": 0.1},
                    {"sourceOffsetBeat": 1.0, "durationBeat": 0.1},
                    {"sourceOffsetBeat": 2.0, "durationBeat": 0.1},
                    {"sourceOffsetBeat": 3.0, "durationBeat": 0.1},
                ],
            }]
            result = roll_render.render_roll_groups(
                shutil.which("ffmpeg"), shutil.which("ffprobe"),
                out_dir, str(src), 120.0, False, groups,
            )
            self.assertEqual(result["skipped"], [], msg=result)
            self.assertEqual(len(result["rendered"]), 1)
            rendered = Path(result["rendered"][0])
            self.assertTrue(rendered.is_file())
            duration = fu.probe_duration(rendered, shutil.which("ffprobe"))
            self.assertAlmostEqual(duration, 0.2, places=2)


if __name__ == "__main__":
    unittest.main()
