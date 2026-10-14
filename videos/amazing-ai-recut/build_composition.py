#!/usr/bin/env python3
"""Builds public/cards/*.html, storyboard.json and public/index.html for the
Amazing AI / HeyGen talking-head recut (9:16, split-screen + captions).

Card animations are declared with data-anim-* attributes inside each card
fragment and compiled here into the single paused GSAP master timeline.
Run:  python3 build_composition.py
"""
import html
import json
import re
from pathlib import Path

from edit import in_cut, remap

ROOT = Path(__file__).resolve().parent
PUB = ROOT / "public"
FPS = 30
W, H = 1080, 1920
# Clamp to the media length, floored to the frame grid so there is no black tail.
_MEDIA = float(json.loads((ROOT / "metadata.json").read_text())["format"]["duration"])
DURATION = round(int(_MEDIA * FPS - 1) / FPS, 4)

LATIN = ("U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,"
         "U+0329,U+2000-206F,U+2074,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD")
LATIN_EXT = ("U+0100-02AF,U+0304,U+0308,U+0329,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,"
             "U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF")


def q(t):
    """Quantize an absolute time to the frame grid."""
    return round(round(t * FPS) / FPS, 4)


def chars(text):
    """Split text into per-word nowrap spans of per-char spans (for kinetic-chars)."""
    words = []
    for word in text.split(" "):
        inner = "".join(f'<span class="char">{html.escape(c)}</span>' for c in word)
        words.append(f'<span class="w">{inner}</span>')
    return '<span class="sp"> </span>'.join(words)


def scoped(card_id, css):
    return css.replace("S ", f'.card[data-card-id="{card_id}"] ')


# ── Video framings (portrait 1080×1920) ─────────────────────────────────────
# The 16:9 source sits in #video-inner (3413×1920 at scale 1) inside a fixed
# full-canvas window; framings are pure transforms (x / y / scale, origin 0 0).
SRC_W = round(H * 16 / 9)          # 3413
FOCUS_X = 0.54                     # speaker's horizontal centre in the source
FULL = dict(x=round(W / 2 - FOCUS_X * SRC_W), y=0, scale=1)
SPLIT = dict(x=round(W / 2 - FOCUS_X * SRC_W * 0.5), y=960, scale=0.5)  # video fills the bottom half

# Caption band top (px) for each framing — sits on the seam in split, on the chest in full.
CAP_TOP = {"full": 1290, "split": 830}

# ── Cards ───────────────────────────────────────────────────────────────────
# zone: video-overlay (full-bleed video, transparent card) or side-panel (portrait → top half)
CARDS = []


def card(cid, start, end, zone, intent, hints, css, body, framing):
    """start/end are on the uncut timeline (see edit.py); end=None runs to the end."""
    start, end = remap(start), (DURATION if end is None else remap(end))
    CARDS.append(dict(id=cid, start=start, end=end, zone=zone, intent=intent,
                      hints=hints, css=css, body=body, framing=framing))


COMMON_SPLIT_CSS = """
S .root { position:absolute; inset:0; overflow:hidden;
  background: radial-gradient(120% 90% at 50% 38%, #3D1A8A 0%, #24105a 38%, #0D0B1E 78%);
  color:#fff; font-family:'Inter', sans-serif; padding:96px 72px 0 72px; box-sizing:border-box; }
S .root::after { content:''; position:absolute; left:0; right:0; bottom:0; height:6px;
  background:linear-gradient(90deg,#5E44E4,#DF0EC4,#9570FF); box-shadow:0 0 28px 6px rgba(223,14,196,.55); }
S .kicker { display:inline-block; font-family:'Barlow Condensed', sans-serif; font-style:italic; font-weight:800;
  font-size:34px; letter-spacing:.06em; text-transform:uppercase; color:#fff;
  background:#DF0EC4; padding:8px 22px 6px; border-radius:12px; box-shadow:0 0 30px rgba(223,14,196,.6); }
S .title { font-family:'Barlow Condensed', sans-serif; font-style:italic; font-weight:800; text-transform:uppercase;
  font-size:116px; line-height:.95; margin:30px 0 0; color:#fff; text-shadow:0 0 34px rgba(149,112,255,.75); }
S .title .hl { color:#C9B6FF; }
S .w { display:inline-block; white-space:nowrap; }
S .char { display:inline-block; }
S .sp { display:inline-block; width:.26em; }
"""

