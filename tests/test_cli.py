from __future__ import annotations

import argparse
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from athena_tts.cli import build_parser, output_path_for
from athena_tts.engines import ENGINE_REGISTRY, F5Engine, StyleTTS2Engine
from athena_tts.text import DEFAULT_SCRIPT_PATH, load_text


class CLITests(unittest.TestCase):
    def test_default_script_contains_requested_phrase(self) -> None:
        text = load_text(DEFAULT_SCRIPT_PATH)
        self.assertIn("The product sounds clear, stable, and natural.", text)
        self.assertIn("Today is June fifteenth, twenty twenty-six.", text)

    def test_registry_contains_requested_engines(self) -> None:
        self.assertEqual(
            {"kokoro", "chatterbox", "f5", "index", "styletts2"},
            set(ENGINE_REGISTRY),
        )

    def test_output_path_for_all_mode_uses_engine_name(self) -> None:
        args = argparse.Namespace(engine="all", out=None, out_dir=Path("out"))
        self.assertEqual(Path("out/f5.wav"), output_path_for(args, "f5"))

    def test_parser_accepts_all_engine(self) -> None:
        args = build_parser().parse_args(["--engine", "all"])
        self.assertEqual("all", args.engine)


class EngineCommandTests(unittest.TestCase):
    def test_f5_command_uses_reference_and_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ref = Path(tmp) / "ref.wav"
            ref.write_bytes(b"RIFF")
            out = Path(tmp) / "out.wav"
            args = argparse.Namespace(
                speaker_reference=ref,
                reference_text="reference transcript",
                f5_command="f5-tts_infer-cli",
                f5_model="F5TTS_v1_Base",
                device="cpu",
                speed=1.0,
            )
            with patch("athena_tts.engines.run_command") as run_command:
                F5Engine().synthesize("hello", out, args)
        command = run_command.call_args.args[0]
        self.assertIn("--ref_audio", command)
        self.assertIn(str(ref), command)
        self.assertIn("--output_file", command)
        self.assertIn("out.wav", command)

    def test_styletts2_template_expands_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "style.wav"
            args = argparse.Namespace(
                styletts2_command="python infer.py --text-file {text_file} --output {output} --device {device}",
                reference_text="",
                speaker_reference=None,
                device="cpu",
            )
            with patch("athena_tts.engines.run_command") as run_command:
                StyleTTS2Engine().synthesize("hello", out, args)
        command = run_command.call_args.args[0]
        self.assertEqual("python", command[0])
        self.assertIn(str(out), command)


if __name__ == "__main__":
    unittest.main()

