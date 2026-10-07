#!/usr/bin/env python3
"""Check a route-map config against reality: outline + every geotagged photo/video (coloured by day) + waypoints.

Usage:
  python3 verify_map.py config.json --inventory work/inventory.json --out work/verify_map.jpg

Look for: waypoints that sit away from the photo clusters (wrong coordinates), days whose photos appear somewhere
the route never goes (missing stop), routes that cut across mountains where the real road follows the coast
(add road waypoints), photos in the sea (taken from a plane/boat — ignore). The image stays local.
"""
import argparse, json, math, cv2, numpy as np
ap = argparse.ArgumentParser(); ap.add_argument('config'); ap.add_argument('--inventory', required=True); ap.add_argument('--out', required=True); A = ap.parse_args()
CFG = json.load(open(A.config)); ring = json.load(open(CFG['outline'])); R = json.load(open(A.inventory))
xs = [c[0] for c in ring]; ys = [c[1] for c in ring]; lat0 = (min(ys) + max(ys)) / 2; lon0 = (min(xs) + max(xs)) / 2
C = math.cos(math.radians(lat0)); IW, IH = 2400, 1500
S = min(IW * 0.9 / ((max(xs) - min(xs)) * C), IH * 0.9 / (max(ys) - min(ys)))
P = lambda la, lo: (int(IW / 2 + (lo - lon0) * C * S), int(IH / 2 - (la - lat0) * S))
img = np.full((IH, IW, 3), (60, 40, 20), np.uint8)
cv2.fillPoly(img, [np.array([P(la, lo) for lo, la in ring])], (190, 215, 225))
days = sorted({(r.get('dt') or '')[:10] for r in R if r.get('lat')} - {''})
pal = [(255, 0, 0), (255, 128, 0), (0, 160, 0), (0, 200, 200), (200, 0, 200), (0, 0, 0), (0, 90, 255), (120, 60, 0), (0, 120, 255), (90, 0, 160)]
col = {d: pal[i % len(pal)] for i, d in enumerate(days)}
for r in R:
    if r.get('lat') and r.get('dt'): cv2.circle(img, P(r['lat'], r['lon']), 5, col[r['dt'][:10]], -1)
for k, (la, lo) in CFG['waypoints'].items():
    p = P(la, lo); cv2.drawMarker(img, p, (255, 255, 255), cv2.MARKER_CROSS, 14, 2); cv2.putText(img, k, (p[0] + 6, p[1] - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
for d in CFG['days']:
    pts = np.array([P(*CFG['waypoints'][w]) for w in d['route']]); cv2.polylines(img, [pts], False, (40, 120, 255), 2)
for i, d in enumerate(days): cv2.putText(img, d, (30, 40 + i * 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, col[d], 2)
cv2.imwrite(A.out, img, [cv2.IMWRITE_JPEG_QUALITY, 85]); print('wrote', A.out)
