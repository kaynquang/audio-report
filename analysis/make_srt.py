"""Xuất .srt CHUẨN HOÁ từ audio đã render (faster-whisper word-level + gom cue đều).
Quy tắc cue: ≤ MAX_WORDS từ, ≤ MAX_CHARS ký tự, ≤ MAX_DUR giây, ưu tiên ngắt ở dấu câu."""
from __future__ import annotations
import os, re
from faster_whisper import WhisperModel

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs5")
SRT_DIR = os.path.join(ROOT, "outputs5_srt")
os.makedirs(SRT_DIR, exist_ok=True)
ENG = ["kokoro", "chatterbox", "f5", "styletts2", "index"]
SCRIPT = open(os.path.join(ROOT, "scripts/harvard_intro.txt")).read().strip()

MAX_WORDS, MAX_CHARS, MAX_DUR = 8, 42, 5.0


def ts(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = int(t % 60); ms = int(round((t - int(t)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def norm(s):
    return re.sub(r"[^a-z0-9 ]", "", s.lower()).split()


def wer(ref, hyp):
    r, h = norm(ref), norm(hyp)
    d = [[0] * (len(h) + 1) for _ in range(len(r) + 1)]
    for i in range(len(r) + 1): d[i][0] = i
    for j in range(len(h) + 1): d[0][j] = j
    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            d[i][j] = min(d[i-1][j] + 1, d[i][j-1] + 1, d[i-1][j-1] + (r[i-1] != h[j-1]))
    return d[len(r)][len(h)] / max(1, len(r))


def chunk(words):
    """Gom list từ (mỗi từ có .start/.end/.word) thành các cue đều."""
    cues, cur = [], []
    for w in words:
        cur.append(w)
        text = "".join(x.word for x in cur).strip()
        dur = cur[-1].end - cur[0].start
        ends_sent = w.word.strip().endswith((".", "?", "!"))
        ends_clause = w.word.strip().endswith((",", ";", ":"))
        if ((ends_sent and len(cur) >= 3)
                or (ends_clause and (len(cur) >= 6 or len(text) >= 32))
                or len(cur) >= MAX_WORDS or len(text) >= MAX_CHARS or dur >= MAX_DUR):
            cues.append(cur); cur = []
    if cur:
        cues.append(cur)
    return cues


model = WhisperModel("mobiuslabsgmbh/faster-whisper-large-v3-turbo", device="cpu", compute_type="int8")

print(f"{'engine':<11}{'cues':<6}{'từ/cue':<8}{'dur(s)':<9}{'WER':<8}")
print("-" * 42)
rows = []
for e in ENG:
    audio = os.path.join(OUT, f"{e}.wav")
    if not os.path.exists(audio):
        continue
    segs, _ = model.transcribe(audio, language="en", word_timestamps=True)
    words = [w for s in segs for w in (s.words or []) if w.start is not None]
    cues = chunk(words)
    lines = []
    for i, c in enumerate(cues, 1):
        txt = "".join(w.word for w in c).strip()
        lines.append(f"{i}\n{ts(c[0].start)} --> {ts(c[-1].end)}\n{txt}\n")
    open(os.path.join(SRT_DIR, f"{e}.srt"), "w").write("\n".join(lines))
    hyp = " ".join(w.word.strip() for w in words)
    avg = sum(len(c) for c in cues) / max(1, len(cues))
    dur = words[-1].end if words else 0
    w_ = wer(SCRIPT, hyp)
    rows.append((e, len(cues), avg, dur, w_))
    print(f"{e:<11}{len(cues):<6}{avg:<8.1f}{dur:<9.1f}{w_*100:<7.1f}%")

best = min(rows, key=lambda r: r[4])[0] if rows else None
for show in [best, "styletts2"]:
    if show:
        print(f"\n===== {show}.srt (sau chuẩn hoá cue) =====")
        print(open(os.path.join(SRT_DIR, f"{show}.srt")).read())
print("SRT ->", SRT_DIR)
