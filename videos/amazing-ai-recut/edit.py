"""Edit decision list shared by cut_source.py and build_composition.py.

All times are on the uncut timeline (original recording minus TRIM seconds).
"""

TRIM = 4.9  # sitting down in front of the camera

# Removed ranges, snapped to the silences around the sentence boundaries.
EDIT_CUTS = [
    (25.95, 33.80),  # "Csak létre… olyan ruhában … amelyeket csak szeretnél." (incl. the false start)
    (38.30, 44.66),  # "lehetsz akár egy napsütötte tengerparton … meg se kell szólalni."
]


def kept_segments(duration):
    segs, t = [], 0.0
    for a, b in EDIT_CUTS:
        segs.append((t, a))
        t = b
    segs.append((t, duration))
    return segs


def in_cut(t):
    return any(a <= t < b for a, b in EDIT_CUTS)


def remap(t):
    """Uncut time → edited time. Times inside a removed range snap to its start."""
    shift = 0.0
    for a, b in EDIT_CUTS:
        if t >= b:
            shift += b - a
        elif t >= a:
            return a - shift
    return t - shift
