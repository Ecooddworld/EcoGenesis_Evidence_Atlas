#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ASSET_DIR="$ROOT_DIR/submission-assets/contest-video-v3"
CAPTURE_DIR="$ASSET_DIR/captures-v4"
BRAND_MARK="$ASSET_DIR/generated/00-brand-mark.png"
VOICEOVER_TEXT="$ASSET_DIR/voiceover-scientific-en.txt"
SUBTITLE_FILE="$ASSET_DIR/voiceover-scientific-en.srt"
TMP_DIR="$ASSET_DIR/.scientific-video-tmp"
OUT_DIR="$ASSET_DIR/video"
OUTPUT_FILE="$OUT_DIR/ecogenesis-v2-scientific-walkthrough-en-subs.mp4"

FONT_REGULAR="/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_BOLD="/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_DIR="/System/Library/Fonts/Supplemental"

VOICE="${VOICE:-Samantha}"
VOICE_RATE="${VOICE_RATE:-165}"
OPENER_SECONDS="${OPENER_SECONDS:-3.5}"
CLOSING_SECONDS="${CLOSING_SECONDS:-3.5}"
CAPTURE_SEQUENCE="${CAPTURE_SEQUENCE:-run-input,run-results,pack,map,graph,methods,workflow}"
MAX_SUBTITLE_LINE_CHARS="${MAX_SUBTITLE_LINE_CHARS:-64}"

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || die "Required command not found: $1"
}

require_nonempty_file() {
  [[ -s "$1" ]] || die "Required file is missing or empty: $1"
}

is_positive_number() {
  awk -v value="$1" 'BEGIN { exit !(value ~ /^[0-9]+([.][0-9]+)?$/ && value > 0) }'
}

require_command ffmpeg
require_command ffprobe
require_command python3

is_positive_number "$OPENER_SECONDS" || die "OPENER_SECONDS must be a positive number"
is_positive_number "$CLOSING_SECONDS" || die "CLOSING_SECONDS must be a positive number"
is_positive_number "$VOICE_RATE" || die "VOICE_RATE must be a positive number"

require_nonempty_file "$BRAND_MARK"
require_nonempty_file "$VOICEOVER_TEXT"
require_nonempty_file "$SUBTITLE_FILE"
require_nonempty_file "$FONT_REGULAR"
require_nonempty_file "$FONT_BOLD"

IFS=',' read -r -a raw_capture_names <<< "$CAPTURE_SEQUENCE"
capture_names=()
capture_files=()
for raw_name in "${raw_capture_names[@]}"; do
  name="${raw_name//[[:space:]]/}"
  [[ -n "$name" ]] || continue
  [[ "$name" =~ ^[A-Za-z0-9._-]+$ ]] || die "Unsafe capture name: $name"
  capture_names+=("$name")
  capture_files+=("$CAPTURE_DIR/$name.webm")
done

(( ${#capture_files[@]} > 0 )) || die "CAPTURE_SEQUENCE did not contain any clip names"

total_capture_seconds="0"
for clip in "${capture_files[@]}"; do
  require_nonempty_file "$clip"

  dimensions="$(
    ffprobe -v error -select_streams v:0 \
      -show_entries stream=width,height \
      -of csv=s=x:p=0 "$clip"
  )"
  [[ "$dimensions" == "1920x1080" ]] || {
    die "Capture must already be 1920x1080; crop and zoom are intentionally disabled: $clip ($dimensions)"
  }

  duration="$(
    ffprobe -v error -show_entries format=duration \
      -of default=noprint_wrappers=1:nokey=1 "$clip"
  )"
  is_positive_number "$duration" || die "Capture has no positive duration: $clip"
  total_capture_seconds="$(awk -v total="$total_capture_seconds" -v item="$duration" 'BEGIN { printf "%.6f", total + item }')"
done

video_duration="$(
  awk -v opening="$OPENER_SECONDS" -v captures="$total_capture_seconds" -v closing="$CLOSING_SECONDS" \
    'BEGIN { printf "%.6f", opening + captures + closing }'
)"

