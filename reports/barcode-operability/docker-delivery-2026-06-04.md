# Docker Delivery Report - 2026-06-04

## What Changed

- `docker compose up --build` is now the contest-facing production stack.
- Backend Docker image is built from the repository root, installs VSEARCH and NCBI BLAST+, bundles `references/`, and uses `REFERENCE_DATA_DIR=/app/references`.
- Frontend Docker image now builds static production assets and serves them through Nginx.
- Nginx proxies `/api/*` and `/health` to the backend service inside Docker, allowing the UI to run from one browser URL.
- Frontend API base now supports an empty `VITE_API_BASE_URL`, so production Docker can use same-origin `/api`.
- Added `scripts/docker_smoke.sh` for a one-command Docker stack smoke test on alternate ports.

## Verified Locally

- Backend regression: `41 passed, 1 skipped`.
- Frontend regression: `6 passed`.
- Frontend production build: passed.
- `docker compose config`: passed.
- `docker compose -f docker-compose.v3.yml config`: passed.
- `git diff --check`: passed.

## Docker Runtime Blocker

Docker Desktop/daemon did not respond in this local session:

```text
docker version --format '{{.Client.Version}} {{.Server.Version}}'
-> DOCKER_DAEMON_TIMEOUT after 10 seconds
```

Because the daemon timed out even for `docker version`, the runtime Docker build/up smoke could not be completed here. After restarting Docker Desktop, run:

```bash
scripts/docker_smoke.sh
```

Expected result:

```text
Docker smoke passed: http://127.0.0.1:13200
```
