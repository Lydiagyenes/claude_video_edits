"""Edit for AI híradó 11.19: the recording plays uncut; the 3D show intro is inserted
after the teaser line "Ezek az AI hírek a nagyvilágból." (pause 17.31–18.14 s)."""

SRC_DUR = 202.32
CUT = 17.75          # source time where the intro is inserted
INTRO_DUR = 5.5
INTRO = (CUT, CUT + INTRO_DUR)   # output window of the intro
TOTAL = SRC_DUR + INTRO_DUR


def O(src):
    """Source-recording time → output time."""
    return src if src < CUT else src + INTRO_DUR
