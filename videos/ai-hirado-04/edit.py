"""Edit for AI híradó 11.05: the recording plays uncut; the 3D show intro is inserted
after the teaser line "Nézzük, mi történt még!" (ends 12.00 s)."""

SRC_DUR = 215.042
CUT = 12.15          # source time where the intro is inserted
INTRO_DUR = 5.5
INTRO = (CUT, CUT + INTRO_DUR)   # output window of the intro
TOTAL = SRC_DUR + INTRO_DUR


def O(src):
    """Source-recording time → output time."""
    return src if src < CUT else src + INTRO_DUR
