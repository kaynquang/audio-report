"""Dựng trang demo HTML self-contained trong demo/ để gửi cho team.
Copy audio/ảnh/PDF cần thiết rồi sinh demo/index.html (mở bằng browser, hoặc zip gửi đi)."""
from __future__ import annotations
import os, shutil, html, json, re, wave, contextlib

ROOT = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(ROOT, "demo")
for sub in ("audio", "img", "pdf", "video"):
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


def _read(name):
    p = os.path.join(ROOT, "scripts", name)
    return open(p, encoding="utf-8").read().strip() if os.path.exists(p) else ""


SCRIPT1 = _read("voice_consistency_test.txt")
SCRIPT2 = _read("voice_similarity_test.txt")
SCRIPT_COURSE = _read("harvard_intro.txt")

# ---- copy audio ----
for e in ENG:
    cp(f"outputs/{e}.wav", f"s1_{e}.wav", "audio")
cp("refs/neil.wav", "ref_neil.wav", "audio")
for e in ENG:
    cp(f"outputs4/{e}.wav", f"rl_{e}.wav", "audio")   # kịch bản B: đúng thoại ref
    cp(f"outputs3/{e}.wav", f"sy_{e}.wav", "audio")   # kịch bản A: "See you next time."
# phụ đề .srt cho course intro + demo điều khiển thời lượng
os.makedirs(os.path.join(D, "srt"), exist_ok=True)
for e in ENG:
    _s = os.path.join(ROOT, f"outputs5_srt/{e}.srt")
    if os.path.exists(_s):
        shutil.copy2(_s, os.path.join(D, "srt", f"{e}.srt"))
for e in ENG:
    for s in ("base", "2s", "3s", "4s", "5s", "6s"):
        cp(f"outputs_dur/{e}_{s}.wav", f"dur_{e}_{s}.wav", "audio")
cp("refs/tiktok_10_20.wav", "course_ref.wav", "audio")   # giọng video TikTok, giây 10–20
for e in ENG:
    cp(f"outputs5/{e}.wav", f"course_{e}.wav", "audio")     # intro khoá học
# dịch vụ thương mại (closed-source)
cp("non-open/humeai.wav", "humeai.wav", "audio")
cp("non-open/knowlify.mp4", "knowlify.mp4", "video")

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
         + '<div class="sub">Kịch bản 2 (dùng cho biểu đồ so sánh 2 kịch bản bên dưới):</div>'
         + f'<pre class="script">{html.escape(SCRIPT2)}</pre>'
         + img("compare_scripts_waveforms.png", "Sóng 2 kịch bản cạnh nhau cho từng engine — trái: kịch bản 1, phải: kịch bản 2."))

nat_block = ('<div class="sub">Điểm proxy 0–100 từ các chỉ số âm học (ngữ điệu, cao độ, năng lượng, timbre…).</div>'
             f'<table><tr><th>Engine</th><th>Điểm tự nhiên /100</th></tr>{rows(human, lambda v: f"{v:.1f}")}</table>'
             + img("compare_to_original.png", "Từng chỉ số của mỗi engine (cột màu) so với GIỌNG GỐC (đường đứt đen). Cột càng gần đường đứt = càng giống người thật."))

_c2 = [("IndexTTS2", 0.825, 0.951), ("F5-TTS", 0.801, 0.876), ("Chatterbox", 0.699, 0.873),
       ("StyleTTS2", 0.751, 0.797), ("Kokoro", 0.482, 0.517)]
_c2rows = "".join(f"<tr><td>{n}</td><td>{a:.3f}</td><td>{b:.3f}</td></tr>" for n, a, b in _c2)
clone_block = ('<table><tr><th>Engine</th><th>Kịch bản A — “See you next time.” (ngắn)</th>'
               '<th>Kịch bản B — “Ladies and gentlemen, welcome.” (đúng thoại ref)</th></tr>'
               + _c2rows + '</table>'
               + '<div class="note">Độ giống = cosine với clip ref neil (0–1). Câu dài & trùng nội dung ref (B) cho số ổn định và cao hơn câu ngắn (A).</div>'
               + img("similarity_refline_chart.png", "Độ giống giọng ref neil — kịch bản B (đọc cùng câu). Trục dọc: cosine (0–1).")
               + img("compare_refline_waveforms.png", "Sóng: clip ref neil (đen, hàng trên) vs 5 engine — kịch bản B. Trục ngang: thời gian; trục dọc: biên độ."))

