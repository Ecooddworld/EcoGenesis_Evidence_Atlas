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
- source-mode compatibility, empty live fallback and legacy fixture fallback
- 16-cell grid output with no-evidence cell separation
- gap-priority scoring and top survey priority cells
- Claim Guardrails
- Publisher Feedback grouping, severity and fix-first ranking
- Graph Memory generation and Obsidian-compatible vault export
- Decision Memo, Validation Summary and Submission Readiness generation
- Publisher issue template export generation
- Evidence Passport schema JSON validity
- fixture-based API run, GBIF status, live/fallback scenario metadata, taxon suggestion, region preset, map layers, quality, sampling gaps, citations, submission-readiness, demo scenario, run listing and export endpoints
- optional live smoke for `Aedes albopictus` in Spain, enabled with `RUN_LIVE_GBIF_SMOKE=1`

## Frontend

```bash
cd frontend
npm install
npm test
npm run build
```

Frontend tests cover:

- auto-run/default demo rendering
- two-mode `Presentation` and `Work with GBIF` rendering
- live-default payloads with `source_mode: "online_with_empty_fallback"` and `use_fixture: false`
- stale-result hiding after form edits
- GBIF taxon search, selected `taxonKey` payload and automatic rerun
- region preset selection, bbox field updates and automatic rerun
- Leaflet/OpenStreetMap live evidence map container rendering
- map layer controls for records, issues, grid cells and priorities
- Decision Memo, key risks, safe/blocked claims and source/provenance sections
- advanced drawer links for ZIP, Graph Memory, Submission Readiness, source summary and CSV/JSON evidence files

## Docker Acceptance

```bash
docker compose up --build
curl http://localhost:18100/health
```

Then open http://localhost:13100. The `Presentation` mode should appear first and show a compact live GBIF Evidence Passport. Switch to `Work with GBIF` to search taxa, select a `taxonKey`, choose a region or bbox and generate another passport. If GBIF is unavailable, the result should show a structured empty live fallback with 16 no-evidence cells and no reused fixture records.

Expected acceptance result:

- backend health returns `{"status":"ok"}`
- `GET /api/evidence/gbif-status` returns `ok`, `degraded` or `unavailable`
- frontend auto-renders the compact Presentation view, then the separate live GBIF workbench
- live GBIF completes when network access is available, empty live fallback avoids old fixture records when GBIF fails, and fixture mode still completes without network access
- exports include `evidence_pack.zip`, `evidence_vault.zip`, `passport.html`, `passport.md`, `evidence_pack.json`, `decision_memo.json`, `decision_memo.md`, `submission_readiness.json`, `submission_readiness.md`, `validation_summary.json`, `validation_summary.md`, `impact_brief.md`, `video_script.md`, `evidence_graph.json`, `graph_memory.md`, `run.json`, `source_summary.json`, `demo_scenario.json`, `records.geojson`, `quality_metrics.csv`, `gap_priorities.csv`, `readiness_scorecard.csv`, `dataset_contributions.csv`, `publisher_feedback.csv`, `publisher_issue_templates.md`, `derived_dataset_recipe.json`, `provenance.json`, `citations.md`, `claim_guardrails.md`, `methods_text.md` and `publisher_feedback.md`
- `evidence_pack.zip` contains a `vault/` Markdown directory and `evidence_vault.zip` opens as a standalone offline evidence-memory bundle

## CLI Smoke

```bash
backend/.venv/bin/python backend/scripts/evidence_passport_cli.py \
  --source-mode fixture \
  --taxon "Aedes albopictus" \
  --taxon-key 1651430 \
  --region-name "Spain fixture smoke" \
  --bbox=-10,35,4.5,44.5 \
  --purpose invasive_watch \
  --output-dir /tmp/ecogenesis-cli-smoke
```

Acceptance: the command exits with code `0`, prints a JSON summary, and `/tmp/ecogenesis-cli-smoke/evidence_pack.zip`, `decision_memo.md`, `publisher_issue_templates.md` and `source_summary.json` exist.
