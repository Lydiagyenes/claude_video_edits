#!/usr/bin/env python3
"""Claude világítási stílusok — assemble public/index.html.

Vertical 1080×1920 reel, same format as claude-vagasi-stilusok: the recording (silent head
trimmed, 3.6 s; quiet tail after 34.4 s cut) plays untouched while she lists 23 lighting
styles. On each name's first syllable the shot is relit in that style — a graded copy of the
same moment (hyperframes media-treatment) plus light/shadow overlays shaped to her face —
and the name joins a two-column list under her chin that stays to the end.

Prep (already done, gitignored): public/source.mp4 (from 3.6 s, -g 25), public/voice.wav
(loudnorm -15 LUFS). Committed derived media: public/silhouette.webm and public/rim.webm,
built from a hyperframes remove-background matte of output 7.6–9.64 s (src/cutout.webm):
  silhouette = matte filled near-black; rim = matte edge (alpha − eroded alpha), blurred, cool white.
Run:  python3 build_composition.py
"""
import html
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PUB = ROOT / "public"
W, H, FPS = 1080, 1920, 25
TOTAL = 30.8
TRIM = 3.6
CUT0 = 7.6                      # output time where silhouette.webm / rim.webm start
FCX, FCY = 720, 660             # face centre
ACCENT = "#FFB347"


def q(t):
    return round(round(t * FPS) / FPS, 4)


# ── 23 styles, word onsets in output seconds (silence ends − 3.6 s) ──
ON = [0.0, 1.2, 2.08, 2.96, 4.0, 4.91, 5.8, 6.71, 7.67, 8.65, 9.53, 10.5, 11.7, 12.75, 13.84,
      14.94, 16.32, 17.62, 18.73, 20.08, 21.46, 22.45, 23.36, 25.0]

# key, name, grading patch, overlay html, extra css class
def g(**adjust):
    return {"adjust": adjust}


