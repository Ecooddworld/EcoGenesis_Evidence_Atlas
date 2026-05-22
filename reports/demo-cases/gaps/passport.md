# GBIF Evidence Passport: Quercus robur

- Region: Western Europe live bbox
- Purpose: Sampling gap analysis
- Source used: online
- Records used: 300
- Datasets used: 7
- Evidence readiness: 82.56/100
- Citation status: online_api_without_download_doi

## Decision Memo

**Verdict:** Usable for the selected decision with documented caveats

**Question:** Can GBIF-mediated occurrence evidence for Quercus robur in Western Europe live bbox support the purpose 'Sampling gap analysis'?

**Evidence basis:** 300 retained occurrence-style records, citation/provenance component 100.0/100, using live GBIF API records and bbox [-10.0, 42.0, 12.0, 56.0].

**Fitness for purpose:** The purpose-aware readiness score is 82.56/100. High readiness: evidence is strong for the selected purpose, with remaining caveats documented.

**Recommended next action:** Create a DOI-backed GBIF occurrence download or derived dataset before publication.

## Source Summary

- Requested source mode: online_with_empty_fallback
- GBIF API status: ok
- Fixture fallback used: False

## Grid Summary

- Total cells: 16
- Occupied cells: 12
- Empty/no-evidence cells: 4
- Under-sampled occupied cells: 3
- Survey priority cells: 7

## Readiness Components

| Component | Score | Weight |
| --- | ---: | ---: |
| Spatial Accuracy | 100.0 | 0.2 |
| Temporal Recency | 100.0 | 0.1 |
| Taxonomic Confidence | 100.0 | 0.15 |
| Sampling Coverage | 61.25 | 0.45 |
| Citation Provenance | 100.0 | 0.1 |
| Issue Explainability | 100.0 | 0.0 |

## Purpose Comparison

| Purpose | Score |
| --- | ---: |
| Conservation brief | 92.25 |
| Invasive watch | 94.19 |
| Sampling gap analysis | 82.56 |
| Dataset quality review | 96.12 |

## Top Sampling Priorities

| Cell | Score | Label | Reasons |
| --- | ---: | --- | --- |
| grid:4:0:2 | 81.0 | High priority for survey | No GBIF-mediated records returned after filters; Neighboring cells contain occurrence evidence; Recent temporal evidence is weak or missing; Dataset/source diversity is low |
| grid:4:2:0 | 81.0 | High priority for survey | No GBIF-mediated records returned after filters; Neighboring cells contain occurrence evidence; Recent temporal evidence is weak or missing; Dataset/source diversity is low |
| grid:4:0:1 | 77.0 | High priority for survey | No GBIF-mediated records returned after filters; Neighboring cells contain occurrence evidence; Recent temporal evidence is weak or missing; Dataset/source diversity is low |

## Main Risks

- 3 occupied grid cells are under-sampled by the coverage proxy.
- 4 grid cells have no retained records; they are no-evidence cells, not absences.
- No GBIF download DOI is attached to this evidence pack yet.

## Allowed Claims

- GBIF-mediated records matching the selected taxon and region are present in the evidence pack.
- Dataset provenance is preserved through datasetKey-level contribution summaries.

## Weak Claims

- Record clusters can indicate areas of observation activity, but they may also reflect observer effort.
- The selected-purpose readiness score is 82.56/100 and should be interpreted with the component scores.

## Unsupported Claims

- Absence cannot be inferred from empty or low-evidence grid cells.
- Observed GBIF distribution must not be treated as the true species distribution.
- Population trend cannot be inferred without temporal sampling-bias correction.

## Required Verification

- Create a DOI-backed GBIF occurrence download or derived dataset before formal publication.
- Inspect high coordinate-uncertainty records before using them in fine-scale decisions.
- Treat undersampled occupied cells as survey priorities, not confirmed absences.
- Treat empty grid cells as no-evidence cells, not absence evidence.

## Citation Guidance

This evidence pack does not include a GBIF download DOI. For publication, create and cite a DOI-backed GBIF occurrence download or derived dataset. Fixture or fallback packs are demo artifacts, not publication evidence.

Occurrence evidence for Quercus robur in Western Europe live bbox was assembled from GBIF-mediated occurrence-style records using bbox [-10.0, 42.0, 12.0, 56.0]. The workflow retained datasetKey provenance, record counts per contributing dataset, coordinate uncertainty, event dates, licenses and GBIF issue flags. The evidence readiness score was computed for purpose 'sampling_gaps' from spatial, temporal, taxonomic, sampling and provenance components. Empty grid cells were treated as no-evidence cells rather than absences.

## Graph Memory

- Evidence graph: evidence_graph.json
- Human-readable summary: graph_memory.md
- Offline vault: evidence_vault.zip

## Submission Readiness

- Stage: Demo-ready MVP; publication-grade DOI case still pending
- Ready checks: 7/9
- Detailed checklist: submission_readiness.md
- Validation summary: validation_summary.md
- Demo script: video_script.md

## Next Actions

- Create a DOI-backed GBIF occurrence download or derived dataset before publication.
- Preserve datasetKey and run.json with any downstream analysis.
- Avoid absence claims for empty or low-effort grid cells.
- Prioritize survey design around no-evidence and under-sampled grid cells.
