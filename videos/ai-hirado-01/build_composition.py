#!/usr/bin/env python3
"""Assemble public/index.html for AI híradó #01.

Layers (back → front): studio plate + light sweep · presenter cut-out clips (EDL from
edit.py) · info cards · lower-third news titles · show bug · show intro (full frame)
· intro flashes. Sound is one pre-mixed track (mix_audio.py).
Run:  python3 build_composition.py
"""
import html
from pathlib import Path

from edit import intro_window, src_to_out, timeline, total

ROOT = Path(__file__).resolve().parent
FPS, W, H = 30, 1920, 1080
T = round(total(), 3)
I0, I1 = intro_window()


def q(t):
    return round(round(t * FPS) / FPS, 4)


def O(src):  # source time → output time
    v = src_to_out(src)
    assert v is not None, src
    return q(v)


# ── lower-third titles: (source start, kicker, title) ────────────────────────
TEASER = [
    (5.18, "Az adásban", "Mi történik, ha egy AI-ügynök kiszabadul?"),
    (10.80, "Az adásban", "Lépnek a hatóságok: Brüsszel és 8 amerikai állam"),
    (15.57, "Az adásban", "Új csúcsmodell a Google-től és a Metától"),
    (18.73, "AI hírek", "A hét legfontosabb technológiai eseményei"),
]
NEWS = [
    (22.38, "1 / 7", "Brüsszel először lép az AI Act alapján"),
    (61.45, "2 / 7", "Nyolc amerikai állam pereli az OpenAI-t"),
    (93.50, "3 / 7", "A Claude hamis gyilkossági tippet küldött a rendőrségnek"),
    (130.50, "4 / 7", "A Meta beszállt a csúcsligába: itt a Muse Wonder"),
    (157.05, "5 / 7", "Gemini 4 Argon: élesben a Google új csúcsmodellje"),
    (190.54, "6 / 7", "Csődbe ment a Character.AI, a Disney licitál"),
    (222.60, "7 / 7", "Anthropic: hónapokon belül jöhetnek az önmagukat másoló MI-k"),
    (249.83, "Kövess minket", "Iratkozz fel, hogy ne maradj le a legfrissebb AI-hírekről"),
]
# info cards: (source start, big line, small line) — shown for CARD_HOLD seconds
CARDS = [
    (26.0, "EU AI Act", "Első éles érvényesítés · célpont: OpenAI és Anthropic"),
    (64.2, "8 állam", "Kétpárti per az OpenAI ellen · bírság és kártérítés"),
    (99.6, "Claude Haiku 4.5", "Tesztelés közben beküldött rendőrségi űrlap"),
    (134.4, "Muse Wonder", "A Meta új csúcsmodellje az OpenAI és az Anthropic ellen"),
    (163.3, "Gemini 4 Argon", "Google AI Pro és Ultra · 40+ app integráció"),
    (199.0, "20 millió $", "A Disney ajánlata a Character.AI licenceiért"),
    (228.0, "< 30 Mrd paraméter", "Kis modellek önmásolása — hónapokon belül?"),
]
CARD_HOLD = 7.5


NBH = "\u2011"  # non-breaking hyphen: keep "AI-hírek", "MI-k", "OpenAI-t" on one line


def segments(items, end_out):
    """Turn (src, kicker, title) cues into (out_start, out_end, kicker, title) windows."""
    outs = [(O(s), k, t.replace('-', NBH)) for s, k, t in items]
    res = []
    for i, (o, k, t) in enumerate(outs):
        nxt = outs[i + 1][0] if i + 1 < len(outs) else end_out
        res.append((o, q(nxt), k, t))
    return res


LT = segments(TEASER, q(I0)) + segments(NEWS, q(T))

# ── HTML pieces ──────────────────────────────────────────────────────────────
presenter = []
for n, (kind, o0, o1, s0) in enumerate(timeline()):
    if kind == "p":
        presenter.append(
            f'<video id="pres-{n}" class="clip presenter" src="presenter.webm" muted playsinline '
            f'data-start="{q(o0)}" data-duration="{q(o1 - o0)}" data-media-start="{s0}" data-track-index="1"></video>')

lower = []
for n, (o0, o1, k, t) in enumerate(LT):
    lower.append(
        f'<div id="lt-{n}" class="clip lt-wrap" data-start="{o0}" data-duration="{round(o1 - o0, 4)}" data-track-index="4">'
        f'<div class="lt"><div class="lt-kicker">{html.escape(k)}</div><div class="lt-title">{html.escape(t)}</div>'
        f'<div class="lt-line"></div></div></div>')

