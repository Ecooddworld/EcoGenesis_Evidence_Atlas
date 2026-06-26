#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ASSET_DIR="$ROOT_DIR/submission-assets/platform-video"
SCREEN_DIR="$ASSET_DIR/screenshots-scroll"
TMP_DIR="$ASSET_DIR/.video-tmp"
OUT_DIR="$ASSET_DIR/video"
FONT_FILE="/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
SUB_FONT_NAME="Arial Unicode MS"
VOICE="${VOICE:-Milena}"

mkdir -p "$TMP_DIR" "$OUT_DIR"
rm -f "$TMP_DIR"/*.mp4 "$TMP_DIR"/*.txt "$TMP_DIR"/*.aiff "$TMP_DIR"/segments.txt

if [[ ! -f "$FONT_FILE" ]]; then
  FONT_FILE="/Library/Fonts/Arial Unicode.ttf"
fi

if ! say -v '?' | awk '{print $1}' | grep -qx "$VOICE"; then
  VOICE="Milena"
fi
if ! say -v '?' | awk '{print $1}' | grep -qx "$VOICE"; then
  VOICE="Anna"
fi

images=(
  "$SCREEN_DIR/01-workflow-full.png"
  "$SCREEN_DIR/02-overview-full.png"
  "$SCREEN_DIR/03-run-compiler-full.png"
  "$SCREEN_DIR/04-evidence-map-home-full.png"
  "$SCREEN_DIR/05-evidence-map-graph-full.png"
  "$SCREEN_DIR/06-evidence-map-exports-full.png"
  "$SCREEN_DIR/07-evidence-map-judge-full.png"
  "$SCREEN_DIR/08-fragment-graph-full.png"
  "$SCREEN_DIR/09-validation-full.png"
  "$SCREEN_DIR/10-methods-audits-full.png"
  "$SCREEN_DIR/11-evidence-pack-full.png"
)

scroll_start_y=(
  0
  0
  0
  0
  0
  0
  0
  0
  0
  0
  0
)

scroll_end_y=(
  10478
  4889
  7754
  3740
  3899
  3656
  4520
  1697
  3240
  12000
  1427
)

subtitle_captions=(
  "Workflow scrolls from molecular input to Evidence Pack, map and graph."
  "Overview states the product claim and exposes the public source repository."
  "Run Compiler shows input, validation, hard gates, decisions, blockers and repairs."
  "Evidence Map links GBIF context, claim states, blockers and export boundaries."
  "Evidence Graph keeps provenance visible and cannot upgrade weak or blocked claims."
  "Evidence Map exports package VSEA, graph, GBIF preview and AI guardrail files."
  "Judge view exposes contest readiness, verification reports and adversarial packs."
  "Fragment Graph checks a marker fragment, hit comparison and safest LCA."
  "Validation shows batch, adversarial, graph, VSEA and export guardrail checks."
  "Methods and Audits document gates, failure modes and publication boundaries."
  "Evidence Pack exports CSV, JSON, HTML, VSEA, graph and audit files for reuse."
)

python3 - "$ASSET_DIR/voiceover-ru.txt" "$TMP_DIR" "${#images[@]}" <<'PY'
from pathlib import Path
import sys

voiceover = Path(sys.argv[1])
tmp_dir = Path(sys.argv[2])
expected = int(sys.argv[3])
segments = [part.strip().replace("\n", " ") for part in voiceover.read_text(encoding="utf-8").split("\n\n") if part.strip()]
if len(segments) != expected:
    raise SystemExit(f"Expected {expected} voice segments, found {len(segments)}")
for idx, segment in enumerate(segments, 1):
    (tmp_dir / f"voice_{idx:02}.txt").write_text(segment + "\n", encoding="utf-8")
PY

make_scroll_video() {
  local index="$1"
  local duration="$2"
  local image_file="$3"
  local start_y="$4"
  local requested_end_y="$5"
  local output="$TMP_DIR/video_${index}.mp4"

  if [[ ! -f "$image_file" ]]; then
    echo "Missing screenshot: $image_file" >&2
    exit 1
  fi

  local image_height
  image_height="$(ffprobe -v error -select_streams v:0 -show_entries stream=height -of csv=p=0 "$image_file")"
  local max_y=$((image_height > 720 ? image_height - 720 : 0))
  local end_y="$requested_end_y"
  if (( end_y > max_y )); then
    end_y="$max_y"
  fi
  if (( start_y > max_y )); then
    start_y="$max_y"
  fi

  ffmpeg -hide_banner -loglevel error -y \
    -loop 1 -t "$duration" -i "$image_file" \
    -vf "scale=1280:-2,crop=1280:720:0:'${start_y}+(${end_y}-${start_y})*t/${duration}'" \
    -r 30 -c:v libx264 -crf 25 -preset medium -pix_fmt yuv420p "$output" >/dev/null
}

computed_durations=()

for i in "${!images[@]}"; do
  index="$(printf '%02d' "$((i + 1))")"
  voice_file="$TMP_DIR/voice_${index}.txt"
  audio_file="$TMP_DIR/voice_${index}.aiff"
  say -v "$VOICE" -r 166 -o "$audio_file" -f "$voice_file"

  audio_duration="$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$audio_file")"
  duration="$(python3 - "$audio_duration" <<'PY'
import math
import sys
print(math.ceil(float(sys.argv[1]) + 0.9))
PY
)"
  computed_durations+=("$duration")

  make_scroll_video "$index" "$duration" "${images[$i]}" "${scroll_start_y[$i]}" "${scroll_end_y[$i]}"

  ffmpeg -hide_banner -loglevel error -y \
    -i "$TMP_DIR/video_${index}.mp4" \
    -i "$audio_file" \
    -map 0:v:0 -map 1:a:0 \
    -c:v copy -c:a aac -b:a 160k \
    "$TMP_DIR/segment_${index}.mp4" >/dev/null

  printf "file '%s'\n" "$TMP_DIR/segment_${index}.mp4" >> "$TMP_DIR/segments.txt"
done

printf '%s\n' "${subtitle_captions[@]}" > "$TMP_DIR/srt_captions.txt"
python3 - "$OUT_DIR/ecogenesis-platform-demo-ru-voice-subs.srt" "$TMP_DIR/srt_captions.txt" "${computed_durations[@]}" <<'PY'
from pathlib import Path
import sys

out = Path(sys.argv[1])
caption_file = Path(sys.argv[2])
durations = [float(item) for item in sys.argv[3:]]
captions = caption_file.read_text(encoding="utf-8").splitlines()

def fmt(t):
    ms = round(t * 1000)
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

cur = 0.0
parts = []
for idx, (duration, caption) in enumerate(zip(durations, captions), 1):
    start, end = cur, cur + duration
    parts.append(f"{idx}\n{fmt(start)} --> {fmt(end)}\n{caption}\n")
    cur = end
out.write_text("\n".join(parts), encoding="utf-8")
PY

ffmpeg -hide_banner -loglevel error -y \
  -f concat -safe 0 -i "$TMP_DIR/segments.txt" \
  -c copy -movflags +faststart \
  "$TMP_DIR/ecogenesis-platform-demo-no-subs.mp4" >/dev/null

ffmpeg -hide_banner -loglevel error -y \
  -i "$TMP_DIR/ecogenesis-platform-demo-no-subs.mp4" \
  -vf "subtitles='${OUT_DIR}/ecogenesis-platform-demo-ru-voice-subs.srt':force_style='FontName=${SUB_FONT_NAME},FontSize=14,PrimaryColour=&H00FFFFFF&,OutlineColour=&H00111D17&,BorderStyle=1,Outline=1,Shadow=0,MarginV=22'" \
  -c:v libx264 -crf 28 -preset medium -pix_fmt yuv420p -c:a copy -movflags +faststart \
  "$OUT_DIR/ecogenesis-platform-demo-ru-voice-subs.mp4" >/dev/null

cp "$ASSET_DIR/voiceover-ru.txt" "$OUT_DIR/ecogenesis-platform-demo-ru-voiceover.txt"

ffmpeg -hide_banner -loglevel error -y -ss 00:00:16 \
  -i "$OUT_DIR/ecogenesis-platform-demo-ru-voice-subs.mp4" \
  -frames:v 1 "$OUT_DIR/demo-thumbnail-platform-ru.png" >/dev/null 2>&1

ffprobe -v error -show_entries format=duration,size -of default=noprint_wrappers=1 "$OUT_DIR/ecogenesis-platform-demo-ru-voice-subs.mp4"
