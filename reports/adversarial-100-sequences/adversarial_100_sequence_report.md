# Adversarial 100-Sequence Fail-Closed Stress Report

Generated: 2026-06-14T22:06:17+02:00
Backend: local compiler script `backend/scripts/generate_competition_reports.py`
Run ID: `ea9e5b6147734b919ec53070bedffeaa`

## Result

- Records submitted: 100
- API status: completed
- Exports returned: 89
- Expected decisions matched: True
- Hard-gate failures: 0
- Evidence Pack ZIP SHA-256: `0f7b7162f2b3e139e1bf60634359392d31f9b015d467e94241b04b0548f02357`
- GSEG/GSIG exports present: True
- ZIP contains GSEG/GSIG exports: True
- VSEA Parquet magic: `PAR1`
- Theorem checklist release gate: `pass`
- Graph roundtrip audit: `pass`
- False species-safe outside positive controls: 0

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

The run is fail-closed. Species-level output is allowed only when match gates, ambiguity/LCA, barcode gap, diagnostic k-mers, marker profile and publication gates agree. The GSEG/GSIG layer adds VSEA, graph provenance, theorem checklist, AI guardrails and roundtrip checks without claiming phenotype, function or production GraphDB/RDF behavior.
