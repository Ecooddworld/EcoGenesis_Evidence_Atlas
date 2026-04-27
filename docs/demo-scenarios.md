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
2. Wait for the default live GBIF passport to appear automatically. If GBIF is unavailable, the app falls back to the offline fixture and labels that clearly.
3. Review the score band, KPI strip, OpenStreetMap/Leaflet evidence map, no-evidence cells, issue points, purpose comparison, scientific interpretation and source/provenance panel.
4. Open the Evidence Map, Data Quality, Sampling Gaps, Claim Guardrails, Citation & Provenance, Publisher Feedback and Export Pack tabs.
5. Download `evidence_pack.zip` or inspect individual artifacts.

## Source Modes

- `Reproducible offline demo`: deterministic and safe for judging without network access.
- `Online GBIF with fallback`: attempts GBIF API and falls back to the fixture if online access fails.
- `Online GBIF only`: fails with a structured API error if GBIF is unavailable.
