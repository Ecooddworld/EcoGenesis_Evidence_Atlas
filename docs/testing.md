# Testing

## Backend

```bash
cd backend
pytest
```

Backend tests cover:

- GBIF normalization and provenance preservation
- Hill/Coverage/Occupancy-like sampling metrics
- purpose-aware scoring
- source-mode compatibility and fixture fallback
- 16-cell grid output with no-evidence cell separation
- gap-priority scoring and top survey priority cells
- Claim Guardrails
- Publisher Feedback grouping
- fixture-based API run, live/fallback scenario metadata, taxon suggestion, region preset, map layers, quality, sampling gaps, citations, demo scenario, run listing and export endpoints

## Frontend

```bash
cd frontend
npm install
npm test
npm run build
```

Frontend tests cover:

- auto-run/default demo rendering
- source-mode selection payloads
- GBIF taxon search and selected `taxonKey` payload
- region preset selection and bbox field updates
- SVG map rendering
- Leaflet/OpenStreetMap live evidence map container rendering
- Sampling Gap Engine panel rendering
- purpose comparison and source/provenance sections
- grouped ZIP and individual download links

## Docker Acceptance

```bash
docker compose up --build
curl http://localhost:18100/health
```

Then open http://localhost:13100. The default live GBIF Evidence Passport should appear automatically, or visibly fall back to the offline fixture if GBIF is unavailable.

Expected acceptance result:

- backend health returns `{"status":"ok"}`
- frontend auto-renders a complete Evidence Passport workbench
- live GBIF with fallback completes when network access is available, and fixture mode still completes without network access
- exports include `evidence_pack.zip`, `passport.html`, `passport.md`, `evidence_pack.json`, `run.json`, `source_summary.json`, `demo_scenario.json`, `records.geojson`, `quality_metrics.csv`, `gap_priorities.csv`, `readiness_scorecard.csv`, `dataset_contributions.csv`, `publisher_feedback.csv`, `derived_dataset_recipe.json`, `provenance.json`, `citations.md`, `claim_guardrails.md`, `methods_text.md` and `publisher_feedback.md`
