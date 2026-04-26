# GBIF Data Use and Citation

EcoGenesis Evidence Atlas helps users preserve the information needed for responsible GBIF data use.

## What the Tool Preserves

- `datasetKey`
- record counts per dataset
- license values when present
- publisher and dataset title when present
- request parameters and run timestamp
- source mode, GBIF API status and fallback warnings
- quality filters and derived metrics

## Citation Guidance

For publication, policy reports or formal reuse, do not cite a screenshot or a copied API response alone. Create a DOI-backed GBIF occurrence download or derived dataset record where appropriate, and cite GBIF-mediated data according to GBIF guidance:

- https://www.gbif.org/citation-guidelines
- https://www.gbif.org/derived-dataset/about

## Evidence Passport Warning

If a passport was generated from fixture, fallback or API mode without a GBIF download DOI, the Citation Autopilot marks citation status as incomplete and provides next actions.

Fixture and fallback packs are reproducible demo artifacts. They are useful for judging, testing and methods review, but they should not be treated as publication-ready GBIF evidence. Online/API packs still require a DOI-backed GBIF occurrence download or derived dataset before formal publication.

## Generated Citation Files

Each run includes:

- `citations.md`: citation status, GBIF DOI warning, suggested methods text and dataset contribution table
- `claim_guardrails.md`: supported, weak, unsupported and verification-required claims
- `dataset_contributions.csv`: `datasetKey`, title, publisher, license, record count and detected issues
- `readiness_scorecard.csv`: purpose-aware readiness scores for all supported purposes
- `source_summary.json`: requested/used source mode, GBIF API status, fallback flag and warnings
- `demo_scenario.json`: compact scenario metadata and request payload
- `run.json`: request, timestamp, source mode and GBIF species match metadata
- `evidence_pack.zip`: the complete export bundle for review and sharing
