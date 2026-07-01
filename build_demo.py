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
SCRIPT_VI = _read("vi_intro.txt")

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
# test tiếng Việt
for e in ("litellm", "kokoro", "index"):
    cp(f"outputs_vi/{e}.wav", f"vi_{e}.wav", "audio")
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

# (engine, license, dùng thương mại?) — nguồn: repo/model card mỗi engine
LICENSE = [
    ("Kokoro", "Apache-2.0 (code + weights)", "Được"),
    ("Chatterbox", "MIT (code + weights)", "Được"),
    ("F5-TTS", "code MIT · <b>weights CC-BY-NC</b>", "KHÔNG — weights phi thương mại (do dữ liệu Emilia)"),
    ("StyleTTS2", "MIT + ràng buộc dùng giọng", "Có điều kiện — phải có quyền dùng giọng / công bố là giọng tổng hợp"),
    ("IndexTTS2", "Custom (Bilibili)", "Phải xin phép (indexspeech@bilibili.com)"),
    ("Gemini 2.5 Pro", "Google API (đóng, trả phí)", "Được (trả phí)"),
]
license_rows = "".join(f'<tr><td class="lbl">{e}</td><td>{lic}</td><td>{com}</td></tr>' for e, lic, com in LICENSE)

# Bảng chọn engine theo nhu cầu (nhu cầu, engine, vì, lưu ý)
DECISION = [
    ("Voiceover / khoá học <b>tiếng Việt</b>", "Gemini 2.5 Pro", "engine DUY NHẤT đọc đúng tiếng Việt", "trả phí theo token"),
    ("Tiếng Anh · khối lượng lớn · rẻ/nhanh", "Kokoro", "gần real-time, Apache-2.0 (thương mại thoải mái)", "không clone · không tiếng Việt"),
    ("Clone giọng cụ thể (tiếng Anh, nội bộ)", "IndexTTS2", "giống giọng gốc nhất (~0.95)", "license Bilibili · dao động mạnh · không VN"),
    ("Clone + <b>cần thương mại tự do</b>", "Chatterbox", "MIT (code+weights) + clone được", "giống kém IndexTTS2, giọng hơi cao"),
    ("Cảm xúc / hội thoại 2 giọng", "Gemini 2.5 Pro", "điều khiển cảm xúc qua prompt + multi-speaker", "trả phí · giọng preset"),
]
decision_rows = "".join(f'<tr><td>{nc}</td><td class="lbl">{en}</td><td>{vi}</td><td class="note">{lu}</td></tr>'
                        for nc, en, vi, lu in DECISION)


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

utmos = [("Chatterbox", 4.57), ("StyleTTS2", 4.55), ("Kokoro", 4.54),
         ("Giọng gốc (người)", 4.52), ("Gemini 2.5 Pro (LiteLLM)", 4.51),
         ("IndexTTS2", 4.10), ("F5-TTS", 4.00)]
utmos_block = ('<div class="sub"><b>UTMOS</b> — mô hình dự đoán MOS (thang 1–5, cao = tự nhiên hơn), chuẩn thay cho người nghe. '
               'Điểm quan trọng: <b>giọng người thật lọt nhóm đầu (4.52)</b> ⇒ thước đo hợp lệ (khác hẳn proxy cũ chấm người 51.7).</div>'
               f'<table><tr><th>Engine</th><th>UTMOS (1–5)</th></tr>{rows(utmos, lambda v: f"{v:.2f}")}</table>'
               '<div class="note">Nhóm đầu (~4.5) chênh nhau trong khoảng nhiễu (mỗi engine n=1) → coi như <b>ngang nhau</b>; '
               'F5 & IndexTTS2 thấp hơn rõ. UTMOS là <i>dự đoán</i> — quyết định cuối vẫn nên xác nhận bằng MOS người nghe.</div>')
_REPVAR = [("Kokoro", "4.49", "±0.001", "2", "Deterministic (tái lập tuyệt đối)"),
           ("StyleTTS2", "4.23", "±0.052", "5", "Thấp"),
           ("Chatterbox", "4.27", "±0.121", "5", "Vừa"),
           ("Gemini 2.5 Pro", "3.89", "±0.000", "2", "Deterministic"),
           ("F5-TTS", "3.90", "<b>±0.232</b>", "5", "<b>CAO</b>"),
           ("IndexTTS2", "3.56", "<b>±0.255</b>", "5", "<b>CAO</b>")]
