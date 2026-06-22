"""Demo điều khiển thời lượng CHO TỪNG MODEL: cùng 1 câu -> gốc + ép 2s + ép 4s.
- Kokoro: native `speed`
- F5-TTS: native `--fix_duration`
- StyleTTS2 / IndexTTS2 / Chatterbox: time-stretch hậu kỳ (ffmpeg atempo)
Ghi ra outputs_dur/{engine}_{base,2s,4s}.wav
"""
import os, subprocess, soundfile as sf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs_dur")
os.makedirs(OUT, exist_ok=True)
SENT = "Welcome to this Harvard introductory course."
TARGETS = [2.0, 4.0]
ENV = dict(os.environ, PATH="/opt/homebrew/bin:" + os.environ.get("PATH", ""),
           PHONEMIZER_ESPEAK_LIBRARY="/opt/homebrew/lib/libespeak-ng.dylib")


def dur(p):
    return sf.info(p).duration


def atempo(src, dst, target):
    f = dur(src) / target
    # atempo chỉ nhận 0.5–2.0; chain nếu vượt
    facs = []
    while f > 2.0:
        facs.append(2.0); f /= 2.0
    while f < 0.5:
        facs.append(0.5); f /= 0.5
    facs.append(round(f, 4))
    chain = ",".join(f"atempo={x}" for x in facs)
    subprocess.run(["ffmpeg", "-y", "-i", src, "-filter:a", chain, dst],
                   env=ENV, capture_output=True)


def run(cmd):
    subprocess.run(cmd, env=ENV, capture_output=True)


def kokoro():
    base = f"{OUT}/kokoro_base.wav"
    run([f"{ROOT}/.venv/bin/python", "-m", "athena_tts", "--engine", "kokoro",
         "--kokoro-voice", "af_heart", "--text", SENT, "--out", base])
    n = dur(base)
    for t in TARGETS:
        run([f"{ROOT}/.venv/bin/python", "-m", "athena_tts", "--engine", "kokoro",
             "--kokoro-voice", "af_heart", "--speed", str(round(n / t, 3)),
             "--text", SENT, "--out", f"{OUT}/kokoro_{int(t)}s.wav"])
    print("kokoro done (native speed)")


def f5():
    cli = f"{ROOT}/.venv_f5/bin/f5-tts_infer-cli"
    base = f"{OUT}/f5_base.wav"
    run([cli, "--model", "F5TTS_v1_Base", "--ref_audio", f"{ROOT}/refs/neil.wav",
         "--ref_text", "Ladies and gentlemen, welcome.", "--gen_text", SENT,
         "--output_dir", OUT, "--output_file", "f5_base.wav", "--device", "cpu"])
    for t in TARGETS:
        run([cli, "--model", "F5TTS_v1_Base", "--ref_audio", f"{ROOT}/refs/neil.wav",
             "--ref_text", "Ladies and gentlemen, welcome.", "--gen_text", SENT,
             "--output_dir", OUT, "--output_file", f"f5_{int(t)}s.wav",
             "--device", "cpu", "--fix_duration", str(t)])
    print("f5 done (native fix_duration)")


def stretch_engine(name, gen_base):
    base = f"{OUT}/{name}_base.wav"
    gen_base(base)
    for t in TARGETS:
        atempo(base, f"{OUT}/{name}_{int(t)}s.wav", t)
    print(f"{name} done (atempo)")


def styletts2_base(base):
    run([f"{ROOT}/.venv_style/bin/python", f"{ROOT}/external/StyleTTS2/infer.py",
         "--text-file", _tmp_text(), "--output", base,
         "--speaker-reference", f"{ROOT}/refs/neil.wav", "--device", "cpu"])


def index_base(base):
    run([f"{ROOT}/external/index-tts/.venv/bin/python", "-m", "athena_tts", "--engine", "index",
         "--index-repo", f"{ROOT}/external/index-tts",
         "--index-model-dir", f"{ROOT}/external/index-tts/checkpoints",
         "--index-cfg", f"{ROOT}/external/index-tts/checkpoints/config.yaml",
         "--speaker-reference", f"{ROOT}/refs/neil.wav", "--device", "cpu",
         "--text", SENT, "--out", base])


def chatterbox_base(base):
    run([f"{ROOT}/.venv/bin/python", "-m", "athena_tts", "--engine", "chatterbox",
         "--device", "cpu", "--speaker-reference", f"{ROOT}/refs/neil.wav",
         "--text", SENT, "--out", base])


def _tmp_text():
    p = f"{OUT}/_sent.txt"
    open(p, "w").write(SENT + "\n")
    return p


if __name__ == "__main__":
    kokoro()
    stretch_engine("chatterbox", chatterbox_base)
    stretch_engine("styletts2", styletts2_base)
    stretch_engine("index", index_base)
    f5()
    print("\n=== durations ===")
    for e in ["kokoro", "chatterbox", "f5", "styletts2", "index"]:
        row = [e]
        for s in ["base", "2s", "4s"]:
            p = f"{OUT}/{e}_{s}.wav"
            row.append(f"{s}={dur(p):.2f}s" if os.path.exists(p) else f"{s}=NA")
        print("  ".join(row))
