#!/usr/bin/env python3
"""AI híradó 2026.11.19 — assemble public/index.html.

Same format as híradó 10.29 and 11.05: the recording (uncut, split around the show intro) · side
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
T_AUDIO = 207.82


def q(t):
    return round(round(t * FPS) / FPS, 4)


def esc(s):
    return html.escape(s).replace("-", "‑")  # keep hyphenated words on one line


# ── full-screen story bumpers (source times): the spoken headline, full frame ──
BUMPERS = [
    ("b1", 17.75, 20.6, "1 / 7", "Lemondott Jensen Huang, az NVIDIA vezére"),
    ("b2", 46.4, 48.7, "2 / 7", "Tőzsdére lép az Anthropic"),
    ("b3", 67.6, 71.4, "3 / 7", "Megérkezett a GPT-6.2 Astra és Sol"),
    ("b4", 93.6, 96.2, "4 / 7", "Kalifornia beperelte az OpenAI-t"),
    ("b5", 121.4, 124.25, "5 / 7", "Itt a Gemini 4 Neon"),
    ("b6", 140.5, 144.5, "6 / 7", "Microsoft: a Copilot az új operációs rendszer"),
    ("b7", 168.9, 171.5, "7 / 7", "Amerika bezárta a kiskaput"),
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


SRC_NV = "Forrás: NVIDIA 8‑K és igazgatótanácsi közlemény, Al Jazeera, CNBC, 2026.11.08–16"
SRC_IPO = "Forrás: CNBC, CNN, Yahoo Finance, 2026.11.18"
SRC_GPT = "Forrás: OpenAI GPT‑6.2 rendszerkártya, The Next Web, 2026.11.17"
SRC_CA = "Forrás: CNBC, NBC News, BleepingComputer, 2026.11.16"
SRC_NEON = "Forrás: Google blog, 9to5Google, 2026.11.18"
SRC_MS = "Forrás: Microsoft blog (Ignite 2026), 2026.11.17"
SRC_RULE = "Forrás: CNBC, The Next Web, TechCrunch, Gizmodo, 2026.11.16–18"

CARDS = [
    dict(id="c0", start=0.5, end=17.2, kicker="Az adásban", source="",
         phases=[(0.5, "A hét AI‑hírei", numbered([
             "Lemondott Jensen Huang", "Tőzsdén az Anthropic", "GPT‑6.2 Astra és Sol",
             "Kalifornia beperelte az OpenAI‑t", "Gemini 4 Neon", "Copilot: a munka új OS‑e",
             "USA: bezárt kiskapu"]))]),
    dict(id="c1", start=20.7, end=28.6, kicker="NVIDIA · 2026. november 12.", source=SRC_NV,
         phases=[(20.7, "Vezetőváltás",
                  items("Jensen Huang azonnali hatállyal lemondott – 33 év után",
                        "Ideiglenes vezérigazgató: Colette Kress pénzügyi igazgató",
                        "Az igazgatótanács első elnöke: Harvey C. Jones"))]),
    dict(id="c2", start=56.2, end=67.3, kicker="Anthropic · IPO", source=SRC_IPO,
         phases=[
             (56.2, "Rekord",
              '<div class="big">81,3 Mrd $</div><div class="note">a valaha volt legnagyobb tőzsdei bevezetés, '
              'a júniusi SpaceX‑rekord fölött</div>'
              + items("Kb. 980 millió részvény", "Teljesen hígított piaci érték: kb. 1500 Mrd $")),
             (60.96, "Kereskedés",
              '<div class="big">ANT</div><div class="note">ezzel a jellel a Nasdaqon, csütörtöktől</div>'),
         ]),
    dict(id="c3", start=71.5, end=83.1, kicker="OpenAI · 2026. november 17.", source=SRC_GPT,
         phases=[(71.5, "GPT‑6.2: két új modell",
                  items("Astra: a legnehezebb szakmai munkákra", "Sol: olcsóbb, hétköznapi feladatokra",
                        "Elérhető: ChatGPT Work, Codex, API"))]),
    dict(id="c4", start=96.3, end=104.85, kicker="Kalifornia · OpenAI", source=SRC_CA,
         phases=[(96.3, "Per: 2026. november 16.",
                  items("Indította: Rob Bonta főügyész",
                        "Jogalap: tisztességtelen piaci magatartás és közérdeksérelem"))]),
    dict(id="c5", start=124.3, end=140.0, kicker="Google · Gemini 4 Neon", source=SRC_NEON,
         phases=[
             (124.3, "Megjelent: 2026. november 18.",
              items("Kódolásban, érvelésben a Carbon szintjén", "Flash‑modellekhez hasonló sebesség",
                    "API: 3 $ / 15 $ millió tokenenként (bevezető ár)")),
             (134.2, "Elérhetőség", items("Google AI Pro és Ultra előfizetők", "API, Antigravity, Gemini app")),
             (137.5, "Egy hét, három modell", items("Carbon és Hydrogen – egy héttel korábban", "Neon – november 18.")),
         ]),
    dict(id="c6", start=144.7, end=157.5, kicker="Microsoft · Ignite 2026", source=SRC_MS,
         phases=[(144.7, "Satya Nadella a Copilotról",
                  '<div class="quote" style="font-size:40px">„A munka új operációs rendszere”</div>'
                  + items("Egy helyen: csevegés, kódolás, Autopilot", "Autopilot: önállóan dolgozó ügynök"))]),
    dict(id="c7", start=171.6, end=180.0, kicker="USA · exportszabály, nov. 16.", source=SRC_RULE,
         phases=[(171.6, "Új engedélykötelezettség",
                  items("Ha fejlett AI‑chip olyan külföldi adatközpontba kerül, amely jelentős kapacitást ad kínai cégeknek",
                        "Érintett: Szingapúr, Malajzia, Thaiföld, Indonézia, Brazília"))]),
    dict(id="c8", start=193.0, end=196.4, kicker="A hét röviden", source="",
         phases=[(193.0, "Hét hír",
                  items("NVIDIA: távozott Huang", "Anthropic: rekord‑IPO", "GPT‑6.2 Astra: „magas” besorolás",
                        "Kalifornia vs. OpenAI", ("USA: bezárt chip‑kiskapu", "warn")))]),
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


# F1 · NVIDIA: timeline of the week
s, e = q(O(28.76)), q(O(41.9))
ev = [("nov. 8.", "Független vizsgálat a jelentett külföldi titkosszolgálati célzás miatt"),
      ("nov. 8.", "A testület: nincs ok azt hinni, hogy nemzetbiztonsági vagy céges titok sérült"),
      ("nov. 12.", "Huang lemond, Colette Kress az ideiglenes vezérigazgató"),
      ("nov. 16.", "CNBC: a testület nem tervezi visszahozni Huangot")]
evh = "".join(f'<div class="ev"><i></i><b>{d}</b><span>{t}</span></div>' for d, t in ev)
fs_wrap("f1", s, e,
        '<div class="fs-col wide"><div class="fs-kick">NVIDIA · a hét eseményei</div>'
        f'<div class="fs-title">Egy hét alatt a vizsgálattól a lemondásig</div></div><div class="tline">{evh}</div>'
        f'<div class="fs-src">{SRC_NV}</div>')
js.append(f"tl.fromTo('#f1 .ev',{{autoAlpha:0,x:-40}},{{autoAlpha:1,x:0,duration:0.5,ease:'power3.out',stagger:2.4}},{q(s + 0.5)});")

# F2 · Anthropic IPO price vs the planned range (scale 65–90 $)
s, e = q(O(48.8)), q(O(56.1))
def px(v):
    return (v - 65) / 25 * 100
fs_wrap("f2", s, e,
        '<div class="fs-col wide"><div class="fs-kick">Anthropic · tőzsdei bevezetés</div>'
        '<div class="fs-title">Részvényár a tervezett sávhoz képest</div></div>'
        f'<div class="pr"><div class="pr-track"></div><div class="pr-band" style="left:{px(70)}%;width:{px(78) - px(70)}%"><span>tervezett sáv: 70–78 $</span></div>'
        f'<div class="pr-mark" style="left:{px(83)}%"><b>83 $</b></div>'
        + "".join(f'<div class="pr-tick" style="left:{px(v)}%">{v}</div>' for v in (65, 70, 75, 80, 85, 90))
        + '</div><div class="mnote" style="top:720px">A végső ár 5 dollárral a sáv teteje fölött lett.</div>'
        f'<div class="fs-src">{SRC_IPO}</div>')
tw("#f2 .pr-band", "scaleX:0", "scaleX:1,duration:0.8,ease:'power3.out'", s + 0.5)
tw("#f2 .pr-mark", "autoAlpha:0,y:-60", "autoAlpha:1,y:0,duration:0.6,ease:'back.out(1.8)'", s + 1.6)
tw("#f2 .mnote", "autoAlpha:0", "autoAlpha:1,duration:0.5", s + 2.6)

# F3 · GPT-6.2 Astra price and risk ratings
risk = ('<div class="risk">'
        '<div class="rk h"><span>Terület</span><span>Astra</span><span>Sol</span></div>'
        '<div class="rk"><span>AI‑önfejlesztés</span><b class="hi">Magas</b><b>küszöb alatt</b></div>'
        '<div class="rk"><span>Kiberbiztonság</span><b class="cr">Kritikus</b><b class="cr">Kritikus</b></div>'
        '<div class="rk"><span>Biológia, kémia</span><b class="hi">Magas</b><b class="hi">Magas</b></div></div>')
phased_bars("f3", 83.24, 93.2, [
    (83.24, "OpenAI · GPT‑6.2 Astra", "API‑ár az elődhöz képest",
     bar("Előd", "100%", 100, "lil") + bar("GPT‑6.2 Astra", "80%", 80, "mag"), "−20%", "olcsóbb input‑ és outputtoken"),
    (87.12, "OpenAI · saját kockázati keretrendszer", "Kockázati besorolások", risk, "", ""),
], SRC_GPT)
js.append(f"tl.fromTo('#f3 .rk',{{autoAlpha:0,y:20}},{{autoAlpha:1,y:0,duration:0.4,stagger:0.5}},{q(O(87.12) + 0.4)});")

# F4 · California v. OpenAI: the Hugging Face incident, then the 80 incidents
phased_bars("f4", 104.92, 121.1, [
    (104.92, "Kalifornia · keresetlevél", "A Hugging Face‑incidens, 2026. július",
     items("Tesztkörnyezetből kitört ügynökök", "Nulladik napi sebezhetőség a JFrog Artifactoryban",
           "Több mint két napig tartó támadás"), "", ""),
    (110.76, "Kalifornia · keresetlevél", "A főügyész szerint",
     "", "80", "ismert incidens, amikor az OpenAI elvesztette az irányítást"),
], SRC_CA)
js.append(f"tl.fromTo('#f4-p0 .li',{{autoAlpha:0,x:30}},{{autoAlpha:1,x:0,duration:0.45,stagger:1.0}},{q(O(104.92) + 0.5)});")

# F5 · Microsoft: Agent 365 and Maia 300
s, e = q(O(157.56), ), q(O(168.5))
fs_wrap("f5", s, e,
        '<div class="fs-col wide"><div class="fs-kick">Microsoft · Ignite 2026</div>'
        '<div class="fs-title">Ügynököknek felügyelet, saját chip</div></div>'
        '<div class="panels"><div class="pn"><div class="pn-h">Agent 365</div><div class="pn-big">50 millió+</div>'
        '<div class="pn-s">felügyelt AI‑ügynök a Microsoft szerint</div></div>'
        '<div class="pn"><div class="pn-h">Maia 300 chip</div><div class="pn-big">+40%</div>'
        '<div class="pn-s">token/watt a vezető GPU‑s rendszerekhez képest (Microsoft)</div></div></div>'
        f'<div class="fs-src">{SRC_MS}</div>')
js.append(f"tl.fromTo('#f5 .pn',{{autoAlpha:0,y:40}},{{autoAlpha:1,y:0,duration:0.55,ease:'power3.out',stagger:3.8}},{q(s + 0.4)});")

# F6 · the closed loophole, China's reaction, Nvidia's H200 halt
s, e = q(O(180.04)), q(O(192.9))
fs_wrap("f6", s, e,
        '<div class="fs-col wide"><div class="fs-kick">USA · Kína · chipháború</div>'
        '<div class="fs-title">Bezárt kiskapu</div></div>'
        '<div class="flow"><div class="fn">Kínai cég</div><div class="fa"><i></i><em>×</em></div>'
        '<div class="fn">Délkelet‑ázsiai adatközpont</div><div class="fa"><i></i></div><div class="fn us">Amerikai AI‑chip</div></div>'
        '<div class="reacts"><div class="rc"><div class="rc-h">Kína</div><div class="rc-t">határozottan ellenzi, '
        'ellenintézkedéseket helyez kilátásba</div></div>'
        '<div class="rc"><div class="rc-h">NVIDIA</div><div class="rc-big">2,4 Mrd $</div><div class="rc-t">kínai H200‑bevétel '
        'az előző negyedévben – ennek vége, leállították az eladást</div></div></div>'
        f'<div class="fs-src">{SRC_RULE}</div>')
js.append(f"tl.fromTo('#f6 .fn, #f6 .fa',{{autoAlpha:0,y:20}},{{autoAlpha:1,y:0,duration:0.4,stagger:0.25}},{q(s + 0.4)});")
tw("#f6 .fa em", "scale:0", "scale:1,duration:0.4,ease:'back.out(3)'", s + 1.8)
js.append(f"tl.fromTo('#f6 .rc',{{autoAlpha:0,y:30}},{{autoAlpha:1,y:0,duration:0.5,ease:'power3.out',stagger:{O(184.72) - O(182.92):.2f}}},{q(O(182.92))});")

# F7 · end card (runs to the end)
s, e = q(O(196.5)), T_VIDEO
fs_wrap("f7", s, e,
        '<div class="endc"><img class="end-logo" src="img/amazing_logo.svg" alt="" />'
        '<div class="end-t"><b>AI</b> HÍREK <span>A NAGYVILÁGBÓL</span></div>'
        '<div class="end-btn">Kövess minket!</div><div class="end-n">Iratkozz fel a hírlevelünkre is – link a leírásban</div></div>')
tw("#f7 .end-t", "autoAlpha:0,y:30", "autoAlpha:1,y:0,duration:0.6,ease:'power3.out'", s + 0.3)
tw("#f7 .end-btn", "autoAlpha:0,scale:0.6", "autoAlpha:1,scale:1,duration:0.5,ease:'back.out(2)'", s + 0.8)
js.append(f"tl.to('#f7 .end-btn',{{scale:1.05,duration:0.45,ease:'sine.inOut',yoyo:true,repeat:5}},{q(s + 1.4)});")
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
#c0 .li.num { margin:9px 0; font-size:21px; }
.tline { position:absolute; left:120px; top:340px; width:1600px; border-left:5px solid rgba(149,112,255,.55); }
.ev { position:relative; padding:0 0 34px 54px; display:flex; flex-direction:column; }
.ev i { position:absolute; left:-19px; top:6px; width:32px; height:32px; border-radius:50%; background:var(--magenta); box-shadow:0 0 18px rgba(223,14,196,.8); }
.ev b { font-family:"Archivo"; font-stretch:115%; font-weight:850; font-size:36px; color:#ff9ff3; }
.ev span { font-size:32px; line-height:1.3; margin-top:4px; }
.pr { position:absolute; left:160px; top:470px; width:1600px; height:200px; }
.pr-track { position:absolute; left:0; right:0; top:80px; height:20px; border-radius:10px; background:rgba(149,112,255,.22); }
.pr-band { position:absolute; top:62px; height:56px; border-radius:12px; background:rgba(149,112,255,.55); border:3px solid var(--lilac); transform-origin:left center; }
.pr-band span { position:absolute; left:0; top:-48px; white-space:nowrap; font-size:28px; color:var(--soft); }
.pr-mark { position:absolute; top:40px; width:6px; height:100px; margin-left:-3px; background:var(--magenta); box-shadow:0 0 24px rgba(223,14,196,.9); }
.pr-mark b { position:absolute; left:50%; top:-110px; transform:translateX(-50%); font-family:"Archivo"; font-stretch:118%; font-weight:850; font-size:84px; white-space:nowrap; text-shadow:0 0 30px rgba(223,14,196,.7); }
.pr-tick { position:absolute; top:150px; transform:translateX(-50%); font-size:26px; color:var(--soft); }
.risk { width:1300px; margin-top:10px; }
.rk { display:grid; grid-template-columns:520px 1fr 1fr; align-items:center; padding:18px 0; border-bottom:1px solid rgba(149,112,255,.3); font-size:34px; }
.rk.h { font-size:22px; letter-spacing:.2em; text-transform:uppercase; color:var(--lilac); font-family:"Archivo"; font-weight:800; }
.rk b { font-family:"Archivo"; font-weight:850; font-size:34px; color:var(--soft); }
.rk b.hi { color:#ff7ff0; } .rk b.cr { color:#fff; background:var(--magenta); justify-self:start; padding:4px 16px; border-radius:8px; }
#f4 .fbars .li { font-size:38px; margin:26px 0; align-items:center; }
.pn-big { font-family:"Archivo"; font-stretch:118%; font-weight:850; font-size:110px; line-height:1.05; margin-top:16px; color:#ff7ff0; text-shadow:0 0 30px rgba(223,14,196,.6); }
#f5 .pn { padding:44px 48px; }
#f5 .pn-s { font-size:30px; margin-top:12px; }
.flow { position:absolute; left:120px; top:330px; display:flex; align-items:center; gap:20px; }
.fn { font-family:"Archivo"; font-stretch:110%; font-weight:850; font-size:38px; padding:26px 34px; border-radius:16px; background:rgba(13,11,30,.6); border:3px solid var(--lilac); }
.fn.us { border-color:var(--magenta); }
.fa { position:relative; width:120px; height:6px; background:repeating-linear-gradient(90deg,var(--lilac) 0 14px,transparent 14px 24px); }
.fa em { position:absolute; left:50%; top:50%; transform:translate(-50%,-50%); font-style:normal; font-family:"Archivo"; font-weight:900; font-size:90px; color:var(--magenta); text-shadow:0 0 20px rgba(223,14,196,.9); line-height:1; }
.reacts { position:absolute; left:120px; top:540px; width:1680px; display:flex; gap:40px; }
.rc { flex:1; background:rgba(13,11,30,.55); border:2px solid rgba(149,112,255,.55); border-radius:20px; padding:28px 36px; }
.rc-h { font-family:"Archivo"; font-stretch:112%; font-weight:850; font-size:40px; }
.rc-big { font-family:"Archivo"; font-stretch:118%; font-weight:850; font-size:72px; color:#ff7ff0; margin-top:6px; }
.rc-t { font-size:28px; line-height:1.3; color:var(--soft); margin-top:8px; }
.grp { font-family:"Archivo"; font-weight:800; font-size:22px; letter-spacing:.2em; text-transform:uppercase; color:var(--lilac); margin:30px 0 2px; }
#f3 .fbars { margin-top:24px; }
#f3 .fbars .row { margin:14px 0; }
.panels { position:absolute; left:120px; top:360px; width:1680px; display:flex; gap:40px; }
.pn { flex:1; background:rgba(13,11,30,.55); border:2px solid rgba(149,112,255,.55); border-radius:20px; padding:34px 40px; }
.pn-h { font-family:"Archivo"; font-stretch:112%; font-weight:850; font-size:48px; }
.pn-s { font-size:24px; color:var(--soft); margin:8px 0 18px; }
.pn .li { font-size:34px; margin:18px 0; align-items:center; }
.call { position:absolute; left:120px; top:400px; width:900px; display:grid; grid-template-columns:1fr 1fr; gap:18px; }
.tile { height:200px; border-radius:18px; background:rgba(149,112,255,.18); border:2px solid rgba(149,112,255,.45); display:flex; align-items:center; justify-content:center; }
.tile span { width:100px; height:100px; border-radius:50%; background:rgba(149,112,255,.45); display:flex; align-items:center; justify-content:center; font-family:"Archivo"; font-weight:850; font-size:44px; }
.tile.cl { background:linear-gradient(135deg, rgba(94,68,228,.75), rgba(223,14,196,.6)); border-color:var(--magenta); }
.tile.cl span { width:auto; height:auto; background:none; font-size:56px; }
.steps { position:absolute; left:1110px; top:410px; width:700px; }
.stp { display:flex; flex-direction:column; padding:0 0 34px 46px; position:relative; border-left:4px solid rgba(149,112,255,.5); margin-left:14px; }
.stp i { position:absolute; left:-16px; top:6px; width:28px; height:28px; border-radius:50%; background:var(--magenta); box-shadow:0 0 16px rgba(223,14,196,.8); }
.stp b { font-family:"Archivo"; font-stretch:112%; font-weight:850; font-size:46px; line-height:1; }
.stp em { font-style:normal; font-size:26px; color:var(--soft); margin-top:6px; }
.facts { position:absolute; left:1150px; top:360px; width:680px; }
.facts .li { font-size:30px; margin:22px 0; }
#f6 .hero span { max-width:920px; white-space:normal; line-height:1.3; }
#f6 .hero b { font-size:220px; }
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
<div id="root" data-composition-id="ai-hirado-1119" data-start="0" data-duration="{T_VIDEO}" data-fps="{FPS}" data-width="{W}" data-height="{H}">
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
window.__timelines["ai-hirado-1119"] = tl;
tl.seek(0);
}})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    (ROOT / "public" / "index.html").write_text(INDEX)
    print(f"{T_VIDEO}s · {len(sub_html)} subtitle chunks · {len(CARDS)} cards · {len(BUMPERS)} bumpers · 7 full-screen scenes")
