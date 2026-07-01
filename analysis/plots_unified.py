"""Sinh lại TẤT CẢ biểu đồ demo theo một chuẩn thống nhất để không gây nhiễu:
- cùng thứ tự & màu cho mỗi engine ở mọi biểu đồ
- giọng tham chiếu (giọng gốc / clip ref) luôn màu đen
- cùng font/cỡ chữ/lưới/DPI, tiêu đề & nhãn trục tiếng Việt nhất quán
- biểu đồ sóng và cao độ dùng CHUNG bố cục (mỗi engine một hàng) — bỏ kiểu chồng rối
- mọi con số "độ giống" đều quy về clip ref neil (đồng bộ với phần nghe)
"""
from __future__ import annotations
import os, csv
import numpy as np
import librosa
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANA = os.path.join(ROOT, "analysis")
SR, FMIN, FMAX = 24000, 65.0, 400.0

ORDER = ["kokoro", "chatterbox", "f5", "styletts2", "index"]          # 5 open-source (mục clone)
ORDER_ALL = ORDER + ["litellm"]                                       # + Gemini (mục 1,2,4)
LABEL = {"kokoro": "Kokoro", "chatterbox": "Chatterbox", "f5": "F5-TTS",
         "styletts2": "StyleTTS2", "index": "IndexTTS2", "litellm": "Gemini (LiteLLM)"}
COLORS = {"kokoro": "#1f77b4", "chatterbox": "#ff7f0e", "f5": "#2ca02c",
          "styletts2": "#d62728", "index": "#9467bd", "litellm": "#17becf"}
REF = "#111111"

# số liệu (đồng bộ, lấy từ các phép đo trước)
SIM_NEIL = {"index": 0.951, "f5": 0.876, "chatterbox": 0.873, "styletts2": 0.797,
            "kokoro": 0.517, "litellm": 0.598}
HUMAN = {"litellm": 4.51, "styletts2": 4.55, "index": 4.10, "kokoro": 4.54, "chatterbox": 4.57, "f5": 4.00}  # UTMOS 1-5

plt.rcParams.update({
    "figure.facecolor": "white", "savefig.facecolor": "white", "savefig.dpi": 120,
    "savefig.bbox": "tight", "font.size": 11, "axes.titlesize": 13,
    "axes.titleweight": "bold", "axes.labelsize": 11,
    "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False,
    "font.family": ["Helvetica Neue", "Arial", "DejaVu Sans"],
})


def load(path):
    y, _ = librosa.load(path, sr=SR, mono=True)
    return y


def f0(y):
    f, _, _ = librosa.pyin(y, fmin=FMIN, fmax=FMAX, sr=SR, frame_length=2048, hop_length=256)
    t = librosa.times_like(f, sr=SR, hop_length=256)
    return t, f


def stack_waveforms(rows, title, out, xmax=None):
    """rows = [(label, path, color, is_ref)] -> mỗi hàng 1 sóng, bố cục thống nhất."""
    ys = [(lab, load(p), c, r) for lab, p, c, r in rows]
    xmax = xmax or max(len(y) / SR for _, y, _, _ in ys)
    n = len(ys)
    fig, axes = plt.subplots(n, 1, figsize=(11, 1.35 * n), sharex=True)
    if n == 1:
        axes = [axes]
    for ax, (lab, y, c, isref) in zip(axes, ys):
        t = np.linspace(0, len(y) / SR, len(y))
        ax.plot(t, y, color=c, lw=0.5)
        ax.set_ylim(-1, 1); ax.set_yticks([]); ax.set_xlim(0, xmax); ax.grid(False)
        ax.set_ylabel(lab, rotation=0, ha="right", va="center", fontsize=11,
                      fontweight="bold" if isref else "normal", color=c)
    axes[-1].set_xlabel("Thời gian (giây)")
    fig.suptitle(title, fontsize=13, fontweight="bold")
    fig.savefig(os.path.join(ANA, out)); plt.close(fig)