rep_block = ('<div class="sub">Chạy lặp cùng 1 câu để đo dao động run-to-run (UTMOS mean ± std). '
             'Engine tự hồi quy/diffusion chạy 5×; Kokoro/Gemini 2× (đủ vì tất định).</div>'
             '<table><tr><th>Engine</th><th>UTMOS mean</th><th>± std</th><th>n</th><th>Độ ổn định</th></tr>'
             + "".join(f'<tr><td class="lbl">{n}</td><td>{mn}</td><td>{sd}</td><td>{c}</td><td>{v}</td></tr>'
                      for n, mn, sd, c, v in _REPVAR) + '</table>'
             '<div class="note"><b>Xác nhận critique #2:</b> F5 (±0.23) &amp; IndexTTS2 (±0.26) dao động mạnh (min–max lệch ~0.6 điểm) '
             '→ <b>điểm 1-lần của chúng KHÔNG đáng tin</b>. Kokoro &amp; Gemini tái lập tuyệt đối (std≈0). '
             'Nên chênh nhỏ giữa các engine trong 1 lần chạy là nhiễu — nhất là engine tự hồi quy. '
             '(Câu test khác mục 2 nên giá trị tuyệt đối lệch; quan trọng là std.)</div>')
nat_block = ('<div class="note"><b>Cảnh báo:</b> bảng proxy /100 dưới đây <b>bị lỗi</b> — nó chấm giọng người 51.7 &lt; máy, tức đo <b>độ đều tín hiệu</b> chứ KHÔNG phải chất lượng. Giữ lại chỉ để xem chỉ số thô, KHÔNG dùng để xếp hạng.</div>'
             f'<table><tr><th>Engine</th><th>Proxy /100 (không dùng xếp hạng)</th></tr>{rows(human, lambda v: f"{v:.1f}")}</table>'
             + img("compare_to_original.png", "Chỉ số âm học mỗi engine vs giọng gốc — mang tính MÔ TẢ (diagnostic), không phải điểm chất lượng."))

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
def md_to_html(md):
    def inline(t):
        t = html.escape(t)
        t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
        t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
        t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" target="_blank">\1</a>', t)
        return t
    lines = md.split("\n"); out = []; i = 0; n = len(lines)
    while i < n:
        ln = lines[i]
        if ln.startswith("```"):
            buf = []; i += 1
            while i < n and not lines[i].startswith("```"):
                buf.append(lines[i]); i += 1
            i += 1
            out.append("<pre class='script'>" + html.escape("\n".join(buf)) + "</pre>"); continue
        if ln.lstrip().startswith("|"):
            tb = []
            while i < n and lines[i].lstrip().startswith("|"):
                tb.append(lines[i].strip().strip("|")); i += 1
            rows = [[c.strip() for c in r.split("|")] for r in tb]
            h = "<table><tr>" + "".join(f"<th>{inline(c)}</th>" for c in rows[0]) + "</tr>"
            for r in rows[2:]:
                h += "<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>"
            out.append(h + "</table>"); continue
        if ln.lstrip().startswith("- "):
            items = []
            while i < n and lines[i].lstrip().startswith("- "):
                items.append(inline(lines[i].lstrip()[2:])); i += 1
            out.append("<ul>" + "".join(f"<li>{x}</li>" for x in items) + "</ul>"); continue
        if ln.startswith("### "): out.append(f"<h4>{inline(ln[4:])}</h4>")
        elif ln.startswith("## "): out.append(f"<h3>{inline(ln[3:])}</h3>")
        elif ln.startswith("# "): pass
        elif ln.startswith("> "): out.append(f"<div class='note'>{inline(ln[2:])}</div>")
        elif ln.strip() == "": pass
        else: out.append(f"<p>{inline(ln)}</p>")
        i += 1
    return "".join(out)


DOC_HTML = md_to_html(_read("../docs/gemini_litellm.md") or
                      open(os.path.join(ROOT, "docs/gemini_litellm.md"), encoding="utf-8").read())


