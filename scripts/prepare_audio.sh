#!/usr/bin/env bash
# Convert phone recordings in data/own50/raw/ into 16 kHz mono WAV clips.
# Numbering continues after the clips that already exist. Converted raw files are
# moved to data/own50/raw_done/ so they are never converted twice.
# Files that hold no audio (for example Windows ":Zone.Identifier" files) are skipped.
set -uo pipefail

RAW=data/own50/raw
OUT=data/own50/audio
DONE=data/own50/raw_done
mkdir -p "$RAW" "$OUT" "$DONE"

n=$(find "$OUT" -maxdepth 1 -name 'clip_*.wav' | wc -l)
for f in "$RAW"/*; do
  [ -f "$f" ] || continue
  name=$(basename "$f")
  case "$name" in
    *:Zone.Identifier) rm -f "$f"; continue ;;
  esac
  if ! ffprobe -v error -select_streams a:0 -show_entries stream=codec_type \
      -of csv=p=0 "$f" 2>/dev/null | grep -q audio; then
    echo "skipped (no audio found): $name"
    continue
  fi
  id=$(printf "clip_%03d" $((n + 1)))
  if ffmpeg -loglevel error -y -i "$f" -ar 16000 -ac 1 "$OUT/$id.wav"; then
    n=$((n + 1))
    mv "$f" "$DONE/"
    echo "$id.wav <- $name"
  else
    rm -f "$OUT/$id.wav"
    echo "FAILED: $name"
  fi
done
echo "Total clips: $(find "$OUT" -maxdepth 1 -name 'clip_*.wav' | wc -l)"
