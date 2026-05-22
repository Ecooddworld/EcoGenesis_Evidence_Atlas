# GBIF Evidence Passport: Lynx pardinus

- Region: Iberian Peninsula live bbox
- Purpose: Dataset quality review
- Source used: online
- Records used: 300
- Datasets used: 5
- Evidence readiness: 86.65/100
- Citation status: online_api_without_download_doi

## Decision Memo

**Verdict:** Usable for the selected decision with documented caveats

**Question:** Can GBIF-mediated occurrence evidence for Lynx pardinus in Iberian Peninsula live bbox support the purpose 'Dataset quality review'?

**Evidence basis:** 300 retained occurrence-style records, citation/provenance component 100.0/100, using live GBIF API records and bbox [-10.0, 35.0, 4.5, 44.5].

**Fitness for purpose:** The purpose-aware readiness score is 86.65/100. High readiness: evidence is strong for the selected purpose, with remaining caveats documented.

**Recommended next action:** Create a DOI-backed GBIF occurrence download or derived dataset before publication.

## Source Summary

- Requested source mode: online_with_empty_fallback
- GBIF API status: ok
- Fixture fallback used: False

## Grid Summary

- Total cells: 16
- Occupied cells: 6
- Empty/no-evidence cells: 10
- Under-sampled occupied cells: 1
- Survey priority cells: 12

## Readiness Components

| Component | Score | Weight |
| --- | ---: | ---: |
| Spatial Accuracy | 74.1 | 0.25 |
| Temporal Recency | 100.0 | 0.1 |
| Taxonomic Confidence | 100.0 | 0.2 |
| Sampling Coverage | 31.25 | 0.1 |
| Citation Provenance | 100.0 | 0.2 |
| Issue Explainability | 100.0 | 0.15 |

## Purpose Comparison

| Purpose | Score |
| --- | ---: |
| Conservation brief | 78.48 |
| Invasive watch | 83.21 |
| Sampling gap analysis | 63.88 |
| Dataset quality review | 86.65 |

## Top Sampling Priorities

| Cell | Score | Label | Reasons |
| --- | ---: | --- | --- |
| grid:4:0:2 | 81.0 | High priority for survey | No GBIF-mediated records returned after filters; Neighboring cells contain occurrence evidence; Recent temporal evidence is weak or missing; Dataset/source diversity is low |
| grid:4:0:3 | 78.33 | High priority for survey | No GBIF-mediated records returned after filters; Neighboring cells contain occurrence evidence; Recent temporal evidence is weak or missing; Dataset/source diversity is low |
| grid:4:2:0 | 73.0 | High priority for survey | No GBIF-mediated records returned after filters; Neighboring cells contain occurrence evidence; Recent temporal evidence is weak or missing; Dataset/source diversity is low |

## Main Risks

- 222 records have coordinate uncertainty above 10 km.
- 1 occupied grid cell is under-sampled by the coverage proxy.
- 10 grid cells have no retained records; they are no-evidence cells, not absences.
- No GBIF download DOI is attached to this evidence pack yet.

## Allowed Claims

- GBIF-mediated records matching the selected taxon and region are present in the evidence pack.
- Dataset provenance is preserved through datasetKey-level contribution summaries.

## Weak Claims

- Record clusters can indicate areas of observation activity, but they may also reflect observer effort.
- The selected-purpose readiness score is 86.65/100 and should be interpreted with the component scores.

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

Occurrence evidence for Lynx pardinus in Iberian Peninsula live bbox was assembled from GBIF-mediated occurrence-style records using bbox [-10.0, 35.0, 4.5, 44.5]. The workflow retained datasetKey provenance, record counts per contributing dataset, coordinate uncertainty, event dates, licenses and GBIF issue flags. The evidence readiness score was computed for purpose 'dataset_quality_review' from spatial, temporal, taxonomic, sampling and provenance components. Empty grid cells were treated as no-evidence cells rather than absences.

## Graph Memory

- Evidence graph: evidence_graph.json
- Human-readable summary: graph_memory.md
- Offline vault: evidence_vault.zip

## Submission Readiness

- Stage: Demo-ready MVP; publication-grade DOI case still pending
- Ready checks: 8/9
- Detailed checklist: submission_readiness.md
- Validation summary: validation_summary.md
- Demo script: video_script.md

## Next Actions

- Create a DOI-backed GBIF occurrence download or derived dataset before publication.
- Preserve datasetKey and run.json with any downstream analysis.
- Avoid absence claims for empty or low-effort grid cells.
- Review records with coordinate uncertainty above 10 km.
- Prioritize survey design around no-evidence and under-sampled grid cells.
- Share the Publisher Feedback Pack with dataset managers for prioritized fixes.
