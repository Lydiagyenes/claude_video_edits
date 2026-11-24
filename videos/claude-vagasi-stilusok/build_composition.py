#!/usr/bin/env python3
"""Claude vágási stílusok és trükkök — assemble public/index.html.

Vertical 1080×1920 reel. The recording (silent first 3.3 s trimmed, see prep below) plays
untouched; while she lists the 13 style names, each style is applied to the footage
exactly on the word that names it, then she plays clean with subtitles.

Every style moves the one footage wrapper #cam (orbit, wall, phone, pullback, vertigo,
zoom, UI card, tier slot) over its own backdrop/overlay, so the picture never cuts away.
Moody uses a graded copy (hyperframes media-treatment), Vertigo a masked unscaled copy.

Prep (already done, files gitignored):
  public/source.mp4  = src/source.mp4 from 3.3 s, -g 25 (seek-safe)
  public/voice.wav   = its sound, loudnorm -15 LUFS
  public/img/still-NN.jpg = stills of the same take for the wall / phones / tier list
Run:  python3 build_composition.py
"""
import html
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PUB = ROOT / "public"
W, H, FPS = 1080, 1920, 25
TOTAL = 25.0
TRIM = 3.3                      # source time of output 0
FX, FY = 536, 980               # face centre in frame = #cam transform origin
ACCENT = "#E07A52"

# ── the 13 styles, output seconds (word onsets from whisper + energy envelope) ──
SEG = [
    ("orbit", "Orbit", 0.0, 1.3),
    ("wall", "Profile wall", 1.3, 2.4),
    ("stamp", "Reject stamp", 2.4, 3.6),
    ("dot", "Dot reveal", 3.6, 4.7),
    ("fan", "Phone fan", 4.7, 5.85),
    ("pull", "Pullback", 5.85, 6.9),
    ("count", "Countdown", 6.9, 8.0),
    ("moody", "Moody", 8.0, 9.1),
    ("giant", "Giant captions", 9.1, 10.4),
    ("vert", "Vertigo", 10.4, 11.65),
    ("zoom", "Digital zoom", 11.65, 12.95),
    ("ui", "Claude UI", 12.95, 14.3),
    ("tier", "Tier list", 14.3, 15.7),
]
SEG = [(k, n, round(round(a * FPS) / FPS, 4), round(round(b * FPS) / FPS, 4)) for k, n, a, b in SEG]  # frame-aligned
S = {k: (a, b) for k, _, a, b in SEG}

# ── subtitles after the list (output seconds) ──
SUBS = [
    (15.75, 16.75, "Ezek mind"),
    (16.8, 18.55, '<em>Claude‑vágási</em> <em>stílusok.</em>'),
    (19.05, 20.0, "Ha érdekel, hogy hogyan"),
    (20.0, 21.15, "tudsz ilyet létrehozni,"),
    (21.25, 23.4, "kövess be minket!"),
]

MOODY_GRADE = {"preset": "deep-contrast",
               "adjust": {"exposure": -0.5, "temperature": -0.22, "tint": 0.04, "saturation": -0.45},
               "details": {"vignette": 0.8}}


VBLUR_GRADE = {"adjust": {"exposure": -0.25}, "effects": {"blur": 1}}


def q(t):
    return round(round(t * FPS) / FPS, 4)


def place(s, cx, cy):
    """x/y for #cam so that, scaled by s around the face origin, the frame centre lands on (cx, cy)."""
    return round(cx - (FX + (W / 2 - FX) * s), 1), round(cy - (FY + (H / 2 - FY) * s), 1)


layers, js = [], []
CAM = "#cam"


def clip(cid, start, end, inner, z, cls="", track=3, extra=""):
    layers.append(f'<div id="{cid}" class="clip ov {cls}" data-start="{q(start)}" '
                  f'data-duration="{round(q(end) - q(start), 4)}" data-track-index="{track}" '
                  f'style="z-index:{z}" {extra}>{inner}</div>')


def T(line):
    js.append(line)


def reset_cam(t):
    T(f"tl.set(CAM,{{x:0,y:0,scale:1,rotationY:0,rotation:0,borderRadius:0}},{q(t)});")


