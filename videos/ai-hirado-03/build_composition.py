#!/usr/bin/env python3
"""AI híradó 2026.10.29 — assemble public/index.html.

Layers (back → front): the recording (uncut, split around the show intro) · side data
cards on the free right-hand wall · full-screen story bumpers and data scenes · show bug
· show intro + flashes · subtitles. Sound is one pre-mixed track (mix_audio.py).
Every figure on screen comes from the sources named on its card (no unverified numbers).
Shared card / subtitle styles live in base.css (same look as híradó 10.22).
Run:  python3 build_composition.py
"""
import html
from pathlib import Path

from captions_src import SENTENCES
from edit import CUT, INTRO, O, SRC_DUR, TOTAL

ROOT = Path(__file__).resolve().parent
FPS, W, H = 25, 1920, 1080
I0, I1 = INTRO
T_VIDEO = round(TOTAL, 3)
T_AUDIO = 150.4   # the recording's audio track is ~0.1 s shorter than its video


def q(t):
    return round(round(t * FPS) / FPS, 4)


def esc(s):
    return html.escape(s).replace("-", "‑")  # keep hyphenated words on one line


# ── full-screen story bumpers (source times): the spoken headline, shown full frame ──
BUMPERS = [
    ("b1", 14.15, 18.45, "1 / 4", "OpenAI: 722 matekkézirat egy titkos modelltől"),
    ("b2", 52.5, 55.55, "2 / 4", "A Claude Mythos 5 kvantumáramköröket tervez"),
    ("b3", 85.5, 88.15, "3 / 4", "Megjött a Gemini 4 Argon"),
    ("b4", 114.5, 117.0, "4 / 4", "„Elkezdődött a szingularitás”"),
]

# ── subtitles: ≤2-line chunks timed by character share, hidden under the bumpers ──
MAX = 84


def chunks(text):
    out, cur = [], ""
    for w in text.split():
        if cur and len(cur) + 1 + len(w) > MAX:
            out.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    out.append(cur)
    if len(out) > 1 and len(out[-1]) < 22:
        both = (out[-2] + " " + out[-1]).split()
        half = len(both) // 2
        out[-2:] = [" ".join(both[:half]), " ".join(both[half:])]
    return out


def under_bumper(src):
    return any(b0 <= src < b1 for _, b0, b1, _, _ in BUMPERS)


subs = []
for s0, s1, text in SENTENCES:
    if under_bumper(s0):
        continue
    parts = chunks(text)
    total = sum(len(p) for p in parts)
    t = s0
    for p in parts:
        d = (s1 - s0) * len(p) / total
        subs.append((q(O(t)), q(O(t + d)), p))
        t += d
for i in range(len(subs) - 1):
    a0, a1, p = subs[i]
    b0 = subs[i + 1][0]
    if 0 < b0 - a1 < 0.6:
        subs[i] = (a0, b0, p)
sub_html = [
    f'<div id="sub-{i}" class="clip subw" data-start="{a}" data-duration="{round(b - a, 4)}" data-track-index="9">'
    f'<div class="sub">{esc(p)}</div></div>'
    for i, (a, b, p) in enumerate(subs) if b - a > 0.05
]


# ── side cards (source times) ────────────────────────────────────────────────
def bar(label, value, pct, cls=""):
    return (f'<div class="row"><div class="rl">{label}</div><div class="track"><div class="fill {cls}" '
            f'data-w="{pct}"></div></div><div class="rv">{value}</div></div>')


def item(text, kind="ok"):
    return f'<li class="li {kind}"><span class="mark"></span><span>{text}</span></li>'


def numbered(items):
    return '<ul class="list">' + "".join(
        f'<li class="li num"><span class="nmark">{n}</span><span>{t}</span></li>' for n, t in enumerate(items, 1)) + "</ul>"


