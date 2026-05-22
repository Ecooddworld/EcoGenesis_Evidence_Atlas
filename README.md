# EcoGenesis Evidence Atlas

EcoGenesis Evidence Atlas turns GBIF-mediated occurrence data into reproducible **Evidence Passports** for a selected taxon, region and decision purpose.

The MVP is intentionally narrow: it is not the full EcoGenesis platform. It now exposes two judge-friendly modes:

1. `Presentation`: a compact contest view for judges, with the problem, current verdict, GBIF status, evidence map, safe/blocked claims and a one-click evidence pack download.
2. `Work with GBIF`: a minimal live workbench where users search GBIF taxa, lock a `taxonKey`, select a region preset or bbox, choose a purpose and generate a real-data Evidence Passport.

The public UI defaults to `Live GBIF`. If GBIF is unavailable, the app shows a clear empty no-evidence fallback and explicitly states that fixture records were not reused. Offline fixture data remains available for tests, demo generation and regression work only.

## Quick Start

```bash
docker compose up --build
```

Open:

- Frontend: http://localhost:13100
- Backend health: http://localhost:18100/health
- Backend docs: http://localhost:18100/docs

The first screen auto-runs `Live GBIF`, so users see real GBIF-mediated records when the API is reachable. The deterministic fixture is hidden from the main UX and remains available only for development, offline demo generation and regression tests.

## API

- `POST /api/evidence/run`
- `GET /api/evidence/demo-scenarios`
- `GET /api/evidence/region-presets`
- `GET /api/evidence/gbif-status`
- `GET /api/evidence/taxon-suggest?q={query}`
- `GET /api/evidence/runs`
- `GET /api/evidence/runs/{run_id}`
- `GET /api/evidence/runs/{run_id}/overview`
- `GET /api/evidence/runs/{run_id}/passport`
- `GET /api/evidence/runs/{run_id}/map`
- `GET /api/evidence/runs/{run_id}/map-layers`
- `GET /api/evidence/runs/{run_id}/quality`
- `GET /api/evidence/runs/{run_id}/sampling-gaps`
- `GET /api/evidence/runs/{run_id}/claims`
- `GET /api/evidence/runs/{run_id}/citations`
- `GET /api/evidence/runs/{run_id}/publisher-feedback`
- `GET /api/evidence/runs/{run_id}/graph-memory`
- `GET /api/evidence/runs/{run_id}/submission-readiness`
- `GET /api/evidence/runs/{run_id}/exports`
- `GET /api/evidence/runs/{run_id}/exports/{artifact_name}`

Example request:

```json
{
  "taxon": "Aedes albopictus",
  "taxon_key": 1651430,
  "region_name": "Spain live GBIF bbox",
  "bbox": [-10.0, 35.0, 4.5, 44.5],
  "purpose": "invasive_watch",
  "source_mode": "online_with_empty_fallback",
  "use_fixture": false,
  "max_records": 300
}
```

## Evidence Pack Artifacts

Each run exports:

- `evidence_pack.zip`
- `evidence_vault.zip`
- `passport.html`
- `passport.md`
- `evidence_pack.json`
- `decision_memo.json`
- `decision_memo.md`
- `submission_readiness.json`
- `submission_readiness.md`
- `validation_summary.json`
- `validation_summary.md`
- `impact_brief.md`
- `video_script.md`
- `evidence_graph.json`
- `graph_memory.md`
- `run.json`
- `source_summary.json`
- `demo_scenario.json`
- `records.geojson`
- `quality_metrics.csv`
- `gap_priorities.csv`
- `readiness_scorecard.csv`
- `dataset_contributions.csv`
- `publisher_feedback.csv`
- `publisher_issue_templates.md`
- `derived_dataset_recipe.json`
- `provenance.json`
- `citations.md`
- `claim_guardrails.md`
- `methods_text.md`
- `publisher_feedback.md`

The main `evidence_pack.zip` also includes a `vault/` directory with portable Markdown notes for the run, taxon, region, datasets, issues, claims, actions and GBIF citation checklist. `evidence_vault.zip` contains that same Obsidian-compatible memory layer as a standalone bundle.

The machine-readable pack follows `schemas/evidence_passport.schema.json`, which gives reviewers and downstream tools a stable contract for `run`, `source_summary`, `decision_memo`, map layers, claims, citations and exports.

The submission kit files are designed for judges and reviewers:

- `decision_memo.md`: the 40-second answer to what the data can and cannot support
- `submission_readiness.md`: contest checklist, accepted research comments and remaining blockers
- `validation_summary.md`: validation checks and the three recommended demo scenarios
- `impact_brief.md`: why this helps GBIF users, publishers and EcoGenesis
- `video_script.md`: a three-minute screen-recording script
- `publisher_issue_templates.md`: copy-ready, evidence-backed feedback messages for GBIF data publishers or node data managers

## CLI Runner

The browser UI is the primary judge experience, but the same workflow can be run from the command line:

```bash
backend/.venv/bin/python backend/scripts/evidence_passport_cli.py \
  --taxon "Lynx pardinus" \
  --taxon-key 2435261 \
  --region-name "Iberian Peninsula live bbox" \
  --bbox=-10,35,4.5,44.5 \
  --purpose dataset_quality_review \
  --source-mode online_with_empty_fallback \
  --output-dir reports/cli-lynx
```

The command writes the same `Evidence Pack` files as the API and prints the `run_id`, GBIF status, record count and pack location. Use `--source-mode fixture` only for offline tests and regression checks.

## GBIF Citation

This tool preserves `datasetKey`, record counts, licenses and source metadata. For research or policy publication, create a DOI-backed GBIF occurrence download or derived dataset record and cite it according to GBIF guidance.

See `docs/gbif-data-use-and-citation.md`.

For the contest narrative, demo path and operating instructions, see `docs/submission.md`.

Prepared submission assets, including the local demo video, screenshots, entry-form draft and final checklist, live in `submission-assets/`.

## Testing

```bash
cd backend
pytest

cd ../frontend
npm install
npm test
npm run build
```

Docker smoke:

```bash
docker compose up --build
curl http://localhost:18100/health
```

The UI includes the two-mode Presentation/Work with GBIF flow, GBIF API status, live taxon search, selectable `taxonKey`, backend-provided region presets, editable bbox coordinates, a real Leaflet/OpenStreetMap evidence map, Decision Memo, key quality risks, Claim Guardrails and compact export links. Advanced outputs such as Graph Memory, Submission Readiness, Publisher Feedback, raw quality tables and machine-readable exports remain in `evidence_pack.zip` and the `Advanced evidence files` drawer instead of crowding the main workflow.
