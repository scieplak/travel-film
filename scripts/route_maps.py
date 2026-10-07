#!/usr/bin/env python3
"""Animated per-day route maps as HyperFrames sub-compositions (mapv1.html, mapv2.html, ...).

Usage:
  python3 route_maps.py config.json --out film/compositions [--durations '[6.3,6.3,...]']

config.json:
{
  "outline": "work/outline.json",            # [[lon,lat],...] land ring — make with fetch_outline.py
  "center": [38.75, 20.70], "scale": 1400,  # map projection: lat/lon at canvas (1000,580), px per degree lat
  "peak": {"name": "Mt. Example", "at": [38.70, 20.68]},   # optional mountain marker
  "waypoints": {"Airport": [38.62, 20.76], "Town": [38.71, 20.70], "Road bend": [..]},
  "days": [ {"n": 1, "date": "01.06", "title": "Arrival",
             "route": ["Airport", "Road bend", "Town"],          # through road waypoints so lines follow roads
             "labels": [["Airport", 1], ["Town", -1], ["Beach label", "Town", 1]] } ]   # [text, side] or [text, waypoint, side]
}
Each map: island fades in, the day's route draws itself, a dot travels it, labels pop when the dot arrives,
previous days stay as faint lines, title "day N · date". Zoom adapts to the day's route.
Verify against reality: plot every geotagged photo on the outline (see references/maps.md) — waypoints should sit
on the photo clusters, and a route should never cross a mountain range where the real road follows the coast.
"""
import json, math, sys, argparse
ap = argparse.ArgumentParser(); ap.add_argument('config'); ap.add_argument('--out', required=True); ap.add_argument('--durations', default=None)
A = ap.parse_args(); CFG = json.load(open(A.config))
ring = json.load(open(CFG['outline']))
LAT0, LON0 = CFG['center']; S = CFG.get('scale', 1400)
C = math.cos(math.radians(LAT0)); CX, CY = 1000, 580
def P(lat, lon): return (CX + (lon - LON0) * C * S, CY - (lat - LAT0) * S)
island = 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in (P(la, lo) for lo, la in ring)) + ' Z'
W = {k: tuple(v) for k, v in CFG['waypoints'].items()}
DAYS = [dict(n=d['n'], date=d.get('date', ''), title=d['title'], route=d['route'], labels=[tuple(l) for l in d['labels']]) for d in CFG['days']]
PEAK = CFG.get('peak')
def catmull(pts,n=14):
    out=[]
    P_=[pts[0]]+pts+[pts[-1]]
    for i in range(1,len(P_)-2):
        p0,p1,p2,p3=P_[i-1],P_[i],P_[i+1],P_[i+2]
        for k in range(n):
            t=k/n; t2=t*t; t3=t2*t
            out.append(tuple(0.5*((2*p1[j])+(-p0[j]+p2[j])*t+(2*p0[j]-5*p1[j]+4*p2[j]-p3[j])*t2+(-p0[j]+3*p1[j]-3*p2[j]+p3[j])*t3) for j in (0,1)))
    out.append(pts[-1]); return out
def route_geom(names):
    pts=[P(*W[n]) for n in names]
    # dedupe consecutive identical (return trips) by tiny offset
    sm=catmull(pts); L=[0]
    for a,b in zip(sm,sm[1:]): L.append(L[-1]+math.dist(a,b))
    d='M'+' L'.join(f'{x:.1f},{y:.1f}' for x,y in sm)
    return sm,L,d
