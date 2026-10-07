#!/usr/bin/env python3
"""Conform one already-rectilinear shot (GoPro Linear mode, phone footage already SDR): optional rotate/zoom/shift
(horizon or hood levelling), slow push-in, constant speed (0.5 = 2x slow motion from 60p), 3840x2160 30p H.264.

Usage:
  python3 conform_linear.py --src GX010171.MP4 --start 100 --dur 0.6 --out shot.mp4 [--rot -1.4 --zoom 1.07 --dy 0.01]
     [--speed 0.5] [--push 1.06]
Give every shot head/tail handles (render 0.5 s before and 0.3 s after the used range) — HyperFrames then seeks
inside the clip instead of at frame 0, which avoids black first frames at cuts.
Refuses clips with a display-matrix rotation (convert phone video with avconvert first).
"""
import argparse, subprocess, json, math, sys
ap=argparse.ArgumentParser()
ap.add_argument('--src',required=True); ap.add_argument('--start',type=float,required=True); ap.add_argument('--dur',type=float,required=True)
ap.add_argument('--speed',type=float,default=1.0); ap.add_argument('--rot',type=float,default=0.0); ap.add_argument('--zoom',type=float,default=1.0)
ap.add_argument('--push',type=float,default=1.0,help='end zoom of slow push-in'); ap.add_argument('--dx',type=float,default=0.0,help='horizontal shift as fraction of width'); ap.add_argument('--dy',type=float,default=0.0,help='vertical shift as fraction of width units (frame height = 9/16)'); ap.add_argument('--out',required=True)
A=ap.parse_args()
pr=json.loads(subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=r_frame_rate:stream_side_data=rotation','-of','json',A.src],capture_output=True,text=True).stdout)['streams'][0]
if any('rotation' in sd and sd['rotation'] for sd in pr.get('side_data_list',[])): sys.exit(f'{A.src}: rotated clip not supported')
num,den=map(int,pr['r_frame_rate'].split('/')); fps=num/den
W,H=3840,2160; z=A.zoom
vf=[]
if A.speed!=1.0: vf.append(f'setpts=PTS/{A.speed}')
vf.append('fps=30')
if z!=1.0 or A.rot or A.dy or A.dx:
    zw,zh=int(round(W*z/2)*2),int(round(H*z/2)*2)
    vf.append(f'scale={zw}:{zh}:flags=lanczos')
    if A.rot: vf.append(f'rotate={math.radians(A.rot):.6f}:ow={zw}:oh={zh}:c=black')
    oy=(zh-H)/2+A.dy*W*z
    oy=max(0,min(zh-H,oy))
    ox=(zw-W)/2+A.dx*W*z; ox=max(0,min(zw-W,ox))
    vf.append(f'crop={W}:{H}:{int(round(ox))}:{int(round(oy))}')
if A.push!=1.0:
    N=int(round(A.dur*30)); vf.append(f"scale=w='2*trunc({W}*(1+{A.push-1:.4f}*n/{N})/2)':h=-2:eval=frame:flags=lanczos,crop={W}:{H}")
vf.append('format=yuv420p')
n=int(round(A.dur*30))
cmd=['ffmpeg','-v','error','-y','-ss',f'{A.start:.3f}','-t',f'{A.dur*A.speed+0.2:.3f}','-i',A.src,'-an','-vf',','.join(vf),
     '-frames:v',str(n),'-c:v','libx264','-preset','medium','-crf','15','-g','15','-keyint_min','15',
     '-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-color_range','tv','-movflags','+faststart',A.out]
r=subprocess.run(cmd,capture_output=True,text=True)
c=subprocess.run(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames','-of','default=nw=1:nk=1',A.out],capture_output=True,text=True).stdout.split()[0]
print(f'{A.out}: {c} frames' + ('' if c==str(n) else f' (WANTED {n}) '+r.stderr[-300:]))
