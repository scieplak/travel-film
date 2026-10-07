---
name: travel-film
description: Edit a cinematic holiday / trip / vacation film from raw GoPro, iPhone and film-camera (analog scan) material with HyperFrames — review and cull the footage, keep strict chronology, cut on the music's beat grid, match-cut drives through the windscreen, add animated GPS route maps, place captions, film-strip interstitials, triptychs of vertical phone videos and selfie mosaics, then render a 4K film memory-safely and verify it end to end. Use this whenever the user wants a film "z wakacji", a travel video, a trip recap, a holiday montage, or hands over folders of GoPro clips / phone photos / film scans from a trip and asks to "zmontuj", "edit", "make a film", "cut this together" — even if they never say "travel film". Also use it for follow-up corrections on such a film ("swap this photo", "wrong order", "make it less jumpy").
---

# Travel film

Turn a trip's raw material into a 4–10 minute cinematic film the person will actually rewatch. The work has
two stages with a hard stop between them: **review** (no rendering) and **edit** (after the person approves).
HyperFrames does composition and rendering; this skill adds the workflow, the footage-specific tools in
`scripts/`, and the taste and lessons learned from real projects. Load `/hyperframes` (and through it
`/hyperframes-core`, `/media-use`) before writing any composition HTML.

Talk to the person in their language. Keep them in the loop on long jobs: say what is running and roughly how
long it takes.

## Ground rules (why they matter)

- **Chronology is sacred.** People remember a trip as a sequence; a sunny shot after a night scene, or day-3
  footage inside day 2, reads as a mistake. Order everything by real capture time (phone EXIF/GPS beats GoPro,
  whose clock is often unset) and sanity-check scene by scene, inside scenes too.
- **Judge people's faces, not just pixels.** Drop photos with eyes closed, mid-chew, from below, faces cropped,
  distorted by wide-angle, blurry or dark — even if they are sharp and well exposed. Pick the best frame of a
  burst. Ask before using unflattering-but-funny shots. See `references/selection.md`.
- **No dialogue unless asked.** Transcribe all clips; ambience comes only from seconds with no speech and no
  wind. Music beds carry the film.
- **Calm, not jumpy.** Every shot at least a bar (≈2–2.5 s) except deliberate beat-cut drive bursts; soft
  dissolves (0.4 s) between places/days, hard cuts on the beat inside scenes. People hate constant flicker.
- **Music with character.** Generic "travel vlog background" tracks sound auto-generated and annoy people. Search
  by concrete genre (60s psych guitar, flamenco urbano, Italian library lounge, 70s home-movie lo-fi …), cut 25 s
  previews from the strongest section, let the person pick. See `references/music.md`.
- **Never surprise-publish or delete.** Keep every previous render; new versions get new names.
- **Protect the machine.** Long 4K renders go through `scripts/render_parts.sh` (parts, 2 workers, memory guard,
  detached). A single big render once filled 32 GB and shut the laptop down.
- **Footage stays local.** Process media only with local tools (FFmpeg, OpenCV, on-device transcription). Do not
  use upload paths such as `heygen asset upload`, HeyGen cloud render, or `hyperframes capture` vision captioning
  without the person's explicit OK. Send Nominatim only place names, never GPS. The README privacy table lists
  every outbound flow.
- **Corrections come in batches.** When the person starts giving fixes one by one, write each into a
  `corrections.md` (and memory) and do not render until they say the list is complete.

## Stage 1 — Review (no rendering)

1. **Inventory** everything: `python3 scripts/inventory.py --out work/inventory.json <dirs…>` — dates, GPS,
   rotation flags, HDR, GoPro lens mode (`VFOV`: W/S = fisheye, L = Linear), GoPro GPS presence.
2. **Contact sheets**: `python3 scripts/contact_sheets.py --inventory work/inventory.json --out work/review`.
   Read every sheet yourself. Note per clip: usable ranges, rejects (blur, tilt, pocket, empty, too dark,
   finger, face in lens), slow-motion candidates (60p+), drive framing groups.