SRC_OPENAI = "Forrás: OpenAI (GitHub-katalógus), Decrypt, 2026.10.06"
SRC_ANTH = "Forrás: Anthropic Research – „Designing more efficient quantum circuits with Claude”, 2026.10."
CARDS = [
    dict(id="c0", start=0.4, end=13.8, kicker="Az adásban", source="",
         phases=[(0.4, "A hét AI‑hírei", numbered([
             "OpenAI: 722 matekkézirat egy titkos modelltől",
             "Claude Mythos 5: kvantumáramköröket tervez",
             "Google: megjött a Gemini 4 Argon",
             "Anthropic‑társalapító: „elkezdődött a szingularitás”"]))]),
    dict(id="c1", start=18.6, end=25.9, kicker="OpenAI · matematika", source=SRC_OPENAI,
         phases=[(18.6, "Közzétéve: 2026. október 6.",
                  '<div class="big">722</div><div class="note">matematikai kézirat egy belső, meg nem nevezett modelltől</div>'
                  '<ul class="list">' + item("372 eredménycsalád") + item("17 matematikai terület")
                  + item("Egyik sem szakmailag lektorált", "warn") + "</ul>")]),
    dict(id="c1b", start=41.3, end=47.2, kicker="OpenAI · visszavonás",
         source="Forrás: Retraction Watch, OpenAI változásnapló, 2026.10.07",
         phases=[(41.3, "Egy nappal később",
                  '<div class="big">722 → 719</div>'
                  '<div class="note">3 kéziratot visszavontak egy előjelhiba miatt, további 14‑et javítottak.</div>')]),
    dict(id="c2", start=55.6, end=63.3, kicker="Anthropic · kvantumáramkörök", source=SRC_ANTH,
         phases=[(55.6, "Egyetlen futás",
                  '<div class="big">53 óra</div><div class="note">a Claude Mythos 5 zárt körben javasolt, '
                  'kapott pontszámot és javított, emberi közbeavatkozás nélkül</div>'
                  '<div class="sub2">Partnerek</div><ul class="list">'
                  + item("Harvard: Susanne Yelin, Mikhail Lukin") + item("QuEra Computing") + "</ul>")]),
    dict(id="c2b", start=74.8, end=81.7, kicker="A hátulütő", source=SRC_ANTH,
         phases=[(74.8, "Qubitigény",
                  '<div class="big">+12%</div><div class="note">ennyivel több qubit kell, mint a legkisebb korábbi '
                  'áramkörhöz – cserébe 17× kevesebb kapuval fut.</div>')]),
    dict(id="c3", start=88.2, end=111.6, kicker="Google · Gemini 4 Argon",
         source="Forrás: Google blog, Google AI for Developers, 9to5Google, 2026.10.13–14",
         phases=[
             (88.2, "Elérhető: 2026. október 13.",
              '<div class="duo"><div class="pill">Google AI Pro</div><div class="pill">Ultra</div></div>'
              '<div class="note" style="margin-top:18px">a Gemini appban és a Keresés AI módjában; '
              'az ingyenes csomagban egyelőre nincs benne</div>'),
             (94.5, "Hosszú válaszok",
              '<div class="big">~1M token</div><div class="note">kimeneti limit, az inputtal közös '
              '1 048 576 tokenes kereten belül</div>'),
             (102.5, "Feladatmód és appok",
              '<div class="big">40+ app</div><div class="note">a feladatok akkor is futnak, amikor nem vagy gépnél</div>'
              '<ul class="list">' + item("Instacart") + item("Shopify") + item("OpenTable") + item("Adobe") + "</ul>"),
         ]),
    dict(id="c4", start=117.1, end=136.9, kicker="Anthropic · Jack Clark",
         source="Forrás: The Rundown AI, indica News, 2026.10.17–18",
         phases=[
             (117.1, "Ki mondta és hol?",
              '<div class="quote">„A szingularitás elkezdődött.”</div>'
              '<div class="note">Jack Clark, az Anthropic társalapítója, az IMF és a Világbank ülésén, '
              'Bangkokban, 2026. október 17‑én</div>'),
             (125.5, "Amire hivatkozott",
              '<div class="sub2">Humanity’s Last Exam</div>' + bar("2025", "8%", 8, "lil") + bar("most", "67,7%", 67.7, "mag")
              + '<div class="sub2">FrontierMath</div>' + bar("2025", "2%", 2, "lil") + bar("most", "94%", 94, "mag")
              + '<div class="note">AI‑modellek legjobb eredménye a két nehéz teszten</div>'),
         ]),
    dict(id="c5", start=137.3, end=145.0, kicker="A hét röviden", source="",
         phases=[(137.3, "Matek · kvantum · új modellek",
                  '<ul class="list">' + item("722 matekkézirat, ebből 162 Lean‑ellenőrzött")
                  + item("17× kevesebb kapu egy kvantumáramkörben") + item("Gemini 4 Argon: 40+ app, feladatmód")
                  + item("A kérdés: ki ellenőrzi, amit az AI kitalál?", "warn") + "</ul>")]),
]