R = 'rgba'
STYLES = [
    ("hk", "High key", {"adjust": {"exposure": 0.45, "contrast": -0.25, "shadows": 0.35, "blacks": 0.2, "highlights": -0.1, "saturation": -0.1}},
     '<div class="L scr" style="background:radial-gradient(ellipse 700px 900px at 720px 640px,rgba(255,255,255,.35),rgba(255,255,255,.12) 70%)"></div>'),
    ("lk", "Low key", {"adjust": {"exposure": -0.45, "contrast": 0.35, "blacks": -0.3, "shadows": -0.35}, "details": {"vignette": 0.6}},
     '<div class="L mul" style="background:radial-gradient(ellipse 300px 400px at 730px 640px,rgba(0,0,0,0) 30%,rgba(0,0,0,.94) 100%)"></div>'),
    ("remb", "Rembrandt", {"adjust": {"exposure": -0.15, "contrast": 0.25, "temperature": 0.12}, "details": {"vignette": 0.5}},
     '<div class="L mul" style="background:linear-gradient(90deg,rgba(0,0,0,.25) 0,rgba(0,0,0,0) 560px,rgba(0,0,0,0) 690px,rgba(12,6,2,.88) 780px)"></div>'
     '<div class="L scr tri"></div>'),
    ("butter", "Butterfly", {"adjust": {"exposure": 0.05, "contrast": 0.2, "temperature": 0.05}, "details": {"vignette": 0.45}},
     '<div class="L scr" style="background:radial-gradient(ellipse 330px 300px at 715px 470px,rgba(255,246,230,.55),rgba(255,246,230,0) 100%)"></div>'
     '<div class="L mul" style="background:linear-gradient(90deg,rgba(0,0,0,.55) 380px,rgba(0,0,0,0) 560px,rgba(0,0,0,0) 880px,rgba(0,0,0,.55) 1040px)"></div>'
     '<div class="nose"></div>'),
    ("split", "Split light", {"adjust": {"exposure": -0.15, "contrast": 0.35}, "details": {"vignette": 0.5}},
     '<div class="L mul" style="background:linear-gradient(90deg,rgba(0,0,0,0) 0,rgba(0,0,0,0) 706px,rgba(0,0,0,.93) 722px)"></div>'),
    ("loop", "Loop light", {"adjust": {"exposure": -0.05, "contrast": 0.15, "temperature": 0.08}, "details": {"vignette": 0.35}},
     '<div class="L mul" style="background:linear-gradient(90deg,rgba(0,0,0,0) 0,rgba(0,0,0,0) 640px,rgba(0,0,0,.55) 960px)"></div>'
     '<div class="nose loop"></div>'),
    ("broad", "Broad light", {"adjust": {"exposure": 0.1, "contrast": 0.1, "temperature": 0.1}},
     '<div class="L scr" style="background:linear-gradient(90deg,rgba(255,238,215,.4) 0,rgba(255,238,215,.15) 700px,rgba(255,238,215,0) 840px)"></div>'
     '<div class="L mul" style="background:linear-gradient(90deg,rgba(0,0,0,0) 0,rgba(0,0,0,0) 840px,rgba(0,0,0,.6) 940px)"></div>'),
    ("short", "Short light", {"adjust": {"exposure": -0.15, "contrast": 0.25}, "details": {"vignette": 0.4}},
     '<div class="L mul" style="background:linear-gradient(90deg,rgba(0,0,0,.85) 0,rgba(0,0,0,.7) 560px,rgba(0,0,0,.15) 760px,rgba(0,0,0,0) 860px)"></div>'
     '<div class="L scr" style="background:radial-gradient(ellipse 160px 300px at 820px 650px,rgba(255,240,220,.35),rgba(255,240,220,0) 100%)"></div>'),
    ("sil", "Silhouette", {"adjust": {"exposure": 0.9, "contrast": -0.2, "temperature": 0.35, "highlights": 0.3}},
     f'<video id="m-sil" class="clip" src="silhouette.webm" muted playsinline data-start="SEGSTART" data-duration="SEGDUR" data-media-start="MSTART" data-layout-allow-occlusion></video>'),
    ("rim", "Rim light", {"adjust": {"exposure": -0.85, "contrast": 0.35, "temperature": -0.2, "saturation": -0.3}, "details": {"vignette": 0.6}},
     f'<video id="m-rim" class="clip scrv" src="rim.webm" muted playsinline data-start="SEGSTART" data-duration="SEGDUR" data-media-start="MSTART" data-layout-allow-occlusion></video>'),
    ("hard", "Hard light", {"adjust": {"exposure": 0.05, "contrast": 0.55, "highlights": 0.2, "shadows": -0.4, "saturation": 0.1}},
     '<div class="L mul" style="background:linear-gradient(112deg,rgba(0,0,0,0) 0,rgba(0,0,0,0) 54%,rgba(0,0,0,.62) 54.2%)"></div>'),
    ("soft", "Soft light", {"adjust": {"exposure": 0.15, "contrast": -0.25, "highlights": -0.15, "shadows": 0.25}},
     '<div class="L scr" style="background:radial-gradient(ellipse 800px 1000px at 700px 600px,rgba(255,250,244,.32),rgba(255,250,244,.08) 100%)"></div>'),
    ("mono", "Monochrome red", {"preset": "mono-clean", "adjust": {"contrast": 0.3}},
     '<div class="L mul" style="background:#ff1f1f"></div><div class="L scr" style="background:rgba(120,0,0,.25)"></div>'),
    ("screen", "Screen glow", {"adjust": {"exposure": -0.75, "contrast": 0.2, "temperature": -0.3}, "details": {"vignette": 0.5}},
     '<div class="L scr" id="glow-sc" style="background:radial-gradient(ellipse 560px 1000px at 790px 1500px,rgba(90,175,255,.95),rgba(90,175,255,.35) 55%,rgba(90,175,255,0) 100%)"></div>'),
    ("neon", "Neon light", {"adjust": {"exposure": -0.6, "contrast": 0.25, "saturation": 0.2}},
     '<div class="L scr" style="background:linear-gradient(90deg,rgba(255,40,200,.8) 0,rgba(255,40,200,.35) 560px,rgba(255,40,200,0) 760px)"></div>'
     '<div class="L scr" style="background:linear-gradient(270deg,rgba(30,230,255,.8) 0,rgba(30,230,255,.35) 260px,rgba(30,230,255,0) 470px)"></div>'),
    ("strobe", "Strobe light", {"adjust": {"exposure": -0.5, "contrast": 0.45, "temperature": -0.2}},
     '<div class="L scr" id="strobe-fl" style="background:rgba(235,245,255,.92);opacity:0"></div>'),
    ("theat", "Theatrical light", {"adjust": {"exposure": -0.1, "contrast": 0.3, "temperature": 0.25}},
     '<div class="L mul" id="spot" style="background:radial-gradient(circle 380px at 720px 760px,rgba(0,0,0,0) 62%,rgba(0,0,0,.96) 74%)"></div>'),
    ("dapple", "Dappled light", {"adjust": {"exposure": 0.05, "temperature": 0.3, "saturation": 0.1}},
     '<svg class="L mul dap" id="dap" viewBox="0 0 1300 1920" preserveAspectRatio="none"><filter id="dapf" x="0" y="0" width="100%" height="100%">'
     '<feTurbulence type="fractalNoise" baseFrequency="0.0045" numOctaves="2" seed="7"/>'
     '<feColorMatrix type="matrix" values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 -9 5.2"/>'
     '<feGaussianBlur stdDeviation="5"/></filter>'
     '<rect width="1300" height="1920" fill="#3b2a12"/><rect width="1300" height="1920" filter="url(#dapf)"/></svg>'
     '<div class="L scr" style="background:rgba(255,190,90,.12)"></div>'),
    ("vol", "Volumetric light", {"adjust": {"exposure": -0.4, "contrast": 0.15, "temperature": 0.12}},
     '<div class="L scr rays" id="rays"></div><div class="L scr" style="background:linear-gradient(160deg,rgba(255,232,200,.28),rgba(255,232,200,0) 70%)"></div>'),
    ("flat", "Flat light", {"adjust": {"contrast": -0.4, "shadows": 0.3, "highlights": -0.3, "saturation": -0.2, "exposure": 0.1}}, ''),
    ("top", "Top light", {"adjust": {"exposure": -0.35, "contrast": 0.3}},
     '<div class="L scr" style="background:radial-gradient(ellipse 420px 330px at 720px 300px,rgba(255,248,235,.75),rgba(255,248,235,0) 100%)"></div>'
     '<div class="L mul" style="background:linear-gradient(180deg,rgba(0,0,0,0) 0,rgba(0,0,0,0) 560px,rgba(0,0,0,.6) 900px,rgba(0,0,0,.8) 1920px)"></div>'
     '<div class="eye" style="left:560px"></div><div class="eye" style="left:750px"></div>'),
    ("under", "Under light", {"adjust": {"exposure": -0.45, "contrast": 0.3, "temperature": 0.05}},
     '<div class="L mul" style="background:linear-gradient(180deg,rgba(0,0,0,.9) 0,rgba(0,0,0,.55) 460px,rgba(0,0,0,0) 860px)"></div>'
     '<div class="L scr" style="background:radial-gradient(ellipse 520px 760px at 720px 1180px,rgba(255,205,160,.7),rgba(255,205,160,0) 100%)"></div>'),
    ("golden", "Golden hour", {"adjust": {"exposure": 0.1, "contrast": 0.1, "temperature": 0.45, "tint": 0.05, "saturation": 0.15, "vibrance": 0.2}},
     '<div class="L scr" style="background:radial-gradient(circle 900px at 130px 260px,rgba(255,170,60,.85),rgba(255,140,40,.25) 55%,rgba(255,140,40,0) 100%)"></div>'
     '<div class="L scr" style="background:rgba(255,160,70,.1)"></div>'),
]
assert len(STYLES) == 23 == len(ON) - 1
SEG = [(k, n, gr, ov, q(ON[i]), q(ON[i + 1])) for i, (k, n, gr, ov) in enumerate(STYLES)]

