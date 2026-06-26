#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ASSET_DIR="$ROOT_DIR/submission-assets/platform-video"
SCREEN_DIR="$ROOT_DIR/submission-assets/barcode-video/screenshots"
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

slides=(
$'EcoGenesis Evidence Atlas\n\nКонкурсное демо\nDNA barcode -> safe claim -> GBIF-ready export candidates\n\nОзвучка и субтитры: русский'
$'Что дает демо\n\n1. Не превращает top hit в species truth\n2. Разделяет TaxStatus и PubStatus\n3. Блокирует unsafe species-level claims\n4. Показывает repair actions для публикации'
$'Проблема публикации\n\nCSV / FASTA / BLAST-like hits / GBIF context\n\nНужно понять:\nчто safe,\nчто downgraded,\nчто blocked,\nчто repairable.'
$''
$''
$''
$''
$''
$''
$'Как встроить в платформу\n\nIngestion adapters:\nCSV, FASTA, BLAST, VSEARCH, BOLD, UNITE, GBIF Sequence ID\n\nReference registry:\nbarcode gaps, diagnostic k-mers, library gaps'
$'Платформенный слой\n\nEvidence graph with provenance hashes\nPublisher repair optimizer\nDataset Observatory\nGBIF-ready export boundary\nAI export guardrails'
$'Финальный смысл\n\nНе “угадай вид по top hit”, а:\n\nкакой claim безопасен,\nчто downgraded,\nчто blocked,\nчто repairable,\nи какие данные нужны дальше.'
)

images=(
""
""
""
"$SCREEN_DIR/01-judge-overview.png"
"$SCREEN_DIR/02-run-compiler-upload.png"
"$SCREEN_DIR/03-run-compiler-result.png"
"$SCREEN_DIR/04-result-details.png"
"$SCREEN_DIR/05-math-proof-top.png"
"$SCREEN_DIR/07-research-audit.png"
""
""
""
)

top_labels=(
"Presentation"
"Value"
"Pipeline"
"Demo overview"
"Run compiler: CSV upload"
"Compiler results"
"Evidence Pack exports"
"Math and proof"
"Research audit and Observatory"
"Platform integration"
"Platform modules"
"Scientific conclusion"
)

subtitle_captions=(
"EcoGenesis: строгий molecular evidence compiler для GBIF-ready решений."
"Демо показывает, где evidence strong, где species claim blocked, и что можно repair."
"Пайплайн: схема входа -> safety gates -> publication gates -> Evidence Pack."
"Главный экран связывает демо, proof layer, exports и walkthrough для оценки."
"Пользователь загружает CSV и видит schema, поля и validation context."
"Результат разделяет TaxStatus, PubStatus, blockers, candidate_taxon и published_taxon."
"Evidence Pack сохраняет таблицы, methods, citations, audits и machine-readable outputs."
"Math and proof фиксирует failure modes: competitor, barcode gap, k-mer, metadata, provenance."
"Research audit показывает GSEG, GSIG, Observatory и AI guardrails без status promotion."
"Платформа расширяется через ingestion, reference registry и provenance graph."
"Следующий слой: repair optimizer, Observatory dashboard, exports и guardrail audits."
"Финальный claim строгий: supported within supplied reference context, not biological truth."
)

voice_segments=(
"EcoGenesis Evidence Atlas — это демонстрация того, как молекулярные наблюдения можно превращать в осторожные, проверяемые и пригодные для публикации решения."
"Главная идея простая: top hit не равен species truth. Демо не обещает доказать присутствие вида только по одной строке результата. Оно показывает, какие утверждения поддержаны supplied reference context, какие надо понизить до рода или более высокого ранга, а какие должны остаться review-only."
"Проблема возникает у лабораторий, экологов и data publishers постоянно. Есть CSV из DNA barcode, metabarcoding, Sequence ID или BLAST-like pipeline. В нем есть последовательности, identity, coverage, lineage, metadata и иногда GBIF occurrence context. Но перед публикацией нужен строгий ответ: что безопасно вывести на species rank, что blocked, что repairable, и какие поля надо исправить первыми."
"Первая часть демо показывает ценность системы. EcoGenesis разделяет taxonomic safety и publication readiness. Запись может быть species-safe по molecular evidence, но все равно not GBIF-ready, если отсутствуют occurrenceID, eventDate, methodOrSOP, referenceDatabase или assay context. В таком случае evidence сохраняется, но publication blocked by metadata."
"Во второй части пользователь открывает compiler, загружает CSV и видит preview. Система проверяет required molecular fields, Darwin Core fields, DNA-derived metadata, invalid DNA characters, duplicated identifiers, coverage, aligned length, marker profile and assay profile."
"Затем включаются safety gates. Exact match требует identity не ниже 99 процентов и query coverage не ниже 80 процентов. Если есть competitor, статистически неотличимый от top hit, species-level claim blocked, а вывод понижается до LCA. Если barcode gap отсутствует или не положительный, species claim тоже blocked."
"Результат не просто показывает зеленую или красную метку. Он объясняет DecisionClass, TaxStatus, PubStatus, candidate_taxon, published_taxon, blockers and repair actions. Это важно для честной публикации: weak, ambiguous и metadata-blocked records не получают published_taxon."
"Дальше демо показывает Evidence Pack and Math proof. Внутри есть sequence safety table, publication blockers, repair plan, methods text, citations, molecular evidence report, math viability audit, marker and assay audits, theorem checklist, VSEA, graph provenance audit and AI guardrail audit."
"Research audit показывает следующий слой: GSEG, GSIG and Observatory. Segment-level evidence не имеет права превращать shared fragment в species-specific claim. Визуализация explanatory only: карта, matrix, graph and proof wheel не меняют claim_state. AI-ready export тоже не может повысить weak_hypothesis, blocked или review_only."
"Последняя часть объясняет, как развить демо в платформу. Первый модуль — ingestion layer для лабораторных CSV, FASTA, BLAST, VSEARCH, BOLD, UNITE and GBIF Sequence ID. Второй — reference and barcode-gap registry, чтобы видеть, где species-level output невозможен из-за library gaps."
"Третий модуль — evidence graph with provenance hashes, чтобы каждое решение было связано с ruleset version, input artifact and blocker. Четвертый модуль — publisher repair optimizer. Он показывает, какие metadata repairs дадут максимальный прирост GBIF-ready records: occurrenceID, eventDate, methodOrSOP, referenceDatabase, assay fields, scientificName conflict resolution and citation completeness."
"Так EcoGenesis становится не просто демо-страницей, а научной платформой проверки гипотез. Она не заменяет эксперта и не угадывает biological truth. Она снижает риск overclaim, сохраняет evidence, блокирует unsafe species claims and produces reproducible, reviewable, GBIF-ready export candidates. Финальный вывод: перейти от “у нас есть top hit” к “мы знаем, какой claim безопасен, что заблокировано, что repairable, и какие данные нужны для следующего шага”."
)

