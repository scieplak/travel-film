#!/bin/bash
# Memory-safe, session-independent 4K render of a long HyperFrames film.
#
# Usage (from anywhere):
#   HYPERFRAMES_RENDER_DETACHED=1 nohup perl -MPOSIX -e 'POSIX::setsid(); exec @ARGV' \
#     render_parts.sh <project_dir> <prefix> <final_output.mp4> > render.out 2>&1 < /dev/null & disown
#
# Expects in <project_dir>: <prefix>_part1.html … <prefix>_partN.html (video only, 4K) and <prefix>_audio.html
# (all audio, whole length, no video). Renders the parts ONE AT A TIME with 2 workers, the audio pass separately,
# concatenates with stream copy, muxes the audio, normalises loudness to -14 LUFS, repairs isolated black frames,
# verifies the result. Progress: <project_dir>/<prefix>_render.status (last line ALLDONE = finished).
#
# Why: one 5–9 min 4K render with all source videos at once filled 32 GB of RAM and shut the Mac down; a background
# render started from an agent shell also dies with the session ("render_cancelled_parent_exited") unless it is
# started in its own session (setsid) with HYPERFRAMES_RENDER_DETACHED=1. The memory guard stops the render if
# free+inactive memory stays below MIN_FREE_MB for 15 s; finished parts are kept, so a rerun resumes.
set -u
PROJ=$(cd "$1" && pwd); PFX=$2; OUT=$3
HERE=$(cd "$(dirname "$0")" && pwd)
PY=${TRAVEL_FILM_PYTHON:-python3}
MIN_FREE_MB=${MIN_FREE_MB:-2500}; WORKERS=${WORKERS:-2}
export HYPERFRAMES_RENDER_DETACHED=1
cd "$PROJ"; mkdir -p "renders/$PFX"
ST="$PROJ/${PFX}_render.status"; echo "START $(date)" > "$ST"
avail_mb(){ vm_stat | awk '/Pages free/{f=$3} /Pages inactive/{i=$3} /Pages speculative/{s=$3} END{gsub("\\.","",f);gsub("\\.","",i);gsub("\\.","",s); print int((f+i+s)*16384/1048576)}'; }
run(){ # $1 composition  $2 output  $3 extra render args
  [ -s "$2" ] && { echo "SKIP $2" >> "$ST"; return 0; }
  echo "RENDER $1 $(date +%T)" >> "$ST"
  caffeinate -i -s npx hyperframes render . -c "$1" $3 --fps 30 --quality delivery --workers "$WORKERS" --browser-timeout 300 --output "$2" > "$PROJ/renders/$PFX/$(basename "$1" .html).log" 2>&1 &
  pid=$!; low=0
  while kill -0 $pid 2>/dev/null; do
    a=$(avail_mb); echo "$(date +%T) $a" >> "$PROJ/renders/$PFX/mem.log"
    if [ "$a" -lt "$MIN_FREE_MB" ]; then low=$((low+1)); else low=0; fi
    if [ $low -ge 3 ]; then echo "MEMORY GUARD: stopped $1 (${a} MB free)" >> "$ST"; pkill -P $pid; kill $pid; pkill -f "hyperframes render"; exit 2; fi
    sleep 5
  done
  wait $pid; rc=$?; echo "EXIT $1 rc=$rc $(date +%T)" >> "$ST"; [ $rc -eq 0 ] || exit $rc
}
n=$(ls ${PFX}_part*.html | wc -l | tr -d ' ')
for i in $(seq 1 "$n"); do run "${PFX}_part$i.html" "renders/$PFX/p$i.mp4" "--resolution 4k"; done
run "${PFX}_audio.html" "renders/$PFX/audio.mp4" ""
( cd "renders/$PFX"; rm -f list.txt; for i in $(seq 1 "$n"); do echo "file 'p$i.mp4'" >> list.txt; done
  ffmpeg -v error -y -f concat -safe 0 -i list.txt -i audio.mp4 -map 0:v -map 1:a -c copy -movflags +faststart ../${PFX}_full.mp4 ) \
  && echo "MUX OK $(date +%T)" >> "$ST" || { echo "MUX FAIL" >> "$ST"; exit 3; }
"$HERE/finalize.sh" "renders/${PFX}_full.mp4" "$OUT" >> "$ST" 2>&1
"$PY" "$HERE/repair_black.py" "$OUT" > "renders/$PFX/repair.log" 2>&1; echo "REPAIR $(tail -1 renders/$PFX/repair.log)" >> "$ST"
"$PY" "$HERE/verify_render.py" "$OUT" --json "renders/$PFX/verify.json" > "renders/$PFX/verify.txt" 2>&1
ffmpeg -v error -y -i "$OUT" -vf "fps=1/4,scale=320:180,tile=12x12" -frames:v 1 "renders/$PFX/sheet.jpg"
echo "ALLDONE $(date)" >> "$ST"
