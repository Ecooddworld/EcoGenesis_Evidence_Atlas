# Final GBIF Submission Checklist

Deadline: **26 June 2026, 23:59 CEST (UTC+2)**
Contest page: https://www.gbif.org/news/3DyM3tK5wgYipqyaHwG2c2/2026-ebbe-nielsen-challenge-open-for-submissions
Official rules: https://www.gbif.org/awards/ebbe-2026-rules
Entry form: https://www.survey-xact.dk/LinkCollector?key=YCAEZQR4SPC1

## Prepared

- [x] Final project positioning: Molecular Evidence Conversion & Repair Engine for GBIF.
- [x] Working module: Barcode-to-GBIF Evidence Compiler.
- [x] Main UX: Upload CSV results -> Validate -> Generate from CSV -> Inspect safe/blocked claims -> Download exports.
- [x] CSV template and CSV import/run API exist.
- [x] JSON API remains compatible for developers.
- [x] Example CSVs exist:
  - `aedes_good.csv` -> `species-safe`
  - `aedes_ambiguous.csv` -> `genus-safe`
  - `aedes_missing_metadata.csv` -> `not-publishable`
  - `aedes_weak_coverage.csv` -> `weak`
- [x] Evidence Pack exports Darwin Core, DNA-derived templates, CSV reports, HTML report, methods, citations, evidence graph, GSEG/GSIG proof artifacts and ZIP.
- [x] GSIG Observatory tab, API, report pack and OPO proof artifacts exist.
- [x] GBIF occurrence-audit layer exists for API status and 1000-record / 100-claim validation.
- [x] Mathematical methodology and proof-by-failure-mode docs exist.
- [x] License, citation and data license files exist.
- [x] Entry form copy is prepared in `submission-assets/gbif-entry-form-draft.md`.
- [x] Final local explainer video exists: `submission-assets/barcode-video/video/ecogenesis-barcode-to-gbif-english-voice-ru-subs.mp4`.
- [x] Russian subtitles and English transcript exist for the final local video.
- [x] Hosted demo is deployed at `https://ecooddworld.eu`.
- [x] Caddy handles HTTPS and redirects HTTP to HTTPS.
- [x] Backend is internal-only behind the Caddy reverse proxy.
- [x] Production CORS is restricted to `https://ecooddworld.eu` and `https://www.ecooddworld.eu`.

## Must Do Before Pressing Submit

- [ ] Confirm the repository visibility follows the final contest rule; if it stays private, add judge access or an approved private review link.
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
npm test -- --run
npm run build
```

## Manual Browser Smoke

1. Open `https://ecooddworld.eu` or local http://localhost:13100.
2. Open `Run compiler`.
3. Upload `examples/aedes_good.csv`.
4. Confirm CSV preview and validation are visible.
5. Click `Generate from CSV`.
6. Confirm `species-safe` appears.
7. Confirm `evidence_pack.zip`, `sequence_safety_table.csv`, `publication_blockers.csv`, `dwc_occurrence_core_publishable.csv`, `molecular_evidence_report.html`, `math_viability_audit.json`, `theorem_checklist.json`, `verified_segment_evidence_array.parquet` and `graph_provenance_audit.csv` are visible or downloadable.
8. Open `Math & proof` and confirm formulas render.
9. Open `Observatory`, run `Run GBIF-backed Aedes Spain`, and confirm `observatory_evidence_pack.zip`, `snapshot_manifest.json`, `observatory_vsea.parquet` and Judge OPO rows are visible.
10. Open `Research audit` and confirm the 1000-record / 100-claim audit summary is visible.
11. Confirm browser console errors are zero.

## Entry Form Fields

- Submission name/title: ready.
- Team members: enter in the official form or approved private submission document.
- Abstract and rationale: ready.
- Operating instructions: ready.
- Video link: paste into the official form after public upload. Local file is ready at `submission-assets/barcode-video/video/ecogenesis-barcode-to-gbif-english-voice-ru-subs.mp4`.
- Source/documentation links: ready; keep private only if the contest review path accepts judge access or an approved private source link.

## Risk Notes

- Do not present FASTA-only upload as enough for `species-safe`; match results are required.
- Do not claim species absence from no-evidence cells.
- Do not claim true distribution or population trend without separate methods.
- Do not claim phenotype truth from barcode evidence.
- Do not submit only local file paths; use public URLs.