# ── 1 Orbit: the footage plane swings round to face camera; a ring orbits it ──
a, b = S["orbit"]
ring = '<div class="ring"></div>'
clip("s-orbit-back", a, b, f'<div class="ringwrap back">{ring}</div>', 2, "dark")
clip("s-orbit-front", a, b, f'<div class="ringwrap front">{ring}</div><div id="orb-dot" class="orb-dot"></div>', 11)
T(f"tl.fromTo(CAM,{{rotationY:-58,scale:0.64}},{{rotationY:0,scale:1,duration:1.18,ease:'power2.inOut'}},{a});")
T(f"tl.fromTo('#orb-dot',{{x:-470}},{{x:470,duration:1.1,ease:'sine.inOut'}},{a});")
T(f"tl.fromTo('#orb-dot',{{y:0}},{{y:120,duration:0.55,ease:'sine.out'}},{a});")
T(f"tl.to('#orb-dot',{{y:0,duration:0.55,ease:'sine.in'}},{a + 0.55});")
T(f"tl.fromTo('#s-orbit-back .ringwrap, #s-orbit-front .ringwrap, #orb-dot',{{opacity:1}},{{opacity:0,duration:0.25,ease:'power2.in'}},{b - 0.3});")

# ── 2 Profile wall: the shot shrinks into one tile of a wall of the same profile ──
a, b = S["wall"]
SW, GAP = 0.31, 14
TW, TH = W * SW, H * SW
wx, wy = place(SW, W / 2, H / 2)
gcx, gcy = W / 2, H / 2
tiles = []
k = 0
for j in range(-2, 3):
    for i in range(-2, 3):
        if i == 0 and j == 0:
            continue
        left = gcx - TW / 2 + i * (TW + GAP)
        top = gcy - TH / 2 + j * (TH + GAP)
        pos = ["50% 40%", "45% 55%", "55% 50%", "50% 60%"][k % 4]
        zoom = [1.0, 1.25, 1.1, 1.4][k % 4]
        tiles.append(f'<div class="tile" data-d="{abs(i) + abs(j)}" style="left:{left:.1f}px;top:{top:.1f}px;'
                     f'width:{TW:.1f}px;height:{TH:.1f}px"><img src="img/still-{k % 24:02d}.jpg" alt="" '
                     f'style="object-position:{pos};transform:scale({zoom})"/></div>')
        k += 1
clip("s-wall", a, b, "".join(tiles), 2, "dark")
T(f"tl.to(CAM,{{x:{wx},y:{wy},scale:{SW},borderRadius:{round(22 / SW)},duration:0.55,ease:'power3.inOut'}},{a});")
for d in (1, 2, 3, 4):
    T(f"tl.fromTo('#s-wall .tile[data-d=\"{d}\"]',{{opacity:0,scale:0.85}},{{opacity:1,scale:1,duration:0.35,ease:'expo.out'}},{q(a + 0.15 + d * 0.07)});")
T(f"tl.to(CAM,{{x:0,y:0,scale:1,borderRadius:0,duration:0.32,ease:'power3.in'}},{q(b - 0.33)});")
T(f"tl.to('#s-wall .tile',{{opacity:0,duration:0.2,ease:'power2.in'}},{q(b - 0.25)});")

# ── 3 Reject stamp: red ink stamp slams on, the frame shakes ──
a, b = S["stamp"]
clip("s-stamp", a, b, '<div id="rs-wash" class="wash"></div><div id="rs-stamp" class="stamp"><span>REJECTED</span></div>', 12)
reset_cam(a)
hit = q(a + 0.3)
T(f"tl.fromTo('#rs-stamp',{{opacity:0,scale:2.6,rotation:-12}},{{opacity:1,scale:1,rotation:-12,duration:0.16,ease:'power4.in'}},{q(hit - 0.16)});")
T(f"tl.fromTo('#rs-wash',{{opacity:0}},{{opacity:0.32,duration:0.12,ease:'power2.out'}},{hit});")
for n, (dx, dy) in enumerate([(-16, 9), (13, -7), (-8, 5), (5, -3), (0, 0)]):
    T(f"tl.to(CAM,{{x:{dx},y:{dy},duration:0.04,ease:'none'}},{q(hit + n * 0.04)});")
T(f"tl.to('#rs-stamp, #rs-wash',{{opacity:0,duration:0.16,ease:'power2.in'}},{q(b - 0.18)});")

