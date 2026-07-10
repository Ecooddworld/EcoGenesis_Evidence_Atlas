# GSIG Observatory Extension

The GSIG Observatory is the contest-facing observability layer above the Barcode-to-GBIF compiler and GSEG/GSIG rule-evidence pack.

It implements the documentation package supplied as machine contracts:

- `backend/app/observatory/contracts/gsig_observatory_source_registry.yaml`
- `backend/app/observatory/contracts/gsig_observatory_pipeline_dag.yaml`
- `backend/app/observatory/contracts/gsig_observatory_ui_contract.yaml`
- generated `ecogenesis_gsig_observatory_release_checks_v1.json` (the historical proof-obligation contract is retained only as a deprecated compatibility source)

## Scope

The Observatory does:

- capture a small GBIF Aedes Spain occurrence snapshot;
- compute `snapshot_hash`, `query_sha256` and source provenance;
- compile the existing molecular barcode/GSEG demo into rule-evidence rows;
- preserve the GBIF snapshot as run-level context without inventing per-record molecular links;
- render the GBIF occurrence context map, rule-evidence matrix, evidence graph and release-check view in the UI;
- export GBIF and AI-ready preview datasets with claim-state guardrails;
- produce all 20 Observatory release-check artifacts.

The Observatory does not:

- infer species truth from occurrence records alone;
- claim absence from missing GBIF records;
- promote weak, blocked or hypothesis rows through visualization;
- let AI-ready exports overwrite rule-checked graph facts;
- link a molecular row to a GBIF occurrence without shared `eventID`, `materialSampleID`, specimen identifier or documented lineage;
- export trait, phenotype or function truth.

## API

The implemented routes live under `/api/observatory/*`:

- `GET /api/observatory/status`
- `GET /api/observatory/sources`
- `POST /api/observatory/run-demo`
- `GET /api/observatory/runs/{run_id}`
- `GET /api/observatory/vsea`
- `GET /api/observatory/segments/{segment_id}`
- `GET /api/observatory/segments/{segment_id}/taxa`
- `GET /api/observatory/segments/{segment_id}/sharedness`
- `GET /api/observatory/segments/{segment_id}/annotations`
- `GET /api/observatory/segments/{segment_id}/publications`
- `GET /api/observatory/segments/{segment_id}/claim-boundary`
- `GET /api/observatory/taxa/{taxon_id}/segments`
- `GET /api/observatory/claims/{claim_id}/provenance`
- `POST /api/observatory/export/gbif`
- `POST /api/observatory/export/ai-ready`

## Demo Modes

- `live_gbif_small`: tries a small GBIF `/occurrence/search` query for `Aedes albopictus` in Spain. If GBIF is unavailable, fixture fallback is recorded in `snapshot_manifest.json`.
- `offline_demo`: deterministic-input judge path using the bundled fixture and barcode demo records. The run records an input fingerprint, but does not claim clean-run reproducibility from a same-run self-hash.
- `cached_snapshot`: reserved alias for replaying cached snapshot behavior.

## Required Reports

Generate the reproducible Observatory report pack:

```bash
cd backend
.venv/bin/python scripts/generate_observatory_demo_report.py
```

Outputs are written to `reports/observatory-demo/`, including:

- `observatory_evidence_pack.zip`
- `observatory_report.md`
- `snapshot_manifest.json`
- `source_registry_audit.json`
- `observatory_vsea.csv`
- `observatory_vsea.parquet`
- `observatory_graph.jsonld`
- `gbif_export_preview.csv`
- `ai_ready_dataset.jsonl`
- `release_check_summary.json`
- `proof_summary.json` (deprecated compatibility alias)
- `observatory_output_verification.json`
- `observatory_output_verification.md`

## Verification

Run:

```bash
cd backend
.venv/bin/python -m pytest tests/test_gsig_observatory_reference_checks.py tests/test_observatory_api.py -q
.venv/bin/python scripts/verify_observatory_outputs.py
```

The tests validate source registry, pipeline DAG, UI contract, release checks, no visual claim promotion, AI label separation, the API layer, generated parquet and live fallback recording.

The output verifier validates the report directory after generation: manifest checksums must match the copied files, rule-evidence and occurrence Parquet files must be real Parquet files, CSV counts must reconcile with the JSON evidence pack, every graph item must carry a provenance hash, visualization and AI export audits must pass, weak rows must not become `positive_rule_supported`, molecular rows must remain unlinked from occurrence context, and the ZIP must contain the manifest-listed artifacts.

`offline_demo_reproducibility.json` is an informational self-check. Its status is `informational_self_check`, `deterministic` is `null`, and it explicitly records that no independent repeat execution or output comparison occurred. A real reproducibility claim requires a separate clean run and normalized output comparison.

The JSON evidence pack does not embed final SHA256 values for `observatory_evidence_pack.json` or `observatory_evidence_pack.zip`; those two self-referential files are marked `external_manifest_only` and verified through `observatory_demo_manifest.csv` and the run API manifest.

## UI Visualization Contract

The Observatory screen must show four non-table visuals before the tabbed data views:

- `GBIF occurrence context map`: plots the normalized GBIF occurrence context inside the requested bounding box and labels the snapshot hash.
- `Rule-evidence matrix`: shows each segment as a row across segment hash, snapshot hash, claim state, GBIF export state and AI label.
- `Evidence graph`: keeps the occurrence snapshot attached to the run, while molecular segment claims remain a separate evidence branch.
- `Release-check view`: shows all 20 Observatory checks as pass/review/fail/not-applicable nodes.

These visuals are explanatory only. They are covered by `visualization_guardrail_audit.csv` and must never promote weak, blocked or hypothesis claims.
