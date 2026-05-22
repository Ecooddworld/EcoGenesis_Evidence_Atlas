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

Occurrence evidence for Lynx pardinus in Iberian Peninsula live bbox was assembled from GBIF-mediated occurrence-style records using bbox [-10.0, 35.0, 4.5, 44.5]. The workflow retained datasetKey provenance, record counts per contributing dataset, coordinate uncertainty, event dates, licenses and GBIF issue flags. The evidence readiness score was computed for purpose 'dataset_quality_review' from spatial, temporal, taxonomic, sampling and provenance components. Empty grid cells were treated as no-evidence cells rather than absences.

## Journal-Ready Methods Text

GBIF-mediated occurrence-style records for Lynx pardinus were queried for Iberian Peninsula live bbox using bounding box [-10.0, 35.0, 4.5, 44.5]. Records were retained with datasetKey-level provenance, contribution counts, coordinate uncertainty, event dates, licenses and issue flags. The EcoGenesis Evidence Passport computed a purpose-aware readiness score for dataset_quality_review; empty grid cells were interpreted as no-evidence cells and not as absences.

## Dataset Contributions

| datasetKey | Records | License |
| --- | ---: | --- |
| 50c9509d-22c7-4a22-a47d-8c48425ef4a7 | 222 | http://creativecommons.org/licenses/by-nc/4.0/legalcode |
| 626c16d0-c37e-4b1f-9337-09d58c9eb9ff | 48 | http://creativecommons.org/licenses/by/4.0/legalcode |
| aa67ebd4-a094-4200-bb3b-55775128a670 | 22 | http://creativecommons.org/licenses/by/4.0/legalcode |
| 460daf52-49b6-4206-84b9-62a23b181f37 | 7 | http://creativecommons.org/licenses/by/4.0/legalcode |
| 3ccfe992-043a-4fff-951d-1e6e158854da | 1 | http://creativecommons.org/licenses/by/4.0/legalcode |

Create a DOI-backed GBIF download or derived dataset before formal publication.