COMMON_OVERLAY_CSS = """
S .root { position:absolute; inset:0; color:#fff; font-family:'Inter', sans-serif; background:transparent; }
S .scrim { position:absolute; left:0; right:0; top:0; height:760px;
  background:linear-gradient(180deg, rgba(13,11,30,.92) 0%, rgba(13,11,30,.6) 55%, rgba(13,11,30,0) 100%); }
S .top { position:absolute; left:64px; right:64px; top:110px; }
S .kicker { display:inline-block; font-family:'Barlow Condensed', sans-serif; font-style:italic; font-weight:800;
  font-size:34px; letter-spacing:.06em; text-transform:uppercase; color:#fff;
  background:#DF0EC4; padding:8px 22px 6px; border-radius:12px; box-shadow:0 0 30px rgba(223,14,196,.6); }
S .title { font-family:'Barlow Condensed', sans-serif; font-style:italic; font-weight:800; text-transform:uppercase;
  font-size:120px; line-height:.95; margin:26px 0 0; color:#fff;
  text-shadow:0 0 36px rgba(149,112,255,.85), 0 4px 18px rgba(0,0,0,.6); }
S .w { display:inline-block; white-space:nowrap; }
S .char { display:inline-block; }
S .sp { display:inline-block; width:.26em; }
"""

# 1 — Avatar vs. real comparison (split: muted HeyGen avatar on top, real footage below)
AVATAR_END = 14.35  # "Csak létrehozol…" — the how-to section takes over the top half
card("card-01", 0.05, AVATAR_END, "video-overlay",
     "Comparison hook: the top video is her HeyGen avatar (muted), the bottom one is the real recording; "
     "then: lifelike avatar in minutes, any text, any language",
     {"badges": ["AI-avatár", "Eredeti felvétel"], "title": "Élethű avatár pár perc alatt",
      "chips": ["Bármilyen szöveg", "Bármilyen nyelv"]},
     """
S .root { position:absolute; inset:0; color:#fff; font-family:'Inter', sans-serif; background:transparent; }
S .w { display:inline-block; white-space:nowrap; }
S .char { display:inline-block; }
S .sp { display:inline-block; width:.26em; }
S .badge { position:absolute; display:inline-flex; align-items:center; gap:14px; padding:12px 26px 9px;
  border-radius:999px; font-family:'Barlow Condensed', sans-serif; font-style:italic; font-weight:800;
  font-size:44px; text-transform:uppercase; letter-spacing:.03em; }
S .ai { left:40px; top:40px; background:#DF0EC4; box-shadow:0 0 30px rgba(223,14,196,.75); }
S .real { left:40px; top:1000px; background:rgba(13,11,30,.6); border:3px solid #fff; box-shadow:0 0 22px rgba(255,255,255,.45); }
S .dot { width:18px; height:18px; border-radius:50%; background:#fff; box-shadow:0 0 12px #fff; }
S .rec { width:18px; height:18px; border-radius:50%; background:#ff3b5c; box-shadow:0 0 12px #ff3b5c; }
S .scrim { position:absolute; left:0; right:0; top:500px; height:460px;
  background:linear-gradient(180deg, rgba(13,11,30,0) 0%, rgba(13,11,30,.78) 42%, rgba(13,11,30,.95) 100%); }
S .seam { position:absolute; left:0; right:0; top:957px; height:6px;
  background:linear-gradient(90deg,#5E44E4,#DF0EC4,#9570FF); box-shadow:0 0 28px 6px rgba(223,14,196,.55); }
S .block { position:absolute; left:56px; right:56px; top:560px; }
S .kicker { display:inline-block; font-family:'Barlow Condensed', sans-serif; font-style:italic; font-weight:800;
  font-size:32px; letter-spacing:.06em; text-transform:uppercase; color:#C9B6FF; }
S .title { font-family:'Barlow Condensed', sans-serif; font-style:italic; font-weight:800; text-transform:uppercase;
  font-size:84px; line-height:.95; margin:10px 0 0; color:#fff; text-shadow:0 0 30px rgba(149,112,255,.85); }
S .title .hl { color:#C9B6FF; }
S .chips { position:absolute; left:40px; top:130px; display:flex; flex-direction:column; align-items:flex-start; gap:14px; }
S .chip { font-family:'Barlow Condensed', sans-serif; font-style:italic; font-weight:800; font-size:40px;
  text-transform:uppercase; padding:10px 22px 7px; border-radius:14px; color:#fff; }
S .c0 { background:#5E44E4; box-shadow:0 0 24px rgba(94,68,228,.85); }
S .c1 { background:#C44DB8; box-shadow:0 0 24px rgba(196,77,184,.85); }
""",
     f"""<div class="seam"></div>
<div class="badge ai" id="card-01-ai" data-anim="scale-pop" data-anim-at="0.2" data-anim-duration="0.5"><span class="dot"></span>AI-avatár · HeyGen</div>
<div class="badge real" id="card-01-real" data-anim="scale-pop" data-anim-at="2.95" data-anim-duration="0.5"><span class="rec"></span>Eredeti felvétel</div>
<div class="chips">
  <div class="chip c0" id="card-01-chip0" data-anim="scale-pop" data-anim-at="11.9" data-anim-duration="0.45">Bármilyen szöveg</div>
  <div class="chip c1" id="card-01-chip1" data-anim="scale-pop" data-anim-at="12.95" data-anim-duration="0.45">Bármilyen nyelv</div>
</div>""", "split")