_course_rows = "".join(
    f'<tr><td class="lbl">{LABEL[e]}{" (giọng cài sẵn)" if e == "kokoro" else ""}</td>'
    f'<td><audio controls preload="none" src="audio/course_{e}.wav"></audio></td>'
    f'<td><a href="srt/{e}.srt" download>⬇ {e}.srt</a></td></tr>' for e in ENG)

_COURSE_WER = {"kokoro": 4.8, "chatterbox": 4.8, "styletts2": 4.8, "index": 4.8, "f5": 14.3}
_course_tbl = ('<table><tr><th>Engine</th><th>Số cue</th><th>WER (lời khớp script)</th></tr>'
               + "".join(f"<tr><td>{LABEL[e]}</td><td>7</td><td>{_COURSE_WER[e]:.1f}%</td></tr>" for e in ENG)
               + '</table><div class="note">SRT chuẩn hoá: ≤8 từ / ≤42 ký tự / ≤5s mỗi cue, ngắt ở dấu câu. '
                 'WER ~4.8% là chênh do tách từ (không phải lỗi nội dung); F5 14.3% là sai chữ thật do giọng kém rõ.</div>')

def _wd(path):
    try:
        with contextlib.closing(wave.open(path, "rb")) as w:
            return w.getnframes() / float(w.getframerate())
    except Exception:
        return 0.0


def _durclip(e, s, lab):
    return (f'<div class="durclip"><div class="durlab">{lab}</div>'
            f'<audio controls preload="none" src="audio/dur_{e}_{s}.wav"></audio></div>')


_dur_blocks = ""
for e in ENG:
    _bd = _wd(os.path.join(ROOT, "outputs_dur", f"{e}_base.wav"))
    _clips = _durclip(e, "base", f"Gốc — {_bd:.1f}s")
    for _t in ("2s", "3s", "4s", "5s", "6s"):
        _ad = _wd(os.path.join(ROOT, "outputs_dur", f"{e}_{_t}.wav"))
        _clips += _durclip(e, _t, f"Ép {_t[:-1]} giây → {_ad:.2f}s")
    _dur_blocks += f'<div class="dureng"><div class="durname">{LABEL[e]}</div><div class="durflex">{_clips}</div></div>'

_DURCTRL = [("F5-TTS", "🟡 Có (tricky)", "<code>--fix_duration</code> nhưng tính CẢ độ dài clip ref; + <code>--speed</code>"),
            ("Kokoro", "🟡 Qua tốc độ", "tham số <code>speed</code> (hệ số tempo)"),
            ("StyleTTS2", "🟡 Qua tốc độ", "scale bộ dự đoán thời lượng (cần code)"),
            ("IndexTTS2", "🟡 Nâng cao", "model hỗ trợ duration-control; API cơ bản tự canh"),
            ("Chatterbox", "❌ Tự canh", "không có tham số thời lượng")]
_durctrl_tbl = ('<table><tr><th>Engine</th><th>Điều khiển thời lượng?</th><th>Cách</th></tr>'
                + "".join(f"<tr><td class='lbl'>{n}</td><td>{s}</td><td>{c}</td></tr>" for n, s, c in _DURCTRL)
                + '</table><div class="note">Cách chắc ăn cho MỌI engine: time-stretch hậu kỳ (ffmpeg <code>atempo</code>, giữ cao độ) '
                  '→ ép đúng số giây mong muốn, như demo bên trên (2/3/4s từ cùng một câu).</div>')

