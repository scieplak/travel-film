#!/bin/bash
# Two-pass loudness normalisation to -14 LUFS (streaming standard), true peak -1 dBTP; video stream copied.
# Usage: finalize.sh in.mp4 out.mp4
set -e
IN="$1"; OUT="$2"; mkdir -p "$(dirname "$OUT")"
J=$(ffmpeg -hide_banner -i "$IN" -af loudnorm=I=-14:TP=-1.0:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
mi=$(echo "$J" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['input_i'],d['input_tp'],d['input_lra'],d['input_thresh'],d['target_offset'])")
read I TP LRA TH OFF <<< "$mi"
ffmpeg -v error -y -i "$IN" -map 0:v -map 0:a -c:v copy -af "loudnorm=I=-14:TP=-1.0:LRA=11:measured_I=$I:measured_TP=$TP:measured_LRA=$LRA:measured_thresh=$TH:offset=$OFF:linear=true,aresample=48000" -c:a aac -b:a 320k -movflags +faststart "$OUT"
echo "in I=$I TP=$TP -> $OUT"
