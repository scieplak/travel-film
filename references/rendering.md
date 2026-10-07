# Rendering

## Split

- Parts of ~1.5 min (5–7 for a 9 min film), boundaries at hard cuts where no dissolve, caption, map or overlay
  is active; clips straddling a boundary get `data-media-start` trimmed so nothing is lost or doubled.
- One audio-only composition for the whole length (music and ambience crossfades stay continuous).
- Composition at 1920×1080, render `--resolution 4k` (supersampled), 30 fps.

## Run

```bash
HYPERFRAMES_RENDER_DETACHED=1 nohup perl -MPOSIX -e 'POSIX::setsid(); exec @ARGV' \
  scripts/render_parts.sh film v3 ~/Movies/trip-film/Trip-4K.mp4 > render.out 2>&1 < /dev/null & disown
```

Watch `film/v3_render.status` (Monitor tool); report progress per part. Typical on an M3 Pro: 7–11 min per
1.5 min part at 4K, ~15 min post-processing. Free memory stayed ≥ 5 GB with 2 workers.

## After

- `repair_black.py` — isolated black frames after cuts (graded media) are replaced by the previous frame.
- `verify_render.py` — black/freeze/silence/loudness. Freezes of a few seconds on prints are expected.
- Contact sheet every 4 s — look at it: order, captions, rotations, duplicates.
- Keep previous renders; name versions (A/B, v3, v3.2).

## Monitor hygiene

Do not put the job script's name in a Monitor command line together with a `pgrep -f <script>` wait — the
monitor itself matches and blocks the wait loop. Re-arm monitors after their 30 min expiry.
