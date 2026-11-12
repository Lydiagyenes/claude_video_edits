#!/usr/bin/env python3
"""AI híradó 2026.11.12 — assemble public/index.html.

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
T_AUDIO = 223.08


def q(t):
    return round(round(t * FPS) / FPS, 4)


def esc(s):
    return html.escape(s).replace("-", "‑")  # keep hyphenated words on one line


# ── full-screen story bumpers (source times): the spoken headline, full frame ──
BUMPERS = [
    ("b1", 19.9, 24.3, "1 / 7", "Az Anthropic kiadta a Fable 5.2-t és a Mythos 5.2-t"),
    ("b2", 60.0, 65.6, "2 / 7", "OpenAI: 11 milliárd dollár, 1250 milliárdos értékelés"),
    ("b3", 84.3, 87.0, "3 / 7", "Gemini az autóban: megérkezett a CarPlay-re"),
    ("b4", 105.0, 109.0, "4 / 7", "Az Instagram világszerte AI-jal tippeli meg, ki kamasz"),
    ("b5", 128.9, 132.9, "5 / 7", "Forrósodik a talaj az NVIDIA alatt Washingtonban"),
    ("b6", 153.0, 155.9, "6 / 7", "A Claude beül a meetingekre"),
    ("b7", 173.6, 176.9, "7 / 7", "Robotagy és DNS-olvasó a DeepMindtól"),
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


SRC_ANTH = "Forrás: Anthropic, CNBC, VentureBeat, 2026.11.09"
SRC_FERMAT = "Forrás: Anthropic (2026.09.04 és 11.09), Tech Times, Neurohive"
SRC_TC = "Forrás: TechCrunch – Mythos 5.2 rendszerkártya, 2026.11.09"
SRC_OAI = "Forrás: Bloomberg (Investing.com, Yahoo Finance), 2026.11.06"
SRC_CARPLAY = "Forrás: Google (MacRumors, Android Authority), 2026.11.11"
SRC_IG = "Forrás: Meta, TechCrunch, 2026.11.09"
SRC_NV = "Forrás: Semafor, SCMP (2026.11.09), CNBC (2026.06.08), Yahoo Finance"
SRC_MEET = "Forrás: Anthropic, TechCrunch, Axios, 2026.11.10"
SRC_ROBO = "Forrás: Google DeepMind, heise, Tech Times, 2026.11.10–11"
SRC_GENOME = "Forrás: Google DeepMind blog, MarkTechPost, 2026.11.11"

CARDS = [
    dict(id="c0", start=0.5, end=19.6, kicker="Az adásban", source="",
         phases=[(0.5, "A hét AI‑hírei", numbered([
             "Fable 5.2 és Mythos 5.2", "OpenAI: 1250 Mrd $‑os értékelés", "Gemini a CarPlay‑en",
             "Instagram: AI tippeli a kamaszokat", "NVIDIA: forró talaj Washingtonban",
             "Claude Meetings", "DeepMind: robotagy és DNS‑olvasó"]))]),
    dict(id="c1", start=24.5, end=35.9, kicker="Anthropic · 2026. november 9.", source=SRC_ANTH,
         phases=[(24.5, "Két új modell",
                  items("Fable 5.2: mindenkinek elérhető",
                        ("Mythos 5.2: csak ellenőrzött szervezeteknek (pl. kiberbiztonsági ellenőrző program)", "warn")))]),
    dict(id="c1b", start=51.1, end=59.6, kicker="Mythos 5.2 · rendszerkártya", source=SRC_TC,
         phases=[(51.1, "A figyelmeztetés",
                  '<div class="quote" style="font-size:38px">„Erősebb rejtett képességek”</div>'
                  '<div class="note">több értékelésen, mint a korábbi Claude‑modellek – főleg, ha az érvelése '
                  'rejtve marad a felügyelő rendszer elől</div>'
                  + items(("Mindkét új modell gyakrabban gyanította, hogy éppen tesztelik", "warn")))]),
    dict(id="c2", start=66.2, end=74.9, kicker="OpenAI · Bloomberg, nov. 6.", source=SRC_OAI,
         phases=[(66.2, "Új befektetési kör",
                  '<div class="big">11 Mrd $</div><div class="note">a kör első része; a teljes kör a hírek szerint '
                  'akár 20 Mrd $‑ig nőhet</div>' + items("Értékelés: 1250 Mrd $"))]),
    dict(id="c3", start=87.1, end=104.9, kicker="Google · Gemini a CarPlay‑en", source=SRC_CARPLAY,
         phases=[
             (87.1, "Indulás: 2026. november 11.",
              items("Gemini Live hanghívás a műszerfalról", "A telefonon kezdett beszélgetés folytatható",
                    "Világszerte, minden Gemini Live‑nyelven")),
             (97.0, "Mi kell hozzá?",
              items("Friss Gemini app az iPhone‑on", "Legalább egyszer használt Gemini Live",
                    ("Zenét, klímát, más CarPlay‑appot nem vezérel", "warn"))),
         ]),
    dict(id="c4", start=109.1, end=117.9, kicker="Meta · Instagram", source=SRC_IG,
         phases=[(109.1, "Világszerte, 2026. november 9‑től",
                  '<div class="big">13–17</div><div class="note">évesnek becsült felhasználók kerülnek tinifiókba – '
                  'akkor is, ha felnőtt születési dátumot adtak meg</div>')]),
    dict(id="c4b", start=125.0, end=128.6, kicker="Tinifiók", source=SRC_IG,
         phases=[(125.0, "Szigorúbb védelem", items("Alapból privát profil", "Korlátozza, ki veheti fel a kapcsolatot"))]),
    dict(id="c5", start=133.1, end=152.8, kicker="NVIDIA · Washington", source=SRC_NV,
         phases=[
             (133.1, "A félidős választások után",
              items("Januártól demokrata többség a Kongresszusban",
                    "Hakeem Jeffries támogatja a szigorúbb chipexport‑szabályokat")),
             (142.5, "Elizabeth Warren",
              '<div class="note">már júniusban tanúskodásra hívta Jensen Huangot a kínai chipeladásokról – '
              'Huang akkor nemet mondott</div>'),
             (149.0, "Republikánusok",
              '<div class="note">a képviselőház republikánusai is meghallgatásra hívták Huangot, '
              'még a demokrata többség januári kezdete előtt</div>'),
         ]),
    dict(id="c6", start=166.0, end=173.5, kicker="Claude Meetings", source=SRC_MEET,
         phases=[(166.0, "Elérhetőség",
                  items("Béta, 2026. november 10‑től", "Team és Enterprise csomagokban",
                        ("Egyelőre csak Google Meettel", "warn"))
                  + '<div class="note">a hívás után a jegyzetek és a teendők a claude.ai‑ban várnak</div>')]),
    dict(id="c7", start=177.0, end=181.9, kicker="Google DeepMind", source=SRC_ROBO,
         phases=[(177.0, "Két bejelentés", items("Gemini Robotics 2.5 – nov. 10.", "AlphaGenome 2 – nov. 11."))]),
    dict(id="c7b", start=191.0, end=201.1, kicker="DeepMind · AlphaGenome 2", source=SRC_GENOME,
         phases=[(191.0, "DNS‑változatok hatása sejttípusonként",
                  '<div class="sub2">Megtalált oki variánsok (90% pontosság)</div>'
                  + bar("1. verzió", "16%", 16 / 30 * 100, "lil") + bar("2. verzió", "30%", 100, "mag")
                  + '<div class="note">a DeepMind saját mérése; nem kereskedelmi kutatásra (API)</div>')]),
    dict(id="c8", start=201.7, end=208.9, kicker="A hét röviden", source="",
         phases=[(201.7, "Három irány",
                  items("Gyorsabb modellek: Fable 5.2, Gemini Robotics 2.5",
                        "Gigantikus pénzek: OpenAI 1250 Mrd $",
                        ("Szabályozói kérdőjelek: NVIDIA, Instagram", "warn")))]),
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


# F1 · Fable 5.2: faster and cheaper
phased_bars("f1", 36.0, 44.9, [
    (36.0, "Anthropic · Fable 5.2", "Gyorsabb szöveggenerálás",
     "", "+30%", "gyorsabb kimenet az elődökhöz képest (Anthropic)"),
    (40.1, "Anthropic · Fable 5.2", "Bemeneti ár, millió tokenenként",
     bar("5.1", "10 $", 100, "lil") + bar("5.2", "8 $", 80, "mag"), "−20%", "kimenet: 50 $ → 40 $"),
], SRC_ANTH)

# F2 · Fermat formalisation: September run vs Fable 5.2
phased_bars("f2", 45.0, 51.0, [
    (45.0, "Nagy Fermat‑tétel · Lean‑formalizálás", "Mennyi idő alatt?",
     bar("2026. szept.", "~11 nap", 100, "lil") + bar("Fable 5.2", "~30 óra", 11.4, "mag"),
     "~1000", "Fable 5.2 ügynök dolgozott rajta párhuzamosan"),
], SRC_FERMAT)

# F3 · OpenAI: September plans vs the round now
s, e = q(O(75.0)), q(O(81.0))
fs_wrap("f3", s, e,
        '<div class="fphases"><div class="fs-kick">OpenAI · szeptemberi hírek vs. most</div>'
        '<div class="fs-title">Kisebb kör, alacsonyabb értékelés</div>'
        '<div class="fbars"><div class="grp">Bevont tőke</div>'
        + bar("Szept. (terv)", "30 Mrd $", 100, "lil") + bar("Most", "11 Mrd $", 36.7, "mag")
        + '<div class="grp">Értékelés</div>'
        + bar("Szept. (terv)", "1400 Mrd $", 100, "lil") + bar("Most", "1250 Mrd $", 89.3, "mag")
        + f'</div></div><div class="fs-src">{SRC_OAI}</div>')
js.append(f"tl.fromTo('#f3 .fill',{{scaleX:0}},{{scaleX:1,duration:0.9,ease:'power3.out',stagger:0.45}},{q(s + 0.4)});")

# F4 · Instagram: what the age model looks at
s, e = q(O(118.0)), q(O(125.0))
fs_wrap("f4", s, e,
        '<div class="fs-col wide"><div class="fs-kick">Instagram · AI‑alapú életkorbecslés</div>'
        '<div class="fs-title">Mire figyel az AI?</div></div>'
        '<div class="panels"><div class="pn"><div class="pn-h">Szövegben</div>'
        '<div class="pn-s">posztok, kommentek, bemutatkozás, képaláírások</div>'
        + items("Születésnapi köszöntések", "Utalás az iskolai évfolyamra")
        + '</div><div class="pn"><div class="pn-h">Képen és videón</div><div class="pn-s">vizuális jelek</div>'
        + items("Látszólagos magasság", "Csontszerkezet")
        + f'</div></div><div class="fs-src">{SRC_IG}</div>')
js.append(f"tl.fromTo('#f4 .pn',{{autoAlpha:0,y:40}},{{autoAlpha:1,y:0,duration:0.55,ease:'power3.out',stagger:0.7}},{q(s + 0.5)});")
js.append(f"tl.fromTo('#f4 .li',{{autoAlpha:0,x:24}},{{autoAlpha:1,x:0,duration:0.4,stagger:0.5}},{q(s + 1.3)});")

# F5 · Claude Meetings: a call with Claude as a visible participant
s, e = q(O(158.0)), q(O(165.6))
tiles = "".join(f'<div class="tile"><span>{n}</span></div>' for n in ("A", "B", "C"))
steps = "".join(f'<div class="stp"><i></i><b>{t}</b><em>{d}</em></div>' for t, d in (
    ("Terv", "vázlat a beszélgetés közben"), ("Idővonal", "mérföldkövek, határidők"), ("Chat", "válasz a kérdésekre")))
fs_wrap("f5", s, e,
        '<div class="fs-col wide"><div class="fs-kick">Anthropic · Claude Meetings</div>'
        '<div class="fs-title">A Claude látható résztvevőként ül be a hívásba</div></div>'
        f'<div class="call">{tiles}<div class="tile cl"><span>Claude</span></div></div>'
        f'<div class="steps">{steps}</div><div class="fs-src">{SRC_MEET}</div>')
js.append(f"tl.fromTo('#f5 .tile',{{autoAlpha:0,scale:0.85}},{{autoAlpha:1,scale:1,duration:0.4,ease:'power2.out',stagger:0.15}},{q(s + 0.4)});")
js.append(f"tl.fromTo('#f5 .tile.cl',{{boxShadow:'0 0 0px rgba(223,14,196,0)'}},{{boxShadow:'0 0 60px rgba(223,14,196,.8)',duration:0.6,yoyo:true,repeat:1}},{q(s + 1.2)});")
js.append(f"tl.fromTo('#f5 .stp',{{autoAlpha:0,x:40}},{{autoAlpha:1,x:0,duration:0.45,ease:'power3.out',stagger:1.2}},{q(s + 1.8)});")

# F6 · Gemini Robotics 2.5 at Mercedes-Benz (Kecskemét!)
s, e = q(O(182.0)), q(O(191.0))
fs_wrap("f6", s, e,
        '<div class="fs-col wide"><div class="fs-kick">Google DeepMind · Gemini Robotics 2.5</div>'
        '<div class="fs-title">Humanoid robotok a Mercedes‑Benz gyártósorán</div></div>'
        '<div class="hero" style="top:330px"><b>96%</b><span>sikerarány egy alkatrész‑összekészítési feladatban</span></div>'
        '<div class="facts">' + items("Apptronik Apollo 2 humanoid robotok",
                                     "Helyszín: Kecskemét és Sindelfingen",
                                     ("A próbák számát nem közölték", "warn")) + '</div>'
        f'<div class="fs-src">{SRC_ROBO}</div>')
tw("#f6 .hero b", "autoAlpha:0,scale:0.7", "autoAlpha:1,scale:1,duration:0.6,ease:'back.out(1.6)'", s + 0.5)
tw("#f6 .hero span", "autoAlpha:0,y:16", "autoAlpha:1,y:0,duration:0.5", s + 1.1)
js.append(f"tl.fromTo('#f6 .li',{{autoAlpha:0,x:30}},{{autoAlpha:1,x:0,duration:0.45,stagger:0.9}},{q(s + 2.0)});")

# F7 · newsletter end card (runs to the end)
s, e = q(O(209.0)), T_VIDEO
fs_wrap("f7", s, e,
        '<div class="endc"><img class="end-logo" src="img/amazing_logo.svg" alt="" />'
        '<div class="end-t"><b>AI</b> HÍREK <span>A NAGYVILÁGBÓL</span></div>'
        '<div class="end-btn">Iratkozz fel a hírlevelünkre!</div><div class="end-n">Link a videó leírásában · '
        'jövő héten jövünk a folytatással</div></div>')
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
<div id="root" data-composition-id="ai-hirado-1112" data-start="0" data-duration="{T_VIDEO}" data-fps="{FPS}" data-width="{W}" data-height="{H}">
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
window.__timelines["ai-hirado-1112"] = tl;
tl.seek(0);
}})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    (ROOT / "public" / "index.html").write_text(INDEX)
    print(f"{T_VIDEO}s · {len(sub_html)} subtitle chunks · {len(CARDS)} cards · {len(BUMPERS)} bumpers · 7 full-screen scenes")
