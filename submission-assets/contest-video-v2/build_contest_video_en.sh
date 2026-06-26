#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ASSET_DIR="$ROOT_DIR/submission-assets/contest-video-v2"
PPTX_SLIDE_DIR="$ASSET_DIR/pptx-slides"
SITE_DIR="$ASSET_DIR/site-screens"
TMP_DIR="$ASSET_DIR/.video-tmp"
OUT_DIR="$ASSET_DIR/video"
FONT_FILE="/System/Library/Fonts/Supplemental/Arial.ttf"
SUB_FONT_NAME="Arial"
VOICE="${VOICE:-Samantha}"

mkdir -p "$TMP_DIR" "$OUT_DIR"
rm -f "$TMP_DIR"/*.mp4 "$TMP_DIR"/*.txt "$TMP_DIR"/*.aiff "$TMP_DIR"/segments.txt

if [[ ! -f "$FONT_FILE" ]]; then
  FONT_FILE="/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
  SUB_FONT_NAME="Arial Unicode MS"
fi

if ! say -v '?' | awk '{print $1}' | grep -qx "$VOICE"; then
  VOICE="Samantha"
fi
if ! say -v '?' | awk '{print $1}' | grep -qx "$VOICE"; then
  VOICE="Daniel"
fi

cat > "$OUT_DIR/ecogenesis-gbif-contest-demo-english-voiceover.txt" <<'EOF'
Problem: biodiversity evidence is fragmented. Occurrence records may live in one system, DNA barcode fragments in another, BLAST or Sequence ID tables in a lab pipeline, and publication metadata in spreadsheets. When these pieces are not connected, useful evidence can be lost, and species-level claims can become stronger than the data actually support.

EcoGenesis is a Barcode-to-GBIF Evidence Compiler. It takes DNA barcode, metabarcoding, Sequence ID and BLAST-like outputs, then runs deterministic evidence gates. The result is not just a label. It is a safe taxonomic rank decision, a publication-readiness state, a repair plan, and a reproducible Evidence Pack.

On the public demo site, the interface is organized around the whole evidence path. Judges can open the overview, run the compiler, inspect the evidence map, view the fragment graph, check validation, read methods and download the Evidence Pack. Each section has its own public route, so the workflow is easy to review and cite.

The Run Compiler screen is where molecular evidence enters the system. A user can upload a CSV, start from a demo workflow, or test a reference fragment. The compiler validates required molecular fields, sequence context, reference-hit metrics, and publication metadata before it lets any record move forward.

In the mixed demo, records do not collapse into one simplistic answer. Some are species-safe, some are genus-safe, some remain weak, and some are not publishable until metadata are repaired. This is the core behavior: useful molecular evidence is preserved, but unsafe species exports and incomplete publication records are stopped.

The Evidence Map turns the results into a spatial evidence atlas. It connects GBIF occurrence context with claim states, snapshot hashes, VSEA rows, graph objects and export boundaries. The map is not a proof of presence by itself; it is a way to inspect provenance, context and claim strength in one place.

In the live Evidence Map, reviewers can see which rows are safe, repair-required, review-only or blocked. The same view exposes judge-mode checks, graph audits and export boundaries before download. That makes the spatial layer explanatory and auditable rather than a visual shortcut.

The Fragment Graph shows how marker fragments link to reference taxa and safe LCA decisions. When a fragment points to multiple close taxa, EcoGenesis reports the most specific safe rank instead of forcing a species claim. This keeps evidence, competitors and caveats together.

Uncertainty is handled through explicit gates: identity and coverage, ambiguity and LCA downgrade, barcode gap, diagnostic k-mer support, marker profile, publication readiness and graph provenance. A top hit does not become a species-level output unless the required gates pass.

Validation is built into the submission package. The project includes backend tests, frontend tests, competition batches, adversarial batches, graph audits and contest-readiness checks. The important validation target is fail-closed behavior: weak coverage, close competitors, metadata gaps and unsafe exports must be blocked or downgraded.

The final deliverable is the Evidence Pack. It includes CSV, JSON, HTML, VSEA, graph and audit outputs for review, repair and reuse. Researchers can inspect sequence safety tables, publication blockers, molecular evidence reports, graph provenance and machine-readable export artifacts.

EcoGenesis is already a working contest prototype with a live demo, public source code, reproducible outputs and downloadable evidence artifacts. It can scale to larger reference libraries, institutional pipelines, richer GBIF publishing workflows and broader molecular evidence observatories. The call to action is simple: open the live demo, run the workflow, and inspect the evidence before publication.
EOF

cat > "$OUT_DIR/ecogenesis-gbif-contest-demo-russian-transcript.md" <<'EOF'
# Русская расшифровка нового конкурсного видео EcoGenesis

## 1. Проблема
Проблема в том, что biodiversity evidence часто раздроблена. Occurrence records могут лежать в одной системе, DNA barcode fragments — в другой, BLAST или Sequence ID tables — в лабораторном pipeline, а publication metadata — в spreadsheets. Когда эти части не связаны, полезное evidence теряется, а species-level claims могут становиться сильнее, чем реально поддерживают данные.

## 2. Что делает EcoGenesis
EcoGenesis — это Barcode-to-GBIF Evidence Compiler. Он принимает DNA barcode, metabarcoding, Sequence ID и BLAST-like outputs, затем применяет deterministic evidence gates. Результат — не просто label. Это safe taxonomic rank decision, publication-readiness state, repair plan и reproducible Evidence Pack.

## 3. Интерфейс сайта
В публичном demo site интерфейс организован вокруг полного evidence path. Судьи могут открыть overview, запустить compiler, посмотреть evidence map, fragment graph, validation, methods и скачать Evidence Pack. У каждого раздела есть public route, поэтому workflow удобно проверять и цитировать.

## 4. Загрузка DNA barcode / molecular evidence
Run Compiler — это экран, где molecular evidence входит в систему. Пользователь может загрузить CSV, запустить demo workflow или проверить reference fragment. Compiler валидирует required molecular fields, sequence context, reference-hit metrics и publication metadata до того, как record может двигаться дальше.

## 5. Пример результата
В mixed demo records не превращаются в один упрощённый ответ. Некоторые становятся species-safe, некоторые genus-safe, некоторые остаются weak, а некоторые not publishable, пока metadata не будут repaired. Главное поведение системы: useful molecular evidence сохраняется, но unsafe species exports и incomplete publication records блокируются.

## 6. Evidence Map
Evidence Map превращает результаты в spatial evidence atlas. Он связывает GBIF occurrence context с claim states, snapshot hashes, VSEA rows, graph objects и export boundaries. Карта сама по себе не является proof of presence; это способ проверить provenance, context и claim strength в одном месте.

## 7. Live Evidence Map
В live Evidence Map reviewers видят, какие rows safe, repair-required, review-only или blocked. Этот же экран показывает judge-mode checks, graph audits и export boundaries before download. Так spatial layer остаётся explanatory and auditable, а не visual shortcut.

## 8. Fragment Graph
Fragment Graph показывает, как marker fragments связаны с reference taxa и safe LCA decisions. Если fragment указывает на несколько близких taxa, EcoGenesis reports the most specific safe rank вместо forced species claim. Evidence, competitors и caveats остаются вместе.

## 9. Проверка неопределённости
Uncertainty обрабатывается через explicit gates: identity and coverage, ambiguity and LCA downgrade, barcode gap, diagnostic k-mer support, marker profile, publication readiness и graph provenance. Top hit не становится species-level output, пока не пройдены required gates.

## 10. Validation
Validation встроена в submission package. Проект включает backend tests, frontend tests, competition batches, adversarial batches, graph audits и contest-readiness checks. Главная цель validation — fail-closed behavior: weak coverage, close competitors, metadata gaps и unsafe exports должны быть blocked or downgraded.

## 11. Evidence Pack
Final deliverable — Evidence Pack. Он включает CSV, JSON, HTML, VSEA, graph и audit outputs для review, repair and reuse. Researchers могут проверять sequence safety tables, publication blockers, molecular evidence reports, graph provenance и machine-readable export artifacts.

## 12. Масштабирование и call to action
EcoGenesis уже является working contest prototype с live demo, public source code, reproducible outputs и downloadable evidence artifacts. Он может масштабироваться на larger reference libraries, institutional pipelines, richer GBIF publishing workflows и broader molecular evidence observatories. Call to action простой: открыть live demo, запустить workflow и проверить evidence before publication.
EOF

python3 - "$OUT_DIR/ecogenesis-gbif-contest-demo-english-voiceover.txt" "$TMP_DIR" <<'PY'
from pathlib import Path
import sys
source = Path(sys.argv[1])
tmp = Path(sys.argv[2])
segments = [part.strip().replace("\n", " ") for part in source.read_text(encoding="utf-8").split("\n\n") if part.strip()]
for i, segment in enumerate(segments, 1):
    (tmp / f"voice_{i:02}.txt").write_text(segment + "\n", encoding="utf-8")
PY

images=(
  "$PPTX_SLIDE_DIR/slide-1.png"
  "$PPTX_SLIDE_DIR/slide-2.png"
  "$SITE_DIR/screencapture-ecooddworld-eu-2026-06-26-16_51_43.png"
  "$PPTX_SLIDE_DIR/slide-3.png"
  "$SITE_DIR/screencapture-ecooddworld-eu-run-compiler-2026-06-26-16_52_06.png"
  "$PPTX_SLIDE_DIR/slide-4.png"
  "$SITE_DIR/screencapture-ecooddworld-eu-evidence-map-2026-06-26-16_52_24.png"
  "$PPTX_SLIDE_DIR/slide-5.png"
  "$PPTX_SLIDE_DIR/slide-7.png"
  "$PPTX_SLIDE_DIR/slide-6.png"
  "$PPTX_SLIDE_DIR/slide-8.png"
  "$PPTX_SLIDE_DIR/slide-9.png"
)

kinds=(
  "slide" "slide" "site" "slide" "site" "slide" "site" "slide" "slide" "slide" "slide" "slide"
)

titles=(
  "Problem: fragmented molecular and biodiversity records"
  "What EcoGenesis does"
  "Public demo interface"
  "Upload CSV or run a bundled workflow"
  "Mixed demo results and repair states"
  "GBIF context and claim-state map"
  "Live evidence map with provenance checks"
  "Fragments, taxa and safe LCA"
  "Uncertainty gates"
  "Validation and adversarial checks"
  "Evidence Pack outputs"
  "Live demo and source code"
)

site_crop_y=(
  0 0 0 0 110 0 80 0 0 0 0 0
)

highlight_filters=(
  "drawbox=x=170:y=455:w=930:h=150:color=0x9EEA76@0.55:t=6"
  "drawbox=x=90:y=370:w=1760:h=470:color=0x9EEA76@0.45:t=5"
  "drawbox=x=295:y=270:w=1230:h=110:color=0x1E5B69@0.65:t=5,drawbox=x=285:y=420:w=1260:h=210:color=0x9EEA76@0.45:t=5"
  "drawbox=x=650:y=335:w=860:h=430:color=0x9EEA76@0.50:t=5"
  "drawbox=x=650:y=290:w=930:h=280:color=0x1E5B69@0.65:t=5,drawbox=x=650:y=620:w=930:h=350:color=0x9EEA76@0.50:t=5"
  "drawbox=x=1480:y=210:w=350:h=690:color=0x9EEA76@0.55:t=5"
  "drawbox=x=310:y=350:w=1280:h=240:color=0x1E5B69@0.55:t=5,drawbox=x=330:y=650:w=1210:h=260:color=0x9EEA76@0.45:t=5"
  "drawbox=x=560:y=420:w=820:h=420:color=0x9EEA76@0.50:t=5"
  "drawbox=x=880:y=400:w=740:h=365:color=0x9EEA76@0.55:t=5"
  "drawbox=x=150:y=430:w=1640:h=440:color=0x9EEA76@0.50:t=5"
  "drawbox=x=120:y=460:w=740:h=455:color=0x9EEA76@0.50:t=5,drawbox=x=1380:y=430:w=430:h=425:color=0x9EEA76@0.50:t=5"
  "drawbox=x=135:y=755:w=1685:h=230:color=0x9EEA76@0.55:t=5"
)

make_video_segment() {
  local idx="$1"
  local duration="$2"
  local image="$3"
  local kind="$4"
  local title="$5"
  local crop_y="$6"
  local highlight="$7"
  local output="$TMP_DIR/video_${idx}.mp4"
  local title_file="$TMP_DIR/title_${idx}.txt"
  local fade_start

  printf '%s\n' "$title" > "$title_file"
  fade_start="$(python3 - "$duration" <<'PY'
import sys
print(max(0, float(sys.argv[1]) - 0.35))
PY
)"

  if [[ "$kind" == "site" ]]; then
    ffmpeg -hide_banner -loglevel error -y \
      -loop 1 -t "$duration" -i "$image" \
      -vf "crop=1020:574:0:${crop_y},scale=1920:1080,drawbox=x=0:y=0:w=1920:h=92:color=0x0B251E@0.80:t=fill,drawtext=fontfile='${FONT_FILE}':textfile='${title_file}':fontcolor=white:fontsize=34:x=48:y=27,${highlight},fade=t=in:st=0:d=0.25,fade=t=out:st=${fade_start}:d=0.35" \
      -r 30 -c:v libx264 -crf 24 -preset medium -pix_fmt yuv420p "$output" >/dev/null
  else
    ffmpeg -hide_banner -loglevel error -y \
      -loop 1 -t "$duration" -i "$image" \
      -vf "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,${highlight},drawbox=x=0:y=0:w=1920:h=82:color=0x061D18@0.38:t=fill,drawtext=fontfile='${FONT_FILE}':textfile='${title_file}':fontcolor=0xEFFFF5:fontsize=30:x=48:y=24,fade=t=in:st=0:d=0.25,fade=t=out:st=${fade_start}:d=0.35" \
      -r 30 -c:v libx264 -crf 24 -preset medium -pix_fmt yuv420p "$output" >/dev/null
  fi
}

durations=()
for i in $(seq 1 12); do
  idx="$(printf '%02d' "$i")"
  voice_file="$TMP_DIR/voice_${idx}.txt"
  audio_file="$TMP_DIR/voice_${idx}.aiff"
  say -v "$VOICE" -r 165 -o "$audio_file" -f "$voice_file"
  audio_duration="$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$audio_file")"
  duration="$(python3 - "$audio_duration" <<'PY'
import math, sys
print(math.ceil(float(sys.argv[1]) + 0.7))
PY
)"
  durations+=("$duration")
  arr_index=$((i - 1))
  make_video_segment "$idx" "$duration" "${images[$arr_index]}" "${kinds[$arr_index]}" "${titles[$arr_index]}" "${site_crop_y[$arr_index]}" "${highlight_filters[$arr_index]}"
  ffmpeg -hide_banner -loglevel error -y \
    -i "$TMP_DIR/video_${idx}.mp4" -i "$audio_file" \
    -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 160k \
    "$TMP_DIR/segment_${idx}.mp4" >/dev/null
  printf "file '%s'\n" "$TMP_DIR/segment_${idx}.mp4" >> "$TMP_DIR/segments.txt"
done

python3 - "$OUT_DIR/ecogenesis-gbif-contest-demo-en.srt" "$OUT_DIR/ecogenesis-gbif-contest-demo-english-voiceover.txt" "${durations[@]}" <<'PY'
from pathlib import Path
import re, sys, textwrap
out = Path(sys.argv[1])
voice = Path(sys.argv[2])
durations = [float(x) for x in sys.argv[3:]]
segments = [part.strip().replace("\n", " ") for part in voice.read_text(encoding="utf-8").split("\n\n") if part.strip()]

def fmt(t):
    ms = round(t * 1000)
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def chunks(text, max_len=62):
    sentences = re.split(r"(?<=[.!?])\\s+", text)
    cur, out = "", []
    for sentence in sentences:
        wrapped = textwrap.wrap(sentence, width=max_len, break_long_words=False, break_on_hyphens=False) or [sentence]
        for part in wrapped:
            if not cur:
                cur = part
            elif len(cur) + 1 + len(part) <= max_len:
                cur += " " + part
            else:
                out.append(cur)
                cur = part
    if cur:
        out.append(cur)
    return out

parts = []
sub_idx = 1
cur = 0.0
for segment, duration in zip(segments, durations):
    lines = chunks(segment)
    per = duration / len(lines)
    for line in lines:
        start, end = cur, cur + per
        parts.append(f"{sub_idx}\n{fmt(start)} --> {fmt(end)}\n{line}\n")
        sub_idx += 1
        cur = end
out.write_text("\n".join(parts), encoding="utf-8")
PY

ffmpeg -hide_banner -loglevel error -y \
  -f concat -safe 0 -i "$TMP_DIR/segments.txt" \
  -c copy -movflags +faststart \
  "$TMP_DIR/ecogenesis-gbif-contest-demo-no-subs.mp4" >/dev/null

ffmpeg -hide_banner -loglevel error -y \
  -i "$TMP_DIR/ecogenesis-gbif-contest-demo-no-subs.mp4" \
  -vf "subtitles='${OUT_DIR}/ecogenesis-gbif-contest-demo-en.srt':force_style='FontName=${SUB_FONT_NAME},FontSize=10,PrimaryColour=&H00FFFFFF&,OutlineColour=&H00111D17&,BorderStyle=1,Outline=1.4,Shadow=0,MarginV=28'" \
  -c:v libx264 -crf 24 -preset medium -pix_fmt yuv420p -c:a copy -movflags +faststart \
  "$OUT_DIR/ecogenesis-gbif-contest-demo-en-subs.mp4" >/dev/null

ffmpeg -hide_banner -loglevel error -y -ss 00:00:35 \
  -i "$OUT_DIR/ecogenesis-gbif-contest-demo-en-subs.mp4" \
  -frames:v 1 "$OUT_DIR/demo-thumbnail-contest-en.png" >/dev/null 2>&1

ffprobe -v error -show_entries format=duration,size -of default=noprint_wrappers=1 "$OUT_DIR/ecogenesis-gbif-contest-demo-en-subs.mp4"