# ── 4 Dot reveal: one dot on her face becomes the iris that opens the shot ──
a, b = S["dot"]
clip("s-dot", a, b, '<div class="dotgrid"></div>', 2, "black")
clip("s-dot-top", a, b, '<div id="dr-dot" class="bigdot"></div>', 11)
T(f"tl.set(CAM,{{clipPath:'circle(0px at {FX}px {FY}px)'}},{a});")
T(f"tl.fromTo('#dr-dot',{{scale:0}},{{scale:1,duration:0.2,ease:'back.out(2.2)'}},{q(a + 0.04)});")
T(f"tl.fromTo('#s-dot .dotgrid',{{opacity:0}},{{opacity:0.55,duration:0.25,ease:'power2.out'}},{a});")
T(f"tl.to(CAM,{{clipPath:'circle(1350px at {FX}px {FY}px)',duration:0.55,ease:'power2.in'}},{q(a + 0.3)});")
T(f"tl.to('#dr-dot',{{scale:3,opacity:0,duration:0.22,ease:'power2.in'}},{q(a + 0.3)});")
T(f"tl.set(CAM,{{clipPath:'none'}},{q(b - 0.04)});")

# ── 5 Phone fan: the shot becomes a phone, more phones fan out behind it ──
a, b = S["fan"]
SP = 0.40
px, py = place(SP, W / 2, 1000)
phones = []
for n, (rot, img) in enumerate([(-30, 3), (-15, 7), (15, 11), (30, 15)]):
    phones.append(f'<div class="phone" id="ph{n}" data-rot="{rot}" style="left:{W / 2 - W * SP / 2:.1f}px;top:{1000 - H * SP / 2:.1f}px;'
                  f'width:{W * SP:.1f}px;height:{H * SP:.1f}px"><img src="img/still-{img:02d}.jpg" alt=""/></div>')
clip("s-fan", a, b, '<div class="glow"></div>' + "".join(phones), 2, "dark")
reset_cam(a)
T(f"tl.to(CAM,{{x:{px},y:{py},scale:{SP},borderRadius:{round(58 / SP)},duration:0.42,ease:'power3.inOut'}},{a});")
T(f"tl.fromTo('#cam-bezel',{{opacity:0}},{{opacity:1,duration:0.25,ease:'power2.out'}},{q(a + 0.12)});")
for n, rot in enumerate([-30, -15, 15, 30]):
    T(f"tl.fromTo('#ph{n}',{{rotation:0,opacity:0}},{{rotation:{rot},opacity:1,duration:0.38,ease:'expo.out'}},{q(a + 0.32 + abs(rot) / 300)});")
    T(f"tl.to('#ph{n}',{{rotation:0,opacity:0,duration:0.26,ease:'power3.in'}},{q(b - 0.3)});")
T(f"tl.to(CAM,{{x:0,y:0,scale:1,borderRadius:0,duration:0.28,ease:'power3.in'}},{q(b - 0.29)});")
T(f"tl.to('#cam-bezel',{{opacity:0,duration:0.2,ease:'power2.in'}},{q(b - 0.22)});")

# ── 6 Pullback: starts tight on her eyes, pulls back to the whole room ──
a, b = S["pull"]
T(f"tl.fromTo(CAM,{{x:0,y:0,scale:2.9,borderRadius:0}},{{scale:1,duration:0.95,ease:'power3.out'}},{a});")

# ── 7 Countdown: film-leader 3·2·1 over a darkened frame, flash into Moody ──
a, b = S["count"]
cd = ['<div class="scrim" id="cd-scrim"></div><div class="leader"><div class="cross h"></div><div class="cross v"></div>']
for n in range(3):
    cd.append(f'<svg class="cd-ring" id="cd-r{n}" viewBox="0 0 520 520"><circle cx="260" cy="260" r="236"/></svg>')
for n, num in enumerate("321"):
    cd.append(f'<div class="cd-n" id="cd-n{n}">{num}</div>')
cd.append('</div><div class="flash" id="cd-flash"></div>')
clip("s-count", a, b, "".join(cd), 12)
reset_cam(a)
T(f"tl.fromTo('#cd-scrim, #s-count .leader',{{opacity:0}},{{opacity:1,duration:0.1,ease:'power2.out'}},{a});")
slot = 0.35
for n in range(3):
    t0 = q(a + 0.04 + n * slot)
    T(f"tl.fromTo('#cd-n{n}',{{opacity:0,scale:1.35}},{{opacity:1,scale:1,duration:0.1,ease:'expo.out'}},{t0});")
    T(f"tl.fromTo('#cd-r{n} circle',{{strokeDashoffset:1483}},{{strokeDashoffset:0,duration:{slot - 0.02},ease:'none'}},{t0});")
    T(f"tl.fromTo('#cd-r{n}',{{opacity:1}},{{opacity:1,duration:0.01}},{t0});")
    T(f"tl.set('#cd-n{n}, #cd-r{n}',{{opacity:0}},{q(t0 + slot)});")
