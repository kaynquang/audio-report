#!/bin/zsh
# Measure generation time (model load + inference, models already cached) for each
# engine, sequentially so there is no CPU contention. Writes analysis/timings.csv.
cd /Users/Brian/Desktop/Athena_TTS
export PATH="/opt/homebrew/bin:$PATH"
CSV=analysis/timings.csv
echo "engine,seconds" > $CSV
TMP=analysis/_timing_out
mkdir -p $TMP

run() {  # name, command...
  local name=$1; shift
  local start=$(python3 -c 'import time;print(time.time())')
  "$@" > $TMP/$name.log 2>&1
  local rc=$?
  local end=$(python3 -c 'import time;print(time.time())')
  local dt=$(python3 -c "print(f'{$end-$start:.1f}')")
  echo "$name,$dt" >> $CSV
  echo "[$name] ${dt}s (rc=$rc)"
}

run kokoro .venv/bin/python -m athena_tts --engine kokoro --kokoro-voice af_heart --out $TMP/kokoro.wav

run chatterbox .venv/bin/python -m athena_tts --engine chatterbox --device cpu \
  --speaker-reference refs/speaker.wav --out $TMP/chatterbox.wav

run styletts2 env PHONEMIZER_ESPEAK_LIBRARY=/opt/homebrew/lib/libespeak-ng.dylib \
  .venv_style/bin/python external/StyleTTS2/infer.py \
  --text-file $PWD/scripts/voice_consistency_test.txt \
  --output $PWD/$TMP/styletts2.wav --speaker-reference $PWD/refs/speaker.wav --device cpu

run f5 .venv_f5/bin/f5-tts_infer-cli --model F5TTS_v1_Base \
  --ref_audio refs/speaker.wav --ref_text "$(cat refs/speaker_ref_text.txt)" \
  --gen_file scripts/voice_consistency_test.txt \
  --output_dir $TMP --output_file f5.wav --device cpu

# index uses its own venv via athena
run index env PATH="/opt/homebrew/bin:$PATH" external/index-tts/.venv/bin/python -m athena_tts \
  --engine index --index-repo external/index-tts \
  --index-model-dir external/index-tts/checkpoints \
  --index-cfg external/index-tts/checkpoints/config.yaml \
  --speaker-reference refs/speaker.wav --device cpu --out $TMP/index.wav

echo "DONE"
cat $CSV
