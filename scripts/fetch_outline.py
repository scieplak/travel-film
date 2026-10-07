#!/usr/bin/env python3
"""Fetch a land outline (island / region) from OpenStreetMap Nominatim and save the largest ring as [[lon,lat],...].

Usage:
  python3 fetch_outline.py "Mallorca" --out work/outline.json [--pick 0] [--threshold 0.0008]

Only the place NAME is sent to Nominatim — never GPS points or anything from the user's media.
Prints the candidates (Nominatim often returns several places with the same name); use --pick to choose.
Natural Earth 1:10m is too coarse for a single island (≈85 points); OSM gives ~900 at threshold 0.0008.
Respect the Nominatim usage policy: one request, a real User-Agent, no bulk use.
"""
import argparse, json, urllib.parse, urllib.request
ap = argparse.ArgumentParser(); ap.add_argument('place'); ap.add_argument('--out', required=True)
ap.add_argument('--pick', type=int, default=0); ap.add_argument('--threshold', type=float, default=0.0008); A = ap.parse_args()
url = 'https://nominatim.openstreetmap.org/search?' + urllib.parse.urlencode(dict(q=A.place, format='json', polygon_geojson=1, polygon_threshold=A.threshold, limit=5))
req = urllib.request.Request(url, headers={'User-Agent': 'travel-film-skill/1.0 (personal video editing)'})
res = json.load(urllib.request.urlopen(req, timeout=60))
for i, r in enumerate(res): print(i, r.get('osm_type'), r.get('type'), r['geojson']['type'], r.get('display_name', '')[:70])
g = res[A.pick]['geojson']
rings = [p[0] for p in g['coordinates']] if g['type'] == 'MultiPolygon' else [g['coordinates'][0]]
ring = max(rings, key=len); json.dump(ring, open(A.out, 'w'))
xs = [c[0] for c in ring]; ys = [c[1] for c in ring]
print(f'saved {len(ring)} points  lon {min(xs):.3f}..{max(xs):.3f}  lat {min(ys):.3f}..{max(ys):.3f}')
