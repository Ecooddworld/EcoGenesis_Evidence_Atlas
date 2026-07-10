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
EcoGenesis V2 is the evidence-bounded release of the Barcode-to-GBIF Evidence Compiler. It addresses a fragmented evidence problem: occurrence records may live in one system, DNA barcode fragments in another, BLAST or Sequence ID tables in a lab pipeline, and publication metadata in spreadsheets. When these pieces are not connected, useful evidence can be lost, and species-level claims can become stronger than the data actually support.

EcoGenesis is a Barcode-to-GBIF Evidence Compiler. It takes DNA barcode, metabarcoding, Sequence ID and BLAST-like outputs, then runs configured evidence gates. The result is not species truth. It is a bounded rank result, a publication-readiness check, a repair plan, and a reproducible Evidence Pack for review.

On the public demo site, judges can open the overview, run the compiler, inspect the Evidence Map, view the Fragment Graph, open Regression and Audits, read Methods and Audits, and download the GBIF Repair Pack. A persistent prototype notice states that the tool is not an independently validated taxonomic identifier or a GBIF publisher.

The Run Compiler screen is where molecular evidence enters the system. A user can upload a CSV, start from a demo workflow, or test a reference fragment. The compiler checks required molecular fields, sequence context, reference-hit metrics, reference and sequence-quality evidence, and publication metadata before it routes a record.

Under the current fail-closed reference attestation, the bundled mixed demo emits no species rule-pass. AALB-COI-good and AALB-COI-metadata-gap are ambiguous, AALB-COI-ambiguous is bounded at genus, and AALB-COI-short is weak. The metadata-gap row also carries publication blockers. These are run-local rule results and validation candidates, not independently confirmed identifications or accepted GBIF records.

The Evidence Map shows hashed GBIF occurrence context beside molecular rule-evidence rows, graph objects and export boundaries. The occurrence rows are explicitly unlinked from the molecular rows unless shared specimen or event identifiers are supplied. The map cannot upgrade a molecular claim and is not evidence of presence by itself.

In the Evidence Map, reviewers can see rule-supported candidates, repair-required rows, review-only hypotheses and blocked exports. The same view exposes release checks, graph audits and export boundaries before download. Passing those checks means the files agree for that run; it does not establish external scientific validity.

The Fragment Graph shows how marker fragments link to reference taxa and an LCA-bounded rank. When a fragment points to multiple close taxa, EcoGenesis reports the most specific rank allowed by the configured rules instead of forcing a species claim. Evidence, competitors and caveats remain together.

Uncertainty is handled through explicit gates: identity and coverage, ambiguity and LCA downgrade, barcode gap, locally unique k-mer support in the selected reference set, marker profile, publication checks and graph provenance. A top hit does not become a species-level validation candidate unless every configured requirement passes.

Regression and integrity checks are built into the submission package. The project includes backend and frontend tests, repeated-fixture competition batches, adversarial cases, graph audits and contest-readiness checks. They test fail-closed behavior and internal consistency; independent multi-taxon scientific validation remains future work.

The final deliverable is the Evidence Pack. It includes CSV, JSON, HTML, rule-evidence, graph and audit outputs for review, repair and reuse. Researchers can inspect sequence decision tables, blockers, validation-candidate templates, molecular evidence reports, graph provenance and machine-readable artifacts.

EcoGenesis is a working contest prototype with a live demo, public source code, reproducible run-local outputs and downloadable evidence artifacts. It is not yet a validated scientific identifier or complete GBIF publishing pipeline. The call to action is simple: run the workflow, inspect its boundaries, and validate candidate records externally before publication.
EOF

cat > "$OUT_DIR/ecogenesis-gbif-contest-demo-transcript.md" <<'EOF'
# Расшифровка EcoGenesis V2 — evidence-bounded release

## 1. Проблема
EcoGenesis V2 — это evidence-bounded release Barcode-to-GBIF Evidence Compiler. Он решает проблему раздробленного biodiversity evidence: occurrence records могут лежать в одной системе, DNA barcode fragments — в другой, BLAST или Sequence ID tables — в лабораторном pipeline, а publication metadata — в spreadsheets. Когда эти части не связаны, полезное evidence теряется, а species-level claims могут становиться сильнее, чем реально поддерживают данные.

## 2. Что делает EcoGenesis
EcoGenesis — это Barcode-to-GBIF Evidence Compiler. Он принимает DNA barcode, metabarcoding, Sequence ID и BLAST-like outputs, затем применяет configured evidence gates. Результат не является species truth. Это bounded rank result, publication-readiness check, repair plan и reproducible Evidence Pack для review.

## 3. Интерфейс сайта
В публичном demo site судьи могут открыть overview, запустить compiler, посмотреть Evidence Map и Fragment Graph, открыть Regression & Audits и Methods & Audits, а затем скачать GBIF Repair Pack. Постоянный prototype notice прямо говорит, что инструмент не является independently validated taxonomic identifier или GBIF publisher.

