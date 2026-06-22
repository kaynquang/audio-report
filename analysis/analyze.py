"""Analyze the five TTS outputs: waveforms, spectrograms, pitch (F0) contours,
and objective proxy metrics for how "human" each voice sounds.

Criteria evaluated (proxies — not a substitute for a human MOS listening test):
  - tone / timbre        -> spectral centroid level & stability
  - pitch height (cao/thap) -> F0 mean and range
  - intonation (luyen lay)  -> F0 variation / dynamism over time
  - naturalness (tu nhien)  -> energy dynamics, natural pausing, pitch in human range
"""
from __future__ import annotations

import os
import csv

import numpy as np
import librosa
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "outputs")
ANA_DIR = os.path.join(ROOT, "analysis")
os.makedirs(ANA_DIR, exist_ok=True)

ENGINES = ["original", "kokoro", "chatterbox", "f5", "styletts2", "index", "litellm"]
COLORS = {"original": "#000000", "kokoro": "#1f77b4", "chatterbox": "#ff7f0e",
          "f5": "#2ca02c", "styletts2": "#d62728", "index": "#9467bd", "litellm": "#17becf"}
SR = 24000
FMIN, FMAX = 65.0, 400.0  # human speech F0 search range


def load(engine):
    if engine == "original":
        path = os.path.join(ROOT, "refs", "original_voice.wav")
    else:
        path = os.path.join(OUT_DIR, f"{engine}.wav")
    y, _ = librosa.load(path, sr=SR, mono=True)
    return y


def analyze(engine, y):
    dur = len(y) / SR
    # --- F0 via probabilistic YIN ---
    f0, voiced_flag, _ = librosa.pyin(y, fmin=FMIN, fmax=FMAX, sr=SR,
                                      frame_length=2048, hop_length=256)
    times = librosa.times_like(f0, sr=SR, hop_length=256)
    vf0 = f0[~np.isnan(f0)]
    voiced_ratio = float(np.mean(~np.isnan(f0)))

    if vf0.size > 5:
        f0_mean = float(np.mean(vf0))
        f0_std = float(np.std(vf0))
        f0_p5, f0_p95 = np.percentile(vf0, [5, 95])
        f0_range = float(f0_p95 - f0_p5)
        # semitone-based variation (perceptual intonation strength)
        semis = 12 * np.log2(np.clip(vf0, 1e-6, None) / f0_mean)
        f0_semi_std = float(np.std(semis))
        # local micro-variation between consecutive voiced frames (luyen lay)
        df = np.abs(np.diff(vf0))
        f0_delta = float(np.median(df[df > 0])) if np.any(df > 0) else 0.0
    else:
        f0_mean = f0_std = f0_range = f0_semi_std = f0_delta = 0.0

    # --- Energy dynamics (measured on ACTIVE speech only, so pauses don't
    # dominate the dB spread) ---
    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=256)[0]
    rms_db = librosa.amplitude_to_db(rms + 1e-8)
    active = rms > (np.percentile(rms, 20) * 1.5 + 1e-6)
    energy_dyn = float(np.std(rms_db[active])) if np.any(active) else 0.0

    # --- Pauses / phrasing: silent gaps > 150 ms ---
    thr = np.percentile(rms, 20) * 1.5 + 1e-6
    silent = rms < thr
    hop_t = 256 / SR
    min_gap = int(0.15 / hop_t)
    pauses, run = 0, 0
    for s in silent:
        run = run + 1 if s else 0
        if run == min_gap:
            pauses += 1
    pause_rate = pauses / dur  # pauses per second

    # --- Timbre / brightness ---
    cent = librosa.feature.spectral_centroid(y=y, sr=SR, hop_length=256)[0]
    cent_mean = float(np.mean(cent))
    cent_std = float(np.std(cent))

    return {
        "engine": engine, "duration_s": dur,
        "f0_mean_hz": f0_mean, "f0_std_hz": f0_std, "f0_range_hz": f0_range,
        "f0_semitone_std": f0_semi_std, "f0_local_delta_hz": f0_delta,
        "voiced_ratio": voiced_ratio, "energy_dyn_db": energy_dyn,
        "pause_rate_per_s": pause_rate, "centroid_hz": cent_mean,
        "centroid_std_hz": cent_std,
        "_f0": f0, "_times": times, "_y": y, "_rms_db": rms_db,
    }