NAVJS = """<script>
(function(){
  var hs=document.querySelectorAll('main h2');
  var side=document.getElementById('toc-side'), inl=document.getElementById('toc');
  var sideOl=document.createElement('ol'); sideOl.className='toclist-side';
  var inlOl=document.createElement('ol'); inlOl.className='toclist';
  var amap={};
  hs.forEach(function(h,i){
    h.id='s'+(i+1);
    var txt=h.textContent.replace(/^\\s*\\d+\\)\\s*/,'');
    var short=h.getAttribute('data-toc')||txt;
    [[side,sideOl,true,short],[inl,inlOl,false,txt]].forEach(function(p){
      if(!p[0]) return;
      var li=document.createElement('li'), a=document.createElement('a');
      a.href='#s'+(i+1); a.textContent=p[3]; li.appendChild(a); p[1].appendChild(li);
      if(p[2]) amap['s'+(i+1)]=a;
    });
  });
  if(side) side.appendChild(sideOl);
  if(inl) inl.appendChild(inlOl);
  if(Object.keys(amap).length){
    var obs=new IntersectionObserver(function(es){
      es.forEach(function(e){ if(e.isIntersecting){
        for(var k in amap) amap[k].classList.remove('active');
        if(amap[e.target.id]) amap[e.target.id].classList.add('active');
      }});
    },{rootMargin:'0px 0px -75% 0px'});
    hs.forEach(function(h){obs.observe(h)});
  }
})();
</script>"""

_VI = [("Gemini 2.5 Pro (LiteLLM)", "vi_litellm.wav", "9.0s",
        "“Chào mừng bạn đến với khoá học nhập môn. Trong các buổi tới…”", "Đọc ĐÚNG tiếng Việt"),
       ("Kokoro", "vi_kokoro.wav", "33.4s",
        "“Chow, M letter 1EBNG, B letter 1EA1N…” (đọc từng ký tự)", "HỎNG — không có tiếng Việt"),
       ("IndexTTS2", "vi_index.wav", "28.6s",
        "“Hãy subscribe cho kênh lalaschool…” (nội dung KHÁC hẳn)", "HỎNG — bịa nội dung")]
vi_rows = "".join(
    f'<tr><td class="lbl">{n}</td>'
    f'<td><audio controls preload="none" src="audio/{f}"></audio></td>'
    f'<td class="note">{d} · {html.escape(t)}</td><td>{v}</td></tr>' for n, f, d, t, v in _VI)
vi_block = (f'<pre class="script">{html.escape(SCRIPT_VI)}</pre>'
            '<table><tr><th>Engine</th><th>Audio</th><th>Whisper nghe lại (dài · nội dung)</th><th>Kết quả</th></tr>'
            + vi_rows + '</table>'
            '<div class="note">Gemini đọc đúng (9s); Kokoro dài gấp ~3.7× do đọc bậy từng ký tự; IndexTTS2 bịa hẳn nội dung khác (rò rỉ dữ liệu huấn luyện). '
            'Xác minh bằng Whisper (vi). ⇒ <b>Ranking đo bằng tiếng Anh KHÔNG áp dụng cho tiếng Việt.</b></div>')

