# travel-film

A [Claude Code](https://claude.com/claude-code) skill for editing cinematic holiday / trip films from raw
GoPro clips, iPhone photos and videos, and film-camera scans with HyperFrames.

Claude reviews and culls the footage, keeps strict chronology, cuts on the music's beat grid, match-cuts drives
through the windscreen, adds animated GPS route maps, place captions, film-strip interstitials, triptychs of
vertical phone videos and selfie mosaics, then renders a 4K film memory-safely and verifies it.

The workflow has two stages with a hard stop between them:

1. **Review** — inventory, contact sheets, audio scan, lens/colour detection, drive grouping, a proposed
   structure and storyboard. Nothing renders until you approve.
2. **Edit** — music choice and beat grid, timeline plan, conformed shots, effects, maps, grade, checks, a
   part-by-part 4K render, loudness normalisation, black-frame repair and verification.

## Install

```bash
git clone https://github.com/<you>/travel-film ~/Development/travel-film
ln -s ~/Development/travel-film ~/.claude/skills/travel-film
pip install -r ~/Development/travel-film/requirements.txt
```

Also required: Node + `npx hyperframes`, the HyperFrames skills (`/hyperframes`, `/media-use`), `ffmpeg`/`ffprobe`, and on macOS
`sips` (HEIC) and `avconvert` (HDR → SDR for iPhone video).

Then ask Claude something like *"edit a holiday film from ~/Movies/trip"*.

## Layout

| Path | What |
|---|---|
| `SKILL.md` | workflow, ground rules, stage checklists |
| `references/` | review, people selection, music, effects, maps, rendering, lessons learned |
| `scripts/` | inventory, contact sheets, audio scan, GoPro lens model + conform, dashboard alignment, media prep, beat grid, effects generator, map outline/verify/build, parts renderer, finalize, black-frame repair, render verification |
| `examples/` | fictional route-map config |

## Privacy

The scripts keep everything local except `fetch_outline.py`, which sends only a place name to OpenStreetMap
Nominatim. No media, GPS data or personal paths are stored in this repository.