def humanness(metrics):
    """Composite 0-100 score using smooth, peaked preference curves so values
    are graded (not saturated). Each criterion peaks at a perceptually
    natural value and decays for monotone/flat OR excessive/unstable extremes.
    Anchored to conversational-speech norms."""
    def peak(x, ideal, width, asym_hi=1.0):
        # Gaussian-ish bump peaking at `ideal`; `width` = 1-sigma below,
        # width*asym_hi above (lets us tolerate more on the high side or less).
        sigma = width if x <= ideal else width * asym_hi
        return float(np.exp(-0.5 * ((x - ideal) / (sigma + 1e-9)) ** 2))

    scores = {}
    # Intonation (luyến láy): perceptual pitch swing in semitones.
    # Monotone TTS ~1-2 st; lively human ~3-5 st; >7 usually = wobble/octave errors.
    scores["intonation"] = peak(metrics["f0_semitone_std"], 4.0, 1.6, asym_hi=0.6)
    # Pitch range (cao/thấp): p5-p95 spread in Hz.
    scores["pitch_range"] = peak(metrics["f0_range_hz"], 150, 70, asym_hi=0.7)
    # Energy dynamics within active speech (dB) — natural stress/emphasis.
    scores["energy"] = peak(metrics["energy_dyn_db"], 9.0, 4.0, asym_hi=1.2)
    # Phrasing: pauses per second — some breathing, not choppy.
    scores["phrasing"] = peak(metrics["pause_rate_per_s"], 0.40, 0.22)
    # Voiced ratio over the passage.
    scores["voicing"] = peak(metrics["voiced_ratio"], 0.60, 0.15)
    # Timbre brightness — centroid; too bright = sibilant/synthetic.
    scores["timbre"] = peak(metrics["centroid_hz"], 2500, 900, asym_hi=0.8)

    weights = {"intonation": 0.30, "pitch_range": 0.16, "energy": 0.18,
               "phrasing": 0.12, "voicing": 0.10, "timbre": 0.14}
    total = sum(scores[k] * w for k, w in weights.items()) * 100
    scores["TOTAL"] = total
    return scores


def plot_per_engine(m):
    y, f0, t = m["_y"], m["_f0"], m["_times"]
    fig, ax = plt.subplots(3, 1, figsize=(11, 8), constrained_layout=True)
    eng = m["engine"]
    c = COLORS[eng]
    # waveform
    tw = np.linspace(0, len(y) / SR, len(y))
    ax[0].plot(tw, y, color=c, lw=0.4)
    ax[0].set_title(f"{eng} — Waveform"); ax[0].set_ylabel("amplitude")
    ax[0].set_xlim(0, len(y) / SR)
    # spectrogram
    S = librosa.amplitude_to_db(np.abs(librosa.stft(y, hop_length=256)), ref=np.max)
    img = librosa.display.specshow(S, sr=SR, hop_length=256, x_axis="time",
                                   y_axis="hz", ax=ax[1], cmap="magma")
    ax[1].set_ylim(0, 6000); ax[1].set_title(f"{eng} — Spectrogram")
    fig.colorbar(img, ax=ax[1], format="%+2.0f dB")
    # F0 contour
    ax[2].plot(t, f0, color=c, lw=1.6)
    ax[2].set_title(f"{eng} — Pitch (F0) contour")
    ax[2].set_ylabel("Hz"); ax[2].set_xlabel("time (s)")
    ax[2].set_ylim(FMIN, FMAX); ax[2].set_xlim(0, len(y) / SR); ax[2].grid(alpha=0.3)
    p = os.path.join(ANA_DIR, f"{eng}_analysis.png")
    fig.savefig(p, dpi=110); plt.close(fig)
    return p


