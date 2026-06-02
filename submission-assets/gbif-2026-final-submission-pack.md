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

Current architecture: **EcoGenesis Nexus V3**. The working compiler now exports hard-gate audit, prevented naive top-hit overclaims, reference gap index, metadata bottlenecks, repair plan and split GBIF-ready/review templates.

## What To Submit

- Submission name/title: use the title above.
- Team members and affiliations: fill final names and contact.
- Abstract and rationale: copy from `submission-assets/gbif-entry-form-draft.md`.
- Operating instructions: copy from `submission-assets/gbif-entry-form-draft.md`.
- Video URL: TODO after uploading final video.
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

Example outcomes:

```text
examples/aedes_good.csv              -> species-safe
examples/aedes_ambiguous.csv         -> genus-safe
examples/aedes_missing_metadata.csv  -> not-publishable
examples/aedes_weak_coverage.csv     -> weak
```

## Final Verification Status

Latest local verification on 2026-06-02:

```text
backend pytest: 35 passed, 1 skipped
frontend tests: 5 passed
frontend build: passed
GBIF API status: ok
CSV run good case: species_safe_records=1
Nexus V3 audit: hard_gate_failures=0
Browser smoke: Nexus V3 audit visible, console errors=0
```

Before final submission, re-run the commands in `submission-assets/final-submission-checklist.md` on the release commit.

## Remaining Manual Items

- Make repository public.
- Fill team/member details.
- Upload the final CSV Upload -> Score demo video from `submission-assets/barcode-video/video/ecogenesis-barcode-to-gbif-english-voice-ru-subs.mp4`.
- Replace TODO video URL in `submission-assets/gbif-entry-form-draft.md`.
- Create GitHub release `v1.0-gbif-2026`.
- Confirm every submitted URL opens without login.
