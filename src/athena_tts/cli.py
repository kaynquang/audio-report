from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .engines import ENGINE_REGISTRY, EngineError, auto_device
from .text import DEFAULT_SCRIPT_PATH, load_text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="athena-tts",
        description="Run a fixed voice consistency script through supported TTS engines.",
    )
    parser.add_argument(
        "--engine",
        default="kokoro",
        choices=[*ENGINE_REGISTRY.keys(), "all"],
        help="TTS engine to run. Use 'all' to try every engine.",
    )
    parser.add_argument("--list-engines", action="store_true", help="Print supported engines and exit.")
    parser.add_argument("--text", help="Inline text to synthesize. Overrides --text-file.")
    parser.add_argument(
        "--text-file",
        type=Path,
        default=DEFAULT_SCRIPT_PATH,
        help=f"Text file to synthesize. Defaults to {DEFAULT_SCRIPT_PATH}.",
    )
    parser.add_argument("--out", type=Path, help="Output WAV path for single-engine runs.")
    parser.add_argument("--out-dir", type=Path, default=Path("outputs"), help="Output directory for --engine all.")
    parser.add_argument(
        "--device",
        default="auto",
        help="Device passed to engines that support it: auto, cpu, cuda, mps, cuda:0, etc.",
    )
    parser.add_argument("--speed", type=float, default=1.0, help="Speech speed where supported.")
    parser.add_argument(
        "--speaker-reference",
        type=Path,
        help="Reference WAV for voice-cloning engines such as F5-TTS, IndexTTS, and Chatterbox.",
    )
    parser.add_argument(
        "--reference-text",
        default="",
        help="Transcript for --speaker-reference. Required by F5-TTS.",
    )

    parser.add_argument("--kokoro-lang", default="a", help="Kokoro language code, e.g. 'a' for American English.")
    parser.add_argument("--kokoro-voice", default="af_heart", help="Kokoro voice name or local voice tensor path.")

    parser.add_argument(
        "--chatterbox-model",
        choices=["standard", "turbo"],
        default="standard",
        help="Chatterbox model family to use.",
    )

    parser.add_argument("--f5-command", default="f5-tts_infer-cli", help="F5-TTS CLI executable.")
    parser.add_argument("--f5-model", default="F5TTS_v1_Base", help="F5-TTS model name.")

    parser.add_argument("--index-repo", type=Path, help="Optional local index-tts checkout to add to PYTHONPATH.")
    parser.add_argument("--index-model-dir", type=Path, default=Path("checkpoints"), help="IndexTTS checkpoint dir.")
    parser.add_argument("--index-cfg", type=Path, default=Path("checkpoints/config.yaml"), help="IndexTTS config path.")
    parser.add_argument("--index-fp16", action="store_true", help="Enable FP16 for IndexTTS on CUDA.")
    parser.add_argument("--index-deepspeed", action="store_true", help="Enable DeepSpeed for IndexTTS.")
    parser.add_argument("--index-cuda-kernel", action="store_true", help="Enable IndexTTS BigVGAN CUDA kernel.")

    parser.add_argument(
        "--styletts2-command",
        help="Command template for a local StyleTTS2 inference script.",
    )
    return parser


def list_engines() -> None:
    for name, engine_cls in ENGINE_REGISTRY.items():
        print(f"{name}\t{engine_cls.description}")


def output_path_for(args: argparse.Namespace, engine: str) -> Path:
    if args.engine == "all":
        return args.out_dir / f"{engine}.wav"
    return args.out or args.out_dir / f"{engine}.wav"


def run_one(engine: str, text: str, args: argparse.Namespace) -> bool:
    output = output_path_for(args, engine)
    try:
        ENGINE_REGISTRY[engine]().synthesize(text=text, output=output, args=args)
    except EngineError as exc:
        print(f"[{engine}] failed: {exc}", file=sys.stderr)
        return False
    print(f"[{engine}] wrote {output}")
    return True


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_engines:
        list_engines()
        return 0

    args.device = auto_device() if args.device == "auto" else args.device
    text = args.text if args.text is not None else load_text(args.text_file)

    if args.engine == "all":
        any_ok = False
        for engine in ENGINE_REGISTRY:
            any_ok = run_one(engine, text, args) or any_ok
        return 0 if any_ok else 1

    return 0 if run_one(args.engine, text, args) else 1

