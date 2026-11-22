#!/usr/bin/env bash
# Podkłada pliki TTS pod film, każdy w swoim oknie czasowym.
# Użycie: ./podloz-lektora.sh [film] [katalog-z-wav] [wyjście]
set -euo pipefail

FILM="${1:-../docs/asystent-urzednika.mp4}"
DIR="${2:-lektor}"
OUT="${3:-../docs/asystent-urzednika-lektor.mp4}"

# start w milisekundach i nazwa pliku bez rozszerzenia
CUES=(
  "0 01"
  "6300 02"
  "15700 03"
  "19000 04a" "25300 04b" "31100 04c" "37800 04d"
  "45800 04e" "53500 04f" "61400 04g" "70300 04h"
  "75400 05"
  "81600 06"
  "87500 07"
  "93500 08"
  "99400 09"
)

[ -f "$FILM" ] || { echo "brak filmu: $FILM" >&2; exit 1; }

DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$FILM")

inputs=(-i "$FILM")
filters=""
mix=""
i=1

for cue in "${CUES[@]}"; do
  read -r start name <<< "$cue"
  file="$DIR/$name.wav"
  [ -f "$file" ] || { echo "brak pliku: $file" >&2; exit 1; }
  inputs+=(-i "$file")
  filters+="[$i:a]aformat=sample_rates=48000:channel_layouts=stereo,adelay=${start}|${start}[a$i];"
  mix+="[a$i]"
  i=$((i + 1))
done

n=$((i - 1))
filters+="${mix}amix=inputs=${n}:normalize=0:dropout_transition=0,apad[aout]"

ffmpeg -y "${inputs[@]}" \
  -filter_complex "$filters" \
  -map 0:v -map "[aout]" \
  -c:v copy -c:a aac -b:a 192k \
  -t "$DUR" \
  "$OUT"

echo "gotowe: $OUT"
