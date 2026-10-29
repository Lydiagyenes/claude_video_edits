"""Edit for AI híradó 10.29: the recording plays uncut; the 3D show intro is inserted
after the teaser line "Ez itt az AI hírek a nagyvilágból." (ends 13.99 s)."""

SRC_DUR = 145.003
CUT = 14.15          # source time where the intro is inserted
INTRO_DUR = 5.5
INTRO = (CUT, CUT + INTRO_DUR)   # output window of the intro
TOTAL = SRC_DUR + INTRO_DUR


def O(src):
    """Source-recording time → output time."""
    return src if src < CUT else src + INTRO_DUR
