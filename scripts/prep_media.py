#!/usr/bin/env python3
"""Prepare phone photos/videos and film scans for HyperFrames: upright, SDR, sensible size.

Usage:
  python3 prep_media.py --out film/assets/media  photo:IMG_7131.HEIC  video:IMG_7290.MOV  live:IMG_7057.MP4  scan:roll2-07.JPG ...
  (paths may be absolute or relative to --src)

- photo: HEIC/JPG -> JPG, EXIF orientation applied (exif_transpose), longest side 3200 px  -> p<stem>.jpg
- video: iPhone HDR (HLG / Dolby Vision) MOV -> SDR H.264 1080p via macOS `avconvert` (Apple's own tone map,
         also bakes in the display-matrix rotation)                                      -> v<stem>.mp4
- live:  the MP4 companion of a Live Photo, same conversion                              -> l<stem>.mp4
- scan:  film scan JPG, EXIF orientation applied (vertical frames otherwise appear sideways) -> a<stem>.jpg
Writes media_meta.json next to the outputs (w, h, duration) for layout decisions (portrait vs landscape).
"""
import argparse, json, os, subprocess
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageOps

ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True); ap.add_argument('--src', default='.')
ap.add_argument('items', nargs='+'); A = ap.parse_args()
os.makedirs(A.out, exist_ok=True)

def path(p): return p if os.path.isabs(p) else os.path.join(os.path.expanduser(A.src), p)
def stem(p): return os.path.splitext(os.path.basename(p))[0].replace('IMG_', '')

def photo(p):
    o = f'{A.out}/p{stem(p)}.jpg'
    if os.path.exists(o): return
    src = path(p)
    if src.lower().endswith('.heic'):
        tmp = o + '.tmp.jpg'; subprocess.run(['sips', '-s', 'format', 'jpeg', '-s', 'formatOptions', '92', src, '--out', tmp], capture_output=True); src_im = Image.open(tmp)
    else:
        tmp = None; src_im = Image.open(src)
    im = ImageOps.exif_transpose(src_im).convert('RGB'); im.thumbnail((3200, 3200), Image.LANCZOS); im.save(o, quality=90)
    if tmp: os.remove(tmp)

def video(p, prefix='v'):
    o = f'{A.out}/{prefix}{stem(p)}.mp4'
    if not os.path.exists(o):
        subprocess.run(['avconvert', '-s', path(p), '-p', 'Preset1920x1080', '-o', o, '--replace'], capture_output=True)

def scan(p):
    o = f'{A.out}/a{stem(p).split("-", 1)[-1] if "-" in stem(p) else stem(p)}.jpg'
    if os.path.exists(o): return
    im = ImageOps.exif_transpose(Image.open(path(p))).convert('RGB'); im.thumbnail((3000, 3000), Image.LANCZOS); im.save(o, quality=92)

jobs = [it.split(':', 1) for it in A.items]
with ThreadPoolExecutor(6) as ex:
    list(ex.map(lambda j: photo(j[1]) if j[0] == 'photo' else scan(j[1]) if j[0] == 'scan' else None, jobs))
with ThreadPoolExecutor(3) as ex:
    list(ex.map(lambda j: video(j[1], 'v') if j[0] == 'video' else video(j[1], 'l') if j[0] == 'live' else None, jobs))
meta = {}
for f in sorted(os.listdir(A.out)):
    p = f'{A.out}/{f}'
    if f.endswith('.jpg'): w, h = Image.open(p).size; meta[f] = dict(w=w, h=h)
    elif f.endswith('.mp4'):
        j = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height:format=duration', '-of', 'json', p], capture_output=True, text=True).stdout)
        s = j['streams'][0]; meta[f] = dict(w=s['width'], h=s['height'], dur=float(j['format']['duration']))
json.dump(meta, open(f'{A.out}/media_meta.json', 'w'), indent=1); print('media', len(meta))
