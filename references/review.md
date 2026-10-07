# Stage 1 — Review

Goal: the person approves a structure and shot list before anything renders. Budget: read every contact sheet
yourself; metrics only point at candidates.

## Inputs to expect

- GoPro: `GX01nnnn.MP4` (4K HEVC 10-bit) + `GL01nnnn.LRV` proxies (768×432 H.264). Review on LRV, render from MP4.
  The clock is often unset (e.g. year 2016) — use relative order (file number / capture time) and phone dates.
- iPhone: HEIC photos (EXIF date + GPS), MOV video (HLG HDR, usually vertical, rotation in display matrix),
  Live-Photo MP4 companions (1.5–3 s).
- Film scans: JPG, often with an EXIF orientation flag for vertical frames.

## Reject criteria (whole clip or a range)

blurred · tilted horizon > ~3° that cannot be levelled · camera in pocket / floor / sky · finger on lens ·
face in the lens · too dark (night/interiors: keep only shots where the subject is readable) · nothing happening ·
information boards / menus · duplicate takes (keep the best) · rotated clips (display matrix ±90/180) unless
converted.

## What to note per usable clip

usable range (s), what it shows, place, day, best 2–5 s, slow-motion potential (60p+), ambience quality
(wind/speech from `audio_scan.py`), drive framing group.

## Drive framing groups

Match cuts only work within one mounting: e.g. A = behind the wheel, dashboard in the lower third;
B = camera low, steering wheel fills the bottom; C = hood strip at the bottom edge; D = driver profile;
E = selfie/cabin. Make one sheet per group with one frame per clip and recommend the group for the match cut.
Hand-held cameras drift *within* a clip: measure the static parts over time (red displays, hood line) and use
only stable windows.

## Lens and colour

- `VFOV` W/S → fisheye correction available (preview before/after on one clip and let the person choose full vs
  partial). `L` → already rectilinear; do not correct again.
- GoPro Color (blacks ≈ 0–10, high saturation) vs Flat (lifted blacks, low saturation).

## Proposal format

A table per section/day: time range, music, shots as `clip start–end (what)`; mark slow motion; list ambience
moments; list effects (map, triptych, mosaic, film strip). Add a storyboard image (one frame per shot) and send
it. Then stop and wait. Ask only what you cannot infer: place names, date (if clocks are wrong), music choice,
length.