srt_end_seconds="$(python3 - "$SUBTITLE_FILE" "$MAX_SUBTITLE_LINE_CHARS" <<'PY'
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
max_chars = int(sys.argv[2])
text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").strip()
if not text:
    raise SystemExit(f"Subtitle file is empty: {path}")

timestamp = re.compile(
    r"^(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s+-->\s+"
    r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})"
)

def seconds(parts):
    hours, minutes, secs, millis = map(int, parts)
    return hours * 3600 + minutes * 60 + secs + millis / 1000

last_end = 0.0
previous_start = -1.0
cues = 0
for block in re.split(r"\n\s*\n", text):
    lines = [line.rstrip() for line in block.splitlines()]
    timeline_index = next((i for i, line in enumerate(lines) if "-->" in line), None)
    if timeline_index is None:
        raise SystemExit(f"Subtitle cue has no timeline: {block!r}")
    match = timestamp.match(lines[timeline_index].strip())
    if not match:
        raise SystemExit(f"Invalid subtitle timeline: {lines[timeline_index]!r}")

    start = seconds(match.groups()[:4])
    end = seconds(match.groups()[4:])
    if end <= start:
        raise SystemExit(f"Subtitle cue ends before it starts: {lines[timeline_index]!r}")
    if start < previous_start:
        raise SystemExit(f"Subtitle cues are not chronological: {lines[timeline_index]!r}")

    caption_lines = [line for line in lines[timeline_index + 1:] if line.strip()]
    if not caption_lines or len(caption_lines) > 2:
        raise SystemExit(
            f"Every subtitle cue must contain one or two text lines; found {len(caption_lines)} in: {block!r}"
        )
    for line in caption_lines:
        if len(re.sub(r"<[^>]+>", "", line)) > max_chars:
            raise SystemExit(
                f"Subtitle line exceeds {max_chars} characters and may wrap to a third line: {line!r}"
            )

    previous_start = start
    last_end = max(last_end, end)
    cues += 1

if cues == 0:
    raise SystemExit("Subtitle file contains no cues")

print(f"{last_end:.3f}")
PY
)"

awk -v subtitles="$srt_end_seconds" -v video="$video_duration" \
  'BEGIN { exit !(subtitles <= video + 0.10) }' || {
    die "Subtitles end at ${srt_end_seconds}s, after the ${video_duration}s video sequence"
  }

rm -rf "$TMP_DIR"
mkdir -p "$TMP_DIR" "$OUT_DIR"

printf '%s\n' 'EVIDENCE-BOUNDED SCIENTIFIC WALKTHROUGH' > "$TMP_DIR/opener-eyebrow.txt"
printf '%s\n' 'EcoGenesis V2' > "$TMP_DIR/opener-title.txt"
printf '%s\n' 'Barcode-to-GBIF Evidence Compiler' > "$TMP_DIR/opener-subtitle.txt"
printf '%s\n' 'DNA INPUT   —   RULE GATES   —   BOUNDED RANK   —   EVIDENCE PACK' > "$TMP_DIR/evidence-flow.txt"
printf '%s\n' 'Inspect the evidence. Preserve the boundary.' > "$TMP_DIR/closing-title.txt"
printf '%s\n' 'ecooddworld.eu' > "$TMP_DIR/closing-url.txt"
printf '%s\n' 'V2 · evidence-bounded release · reproducible outputs' > "$TMP_DIR/closing-release.txt"

if [[ -n "${NARRATION_AUDIO:-}" ]]; then
  narration_audio="$NARRATION_AUDIO"
  require_nonempty_file "$narration_audio"
else
  require_command say
  narration_audio="$TMP_DIR/voiceover-scientific-en.aiff"
  say -v "$VOICE" -r "$VOICE_RATE" -o "$narration_audio" -f "$VOICEOVER_TEXT"
