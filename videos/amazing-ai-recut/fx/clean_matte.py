#!/usr/bin/env python3
"""Clean the subject matte for the FX segment and track the head.

- Drops any alpha blob that sits entirely inside the neon-logo zone above her
  head (the matting model sometimes keeps a piece of the "Amazing AI" sign).
- Writes public/fx-matte.webm (VP9 + alpha) and fx/head-track.json
  (per-frame head top / centre / width in source pixels, smoothed).
Run from the project dir:  python3 fx/clean_matte.py
"""
import json
import subprocess

import numpy as np
from scipy import ndimage

SRC = "fx/seg-matte.webm"
OUT = "public/fx-matte.webm"
W, H, FPS, SEG_START = 1920, 1080, 30, 33.5
DS = 4                                   # analysis downscale
LOGO_ZONE = (980, 100, 1330, 345)        # x0, y0, x1, y1 in source px

dec = subprocess.Popen(["ffmpeg", "-v", "error", "-c:v", "libvpx-vp9", "-i", SRC,
                        "-f", "rawvideo", "-pix_fmt", "rgba", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba",
                        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                        "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0", "-crf", "20",
                        "-row-mt", "1", "-auto-alt-ref", "0", OUT], stdin=subprocess.PIPE)

zx0, zy0, zx1, zy1 = LOGO_ZONE
yy, xx = np.mgrid[0:H, 0:W]
STATIC_KILL = ((xx >= zx0) & (xx < zx1) & (yy >= zy0) & (yy < zy1)
               & (yy < 262 + np.clip(xx - 1150, 0, None) * 0.6))

tops, xs, ws, dropped = [], [], [], 0
frame_bytes = W * H * 4
while True:
    buf = dec.stdout.read(frame_bytes)
    if len(buf) < frame_bytes:
        break
    f = np.frombuffer(buf, np.uint8).reshape(H, W, 4).copy()
    # The sign is static: clear the zone above her head line (head top never
    # rises above y≈265; the sign's diagonal tail slopes down to the right).
    f[..., 3][STATIC_KILL] = 0
    # Where the sign touches her hair, drop only neon pixels (magenta / near-white);
    # her hair is dark brown so it survives.
    band = f[zy0:320, zx0:zx1]
    r, g, b = (band[..., k].astype(np.int16) for k in range(3))
    neon = ((r > 120) & (b > 120) & (g < r - 30)) | ((r + g + b) > 540)
    neon = ndimage.binary_dilation(neon, iterations=3)
    band[..., 3][neon] = 0
    small = f[::DS, ::DS, 3] > 40
    lab, n = ndimage.label(small, structure=np.ones((3, 3)))
    keep = np.ones_like(small)
    for i, sl in enumerate(ndimage.find_objects(lab), start=1):
        y0, y1 = sl[0].start * DS, sl[0].stop * DS
        x0, x1 = sl[1].start * DS, sl[1].stop * DS
        lx0, ly0, lx1, ly1 = LOGO_ZONE
        if x0 >= lx0 and x1 <= lx1 and y0 >= ly0 and y1 <= ly1:
            keep[lab == i] = False
            dropped += 1
    keep = ndimage.binary_dilation(~keep, iterations=2)  # grow the dropped area a little
    kill = np.repeat(np.repeat(keep, DS, 0), DS, 1)[:H, :W]
    f[..., 3][kill] = 0
    enc.stdin.write(f.tobytes())

    m = f[::DS, ::DS, 3] > 128
    top = np.where(m.any(1))[0][0]
    band = m[top: top + 48 // DS]      # just the crown, so raised hands never enter it
    cols = np.where(band.any(0))[0]
    tops.append(top * DS)
    xs.append((cols.min() + cols.max()) / 2 * DS)
    ws.append((cols.max() - cols.min()) * DS * 1.4)   # crown → full head width

enc.stdin.close()
enc.wait()
dec.wait()


def smooth(v, k=4):
    v = np.array(v, float)
    return np.convolve(np.pad(v, k, mode="edge"), np.ones(2 * k + 1) / (2 * k + 1), "valid")


ws = np.clip(ws, 200, 300)            # a head is ~260 px wide in this framing
json.dump({"fps": FPS, "start": SEG_START,
           "top": [round(x, 1) for x in smooth(tops)],
           "x": [round(x, 1) for x in smooth(xs)],
           "w": [round(x, 1) for x in smooth(ws)]}, open("fx/head-track.json", "w"))
print(f"{len(tops)} frames, dropped {dropped} logo blobs, head top {min(tops)}–{max(tops)}, "
      f"x {min(xs):.0f}–{max(xs):.0f}")
