"""Dựng trang demo HTML self-contained trong demo/ để gửi cho team.
Copy audio/ảnh/PDF cần thiết rồi sinh demo/index.html (mở bằng browser, hoặc zip gửi đi)."""
from __future__ import annotations
import os, shutil, html

ROOT = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(ROOT, "demo")
for sub in ("audio", "img", "pdf"):
    os.makedirs(os.path.join(D, sub), exist_ok=True)


def cp(src, dstname, sub):
    s = os.path.join(ROOT, src)
    if os.path.exists(s):
        shutil.copy2(s, os.path.join(D, sub, dstname))
        return True
    return False


ENG = ["kokoro", "chatterbox", "f5", "styletts2", "index"]
LABEL = {"kokoro": "Kokoro", "chatterbox": "Chatterbox", "f5": "F5-TTS",
         "styletts2": "StyleTTS2", "index": "IndexTTS2"}

# ---- copy audio ----
cp("refs/original_voice.wav", "s1_original.wav", "audio")
for e in ENG:
    cp(f"outputs/{e}.wav", f"s1_{e}.wav", "audio")
cp("refs/neil.wav", "ref_neil.wav", "audio")
for e in ENG:
    cp(f"outputs4/{e}.wav", f"rl_{e}.wav", "audio")
for e in ["styletts2", "index", "chatterbox"]:
    cp(f"outputs_belly/{e}_belly.wav", f"belly_{e}.wav", "audio")

# ---- copy images ----
IMGS = ["compare_waveforms.png", "compare_pitch.png", "compare_to_original.png",
        "similarity_chart.png", "tradeoff_scatter.png", "similarity_refline_chart.png",
        "compare_refline_waveforms.png", "compare_scripts_waveforms.png"]
for im in IMGS:
    cp(f"analysis/{im}", im, "img")

# ---- copy pdfs ----
PDFS = [("report_full.pdf", "Báo cáo tổng hợp (chỉ số + similarity)"),
        ("report_clone.pdf", "Báo cáo clone giọng voiceover"),
        ("report.pdf", "Báo cáo so sánh + độ tự nhiên"),
        ("report_similarity.pdf", "Báo cáo similarity")]
for p, _ in PDFS:
    cp(f"analysis/{p}", p, "pdf")


def audio_row(label, fname, note=""):
    p = os.path.join(D, "audio", fname)
    if not os.path.exists(p):
        return ""
    return f"""<tr><td class="lbl">{html.escape(label)}</td>
      <td><audio controls preload="none" src="audio/{fname}"></audio></td>
      <td class="note">{html.escape(note)}</td></tr>"""


def img(name, cap):
    if not os.path.exists(os.path.join(D, "img", name)):
        return ""
    return f"""<figure><img src="img/{name}" alt="{html.escape(cap)}"/>
      <figcaption>{html.escape(cap)}</figcaption></figure>"""


# tables data
human = [("StyleTTS2", 89.6), ("IndexTTS2", 89.5), ("Kokoro", 80.9), ("Chatterbox", 78.4),
         ("Giọng gốc (người)", 51.7), ("F5-TTS", 35.4)]
clone = [("IndexTTS2", 0.951), ("F5-TTS", 0.876), ("Chatterbox", 0.873),
         ("StyleTTS2", 0.797), ("Kokoro (không clone)", 0.517)]
timing = [("Kokoro", 12.7), ("StyleTTS2", 29.5), ("Chatterbox", 38.0),
          ("IndexTTS2", 68.8), ("F5-TTS", 253.7)]


def rows(data, fmt):
    return "\n".join(f"<tr><td>{html.escape(n)}</td><td>{fmt(v)}</td></tr>" for n, v in data)


