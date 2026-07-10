# Testing Plan

## Backend Regression

Run:

```bash
cd backend
.venv/bin/python -m pip install --require-hashes -r requirements-dev.lock
.venv/bin/pytest -q
```

Expected: all collected regression and security tests pass; the live GBIF smoke may remain skipped when its explicit network flag is absent.

Required barcode compiler coverage:

- `examples/aedes_good.csv` -> review-only `ambiguous` because server-attested reference completeness, barcode-gap CI and sequence-QC evidence are not present in the CSV; its `expectedDecision` is also `ambiguous`
- `examples/aedes_ambiguous.csv` -> primary display `genus rule-pass` (`genus-safe` remains an API compatibility token)
- `examples/aedes_missing_metadata.csv` -> missing scientific and publication evidence remains visible in review
- `examples/aedes_weak_coverage.csv` -> `weak`
- invalid DNA characters -> validation error
- missing `sequenceID` or `sequence` -> import error
- alias columns resolve correctly
- `/api/barcode/import-csv` returns normalized request, preview and validation summary
- `/api/barcode/run-csv` creates a run and Evidence Pack exports
- existing `/api/barcode/run` JSON endpoint remains compatible
- reference-search runs generated from pasted FASTA do not synthesize `eventDate` or `occurrenceID`;
- `python-local` search backend is review-only and blocks GBIF validation-candidate publication;
- long-format hit tables with repeated `sequenceID` rows are grouped into one sequence record with multiple hits;
- `/api/barcode/fragment-graph` returns segment-level coordinates, source monitor data, known annotation hints and claim boundaries.
- `scientificName` conflicts with the molecular top hit block publication while preserving the molecular evidence state;
- Evidence Pack exports include `data_accounting_ledger.csv`, `state_machine_audit.csv`, `reference_completeness_audit.csv`, structured `publication_blockers.csv`, graph-backed `claim_boundaries.csv` and `profile_id` in `safe_taxonomic_assignments.csv`.
- Advanced graph exports include `release_invariant_checklist.json`, real `rule_evidence_segment_array.parquet`, `graph_provenance_audit.csv`, `graph_roundtrip_audit.json`, `ai_output_guardrail_audit.csv` and `judge_reproducibility_report.md`.
- `tests/test_gseg_gsig_reference_checks.py` verifies the reference math and guardrail oracle for safe taxa, including an LCA recomputation that fails even when `safe_taxon` and `candidate_taxon` are identical aliases, plus canonical segment hashing, sharedness, claim-state transitions, AI export preservation, provenance and BH-FDR.
- Evidence Map exports include `observatory_evidence_pack.zip`, `snapshot_manifest.json`, `source_registry_audit.json`, the compatibility artifact `observatory_vsea.parquet` (displayed as rule-evidence rows), `observatory_graph.jsonld`, `gbif_export_preview.csv`, `ai_ready_dataset.jsonl`, `release_check_summary.json` and all 20 release-check results.
- `tests/test_gsig_observatory_reference_checks.py` verifies the Evidence Map source registry, pipeline DAG, UI contract, release checks, visual claim-state projection and AI label separation.
- `tests/test_observatory_api.py` verifies `/api/observatory/*`, generated parquet, GBIF fixture fallback recording, rule-evidence/segment/claim endpoints, export links and the non-passing `informational_self_check` boundary for same-run offline input fingerprints.
- `tests/test_math_viability.py` verifies the secondary formula-consistency oracle over default and edge-case packs.
- `tests/test_security.py` verifies mutation authentication, fail-closed configuration, rate/body/upload limits, compiler input quotas and aligner timeouts.
- `tests/test_scientific_gates.py` verifies valid HMAC attestations plus unsigned, invalid-signature, missing-secret, payload-tamper, subject-replay and expired-attestation failure paths for external holdout and reference-completeness evidence.
- `tests/test_retention.py` verifies that runtime retention is age-bounded, dry-run-first and preserves the configured newest runs.

Legacy `/api/evidence/*` tests remain active to guarantee the occurrence-audit layer still works for GBIF context and regression.

## Frontend Regression

Run:

```bash
cd frontend
npm run lint
npm test
npm run build
```

Expected: all frontend tests pass and the production build completes. The header test keeps the prototype and external-validation boundary visible.

Required UI coverage:

- Overview renders.
- Run Compiler opens.
- `Upload CSV results` block is visible.
- `Download CSV template` link is visible.
- CSV upload shows preview and validation warnings.
- `Generate from CSV` displays result dashboard and export links.
- Advanced JSON remains available for developer workflows.
- `Methods & Audits` opens.
- `Regression & Audits` opens (the compatibility route remains `/validation`).
- `Evidence Map` opens, runs the judge demo, renders rule-evidence and Judge audit screens.
- `Data accounting ledger` renders after a run and shows denominators for candidate, safe, publishable and GBIF validation-candidate states.

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
curl http://127.0.0.1:18100/api/observatory/status
curl -X POST http://127.0.0.1:18100/api/observatory/run-demo \
  -H 'Content-Type: application/json' \
  -d '{"mode":"offline_demo","force_fixture":true,"limit":50}'
