# Testing Plan

## Backend Regression

Run:

```bash
cd backend
.venv/bin/pytest -q
```

Expected current result:

```text
65 passed, 1 skipped
```

Required barcode compiler coverage:

- `examples/aedes_good.csv` -> `species-safe`
- `examples/aedes_ambiguous.csv` -> `genus-safe`
- `examples/aedes_missing_metadata.csv` -> taxonomic evidence preserved, publication blocked as `not-publishable`
- `examples/aedes_weak_coverage.csv` -> `weak`
- invalid DNA characters -> validation error
- missing `sequenceID` or `sequence` -> import error
- alias columns resolve correctly
- `/api/barcode/import-csv` returns normalized request, preview and validation summary
- `/api/barcode/run-csv` creates a run and Evidence Pack exports
- existing `/api/barcode/run` JSON endpoint remains compatible
- reference-search runs generated from pasted FASTA do not synthesize `eventDate` or `occurrenceID`;
- `python-local` search backend is review-only and blocks GBIF-ready publication;
- long-format hit tables with repeated `sequenceID` rows are grouped into one sequence record with multiple hits;
- `/api/barcode/fragment-graph` returns segment-level coordinates, source monitor data, known annotation hints and claim boundaries.
- `scientificName` conflicts with the molecular top hit block publication while preserving the molecular evidence state;
- Evidence Pack exports include `data_accounting_ledger.csv`, `state_machine_audit.csv`, `reference_completeness_audit.csv`, structured `publication_blockers.csv`, graph-backed `claim_boundaries.csv` and `profile_id` in `safe_taxonomic_assignments.csv`.
- GSEG/GSIG exports include `theorem_checklist.json`, real `verified_segment_evidence_array.parquet`, `graph_provenance_audit.csv`, `graph_roundtrip_audit.json`, `ai_output_guardrail_audit.csv` and `judge_reproducibility_report.md`.
- `tests/test_gseg_gsig_reference_checks.py` verifies the reference math and guardrail oracle for safe taxa, canonical segment hashing, sharedness, claim-state transitions, AI export preservation, provenance and BH-FDR.

Legacy `/api/evidence/*` tests remain active to guarantee the occurrence-audit layer still works for live GBIF context and regression.

## Frontend Regression

Run:

```bash
cd frontend
npm test
npm run build
```

Expected current result:

```text
13 frontend tests passed
production build passed
```

Required UI coverage:

- Judge overview renders.
- Run compiler opens.
- `Upload CSV results` block is visible.
- `Download CSV template` link is visible.
- CSV upload shows preview and validation warnings.
- `Generate from CSV` displays result dashboard and export links.
- Advanced JSON remains available for developer workflows.
- `Math & proof` opens.
- `Research audit` opens.
- `Data accounting ledger` renders after a run and shows denominators for candidate, safe, publishable and formal GBIF-ready states.

## API Smoke

Start backend and frontend:

```bash
cd backend
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 18100
```

```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 13100
```

Check:

```bash
curl http://127.0.0.1:18100/health
curl http://127.0.0.1:18100/api/evidence/gbif-status
curl http://127.0.0.1:18100/api/barcode/csv-template
curl -F file=@examples/aedes_good.csv http://127.0.0.1:18100/api/barcode/import-csv
curl -F file=@examples/aedes_good.csv http://127.0.0.1:18100/api/barcode/run-csv
```

Expected:

- health returns `ok`;
- GBIF status returns `ok` when GBIF is reachable;
- CSV template returns header row;
- import returns `validation.ok=true`;
- run returns `species_safe_records=1`.

## Browser Smoke

1. Open http://127.0.0.1:13100.
2. Open `Run compiler`.
3. Upload `examples/aedes_good.csv`.
4. Confirm preview and validation summary are visible.
5. Click `Generate from CSV`.
6. Confirm `species-safe` is visible.
7. Confirm key exports are visible:
   - `evidence_pack.zip`
   - `sequence_safety_table.csv`
   - `publication_blockers.csv`
   - `dwc_occurrence_core_publishable.csv`
   - `molecular_evidence_report.html`
   - `theorem_checklist.json`
   - `verified_segment_evidence_array.parquet`
   - `graph_provenance_audit.csv`
8. Open `Math & proof`.
9. Open `Research audit`.
10. Confirm console errors are zero and there is no horizontal overflow.

## Docker Smoke

Run from the repository root:

```bash
scripts/docker_smoke.sh
```

Expected:

- Docker builds the backend and frontend images.
- Backend health passes on the published backend port.
- Frontend Nginx serves the Vite shell and JavaScript asset.
- `/health` and `/api/*` work through the frontend proxy.
- `/api/barcode/search-status` reports `preferred_backend=vsearch` inside Docker.
- The mini Aedes reference-search compile path returns a completed run.
- The bundled shared-fragment graph path returns `higher-rank-shared`.
- The shared-fragment graph path includes segment evidence rather than only top-hit summary data.

## Operability Report

Run:

```bash
cd backend
.venv/bin/python scripts/verify_barcode_operability.py
```

Expected:

- status `pass`;
- direct compiler classes match the expected mixed batch;
- API classes match the expected mixed batch;
- Evidence Pack ZIP is valid;
- required exports are present;
- HTML report endpoint returns `200`.

## Competition Batch Reports

Current Docker-backed batch reports:

- `reports/competition-100-sequences/competition_100_sequence_report.md`
  - 100 records;
  - 89 exports;
  - expected decisions matched;
  - hard-gate failures: `0`;
  - 50 publishable candidates, 0 formal GBIF-ready rows;
  - GSEG/GSIG exports present, VSEA Parquet magic `PAR1`, theorem release gate `pass`, graph roundtrip `pass`.
- `reports/adversarial-100-sequences/adversarial_100_sequence_report.md`
  - 100 adversarial records across no-match, weak, ambiguity, metadata, assay, name-conflict, custom-marker and missing-evidence cases;
  - expected decisions matched;
  - hard-gate failures: `0`;
  - false species-safe outside positive controls: `0`;
  - GSEG/GSIG exports present, VSEA Parquet magic `PAR1`, theorem release gate `pass`, graph roundtrip `pass`.

Regenerate both reports:

```bash
cd backend
.venv/bin/python scripts/generate_competition_reports.py
```

Generated outputs:

- `reports/barcode-operability/operability_report.md`
- `reports/barcode-operability/operability_report.json`

## Live GBIF Scientific Hypothesis Suite

Run only when network access is available:

```bash
cd backend
.venv/bin/python scripts/run_scientific_hypothesis_suite.py --fresh --output-dir /tmp/ecogenesis-scientific-theory-suite
```

Acceptance:

- at least 1,000 deduplicated live GBIF occurrence records;
- at least 10 successful online scenarios;
- no fixture records counted;
- at least 100 hypothesis/claim rows;
- every claim has status, evidence pointer and caveat.

This suite validates the live GBIF occurrence-audit layer. It is not used as proof that the molecular compiler performs Sequence ID matching, because the molecular compiler works from supplied Sequence ID / BLAST-style match results.
