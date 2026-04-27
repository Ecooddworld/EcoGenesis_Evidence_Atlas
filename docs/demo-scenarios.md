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
2. Wait for the default live GBIF passport to appear automatically. If GBIF is unavailable, the app shows an empty live fallback with 16 no-evidence cells and explicitly states that old fixture records were not reused.
3. Type a species or genus in **Taxon**, use **Search GBIF taxon**, and choose a suggestion to lock the run to a concrete GBIF `taxonKey`; the app automatically generates a fresh passport.
4. Pick a region preset to automatically generate a fresh passport, or edit the four bbox fields (`west`, `south`, `east`, `north`) and then generate manually.
5. Review the score band, KPI strip, OpenStreetMap/Leaflet evidence map, no-evidence cells, issue points, purpose comparison, scientific interpretation and source/provenance panel.
6. Open the Evidence Map, Data Quality, Sampling Gaps, Claim Guardrails, Citation & Provenance, Publisher Feedback and Export Pack tabs.
7. Download `evidence_pack.zip` or inspect individual artifacts.

## Source Modes

- `Live GBIF`: attempts GBIF API and uses an empty no-evidence fallback if online access fails.
- `Offline sample`: deterministic fixture, safe for judging without network access and regression checks.
