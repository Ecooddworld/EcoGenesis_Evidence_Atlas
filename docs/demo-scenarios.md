# Demo Scenarios

## Scenario 1: Invasive Watch

- Taxon: `Aedes albopictus`
- Region: Spain live GBIF bbox
- Purpose: `Invasive watch`

Attempts live GBIF occurrence records, maps them on OpenStreetMap tiles and still warns against absence claims in undersampled cells.

## Scenario 2: Live Oak Sampling Gaps

- Taxon: `Quercus robur`
- Region: Western Europe live bbox
- Purpose: `Sampling gaps`

Highlights cells with low Good coverage from real GBIF results and turns the result into next sampling actions.

## Scenario 3: Live Dataset Quality Review

- Taxon: `Lynx pardinus`
- Region: Iberian Peninsula live bbox
- Purpose: `Dataset quality review`

Groups coordinate uncertainty, missing dates and GBIF issue flags by `datasetKey`, producing a Publisher Feedback Pack from live GBIF records when available.

## Scenario 4: Offline Fixture

- Taxon: `Aedes albopictus`
- Region: Spain offline fixture bbox
- Purpose: `Invasive watch`

Uses the deterministic fixture for no-network testing and reproducible regression checks.

## UI Review Path

1. Open http://localhost:13100.
2. Start in **Presentation**. Confirm the screen shows the problem statement, current verdict, live GBIF/API status, map, safe claims, blocked claims, **Open Workbench** and **Download Evidence Pack**.
3. Switch to **Work with GBIF**. Confirm there is no public source-mode selector and the status card says live GBIF is the active source.
4. Type a species or genus in **Taxon**, use **Find taxon in GBIF**, and choose a suggestion to lock the run to a concrete GBIF `taxonKey`; the app automatically generates a fresh passport.
5. Pick a region preset to automatically generate a fresh passport, or edit the four bbox fields (`west`, `south`, `east`, `north`) and then generate manually.
6. Review the Decision Memo, OpenStreetMap/Leaflet evidence map, key quality risks, safe claims, blocked claims and source/provenance panel.
7. Open **Advanced evidence files** only when needed. Confirm Graph Memory, Submission Readiness, Publisher Feedback, raw tables and machine-readable exports are downloadable from the evidence pack without cluttering the main screen.
8. Download `evidence_pack.zip`, then inspect `decision_memo.md`, `submission_readiness.md`, `validation_summary.md`, `publisher_issue_templates.md`, `impact_brief.md` and `video_script.md`.

## Generated Demo Case Suite

Run:

```bash
backend/.venv/bin/python backend/scripts/generate_demo_report.py
```

The script writes three contest-review folders to `reports/demo-cases/`: `invasive/`, `gaps/` and `quality/`. Each folder contains the same files a judge would download from the app, including the full ZIP, Decision Memo, source summary, claim guardrails, publisher issue templates, submission readiness and video script. `reports/demo/` mirrors the invasive-watch case for older links.

## Source Modes

- Public workbench: always sends `source_mode: "online_with_empty_fallback"` and `use_fixture: false`.
- GBIF unavailable: shows an empty no-evidence fallback and the message `GBIF unavailable: no fixture records reused`.
- Offline sample: deterministic fixture kept for API compatibility, demo generation and regression checks; it is hidden from the main user flow.
