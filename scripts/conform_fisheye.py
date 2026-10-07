#!/usr/bin/env python3
"""Conform one GoPro Wide/SuperView shot: fisheye -> rectilinear from the clip's own GPMF lens model,
optional align (dx, dy, rot, zoom) for match cuts, constant speed (0.5 = 2x slow motion from 60p), 3840x2160 30p H.264.

Usage:
  python3 conform_fisheye.py --src GX010357.MP4 --start 1 --dur 5 --out shot.mp4 [--a 1.0] [--speed 0.5]
     [--zoom 1.18 --dx 0.002 --dy -0.001 --rot -0.4] [--audio]
--a 1.0 = full rectilinear (like GoPro Linear), 0.6 = partial (keeps some width), 0 = untouched.
Do not use this on clips shot in Linear mode (VFOV 'L') — they are already rectilinear; use conform_linear.py.
Frames go through numpy/OpenCV in 16-bit RGB so 10-bit HEVC keeps its gradation.
"""
import argparse, subprocess, sys, os, numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lensmodel
from lensmodel import maps
ap=argparse.ArgumentParser()
ap.add_argument('--src',required=True); ap.add_argument('--start',type=float,required=True); ap.add_argument('--dur',type=float,required=True,help='OUTPUT seconds')
ap.add_argument('--speed',type=float,default=1.0,help='1.0 normal, 0.5 = 2x slow motion (uses all 60p frames)')
ap.add_argument('--a',type=float,default=1.0,help='lens correction strength (1=rectilinear, 0=none)')
ap.add_argument('--zoom',type=float,default=1.0); ap.add_argument('--dx',type=float,default=0); ap.add_argument('--dy',type=float,default=0); ap.add_argument('--rot',type=float,default=0,help='degrees')
ap.add_argument('--out',required=True); ap.add_argument('--audio',action='store_true'); ap.add_argument('--crf',type=int,default=14)
ap.add_argument('--w',type=int,default=3840); ap.add_argument('--h',type=int,default=2160)
A=ap.parse_args()
_mode=lensmodel.load_from_clip(A.src)
if _mode=='L' and A.a>0: print('note: clip is Linear mode; lens correction is not needed', file=sys.stderr)
W,H=3840,2160; OW,OH=A.w,A.h
src_dur=A.dur*A.speed
_rot=subprocess.run(['ffprobe','-v','error','-show_entries','stream_side_data=rotation','-of','csv=p=0',A.src],capture_output=True,text=True).stdout.strip()
if _rot and _rot not in ('0',''):
    sys.exit(f'{A.src}: display_matrix rotation {_rot} not supported')
if A.a<=0 and A.zoom==1 and not (A.dx or A.dy or A.rot):
    mx=my=None
else:
    sx,sy=maps(max(A.a,1e-7),W,H,extra=A.zoom,dx=A.dx,dy=A.dy,rot=np.radians(A.rot))
    if (OW,OH)!=(W,H):
        sx=cv2.resize(sx,(OW,OH),interpolation=cv2.INTER_LINEAR); sy=cv2.resize(sy,(OW,OH),interpolation=cv2.INTER_LINEAR)
    mx,my=cv2.convertMaps(sx.astype(np.float32),sy.astype(np.float32),cv2.CV_16SC2)
# 60p source: normal speed keeps every 2nd frame (30p); slow motion 0.5 keeps all frames played at 30p
_num,_den=map(int,subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=r_frame_rate','-of','csv=p=0',A.src],capture_output=True,text=True).stdout.strip().split('/'))
_ratio=(_num/_den)*A.speed/30.0   # source frames per output frame
if abs(_ratio-round(_ratio))<0.02 and round(_ratio)>=1:
    step=int(round(_ratio)); vf=f"select='not(mod(n\\,{step}))'," if step>1 else ""
else:
    vf=f"setpts=PTS/{A.speed},fps=30,"   # non-integer ratio: resample time
vf+="scale=in_color_matrix=bt709:in_range=tv,format=rgb48le"
dec=subprocess.Popen(['ffmpeg','-v','error','-ss',f'{A.start:.3f}','-t',f'{src_dur+0.05:.3f}','-i',A.src,'-an','-vf',vf,'-fps_mode','passthrough','-f','rawvideo','-pix_fmt','rgb48le','-'],stdout=subprocess.PIPE)
enc_cmd=['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb48le','-s',f'{OW}x{OH}','-r','30','-i','-']
if A.audio:
    enc_cmd+=['-ss',f'{A.start:.3f}','-t',f'{src_dur:.3f}','-i',A.src,'-map','0:v','-map','1:a']
    if A.speed!=1: enc_cmd+=['-af',f'atempo={A.speed}']
    enc_cmd+=['-c:a','aac','-b:a','256k']
enc_cmd+=['-vf','scale=out_color_matrix=bt709:out_range=tv:flags=lanczos,format=yuv420p','-c:v','libx264','-preset','medium','-crf',str(A.crf),
          '-g','15','-keyint_min','15','-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-color_range','tv',
          '-frames:v',str(int(round(A.dur*30))),'-movflags','+faststart',A.out]
enc=subprocess.Popen(enc_cmd,stdin=subprocess.PIPE)
fb=W*H*6; n=0; need=int(round(A.dur*30))
while n<need:
    buf=dec.stdout.read(fb)
    if len(buf)<fb: break
    fr=np.frombuffer(buf,np.uint16).reshape(H,W,3)
    out=cv2.remap(fr,mx,my,cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE) if mx is not None else (fr if (OW,OH)==(W,H) else cv2.resize(fr,(OW,OH),interpolation=cv2.INTER_AREA))
    enc.stdin.write(out.tobytes()); n+=1
enc.stdin.close(); enc.wait(); dec.stdout.close(); dec.kill()
print(f'{A.out}: {n} frames' + ('' if n==need else f' (WANTED {need})'))
