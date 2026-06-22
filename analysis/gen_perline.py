"""Cách 3 — điều khiển thời lượng PER-CÂU: mỗi câu ép về 1 target riêng,
ghép lại thành 1 audio + sinh .srt khớp chính xác từng dòng (cho slide/video)."""
import os, re, subprocess
import numpy as np
import soundfile as sf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs_dur")
os.makedirs(OUT, exist_ok=True)
ENV = dict(os.environ, PATH="/opt/homebrew/bin:" + os.environ.get("PATH", ""))
SR, GAP = 24000, 0.30

TEXT = open(os.path.join(ROOT, "scripts/harvard_intro.txt")).read().strip()
SENTS = re.split(r"(?<=[.!?])\s+", TEXT)
TARGETS = [2.5, 6.0, 4.0, 1.5]   # giây mong muốn cho từng câu


def kgen(text, dst):
    subprocess.run([f"{ROOT}/.venv/bin/python", "-m", "athena_tts", "--engine", "kokoro",
                    "--kokoro-voice", "af_heart", "--text", text, "--out", dst],
                   env=ENV, capture_output=True)


def atempo(src, dst, T):
    f = sf.info(src).duration / T
    facs = []
    while f > 2.0:
        facs.append(2.0); f /= 2.0
    while f < 0.5:
        facs.append(0.5); f /= 0.5
    facs.append(round(f, 4))
    subprocess.run(["ffmpeg", "-y", "-i", src, "-filter:a", ",".join(f"atempo={x}" for x in facs), dst],
                   env=ENV, capture_output=True)


def ts(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = int(t % 60); ms = int(round((t - int(t)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


segs, cues, cur, rows = [], [], 0.0, []
for i, (sent, T) in enumerate(zip(SENTS, TARGETS)):
    raw = f"{OUT}/_pl_raw_{i}.wav"
    seg = f"{OUT}/_pl_seg_{i}.wav"
    kgen(sent, raw)
    atempo(raw, seg, T)
    y, _ = sf.read(seg)
    if y.ndim > 1:
        y = y.mean(axis=1)
    d = len(y) / SR
    cues.append((cur, cur + d, sent))
    rows.append((sent, T, d))
    segs.append(y.astype(np.float32))
    cur += d
    if i < len(SENTS) - 1:
        segs.append(np.zeros(int(SR * GAP), dtype=np.float32))
        cur += GAP

audio = np.concatenate(segs)
sf.write(f"{OUT}/perline.wav", audio, SR)
srt = "\n".join(f"{i+1}\n{ts(a)} --> {ts(b)}\n{txt}\n" for i, (a, b, txt) in enumerate(cues))
open(f"{OUT}/perline.srt", "w", encoding="utf-8").write(srt)

print(f"perline.wav = {len(audio)/SR:.2f}s")
for sent, T, d in rows:
    print(f"  target {T:.1f}s -> {d:.2f}s | {sent[:45]}")
print("\n--- perline.srt ---")
print(srt)