# 3 — How it works: 3 steps (split) ─────────────────────────────────────────
STEPS_CSS = """
S .steps { margin-top:40px; display:flex; flex-direction:column; gap:26px; }
S .step { display:flex; align-items:center; gap:28px; background:rgba(255,255,255,.07);
  border:2px solid rgba(149,112,255,.45); border-radius:22px; padding:20px 26px; }
S .num { flex:none; width:78px; height:78px; border-radius:50%; display:flex; align-items:center; justify-content:center;
  font-family:'Barlow Condensed', sans-serif; font-style:italic; font-weight:800; font-size:52px; color:#fff; }
S .n0 { background:#5E44E4; box-shadow:0 0 22px rgba(94,68,228,.9); }
S .n1 { background:#9570FF; box-shadow:0 0 22px rgba(149,112,255,.9); }
S .n2 { background:#DF0EC4; box-shadow:0 0 22px rgba(223,14,196,.9); }
S .txt b { display:block; font-family:'Barlow Condensed', sans-serif; font-style:italic; font-weight:800;
  text-transform:uppercase; font-size:48px; line-height:1; }
S .txt span { display:block; margin-top:6px; font-size:29px; font-weight:400; color:#D9CFFF; line-height:1.25; }
S .done { position:absolute; right:64px; top:92px; font-family:'Barlow Condensed', sans-serif; font-style:italic;
  font-weight:800; font-size:52px; text-transform:uppercase; color:#0D0B1E; background:#fff; padding:10px 28px 6px;
  border-radius:16px; box-shadow:0 0 40px rgba(255,255,255,.75); transform:rotate(-4deg); }
"""
card("card-02", 14.4, 26.7, "side-panel",
     "How it works in three steps: create, upload samples, HeyGen AI copies your gestures — done",
     {"kicker": "Így működik", "steps": ["Új avatár", "Feltöltés", "Az AI lemásol"], "badge": "Kész is vagy"},
     COMMON_SPLIT_CSS + STEPS_CSS,
     f"""<div class="kicker" id="card-02-kicker" data-anim="slide-in" data-anim-at="0.1" data-anim-duration="0.4" data-anim-from="left" data-anim-distance="60">Így működik</div>
<div class="done" id="card-02-done" data-anim="scale-pop" data-anim-at="11.4" data-anim-duration="0.5">Kész is vagy ✓</div>
<div class="steps">
  <div class="step" id="card-02-s0" data-anim="slide-in" data-anim-at="0.4" data-anim-duration="0.5" data-anim-from="left" data-anim-distance="120"><div class="num n0">1</div><div class="txt"><b>Új avatár</b><span>Létrehozod, a saját alakodra formálod</span></div></div>
  <div class="step" id="card-02-s1" data-anim="slide-in" data-anim-at="3.05" data-anim-duration="0.5" data-anim-from="left" data-anim-distance="120"><div class="num n1">2</div><div class="txt"><b>Feltöltés</b><span>Rövid szöveg · hangminta · videóminta</span></div></div>
  <div class="step" id="card-02-s2" data-anim="slide-in" data-anim-at="7.5" data-anim-duration="0.5" data-anim-from="left" data-anim-distance="120"><div class="num n2">3</div><div class="txt"><b>A HeyGen AI lemásol</b><span>A gesztusaidat és a mozgásodat</span></div></div>
</div>""",
     "split")

