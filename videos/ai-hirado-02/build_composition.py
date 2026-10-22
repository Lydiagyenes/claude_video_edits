#!/usr/bin/env python3
"""AI híradó 2026.10.22 — subtitles + one data graphic per story on the finished video.

The source video (studio, intro, cuts) is untouched; this adds:
  * subtitles from captions_src.py (hand-corrected Whisper), hidden during the intro
  * seven graphic cards on the free right-hand wall, every figure taken from the
    sources listed in GRAPHICS[*]['source'] (no unverified numbers on screen)
Run:  python3 build_composition.py   →  public/index.html
"""
import html
from pathlib import Path

from captions_src import SENTENCES

ROOT = Path(__file__).resolve().parent
FPS, W, H = 30, 1920, 1080
DURATION = 287.4333
INTRO = (12.53, 18.03)


def q(t):
    return round(round(t * FPS) / FPS, 4)


def esc(s):
    return html.escape(s).replace("-", "‑")  # keep hyphenated words on one line


# ── subtitles: split each sentence into ≤2-line chunks, timed by character share ──
MAX = 84


def chunks(text):
    words, out, cur = text.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > MAX:
            out.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    out.append(cur)
    # avoid a tiny orphan chunk: rebalance the last two
    if len(out) > 1 and len(out[-1]) < 22:
        both = (out[-2] + " " + out[-1]).split()
        half = len(both) // 2
        out[-2:] = [" ".join(both[:half]), " ".join(both[half:])]
    return out


subs = []
for s0, s1, text in SENTENCES:
    parts = chunks(text)
    total = sum(len(p) for p in parts)
    t = s0
    for p in parts:
        d = (s1 - s0) * len(p) / total
        subs.append((q(t), q(t + d), p))
        t += d
# close tiny gaps so subtitles don't flicker between sentences
for i in range(len(subs) - 1):
    a0, a1, p = subs[i]
    b0 = subs[i + 1][0]
    if 0 < b0 - a1 < 0.6:
        subs[i] = (a0, b0, p)

sub_html = [
    f'<div id="sub-{i}" class="clip subw" data-start="{a}" data-duration="{round(b - a, 4)}" data-track-index="5">'
    f'<div class="sub">{esc(p)}</div></div>'
    for i, (a, b, p) in enumerate(subs) if b - a > 0.05 and not (INTRO[0] <= a < INTRO[1])
]

# ── graphics ────────────────────────────────────────────────────────────────
def bar(label, value, pct, cls="", vid=""):
    return (f'<div class="row"><div class="rl">{label}</div><div class="track"><div class="fill {cls}" id="{vid}" '
            f'data-w="{pct}"></div></div><div class="rv">{value}</div></div>')


def item(text, kind="ok"):
    return f'<li class="li {kind}"><span class="mark"></span><span>{text}</span></li>'


