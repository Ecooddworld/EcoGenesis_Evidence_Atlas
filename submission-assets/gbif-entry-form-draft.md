# GBIF Ebbe Nielsen Challenge Entry Form Draft

## Submission Name / Title

EcoGenesis Evidence Atlas: GBIF Evidence Passports for Safe Biodiversity Decisions

## Team Members and Affiliations

TODO: Add final submitter name, team members, affiliations, country and contact email.

## Abstract and Rationale

EcoGenesis Evidence Atlas is a minimal GBIF-first tool that turns a taxon, region and decision purpose into a reproducible Evidence Passport. It uses GBIF-mediated occurrence data, preserves `taxonKey`, `datasetKey`, license and source metadata, checks quality and sampling limits, and produces a decision memo, evidence map, claim guardrails, citation guidance, publisher feedback and a downloadable review pack.

The problem it addresses is practical and common. GBIF makes biodiversity evidence discoverable, but downstream users still need help deciding what the data can safely support. A map of occurrence records does not explain whether the data are fit for conservation triage, invasive watch, sampling-gap planning or dataset quality review. Empty cells are often misread as species absence. Dataset attribution can be lost after filtering. Citation requirements are often handled after analysis rather than during analysis. Data publishers and GBIF node managers also need clearer feedback about the record-level issues that block reuse.

EcoGenesis Evidence Atlas changes this workflow from "where are the records?" to "what can this evidence safely support, what should be cited, and what should be fixed next?" The tool deliberately avoids pretending that GBIF occurrence data prove absence, true distribution or population trend without additional methods. It labels empty cells as no-evidence survey targets, blocks unsupported claims, and gives the user a purpose-aware readiness score with plain-language caveats.

The current prototype has two modes. `Presentation` is a compact contest view for judges, showing the problem, live GBIF status, current verdict, map, supported claims, blocked claims and Evidence Pack download. `Work with GBIF` is the working mode: users search GBIF taxa, select a concrete `taxonKey`, choose a region preset or bounding box, select a purpose and generate a live Evidence Passport. Live GBIF is the default path. If GBIF is unavailable, the application returns a transparent empty no-evidence fallback and does not reuse fixture records in the user workflow.

The exported Evidence Pack includes `decision_memo.md`, `passport.html`, `records.geojson`, `quality_metrics.csv`, `gap_priorities.csv`, `dataset_contributions.csv`, `citations.md`, `publisher_issue_templates.md`, `submission_readiness.md`, `validation_summary.md`, `evidence_graph.json`, `evidence_pack.json` and `evidence_pack.zip`. The same workflow is available through the web UI, API and command-line runner, making it repeatable for judges and useful for future GBIF-based analyses.

For GBIF, the value is not another generic biodiversity dashboard. It is a responsible-use layer that strengthens citation compliance, improves interpretation of GBIF-mediated data, turns quality issues into publisher-facing feedback, and gives researchers, policy users and data managers a reusable open workflow for evidence readiness.

## Operating Instructions

### Docker

```bash
docker compose up --build
```

Open:

- Frontend: http://localhost:13100
- Backend health: http://localhost:18100/health
- Backend API docs: http://localhost:18100/docs

### Local Development

```bash
cd backend
.venv/bin/python -m pytest tests
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 18100
```

In a second terminal:

```bash
cd frontend
npm install
npm test -- --run
npm run dev -- --host 127.0.0.1 --port 13100
```

### CLI Evidence Passport

```bash
backend/.venv/bin/python backend/scripts/evidence_passport_cli.py \
  --taxon "Aedes albopictus" \
  --taxon-key 1651430 \
  --region-name "Spain live GBIF bbox" \
  --bbox=-10,35,4.5,44.5 \
  --purpose invasive_watch \
  --source-mode online_with_empty_fallback \
  --output-dir reports/cli-aedes-spain
```

### Demo Case Suite

```bash
backend/.venv/bin/python backend/scripts/generate_demo_report.py
```

This writes three live review cases to `reports/demo-cases/`: invasive watch, sampling gaps and dataset quality review.

## Video URL

TODO: Upload `submission-assets/video/ecogenesis-evidence-atlas-demo.mp4` to a public no-cost video location and paste the link here.

Local video file: `submission-assets/video/ecogenesis-evidence-atlas-demo.mp4`

## Source and Submission Documentation Links

- Repository: https://github.com/oddworld666/EcoGenesis_Evidence_Atlas
- Submission documentation: `docs/submission.md`
- Methodology: `docs/methodology.md`
- Testing: `docs/testing.md`
- GBIF citation notes: `docs/gbif-data-use-and-citation.md`
- Demo scenarios: `docs/demo-scenarios.md`
- Evidence schema: `schemas/evidence_passport.schema.json`
- Demo reports: `reports/demo-cases/`

## Notes for Final Form

- Confirm the repository is public before submitting.
- Confirm the video URL is public, playable without login and includes captions or transcript.
- Confirm the team/member details are final.
- Confirm the license files remain visible: `LICENSE`, `DATA_LICENSES.md`, `CITATION.cff`.
