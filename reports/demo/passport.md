# GBIF Evidence Passport: Aedes albopictus

- Region: Spain demo bbox
- Purpose: Invasive watch
- Source used: fixture
- Records used: 12
- Datasets used: 4
- Evidence readiness: 74.03/100
- Citation status: fixture_demo_not_for_publication

## Source Summary

- Requested source mode: fixture
- GBIF API status: not_called
- Fixture fallback used: False

## Grid Summary

- Total cells: 16
- Occupied cells: 9
- Empty/no-evidence cells: 7
- Under-sampled occupied cells: 9
- Survey priority cells: 16

## Readiness Components

| Component | Score | Weight |
| --- | ---: | ---: |
| Spatial Accuracy | 88.33 | 0.25 |
| Temporal Recency | 75.83 | 0.35 |
| Taxonomic Confidence | 93.27 | 0.15 |
| Sampling Coverage | 15.0 | 0.15 |
| Citation Provenance | 91.67 | 0.1 |
| Issue Explainability | 100.0 | 0.0 |

## Purpose Comparison

| Purpose | Score |
| --- | ---: |
| Conservation brief | 72.49 |
| Invasive watch | 74.03 |
| Sampling gap analysis | 55.16 |
| Dataset quality review | 83.15 |

## Top Sampling Priorities

| Cell | Score | Label | Reasons |
| --- | ---: | --- | --- |
| grid:4:0:2 | 81.0 | High priority for survey | No GBIF-mediated records returned after filters; Neighboring cells contain occurrence evidence; Recent temporal evidence is weak or missing; Dataset/source diversity is low |
| grid:4:2:0 | 81.0 | High priority for survey | No GBIF-mediated records returned after filters; Neighboring cells contain occurrence evidence; Recent temporal evidence is weak or missing; Dataset/source diversity is low |
| grid:4:2:3 | 81.0 | High priority for survey | No GBIF-mediated records returned after filters; Neighboring cells contain occurrence evidence; Recent temporal evidence is weak or missing; Dataset/source diversity is low |

## Main Risks

- 4 records have coordinate uncertainty above 10 km.
- 2 records are missing eventDate/year.
- 9 occupied grid cells are under-sampled by the coverage proxy.
- 7 grid cells have no retained records; they are no-evidence cells, not absences.
- No GBIF download DOI is attached to this evidence pack yet.

## Allowed Claims

- GBIF-mediated records matching the selected taxon and region are present in the evidence pack.
- Dataset provenance is preserved through datasetKey-level contribution summaries.

## Weak Claims

- Record clusters can indicate areas of observation activity, but they may also reflect observer effort.
- The selected-purpose readiness score is 74.03/100 and should be interpreted with the component scores.

## Unsupported Claims

- Absence cannot be inferred from empty or low-evidence grid cells.
- Observed GBIF distribution must not be treated as the true species distribution.
- Population trend cannot be inferred without temporal sampling-bias correction.

## Required Verification

- Create a DOI-backed GBIF occurrence download or derived dataset before formal publication.
- Inspect high coordinate-uncertainty records before using them in fine-scale decisions.
- Review records missing eventDate/year before temporal claims.
- Treat undersampled occupied cells as survey priorities, not confirmed absences.
- Treat empty grid cells as no-evidence cells, not absence evidence.

## Citation Guidance

This evidence pack does not include a GBIF download DOI. For publication, create and cite a DOI-backed GBIF occurrence download or derived dataset. Fixture or fallback packs are demo artifacts, not publication evidence.

Occurrence evidence for Aedes albopictus in Spain demo bbox was assembled from GBIF-mediated occurrence-style records using bbox [-10.0, 35.0, 4.5, 44.5]. The workflow retained datasetKey provenance, record counts per contributing dataset, coordinate uncertainty, event dates, licenses and GBIF issue flags. The evidence readiness score was computed for purpose 'invasive_watch' from spatial, temporal, taxonomic, sampling and provenance components. Empty grid cells were treated as no-evidence cells rather than absences.

## Next Actions

- Create a DOI-backed GBIF occurrence download or derived dataset before publication.
- Preserve datasetKey and run.json with any downstream analysis.
- Avoid absence claims for empty or low-effort grid cells.
- Review records with coordinate uncertainty above 10 km.
- Review records missing eventDate/year before temporal interpretation.
- Prioritize survey design around no-evidence and under-sampled grid cells.
- Share the Publisher Feedback Pack with dataset managers for prioritized fixes.
