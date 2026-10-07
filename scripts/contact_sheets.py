#!/usr/bin/env python3
"""Contact sheets for reviewing a trip without opening a single video.

Usage:
  python3 contact_sheets.py --inventory work/inventory.json --out work/review
    [--per-clip-every 2.5] [--max-frames 16]

Writes:
  review/frames/            sampled frames (from GoPro LRV proxies when present, else the source)
  review/clips_NN.jpg       one row per video: clip id, capture time, duration, frames with timestamps
  review/day_YYYY-MM-DD_N.jpg  photos and vertical videos of one day in capture order (videos tagged V)

Why: a 4K source decode per frame is slow; LRV proxies and HEIC thumbnails make a whole trip reviewable in
minutes. Read the sheets yourself — metrics (sharpness, brightness) only flag candidates, they do not judge.
"""
import argparse, json, math, os, subprocess
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from PIL import Image, ImageDraw, ImageFont, ImageOps

ap = argparse.ArgumentParser()
ap.add_argument('--inventory', required=True); ap.add_argument('--out', required=True)
ap.add_argument('--per-clip-every', type=float, default=2.5); ap.add_argument('--max-frames', type=int, default=16)
A = ap.parse_args()
R = json.load(open(A.inventory)); O = A.out; os.makedirs(f'{O}/frames', exist_ok=True)
try: FONT = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 16); SF = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 13)
except OSError: FONT = SF = ImageFont.load_default()

vids = [r for r in R if r['ext'] in ('mp4', 'mov') and not r.get('live_photo_of')]
jobs = []
for r in vids:
    d = r.get('duration') or 0
    k = max(4, min(A.max_frames, math.ceil(d / A.per_clip_every)))
    for i in range(k): jobs.append((r, i, d * (i + 0.5) / k))
def grab(j):
    r, i, ts = j; key = os.path.splitext(r['file'])[0]; o = f'{O}/frames/{key}_{i:02d}_{ts:07.2f}.jpg'
    if not os.path.exists(o):
        src = r.get('proxy') or r['path']
        subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{ts:.3f}', '-i', src, '-frames:v', '1', '-vf', 'scale=384:-2', '-q:v', '4', o])
    return o
with ThreadPoolExecutor(6) as ex: list(ex.map(grab, jobs))

# clip sheets
W, H, COLS, LW = 192, 108, 12, 110
rows = []
for r in sorted(vids, key=lambda r: (r.get('dt') or '', r['file'])):
    key = os.path.splitext(r['file'])[0]
    fr = sorted(f for f in os.listdir(f'{O}/frames') if f.startswith(key + '_'))
    if not fr: continue
    nr = (len(fr) + COLS - 1) // COLS; row = Image.new('RGB', (COLS * W + LW, nr * (H + 2)), (30, 30, 30)); d = ImageDraw.Draw(row)
    d.text((4, 4), key[-8:], fill='yellow', font=FONT); d.text((4, 26), (r.get('dt') or '')[5:16], fill='white', font=SF)
    d.text((4, 44), f"{r.get('duration', 0):.0f}s", fill='white', font=SF)
    if r.get('rotation'): d.text((4, 62), f"rot {r['rotation']}", fill='red', font=SF)
    for k, f in enumerate(fr):
        im = Image.open(f'{O}/frames/{f}'); im.thumbnail((W, H)); x = LW + (k % COLS) * W; y = (k // COLS) * (H + 2)
        row.paste(im, (x, y)); d.text((x + 2, y + 1), f.rsplit('_', 1)[1][:-4].lstrip('0') or '0', fill='white', font=SF, stroke_width=2, stroke_fill='black')
    rows.append(row)
sheet, used, idx = [], 0, 0
def flush():
    global sheet, idx
    if not sheet: return
    im = Image.new('RGB', (COLS * W + LW, sum(r.height for r in sheet)), 'black'); y = 0
    for r in sheet: im.paste(r, (0, y)); y += r.height
    im.save(f'{O}/clips_{idx:02d}.jpg', quality=80); idx += 1; sheet = []
for row in rows:
    n = row.height // (H + 2)
    if used + n > 14: flush(); used = 0
    sheet.append(row); used += n
flush()

# per-day photo sheets (photos + vertical/phone videos)
by = defaultdict(list)
for r in R:
    if r.get('live_photo_of') or r['source'] == 'gopro' or not r.get('dt'): continue
    by[r['dt'][:10]].append(r)
CW = CH = 200; DC = 14
def thumb(r):
    if r['ext'] in ('mp4', 'mov'):
        o = f"{O}/frames/{os.path.splitext(r['file'])[0]}_00_{(r.get('duration') or 0) / 2:07.2f}.jpg"
        cand = sorted(f for f in os.listdir(f'{O}/frames') if f.startswith(os.path.splitext(r['file'])[0] + '_'))
        return Image.open(f"{O}/frames/{cand[len(cand) // 2]}") if cand else None
    try:
        if r['ext'] == 'heic':
            tmp = f"{O}/frames/{r['file']}.jpg"
            if not os.path.exists(tmp): subprocess.run(['sips', '-s', 'format', 'jpeg', '-Z', '400', r['path'], '--out', tmp], capture_output=True)
            return ImageOps.exif_transpose(Image.open(tmp))
        im = ImageOps.exif_transpose(Image.open(r['path'])); im.thumbnail((400, 400)); return im
    except Exception: return None
for day, L in sorted(by.items()):
    L.sort(key=lambda r: r['dt']); tiles = []
    for r in L:
        im = thumb(r)
        if im is None: continue
        im = im.convert('RGB'); im.thumbnail((CW, CH)); c = Image.new('RGB', (CW, CH), (25, 25, 25)); c.paste(im, ((CW - im.width) // 2, (CH - im.height) // 2))
        d = ImageDraw.Draw(c); lab = f"{os.path.splitext(r['file'])[0][-4:]} {r['dt'][11:16]}" + (' V' if r['ext'] in ('mp4', 'mov') else '')
        d.text((3, 2), lab, fill='cyan' if lab.endswith('V') else 'white', font=SF, stroke_width=2, stroke_fill='black'); tiles.append(c)
    for k in range(0, len(tiles), DC * 8):
        chunk = tiles[k:k + DC * 8]; rws = (len(chunk) + DC - 1) // DC
        S = Image.new('RGB', (DC * CW, rws * CH), 'black')
        for i, t in enumerate(chunk): S.paste(t, ((i % DC) * CW, (i // DC) * CH))
        S.save(f'{O}/day_{day}_{k // (DC * 8)}.jpg', quality=78)
print('clip sheets', idx, 'day sheets', len(by))
