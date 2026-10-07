#!/usr/bin/env python3
"""Verify a finished film end to end: streams, black frames, frozen stretches, silence, loudness per 2 s.

Usage: python3 verify_render.py film.mp4 [--json report.json]

Reads the whole file once with ffmpeg (blackdetect, freezedetect, silencedetect, ebur128). Black frames
inside the film, silence where music should play, or a loudness dip are the things to look at; a freeze of
a few seconds is expected for still prints/collages and is reported only for context.
"""
import subprocess, json, sys, numpy as np

f = sys.argv[1]
out_json = sys.argv[sys.argv.index('--json') + 1] if '--json' in sys.argv else None
pr = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_entries',
                                'stream=codec_name,codec_type,width,height,r_frame_rate,pix_fmt,sample_rate,channels,color_primaries,color_transfer:format=duration,bit_rate,size',
                                '-of', 'json', f], capture_output=True, text=True).stdout)
dur = float(pr['format']['duration'])
r = subprocess.run(['ffmpeg', '-hide_banner', '-i', f, '-vf', 'scale=480:-2,blackdetect=d=0.25:pix_th=0.06,freezedetect=n=0.002:d=1.5',
                    '-af', 'silencedetect=n=-50dB:d=0.7,ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
events = [l.split(']')[-1].strip() for l in r.splitlines() if any(k in l for k in ('black_start', 'freeze_start', 'freeze_duration', 'silence_start', 'silence_end'))]
summ = r[r.rfind('Summary:'):]
I = next((float(l.split()[1]) for l in summ.splitlines() if l.strip().startswith('I:')), None)
M = []
for l in r.splitlines():
    if 'Parsed_ebur128' in l and ' t:' in l and ' M:' in l:
        try: M.append((float(l.split(' t:')[1].split()[0]), float(l.split(' M:')[1].split()[0])))
        except ValueError: pass
M = np.array(M) if M else np.zeros((0, 2))
loud = []
for t0 in np.arange(0, dur, 2.0):
    sel = M[(M[:, 0] >= t0) & (M[:, 0] < t0 + 2)][:, 1] if len(M) else []
    loud.append((int(t0), round(float(np.median(sel)), 1) if len(sel) else None))
print(json.dumps(pr, indent=1)[:900])
print('\n'.join(events))
print(f'Integrated loudness: {I} LUFS')
print('quiet 2 s windows (< -28 LUFS):', ' '.join(f'{t}:{v}' for t, v in loud if v is not None and v < -28))
if out_json:
    json.dump(dict(probe=pr, events=events, integrated=I, loudness_2s=loud), open(out_json, 'w'), indent=1)
