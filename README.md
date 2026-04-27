# EcoGenesis Evidence Atlas

EcoGenesis Evidence Atlas turns GBIF-mediated occurrence data into reproducible **Evidence Passports** for a selected taxon, region and decision purpose.

The MVP is intentionally narrow: it is not the full EcoGenesis platform. It focuses on one judge-ready workflow:

1. Open the app.
2. The default fixture Evidence Passport appears automatically.
3. Review the SVG evidence map, purpose comparison, sampling-gap priorities, source/provenance, quality risks, dataset contributors, citation guidance and responsible claim guardrails.
4. Optionally switch source mode to online GBIF with fixture fallback.
5. Download a citation-ready evidence pack, including a single ZIP bundle.

## Quick Start

```bash
docker compose up --build
```

Open:

- Frontend: http://localhost:13100
- Backend health: http://localhost:18100/health
- Backend docs: http://localhost:18100/docs

The first screen auto-runs a deterministic fixture demo, so judges can inspect a complete passport without network access. Online GBIF modes are available from the source selector.

## API

- `POST /api/evidence/run`
- `GET /api/evidence/demo-scenarios`
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
  "region_name": "Spain demo bbox",
  "bbox": [-10.0, 35.0, 4.5, 44.5],
  "purpose": "invasive_watch",
  "source_mode": "fixture",
  "use_fixture": true,
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

The UI includes auto-demo loading, backend-provided presets, source-mode selection, a scientific SVG evidence map with geographic context, readiness component weights, purpose comparison, deterministic Sampling Gap Engine, scientific interpretation, Claim Guardrails, Citation Autopilot, Publisher Feedback and grouped export links with SHA-256 checksums in export metadata.
