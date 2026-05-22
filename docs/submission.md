# EcoGenesis Evidence Atlas Submission Kit

## Contest Link

2026 Ebbe Nielsen Challenge: https://www.gbif.org/news/3DyM3tK5wgYipqyaHwG2c2/2026-ebbe-nielsen-challenge-open-for-submissions

## Proposed Title

EcoGenesis Evidence Atlas: GBIF Evidence Passports for Safe Biodiversity Decisions

## 40-Second Abstract

EcoGenesis Evidence Atlas is a minimal GBIF-first tool that turns a taxon, region and decision purpose into a reproducible Evidence Passport. It fetches GBIF-mediated occurrence data, preserves `taxonKey`, `datasetKey`, licenses and source metadata, scores data readiness for the selected purpose, maps evidence and no-evidence cells, warns against unsupported absence or trend claims, and exports a complete evidence pack for review, citation and publisher feedback.

The goal is simple: help users decide what GBIF data can responsibly support now, what it cannot support yet, and what should be sampled, cited or fixed next.

## Problem

GBIF already makes biodiversity evidence discoverable, but many downstream users still struggle with the final decision step:

- a map point is easy to see, but data fitness for a specific purpose is harder to judge;
- empty areas are often misread as absence instead of no evidence;
- dataset attribution can be lost after filtering or export;
- citation requirements are often handled after analysis instead of during analysis;
- data publishers receive limited actionable feedback about the records that blocked reuse.

This creates a gap between data access and responsible use.

## Solution

The Evidence Passport is a reproducible decision packet generated from a single query:

```text
taxon + selected GBIF taxonKey + region/bbox + purpose
```

It returns:

- Decision Memo: what can be decided, what is weak, what is blocked and what to do next;
- Evidence Map: occurrence points, issue markers, grid cells and sampling-priority cells;
- Evidence Readiness Score: a purpose-aware score, not a universal truth score;
- Claim Guardrails: safe, weak, blocked and verification-required claims;
- Citation Autopilot: dataset contributions, DOI warning, methods text and derived-dataset recipe;
- Publisher Feedback Pack: ranked issues and copy-ready issue templates for data managers;
- Evidence Pack ZIP: machine-readable JSON, CSV, GeoJSON, Markdown, HTML and graph/vault exports.

## Why This Matters for GBIF

The tool does not compete with GBIF. It adds a responsible-use layer on top of GBIF-mediated data:

- improves citation compliance by preserving `datasetKey`, licenses and DOI-completion steps;
- turns GBIF issue flags and uncertainty into practical user warnings;
- helps users avoid overclaiming absence, trends or range limits from opportunistic occurrence data;
- creates a feedback path from reuse back to publishers and GBIF nodes;
- makes demo, review and regression runs reproducible through JSON, CSV, GeoJSON and Markdown artifacts.

In practice, it changes the question from "where are the records?" to "what decisions can these records safely support?"

## What Judges Should Try First

1. Open the frontend.
2. Stay in `Presentation` mode and review the current verdict, GBIF status, map, safe claims and blocked claims.
3. Click `Open Workbench`.
4. Search for a taxon in GBIF, select a suggestion to lock the `taxonKey`, choose a region preset or bbox and click `Generate Evidence Passport`.
5. Review the Decision Memo, map, risks, safe claims and blocked claims.
6. Download `Evidence Pack` and inspect `decision_memo.md`, `source_summary.json`, `citations.md`, `publisher_issue_templates.md`, `submission_readiness.md` and `evidence_pack.json`.

## Operating Instructions

```bash
docker compose up --build
```

Open:

- frontend: http://localhost:13100
- backend docs: http://localhost:18100/docs
- health: http://localhost:18100/health

Run tests:

```bash
backend/.venv/bin/python -m pytest backend/tests
cd frontend && npm test -- --run && npm run build
```

Run a CLI passport:

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

## Default Source Behavior

The public workbench defaults to live GBIF:

- `source_mode: "online_with_empty_fallback"`
- `use_fixture: false`

If GBIF is unreachable, the tool returns an empty no-evidence fallback and clearly says that fixture records were not reused. Fixture mode remains available only for tests, regression and offline development.

## Demo Suite

Generate three review cases:

```bash
backend/.venv/bin/python backend/scripts/generate_demo_report.py
```

Outputs:

- `reports/demo-cases/invasive/`: Aedes albopictus in Spain for invasive watch;
- `reports/demo-cases/gaps/`: Quercus robur in Western Europe for sampling gaps;
- `reports/demo-cases/quality/`: Lynx pardinus in Iberia for dataset quality review.

`reports/demo/` mirrors the invasive-watch case for backward compatibility.

## Video Structure

1. Problem: maps alone do not tell users what they can safely decide.
2. Presentation mode: show live GBIF status, verdict, score, map, safe claims and blocked claims.
3. Workbench: search GBIF taxon, select `taxonKey`, choose region, generate passport.
4. Evidence map: show records, issue markers and no-evidence cells as survey targets.
5. Claims and citation: show absence/trend overclaim warnings and dataset attribution.
6. Evidence Pack: download ZIP and open `decision_memo.md`, `citations.md`, `publisher_issue_templates.md` and `evidence_pack.json`.
7. Close: GBIF data becomes not just discoverable, but decision-ready and feedback-ready.

Prepared local assets:

- `submission-assets/video/ecogenesis-evidence-atlas-demo.mp4`
- `submission-assets/video/ecogenesis-evidence-atlas-demo.srt`
- `submission-assets/screenshots/`
- `submission-assets/gbif-entry-form-draft.md`
- `submission-assets/final-submission-checklist.md`

Before submitting, upload the MP4 to a public no-cost location and paste the public video URL into the official entry form.

## Remaining Publication Caveat

The app preserves the citation path, but formal scientific or policy publication should still use a DOI-backed GBIF occurrence download or derived dataset where applicable. The Evidence Passport makes that requirement visible before users publish, rather than hiding it in a late-stage methods cleanup.