# ── full-screen data scenes (source times) ───────────────────────────────────
N_DOTS, N_LEAN = 722, 162
dots = "".join(f'<i class="d{" h" if k < N_LEAN else ""}"><b></b></i>' for k in range(N_DOTS))
FULL = [
    dict(id="f1", start=26.0, end=34.55, html=(
        '<div class="fs-col">'
        '<div class="fs-kick">OpenAI · 2026. október 6.</div>'
        '<div class="fs-title">Mennyit ellenőrzött gép?</div>'
        '<div class="stat"><b>722</b><span>kézirat</span></div>'
        '<div class="stat"><b>17</b><span>matematikai terület</span></div>'
        '<div class="stat hl"><b>162</b><span>kézirat fő eredménye Lean‑nel formalizálva (22%)</span></div>'
        '</div>'
        f'<div class="waffle">{dots}</div>'
        '<div class="fs-legend"><span><i class="lg h"></i>Lean‑nel ellenőrzött fő eredmény</span>'
        '<span><i class="lg"></i>gépi ellenőrzés nélkül</span></div>'
        f'<div class="fs-src">{SRC_OPENAI}</div>')),
    dict(id="f2", start=63.5, end=73.6, phases=[
        (63.5, "Anthropic · Claude Mythos 5", "Elliptikus görbés áramkör: kapuk száma",
         bar("Eddigi legjobb", "100%", 100, "lil") + bar("Claude", "~6%", 5.9, "mag"),
         "17×", "kevesebb kapu"),
        (68.0, "Anthropic · Claude Mythos 5", "DQI‑dekóder: Toffoli‑kapuk száma",
         bar("Korábbi (Google)", "5,1 millió", 100, "lil") + bar("Claude", "~440 ezer", 8.6, "mag"),
         "~12×", "olcsóbb a legdrágább lépés"),
    ], src=SRC_ANTH),
]

# ── HTML + timeline ──────────────────────────────────────────────────────────
js, layers = [], []


def card_html(g):
    s, e = q(O(g["start"])), q(O(g["end"]))
    ph = "".join(f'<div class="phase" id="{g["id"]}-p{k}"><div class="ptitle">{t}</div>{body}</div>'
                 for k, (_, t, body) in enumerate(g["phases"]))
    srcline = f'<div class="src">{g["source"]}</div>' if g["source"] else ""
    layers.append(
        f'<div id="{g["id"]}" class="clip gw" data-start="{s}" data-duration="{round(e - s, 4)}" data-track-index="3">'
        f'<div class="gcard"><div class="kick">{g["kicker"]}</div><div class="phases">{ph}</div>{srcline}</div></div>')
    sel = f'#{g["id"]} .gcard'
    js.append(f"tl.fromTo('{sel}',{{autoAlpha:0,x:70}},{{autoAlpha:1,x:0,duration:0.55,ease:'power3.out'}},{s});")
    js.append(f"tl.to('{sel}',{{autoAlpha:0,x:40,duration:0.4,ease:'power2.in'}},{q(e - 0.4)});")
    for k, (pt, _, _) in enumerate(g["phases"]):
        p = f'#{g["id"]}-p{k}'
        t0 = q(O(pt) + (0.25 if k == 0 else 0))
        js.append(f"tl.fromTo('{p}',{{autoAlpha:0,y:18}},{{autoAlpha:1,y:0,duration:0.45,ease:'power3.out'}},{t0});")
        if k + 1 < len(g["phases"]):
            js.append(f"tl.to('{p}',{{autoAlpha:0,y:-12,duration:0.3,ease:'power2.in'}},{q(O(g['phases'][k + 1][0]) - 0.3)});")
        js.append(f"tl.fromTo('{p} .fill',{{scaleX:0}},{{scaleX:1,duration:0.9,ease:'power3.out',stagger:0.18}},{q(t0 + 0.2)});")
        js.append(f"tl.fromTo('{p} .li',{{autoAlpha:0,x:24}},{{autoAlpha:1,x:0,duration:0.4,ease:'power2.out',stagger:0.45}},{q(t0 + 0.4)});")


