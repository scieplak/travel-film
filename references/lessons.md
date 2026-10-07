# Lessons (each cost real time)

- GoPro clocks lie; phone EXIF/GPS is the source of truth for dates and order.
- Check the GoPro lens mode before "fixing" fisheye — Linear clips need no correction.
- iPhone video is HLG HDR with a rotation matrix: convert with `avconvert -p Preset1920x1080` (tone map + rotation).
- Film scans and some HEICs carry EXIF orientation: always `ImageOps.exif_transpose`, or vertical frames come
  out sideways.
- A clip with a display-matrix rotation rendered straight looks squashed; refuse it in conform scripts.
- `hyperframes beats` returned 241 BPM for an 85 BPM track; use librosa with a tempo hint and phase alignment.
- Monolithic 4K render of a long film exhausted 32 GB RAM and shut the Mac down → parts + 2 workers + guard.
- Background renders die with the agent session (`render_cancelled_parent_exited`) → setsid +
  `HYPERFRAMES_RENDER_DETACHED=1`.
- Graded renders drop single black frames after some cuts → `repair_black.py` every time.
- `check` reports `sweep_static` as a false positive when every video has data-color-grading; verify with
  snapshots instead.
- Sub-composition videos need `data-hf-media-start-basis="local"`; never time a `<video>` inside a timed wrapper.
- Duplicate media ids (same track used twice) fail lint — suffix ids.
- Head/tail handles on every conformed shot avoid black first frames.
- Do not edit a running bash render script — bash reads it while executing.
- The person's taste after real projects: chronology over theme; fewer car photos; no blurred enlarged faces
  behind prints; no jittery cuts; no dialogue; music with character; maps must match reality.
- Loop-based catalogue tracks repeat a 16-bar phrase almost verbatim; a viewer hears it as "the music plays twice".
  Use each phrase once and jump to a later section of the track on a bar line instead of letting it loop.
- Tracks can contain multi-second silent breaks. Whenever the plan reaches a new part of a track, scan the RMS of
  the media range actually used, and skip a break by a whole number of beats so the cut grid stays in phase.
- Real film edge print: Kodak Gold 200 reads "KODAK GB 200" plus the frame number ("▶ 23 ▶ 23A") and a DX barcode.
  Take the frame numbers from the real scans.
- After lengthening a day (inserts), re-check every music hand-over: the next track can end up starting seconds
  before the previous one ends (two songs at once). Hand over at the day map and keep the beat mapping. Also check
  where each track goes silent on its own (some end several seconds before the file does).
- A push-in on a single film frame must move the whole strip (frame, perforations, edge print), never just the photo
  inside a static frame. Keep the edge print inside the frame (scale about 0.965 → 1.0, with a static backdrop).
