#!/usr/bin/env bash
# Convert phone recordings in data/own50/raw/ into 16 kHz mono WAV clips.
# Numbering continues after the clips that already exist. Raw files are moved
# to data/own50/raw_done/ so they are never converted twice.
set -euo pipefail

RAW=data/own50/raw
OUT=data/own50/audio
DONE=data/own50/raw_done
mkdir -p "$RAW" "$OUT" "$DONE"

n=$(find "$OUT" -maxdepth 1 -name 'clip_*.wav' | wc -l)
for f in "$RAW"/*; do
  [ -f "$f" ] || continue
  n=$((n + 1))
  id=$(printf "clip_%03d" "$n")
  ffmpeg -loglevel error -y -i "$f" -ar 16000 -ac 1 "$OUT/$id.wav"
  mv "$f" "$DONE/"
  echo "$id.wav <- $(basename "$f")"
done
echo "Total clips: $(find "$OUT" -maxdepth 1 -name 'clip_*.wav' | wc -l)"
