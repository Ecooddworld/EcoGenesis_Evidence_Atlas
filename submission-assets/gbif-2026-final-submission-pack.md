# GBIF 2026 Final Submission Pack

Deadline: **26 June 2026, 23:59 CEST (UTC+2)**  
Contest page: https://www.gbif.org/news/3DyM3tK5wgYipqyaHwG2c2/2026-ebbe-nielsen-challenge-open-for-submissions  
Official rules: https://www.gbif.org/awards/ebbe-2026-rules  
Entry form: https://www.survey-xact.dk/LinkCollector?key=YCAEZQR4SPC1

## Submission

**Molecular Evidence Conversion & Repair Engine for GBIF**  
Short title: **Barcode-to-GBIF Evidence Compiler**

One-liner:

> A deterministic workflow that turns DNA barcode, metabarcoding and Sequence ID-style outputs into safe, rank-aware and GBIF-ready molecular occurrence evidence.

Current architecture: **EcoGenesis Nexus V3 + GSEG/GSIG proof layer + GSIG Observatory**. The working compiler now exports hard-gate audit, prevented naive top-hit overclaims, data accounting ledger, state-machine audit, reference completeness audit, reference gap index, metadata bottlenecks, repair plan, split publishable-candidate / formal GBIF-ready / review templates, VSEA, theorem checklist, graph provenance and AI guardrail audits. The Observatory adds source registry checks, hashed GBIF snapshots, VSEA-to-graph visualization, OPO proof artifacts, GBIF export preview and AI-ready export guardrails.

## What To Submit

- Submission name/title: use the title above.
- Team members and affiliations: fill final names and contact.
- Abstract and rationale: copy from `submission-assets/gbif-entry-form-draft.md`.
- Operating instructions: copy from `submission-assets/gbif-entry-form-draft.md`.
- Hosted demo: https://ecooddworld.eu
- Submission video: https://ecooddworld.eu/submission-video/
- Direct MP4: https://ecooddworld.eu/submission-video/ecogenesis-platform-demo-ru-voice-subs.mp4
- Local final video: `submission-assets/platform-video/video/ecogenesis-platform-demo-ru-voice-subs.mp4`.
- Source/docs: https://github.com/Ecooddworld/EcoGenesis_Evidence_Atlas; the canonical docs are `README.md`, `docs/submission.md`, `docs/barcode-compiler-methodology.md`, `docs/production-caddy-deployment.md`, `docs/nexus-v3/EcoGenesis_Nexus_V3_FULL_PROJECT_RU.md` and `docs/testing.md`.

## Current Working Demo

Hosted:

```text
https://ecooddworld.eu
```

Local:

Run:

```bash
docker compose up --build
```

Open the hosted demo at https://ecooddworld.eu or local http://localhost:13100.

Primary flow:

```text
Run compiler
-> Upload CSV results
-> Validate preview
-> Generate from CSV
-> Inspect safe/blocked claims
-> Download Evidence Pack
```

Observatory flow:

```text
Observatory
-> Run GBIF-backed Aedes Spain
-> Inspect source snapshot, VSEA, graph and Judge tabs
-> Download Observatory Evidence Pack
```

Example outcomes:

```text
examples/aedes_good.csv              -> species-safe
examples/aedes_ambiguous.csv         -> genus-safe
examples/aedes_missing_metadata.csv  -> not-publishable
examples/aedes_weak_coverage.csv     -> weak
```

## Final Verification Status

Latest verification on 2026-06-26:

```text
backend pytest: 79 passed, 1 skipped
math viability verifier: pass, 2 packs, 142 checks, 0 failed
frontend tests: 14 passed
frontend build: passed
Docker compose CLI: available
Docker smoke: passed on the production stack; frontend, backend, proxy, VSEARCH backend, compiler, graph, Observatory and contest-readiness API checked
Hosted Caddy deployment: HTTPS 200, HTTP redirects to HTTPS, IP HTTP redirects to https://ecooddworld.eu, backend internal-only, CORS restricted to https://ecooddworld.eu and https://www.ecooddworld.eu
Local backend health: ok
Local frontend HTTP: 200
Contest readiness API: pass, 17 checks, 0 failed
Competition 100-sequence API run: expected decisions matched, hard_gate_failures=0, exports=90, theorem=pass, graph_roundtrip=pass, math_viability=pass
Adversarial 100-sequence stress run: expected decisions matched, false species-safe outside positive controls=0, exports=90, theorem=pass, graph_roundtrip=pass, math_viability=pass
Observatory demo report: hard_gate_status=pass, OPO artifacts present, VSEA Parquet=PAR1
Operability report: pass
```

Before final submission, re-run the commands in `submission-assets/final-submission-checklist.md` on the release commit.

## Remaining Manual Items

- Confirm the public source repository URL remains reachable for the final contest review path.
- Enter team/member details in the official form or approved private submission document.
- Paste the public submission video URL into the official GBIF form: https://ecooddworld.eu/submission-video/
- Keep the direct MP4 URL available if the form requires a file URL: https://ecooddworld.eu/submission-video/ecogenesis-platform-demo-ru-voice-subs.mp4
- Create release tag `v1.0-gbif-2026`.
- Confirm every submitted URL opens without login.
