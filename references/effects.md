# Effects and transitions

All effects are sub-compositions from `scripts/effects.py` (call `setup()` first). They run on the beat times you
pass in (local seconds). Keep one primary idea per moment; effects should carry content, not decorate.

| Effect | Use for | Notes |
|---|---|---|
| `kb` | one strong photo | landscape: full-bleed slow push; portrait: paper print on a warm dark backdrop |
| `burst` | 2–4 photos of one moment | one photo per 2 beats; portrait photos as prints |
| `prints_row` | 2–3 portrait photos | drop in on beats; warm backdrop (a blurred enlargement of a face behind prints looks bad) |
| `mosaic` | 3–4 selfies of the day | tilted prints pop on beats — the "us" moment; max one per day |
| `tri_video` | 1–3 vertical phone videos | panels slide in on beats over a blurred copy; a pair works for sunsets |
| `vid_seq` | vertical clips that must play in full | e.g. original-sound moments |
| `analog` | one film scan | 35 mm strip, grain, gate weave, slow push; light-leak overlay on the way in; portrait-aware |
| `analog_strip` | 2–4 scans of one place | strip pans sideways |
| `finale` | ending | scans drop onto a table on beats, then a title card with dates |
| `live` | Live Photo | print that comes alive — use rarely, people found it odd |

Film scans work best as **interstitials next to the same place shot digitally** (statue on phone → same statue on
film). Put each scan at its chronological spot — ask if unsure (a "dinner" scan may really be lunch elsewhere).

## Transitions

- Dissolve 0.4 s (`sine.inOut`) when the place or day changes, into/out of maps and film strips.
- Hard cut on the beat inside a scene.
- No whip/glitch effects unless asked; travel films want calm.
- Light leak (`organic-light-leak-overlay` from the registry) only on film-scan entrances, 2 s.

## Captions and title

- Title over a moving shot (not a mediocre still): big serif name, small letter-spaced subtitle with the period.
- Place captions bottom-left: eyebrow (what: "dinner", "day 3"), place name in serif, optional sub. Put a soft
  radial scrim under them — bright skies otherwise fail contrast checks.
- Per-day map card: "day N · date" + day title.

## Drives

- Match cut: one framing group, aligned with `dash_align.py`, cuts on beats; a burst of 4 one-beat shots then a
  calm vista (≈4 s) reads better than an endless beat-cut.
- Hyperlapse (3–4× speed, one long shot) is an alternative people may prefer — offer both if unsure.
- Sprinkle 1–2 s driver-profile shots so the drive has people in it.
- Phone videos from the car (dashboard + road) make good triptychs.