T(f"tl.fromTo('#cd-flash',{{opacity:0}},{{opacity:0.9,duration:0.08,ease:'power2.in'}},{q(b - 0.09)});")

# ── 8 Moody: graded copy, letterbox, slow push ──
a, b = S["moody"]
clip("s-moody", a, b, '<div class="bar top" id="mb-top"></div><div class="bar bot" id="mb-bot"></div>', 12)
reset_cam(a)
T(f"tl.fromTo(CAM,{{scale:1}},{{scale:1.07,duration:{b - a},ease:'sine.inOut'}},{a});")
T(f"tl.fromTo('#mb-top, #mb-bot',{{scaleY:0}},{{scaleY:1,duration:0.35,ease:'power3.out'}},{a});")
T(f"tl.to('#mb-top, #mb-bot',{{scaleY:0,duration:0.15,ease:'power2.in'}},{q(b - 0.16)});")

# ── 9 Giant captions: the two words fill the frame ──
a, b = S["giant"]
clip("s-giant", a, b, '<div class="giant g1" id="gc1">GIANT</div><div class="giant g2" id="gc2">CAPTIONS</div>', 12)
reset_cam(a)
c2 = q(a + 0.45)
T(f"tl.fromTo('#gc1',{{opacity:0,scale:1.6}},{{opacity:1,scale:1,duration:0.16,ease:'expo.out'}},{q(a + 0.02)});")
T(f"tl.fromTo('#gc2',{{opacity:0,scale:1.6}},{{opacity:1,scale:1,duration:0.16,ease:'expo.out'}},{c2});")
T(f"tl.set(CAM,{{scale:1.09}},{c2});")
T(f"tl.to('#gc1, #gc2',{{opacity:0,filter:'blur(10px)',duration:0.16,ease:'power2.in'}},{q(b - 0.17)});")

# ── 10 Vertigo: background zooms in while she (masked, unscaled copy) stays put ──
a, b = S["vert"]
reset_cam(a)
FEATHER = "radial-gradient(ellipse 62% 58% at 50% 50%, #000 50%, transparent 100%)"
T(f"tl.set(CAM,{{webkitMaskImage:'{FEATHER}',maskImage:'{FEATHER}'}},{a});")
T(f"tl.fromTo(CAM,{{scale:1,rotation:0}},{{scale:0.7,rotation:-2,duration:{round(b - a - 0.06, 2)},ease:'power2.inOut'}},{a});")
T(f"tl.set(CAM,{{webkitMaskImage:'none',maskImage:'none'}},{b});")

# ── 11 Digital zoom: camera-app HUD, stepped 1× → 2× → 3× punch-ins ──
a, b = S["zoom"]
hud = ('<div class="corner tl"></div><div class="corner tr"></div><div class="corner bl"></div><div class="corner br"></div>'
       '<div class="rec"><span class="recdot" id="recdot"></span>REC</div>'
       '<div class="zpill"><span id="z1">1×</span><span id="z2">2×</span><span id="z3">3×</span></div>')
clip("s-hud", a, b, hud, 12)
reset_cam(a)
steps = [(a, 1.0, "z1"), (q(a + 0.32), 1.6, "z2"), (q(a + 0.7), 2.3, "z3")]
T(f"tl.fromTo('#s-hud .corner, #s-hud .rec, #s-hud .zpill',{{opacity:0}},{{opacity:1,duration:0.1}},{a});")
for t0, sc, zid in steps:
    T(f"tl.to(CAM,{{scale:{sc},duration:0.07,ease:'power4.out'}},{t0});")
    T(f"tl.set('#s-hud .zpill span',{{backgroundColor:'rgba(0,0,0,0)',color:'#fff'}},{t0});")
    T(f"tl.set('#{zid}',{{backgroundColor:'#FFD23F',color:'#111'}},{t0});")
for n in range(4):
    T(f"tl.set('#recdot',{{opacity:{0 if n % 2 else 1}}},{q(a + n * 0.32)});")

# ── 12 Claude UI: the shot lands as an attachment in a chat answer ──
a, b = S["ui"]
SU = 0.40
cardx, cardy = 130 + W * SU / 2, 690 + H * SU / 2
ux, uy = place(SU, cardx, cardy)
spark = "".join(f'<line x1="32" y1="32" x2="{32 + 26 * c:.1f}" y2="{32 + 26 * s:.1f}"/>'
                for c, s in [(1, 0), (0.707, 0.707), (0, 1), (-0.707, 0.707), (-1, 0), (-0.707, -0.707), (0, -1), (0.707, -0.707)])
