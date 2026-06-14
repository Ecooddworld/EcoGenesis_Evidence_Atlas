# Competition 100-Sequence Atlas Run Report

Generated: 2026-06-14 Europe/Madrid
Backend: Docker `http://127.0.0.1:18100`
Run ID: `7a9aea4135a1479e89afe114c16ff9b3`

## Result

- Records submitted: 100
- API status: completed
- Exports returned: 42
- Expected decisions matched: True
- Hard-gate failures: 0
- Evidence Pack ZIP SHA-256: `6a4ff3b8995724c494f6c5345160a5cfc66f3497ddbddb2f4a6334272693a25b`
- New DOCX-required exports present: True
- ZIP contains new DOCX-required exports: True

## Decision classes

```json
{
  "species-safe": 25,
  "genus-safe": 25,
  "weak": 25,
  "not-publishable": 25
}
```

## Publication buckets

```json
{
  "publishable_candidate": 50,
  "repair_required": 50
}
```

## Export states

```json
{
  "dwc_template_ready": 50,
  "review_only": 25,
  "evidence_publishable_repair_required": 25
}
```

## Interpretation

The 100-sequence run remains fail-closed: 25 species-safe records, 25 genus-safe records, 25 weak records and 25 metadata-blocked not-publishable records. Publishable candidate rows are separated from formal GBIF-ready rows; this run has 50 publishable candidates and 0 formal GBIF-ready rows because dataset-level publication metadata remains intentionally gated.

The updated Evidence Pack now includes `data_accounting_ledger.csv`, `state_machine_audit.csv`, `reference_completeness_audit.csv`, structured `publication_blockers.csv`, graph-backed `claim_boundaries.csv`, and `profile_id` in `safe_taxonomic_assignments.csv`.