def stack_pitch(rows, title, out, xmax=None):
    """Cao độ F0 — CÙNG bố cục mỗi engine một hàng (thay cho kiểu chồng rối)."""
    data = [(lab, *f0(load(p)), c, r) for lab, p, c, r in rows]
    xmax = xmax or max(t[-1] for _, t, _, _, _ in data)
    n = len(data)
    fig, axes = plt.subplots(n, 1, figsize=(11, 1.35 * n), sharex=True, sharey=True)
    if n == 1:
        axes = [axes]
    for ax, (lab, t, ff, c, isref) in zip(axes, data):
        ax.plot(t, ff, color=c, lw=1.3)
        ax.set_ylim(80, 340); ax.set_xlim(0, xmax)
        ax.set_yticks([100, 200, 300])
        ax.set_ylabel(lab, rotation=0, ha="right", va="center", fontsize=11,
                      fontweight="bold" if isref else "normal", color=c)
    axes[-1].set_xlabel("Thời gian (giây)")
    fig.text(0.005, 0.5, "Cao độ F0 (Hz)", va="center", rotation="vertical", fontsize=11)
    fig.suptitle(title, fontsize=13, fontweight="bold")
    fig.savefig(os.path.join(ANA, out)); plt.close(fig)


def bar(values, title, ylab, out, ref_line=None, ref_label="", ylim=None, fmt="{:.3f}"):
    names = [LABEL[e] for e in ORDER]
    vals = [values[e] for e in ORDER]
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(names, vals, color=[COLORS[e] for e in ORDER])
    for i, v in enumerate(vals):
        ax.text(i, v, " " + fmt.format(v), ha="center", va="bottom", fontsize=10)
    if ref_line is not None:
        ax.axhline(ref_line, ls="--", color=REF, lw=1.4)
        ax.text(len(names) - 0.5, ref_line, f" {ref_label}", color=REF, va="bottom",
                ha="right", fontsize=9)
    ax.set_ylabel(ylab); ax.set_title(title)
    if ylim:
        ax.set_ylim(*ylim)
    ax.grid(axis="x", visible=False)
    fig.savefig(os.path.join(ANA, out)); plt.close(fig)


def metrics_vs_original(out):
    rows = {}
    with open(os.path.join(ANA, "metrics.csv")) as f:
        for r in csv.DictReader(f):
            rows[r["engine"]] = r
    METRICS = [("f0_mean_hz", "Cao độ TB (Hz)"), ("f0_semitone_std", "Dao động cao độ (st)"),
               ("f0_range_hz", "Khoảng cao độ (Hz)"), ("voiced_ratio", "Tỉ lệ có thanh"),
               ("centroid_hz", "Trọng tâm phổ (Hz)")]
    fig, axes = plt.subplots(1, len(METRICS), figsize=(15, 4.2))
    for ax, (k, lab) in zip(axes, METRICS):
        ov = float(rows["original"][k])
        vals = [float(rows[e][k]) for e in ORDER_ALL]
        ax.bar([LABEL[e] for e in ORDER_ALL], vals, color=[COLORS[e] for e in ORDER_ALL])
        ax.axhline(ov, ls="--", color=REF, lw=1.5)
        ax.set_title(lab, fontsize=11)
        ax.tick_params(axis="x", rotation=90, labelsize=8)
        ax.grid(axis="x", visible=False)
    fig.suptitle("Chỉ số mỗi engine vs GIỌNG GỐC (đường đứt đen)", fontsize=13, fontweight="bold")
    fig.savefig(os.path.join(ANA, out)); plt.close(fig)