## 4. Загрузка DNA barcode / molecular evidence
Run Compiler — это экран, где molecular evidence входит в систему. Пользователь может загрузить CSV, запустить demo workflow или проверить reference fragment. Compiler проверяет required molecular fields, sequence context, reference-hit metrics, reference and sequence-quality evidence и publication metadata до маршрутизации record.

## 5. Пример результата
При текущей fail-closed reference attestation bundled mixed demo не выдаёт ни одного species rule-pass. AALB-COI-good и AALB-COI-metadata-gap получают состояние ambiguous, AALB-COI-ambiguous ограничивается уровнем genus, а AALB-COI-short получает состояние weak. У metadata-gap row также есть publication blockers. Это run-local rule results и validation candidates, а не independently confirmed identifications или принятые GBIF records.

## 6. Evidence Map
Evidence Map показывает hashed GBIF occurrence context рядом с molecular rule-evidence rows, graph objects и export boundaries. Occurrence rows явно не связаны с molecular rows без общих specimen или event identifiers. Карта не может усилить molecular claim и сама по себе не является evidence of presence.

## 7. Live Evidence Map
В Evidence Map reviewers видят rule-supported candidates, repair-required rows, review-only hypotheses и blocked exports. Этот же экран показывает release checks, graph audits и export boundaries before download. Pass означает согласованность файлов конкретного run, а не external scientific validity.

## 8. Fragment Graph
Fragment Graph показывает, как marker fragments связаны с reference taxa и LCA-bounded rank. Если fragment указывает на несколько близких taxa, EcoGenesis сообщает наиболее конкретный rank, разрешённый configured rules, вместо forced species claim. Evidence, competitors и caveats остаются вместе.

## 9. Проверка неопределённости
Uncertainty обрабатывается через explicit gates: identity and coverage, ambiguity and LCA downgrade, barcode gap, locally unique k-mer support в выбранном reference set, marker profile, publication checks и graph provenance. Top hit не становится species-level validation candidate, пока не пройдены все configured requirements.

## 10. Regression и integrity checks
Regression и integrity checks встроены в submission package. Проект включает backend и frontend tests, repeated-fixture competition batches, adversarial cases, graph audits и contest-readiness checks. Они проверяют fail-closed behavior и internal consistency; independent multi-taxon scientific validation остаётся future work.

## 11. Evidence Pack
Final deliverable — Evidence Pack. Он включает CSV, JSON, HTML, rule-evidence, graph и audit outputs для review, repair and reuse. Researchers могут проверять sequence decision tables, blockers, validation-candidate templates, molecular evidence reports, graph provenance и machine-readable artifacts.

## 12. Масштабирование и call to action
EcoGenesis — working contest prototype с live demo, public source code, reproducible run-local outputs и downloadable evidence artifacts. Это ещё не validated scientific identifier и не complete GBIF publishing pipeline. Call to action простой: запустить workflow, проверить его boundaries и externally validate candidate records before publication.
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
  "$SITE_DIR/screencapture-ecooddworld-eu-2026-06-26-16_51_43.png"
  "$SITE_DIR/screencapture-ecooddworld-eu-2026-06-26-16_51_43.png"
  "$SITE_DIR/screencapture-ecooddworld-eu-2026-06-26-16_51_43.png"
  "$SITE_DIR/screencapture-ecooddworld-eu-run-compiler-2026-06-26-16_52_06.png"
  "$SITE_DIR/screencapture-ecooddworld-eu-run-compiler-2026-06-26-16_52_06.png"
  "$SITE_DIR/screencapture-ecooddworld-eu-evidence-map-2026-06-26-16_52_24.png"
  "$SITE_DIR/screencapture-ecooddworld-eu-evidence-map-2026-06-26-16_52_24.png"
  "$SITE_DIR/screencapture-ecooddworld-eu-fragment-graph-2026-06-26-16_52_39.png"
  "$SITE_DIR/screencapture-ecooddworld-eu-methods-2026-06-26-16_53_25.png"
  "$SITE_DIR/screencapture-ecooddworld-eu-validation-2026-06-26-16_53_03.png"
  "$SITE_DIR/screencapture-ecooddworld-eu-evidence-pack-2026-06-26-16_54_14.png"
  "$SITE_DIR/screencapture-ecooddworld-eu-2026-06-26-16_51_43.png"
)

kinds=(
  "site" "site" "site" "site" "site" "site" "site" "site" "site" "site" "site" "site"
)

titles=(
  "EcoGenesis V2: evidence-bounded release"
  "Bounded results, validation candidates and repair actions"
  "Public demo interface"
  "Upload CSV or run a bundled workflow"
  "Mixed demo results and repair states"
  "Unlinked GBIF context and molecular claim states"
  "Live evidence map with provenance checks"
  "Fragments, taxa and LCA-bounded rank"
  "Uncertainty gates"
  "Regression and integrity checks"
  "Validation-candidate Evidence Pack"
  "Live demo and source code"
)

site_crop_y=(
  0 0 0 0 80 0 80 0 0 0 0 0
)

highlight_filters=(
  "null" "null" "null" "null" "null" "null"
  "null" "null" "null" "null" "null" "null"
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