cards = []
for n, (s, big, small) in enumerate(CARDS):
    o = O(s)
    cards.append(
        f'<div id="card-{n}" class="clip card-wrap" data-start="{o}" data-duration="{CARD_HOLD}" data-track-index="3">'
        f'<div class="card"><div class="card-tag">Kulcsadat</div><div class="card-big">{html.escape(big)}</div>'
        f'<div class="card-small">{html.escape(small)}</div></div></div>')

js = []
for n, (o0, o1, k, t) in enumerate(LT):
    sel = f"#lt-{n} > .lt"
    js.append(f"tl.fromTo('{sel}',{{autoAlpha:0,x:-60}},{{autoAlpha:1,x:0,duration:0.45,ease:'power3.out'}},{o0});")
    js.append(f"tl.fromTo('{sel} .lt-kicker',{{scaleX:0}},{{scaleX:1,duration:0.35,ease:'expo.out'}},{q(o0 + 0.1)});")
    js.append(f"tl.fromTo('{sel} .lt-title',{{clipPath:'inset(0 100% 0 0)'}},{{clipPath:'inset(0 0% 0 0)',duration:0.55,ease:'power3.inOut'}},{q(o0 + 0.18)});")
    js.append(f"tl.fromTo('{sel} .lt-line',{{scaleX:0}},{{scaleX:1,duration:0.7,ease:'expo.out'}},{q(o0 + 0.3)});")
    if o1 < T - 0.1 and o1 != q(I0):
        js.append(f"tl.to('{sel}',{{autoAlpha:0,x:-30,duration:0.25,ease:'power2.in'}},{q(o1 - 0.25)});")
for n, (s, big, small) in enumerate(CARDS):
    o = O(s)
    js.append(f"tl.fromTo('#card-{n} > .card',{{autoAlpha:0,x:50}},{{autoAlpha:1,x:0,duration:0.5,ease:'power3.out'}},{o});")
    js.append(f"tl.fromTo('#card-{n} .card-big',{{autoAlpha:0,y:16}},{{autoAlpha:1,y:0,duration:0.45,ease:'power3.out'}},{q(o + 0.2)});")
    js.append(f"tl.to('#card-{n} > .card',{{autoAlpha:0,x:30,duration:0.35,ease:'power2.in'}},{q(o + CARD_HOLD - 0.35)});")

