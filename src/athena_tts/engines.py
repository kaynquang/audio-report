from __future__ import annotations

import os
import shlex
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class EngineError(RuntimeError):
    """Raised when an engine cannot synthesize audio."""


class Engine(Protocol):
    description: str

    def synthesize(self, text: str, output: Path, args: object) -> None:
        ...


def auto_device() -> str:
    try:
        import torch
    except Exception:
        return "cpu"

    try:
        if torch.cuda.is_available():
            return "cuda"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
    except Exception:
        return "cpu"
    return "cpu"


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def require_file(path: Path | None, label: str) -> Path:
    if path is None:
        raise EngineError(f"{label} is required.")
    if not path.exists():
        raise EngineError(f"{label} does not exist: {path}")
    return path


def import_error(package: str, install_hint: str, exc: BaseException) -> EngineError:
    return EngineError(f"Could not import {package}: {exc}. Install it with: {install_hint}")


@dataclass
class KokoroEngine:
    description = "Kokoro Python package adapter."

    def synthesize(self, text: str, output: Path, args: object) -> None:
        try:
            import numpy as np
            import soundfile as sf
            from kokoro import KPipeline
        except Exception as exc:
            raise import_error("kokoro", 'pip install "kokoro>=0.9.4" soundfile numpy', exc) from exc

        ensure_parent(output)
        pipeline = KPipeline(lang_code=args.kokoro_lang)
        generator = pipeline(
            text,
            voice=args.kokoro_voice,
            speed=args.speed,
            split_pattern=r"\n+",
        )
        chunks = [np.asarray(audio) for _, _, audio in generator]
        if not chunks:
            raise EngineError("Kokoro returned no audio chunks.")
        audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
        sf.write(str(output), audio, 24000)


@dataclass
class ChatterboxEngine:
    description = "Resemble AI Chatterbox Python package adapter."

    def synthesize(self, text: str, output: Path, args: object) -> None:
        try:
            import torchaudio as ta
            if args.chatterbox_model == "turbo":
                from chatterbox.tts_turbo import ChatterboxTurboTTS as Model
            else:
                from chatterbox.tts import ChatterboxTTS as Model
        except Exception as exc:
            raise import_error("chatterbox", "pip install chatterbox-tts torchaudio", exc) from exc

        prompt = None
        if args.speaker_reference is not None:
            prompt = require_file(args.speaker_reference, "--speaker-reference")
        if args.chatterbox_model == "turbo" and prompt is None:
            raise EngineError("--chatterbox-model turbo requires --speaker-reference.")

        ensure_parent(output)
        model = Model.from_pretrained(device=args.device)
        kwargs = {"audio_prompt_path": str(prompt)} if prompt else {}
        wav = model.generate(text, **kwargs)
        ta.save(str(output), wav, model.sr)


@dataclass
class F5Engine:
    description = "F5-TTS CLI adapter."

    def synthesize(self, text: str, output: Path, args: object) -> None:
        ref_audio = require_file(args.speaker_reference, "--speaker-reference")
        if not args.reference_text:
            raise EngineError("--reference-text is required for F5-TTS.")

        ensure_parent(output)
        with tempfile.TemporaryDirectory(prefix="athena_f5_") as tmp:
            text_file = Path(tmp) / "script.txt"
            text_file.write_text(text, encoding="utf-8")
            command = [
                args.f5_command,
                "--model",
                args.f5_model,
                "--ref_audio",
                str(ref_audio),
                "--ref_text",
                args.reference_text,
                "--gen_file",
                str(text_file),
                "--output_dir",
                str(output.parent),
                "--output_file",
                output.name,
                "--device",
                args.device,
                "--speed",
                str(args.speed),
            ]
            run_command(command, "F5-TTS")


