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
- Claim Guardrails
- Publisher Feedback grouping
- fixture-based API run, demo scenario, run listing and export endpoints

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
- SVG map rendering
- purpose comparison and source/provenance sections
- grouped ZIP and individual download links

## Docker Acceptance

```bash
docker compose up --build
curl http://localhost:18100/health
```

Then open http://localhost:13100. The default fixture Evidence Passport should appear automatically.

Expected acceptance result:

- backend health returns `{"status":"ok"}`
- frontend auto-renders a complete Evidence Passport workbench
- fixture run completes without network access
- exports include `evidence_pack.zip`, `passport.html`, `passport.md`, `evidence_pack.json`, `run.json`, `source_summary.json`, `demo_scenario.json`, `records.geojson`, `quality_metrics.csv`, `readiness_scorecard.csv`, `dataset_contributions.csv`, `citations.md`, `claim_guardrails.md` and `publisher_feedback.md`
