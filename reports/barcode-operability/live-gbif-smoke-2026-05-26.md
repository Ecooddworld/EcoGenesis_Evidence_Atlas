# Live GBIF Smoke Test - 2026-05-26

## Target

- Taxon: `Aedes albopictus`
- Selected `taxonKey`: `1651430`
- Region: Spain live GBIF bbox
- BBox: `[-10, 35, 4.5, 44.5]`
- Purpose: `invasive_watch`
- Source mode: `online_with_empty_fallback`
- Fixture reuse: `false`
- Max records requested: `50`

## Result

- GBIF API status endpoint: `ok`
- GBIF base URL: `https://api.gbif.org/v1`
- Taxon suggestion source: `gbif_api`
- Accepted suggestion: `Aedes albopictus (Skuse, 1894)`
- Run ID: `1a1fa467affb489cb53c9abcc2d0a973`
- Used source mode: `online`
- Fallback used: `false`
- GBIF result count: `19713`
- GBIF returned records: `50`
- Datasets used: `4`
- Evidence readiness score: `91.05`
- Interpretation: High readiness for the selected invasive-watch purpose, with caveats documented.

## Main Risks Returned By The Tool

- `4` records have coordinate uncertainty above 10 km.
- `7` occupied grid cells are under-sampled by the coverage proxy.
- `3` grid cells have no retained records; these are no-evidence cells, not absences.
- No GBIF download DOI is attached to this evidence pack yet.

## Conclusion

The live path worked against GBIF API data without reusing fixture occurrence records. The occurrence-passport layer reached a concrete, auditable result: GBIF was reachable, the selected `taxonKey` was preserved, records were returned, provenance exports were generated, and the tool correctly reported caveats rather than turning empty or sparse cells into absence claims.

The Barcode-to-GBIF Evidence Compiler remains the molecular decision layer for supplied Sequence ID / BLAST-style outputs. The live GBIF smoke confirms the surrounding GBIF API and evidence-pack infrastructure are operational on real GBIF-mediated occurrence data.