def parse_srt(path):
    cues = []
    if not os.path.exists(path):
        return cues
    for b in open(path, encoding="utf-8").read().strip().split("\n\n"):
        ls = b.strip().splitlines()
        if len(ls) < 3:
            continue
        m = re.search(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)", ls[1])
        if not m:
            continue
        g = list(map(int, m.groups()))
        s = g[0]*3600 + g[1]*60 + g[2] + g[3]/1000
        e = g[4]*3600 + g[5]*60 + g[6] + g[7]/1000
        cues.append([round(s, 2), round(e, 2), " ".join(ls[2:]).strip()])
    return cues


CUES = {e: parse_srt(os.path.join(D, "srt", f"{e}.srt")) for e in ENG}
_kopts = "".join(f'<option value="{e}">{LABEL[e]}</option>' for e in ENG)
_ksrt = " · ".join(f'<a href="srt/{e}.srt" download>{e}.srt</a>' for e in ENG)
_KJS_BODY = """
(function(){
  var sel=document.getElementById('ksel'),aud=document.getElementById('kaud'),box=document.getElementById('kbox');
  function render(){var c=CUES[sel.value]||[];box.innerHTML=c.map(function(x,i){return '<div class="cue" data-i="'+i+'">'+x[2]+'</div>';}).join('');}
  function setEng(){aud.src='audio/course_'+sel.value+'.wav';render();}
  sel.addEventListener('change',setEng);
  aud.addEventListener('timeupdate',function(){
    var t=aud.currentTime,c=CUES[sel.value]||[],a=-1;
    for(var i=0;i<c.length;i++){if(t>=c[i][0]&&t<c[i][1]){a=i;break;}}
    var els=box.querySelectorAll('.cue');
    els.forEach(function(el,i){el.classList.toggle('on',i===a);if(i===a)el.scrollIntoView({block:'nearest'});});
  });
  setEng();
})();
</script>"""
KJS = "<script>\nvar CUES=" + json.dumps(CUES, ensure_ascii=False) + ";\n" + _KJS_BODY