ui = (f'<div class="ui-top"><svg class="spark" viewBox="0 0 64 64">{spark}</svg><span>Claude</span></div>'
      '<div class="ui-user" id="ui-user">/claude-ui</div>'
      '<div class="ui-bot" id="ui-bot"><svg class="spark sm" viewBox="0 0 64 64">' + spark + '</svg>Kész, íme a vágás:</div>'
      '<div class="ui-input"><span>Válasz Claude-nak…</span><b>↑</b></div>')
clip("s-ui", a, b, ui, 2, "cream")
reset_cam(a)
T(f"tl.to(CAM,{{x:{ux},y:{uy},scale:{SU},borderRadius:{round(28 / SU)},duration:0.42,ease:'power3.inOut'}},{a});")
T(f"tl.fromTo('#ui-user',{{opacity:0,y:24}},{{opacity:1,y:0,duration:0.3,ease:'expo.out'}},{q(a + 0.05)});")
T(f"tl.fromTo('#ui-bot',{{opacity:0}},{{opacity:1,duration:0.2,ease:'power2.out'}},{q(a + 0.3)});")
T(f"tl.to(CAM,{{x:0,y:0,scale:1,borderRadius:0,duration:0.3,ease:'power3.in'}},{q(b - 0.31)});")

# ── 13 Tier list: the shot drops into the S tier ──
a, b = S["tier"]
ROW_Y, ROW_H, ROW_G = 390, 170, 12
TILE_W = ROW_H * 9 / 16
ST = ROW_H / H
rows = [("S", "#FF7F7F", [2]), ("A", "#FFBF7F", [5, 9, 13]), ("B", "#FFDF7F", [17, 20]), ("C", "#BFFF7F", [22, 1])]
tr = []
for r, (lab, col, imgs) in enumerate(rows):
    y = ROW_Y + r * (ROW_H + ROW_G)
    cells = "".join(f'<img class="tt" src="img/still-{m:02d}.jpg" alt="" style="left:{212 + n * (TILE_W + 10):.1f}px;width:{TILE_W:.1f}px"/>'
                    for n, m in enumerate(imgs))
    tr.append(f'<div class="trow" id="tr{r}" style="top:{y}px;height:{ROW_H}px">'
              f'<div class="tlab" style="background:{col}">{lab}</div>{cells}</div>')
slot_cx = 212 + 1 * (TILE_W + 10) + TILE_W / 2 + 120   # 120 = board left
slot_cy = ROW_Y + ROW_H / 2
tx, ty = place(ST, slot_cx, slot_cy)
clip("s-tier", a, b, '<div class="board">' + "".join(tr) + "</div>", 2, "dark")
reset_cam(a)
T(f"tl.fromTo('#s-tier .trow',{{opacity:0,x:-40}},{{opacity:1,x:0,duration:0.3,ease:'expo.out',stagger:0.05}},{a});")
T(f"tl.to(CAM,{{x:{tx},y:{ty},scale:{round(ST, 4)},borderRadius:{round(8 / ST)},duration:0.6,ease:'power3.inOut'}},{q(a + 0.05)});")
T(f"tl.fromTo('#tr0 .tlab',{{scale:1}},{{scale:1.12,duration:0.12,ease:'power2.out',yoyo:true,repeat:1}},{q(a + 0.62)});")
T(f"tl.to(CAM,{{x:0,y:0,scale:1,borderRadius:0,duration:0.28,ease:'power3.in'}},{q(b - 0.29)});")
T(f"tl.to('#s-tier .trow',{{opacity:0,duration:0.2,ease:'power2.in'}},{q(b - 0.22)});")

# ── after the list: clean footage, punch-ins on the emphasis ──
reset_cam(15.7)
T("tl.set(CAM,{scale:1.1},16.8);")
T("tl.set(CAM,{scale:1},19.05);")
T("tl.set(CAM,{scale:1.12},21.25);")

# ── captions: the spoken style name for each style, then the subtitles ──
caps = []
for n, (k, name, a, b) in enumerate(SEG):
    if k in ("giant", "ui"):
        continue        # the giant words / the chat prompt are the caption there
    cls = "cap name moodyc" if k == "moody" else "cap name"
    caps.append((f"cap-{k}", max(a, 0.1), b, f'<span class="sl">/</span>{html.escape(name)}', cls))