# 5 — FX scene (full-bleed): flaming hair → underwater → sunny beach ─────────
# The effects themselves are layers inside #video-wrap (see FX below); this card
# only carries the "Lehet akár…" kicker and one label chip per effect.
card("card-03", 33.8, 38.28, "video-overlay",
     "Visualise the three examples on her own footage: hair on fire, frame fills with water, beach background",
     {"kicker": "Lehet akár…", "chips": ["Lángoló haj", "Víz alatt", "Napsütötte tengerpart"]},
     """
S .root { position:absolute; inset:0; color:#fff; font-family:'Inter', sans-serif; background:transparent; }
S .top { position:absolute; left:56px; right:56px; top:96px; }
S .kicker { display:inline-block; font-family:'Barlow Condensed', sans-serif; font-style:italic; font-weight:800;
  font-size:34px; letter-spacing:.06em; text-transform:uppercase; color:#fff;
  background:#DF0EC4; padding:8px 22px 6px; border-radius:12px; box-shadow:0 0 30px rgba(223,14,196,.6); }
S .slot { position:relative; margin-top:22px; height:120px; }
S .chip { position:absolute; left:0; top:0; opacity:0; font-family:'Barlow Condensed', sans-serif; font-style:italic;
  font-weight:800; font-size:84px; line-height:1; text-transform:uppercase; color:#fff; padding:16px 34px 10px;
  border-radius:22px; white-space:nowrap; text-shadow:0 2px 14px rgba(0,0,0,.45); }
S .t0 { background:linear-gradient(100deg,#ff5f2e 0%,#DF0EC4 80%); box-shadow:0 0 40px rgba(255,95,46,.75); }
S .t1 { background:linear-gradient(100deg,#1d8fe0 0%,#5E44E4 80%); box-shadow:0 0 40px rgba(29,143,224,.75); }
S .t2 { font-size:72px; background:linear-gradient(100deg,#f5b52e 0%,#C44DB8 85%); box-shadow:0 0 40px rgba(245,181,46,.75); }
""",
     """<div class="top">
  <div class="kicker" id="card-03-kicker" data-anim="slide-in" data-anim-at="0.1" data-anim-duration="0.4" data-anim-from="left" data-anim-distance="60">Lehet akár…</div>
  <div class="slot">
    <div class="chip t0" id="card-03-t0" data-anim="scale-pop" data-anim-at="0.6" data-anim-duration="0.45">Lángoló haj</div>
    <div class="chip t1" id="card-03-t1" data-anim="scale-pop" data-anim-at="2.75" data-anim-duration="0.45">Víz alatt</div>
  </div>
</div>
<i id="card-03-t0x" data-anim="fade-out" data-anim-at="2.45" data-anim-duration="0.25" data-anim-target="card-03-t0"></i>""",
     "full")

# 6 — Just type the script (split) ───────────────────────────────────────────
PROMPT = "Szia! Ma megmutatom, hogyan készül egy AI-avatár videó…"
card("card-04", 44.7, 51.95, "side-panel",
     "Just type what it should say — the AI says it in your voice with your movements",
     {"kicker": "Csak beírod", "prompt": PROMPT, "outputs": ["Saját hang", "Saját mozgás"]},
     COMMON_SPLIT_CSS + """
S .box { margin-top:38px; background:rgba(255,255,255,.08); border:3px solid #9570FF; border-radius:24px;
  padding:28px 30px; min-height:200px; box-shadow:0 0 30px rgba(149,112,255,.45); }
S .lbl { font-size:26px; font-weight:600; letter-spacing:.08em; text-transform:uppercase; color:#9570FF; }
S .typed { margin-top:14px; font-size:44px; font-weight:600; line-height:1.3; color:#fff; }
S .cursor { display:inline-block; width:4px; height:46px; margin-left:4px; vertical-align:-6px; background:#DF0EC4; }
S .row { display:flex; align-items:center; gap:20px; margin-top:38px; }
S .arrow { font-family:'Barlow Condensed', sans-serif; font-weight:800; font-size:70px; color:#DF0EC4; }
S .out { font-family:'Barlow Condensed', sans-serif; font-style:italic; font-weight:800; font-size:52px;
  text-transform:uppercase; padding:12px 26px 8px; border-radius:16px; color:#fff; }
S .o0 { background:#5E44E4; box-shadow:0 0 26px rgba(94,68,228,.85); }
S .o1 { background:#C44DB8; box-shadow:0 0 26px rgba(196,77,184,.85); }
""",
     f"""<div class="kicker" id="card-04-kicker" data-anim="slide-in" data-anim-at="0.1" data-anim-duration="0.4" data-anim-from="left" data-anim-distance="60">Csak beírod</div>
<div class="box" id="card-04-box" data-anim="fade-in" data-anim-at="0.3" data-anim-duration="0.4">
  <div class="lbl">Mit mondjon az avatár?</div>
  <div class="typed" id="card-04-typed" data-anim="typewriter" data-anim-at="0.6" data-anim-duration="0.12" data-anim-stagger="0.035">{chars(PROMPT)}<span class="cursor"></span></div>
</div>
<div class="row">
  <div class="arrow" id="card-04-arrow" data-anim="slide-in" data-anim-at="2.85" data-anim-duration="0.4" data-anim-from="left" data-anim-distance="40">→</div>
  <div class="out o0" id="card-04-o0" data-anim="scale-pop" data-anim-at="3.0" data-anim-duration="0.45">Saját hang</div>
  <div class="out o1" id="card-04-o1" data-anim="scale-pop" data-anim-at="3.7" data-anim-duration="0.45">Saját mozgás</div>
</div>""",
     "split")