INDEX = f"""<!doctype html>
<html lang="hu">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width={W}, height={H}" />
<script src="vendor/gsap.min.js"></script>
<style>
@font-face {{ font-family:"Archivo"; src:url("fonts/archivo-latin-wdth-normal.woff2") format("woff2"); font-weight:100 900; font-stretch:62% 125%; font-display:block; unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+2000-206F,U+FEFF,U+FFFD; }}
@font-face {{ font-family:"Archivo"; src:url("fonts/archivo-latin-ext-wdth-normal.woff2") format("woff2"); font-weight:100 900; font-stretch:62% 125%; font-display:block; unicode-range:U+0100-02AF,U+1E00-1E9F; }}
@font-face {{ font-family:"Inter"; src:url("fonts/inter-latin-600-normal.woff2") format("woff2"); font-weight:600; font-display:block; unicode-range:U+0000-00FF,U+2000-206F; }}
@font-face {{ font-family:"Inter"; src:url("fonts/inter-latin-ext-600-normal.woff2") format("woff2"); font-weight:600; font-display:block; unicode-range:U+0100-02AF; }}
:root {{ --ink:#0d0b1e; --yellow:#dfff84; --lilac:#9570ff; --violet:#5e44e4; --white:#ffffff; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:{W}px; height:{H}px; overflow:hidden; background:var(--ink); }}
#root {{ position:relative; width:{W}px; height:{H}px; overflow:hidden; font-family:"Archivo","Inter",sans-serif; }}
#studio {{ position:absolute; inset:0; width:{W}px; height:{H}px; object-fit:cover; }}
#sweep {{ position:absolute; top:60px; height:760px; left:90px; width:260px; opacity:.0;
  background:linear-gradient(100deg, rgba(201,182,255,0), rgba(201,182,255,.22), rgba(201,182,255,0)); filter:blur(8px); }}
.presenter {{ position:absolute; left:0; top:0; width:{W}px; height:{H}px; object-fit:cover;
  filter: drop-shadow(0 0 18px rgba(149,112,255,.38)); }}
#intro {{ position:absolute; inset:0; width:{W}px; height:{H}px; object-fit:cover; z-index:20; }}
#flash {{ position:absolute; inset:0; z-index:21; opacity:0; background:radial-gradient(60% 60% at 50% 50%, #ffffff, rgba(149,112,255,.9) 60%, rgba(13,11,30,.9)); pointer-events:none; }}

/* show bug */
#bug {{ position:absolute; left:64px; top:52px; z-index:6; display:flex; align-items:center; gap:14px; }}
#bug .b1 {{ font-stretch:125%; font-weight:800; font-size:34px; color:#fff; letter-spacing:.02em; text-shadow:0 0 16px rgba(149,112,255,.6); }}
#bug .b1 b {{ color:var(--yellow); font-weight:800; }}
#bug .b2 {{ font-stretch:115%; font-weight:600; font-size:13px; letter-spacing:.42em; color:#fff; background:var(--lilac); padding:6px 8px 6px 14px; border-radius:3px; }}

/* lower third */
.lt-wrap {{ position:absolute; inset:0; z-index:5; pointer-events:none; }}
.lt {{ position:absolute; left:64px; bottom:70px; max-width:1340px; }}
.lt-kicker {{ display:inline-block; transform-origin:left center; background:var(--yellow); color:var(--ink);
  font-stretch:115%; font-weight:800; font-size:22px; letter-spacing:.14em; text-transform:uppercase; padding:9px 18px 8px; border-radius:3px 3px 0 0; }}
.lt-title {{ background:rgba(13,11,30,.86); border-left:8px solid var(--lilac); color:#fff; font-stretch:108%; font-weight:750;
  font-size:44px; line-height:1.12; padding:16px 30px 18px 24px; box-shadow:0 10px 40px rgba(0,0,0,.45), 0 0 30px rgba(149,112,255,.25); }}
.lt-line {{ height:5px; background:linear-gradient(90deg, var(--lilac), rgba(149,112,255,0)); transform-origin:left center; }}

/* info card */
.card-wrap {{ position:absolute; inset:0; z-index:4; pointer-events:none; }}
.card {{ position:absolute; right:60px; top:300px; width:400px; background:rgba(13,11,30,.82);
  border:2px solid rgba(149,112,255,.55); border-radius:16px; padding:22px 26px 24px; box-shadow:0 0 40px rgba(149,112,255,.3); }}
.card-tag {{ font-stretch:115%; font-weight:700; font-size:15px; letter-spacing:.32em; text-transform:uppercase; color:var(--lilac); }}
.card-big {{ margin-top:10px; font-stretch:118%; font-weight:800; font-size:44px; line-height:1.02; color:var(--yellow); text-shadow:0 0 18px rgba(223,255,132,.35); }}
.card-small {{ margin-top:12px; font-family:"Inter",sans-serif; font-weight:600; font-size:21px; line-height:1.35; color:#e9e2ff; }}
</style>
</head>
<body>
<div id="root" data-composition-id="ai-hirado-01" data-start="0" data-duration="{T}" data-fps="{FPS}" data-width="{W}" data-height="{H}">
<img id="studio" src="img/studio.png" alt="" />
<div id="sweep"></div>
{chr(10).join(presenter)}
{chr(10).join(cards)}
{chr(10).join(lower)}
<div id="bug" class="clip" data-start="0" data-duration="{T}" data-track-index="6"><div class="b1"><b>AI</b> HÍREK</div><div class="b2">A NAGYVILÁGBÓL</div></div>
<video id="intro" class="clip" src="intro.mp4" muted playsinline data-start="{q(I0)}" data-duration="{q(I1 - I0)}" data-track-index="7"></video>
<div id="flash"></div>
<audio id="mix" src="mix.wav" data-start="0" data-duration="{T}" data-track-index="10"></audio>
</div>
<script>
(function () {{
const tl = gsap.timeline({{ paused: true }});
// slow light sweep across the LED wall (finite repeats)
tl.fromTo('#sweep', {{ x: 0, opacity: 0 }}, {{ x: 1480, opacity: 1, duration: 9, ease: 'sine.inOut', repeat: {int(T // 9) - 1}, yoyo: true }}, 0);
// intro: flash in / flash out
tl.fromTo('#flash', {{ opacity: 0 }}, {{ opacity: 0.9, duration: 0.18, ease: 'power2.out' }}, {q(I0 - 0.18)});
tl.to('#flash', {{ opacity: 0, duration: 0.3, ease: 'power2.in' }}, {q(I0 + 0.02)});
tl.fromTo('#flash', {{ opacity: 0 }}, {{ opacity: 0.9, duration: 0.15, ease: 'power2.out' }}, {q(I1 - 0.15)});
tl.to('#flash', {{ opacity: 0, duration: 0.35, ease: 'power2.in' }}, {q(I1 + 0.02)});
{chr(10).join(js)}
window.__timelines = window.__timelines || {{}};
window.__timelines["ai-hirado-01"] = tl;
tl.seek(0);
}})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    (ROOT / "public" / "index.html").write_text(INDEX)
    print(f"{T}s · {len(presenter)} presenter clips · {len(LT)} titles · {len(CARDS)} cards · intro {I0:.2f}-{I1:.2f}")
