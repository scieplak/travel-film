"""Effect sub-composition generators for HyperFrames travel films.

Every generator returns the HTML text of one templated sub-composition (write it to compositions/<cid>.html and
mount it with data-composition-src). All ids are prefixed with the composition id so the assembled page stays
unique. Times are local to the sub-composition. Media are referenced as assets/<MEDIA_DIR>/<file>.

Call setup(media_meta_path, grade_json, grade_blur_json, grade_film_json, media_dir='media') once first.
- grade:      main look (HyperFrames data-color-grading JSON, e.g. warm-daylight preset + adjust)
- grade_blur: same look darker + blur effect, used for backgrounds behind vertical clips
- grade_film: film-scan finish (grain ~0.22, vignette ~0.18) for analog interstitials

Effects:
  kb            single photo: landscape = full-bleed slow push; portrait = paper print on a warm backdrop
  burst         photos switching on beats (portrait ones as prints)
  prints_row    2-3 portrait prints dropping in on beats
  mosaic        3-4 selfies as tilted prints popping in on beats
  tri_video     1-3 vertical videos as panels sliding in on beats over a blurred copy (triptych / pair / single)
  vid_seq       vertical videos back to back (keeps original sound possible at host level)
  live          Live Photo: print that comes alive at half speed (use sparingly — can feel odd)
  analog        one film scan in a 35 mm strip with grain, slow push and gate weave (portrait-aware)
  analog_strip  2-4 scans on one strip panning sideways
  finale        scans dropping onto a table on beats, then a title card
"""
import json, html as _h

M = {}; G = GB = GA = ''; MEDIA = 'media'
def setup(media_meta, grade, grade_blur, grade_film, media_dir='media'):
    global M, G, GB, GA, MEDIA
    M = json.load(open(media_meta)); MEDIA = media_dir
    G = _h.escape(open(grade).read(), quote=True); GB = _h.escape(open(grade_blur).read(), quote=True); GA = _h.escape(open(grade_film).read(), quote=True)

BASE_CSS = """
#root { position: absolute; inset: 0; overflow: hidden; background: #000; }
.fill { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
.warm-bg { position: absolute; inset: 0; background: radial-gradient(ellipse 90% 90% at 50% 45%, #3b2a1d 0%, #1b130c 70%, #0e0906 100%); }
.blurwrap { position: absolute; inset: -60px; }
.blurwrap img, .blurwrap video { width: 100%; height: 100%; object-fit: cover; }
.print { position: absolute; background: #f7f1e6; box-shadow: 0 18px 50px rgba(0,0,0,0.55); }
.print img, .print video { position: absolute; object-fit: cover; }
.panel { position: absolute; overflow: hidden; border-radius: 6px; box-shadow: 0 18px 60px rgba(0,0,0,0.55); }
.panel video { width: 100%; height: 100%; object-fit: cover; }
.cap { position: absolute; left: 0; right: 0; text-align: center; font-family: "Playfair Display", serif; color: #3a2a1c; }
.strip { position: absolute; inset: 0; background: #160d06; }
.band { position: absolute; left: 0; width: 100%; height: 110px; background: #2b1a0c; overflow: hidden; }
.holes { position: absolute; left: -20px; display: flex; gap: 46px; }
.hole { width: 44px; height: 42px; border-radius: 7px; background: #0b0603; flex: none; }
.edge { position: absolute; font-family: "JetBrains Mono", monospace; font-weight: 700; font-size: 20px; letter-spacing: 0.18em; color: #e89a3c; opacity: 0.85; white-space: nowrap; }
.fwin { position: absolute; overflow: hidden; border-radius: 10px; }
.fwin img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
"""


def orient(f):
    m = M[f]
    return 'p' if m['h'] > m['w'] else 'l'


def wrap(cid, dur, body, tl, extra_css=''):
    return f'''<!doctype html>
<html lang="pl"><head><meta charset="UTF-8" /></head><body>
<template id="{cid}">
<style>
{BASE_CSS}
{extra_css}
</style>
<div id="root" data-composition-id="{cid}" data-width="1920" data-height="1080" data-duration="{dur:.3f}">
{body}
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(tl)}
window.__timelines["{cid}"] = tl;
</script>
</template></body></html>
'''


