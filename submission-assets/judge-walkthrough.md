# Judge Walkthrough

Use this file as the compact demo script for judges, release notes, or the public video description.

## Links

- Hosted demo: https://ecooddworld.eu
- Submission video: https://ecooddworld.eu/submission-video/
- Source repository: https://github.com/Ecooddworld/EcoGenesis_Evidence_Atlas
- Final local video: `submission-assets/contest-video-v2/video/ecogenesis-gbif-contest-demo-en-subs.mp4`
- Captions: `submission-assets/contest-video-v2/video/ecogenesis-gbif-contest-demo-en.srt`
- Transcript: `submission-assets/contest-video-v2/video/ecogenesis-gbif-contest-demo-english-voiceover.txt`

## Main UI Flow

1. Open https://ecooddworld.eu.
2. Open `Run compiler`.
3. Upload `examples/aedes_good.csv`.
4. Review CSV preview and input checks.
5. Click `Generate from CSV`.
6. Confirm the basic CSV remains review-only because audited reference-completeness and sequence-QC evidence are not supplied.
7. Open the output/export list.
8. Confirm `evidence_pack.zip`, `sequence_safety_table.csv`, `publication_blockers.csv`, `dwc_occurrence_core_validation_candidates.csv`, `molecular_evidence_report.html`, `release_invariant_checklist.json`, `rule_evidence_segment_array.parquet` and `graph_provenance_audit.csv`.
9. Open `Methods & Audits` and show the configured gates and run-local invariants.
10. Open `Evidence Map`, run `Run reproducible judge demo`, then inspect `GBIF snapshot`, `Rule evidence`, `Graph`, `Exports` and `Judge`.

## Four Expected CSV Outcomes

| File | Expected outcome | Bounded interpretation |
| --- | --- | --- |
| `examples/aedes_good.csv` | review-only `ambiguous` | The basic CSV lacks audited reference-completeness and sequence-QC evidence; it is not an independent species validation. |
| `examples/aedes_ambiguous.csv` | `genus rule-pass` (`genus-safe` compatibility token) | A statistically indistinguishable competitor blocks species-level export and downgrades to LCA. |
| `examples/aedes_missing_metadata.csv` | `not-publishable` | Taxonomic evidence is preserved, but publication is blocked by missing occurrence metadata. |
| `examples/aedes_weak_coverage.csv` | `weak` | Identity alone is not enough because coverage fails the hard gate. |

## API Smoke

```bash
curl -fsS https://ecooddworld.eu/health
curl -fsS https://ecooddworld.eu/api/barcode/search-status
curl -F file=@examples/aedes_good.csv https://ecooddworld.eu/api/barcode/run-csv
```

Expected:

- health returns `ok`;
- search status reports `vsearch` or `blastn` availability;
- CSV run completes with `species_rule_pass_records=0`, explicit missing-reference/QC blockers and Evidence Pack exports.

## Claim Boundaries To Say Out Loud

- The tool does not infer species truth from top hits alone.
- A species-level validation candidate is emitted only when all configured molecular/assay rules and local metadata gates pass; that remains a run-local result, not species truth or GBIF acceptance.
- GBIF occurrence context explains provenance and citation context; it does not upgrade weak molecular claims.
- AI-ready exports preserve `claim_state`; they cannot promote blocked, weak or review-only records.
- Missing GBIF records are not evidence of absence.
