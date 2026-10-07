#!/usr/bin/env python3
"""Per-clip speech and wind scan, so ambient sound is only used where nobody talks and the mic is not buffeted.

Usage:
  python3 audio_scan.py --inventory work/inventory.json --out work/audio.json [--lang pl] [--only-video]

For every video: transcribes with `npx hyperframes transcribe` (word timestamps) and measures, per second,
the share of energy below 200 Hz (wind rumble) plus RMS. Prints a strip per clip: W = heavy wind, w = some,
. = clean. Use `speech` spans to cut dialogue and pick ambience from clean seconds only.
"""
import argparse, json, os, subprocess, wave, numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('--inventory', required=True); ap.add_argument('--out', required=True); ap.add_argument('--lang', default=None)
ap.add_argument('--work', default=None)
A = ap.parse_args()
R = json.load(open(A.inventory)); work = A.work or os.path.join(os.path.dirname(os.path.abspath(A.out)), 'asr'); os.makedirs(work, exist_ok=True)
res = json.load(open(A.out)) if os.path.exists(A.out) else {}
for r in R:
    if r['ext'] not in ('mp4', 'mov') or r.get('live_photo_of'): continue
    key = os.path.splitext(r['file'])[0]
    if key in res: continue
    d = os.path.join(work, key); os.makedirs(d, exist_ok=True); wav = os.path.join(d, 'a.wav')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', r['path'], '-vn', '-ac', '1', '-ar', '16000', wav])
    if not os.path.exists(wav) or os.path.getsize(wav) < 2000: continue
    cmd = ['npx', 'hyperframes', 'transcribe', wav, '-d', d, '--json'] + (['-l', A.lang] if A.lang else [])
    subprocess.run(cmd, capture_output=True)
    words = []
    try:
        t = json.load(open(os.path.join(d, 'transcript.json'))); words = t if isinstance(t, list) else t.get('words', [])
    except Exception: pass
    speech = [(w['start'], w['end'], w.get('text', '')) for w in words if w.get('text', '').strip('.,!? ')]
    wf = wave.open(wav); a = np.frombuffer(wf.readframes(wf.getnframes()), np.int16).astype(np.float32) / 32768; sr = wf.getframerate()
    wind, rms = [], []
    for i in range(0, len(a) - sr, sr):
        x = a[i:i + sr] * np.hanning(sr); F = np.abs(np.fft.rfft(x)) ** 2; f = np.fft.rfftfreq(sr, 1 / sr)
        wind.append(round(float(F[f < 200].sum() / (F[f > 20].sum() + 1e-12)), 3))
        rms.append(round(float(20 * np.log10(np.sqrt((a[i:i + sr] ** 2).mean()) + 1e-9)), 1))
    res[key] = dict(speech=speech, wind=wind, rms=rms)
    strip = ''.join('W' if x > 0.6 else 'w' if x > 0.35 else '.' for x in wind)
    print(f'{key:12s} words {len(speech):3d} {strip[:80]}', flush=True)
    json.dump(res, open(A.out, 'w'))
print('done', len(res))
