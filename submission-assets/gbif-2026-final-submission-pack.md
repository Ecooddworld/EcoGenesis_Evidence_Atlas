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
- Video URL: paste the public no-login video URL into the official form after upload.
- Local final video for upload: `submission-assets/barcode-video/video/ecogenesis-barcode-to-gbif-english-voice-ru-subs.mp4`.
- Source/docs links:
  - https://github.com/oddworld666/EcoGenesis_Evidence_Atlas
  - https://github.com/oddworld666/EcoGenesis_Evidence_Atlas/blob/main/README.md
  - https://github.com/oddworld666/EcoGenesis_Evidence_Atlas/blob/main/docs/submission.md
  - https://github.com/oddworld666/EcoGenesis_Evidence_Atlas/blob/main/docs/barcode-compiler-methodology.md
  - https://github.com/oddworld666/EcoGenesis_Evidence_Atlas/blob/main/docs/nexus-v3/EcoGenesis_Nexus_V3_FULL_PROJECT_RU.md
  - https://github.com/oddworld666/EcoGenesis_Evidence_Atlas/blob/main/docs/testing.md

## Current Working Demo

Run:

```bash
docker compose up --build
```

Open http://localhost:13100.

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

Latest local verification on 2026-06-24:

```text
backend pytest: 77 passed, 1 skipped
frontend tests: 14 passed
frontend build: passed
Docker compose CLI: available
Docker smoke: passed on the production stack; frontend, backend, proxy, VSEARCH backend, compiler, graph, Observatory and contest-readiness API checked
Local backend health: ok
Local frontend HTTP: 200
Contest readiness API: pass, 17 checks, 0 failed
Competition 100-sequence API run: expected decisions matched, hard_gate_failures=0, exports=89, theorem=pass, graph_roundtrip=pass
Adversarial 100-sequence stress run: expected decisions matched, false species-safe outside positive controls=0, exports=89, theorem=pass, graph_roundtrip=pass
Observatory demo report: hard_gate_status=pass, OPO artifacts present, VSEA Parquet=PAR1
Operability report: pass
```

Before final submission, re-run the commands in `submission-assets/final-submission-checklist.md` on the release commit.

## Remaining Manual Items

- Keep the repository private unless final contest submission rules require public source; otherwise add judge access or provide the approved private source/docs links.
- Enter team/member details in the official form or approved private submission document.
- Upload the final CSV Upload -> Score demo video from `submission-assets/barcode-video/video/ecogenesis-barcode-to-gbif-english-voice-ru-subs.mp4`.
- Paste the public video URL into the official GBIF form after upload.
- Create GitHub release `v1.0-gbif-2026`.
- Confirm every submitted URL opens without login.
