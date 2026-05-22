# Citation Autopilot

Status: **online_api_without_download_doi**
Source used: **online**

This evidence pack does not include a GBIF download DOI. For publication, create and cite a DOI-backed GBIF occurrence download or derived dataset. Fixture or fallback packs are demo artifacts, not publication evidence.

## DOI Completion Checklist

- [x] **datasetKey provenance preserved**: Keep datasetKey in every record, aggregate and derived export.
- [x] **contribution counts generated**: Use dataset_contributions.csv to show records per contributing dataset.
- [x] **license fields retained**: Review missing or unknown licenses before formal publication.
- [ ] **GBIF download DOI or derived dataset attached**: Create a DOI-backed GBIF occurrence download or derived dataset and attach it to the report.
- [x] **methods text generated**: Review plain-English and journal-ready methods blocks before submission.

## Suggested Methods Text

Occurrence evidence for Quercus robur in Western Europe live bbox was assembled from GBIF-mediated occurrence-style records using bbox [-10.0, 42.0, 12.0, 56.0]. The workflow retained datasetKey provenance, record counts per contributing dataset, coordinate uncertainty, event dates, licenses and GBIF issue flags. The evidence readiness score was computed for purpose 'sampling_gaps' from spatial, temporal, taxonomic, sampling and provenance components. Empty grid cells were treated as no-evidence cells rather than absences.

## Journal-Ready Methods Text

GBIF-mediated occurrence-style records for Quercus robur were queried for Western Europe live bbox using bounding box [-10.0, 42.0, 12.0, 56.0]. Records were retained with datasetKey-level provenance, contribution counts, coordinate uncertainty, event dates, licenses and issue flags. The EcoGenesis Evidence Passport computed a purpose-aware readiness score for sampling_gaps; empty grid cells were interpreted as no-evidence cells and not as absences.

## Dataset Contributions

| datasetKey | Records | License |
| --- | ---: | --- |
| 8a863029-f435-446a-821e-275f4f641165 | 206 | http://creativecommons.org/licenses/by-nc/4.0/legalcode |
| 50c9509d-22c7-4a22-a47d-8c48425ef4a7 | 47 | http://creativecommons.org/licenses/by-nc/4.0/legalcode |
| 6ac3f774-d9fb-4796-b3e9-92bf6c81c084 | 21 | http://creativecommons.org/licenses/by/4.0/legalcode |
| 0a013f89-5381-4578-9d82-5f28fd5f1ef6 | 17 | http://creativecommons.org/licenses/by/4.0/legalcode |
| 83fdfd3d-3a25-4705-9fbe-3db1d1892b13 | 5 | http://creativecommons.org/licenses/by/4.0/legalcode |
| 963a6b96-4d22-4428-86e4-afee52cf4a8e | 3 | http://creativecommons.org/licenses/by/4.0/legalcode |
| cef450df-7155-4c9d-9eb3-7b9b4d868bfa | 1 | http://creativecommons.org/licenses/by-nc/4.0/legalcode |

Create a DOI-backed GBIF download or derived dataset before formal publication.
