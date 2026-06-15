"""Speaker-similarity test: how close is each engine's output (new script) to the
ORIGINAL reference voice it cloned from (refs/speaker.wav)?

Uses Resemblyzer (GE2E d-vector speaker encoder). Cosine similarity of speaker
embeddings — higher = more like the reference voice identity.
"""
from __future__ import annotations

import os
import csv
import numpy as np
from resemblyzer import VoiceEncoder, preprocess_wav
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs2")
ANA = os.path.join(ROOT, "analysis")
REF = os.path.join(ROOT, "refs", "speaker.wav")          # the clone reference
REF_FULL = os.path.join(ROOT, "refs", "speaker_full.wav")  # same speaker, more audio
ENGINES = ["kokoro", "chatterbox", "f5", "styletts2", "index"]
CLONES = {"chatterbox", "f5", "styletts2", "index"}  # kokoro can't clone

enc = VoiceEncoder()


def emb(path):
    return enc.embed_utterance(preprocess_wav(path))


def main():
    ref = emb(REF)
    rows = []
    # ceiling: same speaker, different clip
    ceil = float(np.dot(ref, emb(REF_FULL)))
    for e in ENGINES:
        p = os.path.join(OUT, f"{e}.wav")
        if not os.path.exists(p):
            print("missing", p); continue
        sim = float(np.dot(ref, emb(p)))
        rows.append((e, sim))

    rows_sorted = sorted([r for r in rows if r[0] in CLONES], key=lambda x: x[1], reverse=True)
    kok = [r for r in rows if r[0] == "kokoro"]

    with open(os.path.join(ANA, "similarity.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["engine", "cosine_similarity_to_reference", "clones_voice"])
        for e, s in rows:
            w.writerow([e, f"{s:.4f}", e in CLONES])
        w.writerow(["[ceiling] speaker_full vs speaker", f"{ceil:.4f}", "same person"])

    # bar chart
    order = [r[0] for r in rows_sorted] + [r[0] for r in kok]
    vals = dict(rows)
    colors = ["#2ca02c" if v >= 0.80 else "#ff7f0e" if v >= 0.70 else "#d62728"
              for v in [vals[o] for o in order]]
    fig, ax = plt.subplots(figsize=(9, 5), constrained_layout=True)
    bars = ax.bar(order, [vals[o] for o in order], color=colors)
    ax.axhline(ceil, ls="--", color="gray", lw=1.4,
               label=f"ceiling (same speaker) = {ceil:.3f}")
    for b, o in zip(bars, order):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.01,
                f"{vals[o]:.3f}", ha="center", fontsize=10)
    ax.set_ylabel("cosine similarity to reference voice")
    ax.set_title("Speaker similarity to original voice (refs/speaker.wav) — new script")
    ax.set_ylim(0, max(1.0, ceil + 0.05)); ax.legend(); ax.grid(axis="y", alpha=0.3)
    ax.text(0.5, -0.14, "kokoro = preset voice (does not clone) — baseline",
            transform=ax.transAxes, ha="center", fontsize=9, color="gray")
    fig.savefig(os.path.join(ANA, "similarity_chart.png"), dpi=120)

    # report
    print(f"\nReference: refs/speaker.wav   |  ceiling (same speaker, other clip) = {ceil:.3f}\n")
    print("Ranking (voice-cloning engines, most similar first):")
    for i, (e, s) in enumerate(rows_sorted, 1):
        pct = 100 * s / ceil
        print(f"  {i}. {e:11s}  cos={s:.3f}   ({pct:.0f}% of ceiling)")
    for e, s in kok:
        print(f"  -- {e:11s}  cos={s:.3f}   (preset voice, no cloning — baseline)")
    print("\nWrote similarity.csv and similarity_chart.png")


if __name__ == "__main__":
    main()