make_slide_video() {
  local index="$1"
  local duration="$2"
  local text="$3"
  local output="$TMP_DIR/video_${index}.mp4"
  local text_file="$TMP_DIR/slide_${index}.txt"
  printf '%s\n' "$text" > "$text_file"

  ffmpeg -hide_banner -loglevel error -y \
    -f lavfi -i "color=c=0xf4f7f2:s=1280x720:d=${duration}" \
    -vf "drawbox=x=0:y=0:w=1280:h=720:color=0xf4f7f2:t=fill,drawbox=x=0:y=0:w=1280:h=11:color=0x1e6b78:t=fill,drawbox=x=74:y=90:w=6:h=500:color=0x1e6b78:t=fill,drawtext=fontfile='${FONT_FILE}':textfile='${text_file}':fontcolor=0x13231d:fontsize=35:line_spacing=16:x=110:y=96,drawtext=fontfile='${FONT_FILE}':text='ecooddworld.eu':fontcolor=0x476158:fontsize=22:x=1030:y=44" \
    -r 30 -c:v libx264 -pix_fmt yuv420p "$output" >/dev/null
}

make_image_video() {
  local index="$1"
  local duration="$2"
  local image_file="$3"
  local output="$TMP_DIR/video_${index}.mp4"
  local caption_file="$TMP_DIR/section_${index}.txt"
  printf '%s\n' "${top_labels[$((10#$index-1))]}" > "$caption_file"

  if [[ ! -f "$image_file" ]]; then
    echo "Missing screenshot: $image_file" >&2
    exit 1
  fi

  ffmpeg -hide_banner -loglevel error -y \
    -loop 1 -t "$duration" -i "$image_file" \
    -vf "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,drawbox=x=0:y=0:w=1280:h=82:color=0x123F32@0.88:t=fill,drawtext=fontfile='${FONT_FILE}':textfile='${caption_file}':fontcolor=white:fontsize=23:line_spacing=6:x=42:y=25" \
    -r 30 -c:v libx264 -pix_fmt yuv420p "$output" >/dev/null
}

computed_durations=()

for i in "${!voice_segments[@]}"; do
  index="$(printf '%02d' "$((i + 1))")"
  voice_file="$TMP_DIR/voice_${index}.txt"
  audio_file="$TMP_DIR/voice_${index}.aiff"
  printf '%s\n' "${voice_segments[$i]}" > "$voice_file"
  say -v "$VOICE" -r 168 -o "$audio_file" -f "$voice_file"

  audio_duration="$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$audio_file")"
  duration="$(python3 - "$audio_duration" <<'PY'
import math, sys
print(math.ceil(float(sys.argv[1]) + 1.2))
PY
)"
  computed_durations+=("$duration")

  if [[ -n "${images[$i]}" ]]; then
    make_image_video "$index" "$duration" "${images[$i]}"
  else
    make_slide_video "$index" "$duration" "${slides[$i]}"
  fi

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
import sys
from pathlib import Path

out = Path(sys.argv[1])
caption_file = Path(sys.argv[2])
durations = [float(x) for x in sys.argv[3:]]
captions = caption_file.read_text(encoding="utf-8").splitlines()

def fmt(t):
    ms = round(t * 1000)
    h, rem = divmod(ms, 3600000)
    m, rem = divmod(rem, 60000)
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
  -vf "subtitles='${OUT_DIR}/ecogenesis-platform-demo-ru-voice-subs.srt':force_style='FontName=${SUB_FONT_NAME},FontSize=17,PrimaryColour=&H00FFFFFF&,OutlineColour=&H00111D17&,BorderStyle=1,Outline=1,Shadow=0,MarginV=26'" \
  -c:v libx264 -pix_fmt yuv420p -c:a copy -movflags +faststart \
  "$OUT_DIR/ecogenesis-platform-demo-ru-voice-subs.mp4" >/dev/null

cp "$ASSET_DIR/voiceover-ru.txt" "$OUT_DIR/ecogenesis-platform-demo-ru-voiceover.txt"

ffmpeg -hide_banner -loglevel error -y -ss 00:00:35 \
  -i "$OUT_DIR/ecogenesis-platform-demo-ru-voice-subs.mp4" \
  -frames:v 1 "$OUT_DIR/demo-thumbnail-platform-ru.png" >/dev/null 2>&1

ffprobe -v error -show_entries format=duration,size -of default=noprint_wrappers=1 "$OUT_DIR/ecogenesis-platform-demo-ru-voice-subs.mp4"