HTML = f"""<!doctype html>
<html lang="vi"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Athena TTS — Demo</title>
<style>
  :root {{ --bg:#0f1115; --card:#181b22; --fg:#e6e8eb; --mut:#9aa3af; --acc:#6ea8fe; --line:#262b35; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--fg);
    font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }}
  header {{ padding:32px 24px; background:linear-gradient(135deg,#1b2030,#11141b); border-bottom:1px solid var(--line); }}
  h1 {{ margin:0 0 6px; font-size:26px; }}
  h2 {{ margin:34px 0 12px; font-size:20px; border-left:3px solid var(--acc); padding-left:10px; }}
  .sub {{ color:var(--mut); }}
  main {{ max-width:1000px; margin:0 auto; padding:0 24px 60px; }}
  .card {{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:16px 18px; margin:14px 0; }}
  table {{ width:100%; border-collapse:collapse; margin:8px 0; }}
  td,th {{ padding:7px 10px; border-bottom:1px solid var(--line); text-align:left; vertical-align:middle; }}
  th {{ color:var(--mut); font-weight:600; }}
  td.lbl {{ width:190px; font-weight:600; }}
  td.note {{ color:var(--mut); font-size:13px; }}
  audio {{ width:320px; height:34px; }}
  figure {{ margin:14px 0; }}
  img {{ width:100%; border-radius:10px; border:1px solid var(--line); background:#fff; }}
  figcaption {{ color:var(--mut); font-size:13px; margin-top:6px; }}
  a {{ color:var(--acc); }}
  .pill {{ display:inline-block; background:#222836; color:var(--acc); border:1px solid var(--line);
    border-radius:999px; padding:2px 10px; font-size:12px; margin:2px 4px 2px 0; }}
  code {{ background:#222836; padding:1px 6px; border-radius:5px; }}
  .grid2 {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
  @media (max-width:720px) {{ .grid2 {{ grid-template-columns:1fr; }} audio {{ width:100%; }} td.lbl{{width:auto;}} }}
</style></head>
<body>
<header>
  <h1>🎙️ Athena TTS — Demo so sánh 5 engine TTS mã nguồn mở</h1>
  <div class="sub">Kokoro · Chatterbox · F5-TTS · StyleTTS2 · IndexTTS2 — chạy trên CPU (Apple M4 Pro).
  Mở file này bằng trình duyệt để nghe & xem trực tiếp.</div>
</header>
<main>

  <div class="card">
    <b>Đang làm gì?</b> Thử nghiệm 5 engine TTS mã nguồn mở để: (1) đánh giá chất lượng/độ tự nhiên,
    (2) khả năng <b>nhân bản giọng</b> (voice cloning) từ một clip mẫu, (3) tốc độ tạo.
    <div style="margin-top:8px">
      <span class="pill">Kokoro · nhanh, nhẹ, không clone</span>
      <span class="pill">Chatterbox · LM tự hồi quy</span>
      <span class="pill">F5-TTS · flow-matching</span>
      <span class="pill">StyleTTS2 · style diffusion</span>
      <span class="pill">IndexTTS2 · GPT + cảm xúc</span>
    </div>
  </div>

  <h2>1) Kịch bản dài — giọng gốc (người) vs 5 engine</h2>
  <div class="card">
    <div class="sub">Câu: <code>Hello, this is a short voice consistency test…</code> (clone từ <code>refs/speaker.wav</code>).</div>
    <table>
      {audio_row("⭐ Giọng gốc (người)", "s1_original.wav", "ground truth")}
      {''.join(audio_row(LABEL[e], f"s1_{e}.wav", "" if e!="kokoro" else "giọng cài sẵn (không clone)") for e in ENG)}
    </table>
  </div>

  <h2>2) Clone giọng voiceover — nói đúng thoại clip ref</h2>
  <div class="card">
    <div class="sub">Clip ref <code>neil.wav</code> (4.5s) — thoại: <code>“Ladies and gentlemen, welcome.”</code>;
    cả 5 engine đọc đúng câu này.</div>
    <table>
      {audio_row("⭐ Clip ref (neil)", "ref_neil.wav", "giọng gốc cần clone")}
      {''.join(audio_row(LABEL[e], f"rl_{e}.wav") for e in ENG)}
    </table>
    <table>
      <tr><th>Engine</th><th>Độ giống giọng ref (cosine)</th></tr>
      {rows(clone, lambda v: f"{v:.3f}")}
    </table>
  </div>

  <h2>3) Giọng bụng (xử lý hậu kỳ: hạ formant + cao độ + EQ trầm)</h2>
  <div class="card">
    <div class="grid2">
      <table>{audio_row("StyleTTS2 — gốc","s1_styletts2.wav")}{audio_row("StyleTTS2 — giọng bụng","belly_styletts2.wav")}</table>
      <table>{audio_row("IndexTTS2 — gốc","s1_index.wav")}{audio_row("IndexTTS2 — giọng bụng","belly_index.wav")}</table>
    </div>
  </div>

  <h2>4) Số liệu</h2>
  <div class="card grid2">
    <table><tr><th>Engine</th><th>Điểm tự nhiên /100</th></tr>{rows(human, lambda v: f"{v:.1f}")}</table>
    <table><tr><th>Engine</th><th>Thời gian tạo (s)</th></tr>{rows(timing, lambda v: f"{v:.1f}")}</table>
  </div>

  <h2>5) Biểu đồ</h2>
  <div class="card">
    {img("compare_to_original.png","Chỉ số mỗi engine vs giọng gốc (đường đứt đen). Trục: giá trị chỉ số.")}
    {img("tradeoff_scatter.png","Trục ngang: độ giống giọng gốc; trục dọc: điểm tự nhiên.")}
    {img("similarity_refline_chart.png","Độ giống giọng ref (neil) khi đọc cùng câu. Trục dọc: cosine 0–1.")}
    {img("compare_refline_waveforms.png","Sóng: clip ref (đen) vs 5 engine cùng câu. Trục ngang: thời gian; trục dọc: biên độ.")}
    {img("compare_waveforms.png","Sóng 5 engine + giọng gốc (kịch bản 1).")}
    {img("compare_pitch.png","Cao độ F0 (kịch bản 1). Trục ngang: thời gian; trục dọc: Hz.")}
  </div>

  <h2>6) Báo cáo PDF đầy đủ</h2>
  <div class="card">
    <ul>
      {''.join(f'<li><a href="pdf/{p}">{html.escape(t)}</a></li>' for p,t in PDFS if os.path.exists(os.path.join(D,"pdf",p)))}
    </ul>
  </div>

  <div class="sub" style="margin-top:30px">Tạo tự động bằng <code>build_demo.py</code>. Để gửi: zip cả thư mục <code>demo/</code>.</div>
</main>
</body></html>
"""

with open(os.path.join(D, "index.html"), "w", encoding="utf-8") as f:
    f.write(HTML)

na = len(os.listdir(os.path.join(D, "audio")))
ni = len(os.listdir(os.path.join(D, "img")))
npdf = len(os.listdir(os.path.join(D, "pdf")))
print(f"demo/ built: {na} audio, {ni} images, {npdf} pdfs -> demo/index.html")
