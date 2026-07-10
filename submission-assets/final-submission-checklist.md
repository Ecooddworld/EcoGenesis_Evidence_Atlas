# Final GBIF Submission Checklist

Deadline: **26 June 2026, 23:59 CEST (UTC+2)**
Contest page: https://www.gbif.org/news/3DyM3tK5wgYipqyaHwG2c2/2026-ebbe-nielsen-challenge-open-for-submissions
Official rules: https://www.gbif.org/awards/ebbe-2026-rules
Entry form: https://www.survey-xact.dk/LinkCollector?key=YCAEZQR4SPC1

## Prepared

- [x] Final project positioning: Molecular Evidence Conversion & Repair Engine for GBIF.
- [x] Working module: Barcode-to-GBIF Evidence Compiler.
- [x] Main UX: Upload CSV results -> Check input -> Generate from CSV -> Inspect bounded/blocked results -> Download exports.
- [x] CSV template and CSV import/run API exist.
- [x] JSON API remains compatible for developers.
- [x] Example CSVs exist:
  - `aedes_good.csv` -> review-only `ambiguous` unless external reference-completeness and sequence-QC evidence are supplied
  - `aedes_ambiguous.csv` -> primary display `genus rule-pass` (`genus-safe` compatibility token)
  - `aedes_missing_metadata.csv` -> `not-publishable`
  - `aedes_weak_coverage.csv` -> `weak`
- [x] Evidence Pack exports Darwin Core/DNA-derived validation candidates, CSV reports, HTML report, methods, citations, rule-evidence and graph audit artifacts, and ZIP.
- [x] Evidence Map tab, API, report pack and release-check artifacts exist; occurrence context stays unlinked from molecular rows.
- [x] GBIF occurrence-audit layer exists for API status and a historical 1000-record / 100-hypothesis context suite; it is not molecular validation.
- [x] Mathematical methodology and failure-mode-invariant docs exist.
- [x] License, citation and data license files exist.
- [x] Entry form copy is prepared in `submission-assets/gbif-entry-form-draft.md`.
- [x] Final public workflow-first video exists at `https://ecooddworld.eu/submission-video/`.
- [x] Local MP4, subtitles and transcript exist under `submission-assets/contest-video-v2/video/` and are regenerated from the current bounded-claim voiceover.
- [x] Hosted demo is deployed at `https://ecooddworld.eu`.
- [x] Caddy handles HTTPS and redirects HTTP to HTTPS.
- [x] Backend is internal-only behind the Caddy reverse proxy.
- [x] Production CORS is restricted to `https://ecooddworld.eu` and `https://www.ecooddworld.eu`.

## Must Do Before Pressing Submit

- [x] Source repository is public for judge review: https://github.com/Ecooddworld/EcoGenesis_Evidence_Atlas.
- [ ] Enter final team member names, affiliations, country and contact email in the official GBIF form or approved private submission document.
- [x] Record or rebuild the final video around the current CSV Upload -> Score workflow.
- [ ] Upload the video to a public no-cost URL that plays without login.
- [x] Add captions or transcript for the video.
- [ ] Paste the public video URL into the official GBIF form after upload.
- [ ] Create a release tag, for example `v1.0-gbif-2026`.
- [ ] Add the release URL to the final entry form if available.
- [ ] Re-run all final verification commands on the release commit.
- [ ] Confirm no secrets, private local paths or private API keys are present in submitted materials.

## Final Verification Commands

```bash
cd backend
.venv/bin/python -m pytest -q
.venv/bin/python scripts/verify_barcode_operability.py
.venv/bin/python scripts/generate_competition_reports.py
.venv/bin/python scripts/generate_observatory_demo_report.py
.venv/bin/python scripts/run_scientific_hypothesis_suite.py --fresh --output-dir /tmp/ecogenesis-scientific-theory-suite
```

```bash
cd frontend
npm run lint
npm test
npm run build
```

## Manual Browser Smoke

1. Open `https://ecooddworld.eu` or local http://localhost:13100.
2. Open `Run compiler`.
3. Upload `examples/aedes_good.csv`.
4. Confirm CSV preview and input checks are visible.
5. Click `Generate from CSV`.
6. Confirm the row remains review-only unless the required external reference/QC evidence is supplied; do not expect a species-level pass from the basic CSV alone.
7. Confirm `evidence_pack.zip`, `sequence_safety_table.csv`, `publication_blockers.csv`, `dwc_occurrence_core_validation_candidates.csv`, `molecular_evidence_report.html`, `math_viability_audit.json`, `release_invariant_checklist.json`, `rule_evidence_segment_array.parquet` and `graph_provenance_audit.csv` are visible or downloadable.
8. Open `Methods & Audits` and confirm formulas and run-local invariants render.
9. Open `Evidence Map`, run `Run reproducible judge demo`, and confirm `observatory_evidence_pack.zip`, `snapshot_manifest.json`, the rule-evidence Parquet export and release-check rows are visible.
10. Open `Regression & Audits` and confirm the occurrence-context suite is clearly separated from molecular validation.
11. Confirm browser console errors are zero.

## Entry Form Fields

- Submission name/title: ready.
- Team members: enter in the official form or approved private submission document.
- Abstract and rationale: ready.
- Operating instructions: ready.
- Video link: https://ecooddworld.eu/submission-video/
- Source/documentation links: ready; public repository is `https://github.com/Ecooddworld/EcoGenesis_Evidence_Atlas`.

## Risk Notes

- Do not present FASTA-only upload or a local rule pass as independent species validation; representative references, sequence QC and expert/external review are required.
- Do not claim species absence from no-evidence cells.
- Do not claim true distribution or population trend without separate methods.
- Do not claim phenotype truth from barcode evidence.
- Do not submit only local file paths; use public URLs.
