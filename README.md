# Athena TTS

Athena TTS is a small voice consistency harness for running the same script through multiple open-source TTS engines:

- [hexgrad/kokoro](https://github.com/hexgrad/kokoro)
- [resemble-ai/chatterbox](https://github.com/resemble-ai/chatterbox)
- [index-tts/index-tts](https://github.com/index-tts/index-tts)
- [SWivid/F5-TTS](https://github.com/SWivid/F5-TTS)
- [yl4579/StyleTTS2](https://github.com/yl4579/StyleTTS2)

The runner keeps model dependencies lazy. Install only the engine you want to test, then run the same text through it.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

python3 -m athena_tts --list-engines
python3 -m athena_tts --engine kokoro --out outputs/kokoro.wav
```

The default script is stored at [scripts/voice_consistency_test.txt](scripts/voice_consistency_test.txt).

## Engine Setup

Kokoro:

```bash
pip install "kokoro>=0.9.4" soundfile numpy
# macOS: brew install espeak-ng
# Debian/Ubuntu: sudo apt-get install espeak-ng
python3 -m athena_tts --engine kokoro --kokoro-voice af_heart --out outputs/kokoro.wav
```

Chatterbox:

```bash
pip install chatterbox-tts torchaudio
python3 -m athena_tts --engine chatterbox --device auto --out outputs/chatterbox.wav
```

F5-TTS requires a speaker reference clip and transcript:

```bash
pip install f5-tts
python3 -m athena_tts \
  --engine f5 \
  --speaker-reference refs/speaker.wav \
  --reference-text "Transcript of the reference clip." \
  --out outputs/f5.wav
```

IndexTTS2 is normally run from a local checkout with checkpoints:

```bash
git clone https://github.com/index-tts/index-tts.git external/index-tts
cd external/index-tts
uv sync --all-extras
uv tool install "huggingface-hub[cli,hf_xet]"
hf download IndexTeam/IndexTTS-2 --local-dir=checkpoints
cd ../..

PYTHONPATH=external/index-tts python3 -m athena_tts \
  --engine index \
  --index-repo external/index-tts \
  --index-model-dir external/index-tts/checkpoints \
  --index-cfg external/index-tts/checkpoints/config.yaml \
  --speaker-reference refs/speaker.wav \
  --out outputs/index.wav
```

StyleTTS2 does not expose a stable package CLI in the official repository; its upstream inference path is notebook-based. Athena supports it through a command template so you can point at a local StyleTTS2 inference script after you export or create one from the notebook:

```bash
python3 -m athena_tts \
  --engine styletts2 \
  --styletts2-command "python external/StyleTTS2/infer.py --text-file {text_file} --output {output} --device {device}" \
  --out outputs/styletts2.wav
```

Template variables: `{text}`, `{text_file}`, `{output}`, `{device}`, `{speaker_reference}`, `{reference_text}`.

## Run All Available Engines

```bash
python3 -m athena_tts \
  --engine all \
  --speaker-reference refs/speaker.wav \
  --reference-text "Transcript of the reference clip." \
  --styletts2-command "python external/StyleTTS2/infer.py --text-file {text_file} --output {output}" \
  --out-dir outputs
```

Engines fail independently in `all` mode, so one missing dependency does not stop the others.
# audio-report
