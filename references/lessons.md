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
