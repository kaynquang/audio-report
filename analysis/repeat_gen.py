"""Critique #2: chạy lặp nhiều lần để đo dao động run-to-run (mean ± std UTMOS).
Ngẫu nhiên (chatterbox/styletts2/f5/index) 5×; deterministic (kokoro/gemini) 2×."""
import os, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs_rep"); os.makedirs(OUT, exist_ok=True)
S = "Welcome to the course. I hope you enjoy learning with us today."
open(f"{OUT}/_s.txt", "w").write(S + "\n")
ENV = dict(os.environ, PATH="/opt/homebrew/bin:" + os.environ.get("PATH", ""),
           PHONEMIZER_ESPEAK_LIBRARY="/opt/homebrew/lib/libespeak-ng.dylib")
def run(cmd): subprocess.run(cmd, env=ENV, capture_output=True)

V = f"{ROOT}/.venv/bin/python"; VF5 = f"{ROOT}/.venv_f5/bin/f5-tts_infer-cli"
VS = f"{ROOT}/.venv_style/bin/python"; VI = f"{ROOT}/external/index-tts/.venv/bin/python"
REF = f"{ROOT}/refs/neil.wav"; TXT = f"{OUT}/_s.txt"

def gen(engine, i):
    o = f"{OUT}/{engine}_{i}.wav"
    if engine == "kokoro":
        run([V, "-m", "athena_tts", "--engine", "kokoro", "--kokoro-voice", "af_heart", "--text", S, "--out", o])
    elif engine == "litellm":
        run([V, "-m", "athena_tts", "--engine", "litellm", "--litellm-voice", "Kore", "--text", S, "--out", o])
    elif engine == "chatterbox":
        run([V, "-m", "athena_tts", "--engine", "chatterbox", "--device", "cpu", "--speaker-reference", REF, "--text", S, "--out", o])
    elif engine == "styletts2":
        run([VS, f"{ROOT}/external/StyleTTS2/infer.py", "--text-file", TXT, "--output", o, "--speaker-reference", REF, "--device", "cpu"])
    elif engine == "f5":
        run([VF5, "--model", "F5TTS_v1_Base", "--ref_audio", REF, "--ref_text", "Ladies and gentlemen, welcome.",
             "--gen_text", S, "--output_dir", OUT, "--output_file", f"{engine}_{i}.wav", "--device", "cpu"])
    elif engine == "index":
        run([VI, "-m", "athena_tts", "--engine", "index", "--index-repo", f"{ROOT}/external/index-tts",
             "--index-model-dir", f"{ROOT}/external/index-tts/checkpoints",
             "--index-cfg", f"{ROOT}/external/index-tts/checkpoints/config.yaml",
             "--speaker-reference", REF, "--device", "cpu", "--text", S, "--out", o])

PLAN = {"kokoro": 2, "litellm": 2, "chatterbox": 5, "styletts2": 5, "f5": 5, "index": 5}
for engine, n in PLAN.items():
    for i in range(1, n + 1):
        gen(engine, i)
        print(f"{engine}_{i} done", flush=True)
print("ALL_REP_DONE", flush=True)