synth_block = (img("tradeoff_scatter.png", "Mỗi điểm là một engine. Trục ngang: độ giống clip ref neil (cosine); trục dọc: UTMOS độ tự nhiên (1–5). Góc trên-phải là lý tưởng.")
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
  h3 {{ font-size:18px; font-weight:600; margin:24px 0 6px; }}
  h4 {{ font-size:15px; font-weight:600; margin:18px 0 4px; color:var(--fg); }}
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
  .sidebar {{ position:fixed; top:24px; width:210px; max-height:calc(100vh - 48px); overflow-y:auto;
    left:max(16px, calc(50% - 664px)); padding:6px 0; }}
  .sidebar .toc-h {{ padding-left:10px; margin-bottom:8px; }}
  ol.toclist-side {{ list-style:none; margin:0; padding:0; }}
  ol.toclist-side li {{ margin:1px 0; }}
  ol.toclist-side a {{ display:block; padding:5px 10px; border-radius:6px; color:var(--mut);
    font-size:13px; line-height:1.35; }}
  ol.toclist-side a:hover {{ background:var(--soft); color:var(--fg); }}
  ol.toclist-side a.active {{ background:#eef5fd; color:var(--acc); font-weight:600; }}
  @media (max-width:1339px) {{ .sidebar {{ display:none; }} }}
  @media (min-width:1340px) {{ .toc {{ display:none; }} }}
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
<nav class="sidebar"><div class="toc-h">MỤC LỤC</div><div id="toc-side"></div></nav>
<main>

  <div class="callout key"><div class="ico">📌</div><div>
    <b>TL;DR</b> — Research so sánh <b>6 engine TTS</b> (5 open-source + Gemini) cho Athena, trên cùng kịch bản.<br>
    • Tự nhiên (UTMOS): nhóm đầu ~4.5 <b>ngang giọng người</b> (StyleTTS2 / Kokoro / Chatterbox / Gemini); F5 &amp; IndexTTS2 thấp hơn<br>
    • Clone giống giọng nhất: <b>IndexTTS2</b> — <i>nhưng vướng license thương mại</i><br>
    • Nhanh / nhẹ nhất: <b>Kokoro</b> (Apache-2.0, thương mại thoải mái)<br>
    • <b>Tiếng Việt:</b> CHỈ Gemini đọc được (Kokoro/IndexTTS2 hỏng) — quyết định với studio VN<br>
    • <b>License:</b> F5 &amp; IndexTTS2 weights KHÔNG cho dùng thương mại tự do<br>
    <span class="sub" style="margin:0">Cuộn xuống để nghe trực tiếp, xem biểu đồ & cách điều khiển (thời lượng · cảm xúc · phụ đề&nbsp;.srt).</span>
  </div></div>

  <div class="card">
    <b>Chọn engine theo nhu cầu</b> — câu trả lời nhanh:
    <table>
      <tr><th>Nhu cầu</th><th>Nên dùng</th><th>Vì</th><th>Lưu ý</th></tr>
      {decision_rows}
    </table>
    <div class="note">Đường đọc nhanh: <b>PM</b> → TL;DR + bảng này · <b>Kỹ sư</b> → mục 9 (Hướng dẫn tích hợp) · <b>Reviewer</b> → Phương pháp & giới hạn + mục 2.</div>
  </div>

  <div class="toc"><div class="toc-h">MỤC LỤC</div><div id="toc"></div></div>

  <div class="card">
    <b>ℹ️ Về research này</b>
    <table>
      <tr><td class="lbl">Lý do</td><td>Athena cần chọn engine TTS cho voiceover / video course / nhân bản giọng — so sánh khách quan thay vì chọn cảm tính, và có tài liệu tích hợp.</td></tr>
      <tr><td class="lbl">Phạm vi</td><td>6 engine (5 open-source + Gemini commercial), cùng kịch bản; đo độ tự nhiên · clone · tốc độ · chi phí · điều khiển (thời lượng/cảm xúc/multi-speaker) · xuất .srt.</td></tr>
      <tr><td class="lbl">Thời gian</td><td>15–22/06/2026 (cập nhật 24/06/2026)</td></tr>
      <tr><td class="lbl">Version</td><td>Kokoro 0.9.4 · Chatterbox 0.1.7 · F5-TTS 1.1.20 · IndexTTS2 2.0.0 · StyleTTS2 (yl4579/LibriTTS) · Gemini 2.5 Pro Preview TTS</td></tr>
      <tr><td class="lbl">Doc tích hợp Gemini</td><td><a href="#s9">Mục 9 — Hướng dẫn cài &amp; xài Gemini qua LiteLLM</a> (ngay trong trang)</td></tr>
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

  <div class="callout key"><div><b>License — tiêu chí LOẠI TRỪ (xét trước chất lượng).</b>
    Hai engine mạnh nhất về clone lại <b>vướng thương mại</b>: <b>F5-TTS</b> (weights CC-BY-NC — cấm thương mại) và <b>IndexTTS2</b> (phải xin phép Bilibili).
    Nếu Athena dùng thương mại: an toàn nhất là <b>Kokoro</b> (Apache-2.0) &amp; <b>Chatterbox</b> (MIT), hoặc <b>Gemini</b> (API trả phí).</div></div>
  <div class="card">
    <table>
      <tr><th>Engine</th><th>License</th><th>Dùng thương mại?</th></tr>
      {license_rows}
    </table>
    <div class="note">Phân biệt <b>license code</b> vs <b>license weights</b> — nhiều model code MIT nhưng weights phi thương mại. Nguồn: model card / repo mỗi engine (kiểm lại tại thời điểm dùng):
      <a href="https://huggingface.co/hexgrad/Kokoro-82M" target="_blank">Kokoro</a> ·
      <a href="https://github.com/resemble-ai/chatterbox" target="_blank">Chatterbox</a> ·
      <a href="https://github.com/SWivid/F5-TTS" target="_blank">F5-TTS</a> ·
      <a href="https://github.com/yl4579/StyleTTS2" target="_blank">StyleTTS2</a> ·
      <a href="https://github.com/index-tts/index-tts" target="_blank">IndexTTS2</a>.</div>
  </div>

  <div class="callout"><div><b>Phương pháp &amp; giới hạn</b> (đọc trước khi tin số):<br>
    • Đo trên <b>Apple M4 Pro, CPU-only (no GPU)</b> — thứ tự tốc độ có thể đổi trên GPU.<br>
    • Các mục nghe/biểu đồ dùng <b>n = 1</b>; riêng độ tự nhiên đã <b>chạy lặp 5×</b> đo mean±std (xem mục 2) — F5/IndexTTS2 dao động mạnh nên điểm 1-lần của chúng là nhiễu.<br>
    • Cấu hình: Kokoro voice <code>af_heart</code>, Gemini voice <code>Kore</code>, speed 1.0, còn lại mặc định mỗi engine.<br>
    • <b>Open-source ≠ miễn phí:</b> tự host tốn GPU/vận hành (TCO) vs Gemini API trả theo token.<br>
    • Độ giống: embedding <b>Resemblyzer</b>; sàn (2 người khác nhau) ≈ <b>0.61</b>, trần (cùng người) ≈ <b>0.98</b>.<br>
    • Chất lượng dùng UTMOS (dự đoán) — quyết định cuối vẫn nên xác nhận bằng người nghe (MOS thật).</div></div>

  <h2 data-toc="Nghe thử">1) Nghe thử — kịch bản dài (giọng gốc + 6 engine)</h2>
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

  <h2 data-toc="Độ tự nhiên">2) Độ tự nhiên — UTMOS (MOS dự đoán)</h2>
  <div class="callout"><div class="ico">💡</div><div><b>Vì sao:</b> đo độ tự nhiên bằng thước đo hợp lệ. Bản đầu dùng proxy tự chế → chấm <b>giọng người 51.7 &lt; máy</b> (lỗi nặng), nên đã thay bằng <b>UTMOS</b> (mô hình dự đoán MOS chuẩn ngành).
    <b>→ Rút ra:</b> nhóm đầu ~4.5 gồm cả <b>giọng người</b> (Chatterbox/StyleTTS2/Kokoro/Gemini ≈ người); <b>F5 & IndexTTS2 thấp hơn</b>. Chênh nhóm đầu là nhiễu (n=1).</div></div>
  <div class="card">{utmos_block}</div>
  <div class="card">{rep_block}</div>
  {details("Chỉ số mô tả tín hiệu (proxy /100 cũ + biểu đồ) — KHÔNG phải chất lượng (bấm để mở)", nat_block)}

  <h2 data-toc="Clone giọng">3) Clone giọng voiceover (neil) — cùng 1 giọng ref, 2 kịch bản</h2>
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

  <h2 data-toc="Tổng hợp">4) Tổng hợp — giống giọng vs tự nhiên, và tốc độ</h2>
  <div class="callout"><div class="ico">💡</div><div><b>Vì sao:</b> gộp 2 trục (giống giọng × tự nhiên) + tốc độ để chọn engine theo nhu cầu.
    <b>→ Rút ra:</b> IndexTTS2 cân bằng nhất; Gemini tự nhiên nhưng không giống (preset); F5 giống nhưng kém tự nhiên; Kokoro nhanh nhất.</div></div>
  {details("📊 Biểu đồ đánh đổi & thời gian tạo (bấm để mở)", synth_block)}

  <h2 data-toc="Demo ứng dụng">5) Demo ứng dụng — Intro khoá học (giọng clone) + phụ đề chạy theo giọng</h2>
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

  <h2 data-toc="Điều khiển thời lượng">6) Spec: điều khiển thời lượng (đặt câu này = N giây)</h2>
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

  <h2 data-toc="Dịch vụ thương mại">7) Dịch vụ thương mại (closed-source) — có trả phí</h2>
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
      <tr><td><b>Gemini 2.5 Pro TTS</b> (Google, qua LiteLLM)</td><td>Audio (TTS, giọng preset)</td><td>$1 /1M token input + <b>$20 /1M token audio output</b> · (bản Flash rẻ hơn: $0.5 / $10) · qua proxy LiteLLM</td></tr>
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

  <h2 data-toc="Tiếng Việt">8) Tiếng Việt — engine nào đọc được?</h2>
  <div class="callout"><div class="ico">💡</div><div><b>Vì sao:</b> Athena là studio Việt — phải kiểm engine đọc được tiếng Việt không (mọi test trên chỉ tiếng Anh).
    <b>→ Rút ra:</b> <b>Chỉ Gemini đọc đúng tiếng Việt.</b> Kokoro & IndexTTS2 hỏng (đọc bậy / bịa nội dung). Ranking tiếng Anh <b>không</b> suy ra cho tiếng Việt.</div></div>
  <div class="card">{vi_block}</div>

  <h2 data-toc="Hướng dẫn Gemini">9) Hướng dẫn — Gemini 2.5 Pro TTS qua LiteLLM</h2>
  <div class="callout"><div class="ico">💡</div><div><b>Vì sao:</b> để team tự tích hợp Gemini TTS qua proxy LiteLLM mà không phải mò.
    <b>→ Rút ra:</b> 3 cách dùng (đơn giọng · cảm xúc · multi-speaker) + các bẫy đã gặp (SSL, Cloudflare, pcm16, speed/temp bị bỏ qua) + giá.</div></div>
  <div class="card">
    {DOC_HTML}
  </div>

  <h2 data-toc="Kết luận">10) Kết luận &amp; khuyến nghị</h2>
  <div class="callout key"><div><b>Cho Athena (studio Việt · dùng thương mại):</b><br>
    • <b>Tiếng Việt</b> (voiceover / khoá học): <b>Gemini 2.5 Pro</b> — engine duy nhất đọc đúng VN; trả phí theo token (rẻ ở quy mô nhỏ).<br>
    • <b>Tiếng Anh, khối lượng lớn</b>: <b>Kokoro</b> — nhanh gần real-time, Apache-2.0, tự host miễn phí bản quyền.<br>
    • <b>Clone giọng</b>: mạnh nhất (IndexTTS2 / F5) nhưng <b>vướng license thương mại + không đọc VN + dao động mạnh</b> → chỉ hợp nội bộ/demo. Cần thương mại → <b>Chatterbox</b> (MIT) hoặc xin phép Bilibili.</div></div>
  <div class="card">
    <b>Cảnh báo trước khi quyết:</b>
    <ul>
      <li>UTMOS là điểm <i>dự đoán</i> — quyết định lớn nên xác nhận bằng <b>người nghe (MOS thật)</b>.</li>
      <li>F5 &amp; IndexTTS2 <b>dao động mạnh</b> giữa các lần chạy → đừng tin điểm 1-lần.</li>
      <li>Tốc độ đo trên <b>CPU</b>; production chạy GPU thì thứ tự có thể đổi.</li>
      <li><b>Bản quyền giọng:</b> chỉ clone giọng đã có đồng ý / được cấp phép.</li>
    </ul>
  </div>

  <h2 data-toc="Báo cáo PDF">11) Báo cáo PDF đầy đủ</h2>
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

# bỏ hết icon/emoji (giữ nguyên ký tự nội dung như → ≈ · —)
for _ic in ("📌", "ℹ️", "💡", "📊", "📋", "⭐", "✅", "❌", "🟡", "⬇️", "⬇", "🎙️", "🧭"):
    HTML = HTML.replace(_ic + " ", "").replace(_ic, "")
HTML = HTML.replace('<div class="ico"></div>', '').replace('<div class="ico"></div>', '')

with open(os.path.join(D, "index.html"), "w", encoding="utf-8") as f:
    f.write(HTML)

na = len(os.listdir(os.path.join(D, "audio")))
ni = len(os.listdir(os.path.join(D, "img")))
npdf = len(os.listdir(os.path.join(D, "pdf")))
print(f"demo/ built: {na} audio, {ni} images, {npdf} pdfs -> demo/index.html")
