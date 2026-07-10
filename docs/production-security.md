# Production Security and Operations

EcoGenesis is a single-node, rule-based prototype. The controls below make a bounded deployment safer; they do not provide tenant isolation, a durable job queue, cancellation, or independently validated scientific outputs.

## API controls

The FastAPI middleware applies request IDs, structured request audit logs, read/write rate limits, request-body limits and optional bearer authentication. Mutation authentication fails closed when `API_AUTH_REQUIRED=true` but `API_AUTH_TOKEN` is absent.

| Variable | Container default | Purpose |
| --- | ---: | --- |
| `API_AUTH_REQUIRED` | `true` Caddy / `false` local | Require a bearer token for `POST`, `PUT`, `PATCH` and `DELETE` under `/api/`. |
| `API_AUTH_TOKEN` | empty | Token compared in constant time; never returned by the API. |
| `API_AUTH_PROTECT_RUN_READS` | `true` Caddy / `false` local | With required auth, also protect runtime run and export reads from enumeration. |
| `API_RATE_LIMIT_READ_PER_MINUTE` | `240` | Per-client in-memory read budget. Set `0` only behind another trusted limiter. |
| `API_RATE_LIMIT_WRITE_PER_MINUTE` | `20` production / `30` local | Per-client in-memory mutation budget. |
| `API_MAX_REQUEST_BODY_BYTES` | `12582912` | Early `Content-Length` rejection at the application and proxy layers. |
| `API_MAX_CSV_UPLOAD_BYTES` | `2097152` | Bounded CSV read. |
| `API_MAX_REFERENCE_UPLOAD_BYTES` | `10485760` | Bounded FASTA read. |
| `BARCODE_SEARCH_TIMEOUT_SECONDS` | `30` | VSEARCH/BLASTN subprocess timeout, clamped to 1–300 seconds. |
| `MAX_PYTHON_SEARCH_COMPARISONS` | `50000000` | Reject excessive fallback-search work before computation. |
| `API_MAX_CONCURRENT_HEAVY_REQUESTS` | `2` production / `4` local | Process-local admission gate for compiler, search and Evidence Map work. |
| `REFERENCE_UPLOADS_ENABLED` | `false` production / `true` local | Disable persistent user FASTA uploads on the public demo. |
| `ECOGENESIS_EVIDENCE_ATTESTATION_SECRET` | empty | Operator-managed secret of at least 32 bytes; without it, holdout/reference evidence remains informational and cannot unlock scientific release. |
| `ECOGENESIS_EVIDENCE_ATTESTATION_KEY_ID` | `configured-local-hmac-v1` | Non-secret identifier used for explicit key rotation and attestation verification. |
| `TRUST_PROXY_HEADERS` | `true` in Compose | Use the proxy-appended client address for rate limiting. Do not enable for a directly exposed backend. |

The safe configuration is visible without secrets at `GET /api/system/limits`. The health response reports whether mutation authentication is required.

For a controlled API deployment:

```bash
export API_AUTH_REQUIRED=true
export API_AUTH_TOKEN="$(openssl rand -hex 32)"
export API_AUTH_PROTECT_RUN_READS=true
docker compose -f docker-compose.caddy.yml up -d --build
```

Send protected requests with `Authorization: Bearer <token>`. Do not put the token in `VITE_*` variables: Vite values are public browser assets. With authentication enabled, the current browser demo remains read-only unless a separate session/token broker is added.

The Caddy production stack now defaults to authenticated mutations and protected run/export reads. A public interactive contest demo may explicitly override `API_AUTH_REQUIRED=false` and retain rate limits, disabled reference uploads and resource bounds; that deliberate override is a demo posture, not a multi-user production security boundary.

For trusted scientific attestations, inject the attestation secret from the deployment secret manager and rotate the key id with the secret. Do not commit it, expose it through `VITE_*`, pass it as a request/CLI argument or treat a Docker Compose environment value as equivalent to a hardware-backed signing service. The shipped empty default is intentionally fail-closed.

## Container boundary

