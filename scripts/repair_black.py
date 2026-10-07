#!/usr/bin/env python3
"""Find isolated black/near-black frames (render glitches) and replace each with the previous frame. Audio is copied.

Usage: python3 repair_black.py film.mp4      (in place; re-encodes video once, CRF 14)

HyperFrames renders with data-color-grading occasionally drop a single black frame right after a cut, always at
the same places for the same composition. A frame is a glitch when its mean luma is < 12 while the frames around
it are > 30 — real fades to black are longer and are left alone. Re-scans after repair and prints the result.
"""
import sys, re, subprocess, os, shutil
F=sys.argv[1]; tmp=F+'.yavg.txt'
def scan():
    subprocess.run(['ffmpeg','-v','error','-i',F,'-vf',f'scale=96:54,format=gray,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file={tmp}','-f','null','-'],check=True)
    v=[float(x) for x in re.findall(r'YAVG=([\d.]+)',open(tmp).read())]
    bad=[]
    for i in range(1,len(v)-2):
        nb=min(v[i-1],max(v[i+1],v[i+2]))
        if v[i]<12 and nb>30: bad.append(i)
    return v,bad
v,bad=scan(); print('frames',len(v),'glitches',bad)
if not bad: sys.exit(0)
# group consecutive frames
chains=[]
for i in bad:
    if chains and i==chains[-1][1]+1: chains[-1][1]=i
    else: chains.append([i,i])
parts=[]; cur='0:v'
for k,(a,b) in enumerate(chains):
    parts.append(f'[{cur}]split[s{k}][r{k}];[s{k}][r{k}]freezeframes=first={a}:last={b}:replace={a-1}[v{k}]'); cur=f'v{k}'
fc=';'.join(parts)
out=F+'.fix.mp4'
subprocess.run(['ffmpeg','-v','error','-y','-i',F,'-filter_complex',fc,'-map',f'[{cur}]','-map','0:a','-c:v','libx264','-preset','medium','-crf','14','-pix_fmt','yuv420p',
                '-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-color_range','tv','-c:a','copy','-movflags','+faststart',out],check=True)
os.replace(out,F); v2,bad2=scan(); print('after repair glitches',bad2); os.remove(tmp)
