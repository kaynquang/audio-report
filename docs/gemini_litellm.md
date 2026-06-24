# Hướng dẫn: Gemini 2.5 Pro TTS qua LiteLLM

> Cài & dùng **Gemini 2.5 Pro TTS** thông qua proxy **LiteLLM** của Athena.
> Cập nhật: 24/06/2026. Mọi số liệu có nguồn ở cuối file để cross-check.

## 0. Yêu cầu
- **API key** của LiteLLM proxy (xin từ admin Athena).
- **Base URL:** `https://litellm.athena.tools` (proxy chạy LiteLLM, Swagger UI ở `/`).
- **Model:** `gemini-2.5-pro-preview-tts` (là model duy nhất proxy đang expose, kiểm bằng `GET /v1/models`).
- Python 3.10+ (chỉ cần `urllib` chuẩn + `certifi`; không cần SDK riêng).

Đặt key vào biến môi trường (hoặc file `.env`, **không commit**):
```bash
export LITELLM_API_KEY=sk-...
```

## 1. Cách 1 — Đơn giọng (chuẩn OpenAI `/audio/speech`)

**curl:**
```bash
curl https://litellm.athena.tools/v1/audio/speech \
  -H "Authorization: Bearer $LITELLM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"gemini-2.5-pro-preview-tts","input":"Welcome to the course.","voice":"Kore","response_format":"wav"}' \
  --output out.wav
```

**Python (có xử lý SSL + Cloudflare — xem mục Lưu ý):**
```python
import os, json, ssl, urllib.request, certifi

key = os.environ["LITELLM_API_KEY"]
ctx = ssl.create_default_context(cafile=certifi.where())
req = urllib.request.Request(
    "https://litellm.athena.tools/v1/audio/speech",
    data=json.dumps({
        "model": "gemini-2.5-pro-preview-tts",
        "input": "Welcome to the course.",
        "voice": "Kore",
        "response_format": "wav",
    }).encode(),
    headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",   # tránh Cloudflare 1010
    }, method="POST")
open("out.wav", "wb").write(urllib.request.urlopen(req, context=ctx).read())
```

Trong repo này: `python -m athena_tts --engine litellm --litellm-voice Kore --text "..." --out out.wav`.

## 2. Cách 2 — Điều khiển cảm xúc / phong cách (qua prompt)
Gemini điều khiển bằng **mô tả ngôn ngữ tự nhiên** ngay trong `input` — model đổi cách đọc, KHÔNG đọc câu lệnh ra tiếng (đã verify bằng transcribe):
```json
{"input": "Say cheerfully: Welcome to the course.", "voice": "Kore", ...}
{"input": "Say in a sad, somber tone: ...", ...}
```
Cũng hỗ trợ inline audio tag như `[whispers]`, `[laughs]` (theo docs Google).

## 3. Cách 3 — Multi-speaker (2 giọng trong 1 lần sinh)
**KHÔNG dùng `/audio/speech`** (field multi-speaker bị bỏ qua). Phải qua `/v1/chat/completions`,
format **`pcm16`**, truyền config qua `extra_body.generationConfig.speechConfig.multiSpeakerVoiceConfig`.
Audio trả về **base64 PCM16** trong JSON → decode thành wav 24 kHz.

```python
import os, json, ssl, base64, urllib.request, certifi
import numpy as np, soundfile as sf

key = os.environ["LITELLM_API_KEY"]
ctx = ssl.create_default_context(cafile=certifi.where())
dialogue = "Host: Welcome to the course, everyone.\nGuest: Thanks for having me."
body = {
    "model": "gemini-2.5-pro-preview-tts",
    "messages": [{"role": "user", "content": dialogue}],
    "modalities": ["audio"],
    "audio": {"format": "pcm16"},
    "extra_body": {"generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {
        "multiSpeakerVoiceConfig": {"speakerVoiceConfigs": [
            {"speaker": "Host",  "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Kore"}}},
            {"speaker": "Guest", "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Puck"}}},
        ]}}}},
}
req = urllib.request.Request("https://litellm.athena.tools/v1/chat/completions",
    data=json.dumps(body).encode(),
    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
    method="POST")
resp = json.loads(urllib.request.urlopen(req, context=ctx).read())
pcm = np.frombuffer(base64.b64decode(resp["choices"][0]["message"]["audio"]["data"]), dtype=np.int16)
sf.write("dialogue.wav", pcm, 24000)
```
Giới hạn: **tối đa 2 người nói**.

## 4. Giọng (voice)
~**30 giọng preset**, vd: `Kore` (firm), `Puck` (upbeat), `Zephyr` (bright), `Enceladus` (breathy), `Sulafat` (warm)… Chọn qua `voice` (Cách 1/2) hoặc `voiceName` (Cách 3). **Không clone** giọng tùy ý.

## 5. Lưu ý quan trọng (đã test thực tế)
- **SSL:** Python.org trên macOS thiếu CA → dùng `certifi` (`cafile=certifi.where()`), nếu không sẽ `CERTIFICATE_VERIFY_FAILED`.
- **Cloudflare:** thiếu User-Agent → bị chặn `403 error 1010`. Thêm `User-Agent: Mozilla/5.0`.
- **Format:** `/audio/speech` nhận `wav`; `/v1/chat/completions` **chỉ nhận `pcm16`** (trả base64).
- **`speed` và `temperature`: BỊ BỎ QUA** qua proxy (output không đổi). Muốn đổi tốc độ → time-stretch hậu kỳ (ffmpeg `atempo`).
- Output: PCM 24 kHz.

## 6. Chi phí
| Model | Input (text) | Output (audio) |
|---|---|---|
| gemini-2.5-pro-preview-tts | $1.00 / 1M token | **$20.00 / 1M token** |
| gemini-2.5-flash-preview-tts | $0.50 / 1M token | $10.00 / 1M token |

Audio output là phần tốn chính. Ví dụ research này: ~789 ký tự input → 56s audio ≈ vài cent.

## 7. Nguồn (cross-check)
- Gemini speech generation: https://ai.google.dev/gemini-api/docs/speech-generation
- Gemini API pricing: https://ai.google.dev/gemini-api/docs/pricing
- LiteLLM text-to-speech: https://docs.litellm.ai/docs/text_to_speech
- LiteLLM repo: https://github.com/BerriAI/litellm
- Proxy (Swagger UI): https://litellm.athena.tools/