- Backend, nginx and Caddy images run as unprivileged UID/GID values.
- Compose drops Linux capabilities and enables `no-new-privileges`.
- Backend, nginx and Caddy root filesystems are read-only; writable state is limited to the explicit evidence-data mount, TLS/config volumes and bounded tmpfs mounts.
- CPU, memory and PID limits are set for each service.
- Uvicorn limits concurrent connections, disables its server banner and uses a five-second keep-alive timeout.
- The backend is not published in the Caddy deployment.

Run `docker compose config` and `docker compose -f docker-compose.caddy.yml config` before deployment. The Caddy stack deliberately retains `./data:/data/evidence` so existing runtime evidence and privacy-preserving analytics survive an in-place release. Keep that host directory owned by the unprivileged backend UID/GID, back it up before deployment and never publish it through Caddy.

## Artifact retention

Runtime runs remain on disk until an operator applies retention. Preview first:

```bash
backend/.venv/bin/python backend/scripts/prune_runtime_artifacts.py \
  --data-dir ./data \
  --older-than-days 30 \
  --keep-latest 20
```

Apply only after reviewing the JSON plan and confirming backups:

```bash
backend/.venv/bin/python backend/scripts/prune_runtime_artifacts.py \
  --data-dir ./data \
  --older-than-days 30 \
  --keep-latest 20 \
  --apply
```

The tool considers only immediate, non-symlink directories under `runs`, `barcode-runs` and `observatory-runs`. Uploaded reference datasets are deliberately excluded because their deletion requires a separate provenance-aware policy. Schedule the command externally (systemd timer, cron or an orchestrator) and alert on volume usage; it is not an in-process background task.

## CI evidence

`.github/workflows/ci.yml` runs on every pushed commit and pull request. It verifies the checked-out SHA, runs backend and frontend tests, builds the frontend, audits Python and Node dependencies, regenerates and checks evidence artifacts, runs Docker smoke tests, scans images for fixable critical vulnerabilities and publishes CodeQL results. Regenerated artifacts are uploaded with the exact commit SHA and a SHA-256 manifest for 14 days.

The Python runtime, development and audit environments use separate hash-locked requirements files. CI checks that every direct pin is represented by the matching lock, that every locked distribution has a SHA-256 hash, and that the runtime lock is a version-identical subset of the development lock. It then uses the hash-locked `pip-tools` toolchain to regenerate all three locks and rejects any lock-file diff.

Regenerated evidence is intentionally not compared with a raw `git diff --exit-code`. Run UUIDs, timestamps and ZIP container metadata are volatile provenance, so byte-for-byte output changes even when the scientific payload is equivalent. CI instead runs the domain-specific semantic verifiers and records a SHA-256 manifest for the exact artifacts produced by that run. This proves what CI inspected; it does not claim byte-for-byte reproducibility with the repository snapshot.

## Supply-chain boundary

Hash-locked Python packages, npm lock integrity, commit-pinned GitHub Actions, a digest-pinned Trivy scanner and digest-pinned Python, Node, nginx and Caddy base images reduce dependency ambiguity, but the build is not fully content-addressed. The `ubuntu-latest` runner label remains mutable. Debian packages installed by `apt-get` are also selected from the repository state available at build time rather than by an immutable snapshot and package hashes. Every image renewal requires a new verified multi-platform digest and repeated build, smoke and vulnerability-scan runs.

The remaining image/runner/package references should be replaced only with verified digests or snapshots and a documented renewal process; an unverified digest would create a false assurance. Dependabot tracks action updates, but every proposed commit change still requires review. Until the remaining boundaries are content-addressed, retain exact CI provenance and scan results with each accepted release and treat a rebuild at a later date as a new supply-chain event.

Repository settings still need to require these checks on the protected default branch. Tag the accepted submission commit only after the exact-commit workflow is green.

## Remaining production gaps

The in-memory limiter is per process and resets on restart. Long-running scientific work still executes in the API service. Before general public or multi-tenant use, add a shared gateway limiter, durable queue, isolated workers, cancellation, database-backed ownership, object storage, tenant authorization, centralized audit-log retention and backup/restore drills.
