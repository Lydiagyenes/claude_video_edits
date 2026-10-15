#!/usr/bin/env python3
"""Build public/mix.wav: cleaned voice cut to the EDL + looped music bed.

Voice: work/voice_clean.wav (RNNoise 'sh' de-birding, light FFT denoise, compression,
-16 LUFS). Music: src/music.mp3 looped with 2 s crossfades, a quiet bed under speech
(~-17 dB), full level through the show intro, faded out at the end.
"""
import subprocess

from edit import INTRO_DUR, intro_window, timeline, total

T = total()
I0, I1 = intro_window()

# ── voice: kept segments with 15 ms fades + silence where the intro plays ──
parts, labels = [], []
for n, (kind, o0, o1, s0) in enumerate(timeline()):
    d = o1 - o0
    if kind == "intro":
        parts.append(f"anullsrc=r=48000:cl=mono,atrim=0:{INTRO_DUR}[v{n}]")
    else:
        parts.append(f"[0:a]atrim={s0}:{s0 + d},asetpts=PTS-STARTPTS,"
                     f"afade=t=in:d=0.015,afade=t=out:st={d - 0.015}:d=0.015[v{n}]")
    labels.append(f"[v{n}]")
parts.append(f"{''.join(labels)}concat=n={len(labels)}:v=0:a=1,aformat=channel_layouts=stereo[voice]")

# ── music: 4× loop with crossfades, then level automation ──
LOW, HIGH = 0.14, 1.0
ramp_in, ramp_out = 0.6, 1.4
vol = (f"{LOW}+({HIGH}-{LOW})*clip((t-({I0}-{ramp_in}))/{ramp_in},0,1)*clip((({I1}+{ramp_out})-t)/{ramp_out},0,1)")
fade = f"clip(t/1.5,0,1)*clip(({T}-t)/3,0,1)"
parts.append("[1:a]asplit=4[m0][m1][m2][m3]")
parts.append("[m0][m1]acrossfade=d=2:c1=tri:c2=tri[x1];[x1][m2]acrossfade=d=2:c1=tri:c2=tri[x2];"
             "[x2][m3]acrossfade=d=2:c1=tri:c2=tri[mus]")
parts.append(f"[mus]atrim=0:{T},asetpts=PTS-STARTPTS,aresample=48000,volume='({vol})*({fade})':eval=frame[bed]")
parts.append("[voice][bed]amix=inputs=2:duration=first:normalize=0,volume=1.42,alimiter=limit=0.89:level=false[out]")

subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "work/voice_clean.wav", "-i", "src/music.mp3",
                "-filter_complex", ";".join(parts), "-map", "[out]", "-ar", "48000", "-ac", "2",
                "-c:a", "pcm_s16le", "public/mix.wav"], check=True)
print(f"mix {T:.2f}s, intro {I0:.2f}–{I1:.2f}")