GRAPHICS = [
    dict(id="g1", start=26.0, end=47.6, kicker="Anthropic · tőzsdei tervezet",
         source="Forrás: Wall Street Journal (S‑1 tervezet), Fortune, 2026.10.20–21",
         phases=[
             (26.0, "Bevétel, első félév",
              bar("2025 I.", "1,1 Mrd $", 6.7, "lil") + bar("2026 I.", "16,3 Mrd $", 100, "mag")
              + '<div class="big">~15×</div><div class="note">növekedés egy év alatt</div>'),
             (36.0, "Nettó veszteség, 2026 I. félév",
              '<div class="big">80,7 Mrd $</div>'
              '<div class="stack"><div class="seg lil" style="flex:72"></div><div class="seg mag" style="flex:8.7"></div></div>'
              '<div class="legend"><span class="dot lil"></span>~72 Mrd $ nem készpénzes könyvelési tétel</div>'
              '<div class="legend"><span class="dot mag"></span>~8,7 Mrd $ egyéb</div>'),
             (41.5, "Felhőszerződések",
              '<div class="big">≈450 Mrd $</div><div class="note">fel nem mondható felhőkapacitás-szerződés, 7–10 évre</div>'
              + bar("Google", "111 Mrd $", 100, "lil") + bar("AWS", "110 Mrd $", 99, "lil")
              + bar("Microsoft", "31 Mrd $", 28, "lil")),
         ]),
    dict(id="g2", start=73.4, end=95.2, kicker="FTC · polgári idézés",
         source="Forrás: Axios; az FTC megerősítette (CBS News), 2026.10.14–15",
         phases=[
             (73.4, "OpenAI · Anthropic",
              '<div class="duo"><div class="pill">OpenAI</div><div class="pill">Anthropic</div></div>'
              '<div class="big">50+ oldal</div><div class="note">idézésenként, 2026. október 14.</div>'
              '<div class="sub2">Bekért iratok</div><ul class="list">'
              + item("Biztonsági incidensek") + item("Védelmi gyakorlatok") + item("Marketinganyagok")
              + item("Adatvédelmi szabályok") + "</ul>"),
         ]),
    dict(id="g3", start=110.1, end=131.0, kicker="DHS · DeepSeek‑tiltás",
         source="Forrás: DHS kizárási és eltávolítási rendelet #2026‑01 (FASCSA), Federal Register, 2026.10.20",
         phases=[
             (110.1, "Polgári szövetségi hivatalok",
              '<ul class="list">' + item("Új DeepSeek‑termék nem vásárolható", "no")
              + item("A meglévőket el kell távolítani", "no")
              + item("A DeepSeekre épülő, más cégek szoftvereire is vonatkozik", "no") + "</ul>"
              '<div class="sub2">Indok</div><div class="note">Nemzetbiztonsági és adatkezelési kockázat; '
              'a nemzetbiztonsági rendszerekre külön szabályok vonatkoznak.</div>'),
         ]),
    dict(id="g4", start=151.0, end=173.2, kicker="Kína · exportkorlátozási tervezet",
         source="Forrás: MOFCOM–MOST tervezet, AP, 2026.10.16 · véleményezés: nov. 15‑ig",
         phases=[
             (151.0, "40 technológia a listán",
              '<div class="donut-wrap"><svg viewBox="0 0 200 200" class="donut">'
              '<circle cx="100" cy="100" r="78" class="ring"/>'
              '<circle cx="100" cy="100" r="78" class="arc mag" id="g4-a1" data-frac="0.575" data-off="0"/>'
              '<circle cx="100" cy="100" r="78" class="arc lil" id="g4-a2" data-frac="0.30" data-off="0.575"/>'
              '<circle cx="100" cy="100" r="78" class="arc vio" id="g4-a3" data-frac="0.125" data-off="0.875"/>'
              '</svg><div class="donut-c"><b>40</b><span>technológia</span></div></div>'
              '<div class="legend"><span class="dot mag"></span><b>23</b>&nbsp;mesterséges intelligencia</div>'
              '<div class="legend"><span class="dot lil"></span><b>12</b>&nbsp;napelemes</div>'
              '<div class="legend"><span class="dot vio"></span><b>5</b>&nbsp;biotechnológia / orvosi</div>'),
         ]),
    dict(id="g5", start=190.1, end=209.2, kicker="NVIDIA · GTC Berlin",
         source="Forrás: NVIDIA, GTC Berlin keynote, 2026.10.21",
         phases=[
             (190.1, "Szubsztrát‑kapacitás",
              bar("Most", "1×", 40, "lil") + bar("3 év múlva", "2,5×", 100, "mag")
              + '<div class="note">IBIDEN, Samsung Electro‑Mechanics, Unimicron</div>'),
             (200.1, "DSX POD – helyszíni telepítés",
              bar("Eddig", "~6 hónap", 100, "lil") + bar("DSX POD", "~14 nap", 7.8, "mag")
              + '<div class="note">Az NVIDIA szerint, a helyszíni közművek elkészülte után; '
              'szállítás 2027 elejétől.</div>'),
         ]),
    dict(id="g6", start=226.0, end=242.2, kicker="Meta · 3. negyedév",
         source="Forrás: Meta Q3 2026 gyorsjelentés (CNBC, Fortune), 2026.10.21",
         phases=[
             (226.0, "Bevétel",
              bar("2025 Q3", "51,2 Mrd $", 79, "lil") + bar("2026 Q3", "64,6 Mrd $", 100, "mag")
              + '<div class="big">+26%</div><div class="note">éves összevetésben</div>'),
             (233.1, "2026‑os beruházási keret",
              '<div class="big">135–145 Mrd $</div><div class="note">korábban: 130–145 Mrd $</div>'
              '<div class="range"><div class="rtrack"></div><div class="rband" id="g6-band"></div>'
              '<div class="rtick" style="left:0%">120</div><div class="rtick" style="left:50%">135</div>'
              '<div class="rtick" style="left:83.3%">145</div><div class="rtick" style="left:100%">150</div></div>'),
         ]),
    dict(id="g7", start=245.7, end=270.2, kicker="ChatGPT · zárolt csevegések",
         source="Forrás: OpenAI súgó, TechCrunch, 2026.10.20",
         phases=[
             (245.7, "Bevezetés: 2026. október 20.",
              '<div class="lock"><div class="shackle"></div><div class="body"><div class="kh"></div></div></div>'
              '<ul class="list">' + item("4 jegyű PIN, Face ID vagy Touch ID")
              + item("Rejtve az előzményekből és a keresésből") + item("Saját, külön memória")
              + item("Nem végponttól végpontig titkosítás", "warn")
              + item("PIN visszaállítása = a zárolt csevegések törlése", "warn") + "</ul>"),
         ]),
]