SUBS = [
    (25.0, 26.55, 'Ezeket mind a <em>Claude</em>-dal csináltuk.'),
    (26.99, 28.1, "Ha érdekel, hogy hogyan lehet"),
    (28.1, 28.88, "ilyet létrehozni,"),
    (28.9, 30.6, "kövess be minket!"),
]

layers, js, graded = [], [], []


def T(line):
    js.append(line)


for i, (k, name, grade, ov, a, b) in enumerate(SEG):
    d = round(b - a, 4)
    # graded copy of the same moment
    layers.append(f'<video id="v-{k}" class="clip gv" src="source.mp4" muted playsinline data-start="{a}" data-duration="{d}" '
                  f'data-media-start="{a}" data-track-index="2"></video>')
    graded.append((f"#v-{k}", grade))
    if ov:
        ov = ov.replace("SEGSTART", str(a)).replace("SEGDUR", str(d)).replace("MSTART", str(round(a - CUT0, 4)))
        if "<video" in ov:          # matte layers are timed media: keep them out of a timed wrapper
            layers.append(f'<div class="fx" id="fx-{k}">{ov}</div>')
        else:
            layers.append(f'<div id="fx-{k}" class="clip fx" data-start="{a}" data-duration="{d}" data-track-index="3">{ov}</div>')