synth_block = (img("tradeoff_scatter.png", "Mỗi điểm là một engine. Trục ngang: độ giống clip ref neil (cosine); trục dọc: điểm tự nhiên (0–100). Góc trên-phải là lý tưởng.")
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
  main {{ max-width:1000px; margin:0 auto; padding:28px 24px 60px; }}
  .card {{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:16px 18px; margin:14px 0; box-shadow:0 1px 3px rgba(20,30,50,.05); }}
  table {{ width:100%; border-collapse:collapse; margin:8px 0; }}
  td,th {{ padding:7px 10px; border-bottom:1px solid var(--line); text-align:left; vertical-align:middle; }}
  th {{ color:var(--mut); font-weight:600; }}
  td.lbl {{ width:190px; font-weight:600; }}
  td.note {{ color:var(--mut); font-size:13px; }}
  audio {{ width:320px; height:34px; }}
  .dureng {{ margin:14px 0; padding-bottom:12px; border-bottom:1px solid var(--line); }}
  .durname {{ font-weight:700; margin-bottom:7px; }}
  .durflex {{ display:flex; flex-wrap:wrap; gap:10px; }}
  .durclip {{ background:#fafbfc; border:1px solid var(--line); border-radius:8px; padding:6px 9px; }}
  .durlab {{ font-size:12px; color:var(--mut); margin-bottom:4px; }}
  .durclip audio {{ width:178px; height:30px; }}
  video {{ width:100%; max-width:640px; border-radius:10px; border:1px solid var(--line); display:block; }}
  figure {{ margin:14px 0; }}
  img {{ width:100%; border-radius:10px; border:1px solid var(--line); background:#fff; }}
  figcaption {{ color:var(--mut); font-size:13px; margin-top:6px; }}
  details.card > summary {{ cursor:pointer; font-weight:600; list-style:none; user-select:none; }}
  details.card > summary::-webkit-details-marker {{ display:none; }}
  details.card > summary::before {{ content:"▸ "; color:var(--acc); font-weight:700; }}
  details.card[open] > summary::before {{ content:"▾ "; }}
  details.card > .dbody {{ margin-top:14px; }}
  .krow {{ display:flex; gap:10px; align-items:center; flex-wrap:wrap; margin:10px 0; }}
  #ksel {{ padding:6px 10px; border:1px solid var(--line); border-radius:8px; font-size:14px; background:#fff; }}
  #kbox {{ max-height:230px; overflow-y:auto; border:1px solid var(--line); border-radius:10px;
    padding:10px 12px; background:#fafbfc; line-height:1.7; }}
  .cue {{ padding:5px 9px; color:var(--mut); border-radius:6px; transition:background .12s,color .12s; }}
  .cue.on {{ color:var(--fg); background:#e7f0fe; font-weight:700; }}
  a {{ color:var(--acc); }}
  .pill {{ display:inline-block; background:#eef3fb; color:var(--acc); border:1px solid #d6e2f5;
    border-radius:999px; padding:2px 10px; font-size:12px; margin:2px 4px 2px 0; }}
  code {{ background:#eef1f5; padding:1px 6px; border-radius:5px; }}
  pre.script {{ background:#f3f5f8; border:1px solid var(--line); border-radius:8px;
    padding:10px 13px; font-size:13px; line-height:1.55; white-space:pre-wrap;
    margin:8px 0; color:#2a2f36; font-family:Menlo,Consolas,monospace; }}
  .grid2 {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
  @media (max-width:720px) {{ .grid2 {{ grid-template-columns:1fr; }} audio {{ width:100%; }} td.lbl{{width:auto;}} }}
</style></head>
<body>
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

  <h2>1) Nghe thử — kịch bản dài (5 engine)</h2>
  <div class="card">
    <div class="sub">Kịch bản 1 (clone từ <code>refs/speaker.wav</code>) — nghe để cảm nhận tổng thể:</div>
    <pre class="script">{html.escape(SCRIPT1)}</pre>
    <table>
      {''.join(audio_row(LABEL[e], f"s1_{e}.wav", "" if e!="kokoro" else "giọng cài sẵn (không clone)") for e in ENG)}
    </table>
  </div>
  {details("📊 Biểu đồ — sóng & cao độ (bấm để mở)", imgs1)}

  <h2>2) Độ tự nhiên — so với giọng người thật</h2>
  {details("📊 Số liệu & biểu đồ độ tự nhiên (bấm để mở)", nat_block)}

  <h2>3) Clone giọng voiceover (neil) — cùng 1 giọng ref, 2 kịch bản</h2>
  <div class="card">
    <div class="sub">Clip ref <code>neil.wav</code> (4.5s) — dùng làm giọng mẫu nhân bản cho <b>cả 2 kịch bản</b> dưới đây.</div>
    <table>{audio_row("⭐ Clip ref (neil)", "ref_neil.wav", "giọng gốc cần clone")}</table>
    <div class="sub" style="margin-top:12px"><b>Kịch bản A</b> — <code>“See you next time.”</code> (câu ngắn ~1–2s)</div>
    <table>{''.join(audio_row(LABEL[e], f"sy_{e}.wav") for e in ENG)}</table>
    <div class="sub" style="margin-top:12px"><b>Kịch bản B</b> — <code>“Ladies and gentlemen, welcome.”</code> (đúng thoại clip ref)</div>
    <table>{''.join(audio_row(LABEL[e], f"rl_{e}.wav") for e in ENG)}</table>
  </div>
  {details("📊 Bảng độ giống (2 kịch bản) + biểu đồ (bấm để mở)", clone_block)}

  <h2>4) Tổng hợp — giống giọng vs tự nhiên, và tốc độ</h2>
  {details("📊 Biểu đồ đánh đổi & thời gian tạo (bấm để mở)", synth_block)}

  <h2>5) Demo ứng dụng — Intro khoá học (giọng clone) + phụ đề chạy theo giọng</h2>
  <div class="card">
    <div class="sub">Clone từ <b>giọng video TikTok (giây 10–20)</b>, đọc đoạn giới thiệu khoá học.
    <b>Chọn engine → bấm ▶ play → phụ đề tự chạy/sáng theo giọng</b> (như video có sub). Kịch bản:</div>
    <pre class="script">{html.escape(SCRIPT_COURSE)}</pre>
    <table>{audio_row("⭐ Đoạn ref (TikTok, giây 10–20)", "course_ref.wav", "nguồn clone")}</table>
    <div class="krow">
      <select id="ksel">{_kopts}</select>
      <audio id="kaud" controls preload="none"></audio>
    </div>
    <div id="kbox"></div>
    <div class="note" style="margin-top:8px">Tải phụ đề .srt: {_ksrt}</div>
  </div>
  {details("📊 Chất lượng phụ đề (số cue / độ khớp script) (bấm để mở)", _course_tbl)}

  <h2>6) Spec: điều khiển thời lượng (đặt câu này = N giây)</h2>
  <div class="card">
    <div class="sub">Cùng câu <code>“Welcome to this Harvard introductory course.”</code> — mỗi model ở độ dài <b>tự nhiên</b>, rồi <b>ép thành 2 / 3 / 4 / 5 / 6 giây</b> (giữ cao độ). Mỗi nút ghi rõ mốc + số giây thực tế:</div>
    {_dur_blocks}
  </div>
  {details("📋 Khả năng điều khiển thời lượng từng engine (bấm để mở)", _durctrl_tbl)}

  <h2>7) Dịch vụ thương mại (closed-source) — có trả phí</h2>
  <div class="card">
    <div class="sub">Ngoài 5 engine mã nguồn mở, đây là 2 dịch vụ thương mại (đọc cùng kịch bản 1) để so sánh chất lượng/giá.</div>
    <table>
      {audio_row("HumeAI — Octave 2 (audio)", "humeai.wav", "TTS biểu cảm, có API")}
    </table>
    <div class="sub" style="margin-top:12px"><b>Knowlify</b> — không chỉ giọng mà tạo cả <b>VIDEO explainer</b> từ text/tài liệu:</div>
    <video controls preload="none" src="video/knowlify.mp4"></video>
    <table style="margin-top:14px">
      <tr><th>Dịch vụ</th><th>Sản phẩm</th><th>Giá tham khảo</th></tr>
      <tr><td><b>HumeAI</b> (Octave 2)</td><td>Audio (TTS, có cảm xúc)</td><td>~$7.60 / 1 triệu ký tự (API) · free 10k ký tự/tháng · ~½ giá ElevenLabs</td></tr>
      <tr><td><b>Knowlify</b></td><td><b>Video</b> explainer (có narration)</td><td>$50–$500/tháng (video không giới hạn) · Studio ~$1,000/video</td></tr>
    </table>
    <div class="note">Giá tham khảo (6/2026) — kiểm tra lại trên trang chính thức:
      <a href="https://www.hume.ai/pricing" target="_blank">hume.ai/pricing</a> ·
      <a href="https://knowlify.com" target="_blank">knowlify.com</a>.
      Khác biệt chính: engine mã nguồn mở = miễn phí, tự host (cần GPU/setup); dịch vụ thương mại = trả phí nhưng tiện, Knowlify ra thẳng video.</div>
  </div>

  <h2>8) Báo cáo PDF đầy đủ</h2>
  <div class="card">
    <ul>
      {''.join(f'<li><a href="pdf/{p}">{html.escape(t)}</a></li>' for p,t in PDFS if os.path.exists(os.path.join(D,"pdf",p)))}
    </ul>
  </div>

  <div class="sub" style="margin-top:30px">Tạo tự động bằng <code>build_demo.py</code>. Để gửi: zip cả thư mục <code>demo/</code>.</div>
</main>
{KJS}
</body></html>
"""

with open(os.path.join(D, "index.html"), "w", encoding="utf-8") as f:
    f.write(HTML)

na = len(os.listdir(os.path.join(D, "audio")))
ni = len(os.listdir(os.path.join(D, "img")))
npdf = len(os.listdir(os.path.join(D, "pdf")))
print(f"demo/ built: {na} audio, {ni} images, {npdf} pdfs -> demo/index.html")