fi

narration_duration="$(
  ffprobe -v error -show_entries format=duration \
    -of default=noprint_wrappers=1:nokey=1 "$narration_audio"
)"
is_positive_number "$narration_duration" || die "Narration has no positive duration: $narration_audio"

awk -v audio="$narration_duration" -v video="$video_duration" \
  'BEGIN { exit !(audio <= video + 0.75) }' || {
    die "Narration (${narration_duration}s) is longer than the video sequence (${video_duration}s)"
  }

awk -v audio="$narration_duration" -v video="$video_duration" \
  'BEGIN { exit !((video - audio) > 8.0) }' && {
    printf 'WARNING: video is %.2fs longer than narration; verify the intended closing silence.\n' \
      "$(awk -v audio="$narration_duration" -v video="$video_duration" 'BEGIN { print video - audio }')" >&2
  } || true

ffmpeg_inputs=(
  -loop 1 -framerate 30 -i "$BRAND_MARK"
)
for clip in "${capture_files[@]}"; do
  ffmpeg_inputs+=( -i "$clip" )
done
audio_input_index=$(( ${#capture_files[@]} + 1 ))
ffmpeg_inputs+=( -i "$narration_audio" )

closing_label_index=$(( ${#capture_files[@]} + 1 ))
scene_count=$(( ${#capture_files[@]} + 2 ))
closing_fade_start="$(awk -v duration="$CLOSING_SECONDS" 'BEGIN { value = duration - 0.55; if (value < 0) value = 0; printf "%.3f", value }')"

filter_parts=()
filter_parts+=(
  "[0:v]fps=30,split=2[brand_open_source][brand_close_source]"
  "[brand_open_source]scale=320:320:flags=lanczos,trim=duration=${OPENER_SECONDS},setpts=PTS-STARTPTS[brand_open]"
  "[brand_close_source]scale=210:210:flags=lanczos,trim=duration=${CLOSING_SECONDS},setpts=PTS-STARTPTS[brand_close]"
  "color=c=0x061512:s=1920x1080:r=30:d=${OPENER_SECONDS},format=yuv420p,drawgrid=width=120:height=120:thickness=1:color=0x45A884@0.12,drawbox=x=560:y=657:w=1190:h=2:color=0x45A884@0.45:t=fill,drawtext=fontfile='${FONT_BOLD}':textfile='${TMP_DIR}/opener-eyebrow.txt':fontcolor=0x9FE4BE:fontsize=23:x=565:y=315,drawtext=fontfile='${FONT_BOLD}':textfile='${TMP_DIR}/opener-title.txt':fontcolor=white:fontsize=78:x=560:y=356,drawtext=fontfile='${FONT_REGULAR}':textfile='${TMP_DIR}/opener-subtitle.txt':fontcolor=0xD7F3E3:fontsize=37:x=565:y=470,drawtext=fontfile='${FONT_BOLD}':textfile='${TMP_DIR}/evidence-flow.txt':fontcolor=0x8EDCB4:fontsize=22:x=565:y=686[open_background]"
  "[open_background][brand_open]overlay=x=145:y=357:shortest=1,fade=t=in:st=0:d=0.40[v0]"
)

for index in "${!capture_files[@]}"; do
  input_index=$(( index + 1 ))
  output_index=$(( index + 1 ))
  filter_parts+=(
    "[${input_index}:v]fps=30,setsar=1,setpts=PTS-STARTPTS,format=yuv420p[v${output_index}]"
  )
done

filter_parts+=(
  "color=c=0x061512:s=1920x1080:r=30:d=${CLOSING_SECONDS},format=yuv420p,drawgrid=width=120:height=120:thickness=1:color=0x45A884@0.12,drawtext=fontfile='${FONT_BOLD}':textfile='${TMP_DIR}/closing-title.txt':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=480,drawtext=fontfile='${FONT_BOLD}':textfile='${TMP_DIR}/closing-url.txt':fontcolor=0x9FE4BE:fontsize=38:x=(w-text_w)/2:y=565,drawtext=fontfile='${FONT_REGULAR}':textfile='${TMP_DIR}/closing-release.txt':fontcolor=0xCBE9D8:fontsize=24:x=(w-text_w)/2:y=627[close_background]"
  "[close_background][brand_close]overlay=x=(W-w)/2:y=225:shortest=1,fade=t=out:st=${closing_fade_start}:d=0.55[v${closing_label_index}]"
)

concat_inputs=""
for (( index = 0; index < scene_count; index += 1 )); do
  concat_inputs+="[v${index}]"
done

subtitle_style="FontName=Arial,FontSize=7,PrimaryColour=&H00FFFFFF,OutlineColour=&H9005120E,BackColour=&H9005120E,BorderStyle=3,Outline=1,Shadow=0,Alignment=2,MarginL=28,MarginR=28,MarginV=10"
filter_parts+=(
  "${concat_inputs}concat=n=${scene_count}:v=1:a=0[stitched]"
  "[stitched]subtitles='${SUBTITLE_FILE}':fontsdir='${FONT_DIR}':force_style='${subtitle_style}',format=yuv420p[vout]"
  "[${audio_input_index}:a]aresample=48000,aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,loudnorm=I=-16:TP=-1.5:LRA=7,apad[aout]"
)

filter_complex="$(IFS=';'; printf '%s' "${filter_parts[*]}")"
partial_output="$TMP_DIR/ecogenesis-v2-scientific-walkthrough.partial.mp4"

ffmpeg -hide_banner -y \
  "${ffmpeg_inputs[@]}" \
  -filter_complex "$filter_complex" \
  -map '[vout]' -map '[aout]' \
  -c:v libx264 -preset slow -crf 17 -profile:v high -level:v 4.2 \
  -pix_fmt yuv420p -r 30 -fps_mode cfr -g 60 -keyint_min 30 \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -c:a aac -b:a 192k -ar 48000 -ac 2 \
  -shortest -movflags +faststart -map_metadata -1 \
  -metadata title='EcoGenesis V2 — evidence-bounded scientific walkthrough' \
  -metadata:s:v:0 language=eng -metadata:s:a:0 language=eng \
  "$partial_output"

probe_json="$TMP_DIR/final-ffprobe.json"
ffprobe -v error -show_streams -show_format -of json "$partial_output" > "$probe_json"

python3 - "$probe_json" <<'PY'
import json
from fractions import Fraction
from pathlib import Path
import sys

probe = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
video = next((stream for stream in probe["streams"] if stream.get("codec_type") == "video"), None)
audio = next((stream for stream in probe["streams"] if stream.get("codec_type") == "audio"), None)
if video is None or audio is None:
    raise SystemExit("Final MP4 must contain one video stream and one audio stream")

checks = {
    "video codec": video.get("codec_name") == "h264",
    "video dimensions": (video.get("width"), video.get("height")) == (1920, 1080),
    "video pixel format": video.get("pix_fmt") == "yuv420p",
    "video frame rate": abs(float(Fraction(video.get("avg_frame_rate", "0/1"))) - 30.0) < 0.01,
    "audio codec": audio.get("codec_name") == "aac",
    "audio sample rate": int(audio.get("sample_rate", 0)) == 48000,
    "audio channels": int(audio.get("channels", 0)) == 2,
}
failed = [label for label, passed in checks.items() if not passed]
if failed:
    raise SystemExit("Final MP4 QA failed: " + ", ".join(failed))
PY

mv "$partial_output" "$OUTPUT_FILE"

printf 'Built: %s\n' "$OUTPUT_FILE"
ffprobe -v error \
  -show_entries format=duration,size,bit_rate \
  -show_entries stream=index,codec_type,codec_name,width,height,avg_frame_rate,pix_fmt,sample_rate,channels \
  -of default=noprint_wrappers=1 "$OUTPUT_FILE"