for n, (a, b, text) in enumerate(SUBS):
    caps.append((f"sub-{n}", a, b, text, "cap sent"))
for cid, a, b, text, cls in caps:
    layers.append(f'<div id="{cid}" class="clip capw" data-start="{q(a)}" data-duration="{round(q(b) - q(a), 4)}" '
                  f'data-track-index="9"><div class="{cls}">{text}</div></div>')
    T(f"tl.fromTo('#{cid} .cap',{{opacity:0,filter:'blur(8px)'}},{{opacity:1,filter:'blur(0px)',duration:0.14,ease:'power2.out'}},{q(a)});")
    T(f"tl.to('#{cid} .cap',{{opacity:0,duration:0.1,ease:'power2.in'}},{q(b - 0.11)});")

# counter chip 01/13 … 13/13
for n, (k, name, a, b) in enumerate(SEG):
    layers.append(f'<div id="chip-{k}" class="clip chipw" data-start="{q(a)}" data-duration="{round(q(b) - q(a), 4)}" '
                  f'data-track-index="8"><div class="chip">{n + 1:02d}<i> / 13</i></div></div>')

CSS = """
html,body{margin:0;background:#141210;width:1080px;height:1920px;overflow:hidden}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#141210;font-family:Inter,sans-serif}
#bg{position:absolute;inset:0;background:#141210}
.ov{position:absolute;inset:0;pointer-events:none}
.dark{background:radial-gradient(ellipse 80% 60% at 50% 52%,#2a221c 0%,#141210 70%)}
.black{background:#060606}
.cream{background:#F4F1EA}
#stage{position:absolute;inset:0;z-index:5;perspective:1600px;perspective-origin:540px 960px}
#cam{position:absolute;left:0;top:0;width:1080px;height:1920px;overflow:hidden;transform-origin:536px 980px;
  background:#000;will-change:transform}
#cam video{position:absolute;left:0;top:0;width:1080px;height:1920px;object-fit:cover}
#cam-bezel{position:absolute;inset:0;border:36px solid #0c0c0e;border-radius:145px;opacity:0;box-sizing:border-box}
#cam-bezel::after{content:'';position:absolute;left:50%;top:40px;width:330px;height:80px;margin-left:-165px;border-radius:40px;background:#0c0c0e}
#vert-wrap{position:absolute;inset:0;z-index:6}
#vblur-wrap{position:absolute;inset:0;z-index:4;}
#vblur-wrap video,#vert-wrap video{position:absolute;left:0;top:0;width:1080px;height:1920px;object-fit:cover}
/* orbit */
.ringwrap{position:absolute;left:40px;top:860px;width:1000px;height:250px;transform:rotate(-7deg)}
.ringwrap.back{clip-path:inset(0 0 50% 0)}
.ringwrap.front{clip-path:inset(50% 0 0 0)}
.ring{position:absolute;inset:0;border:5px solid #E07A52;border-radius:50%;box-shadow:0 0 30px rgba(224,122,82,.6)}
.orb-dot{position:absolute;left:518px;top:963px;width:36px;height:36px;border-radius:50%;background:#FFD9C7;
  box-shadow:0 0 24px 8px rgba(224,122,82,.8)}
/* wall */
.tile{position:absolute;overflow:hidden;border-radius:22px;background:#221d18}
.tile img{width:100%;height:100%;object-fit:cover;display:block}
/* stamp */
.wash{position:absolute;inset:0;background:#c3281c;mix-blend-mode:multiply;opacity:0}
.stamp{position:absolute;left:110px;top:440px;width:860px;height:230px;display:flex;align-items:center;justify-content:center;
  border:14px solid #D8311F;border-radius:24px;box-shadow:inset 0 0 0 8px rgba(255,255,255,.0),inset 0 0 0 16px #D8311F;
  color:#D8311F;font:900 150px/1 Inter,sans-serif;letter-spacing:8px;background:rgba(255,246,242,.72)}
.stamp span{transform:translateY(4px)}
/* dot */
.dotgrid{position:absolute;inset:0;background-image:radial-gradient(circle,#E07A52 3px,transparent 3.6px);background-size:40px 40px;opacity:0}
.bigdot{position:absolute;left:506px;top:950px;width:60px;height:60px;border-radius:50%;background:#E07A52;
  box-shadow:0 0 40px 10px rgba(224,122,82,.55)}
/* phones */
.glow{position:absolute;inset:0;background:radial-gradient(circle at 50% 55%,rgba(224,122,82,.35),transparent 55%)}
.phone{position:absolute;border:14px solid #0c0c0e;border-radius:58px;overflow:hidden;background:#000;box-sizing:border-box;
  transform-origin:50% 150%;box-shadow:0 30px 60px rgba(0,0,0,.5)}
.phone img{width:100%;height:100%;object-fit:cover;display:block}
/* countdown */
.scrim{position:absolute;inset:0;background:rgba(10,8,6,.5)}
.leader{position:absolute;inset:0}
.cross{position:absolute;background:rgba(255,255,255,.45)}
.cross.h{left:120px;right:120px;top:959px;height:2px}
.cross.v{top:500px;bottom:500px;left:539px;width:2px}
.cd-ring{position:absolute;left:280px;top:700px;width:520px;height:520px;transform:rotate(-90deg);opacity:0}
.cd-ring circle{fill:none;stroke:#E07A52;stroke-width:14;stroke-dasharray:1483}
.cd-n{position:absolute;left:0;right:0;top:760px;text-align:center;font:900 340px/400px Inter,sans-serif;color:#fff;opacity:0;
  text-shadow:0 10px 40px rgba(0,0,0,.5)}
.flash{position:absolute;inset:0;background:#fff;opacity:0}
/* moody */
.bar{position:absolute;left:0;right:0;height:250px;background:#000}
.bar.top{top:0;transform-origin:50% 0}
.bar.bot{bottom:0;transform-origin:50% 100%}
/* giant */
.giant{position:absolute;left:0;right:0;text-align:center;font-family:'League Gothic',Oswald,sans-serif;line-height:.86;
  color:#fff;text-shadow:0 12px 40px rgba(0,0,0,.55);letter-spacing:4px}
.g1{top:390px;font-size:370px}
.g2{top:720px;font-size:250px;color:#FFB08F}
/* hud */
.corner{position:absolute;width:90px;height:90px;border:0 solid rgba(255,255,255,.9);opacity:0}
.corner.tl{left:130px;top:290px;border-top-width:6px;border-left-width:6px}
.corner.tr{right:130px;top:290px;border-top-width:6px;border-right-width:6px}
.corner.bl{left:130px;top:1340px;border-bottom-width:6px;border-left-width:6px}
.corner.br{right:130px;top:1340px;border-bottom-width:6px;border-right-width:6px}
.rec{position:absolute;left:150px;top:400px;font:700 40px/1 'Space Mono',monospace;color:#fff;display:flex;align-items:center;gap:14px;
  opacity:0;text-shadow:0 2px 8px rgba(0,0,0,.6)}
.recdot{width:26px;height:26px;border-radius:50%;background:#ff3b30}
.zpill{position:absolute;left:470px;top:385px;width:380px;height:84px;border-radius:42px;background:rgba(0,0,0,.5);
  display:flex;align-items:center;justify-content:space-around;opacity:0}
.zpill span{width:96px;height:64px;border-radius:32px;display:flex;align-items:center;justify-content:center;
  font:700 36px/1 Inter,sans-serif;color:#fff}
/* claude ui */
.ui-top{position:absolute;left:0;right:0;top:390px;display:flex;align-items:center;justify-content:center;gap:16px;
  font:700 46px/1 Inter,sans-serif;color:#2B2925}
.spark{width:56px;height:56px;stroke:#D97757;stroke-width:8;stroke-linecap:round}
.spark.sm{width:42px;height:42px;margin-right:14px}
.ui-user{position:absolute;right:200px;top:480px;padding:22px 34px;border-radius:30px;background:#E6E0D3;
  font:700 44px/1.1 'Space Mono',monospace;color:#2B2925}
.ui-bot{position:absolute;left:130px;top:610px;display:flex;align-items:center;font:400 40px/1.2 Inter,sans-serif;color:#3a372f}
.ui-input{position:absolute;left:90px;right:90px;top:1520px;height:120px;border-radius:34px;background:#fff;
  border:2px solid #E2DCCF;display:flex;align-items:center;justify-content:space-between;padding:0 24px 0 40px;box-sizing:border-box;
  font:400 38px/1 Inter,sans-serif;color:#9a958a}
.ui-input b{width:76px;height:76px;border-radius:22px;background:#D97757;color:#fff;display:flex;align-items:center;justify-content:center;font-size:40px}
/* tier list */
.board{position:absolute;left:120px;right:40px;top:0;bottom:0}
.trow{position:absolute;left:0;right:0;background:#26221c;border-radius:16px;overflow:hidden}
.tlab{position:absolute;left:0;top:0;bottom:0;width:190px;display:flex;align-items:center;justify-content:center;
  font:900 120px/1 Inter,sans-serif;color:#1a1a1a}
.tt{position:absolute;top:0;height:100%;object-fit:cover;border-radius:8px}
/* captions */
.capw{position:absolute;left:120px;width:660px;top:1048px;height:200px;z-index:20;display:flex;align-items:flex-end;justify-content:center}
.cap{padding:14px 36px 18px;border-radius:24px;background:rgba(16,14,12,.66);color:#fff;text-align:center;max-width:660px;box-sizing:border-box}
.cap.name{font:900 84px/1.05 Inter,sans-serif;letter-spacing:-1px}
.cap .sl{color:#E07A52;margin-right:6px}
.cap.moodyc{font:italic 700 88px/1.05 'Playfair Display',serif;letter-spacing:0}
.cap.sent{font:700 60px/1.15 Inter,sans-serif}
.cap em{font-style:normal;color:#FFB08F}
.chipw{position:absolute;left:0;right:0;top:296px;height:60px;z-index:19;display:flex;justify-content:center}
.chip{font:700 34px/60px 'Space Mono',monospace;color:#fff;background:rgba(16,14,12,.55);border-radius:30px;padding:0 26px}
.chip i{font-style:normal;color:rgba(255,255,255,.55)}
"""

