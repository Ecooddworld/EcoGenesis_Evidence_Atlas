# Bottlenecks And Errors

## Suite Totals

- Successful online scenarios: 10
- Deduplicated records written: 1000
- Duplicate records skipped: 149
- Hypothesis claims: 100
- Blocked claims: 20
- Requires-verification claims: 20
- High coordinate uncertainty records across scenarios: 130
- Missing eventDate/year records across scenarios: 0
- Records still missing publisher after dataset enrichment: 0
- Records still missing datasetTitle after dataset enrichment: 0
- Records missing coordinateUncertaintyInMeters: 154

## Fixed Methodological Bottlenecks

- GBIF API can be unavailable or degraded; empty fallback runs are not counted as valid live evidence.
- The current GBIF API path reads search results, not a DOI-backed GBIF download; formal publication still needs a DOI or derived dataset citation.
- The current client uses the first occurrence-search page for each scenario; large research studies need GBIF download API or pagination.
- A bbox is not the same as an administrative country boundary.
- GBIF occurrence records do not prove species absence.
- Occurrence clusters can reflect observer effort rather than true abundance or distribution.
- Population trend claims are blocked without temporal sampling-bias correction.
- High coordinate uncertainty weakens fine-scale claims.
- Missing eventDate/year weakens temporal claims.
- Single-dataset dominance can bias apparent evidence patterns.
- TaxonKey improves reproducibility, but synonyms and taxonomic changes still need review.
- Barcode/protein layers are outside this live occurrence test because the GBIF occurrence API is not Sequence ID.

## Scenario Failures Or Empty Fallbacks

- None detected.

## Low Record / High Duplicate Scenarios

- aedes-france: 77 deduped records added from 120 downloaded records.
- quercus-germany: 75 deduped records added from 120 downloaded records.
- apis-france: 59 deduped records added from 120 downloaded records.

## Single Dataset Bias

- passer-united-states: only 1 dataset(s) represented.
