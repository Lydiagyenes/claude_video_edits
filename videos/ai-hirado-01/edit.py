"""Edit decision list for AI híradó #01 (times in the source recording, seconds).

Segments are kept ranges of the presenter recording; the 3D show intro is inserted
after the teaser line "Ez itt az AI híradó, a hét legfontosabb technológiai
eseményeivel." Long headline pauses are tightened to ~0.5 s.
"""

INTRO_FILE = "public/intro.mp4"
INTRO_DUR = 5.5

# kept presenter ranges, in order; INTRO marks where the show intro plays
SEGMENTS = [
    (4.90, 21.95),    # teaser (speech starts 5.18, ends 21.81)
    "INTRO",
    (22.25, 91.40),   # Brüsszel / AI Act  +  8 állam vs OpenAI
    (93.00, 97.75),   # Claude headline
    (98.95, 156.40),  # Claude story  +  Meta Muse Wonder
    (156.60, 160.80), # Gemini 4 Argon headline
    (162.35, 259.75), # Gemini story … Character.AI … Anthropic … CTA
]


def timeline():
    """[(kind, out_start, out_end, src_start)] with kind 'p' (presenter) or 'intro'."""
    out, t = [], 0.0
    for s in SEGMENTS:
        if s == "INTRO":
            out.append(("intro", t, t + INTRO_DUR, 0.0))
            t += INTRO_DUR
        else:
            a, b = s
            out.append(("p", t, t + (b - a), a))
            t += b - a
    return out


def src_to_out(ts):
    """Map a source-recording time to the edited timeline (None if cut)."""
    for kind, o0, o1, s0 in timeline():
        if kind == "p" and s0 <= ts <= s0 + (o1 - o0):
            return o0 + (ts - s0)
    return None


def intro_window():
    for kind, o0, o1, _ in timeline():
        if kind == "intro":
            return o0, o1


def total():
    return timeline()[-1][2]