# 7 — CTA (overlay) ──────────────────────────────────────────────────────────
card("card-05", 52.05, 60.2, "video-overlay",
     "CTA: follow us and watch the HeyGen avatar-generation video series",
     {"kicker": "Videósorozat", "title": "HeyGen avatár-generálás lépésről lépésre", "cta": "Kövess minket"},
     COMMON_OVERLAY_CSS + """
S .title { font-size:104px; }
S .cta { display:inline-flex; align-items:center; gap:18px; margin-top:36px; padding:18px 38px 12px;
  border-radius:20px; background:#DF0EC4; font-family:'Barlow Condensed', sans-serif; font-style:italic;
  font-weight:800; font-size:66px; text-transform:uppercase; box-shadow:0 0 44px rgba(223,14,196,.9); }
S .plus { font-size:70px; line-height:1; }
""",
     f"""<div class="scrim"></div>
<div class="top">
  <div class="kicker" id="card-05-kicker" data-anim="slide-in" data-anim-at="0.1" data-anim-duration="0.4" data-anim-from="left" data-anim-distance="60">Részletesen · videósorozat</div>
  <h1 class="title" id="card-05-title" data-anim="kinetic-chars" data-anim-at="0.3" data-anim-duration="0.45" data-anim-stagger="0.02">{chars("HeyGen avatár-")}<br>{chars("generálás")}<br>{chars("lépésről lépésre")}</h1>
  <div class="cta" id="card-05-cta" data-anim="scale-pop" data-anim-at="4.05" data-anim-duration="0.5"><span class="plus">+</span>Kövess minket</div>
</div>""", "full")

# 8 — Outro (fullscreen) ─────────────────────────────────────────────────────
card("card-06", 60.3, None, "fullscreen",
     "Neutral brand outro: Amazing AI logo + tagline",
     {"logo": "Amazing AI", "tagline": "AI-avatárok · videók · automatizáció"},
     """
S .root { position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center;
  background: radial-gradient(70% 45% at 50% 50%, #4A1FA8 0%, #2a1170 40%, #0A0818 85%); color:#fff;
  font-family:'Inter', sans-serif; }
S .logo { width:760px; height:auto; filter:drop-shadow(0 0 40px rgba(149,112,255,.9)); }
S .tag { margin-top:46px; font-family:'Barlow Condensed', sans-serif; font-style:italic; font-weight:800;
  text-transform:uppercase; font-size:56px; letter-spacing:.04em; color:#C9B6FF; }
S .line { margin-top:30px; height:6px; width:0; border-radius:3px; background:linear-gradient(90deg,#5E44E4,#DF0EC4);
  box-shadow:0 0 22px rgba(223,14,196,.8); }
""",
     """<img class="logo" id="card-06-logo" src="img/amazing_logo.png" alt="Amazing AI" data-anim="scale-pop" data-anim-at="0.25" data-anim-duration="0.6">
<div class="line" id="card-06-line" data-anim="grow-x" data-anim-at="0.8" data-anim-duration="0.6" data-anim-target-w="560"></div>
<div class="tag" id="card-06-tag" data-anim="fade-in" data-anim-at="1.0" data-anim-duration="0.5">Kövess minket a további videókért</div>""",
     "hidden")


# ── Card fragments ──────────────────────────────────────────────────────────
def card_html(c):
    return (f'<div class="card" data-card-id="{c["id"]}">\n<style>{scoped(c["id"], c["css"])}</style>\n'
            f'<div class="root">\n{c["body"]}\n</div>\n</div>\n')


ZONE_BOUNDS = {
    "video-overlay": (0, 0, W, H),
    "fullscreen": (0, 0, W, H),
    "side-panel": (0, 0, W, 960),  # split recipe: card top half, video bottom half
}

# ── Compile data-anim declarations ──────────────────────────────────────────
ATTR = re.compile(r'(data-anim[\w-]*|id)="([^"]*)"')
TAG = re.compile(r"<[a-zA-Z0-9]+\s[^>]*data-anim=\"[^\"]+\"[^>]*>")