def fs_wrap(fid, s, e, inner, extra=""):
    layers.append(
        f'<div id="{fid}" class="clip fsw" data-start="{s}" data-duration="{round(e - s, 4)}" data-track-index="4">'
        f'<div class="fs {extra}"><div class="fs-grid"></div><div class="fs-glow"></div>'
        f'<img class="fs-logo" src="img/amazing_logo.svg" alt="" />{inner}</div></div>')
    js.append(f"tl.fromTo('#{fid} .fs',{{autoAlpha:0,scale:1.04}},{{autoAlpha:1,scale:1,duration:0.4,ease:'power2.out'}},{s});")
    js.append(f"tl.to('#{fid} .fs',{{autoAlpha:0,duration:0.35,ease:'power2.in'}},{q(e - 0.35)});")


for fid, b0, b1, num, title in BUMPERS:
    s, e = q(O(b0)), q(O(b1))
    fs_wrap(fid, s, e, f'<div class="bump"><div class="bump-num">{num}</div><div class="bump-title">{esc(title)}</div>'
                       f'<div class="bump-line"></div></div>', "is-bump")
    js.append(f"tl.fromTo('#{fid} .bump-num',{{autoAlpha:0,x:-40}},{{autoAlpha:1,x:0,duration:0.45,ease:'power3.out'}},{q(s + 0.1)});")
    js.append(f"tl.fromTo('#{fid} .bump-title',{{autoAlpha:0,y:50}},{{autoAlpha:1,y:0,duration:0.6,ease:'power3.out'}},{q(s + 0.2)});")
    js.append(f"tl.fromTo('#{fid} .bump-line',{{scaleX:0}},{{scaleX:1,duration:0.8,ease:'power3.inOut'}},{q(s + 0.35)});")

f1 = FULL[0]
s, e = q(O(f1["start"])), q(O(f1["end"]))
fs_wrap("f1", s, e, f1["html"])
js.append(f"tl.fromTo('#f1 .stat',{{autoAlpha:0,x:-30}},{{autoAlpha:1,x:0,duration:0.45,ease:'power3.out',stagger:0.5}},{q(s + 0.3)});")
js.append(f"tl.fromTo('#f1 .d',{{autoAlpha:0,scale:0.2}},{{autoAlpha:1,scale:1,duration:0.3,ease:'power2.out',stagger:0.0016}},{q(s + 0.4)});")
js.append(f"tl.fromTo('#f1 .d.h b',{{scale:0}},{{scale:1,duration:0.35,ease:'back.out(2)',stagger:0.005}},{q(s + 2.2)});")
js.append(f"tl.fromTo('#f1 .fs-legend',{{autoAlpha:0}},{{autoAlpha:1,duration:0.4}},{q(s + 2.4)});")

f2 = FULL[1]
s, e = q(O(f2["start"])), q(O(f2["end"]))
ph = "".join(
    f'<div class="fphase" id="f2-p{k}"><div class="fs-kick">{kick}</div><div class="fs-title">{esc(t)}</div>'
    f'<div class="fbars">{bars}</div><div class="fbig"><b>{big}</b><span>{small}</span></div></div>'
    for k, (_, kick, t, bars, big, small) in enumerate(f2["phases"]))
fs_wrap("f2", s, e, f'<div class="fphases">{ph}</div><div class="fs-src">{f2["src"]}</div>')
for k, (pt, *_rest) in enumerate(f2["phases"]):
    t0 = q(O(pt) + (0.2 if k == 0 else 0))
    js.append(f"tl.fromTo('#f2-p{k}',{{autoAlpha:0,y:24}},{{autoAlpha:1,y:0,duration:0.45,ease:'power3.out'}},{t0});")
    js.append(f"tl.fromTo('#f2-p{k} .fill',{{scaleX:0}},{{scaleX:1,duration:1.0,ease:'power3.out',stagger:0.35}},{q(t0 + 0.3)});")
    js.append(f"tl.fromTo('#f2-p{k} .fbig',{{autoAlpha:0,scale:0.7}},{{autoAlpha:1,scale:1,duration:0.5,ease:'back.out(1.8)'}},{q(t0 + 1.2)});")
    if k + 1 < len(f2["phases"]):
        js.append(f"tl.to('#f2-p{k}',{{autoAlpha:0,y:-16,duration:0.3,ease:'power2.in'}},{q(O(f2['phases'][k + 1][0]) - 0.3)});")

for g in CARDS:
    card_html(g)