```

Expected:

- health returns `ok`;
- GBIF status returns `ok` when GBIF is reachable;
- CSV template returns header row;
- import returns `validation.ok=true`;
- run returns `species_rule_pass_records=0` plus explicit missing-reference/QC blockers.
- Evidence Map run returns `hard_gate_status=pass`, four rule-evidence rows (`vsea_rows=4` compatibility field) and downloadable `observatory_evidence_pack.zip`.

## Browser Smoke

1. Open http://127.0.0.1:13100.
2. Open `Run Compiler`.
3. Upload `examples/aedes_good.csv`.
4. Confirm preview and validation summary are visible.
5. Click `Generate from CSV`.
6. Confirm the CSV result stays review-only and explains the missing scientific evidence.
7. Confirm key exports are visible:
   - `evidence_pack.zip`
   - `sequence_safety_table.csv`
   - `publication_blockers.csv`
   - `dwc_occurrence_core_validation_candidates.csv`
   - `molecular_evidence_report.html`
   - `release_invariant_checklist.json`
   - `rule_evidence_segment_array.parquet`
   - `graph_provenance_audit.csv`
8. Open `Methods & Audits`.
9. Open `Evidence Map`.
10. Click `Run reproducible judge demo`.
11. Confirm `GBIF snapshot`, `Rule evidence`, `Graph`, `Exports` and `Judge` screens render.
12. Confirm `observatory_evidence_pack.zip`, the compatibility artifact `observatory_vsea.parquet`, `snapshot_manifest.json` and `release_check_summary.json` are linked.
13. Open `Regression & Audits`.
14. Confirm console errors are zero and there is no horizontal overflow.

## Docker Smoke

Run from the repository root:

```bash
scripts/docker_smoke.sh
```

Expected:

- Docker builds the backend and frontend images.
- Backend health passes on the published backend port.
- Frontend production server serves the Vite shell and JavaScript asset.
- `/health` and `/api/*` work through the frontend proxy.
- `/api/barcode/search-status` reports `preferred_backend=vsearch` inside Docker.
- The mini Aedes reference-search compile path returns a completed run.
- The bundled shared-fragment graph path returns `higher-rank-shared`.
- The shared-fragment graph path includes segment evidence rather than only top-hit summary data.
- `/api/observatory/status` and `/api/observatory/run-demo` work through the frontend proxy.

## Math Viability

Run from the repository root:

```bash
backend/.venv/bin/python backend/scripts/verify_math_viability.py
```

Expected:

- status `pass`;
- 2 generated packs checked;
- 142 formula and invariant checks;
- match gates, ambiguity boundary, safe LCA, barcode gap, diagnostic k-mer probability, hard-gate invariant, publication separation and batch metrics all reconcile with the Evidence Pack.

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
  - 92 primary exports;
  - expected decisions matched;
  - hard-gate failures: `0`;
  - 50 publishable candidates, 0 GBIF validation-candidate rows;
  - Advanced graph exports present, math viability audit `pass`, rule-evidence Parquet magic `PAR1`, release gate `review` without external validation, graph roundtrip `pass`.
- `reports/adversarial-100-sequences/adversarial_100_sequence_report.md`
  - 100 adversarial records across no-match, weak, ambiguity, metadata, assay, name-conflict, custom-marker and missing-evidence cases;
  - expected decisions matched;
  - hard-gate failures: `0`;
  - unexpected species rule-pass in molecular-negative fixtures: `0`;
  - 92 primary exports;
  - Advanced graph exports present, math viability audit `pass`, rule-evidence Parquet magic `PAR1`, release gate `review` without external validation, graph roundtrip `pass`.

Regenerate both reports:

```bash
cd backend
.venv/bin/python scripts/generate_competition_reports.py
```

## Evidence Map Report

Current generated Evidence Map report:

- `reports/observatory-demo/README.md`
  - hard-gate status: `pass`;
  - 12 occurrence context rows;
  - 4 rule-evidence rows;
  - all 20 release-check artifacts present;
  - rule-evidence and occurrence Parquet magic `PAR1`;
  - output verification status `pass`.

Regenerate:

```bash
cd backend
.venv/bin/python scripts/generate_observatory_demo_report.py
```

Recheck existing generated outputs:

```bash
cd backend
.venv/bin/python scripts/verify_observatory_outputs.py
```

Generated verification outputs:

- `reports/observatory-demo/observatory_output_verification.md`
- `reports/observatory-demo/observatory_output_verification.json`

The verifier recomputes report-file SHA256 checksums, confirms ZIP contents, reconciles CSV counts with `observatory_evidence_pack.json`, checks graph provenance, enforces the visualization, AI export and GBIF claim-boundary guardrails, and verifies that self-referential JSON/ZIP checksums are delegated to the external manifest instead of being embedded as stale values.

## GBIF Occurrence-Audit Scientific Hypothesis Suite

Run only when network access is available:

```bash
cd backend
.venv/bin/python scripts/run_scientific_hypothesis_suite.py --fresh --output-dir /tmp/ecogenesis-scientific-theory-suite
```

Acceptance:

- at least 1,000 deduplicated GBIF occurrence records;
- at least 10 successful online scenarios;
- no fixture records counted;
- at least 100 hypothesis/claim rows;
- every claim has status, evidence pointer and caveat.

This suite validates the GBIF occurrence-audit layer in live network mode. It is not used as proof that the molecular compiler performs Sequence ID matching, because the molecular compiler works from supplied Sequence ID / BLAST-style match results.