def compile_anims(c):
    out = []
    for tag in TAG.findall(c["body"]):
        a = dict(ATTR.findall(tag))
        kind, eid = a["data-anim"], a["id"]
        t = q(c["start"] + float(a["data-anim-at"]))
        d = float(a.get("data-anim-duration", 0.5))
        sel = f'.card[data-card-id="{c["id"]}"] #{a.get("data-anim-target", eid)}'
        if kind == "fade-in":
            out.append(f"tl.fromTo('{sel}',{{opacity:0}},{{opacity:1,duration:{d},ease:'power2.out'}},{t});")
        elif kind == "fade-out":
            out.append(f"tl.to('{sel}',{{opacity:0,duration:{d},ease:'power2.in'}},{t});")
        elif kind == "slide-in":
            dist = float(a.get("data-anim-distance", 80))
            frm = a.get("data-anim-from", "left")
            prop, val = {"left": ("x", -dist), "right": ("x", dist), "top": ("y", -dist), "bottom": ("y", dist)}[frm]
            out.append(f"tl.fromTo('{sel}',{{opacity:0,{prop}:{val}}},{{opacity:1,{prop}:0,duration:{d},ease:'power3.out'}},{t});")
        elif kind == "kinetic-chars":
            s = float(a.get("data-anim-stagger", 0.04))
            out.append(f"tl.from('{sel} .char',{{opacity:0,y:28,scale:0.7,duration:{d},ease:'back.out(2)',stagger:{s}}},{t});")
        elif kind == "typewriter":
            s = float(a.get("data-anim-stagger", 0.06))
            out.append(f"tl.from('{sel} .char',{{opacity:0,duration:{d},ease:'none',stagger:{s}}},{t});")
        elif kind == "count-up":
            fr, to, fmt = a["data-anim-from"], a["data-anim-to"], a.get("data-anim-format", ".0f")
            out.append("(function(){const o={v:%s};tl.to(o,{v:%s,duration:%s,ease:'power1.inOut',onUpdate:function(){"
                       "const el=document.querySelector('%s');if(el)el.textContent=__fmt(o.v,'%s');}},%s);})();"
                       % (fr, to, d, sel, fmt, t))
        elif kind == "grow-x":
            out.append(f"tl.fromTo('{sel}',{{width:0}},{{width:{a['data-anim-target-w']},duration:{d},ease:'power1.inOut'}},{t});")
        elif kind == "scale-pop":
            out.append(f"tl.fromTo('{sel}',{{opacity:0,scale:0.5}},{{opacity:1,scale:1,duration:{d},ease:'back.out(1.8)'}},{t});")
        elif kind == "mask-reveal":
            out.append(f"tl.fromTo('{sel}',{{clipPath:'inset(0 100% 0 0)'}},{{clipPath:'inset(0 0% 0 0)',duration:{d},ease:'power2.inOut'}},{t});")
        else:
            raise ValueError(kind)
    return out


# ── Captions (word-level, Hungarian) ────────────────────────────────────────
words = [dict(w, start=remap(w["start"]), end=remap(w["end"]))
         for w in json.loads((ROOT / "transcript.json").read_text()) if not in_cut(w["start"])]
chunks, cur = [], []
for i, wd in enumerate(words):
    cur.append(wd)
    text_len = sum(len(x["text"]) + 1 for x in cur)
    nxt = words[i + 1] if i + 1 < len(words) else None
    # keep every chunk on one caption line (~18 chars at 86px Barlow Condensed)
    brk = (wd["text"][-1] in ".,?!" or len(cur) >= 4 or nxt is None
           or text_len + len(nxt["text"]) > 18 or nxt["start"] - wd["end"] > 0.35)
    if brk:
        chunks.append(cur)
        cur = []

caption_html, caption_js = [], []
for n, ch in enumerate(chunks):
    st = q(ch[0]["start"])
    nxt_start = chunks[n + 1][0]["start"] if n + 1 < len(chunks) else ch[-1]["end"] + 0.4
    en = q(min(nxt_start, ch[-1]["end"] + 0.6, DURATION))
    dur = round(en - st, 4)
    spans = " ".join(f'<span class="cw" id="cw-{n}-{k}">{html.escape(x["text"].rstrip(",."))}</span>'
                     for k, x in enumerate(ch))
    caption_html.append(f'<div class="cap clip" id="cap-{n}" data-start="{st}" data-duration="{dur}" '
                        f'data-track-index="3">{spans}</div>')
    caption_js.append(f"tl.fromTo('#cap-{n}',{{opacity:0,y:18,scale:0.92}},{{opacity:1,y:0,scale:1,duration:0.14,ease:'power2.out'}},{st});")
    for k, x in enumerate(ch):
        ws = q(max(x["start"], st))
        caption_js.append(f"tl.set('#cw-{n}-{k}',{{className:'cw on'}},{ws});")
        if k + 1 < len(ch):
            caption_js.append(f"tl.set('#cw-{n}-{k}',{{className:'cw'}},{q(max(ch[k + 1]['start'], ws + 1 / FPS))});")

# ── Timeline: cards + framing transitions ───────────────────────────────────
js = []
host_html = []
for c in CARDS:
    x, y, w, h = ZONE_BOUNDS[c["zone"]]
    st, en = q(c["start"]), q(min(c["end"], DURATION))
    host_html.append(
        f'<div class="card-host clip" id="{c["id"]}-host" data-card-id="{c["id"]}" data-start="{st}" data-duration="{round(en - st, 4)}" '
        f'data-track-index="2" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;visibility:hidden;opacity:0;">\n'
        f'{card_html(c)}</div>')
    sel = f'.card-host[data-card-id="{c["id"]}"]'
    js.append(f"// {c['id']} [{st}–{en}] {c['intent']}")
    js.append(f"tl.set('{sel}',{{visibility:'visible'}},{st});")
    js.append(f"tl.fromTo('{sel}',{{opacity:0}},{{opacity:1,duration:0.35,ease:'power2.out'}},{st});")
    js.extend(compile_anims(c))
    if en < DURATION - 0.05:
        js.append(f"tl.to('{sel}',{{opacity:0,duration:0.3,ease:'power2.in'}},{q(en - 0.3)});")
        js.append(f"tl.set('{sel}',{{visibility:'hidden'}},{en});")

