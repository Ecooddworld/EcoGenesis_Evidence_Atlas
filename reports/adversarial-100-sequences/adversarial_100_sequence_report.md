# Adversarial 100-Row Repeated-Fixture Regression Report

Generated: 2026-07-10T13:37:32+02:00
Backend: local compiler script `backend/scripts/generate_competition_reports.py`
Run ID: `538da02248e942119c546a1cbfa10c9b`

## Result

- Records submitted: 100
- Unique DNA sequence payloads: 1
- API status: completed
- Exports returned: 92
- Expected decisions matched: True
- Hard-gate failures: 0
- Evidence Pack ZIP SHA-256: `39bb474325813ef2be175979d1eeecc072737db062f7a57e7fe5b2928ef8ee43`
- GSEG/GSIG exports present: True
- ZIP contains GSEG/GSIG exports: True
- Rule-evidence Parquet magic: `PAR1`
- Math viability audit: `pass` (936 checks, 0 failed)
- Release-invariant gate: `review`
- External validation status: `blocked` (these are repeated regression fixtures, not independent specimens)
- Per-record evidence attestation key: `synthetic-regression-fixture-not-external-trust` (public synthetic regression key; not an external reference audit)
- DwC-A local validation: `blocked`; release gate: `blocked_local_validation`
- Graph roundtrip audit: `pass`
- Unexpected species rule-pass in molecular-negative fixtures: 0

## Decision classes

```json
{
  "species-rule-pass": 30,
  "genus-safe": 20,
  "weak": 10,
  "no-match": 10,
  "species-level-molecular-candidate-assay-blocked": 10,
  "ambiguous": 20
}
```

## Publication buckets

```json
{
  "publishable_candidate": 30,
  "repair_required": 70
}
```

## Export states

```json
{
  "dwc_template_ready": 30,
  "review_only": 40,
  "evidence_publishable_repair_required": 30
}
```

## By adversarial class

```json
{
  "assay_control_failure": {
    "species-level-molecular-candidate-assay-blocked": 10
  },
  "close_sibling_ambiguity": {
    "genus-safe": 10
  },
  "genome_segment_non_barcode_marker": {
    "genus-safe": 10
  },
  "metadata_blocked_taxonomy_safe": {
    "species-rule-pass": 10
  },
  "missing_diagnostic_kmer": {
    "ambiguous": 10
  },
  "negative_barcode_gap": {
    "ambiguous": 10
  },
  "no_match_novel_lineage": {
    "no-match": 10
  },
  "true_species_safe_positive": {
    "species-rule-pass": 10
  },
  "weak_coverage_short_fragment": {
    "weak": 10
  },
  "wrong_taxonomy_name_conflict": {
    "species-rule-pass": 10
  }
}
```

## Interpretation

This is a repeated-fixture regression run, not an empirical validation set. Species-level rule-pass output is fail-closed under the current gates. The GSEG/GSIG layer adds rule-evidence exports, graph provenance, release invariants, AI guardrails and roundtrip checks without claiming biological truth, accuracy, phenotype/function inference or production GraphDB/RDF behavior.