def scatter(out):
    fig, ax = plt.subplots(figsize=(9, 6))
    for e in ORDER_ALL:
        x, y = SIM_NEIL[e], HUMAN[e]
        ax.scatter(x, y, s=190, color=COLORS[e], edgecolor=REF, lw=1.2, zorder=3)
        ax.annotate(LABEL[e], (x, y), textcoords="offset points", xytext=(9, 6), fontsize=11)
    ax.set_xlabel("Độ giống clip ref neil  (cosine →)")
    ax.set_ylabel("UTMOS — độ tự nhiên (1–5 →)")
    ax.set_title("Tổng hợp: độ giống giọng vs độ tự nhiên")
    ax.text(0.02, 0.03, "góc trên-phải = lý tưởng (vừa giống vừa tự nhiên)",
            transform=ax.transAxes, fontsize=9, color="#777")
    fig.savefig(os.path.join(ANA, out)); plt.close(fig)


def main():
    # 1) sóng kịch bản 1: giọng gốc + 5 engine
    rows1 = [("Giọng gốc", os.path.join(ROOT, "refs/original_voice.wav"), REF, True)] + \
            [(LABEL[e], os.path.join(ROOT, f"outputs/{e}.wav"), COLORS[e], False) for e in ORDER_ALL]
    stack_waveforms(rows1, "Sóng âm — kịch bản 1 (giọng gốc + 6 engine)", "compare_waveforms.png")
    stack_pitch(rows1, "Cao độ F0 — kịch bản 1 (giọng gốc + 6 engine)", "compare_pitch.png")

    # 2) clip ref neil + 5 engine (cùng câu)
    rowsr = [("Clip ref (neil)", os.path.join(ROOT, "refs/neil.wav"), REF, True)] + \
            [(LABEL[e], os.path.join(ROOT, f"outputs4/{e}.wav"), COLORS[e], False) for e in ORDER]
    stack_waveforms(rowsr, "Sóng âm — clip ref vs 5 engine (cùng câu)", "compare_refline_waveforms.png")

    # 3) sóng kịch bản 1 vs 2 (mỗi engine 2 cột) — giữ bố cục, đồng bộ style
    fig, axes = plt.subplots(len(ORDER), 2, figsize=(12, 1.5 * len(ORDER)), sharex=True)
    maxd = max(len(load(os.path.join(ROOT, d, f"{e}.wav"))) / SR
               for d in ("outputs", "outputs2") for e in ORDER)
    for i, e in enumerate(ORDER):
        for j, (d, lab) in enumerate([("outputs", "Kịch bản 1"), ("outputs2", "Kịch bản 2")]):
            y = load(os.path.join(ROOT, d, f"{e}.wav"))
            t = np.linspace(0, len(y) / SR, len(y))
            axes[i, j].plot(t, y, color=COLORS[e], lw=0.5)
            axes[i, j].set_ylim(-1, 1); axes[i, j].set_yticks([]); axes[i, j].set_xlim(0, maxd)
            axes[i, j].grid(False)
            if i == 0:
                axes[i, j].set_title(lab, fontsize=12)
        axes[i, 0].set_ylabel(LABEL[e], rotation=0, ha="right", va="center", color=COLORS[e])
    axes[-1, 0].set_xlabel("Thời gian (giây)"); axes[-1, 1].set_xlabel("Thời gian (giây)")
    fig.suptitle("Sóng âm — Kịch bản 1 vs Kịch bản 2", fontsize=13, fontweight="bold")
    fig.savefig(os.path.join(ANA, "compare_scripts_waveforms.png")); plt.close(fig)

    # 4) chỉ số vs giọng gốc
    metrics_vs_original("compare_to_original.png")

    # 5) độ giống clip ref neil
    bar(SIM_NEIL, "Độ giống clip ref neil (đọc cùng câu)",
        "Cosine similarity (0–1, càng cao càng giống)", "similarity_refline_chart.png",
        ylim=(0, 1), fmt="{:.3f}")

    # 6) tổng hợp giống vs tự nhiên
    scatter("tradeoff_scatter.png")
    print("Đã sinh lại 7 biểu đồ theo chuẩn thống nhất.")


if __name__ == "__main__":
    main()