def plot_compare(ms):
    # stacked waveforms
    fig, axes = plt.subplots(len(ms), 1, figsize=(12, 9), constrained_layout=True, sharex=True)
    for ax, m in zip(axes, ms):
        y = m["_y"]; tw = np.linspace(0, len(y) / SR, len(y))
        ax.plot(tw, y, color=COLORS[m["engine"]], lw=0.4)
        ax.set_ylabel(m["engine"], rotation=0, ha="right", va="center")
        ax.set_ylim(-1, 1); ax.set_yticks([])
    axes[-1].set_xlabel("time (s)")
    fig.suptitle("Waveform comparison — all engines", fontsize=14)
    p1 = os.path.join(ANA_DIR, "compare_waveforms.png")
    fig.savefig(p1, dpi=110); plt.close(fig)

    # overlaid F0 contours
    fig, ax = plt.subplots(figsize=(12, 5), constrained_layout=True)
    for m in ms:
        ax.plot(m["_times"], m["_f0"], lw=1.4, label=m["engine"], color=COLORS[m["engine"]], alpha=0.85)
    ax.set_title("Pitch (F0) contour comparison — intonation / luyến láy")
    ax.set_xlabel("time (s)"); ax.set_ylabel("Hz"); ax.set_ylim(FMIN, FMAX)
    ax.grid(alpha=0.3); ax.legend(ncol=5, loc="upper right")
    p2 = os.path.join(ANA_DIR, "compare_pitch.png")
    fig.savefig(p2, dpi=110); plt.close(fig)
    return p1, p2


def main():
    metrics, scores = [], {}
    for eng in ENGINES:
        y = load(eng)
        m = analyze(eng, y)
        metrics.append(m)
        scores[eng] = humanness(m)
        plot_per_engine(m)
    plot_compare(metrics)

    # CSV of raw metrics
    keys = [k for k in metrics[0] if not k.startswith("_")]
    with open(os.path.join(ANA_DIR, "metrics.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for m in metrics:
            w.writerow({k: m[k] for k in keys})

    # ranking
    ranking = sorted(ENGINES, key=lambda e: scores[e]["TOTAL"], reverse=True)

    # markdown report
    lines = ["# Voice humanness analysis\n",
             "Objective proxy metrics over the same script. Higher = more human-like.\n",
             "## Ranking (composite humanness)\n"]
    for i, e in enumerate(ranking, 1):
        lines.append(f"{i}. **{e}** — {scores[e]['TOTAL']:.1f}/100")
    lines.append("\n## Per-criterion scores (0–1)\n")
    crit = ["intonation", "pitch_range", "energy", "phrasing", "voicing", "timbre", "TOTAL"]
    lines.append("| engine | " + " | ".join(crit) + " |")
    lines.append("|" + "---|" * (len(crit) + 1))
    for e in ranking:
        row = [f"{scores[e][c]:.2f}" if c != "TOTAL" else f"{scores[e][c]:.1f}" for c in crit]
        lines.append(f"| {e} | " + " | ".join(row) + " |")
    lines.append("\n## Raw measurements\n")
    show = ["f0_mean_hz", "f0_std_hz", "f0_range_hz", "f0_semitone_std",
            "energy_dyn_db", "pause_rate_per_s", "voiced_ratio", "centroid_hz", "duration_s"]
    lines.append("| engine | " + " | ".join(show) + " |")
    lines.append("|" + "---|" * (len(show) + 1))
    for m in metrics:
        row = [f"{m[k]:.1f}" if abs(m[k]) >= 10 else f"{m[k]:.2f}" for k in show]
        lines.append(f"| {m['engine']} | " + " | ".join(row) + " |")
    report = "\n".join(lines) + "\n"
    with open(os.path.join(ANA_DIR, "REPORT.md"), "w") as f:
        f.write(report)
    print(report)
    print("Wrote PNGs, metrics.csv, REPORT.md to", ANA_DIR)


if __name__ == "__main__":
    main()