# per-style motion
a, b = [(s[4], s[5]) for s in SEG if s[0] == "screen"][0]
for n, (dt, op) in enumerate([(0, 1), (0.28, 0.82), (0.36, 1), (0.66, 0.88), (0.74, 1)]):
    T(f"tl.set('#glow-sc',{{opacity:{op}}},{q(a + dt)});")
a, b = [(s[4], s[5]) for s in SEG if s[0] == "strobe"][0]
t = a
while t < b - 0.05:
    T(f"tl.set('#strobe-fl',{{opacity:0.92}},{q(t)});")
    T(f"tl.set('#strobe-fl',{{opacity:0}},{q(t + 0.08)});")
    t += 0.24
a, b = [(s[4], s[5]) for s in SEG if s[0] == "theat"][0]
T(f"tl.fromTo('#spot',{{x:-420,y:-120}},{{x:0,y:0,duration:0.55,ease:'power3.out'}},{a});")
a, b = [(s[4], s[5]) for s in SEG if s[0] == "dapple"][0]
T(f"tl.fromTo('#dap',{{x:-90,y:0}},{{x:0,y:30,duration:{round(b - a, 3)},ease:'sine.inOut'}},{a});")
a, b = [(s[4], s[5]) for s in SEG if s[0] == "vol"][0]
T(f"tl.fromTo('#rays',{{x:-40,opacity:0.7}},{{x:30,opacity:1,duration:{round(b - a, 3)},ease:'sine.inOut'}},{a});")

# ── two-column list of the names under her chin, persisting to the end ──
LIST_X, LIST_Y, ROW = (120, 500), 930, 47
for n, (k, name, grade, ov, a, b) in enumerate(SEG):
    col, row = divmod(n, 12)
    t0 = q(max(a, 0.3))
    cid = f"li-{k}"
    layers.append(f'<div id="{cid}" class="clip liw" data-start="{t0}" data-duration="{round(TOTAL - t0, 4)}" '
                  f'data-track-index="8" style="left:{LIST_X[col]}px;top:{LIST_Y + row * ROW}px">'
                  f'<div class="li"><span class="sl">/</span>{html.escape(name)}</div></div>')
    T(f"tl.fromTo('#{cid} .li',{{opacity:0,x:-22,filter:'blur(6px)'}},{{opacity:1,x:0,filter:'blur(0px)',duration:0.2,ease:'expo.out'}},{t0});")
    T(f"tl.fromTo('#{cid} .li',{{backgroundColor:'rgba(255,179,71,0.96)',color:'#1a1206'}},{{backgroundColor:'rgba(14,12,10,0.66)',color:'#ffffff',duration:0.25,ease:'power2.inOut'}},{q(b - 0.25)});")
    T(f"tl.fromTo('#{cid} .sl',{{color:'#1a1206'}},{{color:'#FFB347',duration:0.25,ease:'power2.inOut'}},{q(b - 0.25)});")

# ── subtitles at the end, below the list ──
for n, (a, b, text) in enumerate(SUBS):
    cid = f"sub-{n}"
    layers.append(f'<div id="{cid}" class="clip capw" data-start="{q(a)}" data-duration="{round(q(b) - q(a), 4)}" '
                  f'data-track-index="9"><div class="cap">{text}</div></div>')
    T(f"tl.fromTo('#{cid} .cap',{{opacity:0,filter:'blur(8px)'}},{{opacity:1,filter:'blur(0px)',duration:0.14,ease:'power2.out'}},{q(a)});")
    T(f"tl.to('#{cid} .cap',{{opacity:0,duration:0.1,ease:'power2.in'}},{q(b - 0.11)});")

