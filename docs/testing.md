# Testing Plan

## Backend Regression

Run:

```bash
cd backend
.venv/bin/python -m pytest -q
```

Expected current result:

```text
35 passed, 1 skipped
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

Legacy `/api/evidence/*` tests remain active to guarantee the occurrence-audit layer still works for live GBIF context and regression.

## Frontend Regression

Run:

```bash
cd frontend
npm test -- --run
npm run build
```

Expected current result:

```text
5 frontend tests passed
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
8. Open `Math & proof`.
9. Open `Research audit`.
10. Confirm console errors are zero and there is no horizontal overflow.

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
