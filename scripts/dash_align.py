#!/usr/bin/env python3
"""Align driving shots to one reference framing so the dashboard/hood stays put in a match-cut sequence.

Usage:
  python3 dash_align.py --ref ref_shot.mp4@1.0 --mask bottom:0.40 shotA.mp4@0.3 shotB.mp4@0.3 ... --out align.json
  # then re-conform each shot: conform_linear.py --src shotA.mp4 ... --rot R --zoom Z --dx DX --dy DY

Works on already lens-corrected shots (or Linear-mode GoPro). Estimates a similarity transform (scale, rotation,
translation) with OpenCV ECC on edge maps inside a mask that covers only the static car parts (dashboard, hood,
mirror) — the moving landscape outside the window would otherwise dominate. Outputs conform_linear parameters
with the minimum zoom that keeps the frame covered. Shots whose ECC correlation is low (< 0.35) are flagged:
the camera moved too much; pick a different moment.

--mask examples: bottom:0.40 (lower 40% = dashboard), bottom:0.12 (hood strip), box:0.6,0,0.92,0.22 (mirror).
"""
import argparse, json, math, subprocess, numpy as np, cv2

ap = argparse.ArgumentParser(); ap.add_argument('--ref', required=True); ap.add_argument('--mask', action='append', default=[])
ap.add_argument('--out', required=True); ap.add_argument('shots', nargs='+'); A = ap.parse_args()
W, H = 960, 540

def frame(spec):
    p, t = spec.rsplit('@', 1)
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', t, '-i', p, '-frames:v', '1', '-vf', f'scale={W}:{H}', '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(H, W)

def edges(g):
    g = cv2.GaussianBlur(np.log1p(g.astype(np.float32)), (0, 0), 1.5)
    m = np.hypot(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1)); return m / (m.max() + 1e-6)

M = np.zeros((H, W), np.uint8)
for spec in (A.mask or ['bottom:0.40']):
    kind, v = spec.split(':', 1)
    if kind == 'bottom': M[int(H * (1 - float(v))):, :] = 255
    elif kind == 'box':
        x0, y0, x1, y1 = map(float, v.split(',')); M[int(H * y0):int(H * y1), int(W * x0):int(W * x1)] = 255
ref = edges(frame(A.ref)); res = {}
for spec in A.shots:
    cur = edges(frame(spec)); Wm = np.eye(2, 3, dtype=np.float32); cc = -1
    for lvl in (4, 2, 1):
        a = cv2.resize(ref, (W // lvl, H // lvl)); b = cv2.resize(cur, (W // lvl, H // lvl)); mk = cv2.resize(M, (W // lvl, H // lvl), interpolation=cv2.INTER_NEAREST)
        Ws = Wm.copy(); Ws[:, 2] /= lvl
        try: cc, Ws = cv2.findTransformECC(a, b, Ws, cv2.MOTION_AFFINE, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-5), mk, 3)
        except cv2.error: cc = -1
        Wm = Ws.copy(); Wm[:, 2] *= lvl
    # Wm maps ref coords -> shot coords. We need shot -> ref: invert, then decompose into scale/rotation/shift.
    inv = cv2.invertAffineTransform(Wm); s = math.sqrt(abs(np.linalg.det(inv[:, :2]))); rot = math.degrees(math.atan2(inv[1, 0], inv[0, 0]))
    cx, cy = W / 2, H / 2; tx = inv[0, 0] * cx + inv[0, 1] * cy + inv[0, 2] - cx; ty = inv[1, 0] * cx + inv[1, 1] * cy + inv[1, 2] - cy
    th = math.radians(abs(rot)); cover = max(((0.5 + abs(tx / W / s)) * math.cos(th) + (0.28125 + abs(ty / W / s)) * math.sin(th)) / 0.5,
                                         ((0.5 + abs(tx / W / s)) * math.sin(th) + (0.28125 + abs(ty / W / s)) * math.cos(th)) / 0.28125)
    res[spec] = dict(ecc=round(float(cc), 3), rot=round(rot, 3), zoom=round(max(s, cover) * 1.005, 4), dx=round(tx / W, 5), dy=round(ty / W, 5), ok=cc >= 0.35)
    print(spec, res[spec])
json.dump(res, open(A.out, 'w'), indent=1)
