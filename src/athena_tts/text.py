from __future__ import annotations

from pathlib import Path


DEFAULT_SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "voice_consistency_test.txt"


def load_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Text file does not exist: {path}")
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"Text file is empty: {path}")
    return text