g_html, g_js = [], []
for g in GRAPHICS:
    s, e = q(g["start"]), q(g["end"])
    ph_html = []
    for k, (pt, ptitle, body) in enumerate(g["phases"]):
        ph_html.append(f'<div class="phase" id="{g["id"]}-p{k}"><div class="ptitle">{ptitle}</div>{body}</div>')
    g_html.append(
        f'<div id="{g["id"]}" class="clip gw" data-start="{s}" data-duration="{round(e - s, 4)}" data-track-index="3">'
        f'<div class="gcard"><div class="kick">{g["kicker"]}</div><div class="phases">{"".join(ph_html)}</div>'
        f'<div class="src">{g["source"]}</div></div></div>')
    sel = f'#{g["id"]} .gcard'
    g_js.append(f"tl.fromTo('{sel}',{{autoAlpha:0,x:70}},{{autoAlpha:1,x:0,duration:0.55,ease:'power3.out'}},{s});")
    g_js.append(f"tl.to('{sel}',{{autoAlpha:0,x:40,duration:0.4,ease:'power2.in'}},{q(e - 0.4)});")
    for k, (pt, _, body) in enumerate(g["phases"]):
        p = f'#{g["id"]}-p{k}'
        t0 = q(max(pt, g["start"]) + (0.25 if k == 0 else 0))
        g_js.append(f"tl.fromTo('{p}',{{autoAlpha:0,y:18}},{{autoAlpha:1,y:0,duration:0.45,ease:'power3.out'}},{t0});")
        if k + 1 < len(g["phases"]):
            g_js.append(f"tl.to('{p}',{{autoAlpha:0,y:-12,duration:0.3,ease:'power2.in'}},{q(g['phases'][k + 1][0] - 0.3)});")
        # bars grow, list items stagger, donut arcs sweep
        g_js.append(f"tl.fromTo('{p} .fill',{{scaleX:0}},{{scaleX:1,duration:0.9,ease:'power3.out',stagger:0.18}},{q(t0 + 0.2)});")
        g_js.append(f"tl.fromTo('{p} .li',{{autoAlpha:0,x:24}},{{autoAlpha:1,x:0,duration:0.4,ease:'power2.out',stagger:0.45}},{q(t0 + 0.4)});")
        g_js.append(f"tl.fromTo('{p} .seg',{{scaleX:0}},{{scaleX:1,duration:0.8,ease:'power3.out',stagger:0.25}},{q(t0 + 0.3)});")
        g_js.append(f"tl.fromTo('{p} .rband',{{scaleX:0}},{{scaleX:1,duration:0.8,ease:'power3.out'}},{q(t0 + 0.4)});")

# bar widths are static CSS (scaleX animates from 0), donut arcs computed from fractions
CIRC = 2 * 3.14159265 * 78

