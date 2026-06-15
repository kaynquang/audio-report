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

# ---- copy images ----
IMGS = ["compare_waveforms.png", "compare_pitch.png", "compare_to_original.png",
        "tradeoff_scatter.png", "similarity_refline_chart.png",
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
# (engine, cơ chế, dung lượng model, github repo "owner/name")
OVERVIEW = [
    ("Kokoro",     "non-autoregressive 82M · không clone", "~313 MB", "hexgrad/kokoro"),
    ("Chatterbox", "LM tự hồi quy (Llama 0.5B)",           "~3.0 GB", "resemble-ai/chatterbox"),
    ("F5-TTS",     "flow-matching (DiT)",                   "~1.3 GB", "SWivid/F5-TTS"),
    ("StyleTTS2",  "style diffusion + GAN",                 "~870 MB", "yl4579/StyleTTS2"),
    ("IndexTTS2",  "GPT tự hồi quy + cảm xúc",              "~11 GB",  "index-tts/index-tts"),
]
overview_rows = "\n".join(
    f'<tr><td class="lbl">{e}</td><td>{html.escape(m)}</td><td>{sz}</td>'
    f'<td><a href="https://github.com/{r}" target="_blank">{r}</a></td></tr>'
    for e, m, sz, r in OVERVIEW)


def rows(data, fmt):
    return "\n".join(f"<tr><td>{html.escape(n)}</td><td>{fmt(v)}</td></tr>" for n, v in data)


def details(title, inner):
    return (f'<details class="card"><summary>{html.escape(title)}</summary>'
            f'<div class="dbody">{inner}</div></details>')


# nội dung gập sẵn cho từng mục
imgs1 = (img("compare_waveforms.png", "Biểu đồ sóng 5 engine + giọng gốc. Trục ngang: thời gian (giây); trục dọc: biên độ tín hiệu.")
         + img("compare_pitch.png", "Cao độ F0 theo thời gian. Trục ngang: thời gian (giây); trục dọc: cao độ (Hz). Màu đen = giọng gốc.")
         + img("compare_scripts_waveforms.png", "Sóng 2 kịch bản cạnh nhau cho từng engine — trái: kịch bản 1, phải: kịch bản 2."))

nat_block = ('<div class="sub">Điểm proxy 0–100 từ các chỉ số âm học (ngữ điệu, cao độ, năng lượng, timbre…).</div>'
             f'<table><tr><th>Engine</th><th>Điểm tự nhiên /100</th></tr>{rows(human, lambda v: f"{v:.1f}")}</table>'
             + img("compare_to_original.png", "Từng chỉ số của mỗi engine (cột màu) so với GIỌNG GỐC (đường đứt đen). Cột càng gần đường đứt = càng giống người thật."))

clone_block = (f'<table><tr><th>Engine</th><th>Độ giống giọng ref (cosine 0–1)</th></tr>{rows(clone, lambda v: f"{v:.3f}")}</table>'
               + img("similarity_refline_chart.png", "Độ giống giọng ref neil khi đọc cùng câu. Trục dọc: cosine (0–1), càng cao càng giống.")
               + img("compare_refline_waveforms.png", "Sóng: clip ref neil (đen, hàng trên) vs 5 engine cùng câu. Trục ngang: thời gian; trục dọc: biên độ."))

synth_block = (img("tradeoff_scatter.png", "Mỗi điểm là một engine. Trục ngang: độ giống giọng gốc; trục dọc: điểm tự nhiên. Góc trên-phải là lý tưởng.")
               + f'<table><tr><th>Engine</th><th>Thời gian tạo (giây, CPU)</th></tr>{rows(timing, lambda v: f"{v:.1f}")}</table>')


HTML = f"""<!doctype html>
<html lang="vi"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Athena TTS — Demo</title>
<style>
  :root {{ --bg:#f6f7f9; --card:#ffffff; --fg:#1a1d21; --mut:#5c6670; --acc:#1a73e8; --line:#e3e6ea; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--fg);
    font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }}
  header {{ padding:32px 24px; background:linear-gradient(135deg,#eef3fb,#f6f7f9); border-bottom:1px solid var(--line); }}
  h1 {{ margin:0 0 6px; font-size:26px; }}
  h2 {{ margin:34px 0 12px; font-size:20px; border-left:3px solid var(--acc); padding-left:10px; }}
  .sub {{ color:var(--mut); }}
  main {{ max-width:1000px; margin:0 auto; padding:0 24px 60px; }}
  .card {{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:16px 18px; margin:14px 0; box-shadow:0 1px 3px rgba(20,30,50,.05); }}
  table {{ width:100%; border-collapse:collapse; margin:8px 0; }}
  td,th {{ padding:7px 10px; border-bottom:1px solid var(--line); text-align:left; vertical-align:middle; }}
  th {{ color:var(--mut); font-weight:600; }}
  td.lbl {{ width:190px; font-weight:600; }}
  td.note {{ color:var(--mut); font-size:13px; }}
  audio {{ width:320px; height:34px; }}
  figure {{ margin:14px 0; }}
  img {{ width:100%; border-radius:10px; border:1px solid var(--line); background:#fff; }}
  figcaption {{ color:var(--mut); font-size:13px; margin-top:6px; }}
  details.card > summary {{ cursor:pointer; font-weight:600; list-style:none; user-select:none; }}
  details.card > summary::-webkit-details-marker {{ display:none; }}
  details.card > summary::before {{ content:"▸ "; color:var(--acc); font-weight:700; }}
  details.card[open] > summary::before {{ content:"▾ "; }}
  details.card > .dbody {{ margin-top:14px; }}
  a {{ color:var(--acc); }}
  .pill {{ display:inline-block; background:#eef3fb; color:var(--acc); border:1px solid #d6e2f5;
    border-radius:999px; padding:2px 10px; font-size:12px; margin:2px 4px 2px 0; }}
  code {{ background:#eef1f5; padding:1px 6px; border-radius:5px; }}
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
    <b>Overview</b> — Thử nghiệm 5 engine TTS mã nguồn mở: đánh giá (1) độ tự nhiên,
    (2) khả năng <b>nhân bản giọng</b> từ clip mẫu, (3) tốc độ tạo. Bảng dưới: cơ chế,
    dung lượng model (tải về), và link tới repo gốc của từng engine.
    <table>
      <tr><th>Engine</th><th>Cơ chế</th><th>Dung lượng model</th><th>Repo gốc (GitHub)</th></tr>
      {overview_rows}
    </table>
    <div class="note">Dung lượng = tổng weights tải về (Kokoro nhẹ nhất, IndexTTS2 nặng nhất ~11&nbsp;GB gồm cả model phụ trợ).</div>
  </div>

  <h2>1) Nghe thử — kịch bản dài: giọng gốc (người) vs 5 engine</h2>
  <div class="card">
    <div class="sub">Câu: <code>Hello, this is a short voice consistency test…</code> (clone từ <code>refs/speaker.wav</code>). Nghe để cảm nhận tổng thể trước.</div>
    <table>
      {audio_row("⭐ Giọng gốc (người)", "s1_original.wav", "ground truth")}
      {''.join(audio_row(LABEL[e], f"s1_{e}.wav", "" if e!="kokoro" else "giọng cài sẵn (không clone)") for e in ENG)}
    </table>
  </div>
  {details("📊 Biểu đồ — sóng & cao độ (bấm để mở)", imgs1)}

  <h2>2) Độ tự nhiên — so với giọng người thật</h2>
  {details("📊 Số liệu & biểu đồ độ tự nhiên (bấm để mở)", nat_block)}

  <h2>3) Clone giọng — đọc đúng thoại clip ref</h2>
  <div class="card">
    <div class="sub">Clip ref <code>neil.wav</code> (4.5s) — thoại: <code>“Ladies and gentlemen, welcome.”</code>; cả 5 engine đọc đúng câu này để so độ giống giọng.</div>
    <table>
      {audio_row("⭐ Clip ref (neil)", "ref_neil.wav", "giọng gốc cần clone")}
      {''.join(audio_row(LABEL[e], f"rl_{e}.wav") for e in ENG)}
    </table>
  </div>
  {details("📊 Bảng độ giống + biểu đồ (bấm để mở)", clone_block)}

  <h2>4) Tổng hợp — giống giọng vs tự nhiên, và tốc độ</h2>
  {details("📊 Biểu đồ đánh đổi & thời gian tạo (bấm để mở)", synth_block)}

  <h2>5) Báo cáo PDF đầy đủ</h2>
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
