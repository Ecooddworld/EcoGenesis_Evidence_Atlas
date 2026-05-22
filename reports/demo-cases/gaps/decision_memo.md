# Decision Memo

Verdict: **Usable for the selected decision with documented caveats**

## 1. Question

Can GBIF-mediated occurrence evidence for Quercus robur in Western Europe live bbox support the purpose 'Sampling gap analysis'?

## 2. Evidence Basis

300 retained occurrence-style records, citation/provenance component 100.0/100, using live GBIF API records and bbox [-10.0, 42.0, 12.0, 56.0].

## 3. Fitness For Purpose

The purpose-aware readiness score is 82.56/100. High readiness: evidence is strong for the selected purpose, with remaining caveats documented.

## 4. Safe Claims

- GBIF-mediated records matching the selected taxon and region are present in the evidence pack.
- Dataset provenance is preserved through datasetKey-level contribution summaries.

## 5. Blocked Claims

- Absence cannot be inferred from empty or low-evidence grid cells.
- Observed GBIF distribution must not be treated as the true species distribution.
- Population trend cannot be inferred without temporal sampling-bias correction.

## Main Limitations

- 3 occupied grid cells are under-sampled by the coverage proxy.
- 4 grid cells have no retained records; they are no-evidence cells, not absences.
- No GBIF download DOI is attached to this evidence pack yet.

## Recommended Next Action

Create a DOI-backed GBIF occurrence download or derived dataset before publication.

## Plain-Language Summary

The passport is a decision memo, not a species distribution model: it shows what the selected GBIF records can responsibly support, what they cannot support, which data issues matter, and what to cite or fix next.

## Who Benefits

- A non-expert can see the safe conclusion without reading raw GBIF tables.
- A reviewer can audit datasetKey provenance, claims and methods from exported files.
- A publisher can receive a prioritized issue list instead of vague data-quality feedback.

## Citation Gate

- Status: online_api_without_download_doi
- Publication ready: False
- Message: This evidence pack does not include a GBIF download DOI. For publication, create and cite a DOI-backed GBIF occurrence download or derived dataset. Fixture or fallback packs are demo artifacts, not publication evidence.