INDEX = f"""<!doctype html>
<html lang="hu">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width={W}, height={H}" />
<script src="vendor/gsap.min.js"></script>
<style>
@font-face {{ font-family:"Archivo"; src:url("fonts/archivo-latin-wdth-normal.woff2") format("woff2"); font-weight:100 900; font-stretch:62% 125%; font-display:block; unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+2000-206F,U+2190-22FF,U+FEFF,U+FFFD; }}
@font-face {{ font-family:"Archivo"; src:url("fonts/archivo-latin-ext-wdth-normal.woff2") format("woff2"); font-weight:100 900; font-stretch:62% 125%; font-display:block; unicode-range:U+0100-02AF,U+1E00-1E9F; }}
@font-face {{ font-family:"Inter"; src:url("fonts/inter-latin-600-normal.woff2") format("woff2"); font-weight:600; font-display:block; unicode-range:U+0000-00FF,U+2000-206F,U+2190-22FF; }}
@font-face {{ font-family:"Inter"; src:url("fonts/inter-latin-ext-600-normal.woff2") format("woff2"); font-weight:600; font-display:block; unicode-range:U+0100-02AF; }}
:root {{ --ink:#0d0b1e; --violet:#5e44e4; --lilac:#9570ff; --magenta:#df0ec4; --white:#ffffff; --soft:#e4dcff; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:{W}px; height:{H}px; overflow:hidden; background:#000; }}
#root {{ position:relative; width:{W}px; height:{H}px; overflow:hidden; font-family:"Inter","Archivo",sans-serif; }}
#main {{ position:absolute; inset:0; width:{W}px; height:{H}px; object-fit:cover; }}

/* subtitles */
.subw {{ position:absolute; inset:0; z-index:6; pointer-events:none; }}
.sub {{ position:absolute; left:50%; bottom:44px; transform:translateX(-50%); max-width:1240px; width:max-content;
  text-align:center; font-family:"Inter",sans-serif; font-weight:600; font-size:40px; line-height:1.3; color:#fff;
  background:rgba(13,11,30,.72); padding:10px 26px 12px; border-radius:12px; border-bottom:3px solid var(--lilac);
  text-shadow:0 2px 8px rgba(0,0,0,.6); }}

/* graphic card */
.gw {{ position:absolute; inset:0; z-index:4; pointer-events:none; }}
.gcard {{ position:absolute; right:44px; top:70px; width:480px; min-height:660px; padding:26px 28px 22px;
  background:linear-gradient(160deg, rgba(30,20,78,.92), rgba(13,11,30,.94)); border:2px solid rgba(149,112,255,.65);
  border-radius:20px; box-shadow:0 18px 60px rgba(0,0,0,.5), 0 0 40px rgba(149,112,255,.35); color:#fff;
  display:flex; flex-direction:column; }}
.kick {{ font-family:"Archivo"; font-stretch:115%; font-weight:800; font-size:17px; letter-spacing:.2em; text-transform:uppercase;
  color:#fff; background:var(--violet); align-self:flex-start; padding:7px 12px 6px; border-radius:4px; }}
.phases {{ position:relative; flex:1; margin-top:16px; }}
.phase {{ position:absolute; inset:0; }}
.ptitle {{ font-family:"Archivo"; font-stretch:110%; font-weight:800; font-size:30px; line-height:1.1; color:var(--soft); margin-bottom:18px; }}
.big {{ font-family:"Archivo"; font-stretch:118%; font-weight:850; font-size:58px; line-height:1; color:#fff; margin-top:8px; white-space:nowrap;
  text-shadow:0 0 26px rgba(223,14,196,.45); }}
.note {{ font-size:20px; line-height:1.35; color:#cfc4ff; margin-top:8px; }}
.sub2 {{ font-family:"Archivo"; font-weight:800; font-size:17px; letter-spacing:.2em; text-transform:uppercase; color:var(--lilac); margin:18px 0 8px; }}
.row {{ display:flex; align-items:center; gap:12px; margin:12px 0; }}
.rl {{ width:96px; font-size:19px; color:#d9d0ff; }}
.track {{ flex:1; height:30px; background:rgba(149,112,255,.14); border-radius:6px; overflow:hidden; }}
.fill {{ height:100%; border-radius:6px; transform-origin:left center; }}
.rv {{ width:136px; text-align:right; white-space:nowrap; font-family:"Archivo"; font-stretch:110%; font-weight:800; font-size:22px; }}
.lil {{ background:var(--lilac); }} .mag {{ background:linear-gradient(90deg,var(--violet),var(--magenta)); }} .vio {{ background:var(--violet); }}
.stack {{ display:flex; height:34px; border-radius:6px; overflow:hidden; margin:18px 0 12px; gap:3px; }}
.seg {{ height:100%; transform-origin:left center; }}
.legend {{ display:flex; align-items:center; font-size:20px; color:#e4dcff; margin:8px 0; }}
.dot {{ width:16px; height:16px; border-radius:4px; margin-right:10px; flex:none; }}
.duo {{ display:flex; gap:12px; }}
.pill {{ font-family:"Archivo"; font-weight:800; font-size:22px; padding:8px 16px; border-radius:999px; border:2px solid var(--lilac); }}
.list {{ list-style:none; margin-top:8px; }}
.li {{ display:flex; align-items:flex-start; gap:12px; font-size:20px; line-height:1.28; margin:8px 0; color:#f1edff; }}
.mark {{ flex:none; width:24px; height:24px; border-radius:50%; margin-top:2px; position:relative; }}
.ok .mark {{ background:var(--lilac); }}
.ok .mark::after {{ content:""; position:absolute; left:8px; top:4px; width:6px; height:11px; border:solid #fff; border-width:0 3px 3px 0; transform:rotate(45deg); }}
.no .mark {{ background:var(--magenta); }}
.no .mark::before, .no .mark::after {{ content:""; position:absolute; left:11px; top:5px; width:3px; height:14px; background:#fff; border-radius:2px; }}
.no .mark::before {{ transform:rotate(45deg); }} .no .mark::after {{ transform:rotate(-45deg); }}
.warn .mark {{ background:transparent; border:2px solid var(--magenta); }}
.warn .mark::after {{ content:""; position:absolute; left:9px; top:3px; width:3px; height:10px; background:var(--magenta); box-shadow:0 13px 0 -0.5px var(--magenta); border-radius:2px; }}
.donut-wrap {{ position:relative; width:230px; height:230px; margin:0 auto 6px; }}
.donut {{ width:230px; height:230px; }}
.ring {{ fill:none; stroke:rgba(149,112,255,.15); stroke-width:30; }}
.arc {{ fill:none; stroke-width:30; }}
.arc.mag {{ stroke:var(--magenta); background:none; }} .arc.lil {{ stroke:var(--lilac); background:none; }} .arc.vio {{ stroke:var(--violet); background:none; }}
.donut-c {{ position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; }}
.donut-c b {{ font-family:"Archivo"; font-stretch:118%; font-weight:850; font-size:60px; line-height:1; }}
.donut-c span {{ font-size:18px; color:#cfc4ff; }}
.range {{ position:relative; height:70px; margin-top:26px; }}
.rtrack {{ position:absolute; left:0; right:0; top:10px; height:14px; border-radius:7px; background:rgba(149,112,255,.18); }}
.rband {{ position:absolute; left:50%; width:33.3%; top:6px; height:22px; border-radius:6px; transform-origin:left center;
  background:linear-gradient(90deg,var(--violet),var(--magenta)); box-shadow:0 0 18px rgba(223,14,196,.5); }}
.rtick {{ position:absolute; top:38px; transform:translateX(-50%); font-size:16px; color:#cfc4ff; }}
.lock {{ position:relative; width:76px; height:86px; margin:0 0 6px 4px; }}
.lock .shackle {{ position:absolute; left:14px; top:0; width:48px; height:48px; border:9px solid var(--lilac); border-bottom:none; border-radius:26px 26px 0 0; }}
.lock .body {{ position:absolute; left:0; bottom:0; width:76px; height:52px; border-radius:10px; background:linear-gradient(135deg,var(--violet),var(--magenta)); }}
.lock .kh {{ position:absolute; left:33px; top:16px; width:10px; height:18px; border-radius:5px; background:#fff; }}
.src {{ margin-top:12px; font-size:13.5px; line-height:1.35; color:#a99bd9; border-top:1px solid rgba(149,112,255,.3); padding-top:10px; }}
</style>
</head>
<body>
<div id="root" data-composition-id="ai-hirado-1022" data-start="0" data-duration="{DURATION}" data-fps="{FPS}" data-width="{W}" data-height="{H}">
<video id="main" src="source.mp4" playsinline data-has-audio="true" data-start="0" data-duration="{DURATION}" data-track-index="1"></video>
{chr(10).join(g_html)}
{chr(10).join(sub_html)}
</div>
<script>
(function () {{
// static geometry: bar widths and donut arcs
document.querySelectorAll('.fill[data-w]').forEach(function (el) {{ el.style.width = el.dataset.w + '%'; }});
document.querySelectorAll('.arc[data-frac]').forEach(function (el) {{
  var c = {CIRC:.3f}, f = parseFloat(el.dataset.frac), o = parseFloat(el.dataset.off);
  el.style.strokeDasharray = (c * f - 3) + ' ' + c; el.style.strokeDashoffset = (-c * o);
}});
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(g_js)}
// donut sweep for the China card
tl.fromTo('#g4 .donut', {{ rotation: -150, scale: 0.85, autoAlpha: 0 }}, {{ rotation: -90, scale: 1, autoAlpha: 1, duration: 0.9, ease: 'power3.out' }}, {q(151.5)});
window.__timelines = window.__timelines || {{}};
window.__timelines["ai-hirado-1022"] = tl;
tl.seek(0);
}})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    (ROOT / "public" / "index.html").write_text(INDEX)
    print(f"{len(sub_html)} subtitle chunks · {len(GRAPHICS)} graphics")