# Video + caption band follow the framing of each card. Transition starts 0.25s
# before the incoming card so the move reads as a split-screen "wipe".
prev = CARDS[0]["framing"]  # the opening framing is set at t=0 below
for c in CARDS:
    f = c["framing"]
    if f == prev:
        continue
    t = q(c["start"] - 0.3)
    if f == "split":
        js.append(f"tl.to('#video-inner',{{x:{SPLIT['x']},y:{SPLIT['y']},scale:{SPLIT['scale']},duration:0.6,ease:'power3.inOut'}},{t});")
        js.append(f"tl.to('#captions',{{y:{CAP_TOP['split'] - CAP_TOP['full']},duration:0.6,ease:'power3.inOut'}},{t});")
    elif f == "full":
        js.append(f"tl.to('#video-inner',{{x:{FULL['x']},y:{FULL['y']},scale:{FULL['scale']},duration:0.6,ease:'power3.inOut'}},{t});")
        js.append(f"tl.to('#captions',{{y:0,duration:0.6,ease:'power3.inOut'}},{t});")
    elif f == "hidden":
        js.append(f"tl.to('#video-wrap',{{scale:0.86,opacity:0,duration:0.6,ease:'power2.in'}},{t});")
    prev = f

# ── FX: flaming hair → underwater (inside the full-bleed card-03) ─────────────
# Cutaways to her HeyGen avatar promo (heygen_promo_cio_.mp4, 5.52–8.82s and
# 9.0–12.8s, muted, cropped to 9:16 → public/fx-fire.mp4 / fx-water.mp4); her
# own voice keeps running underneath. Times on the uncut timeline, remapped.
FIRE = (remap(34.3), remap(36.55))     # "…a hajad lángoló, lehet akár…"
WATER = (remap(36.55), remap(38.28))   # "…az egész tested víz alatt"

FX_JS = f"""
// ── FX: avatar cutaways, hard cut in with a small punch-out ──
tl.fromTo('#fx-fire-clip', {{ scale: 1.12 }}, {{ scale: 1, duration: 0.5, ease: 'power3.out' }}, {q(FIRE[0])});
tl.fromTo('#fx-water-clip', {{ scale: 1.12 }}, {{ scale: 1, duration: 0.5, ease: 'power3.out' }}, {q(WATER[0])});
"""

START_KEY = CARDS[0]["framing"]
START = SPLIT if START_KEY == "split" else FULL

# ── Assemble ────────────────────────────────────────────────────────────────
def ff(family, file_stub, weight, style):
    return "\n".join(
        f"@font-face{{font-family:'{family}';src:url('fonts/{file_stub.format(sub=sub)}') format('woff2');"
        f"font-weight:{weight};font-style:{style};font-display:block;unicode-range:{rng};}}"
        for sub, rng in (("latin", LATIN), ("latin-ext", LATIN_EXT)))


FONTS = "\n".join([
    ff("Barlow Condensed", "barlow-condensed-{sub}-700-italic.woff2", 700, "italic"),
    ff("Barlow Condensed", "barlow-condensed-{sub}-800-italic.woff2", 800, "italic"),
    ff("Inter", "inter-{sub}-400-normal.woff2", 400, "normal"),
    ff("Inter", "inter-{sub}-600-normal.woff2", 600, "normal"),
    ff("Inter", "inter-{sub}-800-normal.woff2", 800, "normal"),
])

