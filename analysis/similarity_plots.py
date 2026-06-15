"""Extra plots for the speaker-similarity report:
  1. waveform comparison of the NEW-script outputs (outputs2/)
  2. F0 pitch-contour comparison of those outputs
  3. similarity-vs-naturalness scatter (shows the fidelity/naturalness trade-off)
"""
from __future__ import annotations
import os
import numpy as np
import librosa
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs2")
ANA = os.path.join(ROOT, "analysis")
SR, FMIN, FMAX = 24000, 65.0, 400.0
ENGINES = ["kokoro", "chatterbox", "f5", "styletts2", "index"]
COLORS = {"kokoro": "#1f77b4", "chatterbox": "#ff7f0e", "f5": "#2ca02c",
          "styletts2": "#d62728", "index": "#9467bd"}

# results from the two tests
SIM = {"f5": 0.969, "index": 0.966, "chatterbox": 0.953, "styletts2": 0.923, "kokoro": 0.832}
HUMAN = {"styletts2": 89.6, "index": 89.5, "kokoro": 80.9, "chatterbox": 78.4, "f5": 35.4}


def load(e):
    y, _ = librosa.load(os.path.join(OUT, f"{e}.wav"), sr=SR, mono=True)
    return y


def waveforms():
    fig, axes = plt.subplots(len(ENGINES), 1, figsize=(12, 9), constrained_layout=True, sharex=True)
    for ax, e in zip(axes, ENGINES):
        y = load(e); t = np.linspace(0, len(y) / SR, len(y))
        ax.plot(t, y, color=COLORS[e], lw=0.4)
        ax.set_ylabel(e, rotation=0, ha="right", va="center"); ax.set_ylim(-1, 1); ax.set_yticks([])
    axes[-1].set_xlabel("time (s)")
    fig.suptitle("Waveform comparison — new script (outputs2)", fontsize=14)
    fig.savefig(os.path.join(ANA, "compare_waveforms2.png"), dpi=110); plt.close(fig)


def pitches():
    fig, ax = plt.subplots(figsize=(12, 5), constrained_layout=True)
    for e in ENGINES:
        y = load(e)
        f0, _, _ = librosa.pyin(y, fmin=FMIN, fmax=FMAX, sr=SR, frame_length=2048, hop_length=256)
        t = librosa.times_like(f0, sr=SR, hop_length=256)
        ax.plot(t, f0, lw=1.4, label=e, color=COLORS[e], alpha=0.85)
    ax.set_title("Pitch (F0) contour — new script"); ax.set_xlabel("time (s)")
    ax.set_ylabel("Hz"); ax.set_ylim(FMIN, FMAX); ax.grid(alpha=0.3); ax.legend(ncol=5)
    fig.savefig(os.path.join(ANA, "compare_pitch2.png"), dpi=110); plt.close(fig)


def scatter():
    fig, ax = plt.subplots(figsize=(8.5, 6), constrained_layout=True)
    for e in ENGINES:
        x, y = SIM[e], HUMAN[e]
        ax.scatter(x, y, s=180, color=COLORS[e], edgecolor="black", zorder=3)
        ax.annotate(e, (x, y), textcoords="offset points", xytext=(8, 6), fontsize=11)
    ax.axvline(0.983, ls="--", color="gray", lw=1.2)
    ax.text(0.983, ax.get_ylim()[0] + 3, " ceiling 0.983", color="gray", rotation=90, va="bottom", fontsize=9)
    ax.set_xlabel("Speaker similarity to reference  (giống giọng gốc) →")
    ax.set_ylabel("Naturalness / humanness score  (tự nhiên) →")
    ax.set_title("Trade-off: cloning fidelity vs naturalness")
    ax.grid(alpha=0.3)
    ax.text(0.02, 0.02, "góc trên-phải = lý tưởng (vừa giống vừa tự nhiên)",
            transform=ax.transAxes, fontsize=9, color="gray")
    fig.savefig(os.path.join(ANA, "tradeoff_scatter.png"), dpi=120); plt.close(fig)


if __name__ == "__main__":
    waveforms(); pitches(); scatter()
    print("Wrote compare_waveforms2.png, compare_pitch2.png, tradeoff_scatter.png")
