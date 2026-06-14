# GSIG Observatory Extension

The GSIG Observatory is the contest-facing observability layer above the Barcode-to-GBIF compiler and GSEG/GSIG proof pack.

It implements the documentation package supplied as machine contracts:

- `backend/app/observatory/contracts/gsig_observatory_source_registry.yaml`
- `backend/app/observatory/contracts/gsig_observatory_pipeline_dag.yaml`
- `backend/app/observatory/contracts/gsig_observatory_ui_contract.yaml`
- `backend/app/observatory/contracts/ecogenesis_gsig_observatory_proof_obligations_v4.json`

## Scope

The Observatory does:

- capture a small GBIF Aedes Spain occurrence snapshot;
- compute `snapshot_hash`, `query_sha256` and source provenance;
- compile the existing molecular barcode/GSEG demo into VSEA rows;
- link occurrence context and molecular evidence in a graph;
- export GBIF and AI-ready preview datasets with claim-state guardrails;
- produce all 20 Observatory proof-obligation artifacts.

The Observatory does not:

- infer species truth from occurrence records alone;
- claim absence from missing GBIF records;
- promote weak, blocked or hypothesis rows through visualization;
- let AI-ready exports overwrite verified graph facts;
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
- `offline_demo`: deterministic judge path using the bundled fixture and barcode demo records.
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
- `proof_summary.json`

## Verification

Run:

```bash
cd backend
.venv/bin/python -m pytest tests/test_gsig_observatory_reference_checks.py tests/test_observatory_api.py -q
```

The tests validate source registry, pipeline DAG, UI contract, proof obligations, no visual claim promotion, AI label separation, the API layer, generated parquet and live fallback recording.