@dataclass
class IndexTTSEngine:
    description = "IndexTTS2 Python adapter."

    def synthesize(self, text: str, output: Path, args: object) -> None:
        ref_audio = require_file(args.speaker_reference, "--speaker-reference")
        if args.index_repo is not None:
            sys.path.insert(0, str(args.index_repo.resolve()))

        try:
            from indextts.infer_v2 import IndexTTS2
        except Exception as exc:
            raise import_error(
                "indextts",
                "clone https://github.com/index-tts/index-tts and run with --index-repo or PYTHONPATH",
                exc,
            ) from exc

        ensure_parent(output)
        tts = IndexTTS2(
            cfg_path=str(args.index_cfg),
            model_dir=str(args.index_model_dir),
            device=None if args.device == "auto" else args.device,
            use_fp16=args.index_fp16,
            use_cuda_kernel=args.index_cuda_kernel,
            use_deepspeed=args.index_deepspeed,
        )
        tts.infer(
            spk_audio_prompt=str(ref_audio),
            text=text,
            output_path=str(output),
            verbose=True,
        )


@dataclass
class StyleTTS2Engine:
    description = "StyleTTS2 command-template adapter for local inference scripts."

    def synthesize(self, text: str, output: Path, args: object) -> None:
        if not args.styletts2_command:
            raise EngineError(
                "StyleTTS2 needs --styletts2-command because the official repository exposes inference through notebooks."
            )
        ensure_parent(output)
        with tempfile.TemporaryDirectory(prefix="athena_styletts2_") as tmp:
            text_file = Path(tmp) / "script.txt"
            ref_text_file = Path(tmp) / "reference_text.txt"
            text_file.write_text(text, encoding="utf-8")
            ref_text_file.write_text(args.reference_text or "", encoding="utf-8")
            values = {
                "text": text,
                "text_file": str(text_file),
                "output": str(output),
                "device": args.device,
                "speaker_reference": str(args.speaker_reference or ""),
                "reference_text": args.reference_text or "",
                "reference_text_file": str(ref_text_file),
            }
            command = shlex.split(args.styletts2_command.format(**values))
            run_command(command, "StyleTTS2")


@dataclass
class LiteLLMEngine:
    description = "LiteLLM proxy (OpenAI-compatible /audio/speech), e.g. Gemini TTS."

    def synthesize(self, text: str, output: Path, args: object) -> None:
        import json
        import urllib.error
        import urllib.request

        key = args.litellm_api_key or os.environ.get("LITELLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
        if not key:
            raise EngineError(
                "LiteLLM needs an API key. Set --litellm-api-key or env LITELLM_API_KEY."
            )
        base = args.litellm_base_url.rstrip("/")
        url = base + "/v1/audio/speech"
        fmt = args.litellm_format
        payload = {
            "model": args.litellm_model,
            "input": text,
            "voice": args.litellm_voice,
            "response_format": fmt,
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=args.litellm_timeout) as resp:
                data = resp.read()
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")[:500]
            raise EngineError(f"LiteLLM HTTP {exc.code}: {body}") from exc
        except Exception as exc:
            raise EngineError(f"LiteLLM request failed: {exc}") from exc

        if not data or len(data) < 256:
            raise EngineError(f"LiteLLM returned too little data ({len(data)} bytes): {data[:200]!r}")

        ensure_parent(output)
        if fmt == "wav":
            output.write_bytes(data)
        else:
            # tải về dạng fmt rồi chuyển sang wav bằng ffmpeg
            with tempfile.TemporaryDirectory(prefix="athena_litellm_") as tmp:
                raw = Path(tmp) / f"audio.{fmt}"
                raw.write_bytes(data)
                run_command(["ffmpeg", "-y", "-i", str(raw), str(output)], "LiteLLM ffmpeg")


def run_command(command: list[str], label: str) -> None:
    try:
        subprocess.run(command, check=True)
    except FileNotFoundError as exc:
        raise EngineError(f"{label} command was not found: {command[0]}") from exc
    except subprocess.CalledProcessError as exc:
        raise EngineError(f"{label} exited with status {exc.returncode}: {shlex.join(command)}") from exc


ENGINE_REGISTRY: dict[str, type[Engine]] = {
    "kokoro": KokoroEngine,
    "chatterbox": ChatterboxEngine,
    "f5": F5Engine,
    "index": IndexTTSEngine,
    "styletts2": StyleTTS2Engine,
    "litellm": LiteLLMEngine,
}

