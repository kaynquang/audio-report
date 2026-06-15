"""Biến output TTS thành "giọng bụng" (chest/diaphragm voice): trầm hơn, đầy hơn,
cộng hưởng ngực nhiều hơn.

Cơ chế:
  1. Hạ FORMANT (Praat "Change gender", formant_shift < 1) -> giả lập khoang
     ngực/thanh quản LỚN hơn => giọng dày, "to con" hơn.
  2. Hạ cao độ trung bình (new pitch median thấp) => trầm.
  3. Low-shelf EQ +dB ở tần số thấp => ấm, cộng hưởng ngực.
"""
from __future__ import annotations
import os, sys
import numpy as np
import soundfile as sf
import parselmouth
from parselmouth.praat import call
from scipy.signal import lfilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def low_shelf(x, sr, f0=180.0, gain_db=5.0):
    """RBJ low-shelf: tăng năng lượng dưới f0 để thêm 'ngực'."""
    A = 10 ** (gain_db / 40.0)
    w0 = 2 * np.pi * f0 / sr
    cw, sw = np.cos(w0), np.sin(w0)
    alpha = sw / 2 * np.sqrt((A + 1 / A) * (1 / 0.9 - 1) + 2)
    sa = 2 * np.sqrt(A) * alpha
    b0 = A * ((A + 1) - (A - 1) * cw + sa)
    b1 = 2 * A * ((A - 1) - (A + 1) * cw)
    b2 = A * ((A + 1) - (A - 1) * cw - sa)
    a0 = (A + 1) + (A - 1) * cw + sa
    a1 = -2 * ((A - 1) + (A + 1) * cw)
    a2 = (A + 1) + (A - 1) * cw - sa
    return lfilter([b0 / a0, b1 / a0, b2 / a0], [1, a1 / a0, a2 / a0], x)


def belly(in_path, out_path, formant_shift=0.85, pitch_median=115.0,
          pitch_range=0.8, duration=1.04, shelf_db=5.0):
    snd = parselmouth.Sound(in_path)
    # Change gender: min_pitch, max_pitch, formant_shift_ratio, new_pitch_median,
    #                pitch_range_factor, duration_factor
    out = call(snd, "Change gender", 60, 500, formant_shift, pitch_median,
               pitch_range, duration)
    sr = int(out.sampling_frequency)
    y = np.asarray(out.values).mean(axis=0).astype(np.float64)
    y = low_shelf(y, sr, f0=180.0, gain_db=shelf_db)
    peak = np.max(np.abs(y)) + 1e-9
    y = (y / peak * 0.97).astype(np.float32)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    sf.write(out_path, y, sr)
    return sr, len(y) / sr


if __name__ == "__main__":
    jobs = sys.argv[1:] or ["outputs/styletts2.wav", "outputs/index.wav"]
    for src in jobs:
        name = os.path.splitext(os.path.basename(src))[0]
        dst = os.path.join(ROOT, "outputs_belly", f"{name}_belly.wav")
        sr, dur = belly(os.path.join(ROOT, src), dst)
        print(f"{src} -> {dst}  ({dur:.1f}s, {sr}Hz)")
