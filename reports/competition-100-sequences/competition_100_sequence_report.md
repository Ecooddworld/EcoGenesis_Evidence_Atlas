# Competition 100-Sequence Atlas Run Report

Generated: 2026-06-24T23:51:48+02:00
Backend: local compiler script `backend/scripts/generate_competition_reports.py`
Run ID: `70fbc9adfcab4cdaae0693fff8e21760`

## Result

- Records submitted: 100
- API status: completed
- Exports returned: 90
- Expected decisions matched: True
- Hard-gate failures: 0
- Evidence Pack ZIP SHA-256: `788eb5820d0dc8e0144991aa56c98551e88bf6f1e9371ba18fa73004c64f1221`
- GSEG/GSIG exports present: True
- ZIP contains GSEG/GSIG exports: True
- VSEA Parquet magic: `PAR1`
- Math viability audit: `pass` (941 checks, 0 failed)
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