CSS = """
html,body{margin:0;background:#111;width:1080px;height:1920px;overflow:hidden}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#111;font-family:Inter,sans-serif}
video{position:absolute;left:0;top:0;width:1080px;height:1920px;object-fit:cover}
/* no z-index on footage/fx: blend layers must share the root stacking context; DOM order paints them */
.fx{position:absolute;inset:0;pointer-events:none}
.L{position:absolute;inset:0}
.mul{mix-blend-mode:multiply}
.scr{mix-blend-mode:screen}
.scrv{mix-blend-mode:screen;opacity:.75;-webkit-mask-image:linear-gradient(180deg,#000 0,#000 40%,transparent 62%);mask-image:linear-gradient(180deg,#000 0,#000 40%,transparent 62%)}
.tri{background:radial-gradient(ellipse 46px 62px at 790px 712px,rgba(255,214,170,.42),rgba(255,214,170,0) 100%);
  clip-path:polygon(752px 668px,836px 668px,792px 770px)}
.nose{position:absolute;left:672px;top:770px;width:64px;height:26px;border-radius:50%;background:rgba(20,10,5,.55);filter:blur(7px);mix-blend-mode:multiply}
.nose.loop{left:700px;top:768px;width:56px;transform:rotate(25deg)}
.eye{position:absolute;top:620px;width:150px;height:70px;border-radius:50%;background:rgba(0,0,0,.5);filter:blur(16px);mix-blend-mode:multiply}
.dap{width:1300px;left:-110px;opacity:.7}
.rays{background:repeating-linear-gradient(105deg,rgba(255,236,205,0) 0,rgba(255,236,205,0) 70px,rgba(255,236,205,.6) 110px,rgba(255,236,205,0) 160px,
  rgba(255,236,205,0) 230px,rgba(255,236,205,.45) 260px,rgba(255,236,205,0) 300px);filter:blur(16px);
  -webkit-mask-image:linear-gradient(160deg,#000 0,rgba(0,0,0,.6) 45%,transparent 85%);mask-image:linear-gradient(160deg,#000 0,rgba(0,0,0,.6) 45%,transparent 85%)}
.liw{position:absolute;height:42px;z-index:21}
.li{display:inline-block;white-space:nowrap;font:900 30px/42px Inter,sans-serif;color:#fff;padding:0 18px 0 12px;border-radius:12px;
  background:rgba(14,12,10,.66);letter-spacing:-0.3px}
.li .sl{color:#FFB347;margin-right:3px}
.capw{position:absolute;left:120px;width:660px;top:1500px;height:180px;z-index:22;display:flex;align-items:flex-end;justify-content:center}
.cap{padding:12px 32px 16px;border-radius:22px;background:rgba(14,12,10,.7);color:#fff;text-align:center;max-width:660px;box-sizing:border-box;
  font:700 52px/1.15 Inter,sans-serif}
.cap em{font-style:normal;color:#FFB347}
"""

doc = f"""<!doctype html>
<html lang="hu">
<head>
<meta charset="utf-8"/>
<title>Claude világítási stílusok</title>
<script src="vendor/gsap.min.js"></script>
<style>{CSS}</style>
</head>
<body>
<div id="root" data-composition-id="claude-vilagitas" data-start="0" data-duration="{TOTAL}" data-fps="{FPS}" data-width="{W}" data-height="{H}">
<video id="main" class="clip" src="source.mp4" muted playsinline data-start="0" data-duration="{TOTAL}" data-media-start="0" data-track-index="1"></video>
{chr(10).join(layers)}
<audio id="voice" src="voice.wav" data-start="0" data-duration="30.74" data-volume="1" data-track-index="10"></audio>
</div>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(js)}
tl.set({{}},{{}},{TOTAL});
window.__timelines["claude-vilagitas"] = tl;
</script>
</body>
</html>
"""
(PUB / "index.html").write_text(doc)

cli = ROOT.parents[1] / ".claude/skills/hyperframes/scripts/plugin-cli.mjs"
for sel, grade in graded:
    subprocess.run(["node", str(cli), "media-treatment", "--project", str(PUB), "--selector", sel,
                    "--grading", json.dumps(grade), "--apply", "--json"], check=True, stdout=subprocess.DEVNULL)
print(f"wrote public/index.html: {len(layers)} layers, {len(js)} tweens, {len(graded)} grades")
