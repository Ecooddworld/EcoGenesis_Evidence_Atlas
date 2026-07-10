# Competition 100-Row Repeated-Fixture Regression Report

Generated: 2026-07-10T13:37:12+02:00
Backend: local compiler script `backend/scripts/generate_competition_reports.py`
Run ID: `b2a2d9edb772432db11c6be440a5df05`

## Result

- Records submitted: 100
- Unique DNA sequence payloads: 1
- API status: completed
- Exports returned: 92
- Expected decisions matched: True
- Hard-gate failures: 0
- Evidence Pack ZIP SHA-256: `63e994dba0909dba4bf1b9b4155a78a4f90cc71e5dbba4484b2260824eda477a`
- GSEG/GSIG exports present: True
- ZIP contains GSEG/GSIG exports: True
- Rule-evidence Parquet magic: `PAR1`
- Math viability audit: `pass` (941 checks, 0 failed)
- Release-invariant gate: `review`
- External validation status: `blocked` (these are repeated regression fixtures, not independent specimens)
- Per-record evidence attestation key: `synthetic-regression-fixture-not-external-trust` (public synthetic regression key; not an external reference audit)
- DwC-A local validation: `blocked`; release gate: `blocked_local_validation`
- Graph roundtrip audit: `pass`

## Decision classes

```json
{
  "species-rule-pass": 50,
  "genus-safe": 25,
  "weak": 25
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

This is a repeated-fixture regression run, not an empirical validation set. Species-level rule-pass output is fail-closed under the current gates. The GSEG/GSIG layer adds rule-evidence exports, graph provenance, release invariants, AI guardrails and roundtrip checks without claiming biological truth, accuracy, phenotype/function inference or production GraphDB/RDF behavior.
