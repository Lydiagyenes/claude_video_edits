#!/usr/bin/env bash
# Studio relight of the presenter cut-out: cooler WB, face-centred key (vignette
# falloff), lilac-tinted shadows, lilac rim light along the silhouette, edge choke.
# usage: relight.sh <matte.webm> <out.webm|out.png> [extra ffmpeg input args]
set -euo pipefail
IN=$1; OUT=$2; shift 2
FC="[0]format=rgba,split=3[c][x][y];
[x]alphaextract,erosion,erosion,erosion,gblur=sigma=1.2,split[al][al2];
[al2]erosion,erosion,erosion,erosion,erosion,erosion,erosion,erosion[in];
[y]alphaextract,erosion,erosion,erosion[o];
[o][in]blend=all_mode=subtract,gblur=sigma=11,colorlevels=romax=0.75:gomax=0.75:bomax=0.75[rimA];
[c]colortemperature=temperature=5200:mix=0.85,
  eq=contrast=1.10:brightness=0.005:saturation=1.03:gamma=1.03,
  vignette=angle=0.5:x0=w*0.5:y0=h*0.28:mode=forward,
  colorbalance=rs=0.02:gs=-0.04:bs=0.10:rm=0.01:gm=-0.015:bm=0.05,format=rgba[cg];
color=c=0xB49BFF:s=1920x1080:r=30,format=rgba[lil];
[lil][rimA]alphamerge[rim];
[cg][rim]overlay=format=auto:shortest=1[lit];
[lit][al]alphamerge,format=yuva420p"
ffmpeg -v error -y -c:v libvpx-vp9 "$@" -i "$IN" -filter_complex "$FC" \
  $( [[ $OUT == *.png ]] && echo "-frames:v 1" || echo "-c:v libvpx-vp9 -pix_fmt yuva420p -b:v 0 -crf 24 -deadline realtime -cpu-used 8 -row-mt 1 -g 30 -an" ) "$OUT"