EXTRA_CSS = """
.subw { z-index:12; }
/* show bug */
#bug { position:absolute; left:56px; top:46px; z-index:7; display:flex; align-items:center; gap:12px; }
#bug .b1 { font-family:"Archivo"; font-stretch:125%; font-weight:800; font-size:30px; color:#fff; letter-spacing:.02em; text-shadow:0 0 16px rgba(149,112,255,.7); }
#bug .b1 b { color:#dfff84; font-weight:800; }
#bug .b2 { font-family:"Archivo"; font-stretch:115%; font-weight:600; font-size:12px; letter-spacing:.42em; color:#fff; background:var(--lilac); padding:6px 8px 6px 14px; border-radius:3px; }
/* presenter footage + intro */
.pres { position:absolute; inset:0; width:1920px; height:1080px; object-fit:cover; }
#intro { position:absolute; inset:0; width:1920px; height:1080px; object-fit:cover; z-index:20; }
#flash { position:absolute; inset:0; z-index:21; opacity:0; pointer-events:none;
  background:radial-gradient(60% 60% at 50% 50%, #ffffff, rgba(149,112,255,.9) 60%, rgba(13,11,30,.9)); }
/* numbered list in the teaser card */
.li.num { align-items:center; font-size:22px; margin:16px 0; }
.nmark { flex:none; width:38px; height:38px; border-radius:50%; background:linear-gradient(135deg,var(--violet),var(--magenta));
  display:flex; align-items:center; justify-content:center; font-family:"Archivo"; font-weight:800; font-size:19px; }
.quote { font-family:"Archivo"; font-stretch:105%; font-weight:800; font-size:44px; line-height:1.12; color:#fff; margin:6px 0 14px;
  text-shadow:0 0 26px rgba(223,14,196,.45); }
/* full-screen scenes */
.fsw { position:absolute; inset:0; z-index:8; pointer-events:none; }
.fs { position:absolute; inset:0; overflow:hidden; color:#fff; opacity:0; visibility:hidden;
  background:radial-gradient(90% 80% at 75% 20%, #2a1a7a 0%, #160f45 45%, #0d0b1e 100%); }
.fs-grid { position:absolute; inset:0; opacity:.35;
  background-image:linear-gradient(rgba(149,112,255,.18) 1px, transparent 1px), linear-gradient(90deg, rgba(149,112,255,.18) 1px, transparent 1px);
  background-size:64px 64px; }
.fs-glow { position:absolute; width:900px; height:900px; right:-200px; top:-300px; border-radius:50%;
  background:radial-gradient(circle, rgba(223,14,196,.28), rgba(223,14,196,0) 65%); }
.fs-logo { position:absolute; right:64px; top:52px; width:210px; opacity:.9; }
.bump { position:absolute; left:140px; right:140px; top:330px; }
.bump-num { display:inline-block; font-family:"Archivo"; font-stretch:115%; font-weight:800; font-size:30px; letter-spacing:.2em;
  background:var(--violet); padding:10px 20px 9px; border-radius:5px; }
.bump-title { margin-top:34px; font-family:"Archivo"; font-stretch:112%; font-weight:850; font-size:96px; line-height:1.04;
  text-shadow:0 0 40px rgba(149,112,255,.55); max-width:1500px; }
.bump-line { margin-top:38px; width:620px; height:8px; border-radius:4px; transform-origin:left center;
  background:linear-gradient(90deg,var(--lilac),var(--magenta)); box-shadow:0 0 24px rgba(223,14,196,.6); }
.fs-kick { display:inline-block; font-family:"Archivo"; font-stretch:115%; font-weight:800; font-size:20px; letter-spacing:.2em;
  text-transform:uppercase; background:var(--violet); padding:8px 14px 7px; border-radius:4px; }
.fs-title { margin-top:22px; font-family:"Archivo"; font-stretch:110%; font-weight:850; font-size:58px; line-height:1.06; }
.fs-col { position:absolute; left:120px; top:150px; width:560px; }
.stat { margin-top:30px; padding-left:22px; border-left:6px solid var(--lilac); }
.stat b { display:block; font-family:"Archivo"; font-stretch:118%; font-weight:850; font-size:84px; line-height:1; }
.stat span { display:block; margin-top:6px; font-size:24px; line-height:1.3; color:var(--soft); }
.stat.hl { border-left-color:var(--magenta); }
.stat.hl b { color:#ff7ff0; text-shadow:0 0 30px rgba(223,14,196,.6); }
.waffle { position:absolute; left:770px; top:190px; width:1036px; display:grid; grid-template-columns:repeat(38, 20px); gap:7px; }
.waffle .d { position:relative; width:20px; height:20px; border-radius:50%; background:rgba(149,112,255,.32); }
.waffle .d b { position:absolute; inset:0; border-radius:50%; background:var(--magenta); box-shadow:0 0 10px rgba(223,14,196,.8); }
.waffle .d:not(.h) b { display:none; }
.fs-legend { position:absolute; left:770px; top:740px; display:flex; gap:40px; font-size:24px; color:var(--soft); }
.fs-legend span { display:flex; align-items:center; gap:12px; }
.lg { display:inline-block; width:20px; height:20px; border-radius:50%; background:rgba(149,112,255,.45); }
.lg.h { background:var(--magenta); }
.fs-src { position:absolute; left:120px; bottom:200px; font-size:18px; color:#a99bd9; }
.fphases { position:absolute; left:140px; right:140px; top:150px; height:640px; }
.fphase { position:absolute; inset:0; }
.fbars { margin-top:56px; width:1500px; }
.fbars .row { margin:26px 0; gap:24px; }
.fbars .rl { width:260px; font-size:30px; }
.fbars .track { height:56px; border-radius:10px; }
.fbars .fill { border-radius:10px; }
.fbars .rv { width:220px; font-size:38px; }
.fbig { position:absolute; left:0; top:400px; display:flex; align-items:baseline; gap:30px; }
.fbig b { display:block; font-family:"Archivo"; font-stretch:120%; font-weight:850; font-size:200px; line-height:1; color:#fff;
  text-shadow:0 0 50px rgba(223,14,196,.7); }
.fbig span { display:block; font-size:40px; color:var(--soft); }
"""

