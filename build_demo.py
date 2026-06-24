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
         "styletts2": "StyleTTS2", "index": "IndexTTS2",
         "litellm": "Gemini 2.5 Pro (LiteLLM)"}
ENG_ALL = ENG + ["litellm"]   # gồm cả Gemini (commercial) cho các mục nghe/karaoke/thời lượng


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
# Gemini (LiteLLM) audio cho mục nghe/commercial
cp("outputs/litellm.wav", "s1_litellm.wav", "audio")
for _emo in ("neutral", "happy", "sad", "formal"):   # Gemini điều khiển cảm xúc bằng prompt
    cp(f"outputs_dur/gemini_{_emo}.wav", f"gemini_{_emo}.wav", "audio")
cp("outputs_dur/gemini_dialogue.wav", "gemini_dialogue.wav", "audio")   # multi-speaker
# phụ đề .srt cho course intro + demo điều khiển thời lượng (gồm cả Gemini)
os.makedirs(os.path.join(D, "srt"), exist_ok=True)
for e in ENG_ALL:
    cp(f"outputs5/{e}.wav", f"course_{e}.wav", "audio")
    _s = os.path.join(ROOT, f"outputs5_srt/{e}.srt")
    if os.path.exists(_s):
        shutil.copy2(_s, os.path.join(D, "srt", f"{e}.srt"))
for e in ENG_ALL:
    for s in ("base", "2s", "3s", "4s", "5s", "6s"):
        cp(f"outputs_dur/{e}_{s}.wav", f"dur_{e}_{s}.wav", "audio")
# demo ép speed cho ĐOẠN NHIỀU CÂU (course intro 4 câu)
for _src, _dst in [("multi_kokoro_sp1.3", "multi_sp13"), ("multi_kokoro_sp1.0", "multi_sp10"),
                   ("multi_kokoro_sp0.8", "multi_sp08"), ("multi_total_10s", "multi_total_10s"),
                   ("multi_total_12s", "multi_total_12s"), ("multi_total_20s", "multi_total_20s")]:
    cp(f"outputs_dur/{_src}.wav", f"{_dst}.wav", "audio")
cp("outputs_dur/perline.wav", "perline.wav", "audio")   # Cách 3: per-câu
_pls = os.path.join(ROOT, "outputs_dur/perline.srt")
if os.path.exists(_pls):
    shutil.copy2(_pls, os.path.join(D, "srt", "perline.srt"))
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
human = [("Gemini 2.5 Pro (LiteLLM)", 90.2), ("StyleTTS2", 89.6), ("IndexTTS2", 89.5),
         ("Kokoro", 80.9), ("Chatterbox", 78.4), ("Giọng gốc (người)", 51.7), ("F5-TTS", 35.4)]
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
    f'<td><a href="srt/{e}.srt" download>⬇ {e}.srt</a></td></tr>' for e in ENG_ALL)

