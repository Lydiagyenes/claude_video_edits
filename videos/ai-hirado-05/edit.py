"""Edit for AI híradó 11.12: the recording plays uncut; the 3D show intro is inserted
after the teaser line "Ezek az AI hírek a nagyvilágból." (pause 19.74–20.13 s)."""

SRC_DUR = 217.58
CUT = 19.9           # source time where the intro is inserted
INTRO_DUR = 5.5
INTRO = (CUT, CUT + INTRO_DUR)   # output window of the intro
TOTAL = SRC_DUR + INTRO_DUR


def O(src):
    """Source-recording time → output time."""
    return src if src < CUT else src + INTRO_DUR
