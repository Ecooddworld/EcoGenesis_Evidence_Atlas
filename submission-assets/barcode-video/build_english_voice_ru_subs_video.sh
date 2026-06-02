#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VIDEO_ASSET_DIR="$ROOT_DIR/submission-assets/barcode-video"
SCREEN_DIR="$VIDEO_ASSET_DIR/screenshots"
TMP_DIR="$VIDEO_ASSET_DIR/.video-tmp"
OUT_DIR="$VIDEO_ASSET_DIR/video"
FONT_FILE="/System/Library/Fonts/Supplemental/Arial.ttf"
SUB_FONT_NAME="Arial Unicode MS"
VOICE="${VOICE:-Samantha}"

mkdir -p "$TMP_DIR" "$OUT_DIR"
rm -f "$TMP_DIR"/*.mp4 "$TMP_DIR"/*.txt "$TMP_DIR"/*.aiff "$TMP_DIR"/segments.txt

if [[ ! -f "$FONT_FILE" ]]; then
  FONT_FILE="/Library/Fonts/Arial Unicode.ttf"
fi

if ! say -v '?' | awk '{print $1}' | grep -qx "$VOICE"; then
  VOICE="Samantha"
fi

make_text_segment() {
  local index="$1"
  local duration="$2"
  local text_file="$3"
  local output="$TMP_DIR/segment_${index}.mp4"

  ffmpeg -hide_banner -loglevel error -y \
    -f lavfi -i "color=c=0xf3f7f1:s=1280x720:d=${duration}" \
  -vf "drawbox=x=0:y=0:w=1280:h=720:color=0xf3f7f1:t=fill,drawbox=x=0:y=0:w=1280:h=9:color=0x1e6b78:t=fill,drawtext=fontfile='${FONT_FILE}':textfile='${text_file}':fontcolor=0x14231d:fontsize=38:line_spacing=15:x=70:y=110,drawtext=fontfile='${FONT_FILE}':text='EcoGenesis for GBIF Ebbe Nielsen Challenge 2026':fontcolor=0x476158:fontsize=22:x=70:y=44" \
    -r 30 -c:v libx264 -pix_fmt yuv420p "$output" >/dev/null
  printf "file '%s'\n" "$output" >> "$TMP_DIR/segments.txt"
}

make_screenshot_segment() {
  local index="$1"
  local duration="$2"
  local image_file="$3"
  local caption_file="$4"
  local output="$TMP_DIR/segment_${index}.mp4"

  if [[ ! -f "$image_file" ]]; then
    echo "Missing screenshot: $image_file" >&2
    exit 1
  fi

  ffmpeg -hide_banner -loglevel error -y \
    -loop 1 -t "$duration" -i "$image_file" \
    -vf "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,drawbox=x=0:y=0:w=1280:h=74:color=0x123F32@0.86:t=fill,drawtext=fontfile='${FONT_FILE}':textfile='${caption_file}':fontcolor=white:fontsize=24:line_spacing=6:x=42:y=22" \
    -r 30 -c:v libx264 -pix_fmt yuv420p "$output" >/dev/null
  printf "file '%s'\n" "$output" >> "$TMP_DIR/segments.txt"
}

make_text_segment "01" 18 "$VIDEO_ASSET_DIR/slides/01-title.txt"
make_text_segment "02" 22 "$VIDEO_ASSET_DIR/slides/02-problem.txt"
make_screenshot_segment "03" 28 "$SCREEN_DIR/01-judge-overview.png" "$VIDEO_ASSET_DIR/captions/03-overview.txt"
make_screenshot_segment "04" 40 "$SCREEN_DIR/02-run-compiler-upload.png" "$VIDEO_ASSET_DIR/captions/04-upload.txt"
make_screenshot_segment "05" 27 "$SCREEN_DIR/03-run-compiler-result.png" "$VIDEO_ASSET_DIR/captions/05-result.txt"
make_screenshot_segment "06" 10 "$SCREEN_DIR/04-result-details.png" "$VIDEO_ASSET_DIR/captions/06-exports.txt"
make_screenshot_segment "07" 18 "$SCREEN_DIR/05-math-proof-top.png" "$VIDEO_ASSET_DIR/captions/07-math.txt"
make_screenshot_segment "08" 18 "$SCREEN_DIR/06-math-proof-formulas.png" "$VIDEO_ASSET_DIR/captions/08-formulas.txt"
make_screenshot_segment "09" 17 "$SCREEN_DIR/07-research-audit.png" "$VIDEO_ASSET_DIR/captions/09-audit.txt"
make_text_segment "10" 17 "$VIDEO_ASSET_DIR/slides/10-platform-benefits.txt"
make_text_segment "11" 10 "$VIDEO_ASSET_DIR/slides/11-boundaries.txt"
make_text_segment "12" 15 "$VIDEO_ASSET_DIR/slides/12-closing.txt"

say -v "$VOICE" -r 168 -o "$TMP_DIR/voiceover.aiff" -f "$VIDEO_ASSET_DIR/english-voiceover.txt"

ffmpeg -hide_banner -loglevel error -y \
  -f concat -safe 0 -i "$TMP_DIR/segments.txt" \
  -i "$TMP_DIR/voiceover.aiff" \
  -map 0:v:0 -map 1:a:0 \
  -c:v libx264 -pix_fmt yuv420p \
  -c:a aac -b:a 160k \
  -af "afade=t=in:st=0:d=0.4" \
  -movflags +faststart \
  "$TMP_DIR/ecogenesis-barcode-to-gbif-no-subs.mp4" >/dev/null

ffmpeg -hide_banner -loglevel error -y \
  -i "$TMP_DIR/ecogenesis-barcode-to-gbif-no-subs.mp4" \
  -vf "subtitles='${VIDEO_ASSET_DIR}/russian-subtitles.srt':force_style='FontName=${SUB_FONT_NAME},FontSize=15,PrimaryColour=&H00FFFFFF&,OutlineColour=&H00111D17&,BorderStyle=1,Outline=1,Shadow=0,MarginV=24'" \
  -c:v libx264 -pix_fmt yuv420p -c:a copy -movflags +faststart \
  "$OUT_DIR/ecogenesis-barcode-to-gbif-english-voice-ru-subs.mp4" >/dev/null

cp "$VIDEO_ASSET_DIR/russian-subtitles.srt" "$OUT_DIR/ecogenesis-barcode-to-gbif-english-voice-ru-subs.srt"
cp "$VIDEO_ASSET_DIR/english-voiceover.txt" "$OUT_DIR/ecogenesis-barcode-to-gbif-english-voiceover.txt"

ffmpeg -hide_banner -loglevel error -y -ss 00:00:35 \
  -i "$OUT_DIR/ecogenesis-barcode-to-gbif-english-voice-ru-subs.mp4" \
  -frames:v 1 "$OUT_DIR/demo-thumbnail-english-voice-ru-subs.png" >/dev/null 2>&1

ffprobe -v error -show_entries format=duration,size -of default=noprint_wrappers=1 "$OUT_DIR/ecogenesis-barcode-to-gbif-english-voice-ru-subs.mp4"
