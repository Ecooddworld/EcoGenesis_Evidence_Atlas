# Methodology

EcoGenesis Evidence Atlas is a data-readiness workflow, not a species distribution model and not an absence detector.

## Inputs

The core request is:

```text
taxon + region + purpose + source mode
```

The MVP uses GBIF species matching and GBIF occurrence-style records. Fixture mode uses a small deterministic dataset for repeatable tests and demos. Online GBIF with fallback attempts the GBIF API and falls back to the fixture if network/API access fails.

## Quality Metrics

The pipeline checks:

- coordinate validity
- coordinate uncertainty
- temporal completeness
- taxonomic match availability
- dataset provenance availability
- GBIF issue flags when present

## Diversity and Sampling

Grid cells use occurrence counts and accepted taxon identifiers to compute:

- Hill q=0: observed richness
- Hill q=1: exp(Shannon entropy)
- Hill q=2: inverse Simpson diversity
- Good coverage: `1 - singletons / N`
- Chao1 richness when coverage is low

The 4x4 grid always returns all 16 cells. Empty cells are marked as no-evidence cells, not absences. Under-sampled occupied cells and empty cells are counted separately so downstream users can distinguish data gaps from observed occurrence evidence.

## Purpose-Aware Readiness

Evidence Readiness is a weighted score. The same data can be suitable for one purpose and weak for another. For example, invasive watch gives more weight to recency, while dataset review gives more weight to provenance and issue explainability.

Each run also includes a purpose score matrix for all supported purposes, computed from the same normalized record set.

## Claim Guardrails

The Claim Guardrails module states what the data supports, weakly suggests, does not support, and what must be verified before research or policy use.

## Scientific Map

The application renders a geographic evidence map for the query bounding box. It combines a local SVG basemap, the 4x4 sampling grid, occurrence points, high-uncertainty/issue markers and a short evidence thesis. No-evidence cells are visualized as survey targets, not as absence observations.

## Export Bundle

Every completed run writes a reproducible evidence pack:

- `evidence_pack.json` for machine reuse
- `run.json` for request parameters, timestamp and GBIF match metadata
- `source_summary.json` and `demo_scenario.json`
- `records.geojson` for mapped retained occurrences
- `quality_metrics.csv`, `readiness_scorecard.csv` and `dataset_contributions.csv`
- `citations.md`, `claim_guardrails.md` and `publisher_feedback.md`
- `passport.md`, `passport.html` and `evidence_pack.zip`

The ZIP file is a convenience bundle. Formal publication still requires DOI-backed GBIF download or derived-dataset citation where applicable.
