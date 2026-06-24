# Competition 100-Sequence Atlas Run Report

Generated: 2026-06-15T02:27:51+02:00
Backend: local compiler script `backend/scripts/generate_competition_reports.py`
Run ID: `cc3a9564cc8e433b8a22ba1d1fb63d77`

## Result

- Records submitted: 100
- API status: completed
- Exports returned: 89
- Expected decisions matched: True
- Hard-gate failures: 0
- Evidence Pack ZIP SHA-256: `9b48725120d55cbd24bb9f769e72d8895b7317a4849394e6e2c0030cc1dc2fd2`
- GSEG/GSIG exports present: True
- ZIP contains GSEG/GSIG exports: True
- VSEA Parquet magic: `PAR1`
- Theorem checklist release gate: `pass`
- Graph roundtrip audit: `pass`

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

The run is fail-closed. Species-level output is allowed only when match gates, ambiguity/LCA, barcode gap, diagnostic k-mers, marker profile and publication gates agree. The GSEG/GSIG layer adds VSEA, graph provenance, theorem checklist, AI guardrails and roundtrip checks without claiming phenotype, function or production GraphDB/RDF behavior.
