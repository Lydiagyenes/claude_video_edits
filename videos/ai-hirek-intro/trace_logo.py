#!/usr/bin/env python3
"""Vectorise assets/amazing_logo.png (323×62 raster) into assets/amazing_logo.svg
so the logo stays sharp at 1080p and can be extruded in 3D. Two layers:
#icon (purple mark) and #wordmark (white text)."""
import subprocess

import numpy as np
import potrace

S = 12
H, W = 62 * S, 323 * S
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", "assets/amazing_logo.png", "-vf",
                      f"scale=iw*{S}:ih*{S}:flags=lanczos", "-f", "rawvideo", "-pix_fmt", "rgba", "-"],
                     capture_output=True, check=True).stdout
a = np.frombuffer(raw, np.uint8).reshape(H, W, 4).astype(float)
alpha = a[..., 3]
lum = a[..., 0] * .3 + a[..., 1] * .59 + a[..., 2] * .11
xs = np.arange(W)[None, :]


def trace(mask):
    # potracer fills the "dark" side of the bitmap, so hand it the inverted mask
    plist = potrace.Bitmap(~mask).trace(turdsize=60, alphamax=1.0, opticurve=True, opttolerance=0.25)
    parts = []
    for curve in plist:
        p = curve.start_point
        d = f"M{p.x / S:.3f},{p.y / S:.3f}"
        for seg in curve.segments:
            e = seg.end_point
            if seg.is_corner:
                d += f"L{seg.c.x / S:.3f},{seg.c.y / S:.3f}L{e.x / S:.3f},{e.y / S:.3f}"
            else:
                d += (f"C{seg.c1.x / S:.3f},{seg.c1.y / S:.3f} {seg.c2.x / S:.3f},{seg.c2.y / S:.3f} "
                      f"{e.x / S:.3f},{e.y / S:.3f}")
        parts.append(d + "Z")
    return " ".join(parts)


icon = (alpha > 128) & (xs < 61 * S)
text = (alpha > 185) & (xs >= 61 * S)   # high cut keeps the original light stroke weight
svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 323 62">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#A585FF"/><stop offset="1" stop-color="#7B5CF5"/></linearGradient></defs>
<path id="icon" fill="url(#g)" d="{trace(icon)}"/>
<path id="wordmark" fill="#FFFFFF" d="{trace(text)}"/>
</svg>
"""
open("assets/amazing_logo.svg", "w").write(svg)
print("ok", len(svg))
