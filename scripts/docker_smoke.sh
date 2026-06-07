#!/usr/bin/env bash
set -euo pipefail

PROJECT_NAME="${PROJECT_NAME:-ecogenesis-docker-smoke}"
FRONTEND_PORT="${FRONTEND_PORT:-13200}"
BACKEND_PORT="${BACKEND_PORT:-18200}"
KEEP_DOCKER_STACK="${KEEP_DOCKER_STACK:-0}"

export FRONTEND_PORT BACKEND_PORT

cleanup() {
  if [[ "${KEEP_DOCKER_STACK}" != "1" ]]; then
    docker compose -p "${PROJECT_NAME}" down --remove-orphans >/dev/null
  fi
}
trap cleanup EXIT

tmpdir="$(mktemp -d)"
trap 'rm -rf "${tmpdir}"; cleanup' EXIT

wait_for_url() {
  local url="$1"
  local label="$2"
  for _ in $(seq 1 60); do
    if curl -fs --max-time 5 "${url}" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  echo "Timed out waiting for ${label}: ${url}" >&2
  return 1
}

docker compose -p "${PROJECT_NAME}" up --build -d

wait_for_url "http://127.0.0.1:${BACKEND_PORT}/health" "backend health"
wait_for_url "http://127.0.0.1:${FRONTEND_PORT}/" "frontend"
wait_for_url "http://127.0.0.1:${FRONTEND_PORT}/health" "frontend proxied backend health"

curl -fsS "http://127.0.0.1:${BACKEND_PORT}/health" | grep -q '"status":"ok"'
curl -fsS "http://127.0.0.1:${FRONTEND_PORT}/health" | grep -q '"status":"ok"'

index_html="$(curl -fsS "http://127.0.0.1:${FRONTEND_PORT}/")"
printf "%s" "${index_html}" | grep -q "<title>Barcode-to-GBIF Evidence Compiler</title>"
printf "%s" "${index_html}" | grep -q '<div id="root"></div>'
asset_path="$(printf "%s" "${index_html}" | grep -o 'src="/assets/[^"]*\.js"' | head -n 1 | sed 's/src="//;s/"//')"
if [[ -z "${asset_path}" ]]; then
  echo "Frontend index did not contain a Vite JavaScript asset." >&2
  exit 1
fi
curl -fsS "http://127.0.0.1:${FRONTEND_PORT}${asset_path}" -o "${tmpdir}/frontend.js"
grep -q "Molecular Evidence" "${tmpdir}/frontend.js"

curl -fsS "http://127.0.0.1:${FRONTEND_PORT}/api/barcode/search-status" -o "${tmpdir}/search-status.json"
grep -q '"preferred_backend":"vsearch"' "${tmpdir}/search-status.json"

curl -fsS \
  -H "Content-Type: application/json" \
  -d '{
    "sequence_id": "docker-smoke-aedes",
    "sequence": "ACGTTGACCTAGGCTTACGATCGTACCGATGCTAGCTAGGATCCGATCGTACGATCGTAGCTAGCATCGGATCGTACCGTAGCTAGCTAGGCTAGCTAGGATCGATCGTACGAT",
    "reference_dataset": "aedes_coi_mini",
    "backend": "auto",
    "compile": true
  }' \
  "http://127.0.0.1:${FRONTEND_PORT}/api/barcode/search" \
  -o "${tmpdir}/reference-search.json"
grep -q '"status":"completed"' "${tmpdir}/reference-search.json"

curl -fsS \
  -H "Content-Type: application/json" \
  -d '{
    "sequence_id": "docker-smoke-fragment",
    "sequence": "ACGTTGACCTAGGCTTACGATCGTACCGATGC",
    "reference_dataset": "culicidae_short_shared_marker",
    "backend": "auto",
    "max_hits": 20
  }' \
  "http://127.0.0.1:${FRONTEND_PORT}/api/barcode/fragment-graph" \
  -o "${tmpdir}/fragment-graph.json"
grep -q '"status":"higher-rank-shared"' "${tmpdir}/fragment-graph.json"
grep -q '"segments":' "${tmpdir}/fragment-graph.json"

echo "Docker smoke passed: http://127.0.0.1:${FRONTEND_PORT}"
