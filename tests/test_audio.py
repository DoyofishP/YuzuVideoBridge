"""Offline regression tests: no real video downloads or Whisper model weights needed."""
import json
import struct
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

import yuzu_bili_bridge as bridge


class ASRTests(unittest.TestCase):
    def test_float_audio_bypasses_pyav(self):
        class FakeWhisperModel:
            def __init__(self, name, device, compute_type):
                self.name = name

            def transcribe(self, audio, **kwargs):
                import numpy as np
                self_is_float_audio = (isinstance(audio, np.ndarray)
                                       and audio.dtype == np.float32
                                       and len(audio) == 3)
                assert self_is_float_audio
                assert kwargs["vad_filter"] is True
                segment = types.SimpleNamespace(start=1.25, end=2.5, text=" 你好 ")
                return iter([segment]), types.SimpleNamespace(language="zh")

        module = types.ModuleType("faster_whisper")
        module.WhisperModel = FakeWhisperModel
        wav_bytes = struct.pack("<fff", 0.0, 0.5, -0.5)
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.dict(sys.modules, {"faster_whisper": module}), \
                 mock.patch.object(bridge.subprocess, "run") as ffmpeg:
                ffmpeg.return_value = types.SimpleNamespace(
                    returncode=0, stdout=wav_bytes, stderr=b"")
                name, note = bridge.offline_asr("source.mp4", Path(td), "base")
            self.assertEqual(name, "transcript.txt")
            self.assertIn("detected=zh", note)
            self.assertIn("pipe:1", ffmpeg.call_args.args[0])
            transcript = (Path(td) / name).read_text(encoding="utf-8")
            self.assertEqual(transcript, "[00:01.250 → 00:02.500] 你好\n")

    def test_empty_audio_is_reported(self):
        module = types.ModuleType("faster_whisper")
        module.WhisperModel = object
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.dict(sys.modules, {"faster_whisper": module}), \
                 mock.patch.object(bridge.subprocess, "run") as ffmpeg:
                ffmpeg.return_value = types.SimpleNamespace(
                    returncode=0, stdout=b"", stderr=b"")
                with self.assertRaisesRegex(RuntimeError, "no audio"):
                    bridge.offline_asr("source.mp4", Path(td), "base")

    def packet_fixture(self, root):
        repo = Path(root)
        (repo / ".git").mkdir()
        packet = repo / "packets" / "MC" / "BV123abc"
        (packet / "images").mkdir(parents=True)
        picture = packet / "images" / "sheet_001.jpg"
        picture.write_bytes(b"unchanged-image")
        (packet / "manifest.json").write_text(
            json.dumps({"title": "test", "sampled_frames": 1,
                        "image_sheets": ["images/sheet_001.jpg"],
                        "subtitle_file": None, "transcript_file": None,
                        "asr_note": "ASR failed: metadata_errors"}),
            encoding="utf-8")
        return repo, packet, picture

    def run_repair(self, repo, transcriber, push=False):
        args = ["yuzu_bili_bridge.py", "https://www.bilibili.com/video/BV123abc",
                "--repo", str(repo), "--series", "MC", "--asr", "--asr-only"]
        if push:
            args.append("--push")
        fake_download = ({"id": "BV123abc"}, Path(repo) / "source.mp4")
        with mock.patch.object(sys, "argv", args), \
             mock.patch.object(bridge.shutil, "which", return_value="ffmpeg"), \
             mock.patch.object(bridge, "download_video", return_value=fake_download), \
             mock.patch.object(bridge, "get_duration", return_value=100.0), \
             mock.patch.object(bridge, "offline_asr", side_effect=transcriber), \
             mock.patch.object(bridge, "make_sheets", side_effect=AssertionError("images rebuilt")), \
             mock.patch.object(bridge, "run") as git_run:
            bridge.main()
            git_run.assert_not_called()

    def test_repair_keeps_existing_sheets(self):
        with tempfile.TemporaryDirectory() as td:
            repo, packet, picture = self.packet_fixture(td)

            def transcription(video, packet_path, model):
                (packet_path / "transcript.txt").write_text("hello\n", encoding="utf-8")
                return "transcript.txt", "Whisper base; detected=en"

            self.run_repair(repo, transcription)
            self.assertEqual(picture.read_bytes(), b"unchanged-image")
            manifest = json.loads((packet / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["transcript_file"], "transcript.txt")
            self.assertIn("asr_updated_utc", manifest)

    def test_failed_repair_is_not_pushed(self):
        with tempfile.TemporaryDirectory() as td:
            repo, packet, picture = self.packet_fixture(td)

            def transcription(*_):
                raise RuntimeError("fake ASR failure")

            with self.assertRaisesRegex(RuntimeError, "ASR transcription failed"):
                self.run_repair(repo, transcription, push=True)
            self.assertEqual(picture.read_bytes(), b"unchanged-image")
            manifest = json.loads((packet / "manifest.json").read_text(encoding="utf-8"))
            self.assertIn("fake ASR failure", manifest["asr_note"])
            self.assertIsNone(manifest["transcript_file"])


if __name__ == "__main__":
    unittest.main()
