# Adversarial 100-Sequence Fail-Closed Stress Report

Generated: 2026-06-14 Europe/Madrid
Backend: Docker `http://127.0.0.1:18100`
Run ID: `3942895d39fc4ef0978cd2670b0ca284`

## Result

- Records submitted: 100
- API status: completed
- Exports returned: 42
- Expected decisions matched: True
- Hard-gate failures: 0
- False species-safe outside positive controls: 0
- ZIP contains DOCX-required exports: True
- Evidence Pack ZIP SHA-256: `2b06bb7338a1942006439b56f3bfe662b5551853e3c38b0e98505fa87fcee47a`

## Decision classes

```json
{
  "species-safe": 10,
  "genus-safe": 20,
  "weak": 10,
  "no-match": 10,
  "not-publishable": 30,
  "ambiguous": 20
}
```

## By adversarial class

```json
{
  "assay_control_failure": {
    "not-publishable": 10
  },
  "close_sibling_ambiguity": {
    "genus-safe": 10
  },
  "genome_segment_non_barcode_marker": {
    "genus-safe": 10
  },
  "metadata_blocked_taxonomy_safe": {
    "not-publishable": 10
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
    "species-safe": 10
  },
  "weak_coverage_short_fragment": {
    "weak": 10
  },
  "wrong_taxonomy_name_conflict": {
    "not-publishable": 10
  }
}
```

## Interpretation

This stress suite intentionally includes no-match records, weak/short fragments, close-sibling ambiguity, metadata blockers, qPCR/control blockers, scientificName conflicts, custom non-barcode marker records, negative barcode gaps and missing diagnostic k-mers. Only the positive-control group is allowed to remain species-safe. All other species-looking inputs are blocked, downgraded or kept in repair/review states.
