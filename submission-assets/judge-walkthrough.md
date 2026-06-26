# Judge Walkthrough

Use this file as the compact demo script for judges, release notes, or the public video description.

## Links

- Hosted demo: https://ecooddworld.eu
- Source repository: https://github.com/Ecooddworld/EcoGenesis_Evidence_Atlas
- Final local video: `submission-assets/barcode-video/video/ecogenesis-barcode-to-gbif-english-voice-ru-subs.mp4`
- Captions: `submission-assets/barcode-video/video/ecogenesis-barcode-to-gbif-english-voice-ru-subs.srt`
- Transcript: `submission-assets/barcode-video/video/ecogenesis-barcode-to-gbif-english-voiceover.txt`

## Main UI Flow

1. Open https://ecooddworld.eu.
2. Open `Run compiler`.
3. Upload `examples/aedes_good.csv`.
4. Review CSV preview and validation.
5. Click `Generate from CSV`.
6. Confirm the record is `species-safe`.
7. Open the output/export list.
8. Confirm `evidence_pack.zip`, `sequence_safety_table.csv`, `publication_blockers.csv`, `dwc_occurrence_core_publishable.csv`, `molecular_evidence_report.html`, `theorem_checklist.json`, `verified_segment_evidence_array.parquet` and `graph_provenance_audit.csv`.
9. Open `Math & proof` and show deterministic gates.
10. Open `Observatory`, run `Run GBIF-backed Aedes Spain`, then inspect `GBIF snapshot`, `VSEA`, `Graph`, `Exports` and `Judge`.

## Four Expected CSV Outcomes

| File | Expected outcome | Safe interpretation |
| --- | --- | --- |
| `examples/aedes_good.csv` | `species-safe` | Species-level molecular evidence is supported within the supplied reference context and required metadata pass. |
| `examples/aedes_ambiguous.csv` | `genus-safe` | A statistically indistinguishable competitor blocks species-level export and downgrades to LCA. |
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
- CSV run completes with `species_safe_records=1` and Evidence Pack exports.

## Claim Boundaries To Say Out Loud

- The tool does not infer species truth from top hits alone.
- A species label is exported only when identity, coverage, ambiguity, barcode gap, diagnostic k-mer and metadata gates pass.
- GBIF occurrence context explains provenance and citation context; it does not upgrade weak molecular claims.
- AI-ready exports preserve `claim_state`; they cannot promote blocked, weak or review-only records.
- Missing GBIF records are not evidence of absence.