def html(day,D):
    sm,L,d=route_geom(day['route']); total=L[-1]
    prev=[route_geom(dd['route'])[2] for dd in DAYS if dd['n']<day['n']]
    t0,t1=0.55,D-0.75
    pts=[P(*W[n]) for n in day['route']]
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
    bw=max(xs)-min(xs)+260; bh=max(ys)-min(ys)+200
    z=min(1920*0.62/bw,1080*0.66/bh,1.55); z=max(z,0.95)
    mx=(max(xs)+min(xs))/2; my=(max(ys)+min(ys))/2
    vx,vy=1060-mx*z,620-my*z
    # dot keyframes (40 segments)
    seg=40; frames=[]
    for i in range(1,seg+1):
        target=total*i/seg; j=next(k for k in range(len(L)) if L[k]>=target-1e-6); x,y=sm[j]
        frames.append(f'{{ x: {x:.1f}, y: {y:.1f} }}')
    kf=[f'tl.to("#m{day["n"]}-dot", {{ keyframes: [{", ".join(frames)}], duration: {t1-t0:.3f}, ease: "none" }}, {t0});']
    labs=[]; lab_js=[]
    for k,lab in enumerate(day['labels']):
        if len(lab)==3: text,wp,side=lab
        else: text,side=lab; wp=text
        x,y=P(*W[wp])
        # time when dot reaches waypoint: nearest sample
        j=min(range(len(sm)),key=lambda q:math.dist(sm[q],(x,y))); tt=t0+(t1-t0)*L[j]/total
        anchor='start' if side>0 else 'end'; dx=22*side
        labs.append(f'<g class="lab" id="m{day["n"]}-lab{k}"><circle cx="{x:.1f}" cy="{y:.1f}" r="{9/z:.2f}" fill="#ff7a3d" stroke="#fff" stroke-width="{3/z:.2f}"/><text x="{x+dx/z:.1f}" y="{y+9/z:.1f}" font-size="{30/z:.2f}" stroke-width="{7/z:.2f}" text-anchor="{anchor}" class="labt">{text}</text></g>')
        lab_js.append(f'tl.fromTo("#m{day["n"]}-lab{k}", {{ opacity: 0, y: 8 }}, {{ opacity: 1, y: 0, duration: 0.35, ease: "back.out(2)" }}, {max(0.3,tt-0.15):.3f});')
    tx,ty=P(*PEAK['at']) if PEAK else (-9999,-9999); pname=PEAK.get('name','') if PEAK else ''
    teide=f'<g id="m{day["n"]}-teide" opacity="0.85"><path d="M{tx-16/z:.1f},{ty+12/z:.1f} L{tx:.1f},{ty-16/z:.1f} L{tx+16/z:.1f},{ty+12/z:.1f} Z" fill="#7b6a58"/><path d="M{tx-6/z:.1f},{ty-4/z:.1f} L{tx:.1f},{ty-16/z:.1f} L{tx+6/z:.1f},{ty-4/z:.1f} Z" fill="#fff"/><text x="{tx:.1f}" y="{ty+40/z:.1f}" text-anchor="middle" class="peak" font-size="{22/z:.2f}">{pname}</text></g>'
    sx,sy=sm[0]
    cid=f'mapv{day["n"]}'
    return f'''<!doctype html>
<html lang="pl">
  <head><meta charset="UTF-8" /></head>
  <body>
    <template id="{cid}">
      <style>
        #root {{ position: absolute; inset: 0; background: radial-gradient(ellipse 80% 90% at 55% 50%, #17465c 0%, #0d2c3c 60%, #081d29 100%); overflow: hidden; }}
        .map-svg {{ position: absolute; inset: 0; width: 1920px; height: 1080px; }}
        .labt {{ font-family: "Montserrat", sans-serif; font-weight: 700; fill: #fffaf0; paint-order: stroke; stroke: #0b2433; stroke-linejoin: round; }}
        .peak {{ font-family: "Montserrat", sans-serif; font-weight: 400; fill: #3d342b; letter-spacing: 0.1em; }}
        .day-head {{ position: absolute; left: 110px; top: 96px; }}
        .day-eyebrow {{ font-family: "Montserrat", sans-serif; font-weight: 700; font-size: 26px; letter-spacing: 0.32em; text-transform: uppercase; color: #ffb27f; }}
        .day-title {{ margin-top: 10px; font-family: "Playfair Display", serif; font-weight: 400; font-size: 84px; line-height: 1.05; color: #fffaf0; text-shadow: 0 3px 18px rgba(5,20,30,0.85), 0 1px 3px rgba(5,20,30,0.9); }}
      </style>
      <div id="root" data-composition-id="{cid}" data-width="1920" data-height="1080" data-duration="{D:.3f}">
        <svg class="map-svg" viewBox="0 0 1920 1080" xmlns="http://www.w3.org/2000/svg">
          <g transform="translate({vx:.1f},{vy:.1f}) scale({z:.4f})"><g id="{cid}-island-g">
            <path d="{island}" fill="#e9dcc0" stroke="#fff6e6" stroke-width="3" vector-effect="non-scaling-stroke" stroke-linejoin="round"/>
            {teide}
            {''.join(f'<path d="{p}" fill="none" stroke="#ff7a3d" stroke-opacity="0.32" stroke-width="5" vector-effect="non-scaling-stroke" stroke-linecap="round" stroke-linejoin="round"/>' for p in prev)}
            <path id="m{day["n"]}-route" d="{d}" fill="none" stroke="#ff7a3d" stroke-width="{7/z:.2f}" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="{total:.1f}" stroke-dashoffset="{total:.1f}"/>
            {''.join(labs)}
            <circle id="m{day["n"]}-dot" cx="0" cy="0" r="{13/z:.2f}" fill="#fff" stroke="#ff7a3d" stroke-width="{6/z:.2f}"/>
          </g></g>
        </svg>
        <div class="day-head"><div class="day-eyebrow" id="m{day["n"]}-eyebrow">dzień {day["n"]} · {day["date"]}</div><div class="day-title" id="m{day["n"]}-title">{day["title"]}</div></div>
      </div>
      <script>
        const tl = gsap.timeline({{ paused: true }});
        tl.fromTo("#{cid}-island-g", {{ opacity: 0, scale: 0.94, transformOrigin: "50% 50%" }}, {{ opacity: 1, scale: 1, duration: 0.6, ease: "power2.out" }}, 0);
        tl.fromTo("#m{day["n"]}-eyebrow", {{ opacity: 0, y: 14 }}, {{ opacity: 1, y: 0, duration: 0.5, ease: "power2.out" }}, 0.1);
        tl.fromTo("#m{day["n"]}-title", {{ opacity: 0, y: 22 }}, {{ opacity: 1, y: 0, duration: 0.6, ease: "power3.out" }}, 0.2);
        tl.set("#m{day["n"]}-dot", {{ x: {sx:.1f}, y: {sy:.1f} }}, 0);
        tl.fromTo("#m{day["n"]}-route", {{ attr: {{ "stroke-dashoffset": {total:.1f} }} }}, {{ attr: {{ "stroke-dashoffset": 0 }}, duration: {t1-t0:.3f}, ease: "none" }}, {t0});
        {chr(10).join('        '+x for x in kf).strip()}
        {chr(10).join('        '+x for x in lab_js).strip()}
        window.__timelines["{cid}"] = tl;
      </script>
    </template>
  </body>
</html>
'''
durs = json.loads(A.durations) if A.durations else [6.34] * len(DAYS)
for day, D in zip(DAYS, durs):
    open(f'{A.out}/mapv{day["n"]}.html', 'w').write(html(day, D)); print('map', day['n'], D)
