#!/usr/bin/env python3
"""Cut the source recording into public/input-video.mp4 and refresh metadata.json.

Times in EDIT_CUTS and everywhere in build_composition.py are on the *uncut*
timeline: the original .mov minus its first TRIM seconds (sitting down). The
transcript (transcript.json / audio.mp3) stays on that timeline too; the build
maps every time through remap() from edit.py.
Run:  python3 cut_source.py /path/to/original.mov
"""
import json
import subprocess
import sys
from pathlib import Path

from edit import EDIT_CUTS, TRIM, kept_segments

ROOT = Path(__file__).resolve().parent
src = sys.argv[1]
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src],
                           capture_output=True, text=True).stdout) - TRIM
segs = kept_segments(dur)

FADE = 0.02  # tiny audio fades at each join so the cuts don't click
parts, labels = [], []
for i, (a, b) in enumerate(segs):
    a0, b0 = a + TRIM, b + TRIM
    parts.append(f"[0:v]trim={a0}:{b0},setpts=PTS-STARTPTS,fps=30[v{i}]")
    parts.append(f"[0:a]atrim={a0}:{b0},asetpts=PTS-STARTPTS,"
                 f"afade=t=in:d={FADE},afade=t=out:st={b - a - FADE}:d={FADE}[a{i}]")
    labels.append(f"[v{i}][a{i}]")
parts.append(f"{''.join(labels)}concat=n={len(segs)}:v=1:a=1[v][a]")

out = ROOT / "public" / "input-video.mp4"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", ";".join(parts),
                "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "18", "-g", "30", "-keyint_min", "30",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)],
               check=True)
meta = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                       "stream=width,height,r_frame_rate", "-show_entries", "format=duration", "-of", "json",
                       str(out)], capture_output=True, text=True, check=True).stdout
(ROOT / "metadata.json").write_text(meta)
print(f"kept {segs} → {json.loads(meta)['format']['duration']}s")
