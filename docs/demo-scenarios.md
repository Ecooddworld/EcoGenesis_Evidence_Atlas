# Demo Scenarios

## Scenario 1: Invasive Watch

- Taxon: `Aedes albopictus`
- Region: Spain demo bbox
- Purpose: `Invasive watch`

Shows why recent, coordinate-aware GBIF records can support watchlist evidence, while still warning against absence claims in undersampled cells.

## Scenario 2: Sampling Gaps

- Taxon: `Aedes albopictus`
- Region: Spain demo bbox
- Purpose: `Sampling gaps`

Highlights cells with low Good coverage and turns the result into next sampling actions.

## Scenario 3: Dataset Quality Review

- Taxon: `Aedes albopictus`
- Region: Spain demo bbox
- Purpose: `Dataset quality review`

Groups coordinate uncertainty, missing dates and GBIF issue flags by `datasetKey`, producing a Publisher Feedback Pack.

## Scenario 4: Conservation Brief

- Taxon: `Aedes albopictus`
- Region: Spain demo bbox
- Purpose: `Conservation brief`

Uses a more balanced score profile to show whether the same GBIF-mediated evidence is suitable for a concise conservation evidence summary.

## UI Review Path

1. Open http://localhost:13100.
2. Wait for the default fixture passport to appear automatically.
3. Review the score band, KPI strip, scientific evidence map, no-evidence cells, issue points, purpose comparison, scientific interpretation and source/provenance panel.
4. Open the Source, Claims, Quality, Citation, Publisher and Exports tabs.
5. Download `evidence_pack.zip` or inspect individual artifacts.

## Source Modes

- `Fixture demo`: deterministic and safe for judging without network access.
- `Online GBIF with fallback`: attempts GBIF API and falls back to the fixture if online access fails.
- `Online GBIF only`: fails with a structured API error if GBIF is unavailable.
