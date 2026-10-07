#!/usr/bin/env python3
"""Inventory every media file of a trip: camera, capture time, GPS, orientation, HDR, lens mode, duration.

Usage:
  python3 inventory.py --out work/inventory.json SRC_DIR [SRC_DIR ...]

Handles GoPro (GX*.MP4 + GL*.LRV proxies + GPMF lens/GPS metadata), iPhone (HEIC/JPG photos with EXIF date
and GPS, MOV video with QuickTime date/location, Live-Photo MP4 companions), and scanned film (JPG with an EXIF
orientation flag). Prints a per-day summary. Nothing leaves the machine.

Why: GoPro clocks are often wrong (the trip may show up as 2016), iPhone media carries the real date and GPS,
and rotation/HDR flags silently break later steps if they are not known up front.
"""
import argparse, json, os, re, struct, subprocess, glob
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor

ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True); ap.add_argument('dirs', nargs='+')
A = ap.parse_args()

def ffprobe(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries',
                        'stream=index,codec_type,codec_tag_string,width,height,r_frame_rate,color_transfer:stream_side_data=rotation:format=duration:format_tags',
                        '-of', 'json', path], capture_output=True, text=True).stdout
    return json.loads(r or '{}')

def gpmf_info(path):
    """Lens mode + GPS presence from the GoPro GPMF metadata (cheap scan of file head/tail)."""
    out = {}
    with open(path, 'rb') as f:
        d = f.read(4_000_000); f.seek(max(0, os.path.getsize(path) - 3_000_000)); d += f.read()
    for key in (b'VFOV', b'ZFOV', b'POLY', b'ZMPL'):
        i = d.find(key)
        if i < 0: continue
        t = chr(d[i + 4]); sz = d[i + 5]; rep = struct.unpack('>H', d[i + 6:i + 8])[0]; raw = d[i + 8:i + 8 + sz * rep]
        out[key.decode()] = raw.decode('latin1').strip() if t == 'c' else [round(x, 5) for x in struct.unpack('>' + 'f' * (len(raw) // 4), raw[:len(raw) // 4 * 4])]
    j = ffprobe(path)
    g = [s['index'] for s in j.get('streams', []) if s.get('codec_tag_string') == 'gpmd']
    if g:
        data = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-map', f'0:{g[0]}', '-c', 'copy', '-f', 'data', '-'], capture_output=True).stdout
        out['gps_records'] = data.count(b'GPS5') + data.count(b'GPS9')
    return out

def mdls(path):
    o = subprocess.run(['mdls', '-name', 'kMDItemLatitude', '-name', 'kMDItemLongitude', path], capture_output=True, text=True).stdout
    g = lambda k: (re.search(k + r'\s*=\s*(\S+)', o) or [None, None])[1]
    la, lo = g('kMDItemLatitude'), g('kMDItemLongitude')
    return (None if la in (None, '(null)') else float(la), None if lo in (None, '(null)') else float(lo))

def exif(path):
    try:
        from PIL import Image
        im = Image.open(path); e = im.getexif(); dt = e.get(306) or e.get_ifd(0x8769).get(36867)
        return dict(w=im.width, h=im.height, orientation=e.get(274, 1), dt=(dt.replace(':', '-', 2) if dt else None))
    except Exception:
        o = subprocess.run(['sips', '-g', 'creation', '-g', 'pixelWidth', '-g', 'pixelHeight', path], capture_output=True, text=True).stdout
        m = re.search(r'creation:\s*(\S+ \S+)', o)
        return dict(dt=m.group(1).replace(':', '-', 2) if m else None)

def one(path):
    name = os.path.basename(path); ext = name.rsplit('.', 1)[-1].lower()
    r = dict(path=path, file=name, ext=ext)
    if name.startswith(('GL', 'GOPR')) and ext in ('lrv', 'thm'): return None
    if name.startswith('GX') or name.startswith('GH'):
        r['source'] = 'gopro'
    elif ext in ('heic', 'mov') or (name.startswith('IMG_') and ext in ('jpg', 'png', 'mp4')):
        r['source'] = 'iphone'
    else:
        r['source'] = 'scan' if ext in ('jpg', 'jpeg', 'tif', 'tiff') else 'other'
    if ext in ('mp4', 'mov'):
        j = ffprobe(path); v = next((s for s in j.get('streams', []) if s.get('codec_type') == 'video'), {})
        tags = j.get('format', {}).get('tags', {})
        r.update(w=v.get('width'), h=v.get('height'), fps=v.get('r_frame_rate'), transfer=v.get('color_transfer'),
                 hdr=v.get('color_transfer') in ('arib-std-b67', 'smpte2084'),
                 rotation=next((sd.get('rotation') for sd in v.get('side_data_list', []) if 'rotation' in sd), 0),
                 duration=float(j.get('format', {}).get('duration', 0) or 0),
                 dt=(tags.get('com.apple.quicktime.creationdate') or tags.get('creation_time') or '')[:19].replace('T', ' ') or None)
        loc = tags.get('com.apple.quicktime.location.ISO6709')
        if loc:
            m = re.match(r'([+-][\d.]+)([+-][\d.]+)', loc); r['lat'], r['lon'] = float(m.group(1)), float(m.group(2))
        if r['source'] == 'gopro':
            r['gpmf'] = gpmf_info(path)
            lrv = os.path.join(os.path.dirname(path), 'GL' + name[2:-4] + '.LRV')
            r['proxy'] = lrv if os.path.exists(lrv) else None
        if r['source'] == 'iphone' and ext == 'mp4' and os.path.exists(path[:-4] + '.HEIC'):
            r['live_photo_of'] = name[:-4] + '.HEIC'
    else:
        r.update(exif(path))
        if r['source'] == 'iphone' or ext == 'heic':
            r['lat'], r['lon'] = mdls(path)
    return r

files = sorted(f for d in A.dirs for f in glob.glob(os.path.join(os.path.expanduser(d), '**', '*'), recursive=True) if os.path.isfile(f) and not f.endswith('.DS_Store'))
with ThreadPoolExecutor(8) as ex: R = [r for r in ex.map(one, files) if r]
os.makedirs(os.path.dirname(os.path.abspath(A.out)), exist_ok=True)
json.dump(R, open(A.out, 'w'), indent=1)
print('files', len(R), Counter((r['source'], r['ext']) for r in R).most_common())
by = defaultdict(list)
for r in R:
    if r.get('live_photo_of'): continue
    by[(r.get('dt') or '????')[:10]].append(r)
for day in sorted(by):
    L = by[day]; print(day, Counter(r['source'] for r in L).most_common(), 'gps', sum(1 for r in L if r.get('lat')))
flags = [r['file'] for r in R if r.get('rotation') or r.get('orientation', 1) not in (1, None)]
print('rotated (handle before use):', len(flags), flags[:20])
print('HDR videos (convert to SDR):', sum(1 for r in R if r.get('hdr')))
gp = [r for r in R if r['source'] == 'gopro']
if gp: print('GoPro lens modes:', Counter(r.get('gpmf', {}).get('VFOV') for r in gp), 'clips with GPS:', sum(1 for r in gp if r.get('gpmf', {}).get('gps_records')))