INDEX = f"""<!doctype html>
<html lang="hu">
<head>
<meta charset="utf-8" />
<style>
{FONTS}
:root {{ --bg:#0D0B1E; --text:#ffffff; --accent-0:#5E44E4; --accent-1:#DF0EC4; --accent-2:#9570FF; --accent-3:#C44DB8; --accent-4:#7129D6; }}
* {{ box-sizing:border-box; }}
html, body {{ margin:0; padding:0; width:100%; height:100%; overflow:hidden; background:#0D0B1E;
  font-family:'Inter', 'Barlow Condensed', ui-sans-serif, system-ui, sans-serif; }}
#stage {{ position:relative; width:{W}px; height:{H}px; overflow:hidden; background:#0D0B1E; }}
.video-wrapper {{ position:absolute; left:0; top:0; width:{W}px; height:{H}px; overflow:hidden; }}
#video-inner {{ position:absolute; left:0; top:0; width:{SRC_W}px; height:{H}px; transform-origin:0 0; }}
#video-inner video {{ width:100%; height:100%; display:block; }}
.card-host {{ position:absolute; pointer-events:none; overflow:hidden; z-index:2; }}
.fx-cut {{ position:absolute; left:0; top:0; width:{W}px; height:{H}px; overflow:hidden; z-index:1; pointer-events:none; }}
.fx-cut video {{ width:100%; height:100%; object-fit:cover; display:block; }}
#avatar-video {{ position:absolute; left:0; top:0; width:{W}px; height:960px; object-fit:cover; object-position:50% 30%; z-index:1; }}
.card-host .card {{ position:relative; width:100%; height:100%; overflow:hidden; }}
#captions {{ z-index:3; position:absolute; left:40px; right:40px; top:{CAP_TOP['full']}px; height:160px; pointer-events:none; }}
.cap {{ position:absolute; left:0; right:0; top:0; text-align:center; font-family:'Barlow Condensed', sans-serif;
  font-style:italic; font-weight:800; font-size:86px; line-height:1.05; text-transform:uppercase; color:#fff;
  -webkit-text-stroke:3px #0D0B1E; paint-order:stroke fill;
  text-shadow:0 0 18px rgba(13,11,30,.9), 0 6px 22px rgba(0,0,0,.6); }}
.cw {{ display:inline-block; }}
.cw.on {{ color:#FF4FE0; text-shadow:0 0 22px rgba(223,14,196,.95), 0 0 6px rgba(223,14,196,.9), 0 6px 22px rgba(0,0,0,.6); }}
</style>
</head>
<body>
<div id="stage" data-composition-id="talking-head-recut" data-start="0" data-duration="{DURATION}" data-fps="{FPS}" data-width="{W}" data-height="{H}">
<div class="video-wrapper" id="video-wrap">
<div id="video-inner">
<video id="bg-video" src="input-video.mp4" playsinline data-has-audio="true" data-start="0" data-duration="{DURATION}" data-track-index="1"></video>
</div>
</div>
<div class="fx-cut" id="fx-fire-clip"><video id="fx-fire-video" class="clip" src="fx-fire.mp4" muted playsinline data-start="{q(FIRE[0])}" data-duration="{q(FIRE[1] - FIRE[0])}" data-track-index="6"></video></div>
<div class="fx-cut" id="fx-water-clip"><video id="fx-water-video" class="clip" src="fx-water.mp4" muted playsinline data-start="{q(WATER[0])}" data-duration="{q(WATER[1] - WATER[0])}" data-track-index="7"></video></div>
<video id="avatar-video" class="clip" src="avatar-intro.mp4" muted playsinline data-start="0" data-duration="{q(AVATAR_END)}" data-track-index="4"></video>
{chr(10).join(host_html)}
<div id="captions">
{chr(10).join(caption_html)}
</div>
<script src="vendor/gsap.min.js"></script>
<script>
(function () {{
window.__fmt = function (v, fmt) {{
  if (typeof fmt === "string" && /^\\.[0-9]+f$/.test(fmt)) return Number(v).toFixed(Number(fmt.slice(1, -1)));
  if (fmt === ",d") return Math.round(v).toLocaleString();
  return String(Math.round(v));
}};
const tl = window.gsap.timeline({{ paused: true }});
tl.set('#video-inner',{{x:{START['x']},y:{START['y']},scale:{START['scale']}}},0);
tl.set('#captions',{{y:{CAP_TOP[START_KEY] - CAP_TOP['full']}}},0);
// muted HeyGen avatar on the top half, fades out as the how-to card takes over
tl.to('#avatar-video',{{opacity:0,duration:0.3,ease:'power2.in'}},{q(AVATAR_END - 0.3)});
{chr(10).join(js)}
{FX_JS}
// ── captions ──
{chr(10).join(caption_js)}
window.__timelines = window.__timelines || {{}};
window.__timelines["talking-head-recut"] = tl;
}})();
</script>
</div>
</body>
</html>
"""

if __name__ == "__main__":
    (PUB / "cards").mkdir(parents=True, exist_ok=True)
    for c in CARDS:
        (PUB / "cards" / f"{c['id']}.html").write_text(card_html(c))
    (PUB / "index.html").write_text(INDEX)
    storyboard = {
        "schemaVersion": 3,
        "composition": {"fps": FPS, "width": W, "height": H, "durationSeconds": DURATION,
                        "layout": "portrait", "themeId": "amazing-ai-neon", "seed": 42},
        "videoTrack": {"sourcePath": "input-video.mp4", "startSec": 0, "endSec": DURATION,
                       "bounds": {"x": 0, "y": 0, "width": W, "height": H}},
        "subtitles": {"enabled": True, "style": "karaoke word highlight", "chunks": len(chunks)},
        "cards": [{"id": c["id"], "intent": c["intent"], "startSec": c["start"], "endSec": min(c["end"], DURATION),
                   "accentIndex": i % 5, "zone": c["zone"], "contentHints": c["hints"]}
                  for i, c in enumerate(CARDS)],
    }
    (ROOT / "storyboard.json").write_text(json.dumps(storyboard, ensure_ascii=False, indent=2))
    print(f"{len(CARDS)} cards, {len(chunks)} caption chunks, duration {DURATION}s")
