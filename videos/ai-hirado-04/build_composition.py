#!/usr/bin/env python3
"""AI híradó 2026.11.05 — assemble public/index.html.

Same format as híradó 10.29: the recording (uncut, split around the show intro) · side
data cards on the free right-hand wall · full-screen story bumpers and data scenes ·
show bug · show intro + flashes · subtitles. Sound is one pre-mixed track (mix_audio.py).
Every figure on screen comes from the sources named on its card (no unverified numbers).
Shared styles live in base.css.
Run:  python3 build_composition.py
"""
import html
import math
from pathlib import Path

from captions_src import SENTENCES
from edit import CUT, INTRO, O, SRC_DUR, TOTAL

ROOT = Path(__file__).resolve().parent
FPS, W, H = 25, 1920, 1080
I0, I1 = INTRO
T_VIDEO = round(TOTAL, 3)
T_AUDIO = 220.43   # the recording's audio track is ~0.1 s shorter than its video


def q(t):
    return round(round(t * FPS) / FPS, 4)


def esc(s):
    return html.escape(s).replace("-", "‑")  # keep hyphenated words on one line


# ── full-screen story bumpers (source times): the spoken headline, full frame ──
BUMPERS = [
    ("b1", 12.15, 15.0, "1 / 6", "Siri AI: több tudás, de korlátokkal"),
    ("b2", 45.4, 49.0, "2 / 6", "Google: kereső csak AI-jal az iskoláknak"),
    ("b3", 78.2, 82.0, "3 / 6", "Anthropic: gigabevétel és egy nyugtalanító mondat"),
    ("b4", 115.0, 118.0, "4 / 6", "NVIDIA: plafon a kínai ügyfeleknek"),
    ("b5", 141.2, 145.0, "5 / 6", "Brazília: a Meta AI-ja nem tanulhat a hírekből"),
    ("b6", 172.0, 174.95, "6 / 6", "Egyszemélyes biotechcéget vett az Anthropic"),
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


def items(*pairs):
    return '<ul class="list">' + "".join(item(*p) if isinstance(p, tuple) else item(p) for p in pairs) + "</ul>"


def numbered(texts):
    return '<ul class="list">' + "".join(
        f'<li class="li num"><span class="nmark">{n}</span><span>{t}</span></li>' for n, t in enumerate(texts, 1)) + "</ul>"


SRC_APPLE_DEV = "Forrás: Apple Developer News, Cult of Mac, 2026.11.03"
SRC_APPLE_Q4 = "Forrás: Apple Q4 2026 negyedéves beszámoló (Yahoo Tech, Benzinga), 2026.11.02"
SRC_GOOGLE = "Forrás: CBS News, TechCrunch, NBC News, Google blog, 2026.11.03–04"
SRC_ANTH = "Forrás: Anthropic S‑1/A (2026.11.02), CNBC, TechCrunch"
SRC_NV = "Forrás: Financial Times (TNW, Yahoo Finance), The Information, 2026.11.03–04"
SRC_BR = "Forrás: AFP (The Star, Malay Mail), 2026.11.04"
SRC_MITH = "Forrás: Anthropic (2026.10.27), R&D World, Becker’s Hospital Review"

CARDS = [
    dict(id="c0", start=0.4, end=11.9, kicker="Az adásban", source="",
         phases=[(0.4, "A hét AI‑hírei", numbered([
             "Siri AI: több tudás, korlátokkal", "Google: kereső csak AI‑jal?",
             "Anthropic: gigabevétel", "NVIDIA: plafon Kínának",
             "Brazília: a Meta nem taníthat hírekből", "Egyszemélyes biotech az Anthropicnál"]))]),
    dict(id="c1", start=15.1, end=32.9, kicker="Apple · Siri AI", source=SRC_APPLE_DEV,
         phases=[
             (15.1, "iOS 27.3 fejlesztői béta · nov. 3.",
              '<div class="big">15 app</div><div class="note">Apple‑alkalmazás, amelyben a Siri AI összetettebb '
              'feladatokat old meg, pl.:</div>'
              + items("Naptár, Zene, Üzenetek", "Emlékeztetők, Időjárás")),
             (27.0, "Külső fejlesztők",
              '<div class="big">jövő tavasz</div><div class="note">ekkortól fogad az App Store Siri AI‑t használó '
              'appokat; a fejlesztői előzetest már bárki kipróbálhatja</div>'),
         ]),
    dict(id="c1b", start=41.3, end=45.35, kicker="Siri AI · EU", source="Forrás: Apple Developer News, 2026.11.03",
         phases=[(41.3, "Elérhetőség",
                  '<div class="big">EU: nincs</div><div class="note">a Siri AI az Európai Unióban '
                  'egyelőre nem érhető el</div>')]),
    dict(id="c2", start=49.1, end=59.95, kicker="Google · iskolák (K‑12)", source=SRC_GOOGLE,
         phases=[
             (49.1, "A feltétel",
              items(("AI‑eszközök kikapcsolva", "no"), ("= nincs Google‑kereső a diákfiókokban", "no"))
              + '<div class="note">Chris Phillips, a Google oktatási alelnöke szerint</div>'),
             (57.3, "A kritika",
              '<div class="quote">„Zsarolás.”</div><div class="note">Bernie Sanders szenátor az X‑en</div>'
              '<div class="sub2">Bírálta még</div>'
              + items(("Richard Blumenthal szenátor", "warn"), ("Lina Khan, volt FTC‑elnök", "warn"))),
         ]),
    dict(id="c2b", start=68.0, end=77.9, kicker="DuckDuckGo", source="Forrás: The AI Insider, 2026.11.05",
         phases=[(68.0, "Az alternatíva",
                  items("Útmutatót adott ki: hogyan legyen alapértelmezett kereső az iskolákban",
                        "Az AI‑funkciói teljesen kikapcsolhatók"))]),
    dict(id="c3", start=101.0, end=114.95, kicker="Anthropic · kockázati tényezők", source=SRC_ANTH,
         phases=[
             (101.0, "A nyugtalanító mondat",
              '<div class="quote" style="font-size:36px">Közel lehet az AI által drámaian felgyorsított fejlődés küszöbe</div>'
              '<div class="note">a cég saját felelős skálázási irányelve (RSP) szerinti küszöb</div>'),
             (108.0, "Az Anthropic szerint",
              items("Egyik mostani modellje sem lépte át a küszöböt",
                    "Emberi felügyelet nélkül nem engedné a Claude‑ot új csúcsmodelleket tervezni és építeni")),
         ]),
    dict(id="c4", start=129.3, end=140.95, kicker="NVIDIA · 49%", source=SRC_NV,
         phases=[(129.3, "Mennyire szigorú?",
                  items("Csak az új szerződésekre vonatkozik", ("The Information: egyelőre nem kötelező", "warn"),
                        ("Az NVIDIA nem erősítette meg a 49%‑ot", "warn")))]),
    dict(id="c5", start=145.0, end=162.95, kicker="Brazília · Meta", source=SRC_BR,
         phases=[
             (145.0, "São Paulo, 2026. november 3.",
              items("Ideiglenes intézkedés (44. polgári bíróság)",
                    ("Tilos a brazil sajtó tartalmain tanítani a Meta AI‑ját", "no"))),
             (152.0, "A felperesek",
              '<div class="duo"><div class="pill">ANJ</div><div class="pill">Abert</div><div class="pill">Aner</div></div>'
              '<div class="note" style="margin-top:18px">három országos médiaszövetség; a Meta november 20‑tól '
              'érvényes új üzleti feltételei miatt pereltek</div>'),
         ]),
    dict(id="c6", start=175.0, end=185.0, kicker="Anthropic · Mithril Medicine", source=SRC_MITH,
         phases=[(175.0, "Bejelentve: 2026. október 27.",
                  '<div class="big">1 fő</div><div class="note">az alapító, Cody Tranbarger volt az egyetlen '
                  'teljes munkaidős alkalmazott</div>'
                  + items("Célpont: LAMA2‑hoz kötött veleszületett izomdisztrófia"))]),
    dict(id="c7", start=200.2, end=210.95, kicker="A hét röviden", source="",
         phases=[(200.2, "Hat hír, egy irány",
                  items("Siri AI: keret + fizetős bővítés", ("Google: kereső csak AI‑jal?", "warn"),
                        "Anthropic: 17 Mrd $ a 3. negyedévben", "NVIDIA: max. 49% kínai ügyfél",
                        "Brazília: tilalom a Metának", "Mithril: 1 ember, 11 labor"))]),
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
    if e < T_VIDEO - 0.05:
        js.append(f"tl.to('#{fid} .fs',{{autoAlpha:0,duration:0.35,ease:'power2.in'}},{q(e - 0.35)});")


def tw(sel, frm, to, at):
    js.append(f"tl.fromTo('{sel}',{{{frm}}},{{{to}}},{q(at)});")


for fid, b0, b1, num, title in BUMPERS:
    s, e = q(O(b0)), q(O(b1))
    fs_wrap(fid, s, e, f'<div class="bump"><div class="bump-num">{num}</div><div class="bump-title">{esc(title)}</div>'
                       f'<div class="bump-line"></div></div>', "is-bump")
    tw(f'#{fid} .bump-num', "autoAlpha:0,x:-40", "autoAlpha:1,x:0,duration:0.45,ease:'power3.out'", s + 0.1)
    tw(f'#{fid} .bump-title', "autoAlpha:0,y:50", "autoAlpha:1,y:0,duration:0.6,ease:'power3.out'", s + 0.2)
    tw(f'#{fid} .bump-line', "scaleX:0", "scaleX:1,duration:0.8,ease:'power3.inOut'", s + 0.35)


def phased_bars(fid, start, end, phases, src):
    """Full-screen bar comparison in phases: (src_t, kicker, title, bars_html, big, small)."""
    s, e = q(O(start)), q(O(end))
    ph = "".join(
        f'<div class="fphase" id="{fid}-p{k}"><div class="fs-kick">{kick}</div><div class="fs-title">{esc(t)}</div>'
        f'<div class="fbars">{bars}</div><div class="fbig"><b>{big}</b><span>{small}</span></div></div>'
        for k, (_, kick, t, bars, big, small) in enumerate(phases))
    fs_wrap(fid, s, e, f'<div class="fphases">{ph}</div><div class="fs-src">{src}</div>')
    for k, (pt, *_r) in enumerate(phases):
        t0 = q(O(pt) + (0.2 if k == 0 else 0))
        tw(f'#{fid}-p{k}', "autoAlpha:0,y:24", "autoAlpha:1,y:0,duration:0.45,ease:'power3.out'", t0)
        js.append(f"tl.fromTo('#{fid}-p{k} .fill',{{scaleX:0}},{{scaleX:1,duration:1.0,ease:'power3.out',stagger:0.35}},{q(t0 + 0.3)});")
        tw(f'#{fid}-p{k} .fbig', "autoAlpha:0,scale:0.7", "autoAlpha:1,scale:1,duration:0.5,ease:'back.out(1.8)'", t0 + 1.2)
        if k + 1 < len(phases):
            js.append(f"tl.to('#{fid}-p{k}',{{autoAlpha:0,y:-16,duration:0.3,ease:'power2.in'}},{q(O(phases[k + 1][0]) - 0.3)});")


# F1 · Siri AI limits
s, e = q(O(33.0)), q(O(41.2))
fs_wrap("f1", s, e,
        '<div class="fs-col wide"><div class="fs-kick">Apple · negyedéves beszámoló, 2026.11.02.</div>'
        '<div class="fs-title">Siri AI: ingyen, de nem korlátlanul</div></div>'
        '<div class="meter"><div class="mfree"><span>Ingyenes keret</span></div>'
        '<div class="mpaid"><span>+ fizetős bővítés</span></div></div>'
        '<div class="mnote">A felhőben (Private Cloud Compute) futó funkciókra jön használati korlát; '
        'az árat és a keret méretét az Apple még nem közölte.</div>'
        '<div class="fstat"><b>2,5 Mrd+</b><span>Siri‑kérés naponta (John Ternus, Apple‑vezérigazgató)</span></div>'
        f'<div class="fs-src">{SRC_APPLE_Q4}</div>')
tw("#f1 .mfree", "scaleX:0", "scaleX:1,duration:1.1,ease:'power3.out'", s + 0.6)
tw("#f1 .mpaid", "autoAlpha:0,x:-40", "autoAlpha:1,x:0,duration:0.6,ease:'power3.out'", s + 2.0)
tw("#f1 .mnote", "autoAlpha:0,y:16", "autoAlpha:1,y:0,duration:0.5,ease:'power2.out'", s + 2.6)
tw("#f1 .fstat", "autoAlpha:0,y:20", "autoAlpha:1,y:0,duration:0.5,ease:'power2.out'", s + 3.6)

# F2 · Google: three toggles, all off by default
s, e = q(O(60.0)), q(O(68.0))
toggles = "".join(f'<div class="tg"><span class="sw"><i></i></span><b>{n}</b><em>alapból kikapcsolva</em></div>'
                  for n in ("Gemini", "Gemini Notebook", "Google‑kereső"))
fs_wrap("f2", s, e,
        '<div class="fs-col wide"><div class="fs-kick">Google · K‑12 diákfiókok</div>'
        '<div class="fs-title">Alapból minden ki van kapcsolva – az iskola dönt</div></div>'
        f'<div class="toggles">{toggles}</div>'
        '<div class="mnote" style="top:760px">A kritikusok szerint a kereső nem kapcsolható be '
        'AI‑összefoglalók nélkül.</div>'
        f'<div class="fs-src">{SRC_GOOGLE}</div>')
js.append(f"tl.fromTo('#f2 .tg',{{autoAlpha:0,x:-50}},{{autoAlpha:1,x:0,duration:0.5,ease:'power3.out',stagger:0.6}},{q(s + 0.5)});")
tw("#f2 .mnote", "autoAlpha:0", "autoAlpha:1,duration:0.5", s + 3.4)

# F3 · Anthropic revenue vs commitments
phased_bars("f3", 86.1, 101.0, [
    (86.1, "Anthropic · S‑1/A, 2026.11.02.", "Bevétel 2026‑ban",
     bar("2. negyedév", "11,6 Mrd $", 68.2, "lil") + bar("3. negyedév", "17,0 Mrd $", 100, "mag"),
     "33,2 Mrd $", "január–szeptember"),
    (94.07, "Anthropic · S‑1/A, 2026.11.02.", "Kötelezettségvállalás a bevételhez képest",
     bar("Bevétel (9 hó)", "33,2 Mrd $", 3.7, "lil") + bar("Kötelezettség", "895,4 Mrd $", 100, "mag"),
     "~27×", "főleg számítási kapacitásra"),
], SRC_ANTH)

# F4 · NVIDIA 49 / 51 split
s, e = q(O(118.0)), q(O(129.2))
fs_wrap("f4", s, e,
        '<div class="fs-col wide"><div class="fs-kick">NVIDIA · Financial Times értesülése</div>'
        '<div class="fs-title">Kinek mehet a felhőkapacitás?</div></div>'
        '<div class="split"><div class="sp cn" style="flex:49"><b>max. 49%</b><span>kínai ügyfelek</span></div>'
        '<div class="sp ot" style="flex:51"><b>min. 51%</b><span>nem kínai ügyfelek</span></div></div>'
        '<div class="mnote" style="top:720px">Az NVIDIA kérése a felhő‑ és adatközpont‑partnereinek, '
        'a jelentés szerint szóban közölve.</div>'
        f'<div class="fs-src">{SRC_NV}</div>')
tw("#f4 .sp.cn", "scaleX:0", "scaleX:1,duration:0.9,ease:'power3.out'", s + 0.6)
tw("#f4 .sp.ot", "scaleX:0", "scaleX:1,duration:0.9,ease:'power3.out'", s + 1.3)
js.append(f"tl.fromTo('#f4 .sp b, #f4 .sp span',{{autoAlpha:0,y:14}},{{autoAlpha:1,y:0,duration:0.45,stagger:0.15}},{q(s + 2.0)});")
tw("#f4 .mnote", "autoAlpha:0", "autoAlpha:1,duration:0.5", s + 3.2)

# F5 · Brazil daily fine
s, e = q(O(163.0)), q(O(168.0))
fs_wrap("f5", s, e,
        '<div class="fs-col wide"><div class="fs-kick">São Paulo · 44. polgári bíróság</div>'
        '<div class="fs-title">Ha a Meta nem tartja be:</div></div>'
        '<div class="hero"><b>R$ 1 millió</b><span>bírság naponta · ≈ 180 000 USD · ≈ 59 millió Ft</span></div>'
        f'<div class="fs-src">{SRC_BR}</div>')
tw("#f5 .hero b", "autoAlpha:0,scale:0.7", "autoAlpha:1,scale:1,duration:0.6,ease:'back.out(1.6)'", s + 0.4)
tw("#f5 .hero span", "autoAlpha:0,y:16", "autoAlpha:1,y:0,duration:0.5", s + 1.0)

# F6 · Mithril: one founder + Claude, eleven labs
s, e = q(O(185.1)), q(O(195.0))
CX, CY, R = 520, 500, 290
nodes, lines = [], []
for k in range(11):
    a = -math.pi / 2 + 2 * math.pi * k / 11
    x, y = CX + R * math.cos(a), CY + R * math.sin(a)
    lines.append(f'<line class="ln" x1="{CX}" y1="{CY}" x2="{x:.1f}" y2="{y:.1f}"/>')
    nodes.append(f'<div class="lab" style="left:{x - 46:.0f}px;top:{y - 46:.0f}px"><b>{k + 1}</b><span>labor</span></div>')
fs_wrap("f6", s, e,
        '<div class="hub">'
        f'<svg class="hub-svg" viewBox="0 0 1040 1040" width="1040" height="1040">{"".join(lines)}</svg>'
        f'{"".join(nodes)}<div class="core"><b>1 alapító</b><span>+ Claude</span></div></div>'
        '<div class="mcol"><div class="fs-kick">Mithril Medicine</div>'
        '<div class="fstat2"><b>11</b><span>külső labor koordinálása a Claude segítségével</span></div>'
        '<div class="fstat2"><b>&lt; 18 hónap</b><span>az ötlettől az ígéretes egérkísérletekig</span></div>'
        '<div class="fstat2 hl"><b>6 hiba</b><span>a Claude‑nak – a folyamat során dokumentálva</span></div></div>'
        f'<div class="fs-src">{SRC_MITH}</div>')
tw("#f6 .core", "autoAlpha:0,scale:0.5", "autoAlpha:1,scale:1,duration:0.6,ease:'back.out(1.8)'", s + 0.3)
js.append(f"tl.fromTo('#f6 .ln',{{autoAlpha:0}},{{autoAlpha:1,duration:0.3,stagger:0.08}},{q(s + 0.8)});")
js.append(f"tl.fromTo('#f6 .lab',{{autoAlpha:0,scale:0.4}},{{autoAlpha:1,scale:1,duration:0.4,ease:'back.out(2)',stagger:0.08}},{q(s + 0.9)});")
js.append(f"tl.fromTo('#f6 .fstat2',{{autoAlpha:0,x:30}},{{autoAlpha:1,x:0,duration:0.5,ease:'power3.out',stagger:1.6}},{q(s + 1.2)});")

# F7 · subscribe end card (runs to the end)
s, e = q(O(211.0)), T_VIDEO
fs_wrap("f7", s, e,
        '<div class="endc"><img class="end-logo" src="img/amazing_logo.svg" alt="" />'
        '<div class="end-t"><b>AI</b> HÍREK <span>A NAGYVILÁGBÓL</span></div>'
        '<div class="end-btn">Iratkozz fel!</div><div class="end-n">Jövő héten jövünk a folytatással.</div></div>')
tw("#f7 .end-t", "autoAlpha:0,y:30", "autoAlpha:1,y:0,duration:0.6,ease:'power3.out'", s + 0.3)
tw("#f7 .end-btn", "autoAlpha:0,scale:0.6", "autoAlpha:1,scale:1,duration:0.5,ease:'back.out(2)'", s + 0.8)
js.append(f"tl.to('#f7 .end-btn',{{scale:1.06,duration:0.45,ease:'sine.inOut',yoyo:true,repeat:3}},{q(s + 1.4)});")
tw("#f7 .end-n", "autoAlpha:0", "autoAlpha:1,duration:0.5", s + 1.2)

for g in CARDS:
    card_html(g)

EXTRA_CSS = """
.fs-col.wide { width:1500px; }
.meter { position:absolute; left:120px; top:470px; width:1500px; height:110px; display:flex; gap:10px; }
.mfree { flex:62; border-radius:14px; background:linear-gradient(90deg,var(--violet),var(--lilac)); transform-origin:left center;
  display:flex; align-items:center; padding-left:32px; box-shadow:0 0 30px rgba(149,112,255,.5); }
.mpaid { flex:38; border-radius:14px; border:3px dashed var(--magenta); display:flex; align-items:center; padding-left:28px;
  background:repeating-linear-gradient(135deg, rgba(223,14,196,.22) 0 14px, rgba(223,14,196,.08) 14px 28px); }
.mfree span, .mpaid span { font-family:"Archivo"; font-stretch:112%; font-weight:800; font-size:38px; }
.mnote { position:absolute; left:120px; top:620px; width:1500px; font-size:30px; line-height:1.35; color:var(--soft); }
.fstat { position:absolute; left:120px; top:730px; display:flex; align-items:baseline; gap:24px; }
.fstat b { font-family:"Archivo"; font-stretch:118%; font-weight:850; font-size:72px; color:#ff7ff0; text-shadow:0 0 30px rgba(223,14,196,.6); }
.fstat span { font-size:28px; color:var(--soft); }
.toggles { position:absolute; left:120px; top:420px; }
.tg { display:flex; align-items:center; gap:30px; margin:0 0 34px; }
.tg .sw { position:relative; width:120px; height:62px; border-radius:31px; background:rgba(149,112,255,.22); border:3px solid rgba(149,112,255,.6); flex:none; }
.tg .sw i { position:absolute; left:6px; top:6px; width:44px; height:44px; border-radius:50%; background:#cfc4ff; }
.tg b { font-family:"Archivo"; font-stretch:112%; font-weight:850; font-size:52px; min-width:560px; }
.tg em { font-style:normal; font-size:28px; color:var(--magenta); font-weight:600; letter-spacing:.04em; }
.split { position:absolute; left:120px; top:420px; width:1680px; height:240px; display:flex; gap:12px; }
.sp { border-radius:16px; transform-origin:left center; padding:34px 36px; display:flex; flex-direction:column; justify-content:center; }
.sp.cn { background:linear-gradient(135deg,var(--violet),var(--magenta)); box-shadow:0 0 40px rgba(223,14,196,.45); }
.sp.ot { background:rgba(149,112,255,.28); border:3px solid var(--lilac); transform-origin:right center; }
.sp b { font-family:"Archivo"; font-stretch:118%; font-weight:850; font-size:96px; line-height:1; }
.sp span { font-size:32px; margin-top:10px; color:#fff; }
.hero { position:absolute; left:120px; top:400px; }
.hero b { display:block; font-family:"Archivo"; font-stretch:120%; font-weight:850; font-size:230px; line-height:1; transform-origin:left center;
  text-shadow:0 0 60px rgba(223,14,196,.7); }
.hero span { display:block; margin-top:26px; font-size:40px; color:var(--soft); }
.hub { position:absolute; left:80px; top:20px; width:1040px; height:1040px; }
.hub-svg { position:absolute; left:0; top:0; }
.hub-svg .ln { stroke:rgba(149,112,255,.65); stroke-width:3; stroke-dasharray:8 8; }
.lab { position:absolute; width:92px; height:92px; border-radius:50%; background:rgba(13,11,30,.9); border:3px solid var(--lilac);
  display:flex; flex-direction:column; align-items:center; justify-content:center; box-shadow:0 0 18px rgba(149,112,255,.5); }
.lab b { font-family:"Archivo"; font-weight:850; font-size:32px; line-height:1; }
.lab span { font-size:14px; color:var(--soft); }
.core { position:absolute; left:400px; top:380px; width:240px; height:240px; border-radius:50%;
  background:linear-gradient(135deg,var(--violet),var(--magenta)); display:flex; flex-direction:column; align-items:center; justify-content:center;
  box-shadow:0 0 60px rgba(223,14,196,.6); }
.core b { font-family:"Archivo"; font-stretch:112%; font-weight:850; font-size:40px; }
.core span { font-size:30px; margin-top:6px; }
.mcol { position:absolute; left:1180px; top:200px; width:640px; }
.fstat2 { margin-top:40px; padding-left:22px; border-left:6px solid var(--lilac); }
.fstat2 b { display:block; font-family:"Archivo"; font-stretch:118%; font-weight:850; font-size:72px; line-height:1; }
.fstat2 span { display:block; margin-top:8px; font-size:26px; line-height:1.3; color:var(--soft); }
.fstat2.hl { border-left-color:var(--magenta); }
.fstat2.hl b { color:#ff7ff0; }
.endc { position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; }
.end-logo { width:300px; margin-bottom:40px; }
.end-t { font-family:"Archivo"; font-stretch:125%; font-weight:800; font-size:110px; letter-spacing:.02em; text-shadow:0 0 30px rgba(149,112,255,.7); }
.end-t b { color:#dfff84; font-weight:800; }
.end-t span { display:block; text-align:center; font-size:30px; letter-spacing:.5em; font-weight:600; color:#fff; margin-top:10px; }
.end-btn { margin-top:60px; font-family:"Archivo"; font-stretch:115%; font-weight:850; font-size:54px; padding:22px 60px; border-radius:999px;
  background:linear-gradient(90deg,var(--violet),var(--magenta)); box-shadow:0 0 50px rgba(223,14,196,.6); }
.end-n { margin-top:34px; font-size:32px; color:var(--soft); }
.fs-logo { display:block; }
#f7 .fs-logo { display:none; }
.fbig b, .fbig span { white-space:nowrap; }
#f3 .fbig b { font-size:170px; }
#f6 .fs-src { left:1180px; }
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
<div id="root" data-composition-id="ai-hirado-1105" data-start="0" data-duration="{T_VIDEO}" data-fps="{FPS}" data-width="{W}" data-height="{H}">
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
window.__timelines["ai-hirado-1105"] = tl;
tl.seek(0);
}})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    (ROOT / "public" / "index.html").write_text(INDEX)
    print(f"{T_VIDEO}s · {len(sub_html)} subtitle chunks · {len(CARDS)} cards · {len(BUMPERS)} bumpers · 7 full-screen scenes")
