# Judge Reproducibility Report

Run ID: `70fbc9adfcab4cdaae0693fff8e21760`

## One-command checks

```bash
cd backend && .venv/bin/pytest -q
cd frontend && npm test -- --run && npm run build
scripts/docker_smoke.sh
```

## Required judge artifacts

- `theorem_checklist.json`
- `verified_segment_evidence_array.csv`
- `verified_segment_evidence_array.parquet`
- `graph_provenance_audit.csv`
- `molecular_evidence_report.html`
- `evidence_pack.zip`

The theorem checklist currently reports release gate `pass` with `0` blocking failures. Roadmap/no-claim items are allowed only because the corresponding stronger claim is not exported.
