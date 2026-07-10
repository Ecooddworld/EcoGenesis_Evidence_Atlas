# GBIF 2026 Final Submission Pack

Deadline: **26 June 2026, 23:59 CEST (UTC+2)**  
Contest page: https://www.gbif.org/news/3DyM3tK5wgYipqyaHwG2c2/2026-ebbe-nielsen-challenge-open-for-submissions  
Official rules: https://www.gbif.org/awards/ebbe-2026-rules  
Entry form: https://www.survey-xact.dk/LinkCollector?key=YCAEZQR4SPC1

## Submission

**Molecular Evidence Conversion & Repair Engine for GBIF**  
Short title: **Barcode-to-GBIF Evidence Compiler**

One-liner:

> A deterministic workflow that turns DNA barcode, metabarcoding and Sequence ID-style outputs into bounded rank results, GBIF validation candidates and explicit repair actions.

Current architecture: **Barcode-to-GBIF Evidence Compiler + Evidence Map + advanced graph audits**. The working compiler exports run-local gate checks, prevented naive top-hit overclaims, data accounting, state-machine and reference-completeness audits, metadata bottlenecks, repair plans, validation-candidate/review templates, rule-evidence rows, a release-invariant checklist, graph provenance and AI guardrails. The Evidence Map adds source-registry checks, hashed GBIF snapshots, unlinked occurrence context, rule-evidence visualization and GBIF validation-candidate previews. These artifacts support inspection; they are not formal proof, independent taxonomic validation or evidence of GBIF acceptance.

## What To Submit

- Submission name/title: use the title above.
- Team members and affiliations: fill final names and contact.
- Abstract and rationale: copy from `submission-assets/gbif-entry-form-draft.md`.
- Operating instructions: copy from `submission-assets/gbif-entry-form-draft.md`.
- Hosted demo: https://ecooddworld.eu
- Submission video: https://ecooddworld.eu/submission-video/
- Direct MP4: https://ecooddworld.eu/submission-video/ecogenesis-gbif-contest-demo-en-subs.mp4
- Local final video: `submission-assets/contest-video-v2/video/ecogenesis-gbif-contest-demo-en-subs.mp4`.
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
-> Inspect bounded/blocked results
-> Download Evidence Pack
```

Evidence Map flow:

```text
Evidence Map
-> Run reproducible judge demo
-> Inspect source snapshot, rule-evidence rows, graph and Judge tabs
-> Download Evidence Map Pack
```

Example outcomes:

```text
examples/aedes_good.csv              -> review-only ambiguous unless external reference/QC evidence is supplied
examples/aedes_ambiguous.csv         -> genus rule-pass (genus-safe compatibility token)
examples/aedes_missing_metadata.csv  -> not-publishable
examples/aedes_weak_coverage.csv     -> weak
```

## Final Verification Status

Current local regression snapshot on 2026-07-10 (re-run on the exact release commit):

```text
backend pytest: full suite passed at this local snapshot; exact count belongs to exact-commit CI
math viability verifier: pass, 2 packs, 142 checks, 0 failed
frontend tests: 16 passed
frontend build: passed
Docker compose CLI: available
Docker smoke: passed on the production stack; frontend, backend, proxy, VSEARCH backend, compiler, graph, Observatory and contest-readiness API checked
Hosted Caddy deployment: HTTPS 200, HTTP redirects to HTTPS, IP HTTP redirects to https://ecooddworld.eu, backend internal-only, CORS restricted to https://ecooddworld.eu and https://www.ecooddworld.eu
Local backend health: ok
Local frontend HTTP: 200
Contest readiness API: review, 18 checks, 0 failed, 1 external-validation review item
Competition 100-row repeated-fixture regression: expected decisions matched, hard_gate_failures=0, exports=98, release-invariant gate=review, graph_roundtrip=pass, math_viability=pass
Adversarial 100-row repeated-fixture regression: expected decisions matched, hard_gate_failures=0, exports=98, release-invariant gate=review, graph_roundtrip=pass, math_viability=pass
Evidence Map demo report: hard_gate_status=pass, release checks present, rule-evidence Parquet=PAR1; occurrence rows remain unlinked context
Operability report: pass
```

Before final submission, re-run the commands in `submission-assets/final-submission-checklist.md` on the release commit.

## Remaining Manual Items

- Confirm the public source repository URL remains reachable for the final contest review path.
- Enter team/member details in the official form or approved private submission document.
- Paste the public submission video URL into the official GBIF form: https://ecooddworld.eu/submission-video/
- Keep the direct MP4 URL available if the form requires a file URL: https://ecooddworld.eu/submission-video/ecogenesis-gbif-contest-demo-en-subs.mp4
- Create release tag `v1.0-gbif-2026`.
- Confirm every submitted URL opens without login.