def print_box(cid, k, f, x, y, w, h, rot, pad=16, bottom=None, caption=None, grade=True):
    """A paper print holding photo f. Returns (html, selector)."""
    bottom = pad if bottom is None else bottom
    iw, ih = w - 2 * pad, h - pad - bottom
    cap = f'<div class="cap" style="bottom:{max(12, bottom // 2 - 22)}px;font-size:34px;">{caption}</div>' if caption else ''
    g = f' data-color-grading="{G}"' if grade else ''
    return (f'<div id="{cid}-pr{k}" class="print" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;">'
            f'<img id="{cid}-pi{k}" src="assets/{MEDIA}/{f}"{g} style="left:{pad}px;top:{pad}px;width:{iw}px;height:{ih}px;" alt="" />{cap}</div>',
            f'#{cid}-pr{k}')


def blur_bg(cid, f):
    return f'<div class="blurwrap"><img id="{cid}-bg" src="assets/{MEDIA}/{f}" data-color-grading="{GB}" alt="" /></div>'


def kb(cid, f, dur):
    """Single photo: landscape full-bleed slow push; portrait as a print on its own blurred background."""
    if orient(f) == 'l':
        body = f'<div id="{cid}-w" class="fill"><img id="{cid}-i" class="fill" src="assets/{MEDIA}/{f}" data-color-grading="{G}" alt="" /></div>'
        tl = [f'tl.fromTo("#{cid}-w", {{ scale: 1.0, xPercent: 0 }}, {{ scale: 1.08, xPercent: -1.5, duration: {dur:.3f}, ease: "none" }}, 0);']
    else:
        h = 960; w = int(h * 3 / 4) + 0
        pr, sel = print_box(cid, 0, f, (1920 - w) // 2, 60, w, h, 0, pad=18)
        body = '<div class="warm-bg"></div>' + pr
        tl = [f'tl.fromTo("{sel}", {{ scale: 0.97, rotation: -1.2 }}, {{ scale: 1.03, rotation: -0.4, duration: {dur:.3f}, ease: "none" }}, 0);']
    return wrap(cid, dur, body, tl)


def burst(cid, files, beat_times, dur):
    """Photos switching hard on beats. beat_times[i] is local start of photo i."""
    body = []; tl = []
    for k, f in enumerate(files):
        t0 = beat_times[k]; t1 = beat_times[k + 1] if k + 1 < len(files) else dur
        if orient(f) == 'l':
            body.append(f'<div id="{cid}-s{k}" class="fill" style="opacity:0"><img id="{cid}-i{k}" class="fill" src="assets/{MEDIA}/{f}" data-color-grading="{G}" alt="" /></div>')
            tl.append(f'tl.fromTo("#{cid}-i{k}", {{ scale: 1.04 }}, {{ scale: 1.0, duration: {t1 - t0:.3f}, ease: "power2.out" }}, {t0:.3f});')
        else:
            h = 960; w = 720
            pr, sel = print_box(cid, k, f, (1920 - w) // 2, 60, w, h, 0, pad=18)
            body.append(f'<div id="{cid}-s{k}" class="fill" style="opacity:0"><div class="warm-bg"></div>{pr}</div>')
            rot = [-2.0, 1.6, -1.0, 2.2][k % 4]
            tl.append(f'tl.fromTo("{sel}", {{ scale: 1.08, rotation: {rot * 2} }}, {{ scale: 1.0, rotation: {rot}, duration: 0.35, ease: "back.out(1.5)" }}, {t0:.3f});')
        tl.append(f'tl.set("#{cid}-s{k}", {{ opacity: 1 }}, {t0:.3f});')
        if k + 1 < len(files): tl.append(f'tl.set("#{cid}-s{k}", {{ opacity: 0 }}, {t1:.3f});')
    return wrap(cid, dur, '\n'.join(body), tl)


def prints_row(cid, files, dur, beat_times, caption=None):
    """2-3 portrait prints side by side on the blurred first photo, entering on beats."""
    n = len(files); h = 780 if n == 3 else 880; w = int(h * 0.75)
    gap = 60; total = n * w + (n - 1) * gap; x0 = (1920 - total) // 2
    rots = [-3, 1.5, -1.5, 2.5]
    body = ['<div class="warm-bg"></div>']; tl = []
    for k, f in enumerate(files):
        pr, sel = print_box(cid, k, f, x0 + k * (w + gap), (1080 - h) // 2 - 10 + (k % 2) * 24, w, h, rots[k], pad=16)
        body.append(pr)
        tl.append(f'tl.fromTo("{sel}", {{ opacity: 0, y: 60, rotation: {rots[k] * 3} }}, {{ opacity: 1, y: 0, rotation: {rots[k]}, duration: 0.45, ease: "back.out(1.4)" }}, {beat_times[k]:.3f});')
    return wrap(cid, dur, '\n'.join(body), tl)


def mosaic(cid, files, dur, beat_times):
    """3-4 selfie prints popping in on beats over a warm dark background."""
    land = all(orient(f) == 'l' for f in files)
    if land and len(files) == 4:
        boxes = [(150, 45, 780, 585, -3), (990, 70, 780, 585, 2.5), (170, 470, 780, 585, 1.5), (975, 450, 780, 585, -2.2)]
    elif land:
        boxes = [(110, 140, 700, 525, -3), (610, 380, 700, 525, 2), (1110, 160, 700, 525, -1.5)]
    else:
        n = len(files); h = 700; w = 525; gap = 40; x0 = (1920 - (n * w + (n - 1) * gap)) // 2
        boxes = [(x0 + k * (w + gap), 170 + (k % 2) * 60, w, h, [-3, 2.5, -1.5, 2.2][k]) for k in range(n)]
    body = ['<div class="warm-bg"></div>']; tl = []
    for k, f in enumerate(files):
        x, y, w, h, r = boxes[k]
        pr, sel = print_box(cid, k, f, x, y, w, h, r, pad=16)
        body.append(pr)
        tl.append(f'tl.fromTo("{sel}", {{ opacity: 0, scale: 1.25, rotation: {r * 3} }}, {{ opacity: 1, scale: 1, rotation: {r}, duration: 0.35, ease: "back.out(1.6)" }}, {beat_times[k]:.3f});')
    return wrap(cid, dur, '\n'.join(body), tl)


def tri_video(cid, files, dur, beat_times):
    """Three vertical clips sliding in on beats over a blurred copy of the middle clip."""
    n = len(files); H = 900 if n == 3 else 960; W = 506 if n == 3 else int(H * 9 / 16); gap = 28 if n == 3 else 48
    x0 = (1920 - (n * W + (n - 1) * gap)) // 2; top = (1080 - H) // 2
    body = []; tl = []
    mid = files[n // 2]; md = M[mid]['dur']
    body.append(f'<div class="blurwrap"><video id="{cid}-bg" src="assets/{MEDIA}/{mid}" muted playsinline data-start="0" data-duration="{min(dur, md - 0.05):.3f}" data-color-grading="{GB}"></video></div>')
    for k, f in enumerate(files):
        need = dur - beat_times[k] + 0.2
        cd = M[f]['dur']
        rate = 1.0 if cd - 0.3 >= need else max(0.5, (cd - 0.3) / need)
        ms = max(0.0, min(cd / 2 - need * rate / 2, cd - need * rate - 0.1))
        st = max(0.0, beat_times[k] - 0.2)
        body.append(f'<div id="{cid}-p{k}" class="panel" style="left:{x0 + k * (W + gap)}px;top:{top}px;width:{W}px;height:{H}px;opacity:0;">'
                    f'<video id="{cid}-v{k}" src="assets/{MEDIA}/{f}" muted playsinline data-hf-media-start-basis="local" data-start="{st:.3f}" data-duration="{dur - st:.3f}" data-media-start="{ms:.3f}"'
                    + (f' data-playback-rate="{rate:.3f}"' if rate < 1 else '') + f' data-color-grading="{G}"></video></div>')
        tl.append(f'tl.fromTo("#{cid}-p{k}", {{ opacity: 0, y: 70 }}, {{ opacity: 1, y: 0, duration: 0.55, ease: "power3.out" }}, {beat_times[k]:.3f});')
    tl.append(f'tl.fromTo("#{cid}-bg", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4 }}, 0);')
    return wrap(cid, dur, '\n'.join(body), tl)


def live(cid, still, clip, dur, caption):
    """A print holding the still frame; on the second beat it comes alive (Live Photo at half speed)."""
    w = 600; h = 800
    x = (1920 - w) // 2; y = 50
    cd = M[clip]['dur']; play = min(dur - 1.0, cd / 0.5)
    body = ['<div class="warm-bg"></div>',
            f'<div id="{cid}-pr" class="print" style="left:{x}px;top:{y}px;width:{w}px;height:{h + 90}px;">'
            f'<img id="{cid}-st" src="assets/{MEDIA}/{still}" data-color-grading="{G}" style="left:18px;top:18px;width:{w - 36}px;height:{h - 36}px;" alt="" />'
            f'<video id="{cid}-lv" src="assets/{MEDIA}/{clip}" muted playsinline data-hf-media-start-basis="local" data-start="1.0" data-duration="{play:.3f}" data-playback-rate="0.5" data-color-grading="{G}" style="left:18px;top:18px;width:{w - 36}px;height:{h - 36}px;"></video>'
            f'<div class="cap" style="bottom:28px;font-size:34px;">{caption}</div></div>']
    tl = [f'tl.fromTo("#{cid}-pr", {{ opacity: 0, y: 40, rotation: -4 }}, {{ opacity: 1, y: 0, rotation: -1.5, duration: 0.6, ease: "power3.out" }}, 0.05);',
          f'tl.to("#{cid}-pr", {{ keyframes: [{{ scale: 1.02 }}, {{ scale: 1 }}], duration: 0.3, ease: "sine.inOut" }}, 0.95);']
    return wrap(cid, dur, '\n'.join(body), tl)


def _holes(n=21):
    return ''.join('<div class="hole"></div>' for _ in range(n))


def analog(cid, code, dur, frame_no):
    """One analog frame in a 35 mm strip with grain, slow push and gate weave."""
    a = f'a{code}.jpg'; m = M[a]; port = m['h'] > m['w']
    if port:
        fw, fh = 560, 824; fx = (1920 - fw) // 2
    else:
        fw, fh = 1470, 824; fx = 225
    body = (f'<div id="{cid}-strip" class="strip">'
            f'<div class="band" style="top:0"><div class="holes" style="top:34px">{_holes()}</div></div>'
            f'<div class="band" style="bottom:0"><div class="holes" style="bottom:34px">{_holes()}</div></div>'
            f'<div class="edge" style="top:8px;left:120px">KODAK 400 &nbsp; {frame_no} &nbsp; ▶ {frame_no}A</div>'
            f'<div class="edge" style="bottom:8px;left:760px">{frame_no + 1} &nbsp; ▶ {frame_no + 1}A &nbsp; KODAK 400</div>'
            f'<div id="{cid}-fw" class="fwin" style="left:{fx}px;top:128px;width:{fw}px;height:{fh}px;"><img id="{cid}-ai" src="assets/{MEDIA}/{a}" data-color-grading="{GA}" alt="" /></div></div>')
    tl = [f'tl.fromTo("#{cid}-ai", {{ scale: 1.0 }}, {{ scale: 1.07, duration: {dur:.3f}, ease: "none" }}, 0);',
          f'tl.fromTo("#{cid}-strip", {{ x: 0, y: 0 }}, {{ keyframes: [{{ x: 1.5, y: -1 }}, {{ x: -1, y: 1.2 }}, {{ x: 0.8, y: 0.4 }}, {{ x: -1.2, y: -0.8 }}, {{ x: 0, y: 0 }}], duration: {dur:.3f}, ease: "sine.inOut" }}, 0);']
    return wrap(cid, dur, body, tl)


def analog_strip(cid, codes, dur, frame_no):
    """Three analog frames on one strip panning right-to-left."""
    fh, gap = 736, 70
    ws = [(492 if M[f'a{c}.jpg']['h'] > M[f'a{c}.jpg']['w'] else 1100) for c in codes]
    xs = []; x = 60
    for w in ws: xs.append(x); x += w + gap
    frames = ''.join(f'<div class="fwin" style="left:{xs[k]}px;top:172px;width:{ws[k]}px;height:{fh}px;"><img id="{cid}-ai{k}" src="assets/{MEDIA}/a{c}.jpg" data-color-grading="{GA}" alt="" /></div>' for k, c in enumerate(codes))
    total = x + 60
    edges = ''.join(f'<div class="edge" style="top:8px;left:{xs[k] + 60}px">KODAK 400 &nbsp; {frame_no + k} &nbsp; ▶ {frame_no + k}A</div>' for k in range(len(codes)))
    body = (f'<div class="strip"><div id="{cid}-rail" style="position:absolute;left:0;top:0;width:{total}px;height:1080px;">'
            f'<div class="band" style="top:0;width:{total}px"><div class="holes" style="top:34px">{_holes(60)}</div></div>'
            f'<div class="band" style="bottom:0;width:{total}px"><div class="holes" style="bottom:34px">{_holes(60)}</div></div>'
            f'{edges}{frames}</div></div>')
    x1 = min(0, 1920 - total) - 120
    tl = [f'tl.fromTo("#{cid}-rail", {{ x: 240 }}, {{ x: {x1}, duration: {dur:.3f}, ease: "sine.inOut" }}, 0);']
    return wrap(cid, dur, body, tl)


def finale(cid, codes, dur, beat_times, title="Trip", subtitle="01 — 07 · 06 · 2026"):
    """Analog prints dropping onto a table on beats, then the closing card (title + dates)."""
    import math
    body = ['<div class="warm-bg"></div>']; tl = []
    n = len(codes)
    for k, c in enumerate(codes):
        m = M[f'a{c}.jpg']; port = m['h'] > m['w']
        w, h = (330, 470) if port else (520, 370)
        ang = (k * 137.5) % 360; rad = 330 + (k % 3) * 70
        x = int(960 + math.cos(math.radians(ang)) * rad * 1.45 - w / 2); y = int(520 + math.sin(math.radians(ang)) * rad * 0.62 - h / 2)
        r = [-8, 6, -4, 9, -6, 4, -10, 7, -3, 5, -7, 8, -5][k % 13]
        pr, sel = print_box(cid, k, f'a{c}.jpg', x, y, w, h, r, pad=14, grade=False)
        body.append(pr)
        tl.append(f'tl.fromTo("{sel}", {{ opacity: 0, scale: 1.4, rotation: {r * 2} }}, {{ opacity: 1, scale: 1, rotation: {r}, duration: 0.4, ease: "power3.out" }}, {beat_times[k]:.3f});')
    body.append(f'<div id="{cid}-card" style="position:absolute;left:560px;top:380px;width:800px;height:320px;background:#f7f1e6;box-shadow:0 24px 70px rgba(0,0,0,0.6);display:flex;flex-direction:column;align-items:center;justify-content:center;">'
                f'<div id="{cid}-t1" style="font-family:\'Playfair Display\',serif;font-size:110px;color:#2b1d12;line-height:1;">{title}</div>'
                f'<div id="{cid}-t2" style="margin-top:22px;font-family:Montserrat,sans-serif;font-weight:700;font-size:28px;letter-spacing:0.3em;color:#9a5b2a;">{subtitle}</div></div>')
    tcard = beat_times[n] if len(beat_times) > n else dur - 4
    tl.append(f'tl.fromTo("#{cid}-card", {{ opacity: 0, y: 40, rotation: -2 }}, {{ opacity: 1, y: 0, rotation: 0, duration: 0.8, ease: "power3.out" }}, {tcard:.3f});')
    return wrap(cid, dur, '\n'.join(body), tl)


def vid_seq(cid, files, durs):
    """Vertical clips played back to back, each centred on a blurred copy of itself. durs = on-screen seconds per clip."""
    H = 1000; W = int(H * 9 / 16); x = (1920 - W) // 2
    body = []; tl = []; t = 0.0
    for k, (f, d) in enumerate(zip(files, durs)):
        st = f'{t:.3f}'; du = f'{d:.3f}'
        body.append(f'<div id="{cid}-s{k}" class="fill" style="opacity:0">'
                    f'<div class="blurwrap"><video id="{cid}-b{k}" src="assets/{MEDIA}/{f}" muted playsinline data-hf-media-start-basis="local" data-start="{st}" data-duration="{du}" data-color-grading="{GB}"></video></div>'
                    f'<div class="panel" style="left:{x}px;top:40px;width:{W}px;height:{H}px;"><video id="{cid}-v{k}" src="assets/{MEDIA}/{f}" muted playsinline data-hf-media-start-basis="local" data-start="{st}" data-duration="{du}" data-color-grading="{G}"></video></div></div>')
        tl.append(f'tl.set("#{cid}-s{k}", {{ opacity: 1 }}, {t:.3f});')
        if k + 1 < len(files): tl.append(f'tl.set("#{cid}-s{k}", {{ opacity: 0 }}, {t + d:.3f});')
        t += d
    return wrap(cid, t, '\n'.join(body), tl)