doc = f"""<!doctype html>
<html lang="hu">
<head>
<meta charset="utf-8"/>
<title>Claude vágási stílusok</title>
<script src="vendor/gsap.min.js"></script>
<style>{CSS}</style>
</head>
<body>
<div id="root" data-composition-id="claude-stilusok" data-start="0" data-duration="{TOTAL}" data-fps="{FPS}" data-width="{W}" data-height="{H}">
<div id="bg"></div>
<div id="stage"><div id="cam">
<video id="main" class="clip" src="source.mp4" muted playsinline data-start="0" data-duration="{TOTAL}" data-media-start="0" data-track-index="1"></video>
<video id="v-moody" class="clip" src="source.mp4" muted playsinline data-start="{q(S['moody'][0])}" data-duration="{round(q(S['moody'][1]) - q(S['moody'][0]), 4)}" data-media-start="{q(S['moody'][0])}" data-track-index="2"></video>
<div id="cam-bezel"></div>
</div></div>
<div id="vblur-wrap"><video id="v-vblur" class="clip" src="source.mp4" muted playsinline data-start="{q(S['vert'][0])}" data-duration="{round(q(S['vert'][1]) - q(S['vert'][0]), 4)}" data-media-start="{q(S['vert'][0])}" data-track-index="2"></video></div>
<div id="vert-wrap"><video id="v-vert" class="clip" src="vert-cutout.webm" muted playsinline data-start="{q(S['vert'][0])}" data-duration="{round(q(S['vert'][1]) - q(S['vert'][0]), 4)}" data-media-start="0" data-track-index="2" data-layout-allow-occlusion></video></div>
{chr(10).join(layers)}
<audio id="voice" src="voice.wav" data-start="0" data-duration="24.26" data-volume="1" data-track-index="10"></audio>
</div>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});
const CAM = "#cam";
tl.set(CAM,{{x:0,y:0,scale:1,rotationY:0,rotation:0,borderRadius:0}},0);
{chr(10).join(js)}
tl.set({{}},{{}},{TOTAL});
window.__timelines["claude-stilusok"] = tl;
</script>
</body>
</html>
"""
(PUB / "index.html").write_text(doc)

# Moody grade through the canonical media treatment (writes the attribute on #v-moody)
cli = ROOT.parents[1] / ".claude/skills/hyperframes/scripts/plugin-cli.mjs"
subprocess.run(["node", str(cli), "media-treatment", "--project", str(PUB), "--selector", "#v-moody",
                "--grading", json.dumps(MOODY_GRADE), "--apply", "--json"], check=True, stdout=subprocess.DEVNULL)
subprocess.run(["node", str(cli), "media-treatment", "--project", str(PUB), "--selector", "#v-vblur",
                "--grading", json.dumps(VBLUR_GRADE), "--apply", "--json"], check=True, stdout=subprocess.DEVNULL)
print(f"wrote public/index.html: {len(layers)} layers, {len(js)} tweens")
