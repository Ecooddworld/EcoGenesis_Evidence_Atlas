# GBIF Evidence Passport: Aedes albopictus

- Region: Spain live GBIF bbox
- Purpose: Invasive watch
- Source used: online
- Records used: 300
- Datasets used: 8
- Evidence readiness: 97.73/100
- Citation status: online_api_without_download_doi

## Source Summary

- Requested source mode: online_with_fixture_fallback
- GBIF API status: ok
- Fixture fallback used: False

## Grid Summary

- Total cells: 16
- Occupied cells: 16
- Empty/no-evidence cells: 0
- Under-sampled occupied cells: 1
- Survey priority cells: 1

## Readiness Components

| Component | Score | Weight |
| --- | ---: | ---: |
| Spatial Accuracy | 97.67 | 0.25 |
| Temporal Recency | 100.0 | 0.35 |
| Taxonomic Confidence | 100.0 | 0.15 |
| Sampling Coverage | 88.75 | 0.15 |
| Citation Provenance | 100.0 | 0.1 |
| Issue Explainability | 100.0 | 0.0 |

## Purpose Comparison

| Purpose | Score |
| --- | ---: |
| Conservation brief | 97.05 |
| Invasive watch | 97.73 |
| Sampling gap analysis | 94.47 |
| Dataset quality review | 98.29 |

## Top Sampling Priorities

| Cell | Score | Label | Reasons |
| --- | ---: | --- | --- |
| grid:4:2:0 | 51.25 | Medium priority for survey | Occupied cell remains below sampling coverage threshold; Neighboring cells contain occurrence evidence; Coordinate uncertainty burdens cell interpretation; Dataset/source diversity is low |

## Main Risks

- 20 records have coordinate uncertainty above 10 km.
- 1 occupied grid cells are under-sampled by the coverage proxy.
- No GBIF download DOI is attached to this evidence pack yet.

## Allowed Claims

- GBIF-mediated records matching the selected taxon and region are present in the evidence pack.
- Dataset provenance is preserved through datasetKey-level contribution summaries.

## Weak Claims

- Record clusters can indicate areas of observation activity, but they may also reflect observer effort.
- The selected-purpose readiness score is 97.73/100 and should be interpreted with the component scores.

## Unsupported Claims

- Absence cannot be inferred from empty or low-evidence grid cells.
- Observed GBIF distribution must not be treated as the true species distribution.
- Population trend cannot be inferred without temporal sampling-bias correction.

## Required Verification

- Create a DOI-backed GBIF occurrence download or derived dataset before formal publication.
- Inspect high coordinate-uncertainty records before using them in fine-scale decisions.
- Treat undersampled occupied cells as survey priorities, not confirmed absences.

## Citation Guidance

This evidence pack does not include a GBIF download DOI. For publication, create and cite a DOI-backed GBIF occurrence download or derived dataset. Fixture or fallback packs are demo artifacts, not publication evidence.

Occurrence evidence for Aedes albopictus in Spain live GBIF bbox was assembled from GBIF-mediated occurrence-style records using bbox [-10.0, 35.0, 4.5, 44.5]. The workflow retained datasetKey provenance, record counts per contributing dataset, coordinate uncertainty, event dates, licenses and GBIF issue flags. The evidence readiness score was computed for purpose 'invasive_watch' from spatial, temporal, taxonomic, sampling and provenance components. Empty grid cells were treated as no-evidence cells rather than absences.

## Next Actions

- Create a DOI-backed GBIF occurrence download or derived dataset before publication.
- Preserve datasetKey and run.json with any downstream analysis.
- Avoid absence claims for empty or low-effort grid cells.
- Review records with coordinate uncertainty above 10 km.
- Prioritize survey design around no-evidence and under-sampled grid cells.
- Share the Publisher Feedback Pack with dataset managers for prioritized fixes.
