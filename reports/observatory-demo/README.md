# GSIG Observatory Demo Report

Generated from the repository code with:

```bash
cd backend
.venv/bin/python scripts/generate_observatory_demo_report.py
```

Run ID: `0026e96063174d8f96d6066a7d59c14c`

## Result

- Hard gate status: `pass`
- GBIF source mode: `fixture`
- Occurrence context rows: `12`
- Rule-evidence rows: `4`
- Segments: `4`
- Graph: `14` nodes, `13` edges
- Claim states: `{"taxon_ambiguous": 2, "taxon_supported": 1, "weak_hypothesis": 1}`

## Contest Boundary

This report uses the Observatory layer as a source-backed explanation and audit shell. GBIF occurrence rows are hashed context only. Molecular claim states are produced by the barcode/GSEG gates, and the UI/export layer cannot upgrade them.

Key files:

- `observatory_evidence_pack.zip`
- `observatory_report.md`
- `snapshot_manifest.json`
- `source_registry_audit.json`
- `observatory_vsea.parquet`
- `observatory_graph.jsonld`
- `gbif_export_preview.csv`
- `ai_ready_dataset.jsonl`
- `release_check_summary.json`
- `proof_summary.json` (deprecated compatibility alias)
- `observatory_output_verification.json`
- `observatory_output_verification.md`
