# Report status

The current reproducible report sets are:

- `barcode-demo/`: the unsigned public mixed demo; it deliberately emits no trusted species rule-pass;
- `competition-100-sequences/` and `adversarial-100-sequences/`: repeated-fixture regression reports, not biological validation;
- `synthetic-ambiguity-benchmark/`: repeated synthetic stress fixtures with `release_eligible=false`, not an independent benchmark;
- `observatory-demo/`: offline/demo release-check evidence with occurrence context explicitly unlinked from molecular rows;
- `math-viability-audit/` and `barcode-operability/`: internal formula/operability checks.

Other dated or legacy report directories are preserved for traceability. Their historical `species-safe`, `GBIF-ready`, `verified`, theorem, proof, “scientific validation” and similar labels are superseded compatibility-era language and must not be cited as independent scientific validation, IPT ingestion or GBIF acceptance. Current release decisions must use `scientific_release_gate`, `dwca_validation.release_gate` and the external holdout/IPT boundaries in the current reports.

Historical directories may still contain `_gbif_ready.csv`, `theorem_checklist.json` or `verified_segment_evidence_array.*` bytes. New packs do not generate them, and the competition-report file API does not expose those retired aliases; use the explicit validation-candidate, release-invariant and rule-evidence filenames instead.
