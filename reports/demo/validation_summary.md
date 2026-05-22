# Validation Summary

Current case: **Aedes albopictus - Spain live GBIF bbox - Invasive watch**
Score: **97.7/100**
Source mode: **online**
Passed checks: **5/5**

## Checks

| Passed | Check | Metric | Why it matters |
| --- | --- | ---: | --- |
| yes | datasetKey provenance preserved | 1.0 | GBIF reuse and derived datasets need auditable datasetKey lineage. |
| yes | No-evidence cells separated from absence claims | 0 | The tool blocks a common misuse of occurrence data: treating missing records as absences. |
| yes | Citation completion flow generated | 5 | Users get explicit steps for DOI-backed or derived-dataset reuse. |
| yes | Publisher feedback rows generated when data issues exist | 1 | Data managers receive actionable fixes grouped by datasetKey. |
| yes | Repeatable run metadata generated | 300 | run.json, source_summary.json and checksums let judges and reviewers reproduce the analysis. |

## Measurable Outcomes

- Time-to-first-review is reduced because the app opens with a complete evidence memo, map and export bundle.
- Risk of unsupported absence, trend or distribution claims is reduced through explicit claim guardrails.
- Citation compliance improves because dataset contributions, DOI gaps and methods text are generated together.
- Publisher feedback becomes actionable because issues are grouped by datasetKey, severity and fix priority.

## Recommended Demo Suite

- **invasive_watch**: Aedes albopictus in Spain live GBIF bbox for invasive_watch - Recent invasive-species screening with coordinate uncertainty caveats.
- **sampling_gaps**: Quercus robur in Western Europe live bbox for sampling_gaps - No-evidence cells and survey priorities without absence overclaiming.
- **dataset_quality_review**: Lynx pardinus in Iberian Peninsula live bbox for dataset_quality_review - Publisher-side issue prioritization and provenance review.

## Remaining Validation Work

- Attach at least one DOI-backed GBIF download or derived dataset case before final publication use.
- Record a three-minute screen capture that walks through the default run, claim guardrails and export pack.
- Run the three demo scenarios before submission freeze and save their generated passports as release assets.