3. **Audio scan**: `python3 scripts/audio_scan.py --inventory … --out work/audio.json --lang <xx>` — speech spans
   and wind per second.
4. **Colour/lens**: GoPro Color vs Flat from blacks/saturation; lens mode from metadata (no fisheye correction for
   Linear clips). Phone video is HDR (HLG) — will be converted with `avconvert`.
5. **Places and days**: cluster phone GPS per day; ask the person to confirm names of places you are unsure of —
   do not invent them.
6. **Drives**: group GoPro drive clips by camera mounting (dashboard position, hood strip, driver profile). One
   group feeds a match cut; driver-profile shots are 1–2 s cutaways.
7. **Propose** structure (per day: map → scenes → drive → …), shot list with timings, music per section, effects;
   show a storyboard sheet; wait for approval. Details: `references/review.md`.

## Stage 2 — Edit

1. **Music**: choose tracks with the person (`/media-use` catalog or their files). Beat grid with
   `scripts/beats.py` (not `hyperframes beats` — it misjudged tempo on several tracks). Extend a track by whole
   bars if a section needs more time.
2. **Plan** a timeline in code (a `plan.py` that writes `plan.json`): every item starts on a beat (≈15 ms early),
   scenes as sub-compositions, dissolves only at place/day changes, captions at scene starts, J-cuts (ambience
   or next music starts ~1 s before the picture). Inserts of phone/analog material shift later items by whole
   bars of their music so the grid survives.
3. **Conform shots** with head/tail handles (0.5 s / 0.3 s): `scripts/conform_fisheye.py` (Wide/SuperView, lens
   model read from the clip) or `scripts/conform_linear.py` (Linear, levelling, push-in, slow motion). Match-cut
   drives: align the static car parts with `scripts/dash_align.py`.
4. **Phone & scans**: `scripts/prep_media.py` (HDR→SDR, EXIF rotation for photos AND film scans).
5. **Effects**: `scripts/effects.py` generates sub-compositions (prints, bursts, selfie mosaic, triptych of
   vertical videos, film-strip interstitial with light leak, finale collage). See `references/effects.md`.
6. **Maps**: `scripts/fetch_outline.py` (OSM outline by place name) → config with waypoints incl. road bends →
   `scripts/verify_map.py` against the photos' GPS → `scripts/route_maps.py`. See `references/maps.md`.
7. **Grade**: one warm summer look for everything via `hyperframes media-treatment` / data-color-grading; foggy
   or flat shots get a stronger-contrast variant. Snapshot before/after; look at the frames, don't trust numbers.
8. **Check**: `npx hyperframes lint`/`check`, then snapshot every scene midpoint and every dissolve into one
   sheet and look at it (captions legible? photos upright? nothing sideways or duplicated?).
9. **Render**: split into ~1.5 min video parts at hard cuts plus one audio-only composition, then
   `scripts/render_parts.sh` (detached). It normalises to -14 LUFS, repairs isolated black frames, verifies.
   Details and timings: `references/rendering.md`.
10. **Deliver**: final path, length, what changed, what was verified; keep older versions side by side.

## References

- `references/review.md` — stage-1 checklist, reject criteria, drive grouping, proposal format
- `references/selection.md` — choosing photos of people (critical eye)
- `references/music.md` — finding non-generic music, previews, beat grids, extending tracks, mixing levels
- `references/effects.md` — effect catalogue, when each works, layout rules, transitions and J-cuts
- `references/maps.md` — outlines, waypoints, verification against GPS, common mistakes
- `references/rendering.md` — memory-safe parts render, detaching, black-frame glitch, verification
- `references/lessons.md` — pitfalls that cost hours (read before Stage 2)
- `examples/route_config.example.json` — map config shape (fictional data)
