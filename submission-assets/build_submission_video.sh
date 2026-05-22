#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ASSET_DIR="$ROOT_DIR/submission-assets"
SCREEN_DIR="$ASSET_DIR/screenshots"
VIDEO_DIR="$ASSET_DIR/video"
TMP_DIR="$ASSET_DIR/.video-tmp"
FONT_FILE="/System/Library/Fonts/Supplemental/Arial.ttf"

mkdir -p "$VIDEO_DIR" "$TMP_DIR"
rm -f "$TMP_DIR"/*.mp4 "$TMP_DIR"/*.txt "$TMP_DIR"/*.aiff

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

durations=(12 14 14 13 13 16 16 16)

captions=(
  "GBIF records to a defensible decision memo."
  "Presentation: live status, verdict, map, safe and blocked claims."
  "Workbench: taxonKey, region, purpose and generate."
  "GBIF taxon search locks the run to taxonKey 1651430."
  "Region presets and bbox fields keep the workflow reusable."
  "Evidence Passport: score, memo, records, risks and next action."
  "Claim guardrails: no-evidence cells are not absence."
  "Evidence Pack: citations, quality files, publisher feedback and JSON."
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

say -v Samantha -r 172 -o "$TMP_DIR/voiceover.aiff" -f "$ASSET_DIR/video-voiceover.txt"

ffmpeg -hide_banner -y \
  -f concat -safe 0 -i "$TMP_DIR/segments.txt" \
  -i "$TMP_DIR/voiceover.aiff" \
  -map 0:v:0 -map 1:a:0 \
  -c:v libx264 -pix_fmt yuv420p \
  -c:a aac -b:a 160k \
  -af "afade=t=in:st=0:d=0.5,afade=t=out:st=112:d=2" \
  -movflags +faststart \
  "$VIDEO_DIR/ecogenesis-evidence-atlas-demo.mp4"

cp "$ASSET_DIR/demo-video-captions.srt" "$VIDEO_DIR/ecogenesis-evidence-atlas-demo.srt"

ffprobe -v error -show_entries format=duration,size -of default=noprint_wrappers=1 "$VIDEO_DIR/ecogenesis-evidence-atlas-demo.mp4"
