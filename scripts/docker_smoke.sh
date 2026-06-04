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

docker compose -p "${PROJECT_NAME}" up --build -d

for _ in $(seq 1 60); do
  if curl -fsS "http://127.0.0.1:${BACKEND_PORT}/health" >/dev/null \
    && curl -fsS "http://127.0.0.1:${FRONTEND_PORT}/" >/dev/null; then
    break
  fi
  sleep 2
done

curl -fsS "http://127.0.0.1:${BACKEND_PORT}/health" | grep -q '"status":"ok"'
curl -fsS "http://127.0.0.1:${FRONTEND_PORT}/" | grep -q "Molecular Evidence"

curl -fsS "http://127.0.0.1:${FRONTEND_PORT}/api/barcode/search-status" | grep -Eq '"preferred_backend":"(vsearch|blastn|python-local)"'

curl -fsS \
  -H "Content-Type: application/json" \
  -d '{
    "sequence_id": "docker-smoke-aedes",
    "sequence": "ACGTTGACCTAGGCTTACGATCGTACCGATGCTAGCTAGGATCCGATCGTACGATCGTAGCTAGCATCGGATCGTACCGTAGCTAGCTAGGCTAGCTAGGATCGATCGTACGAT",
    "reference_dataset": "aedes_coi_mini",
    "backend": "auto",
    "compile": true
  }' \
  "http://127.0.0.1:${FRONTEND_PORT}/api/barcode/search" | grep -q '"status":"completed"'

echo "Docker smoke passed: http://127.0.0.1:${FRONTEND_PORT}"