INDEX = f"""<!doctype html>
<html lang="hu">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width={W}, height={H}" />
<script src="vendor/gsap.min.js"></script>
<style>
{(ROOT / "base.css").read_text()}
{EXTRA_CSS}
</style>
</head>
<body>
<div id="root" data-composition-id="ai-hirado-1029" data-start="0" data-duration="{T_VIDEO}" data-fps="{FPS}" data-width="{W}" data-height="{H}">
<video id="pres-a" class="clip pres" src="source.mp4" muted playsinline data-start="0" data-duration="{q(CUT)}" data-media-start="0" data-track-index="1"></video>
<video id="pres-b" class="clip pres" src="source.mp4" muted playsinline data-start="{q(I1)}" data-duration="{round(SRC_DUR - CUT, 3)}" data-media-start="{CUT}" data-track-index="1"></video>
{chr(10).join(layers)}
<div id="bug" class="clip" data-start="0" data-duration="{T_VIDEO}" data-track-index="6"><div class="b1"><b>AI</b> HÍREK</div><div class="b2">A NAGYVILÁGBÓL</div></div>
<video id="intro" class="clip" src="intro.mp4" muted playsinline data-start="{q(I0)}" data-duration="{q(I1 - I0)}" data-track-index="7"></video>
<div id="flash"></div>
{chr(10).join(sub_html)}
<audio id="mix" src="mix.wav" data-start="0" data-duration="{T_AUDIO}" data-track-index="10"></audio>
</div>
<script>
(function () {{
document.querySelectorAll('.fill[data-w]').forEach(function (el) {{ el.style.width = el.dataset.w + '%'; }});
const tl = gsap.timeline({{ paused: true }});
tl.fromTo('#flash', {{ opacity: 0 }}, {{ opacity: 0.9, duration: 0.16, ease: 'power2.out' }}, {q(I0 - 0.16)});
tl.to('#flash', {{ opacity: 0, duration: 0.3, ease: 'power2.in' }}, {q(I0 + 0.04)});
tl.fromTo('#flash', {{ opacity: 0 }}, {{ opacity: 0.9, duration: 0.16, ease: 'power2.out' }}, {q(I1 - 0.16)});
tl.to('#flash', {{ opacity: 0, duration: 0.36, ease: 'power2.in' }}, {q(I1 + 0.04)});
{chr(10).join(js)}
window.__timelines = window.__timelines || {{}};
window.__timelines["ai-hirado-1029"] = tl;
tl.seek(0);
}})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    (ROOT / "public" / "index.html").write_text(INDEX)
    print(f"{T_VIDEO}s · {len(sub_html)} subtitle chunks · {len(CARDS)} cards · {len(BUMPERS)} bumpers · 2 full-screen scenes")
