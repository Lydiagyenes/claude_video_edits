#!/usr/bin/env python3
"""Fast presenter matte for a plain-wall recording.

1. u2net_human_seg (the model `hyperframes remove-background` uses) runs on every
   STEP-th frame at 320x320 → coarse masks, linearly blended in between.
2. A smooth wall plate is fitted per keyframe (2-D quadratic per channel over pixels
   the coarse mask calls background) — the wall is a plain, evenly lit surface.
3. Per frame at full resolution: inside the eroded coarse mask → opaque; outside the
   dilated mask → transparent; in the band between → colour-difference key against
   the plate, softened. This keeps hair / hands sharp without per-frame inference.

Writes work/matte.webm (VP9 + alpha, the colour channels are the source frame).
Usage: python3 matte.py src/source30.mov work/matte.webm [STEP]
"""
import subprocess
import sys

import numpy as np
import onnxruntime as ort
from scipy import ndimage

SRC, OUT = sys.argv[1], sys.argv[2]
STEP = int(sys.argv[3]) if len(sys.argv) > 3 else 6
W, H = 1920, 1080
MODEL = "/root/.cache/hyperframes/background-removal/models/u2net_human_seg.onnx"

probe = subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v:0", "-show_entries",
                        "stream=nb_read_packets", "-of", "csv=p=0", SRC], capture_output=True, text=True)
NFR = int(probe.stdout.strip())

so = ort.SessionOptions()
so.intra_op_num_threads = int(__import__("os").environ.get("ORT_THREADS", "1"))
sess = ort.InferenceSession(MODEL, so, providers=["CPUExecutionProvider"])
INP = sess.get_inputs()[0].name
MEAN = np.array([0.485, 0.456, 0.406], np.float32)[:, None, None]
STD = np.array([0.229, 0.224, 0.225], np.float32)[:, None, None]


def coarse(frame320):
    x = frame320.astype(np.float32).transpose(2, 0, 1) / 255.0
    x = ((x / max(x.max(), 1e-6)) - MEAN) / STD
    d = sess.run(None, {INP: x[None]})[0][0, 0]
    d = (d - d.min()) / max(d.max() - d.min(), 1e-6)
    return d  # 320x320, 0..1


# ── pass 1: coarse masks on keyframes (decoded at 320x320) ──
small = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-vf",
                          f"select='not(mod(n\\,{STEP}))',scale=320:320:flags=area",
                          "-vsync", "0", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
keys = []
while True:
    b = small.stdout.read(320 * 320 * 3)
    if len(b) < 320 * 320 * 3:
        break
    keys.append(coarse(np.frombuffer(b, np.uint8).reshape(320, 320, 3)))
    if len(keys) % 50 == 0:
        print(f"coarse {len(keys)}/{NFR // STEP + 1}", flush=True)
small.wait()
keys = np.array(keys, np.float32)
print("coarse done", keys.shape, flush=True)

# ── wall plate: quadratic surface per channel, fitted on a downscaled keyframe ──
DS = 8
yy, xx = np.mgrid[0:H // DS, 0:W // DS].astype(np.float32)
xn, yn = xx / (W // DS), yy / (H // DS)
BASIS = np.stack([np.ones_like(xn), xn, yn, xn * xn, yn * yn, xn * yn], -1).reshape(-1, 6)
FULL_Y, FULL_X = np.mgrid[0:H, 0:W].astype(np.float32)
FXN, FYN = FULL_X / W, FULL_Y / H
FULL_BASIS = [np.ones_like(FXN), FXN, FYN, FXN * FXN, FYN * FYN, FXN * FYN]


def fit_plate(frame, mask_small):
    f = frame[::DS, ::DS].astype(np.float32).reshape(-1, 3)
    m = (ndimage.zoom(mask_small, ((H // DS) / 320, (W // DS) / 320), order=1) < 0.05).reshape(-1)
    coef, *_ = np.linalg.lstsq(BASIS[m], f[m], rcond=None)
    return sum(FULL_BASIS[k][..., None] * coef[k] for k in range(6))  # H×W×3


# ── pass 2: full-res refinement + encode (OpenCV for speed) ──
import cv2

KER = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                       stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
                        "-r", "30", "-i", "-", "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0",
                        "-crf", "22", "-deadline", "realtime", "-cpu-used", "8", "-row-mt", "1", "-g", "30", OUT],
                       stdin=subprocess.PIPE)
plate, plate_key = None, -1
out = np.empty((H, W, 4), np.uint8)
for i in range(NFR):
    b = dec.stdout.read(W * H * 3)
    if len(b) < W * H * 3:
        break
    frame = np.frombuffer(b, np.uint8).reshape(H, W, 3)
    k, r = divmod(i, STEP)
    k0, k1 = min(k, len(keys) - 1), min(k + 1, len(keys) - 1)
    m320 = keys[k0] * (1 - r / STEP) + keys[k1] * (r / STEP)
    if k % 10 == 0 and k != plate_key:  # refresh the plate every ~2 s
        plate, plate_key = fit_plate(frame, keys[k0]).astype(np.float32), k
    # band logic at half resolution
    hw, hh = W // 2, H // 2
    m = (cv2.resize(m320, (hw, hh), interpolation=cv2.INTER_LINEAR) > 0.5).astype(np.uint8)
    inner = cv2.erode(m, KER, iterations=3)
    outer = cv2.dilate(m, KER, iterations=6)
    fh = cv2.resize(frame, (hw, hh), interpolation=cv2.INTER_AREA).astype(np.float32)
    ph = plate[::2, ::2]
    diff = np.abs(fh - ph).sum(-1)
    key = np.clip((diff - 30.0) / 30.0, 0, 1)  # 30 → wall, 60 → subject
    a = np.where(inner > 0, 1.0, np.where(outer > 0, key, 0.0)).astype(np.float32)
    a = cv2.GaussianBlur(a, (0, 0), 0.9)
    a = cv2.resize(a, (W, H), interpolation=cv2.INTER_LINEAR)
    a = np.clip(a, 0, 1) ** 1.3  # pull the edge in slightly
    # de-spill: remove the wall colour mixed into soft edge pixels
    soft = (a > 0.02) & (a < 0.98)
    rgb = frame.astype(np.float32)
    aa = a[soft][:, None]
    rgb[soft] = np.clip((rgb[soft] - (1 - aa) * plate[soft]) / np.maximum(aa, 0.25), 0, 255)
    out[..., :3] = rgb.astype(np.uint8)
    out[..., 3] = (a * 255).astype(np.uint8)
    enc.stdin.write(out.tobytes())
    if i % 300 == 0:
        print(f"frame {i}/{NFR}", flush=True)
enc.stdin.close()
enc.wait()
dec.wait()
print("done", flush=True)
