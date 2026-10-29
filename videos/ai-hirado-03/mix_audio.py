#!/usr/bin/env python3
"""Build public/mix.wav: the recording's voice (loudness-normalised, silence where the
intro plays) + src/music.mp3 looped under the whole show — a quiet bed under speech,
full level through the intro, faded in/out at the ends (same levels as híradó #01)."""
import subprocess

from edit import CUT, INTRO, INTRO_DUR, TOTAL

T = round(TOTAL, 3)
I0, I1 = INTRO
LOW, HIGH = 0.14, 1.0
ramp_in, ramp_out = 0.6, 1.4
vol = f"{LOW}+({HIGH}-{LOW})*clip((t-({I0}-{ramp_in}))/{ramp_in},0,1)*clip((({I1}+{ramp_out})-t)/{ramp_out},0,1)"
fade = f"clip(t/1.5,0,1)*clip(({T}-t)/3,0,1)"

parts = [
    "[0:a]aformat=sample_rates=48000:channel_layouts=mono,highpass=f=70,"
    "loudnorm=I=-16:TP=-1.5:LRA=9,aresample=48000,asplit=2[va][vb]",
    f"[va]atrim=0:{CUT},asetpts=PTS-STARTPTS,afade=t=out:st={CUT - 0.03}:d=0.03[v0]",
    f"anullsrc=r=48000:cl=mono,atrim=0:{INTRO_DUR}[v1]",
    f"[vb]atrim={CUT},asetpts=PTS-STARTPTS,afade=t=in:d=0.03[v2]",
    "[v0][v1][v2]concat=n=3:v=0:a=1,aformat=channel_layouts=stereo[voice]",
    "[1:a]aresample=48000,asplit=3[m0][m1][m2]",
    "[m0][m1]acrossfade=d=2:c1=tri:c2=tri[x1];[x1][m2]acrossfade=d=2:c1=tri:c2=tri[mus]",
    f"[mus]atrim=0:{T},asetpts=PTS-STARTPTS,volume='({vol})*({fade})':eval=frame[bed]",
    "[voice][bed]amix=inputs=2:duration=longest:normalize=0,volume=1.42,alimiter=limit=0.89:level=false,apad,"
    f"atrim=0:{T}[out]",
]
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "src/source.mp4", "-i", "src/music.mp3",
                "-filter_complex", ";".join(parts), "-map", "[out]", "-ar", "48000", "-ac", "2",
                "-c:a", "pcm_s16le", "public/mix.wav"], check=True)
print(f"mix {T}s, intro {I0:.2f}–{I1:.2f}")
