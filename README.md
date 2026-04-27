# EcoGenesis Evidence Atlas

EcoGenesis Evidence Atlas turns GBIF-mediated occurrence data into reproducible **Evidence Passports** for a selected taxon, region and decision purpose.

The MVP is intentionally narrow: it is not the full EcoGenesis platform. It focuses on one judge-ready workflow:

1. Open the app.
2. The default live GBIF Evidence Passport appears automatically. If GBIF is unavailable, the app shows an empty no-evidence grid rather than reusing old fixture records.
3. Review the Leaflet/OpenStreetMap evidence map, purpose comparison, sampling-gap priorities, source/provenance, quality risks, dataset contributors, citation guidance and responsible claim guardrails.
4. Search GBIF taxa, choose a `taxonKey`, pick a region preset or edit the bbox, then generate another real-data passport.
5. Download a citation-ready evidence pack, including a single ZIP bundle.

## Quick Start

```bash
docker compose up --build
```

Open:

- Frontend: http://localhost:13100
- Backend health: http://localhost:18100/health
- Backend docs: http://localhost:18100/docs

The first screen auto-runs `Live GBIF`, so users see real GBIF-mediated records when the API is reachable. The deterministic fixture remains available as a separate `Offline sample` source for offline judging and regression tests.

## API

- `POST /api/evidence/run`
- `GET /api/evidence/demo-scenarios`
- `GET /api/evidence/region-presets`
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
- `passport.html`
- `passport.md`
- `evidence_pack.json`
- `run.json`
- `source_summary.json`
- `demo_scenario.json`
- `records.geojson`
- `quality_metrics.csv`
- `gap_priorities.csv`
- `readiness_scorecard.csv`
- `dataset_contributions.csv`
- `publisher_feedback.csv`
- `derived_dataset_recipe.json`
- `provenance.json`
- `citations.md`
- `claim_guardrails.md`
- `methods_text.md`
- `publisher_feedback.md`

## GBIF Citation

This tool preserves `datasetKey`, record counts, licenses and source metadata. For research or policy publication, create a DOI-backed GBIF occurrence download or derived dataset record and cite it according to GBIF guidance.

See `docs/gbif-data-use-and-citation.md`.

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

The UI includes auto-demo loading, GBIF taxon search, selectable `taxonKey`, backend-provided live region presets, editable bbox coordinates, source-mode selection, a real Leaflet/OpenStreetMap evidence map, readiness component weights, purpose comparison, deterministic Sampling Gap Engine, scientific interpretation, Claim Guardrails, Citation Autopilot, Publisher Feedback and grouped export links with SHA-256 checksums in export metadata.