_COURSE_WER = {"kokoro": 4.8, "chatterbox": 4.8, "styletts2": 4.8, "index": 4.8, "f5": 14.3, "litellm": 9.5}
_course_tbl = ('<table><tr><th>Engine</th><th>Số cue</th><th>WER (lời khớp script)</th></tr>'
               + "".join(f"<tr><td>{LABEL[e]}</td><td>7</td><td>{_COURSE_WER[e]:.1f}%</td></tr>" for e in ENG_ALL)
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
for e in ENG_ALL:
    _bd = _wd(os.path.join(ROOT, "outputs_dur", f"{e}_base.wav"))
    _clips = _durclip(e, "base", f"Gốc — {_bd:.1f}s")
    for _t in ("2s", "3s", "4s", "5s", "6s"):
        _ad = _wd(os.path.join(ROOT, "outputs_dur", f"{e}_{_t}.wav"))
        _clips += _durclip(e, _t, f"Ép {_t[:-1]} giây → {_ad:.2f}s")
    _dur_blocks += f'<div class="dureng"><div class="durname">{LABEL[e]}</div><div class="durflex">{_clips}</div></div>'


def _mc(fn, lab):
    return (f'<div class="durclip"><div class="durlab">{lab}</div>'
            f'<audio controls preload="none" src="audio/{fn}"></audio></div>')


_multi_block = (
    '<div class="durname">Cách 1 — đổi tốc độ khi sinh (native, tự nhiên nhất, ~xấp xỉ giây):</div>'
    '<div class="durflex">'
    + _mc("multi_sp13.wav", "speed 1.3 → 12.8s")
    + _mc("multi_sp10.wav", "speed 1.0 (gốc) → 15.5s")
    + _mc("multi_sp08.wav", "speed 0.8 → 19.7s")
    + '</div>'
    '<div class="durname" style="margin-top:12px">Cách 2 — ép TỔNG đoạn về đúng N giây (atempo, mọi engine):</div>'
    '<div class="durflex">'
    + _mc("multi_total_10s.wav", "ép tổng 10s → 9.99s")
    + _mc("multi_total_12s.wav", "ép tổng 12s → 11.99s")
    + _mc("multi_total_20s.wav", "ép tổng 20s → 19.97s")
    + '</div>')

_PERLINE = [("Welcome to this Harvard introductory course.", 2.5, 2.51),
            ("Over the next few sessions, we will explore the core concepts together, with clear examples and hands-on practice.", 6.0, 6.00),
            ("Whether you are just starting out or brushing up, you are in the right place.", 4.0, 4.01),
            ("Let's get started.", 1.5, 1.51)]
_perline_tbl = ('<table><tr><th>Câu</th><th>Target</th><th>Thực tế</th></tr>'
                + "".join(f'<tr><td>{html.escape(s)}</td><td>{t:.1f}s</td><td>{a:.2f}s</td></tr>'
                         for s, t, a in _PERLINE) + '</table>')
_perline_srt = ""
_plsrc = os.path.join(D, "srt", "perline.srt")
if os.path.exists(_plsrc):
    _perline_srt = open(_plsrc, encoding="utf-8").read()

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


CUES = {e: parse_srt(os.path.join(D, "srt", f"{e}.srt")) for e in ENG_ALL}
_kopts = "".join(f'<option value="{e}">{LABEL[e]}</option>' for e in ENG_ALL)
_ksrt = " · ".join(f'<a href="srt/{e}.srt" download>{e}.srt</a>' for e in ENG_ALL)
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
NAVJS = """<script>
(function(){
  var toc=document.getElementById('toc'); if(!toc) return;
  var hs=document.querySelectorAll('main h2');
  var ol=document.createElement('ol'); ol.className='toclist';
  hs.forEach(function(h,i){
    h.id='s'+(i+1);
    var li=document.createElement('li'), a=document.createElement('a');
    a.href='#s'+(i+1); a.textContent=h.textContent; li.appendChild(a); ol.appendChild(li);
  });
  toc.appendChild(ol);
})();
</script>"""

synth_block = (img("tradeoff_scatter.png", "Mỗi điểm là một engine. Trục ngang: độ giống clip ref neil (cosine); trục dọc: điểm tự nhiên (0–100). Góc trên-phải là lý tưởng.")
               + f'<table><tr><th>Engine</th><th>Thời gian tạo (giây, CPU)</th></tr>{rows(timing, lambda v: f"{v:.1f}")}</table>')


HTML = f"""<!doctype html>
<html lang="vi"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Athena TTS — Demo</title>
<style>
  :root {{ --bg:#ffffff; --card:#ffffff; --fg:#37352f; --mut:#787774; --acc:#2383e2;
           --line:#e9e9e7; --callout:#f7f6f3; --soft:#fbfbfa; --code:#f1f0ee; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--fg); -webkit-font-smoothing:antialiased;
    font:16px/1.65 ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,Helvetica,Arial,sans-serif; }}
  h1 {{ margin:0 0 6px; font-size:30px; font-weight:700; letter-spacing:-.01em; }}
  h2 {{ font-size:23px; font-weight:600; line-height:1.3; margin:48px 0 4px;
    padding-top:22px; border-top:1px solid var(--line); scroll-margin-top:14px; }}
  .sub {{ color:var(--mut); font-size:15px; margin:6px 0 12px; }}
  main {{ max-width:860px; margin:0 auto; padding:52px 24px 90px; }}
  .card {{ background:var(--card); border:1px solid var(--line); border-radius:8px; padding:16px 18px; margin:14px 0; }}
  .callout {{ display:flex; gap:12px; align-items:flex-start; background:var(--callout);
    border:1px solid var(--line); border-radius:8px; padding:14px 16px; margin:16px 0; font-size:15px; }}
  .callout .ico {{ font-size:18px; line-height:1.5; flex:none; }}
  .callout.key {{ background:#eef5fd; border-color:#cfe3fa; }}
  .toc {{ border:1px solid var(--line); border-radius:8px; padding:12px 16px; margin:16px 0; background:var(--soft); }}
  .toc-h {{ font-weight:600; font-size:13px; color:var(--mut); margin-bottom:6px; }}
  ol.toclist {{ margin:0; padding-left:20px; columns:2; column-gap:28px; }}
  ol.toclist li {{ margin:4px 0; font-size:14px; }}
  ol.toclist a {{ color:var(--fg); }}
  table {{ width:100%; border-collapse:collapse; margin:10px 0; font-size:14.5px; }}
  td,th {{ padding:8px 10px; border-bottom:1px solid var(--line); text-align:left; vertical-align:middle; }}
  th {{ color:var(--mut); font-weight:500; font-size:13px; }}
  tr:last-child td {{ border-bottom:none; }}
  td.lbl {{ width:190px; font-weight:600; }}
  td.note {{ color:var(--mut); font-size:13px; }}
  audio {{ width:320px; height:34px; }}
  .dureng {{ margin:14px 0; padding-bottom:12px; border-bottom:1px solid var(--line); }}
  .durname {{ font-weight:700; margin-bottom:7px; }}
  .durflex {{ display:flex; flex-wrap:wrap; gap:10px; }}
  .durclip {{ background:var(--soft); border:1px solid var(--line); border-radius:8px; padding:6px 9px; }}
  .durlab {{ font-size:12px; color:var(--mut); margin-bottom:4px; }}
  .durclip audio {{ width:178px; height:30px; }}
  video {{ width:100%; max-width:640px; border-radius:10px; border:1px solid var(--line); display:block; }}
  figure {{ margin:14px 0; }}
  img {{ width:100%; border-radius:10px; border:1px solid var(--line); background:#fff; }}
  figcaption {{ color:var(--mut); font-size:13px; margin-top:6px; }}
  details.card {{ background:var(--soft); }}
  details.card > summary {{ cursor:pointer; font-weight:500; list-style:none; user-select:none; }}
  details.card > summary::-webkit-details-marker {{ display:none; }}
  details.card > summary::before {{ content:"▸"; color:var(--mut); display:inline-block; width:1.3em; }}
  details.card[open] > summary::before {{ content:"▾"; }}
  details.card > .dbody {{ margin-top:14px; }}
  .krow {{ display:flex; gap:10px; align-items:center; flex-wrap:wrap; margin:10px 0; }}
  #ksel {{ padding:6px 10px; border:1px solid var(--line); border-radius:8px; font-size:14px; background:#fff; }}
  #kbox {{ max-height:230px; overflow-y:auto; border:1px solid var(--line); border-radius:8px;
    padding:10px 12px; background:var(--soft); line-height:1.7; }}
  .cue {{ padding:5px 9px; color:var(--mut); border-radius:6px; transition:background .12s,color .12s; }}
  .cue.on {{ color:var(--fg); background:#eef5fd; font-weight:600; }}
  a {{ color:var(--acc); text-decoration:none; }}
  a:hover {{ text-decoration:underline; }}
  .pill {{ display:inline-block; background:var(--soft); color:var(--mut); border:1px solid var(--line);
    border-radius:999px; padding:2px 10px; font-size:12px; margin:2px 4px 2px 0; }}
  code {{ background:var(--code); padding:1.5px 5px; border-radius:4px; font-size:13.5px;
    font-family:ui-monospace,Menlo,Consolas,monospace; }}
  pre.script {{ background:var(--code); border:1px solid var(--line); border-radius:6px;
    padding:12px 14px; font-size:13px; line-height:1.6; white-space:pre-wrap;
    margin:10px 0; color:#37352f; font-family:ui-monospace,Menlo,Consolas,monospace; }}
  .note {{ color:var(--mut); font-size:13.5px; margin:8px 0; }}
  .grid2 {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
  @media (max-width:720px) {{ .grid2 {{ grid-template-columns:1fr; }} ol.toclist {{ columns:1; }} audio {{ width:100%; }} td.lbl{{width:auto;}} }}
</style></head>
<body>
<main>

  <div class="callout key"><div class="ico">📌</div><div>
    <b>TL;DR.</b> Research so sánh <b>6 engine TTS</b> (5 open-source + Gemini) cho Athena, cùng kịch bản.
    Tự nhiên nhất: <b>Gemini ≈ StyleTTS2 ≈ IndexTTS2</b> · clone giống nhất: <b>IndexTTS2</b> · nhanh/nhẹ nhất: <b>Kokoro</b>.
    Cuộn xuống để <b>nghe trực tiếp</b>, xem biểu đồ, và cách điều khiển (thời lượng · cảm xúc · phụ đề&nbsp;.srt).
  </div></div>

  <div class="toc"><div class="toc-h">MỤC LỤC</div><div id="toc"></div></div>

  <div class="card">
    <b>ℹ️ Về research này</b>
    <table>
      <tr><td class="lbl">Lý do</td><td>Athena cần chọn engine TTS cho voiceover / video course / nhân bản giọng — so sánh khách quan thay vì chọn cảm tính, và có tài liệu tích hợp.</td></tr>
      <tr><td class="lbl">Phạm vi</td><td>6 engine (5 open-source + Gemini commercial), cùng kịch bản; đo độ tự nhiên · clone · tốc độ · chi phí · điều khiển (thời lượng/cảm xúc/multi-speaker) · xuất .srt.</td></tr>
      <tr><td class="lbl">Thời gian</td><td>15–22/06/2026 (cập nhật 24/06/2026)</td></tr>
      <tr><td class="lbl">Version</td><td>Kokoro 0.9.4 · Chatterbox 0.1.7 · F5-TTS 1.1.20 · IndexTTS2 2.0.0 · StyleTTS2 (yl4579/LibriTTS) · Gemini 2.5 Pro Preview TTS</td></tr>
      <tr><td class="lbl">Doc tích hợp Gemini</td><td><a href="https://github.com/kaynquang/audio-report/blob/main/docs/gemini_litellm.md" target="_blank">docs/gemini_litellm.md</a> (cài & xài qua LiteLLM)</td></tr>
    </table>
  </div>

  <div class="card">
    <b>Overview</b> — cơ chế · dung lượng model (tải về) · repo gốc của từng engine.
    <table>
      <tr><th>Engine</th><th>Cơ chế</th><th>Dung lượng model</th><th>Repo gốc (GitHub)</th></tr>
      {overview_rows}
    </table>
    <div class="note">Dung lượng = tổng weights tải về (Kokoro nhẹ nhất, IndexTTS2 nặng nhất ~11&nbsp;GB gồm cả model phụ trợ).</div>
  </div>

  <h2>1) Nghe thử — kịch bản dài (giọng gốc + 6 engine)</h2>
  <div class="callout"><div class="ico">💡</div><div><b>Vì sao:</b> nghe cùng 1 kịch bản + đối chiếu giọng người gốc để cảm nhận tổng thể.
    <b>→ Rút ra:</b> Gemini / StyleTTS2 / IndexTTS2 mượt & tự nhiên; F5 lộ wobble; Kokoro rõ nhưng hơi “máy”.</div></div>
  <div class="card">
    <div class="sub">4 engine clone từ <code>refs/speaker.wav</code>; Kokoro & Gemini dùng giọng preset.</div>
    <pre class="script">{html.escape(SCRIPT1)}</pre>
    <table>
      {audio_row("⭐ Giọng gốc (người)", "s1_original.wav", "ground truth")}
      {''.join(audio_row(LABEL[e], f"s1_{e}.wav", "giọng preset (không clone)" if e in ("kokoro", "litellm") else "") for e in ENG_ALL)}
    </table>
  </div>
  {details("📊 Biểu đồ — sóng & cao độ (bấm để mở)", imgs1)}

  <h2>2) Độ tự nhiên — so với giọng người thật</h2>
  <div class="callout"><div class="ico">💡</div><div><b>Vì sao:</b> chấm điểm khách quan (ngữ điệu, cao độ, năng lượng…) và so trực tiếp với giọng người.
    <b>→ Rút ra:</b> Gemini điểm cao nhất (90); nhưng metric phạt giọng người (dao động rộng) → phải nhìn số thô + nghe, đừng tin mỗi điểm tổng.</div></div>
  {details("📊 Số liệu & biểu đồ độ tự nhiên (bấm để mở)", nat_block)}

  <h2>3) Clone giọng voiceover (neil) — cùng 1 giọng ref, 2 kịch bản</h2>
  <div class="callout"><div class="ico">💡</div><div><b>Vì sao:</b> test nhân bản 1 giọng cụ thể từ clip mẫu; dùng 2 kịch bản (ngắn / đúng thoại ref) để kiểm độ tin cậy phép đo.
    <b>→ Rút ra:</b> IndexTTS2 clone giống nhất; câu dài & trùng nội dung ref cho số ổn định, câu ngắn thì nhiễu.</div></div>
  <div class="card">
    <div class="sub">Clip ref <code>neil.wav</code> (4.5s) — giọng mẫu cho <b>cả 2 kịch bản</b>.</div>
    <table>{audio_row("⭐ Clip ref (neil)", "ref_neil.wav", "giọng gốc cần clone")}</table>
    <div class="sub" style="margin-top:12px"><b>Kịch bản A</b> — <code>“See you next time.”</code> (câu ngắn ~1–2s)</div>
    <table>{''.join(audio_row(LABEL[e], f"sy_{e}.wav") for e in ENG)}</table>
    <div class="sub" style="margin-top:12px"><b>Kịch bản B</b> — <code>“Ladies and gentlemen, welcome.”</code> (đúng thoại clip ref)</div>
    <table>{''.join(audio_row(LABEL[e], f"rl_{e}.wav") for e in ENG)}</table>
  </div>
  {details("📊 Bảng độ giống (2 kịch bản) + biểu đồ (bấm để mở)", clone_block)}

  <h2>4) Tổng hợp — giống giọng vs tự nhiên, và tốc độ</h2>
  <div class="callout"><div class="ico">💡</div><div><b>Vì sao:</b> gộp 2 trục (giống giọng × tự nhiên) + tốc độ để chọn engine theo nhu cầu.
    <b>→ Rút ra:</b> IndexTTS2 cân bằng nhất; Gemini tự nhiên nhưng không giống (preset); F5 giống nhưng kém tự nhiên; Kokoro nhanh nhất.</div></div>
  {details("📊 Biểu đồ đánh đổi & thời gian tạo (bấm để mở)", synth_block)}

  <h2>5) Demo ứng dụng — Intro khoá học (giọng clone) + phụ đề chạy theo giọng</h2>
  <div class="callout"><div class="ico">💡</div><div><b>Vì sao:</b> thử ứng dụng thật — clone giọng đọc intro khoá học + xuất phụ đề <code>.srt</code> khớp giọng cho video.
    <b>→ Rút ra:</b> clone đọc intro ổn; <code>.srt</code> chuẩn hoá cue khớp tốt; giọng rõ (Kokoro/Index) cho phụ đề chính xác, F5 sai chữ.</div></div>
  <div class="card">
    <div class="sub">Clone từ <b>giọng TikTok (giây 10–20)</b>. <b>Chọn engine → ▶ play → phụ đề tự sáng theo giọng.</b></div>
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
  <div class="callout"><div class="ico">💡</div><div><b>Vì sao:</b> kiểm tra có ép được “câu/đoạn = N giây” để khớp video/slide không.
    <b>→ Rút ra:</b> ép được, 3 cách — native speed (xấp xỉ, tự nhiên) · atempo (đúng tổng) · per-câu (khớp từng dòng, chuẩn nhất cho slide).</div></div>
  <div class="card">
    <div class="sub">1 câu — mỗi model ở độ dài <b>tự nhiên</b> rồi <b>ép 2/3/4/5/6 giây</b> (giữ cao độ); nút ghi rõ giây thực tế.</div>
    {_dur_blocks}
  </div>
  {details("📋 Khả năng điều khiển thời lượng từng engine (bấm để mở)", _durctrl_tbl)}
  <div class="card">
    <div class="sub"><b>Đoạn nhiều câu</b> (course intro, 4 câu) — ép tốc độ / thời lượng cho cả đoạn:</div>
    {_multi_block}
    <div class="durname" style="margin-top:12px">Cách 3 — PER-CÂU: mỗi câu một target riêng → phụ đề khớp chính xác từng dòng:</div>
    {_perline_tbl}
    <div class="durflex">{_mc("perline.wav", "Ghép lại (14.9s) + .srt khớp")}</div>
    <div class="note">Tải <a href="srt/perline.srt" download>perline.srt</a> — mỗi dòng đúng thời lượng đặt trước (khớp slide/animation/video). SRT sinh ra:</div>
    <pre class="script">{html.escape(_perline_srt)}</pre>
  </div>

  <h2>7) Dịch vụ thương mại (closed-source) — có trả phí</h2>
  <div class="callout"><div class="ico">💡</div><div><b>Vì sao:</b> so engine open-source với dịch vụ trả phí (Gemini/HumeAI/Knowlify) về chất lượng/giá; test sâu khả năng điều khiển của Gemini.
    <b>→ Rút ra:</b> Gemini chỉnh được giọng + cảm xúc (prompt) + multi-speaker 2 giọng; <code>speed</code>/<code>temperature</code> bị bỏ qua; chi phí research chỉ vài cent.</div></div>
  <div class="card">
    <div class="sub">Đọc cùng kịch bản 1 để so chất lượng/giá với 5 engine open-source.</div>
    <table>
      {audio_row("HumeAI — Octave 2 (audio)", "humeai.wav", "TTS biểu cảm, có API")}
      {audio_row("Gemini 2.5 Pro TTS (qua LiteLLM)", "s1_litellm.wav", "Google · giọng preset · không clone")}
    </table>
    <div class="sub" style="margin-top:12px"><b>Knowlify</b> — không chỉ giọng mà tạo cả <b>VIDEO explainer</b> từ text/tài liệu:</div>
    <video controls preload="none" src="video/knowlify.mp4"></video>
    <table style="margin-top:14px">
      <tr><th>Dịch vụ</th><th>Sản phẩm</th><th>Giá tham khảo</th></tr>
      <tr><td><b>HumeAI</b> (Octave 2)</td><td>Audio (TTS, có cảm xúc)</td><td>~$7.60 / 1 triệu ký tự (API) · free 10k ký tự/tháng · ~½ giá ElevenLabs</td></tr>
      <tr><td><b>Gemini 2.5 Pro TTS</b> (Google, qua LiteLLM)</td><td>Audio (TTS, giọng preset)</td><td>$1 /1M token input + <b>$20 /1M token audio output</b> · qua proxy LiteLLM nội bộ</td></tr>
      <tr><td><b>Knowlify</b></td><td><b>Video</b> explainer (có narration)</td><td>$50–$500/tháng (video không giới hạn) · Studio ~$1,000/video</td></tr>
    </table>
    <div class="sub" style="margin-top:14px"><b>Gemini — điều khiển cảm xúc bằng prompt</b> (cùng câu, chỉ đổi mô tả style trong text):</div>
    <div class="durflex">
      {_mc("gemini_neutral.wav", "Neutral (4.2s)")}
      {_mc("gemini_happy.wav", "Vui (cheerful)")}
      {_mc("gemini_sad.wav", "Buồn (somber)")}
      {_mc("gemini_formal.wav", "Trang trọng (formal)")}
    </div>
    <div class="note">Cách điều khiển của Gemini: ghi mô tả vào text (vd <code>"Say cheerfully: ..."</code>) — model đổi cách đọc, KHÔNG đọc câu lệnh ra. Đã test: tham số <code>speed</code> và <code>temperature</code> qua proxy <b>bị bỏ qua</b> → Gemini chỉ chỉnh được <b>giọng (voice ~30) + cảm xúc/phong cách (prompt)</b>; muốn đổi tốc độ phải dùng atempo hậu kỳ.</div>
    <div class="sub" style="margin-top:14px"><b>Gemini — multi-speaker (2 giọng trong 1 lần sinh)</b> ✅ chạy được qua proxy:</div>
    <div class="durflex">{_mc("gemini_dialogue.wav", "Host: Kore (~260Hz) + Guest: Puck (~129Hz)")}</div>
    <div class="note">Hội thoại 2 người, mỗi người 1 giọng riêng — gọi qua <code>/v1/chat/completions</code> + <code>extra_body.generationConfig.speechConfig.multiSpeakerVoiceConfig</code> (format <code>pcm16</code>). Gemini hỗ trợ tối đa 2 người nói; 5 engine open-source không có (phải ghép thủ công).</div>
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
{NAVJS}
</body></html>
"""

with open(os.path.join(D, "index.html"), "w", encoding="utf-8") as f:
    f.write(HTML)

na = len(os.listdir(os.path.join(D, "audio")))
ni = len(os.listdir(os.path.join(D, "img")))
npdf = len(os.listdir(os.path.join(D, "pdf")))
print(f"demo/ built: {na} audio, {ni} images, {npdf} pdfs -> demo/index.html")
