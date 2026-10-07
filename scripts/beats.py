#!/usr/bin/env python3
"""Beat grid for a music track (librosa, phase-aligned to percussive onsets) and optional extension by whole bars.

Usage:
  python3 beats.py track.mp3 --bpm 112 --out beats.json                      # grid only
  python3 beats.py track.mp3 --bpm 112 --extend 12:16 --out beats.json --audio-out track_long.wav
     # repeat bars 12..15 once (inserted at bar 16), seamless 15 ms crossfade, beat grid rewritten

Prints tempo, beat jitter, and loudness per bar so section changes (drops, breaks, quiet bridges) are visible.
Why not `hyperframes beats`: on several tracks it returned a grid at a non-musical subdivision (e.g. 241 BPM for
an 85 BPM song). Always sanity-check: median beat interval should be stable (std < 0.02 s) and match by ear.
Cut on beats; offset each cut ~15 ms early so the picture change lands with the transient.
"""
import argparse, json, subprocess, numpy as np, librosa, soundfile as sf

ap = argparse.ArgumentParser(); ap.add_argument('track'); ap.add_argument('--bpm', type=float, required=True, help='approximate tempo (start hint)')
ap.add_argument('--out', required=True); ap.add_argument('--extend', default=None, help='A:B — repeat bars A..B-1 once, inserted at bar B')
ap.add_argument('--audio-out', default=None); A = ap.parse_args()

y, sr = librosa.load(A.track, sr=22050)
_, bt = librosa.beat.beat_track(y=y, sr=sr, start_bpm=A.bpm, tightness=300, units='time')
yp = librosa.effects.percussive(y); hop = 128
op = librosa.onset.onset_strength(y=yp, sr=sr, hop_length=hop); tt = librosa.frames_to_time(np.arange(len(op)), sr=sr, hop_length=hop)
offs = np.arange(-0.12, 0.121, 0.005); off = offs[int(np.argmax([np.interp(bt + d, tt, op).mean() for d in offs]))]; bt = bt + off
iv = np.diff(bt); print(f'tempo {60 / np.median(iv):.1f} BPM  jitter {iv.std():.3f}s  beats {len(bt)}  phase offset {off:+.3f}s  duration {len(y) / sr:.1f}s')
S = np.abs(librosa.stft(y, hop_length=512)); fq = librosa.fft_frequencies(sr=sr); t = librosa.frames_to_time(np.arange(S.shape[1]), sr=sr, hop_length=512)
low = S[fq < 150].sum(0); tot = S.sum(0)
for i in range(0, len(bt) - 4, 4):
    m = (t >= bt[i]) & (t < bt[i + 4]); print(f'bar{i // 4:3d} {bt[i]:7.2f}s  level {20 * np.log10(tot[m].mean()):5.1f}  low {20 * np.log10(low[m].mean()):5.1f}')
beats = [float(b) for b in bt]; dur = len(y) / sr
if A.extend:
    a, b = map(int, A.extend.split(':'))
    src = A.audio_out + '.src.wav'; subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', A.track, '-ar', '48000', '-ac', '2', src])
    Y, SR = sf.read(src); xf = int(0.015 * SR)
    ta, tb = beats[4 * b], beats[4 * a]; ia, ib = int(round(ta * SR)), int(round(tb * SR))
    head, tail = Y[:ia + xf], Y[ib:]; r = np.linspace(0, 1, xf)[:, None]
    out = np.concatenate([head[:-xf], head[-xf:] * (1 - r) + tail[:xf] * r, tail[xf:]]); sf.write(A.audio_out, out, SR)
    shift = ta - tb; beats = [x for x in beats if x < ta - 1e-3] + [x + shift for x in beats if x >= tb - 1e-3]; dur = len(out) / SR
    print(f'extended: +{shift:.2f}s -> {dur:.1f}s')
json.dump(dict(beats=[round(x, 4) for x in beats], bars=[round(beats[4 * n], 4) for n in range(len(beats) // 4)], duration=dur, phase_offset=float(off)), open(A.out, 'w'))
