# Music

## Finding tracks with character

Generic queries ("upbeat travel vlog acoustic") return tracks that sound auto-generated. Query by concrete genre
and era instead, and filter out anything whose description says vlog / background / corporate / tutorial:

60s psychedelic reverb guitar · Khruangbin-style psych funk · flamenco urbano / tangos / rumba catalana ·
Italian 60s–70s library / dolce vita lounge · 70s home-movie lo-fi · retro synth nostalgic documentary ·
bossa nova · surf rock · spaghetti western · French yé-yé · tropicália · Balearic sunset guitar.

With `/media-use` (HeyGen catalog): `heygen audio sounds list --query "<genre>" --type music --limit 25
--min-score 0.6`, keep ≥ 90 s tracks, download 6–8, cut a 25 s preview from the loudest-median window of each,
send them numbered with a one-line character note. Let the person pick; offer "something similar to N" rounds.
If they bring commercial songs, fine for a private film — mention that platforms may mute/claim them.

## One track per section

Give each day (or pair of days) its own track and change tracks under a map/dissolve. A single track for a long
film gets monotonous; too many changes feel like a playlist.

## Beat grid

`scripts/beats.py track --bpm <hint> --out beats.json` — prints tempo, jitter and loudness per bar. Check that
the BPM matches what you hear (double/half tempo errors are common). Cut ~15 ms before the beat.
Typical shot lengths: scenes 1–2 bars, bursts 1–2 beats per photo, drive bursts 1 beat.

## Extending a track

`--extend A:B --audio-out long.wav` repeats bars A..B-1 once at bar B with a 15 ms crossfade. Pick a repeat
inside one section (same instruments before and after) so the join is inaudible.

## Mixing

Music bed ≈ 0.75–0.85 volume, ambience (waves, fire, restaurant, engine) at -24…-27 LUFS before placement,
J-cut: next ambience/music fades in ~1 s before its picture. Original sound (e.g. the song playing in the car)
replaces the bed: fade the bed out over 0.6 s, play the original, resume the bed from the beat where it paused.
Normalise the final mix to -14 LUFS (`finalize.sh`).
