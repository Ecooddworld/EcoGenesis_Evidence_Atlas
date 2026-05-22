#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RU_DIR="$ROOT_DIR/submission-assets/ru"
SCREEN_DIR="$ROOT_DIR/submission-assets/screenshots"
VIDEO_DIR="$RU_DIR/video"
TMP_DIR="$RU_DIR/.video-tmp"
FONT_FILE="/System/Library/Fonts/Supplemental/Arial Unicode.ttf"

mkdir -p "$VIDEO_DIR" "$TMP_DIR"
rm -f "$TMP_DIR"/*.mp4 "$TMP_DIR"/*.txt "$TMP_DIR"/*.aiff "$TMP_DIR"/segments.txt

frames=(
  "01-presentation.png"
  "02-workbench-inputs.png"
  "03-taxon-search.png"
  "04-selected-taxon.png"
  "05-region-selection.png"
  "06-generated-result.png"
  "07-map-claims.png"
  "08-advanced-evidence-files.png"
)

durations=(16 17 17 16 17 20 19 20)

captions=(
  "EcoGenesis показывает, какие решения реально поддерживают данные GBIF."
  "Карта с точками — еще не доказательство отсутствия, тренда или полной картины."
  "Пользователь выбирает вид, регион и цель. Инструмент строит паспорт доказательств."
  "Presentation: статус GBIF, вывод, карта, безопасные и заблокированные утверждения."
  "Workbench: реальный GBIF API, taxonKey, регион, bbox, цель и генерация."
  "Evidence Passport: score, memo, записи, риски, пробелы и следующий шаг."
  "Claim Guardrails: нет записей — не значит нет вида."
  "Evidence Pack: отчет, цитирование, quality files, publisher feedback и JSON."
)

for index in "${!frames[@]}"; do
  frame="$SCREEN_DIR/${frames[$index]}"
  segment="$TMP_DIR/segment_$index.mp4"
  caption_file="$TMP_DIR/caption_$index.txt"
  printf '%s\n' "${captions[$index]}" > "$caption_file"
  if [[ ! -f "$frame" ]]; then
    echo "Missing screenshot: $frame" >&2
    exit 1
  fi
  ffmpeg -hide_banner -y \
    -loop 1 -t "${durations[$index]}" -i "$frame" \
    -vf "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,format=yuv420p,drawbox=x=0:y=592:w=1280:h=128:color=0x123F32@0.78:t=fill,drawtext=fontfile='$FONT_FILE':textfile='$caption_file':fontcolor=white:fontsize=27:line_spacing=8:x=48:y=620:box=0" \
    -r 30 -c:v libx264 -pix_fmt yuv420p "$segment" >/dev/null
  printf "file '%s'\n" "$segment" >> "$TMP_DIR/segments.txt"
done

say -v Milena -r 170 -o "$TMP_DIR/voiceover.aiff" -f "$RU_DIR/russian-video-voiceover.txt"

ffmpeg -hide_banner -y \
  -f concat -safe 0 -i "$TMP_DIR/segments.txt" \
  -i "$TMP_DIR/voiceover.aiff" \
  -map 0:v:0 -map 1:a:0 \
  -c:v libx264 -pix_fmt yuv420p \
  -c:a aac -b:a 160k \
  -af "afade=t=in:st=0:d=0.5,afade=t=out:st=140:d=2" \
  -movflags +faststart \
  "$VIDEO_DIR/ecogenesis-evidence-atlas-demo-ru.mp4"

cp "$RU_DIR/russian-video-captions.srt" "$VIDEO_DIR/ecogenesis-evidence-atlas-demo-ru.srt"

ffmpeg -hide_banner -y -ss 00:01:15 -i "$VIDEO_DIR/ecogenesis-evidence-atlas-demo-ru.mp4" -frames:v 1 "$VIDEO_DIR/demo-thumbnail-ru.png" >/dev/null 2>&1
ffprobe -v error -show_entries format=duration,size -of default=noprint_wrappers=1 "$VIDEO_DIR/ecogenesis-evidence-atlas-demo-ru.mp4"
