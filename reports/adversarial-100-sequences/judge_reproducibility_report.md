# Judge Reproducibility Report

Run ID: `538da02248e942119c546a1cbfa10c9b`

## One-command checks

```bash
cd backend && .venv/bin/pytest -q
cd frontend && npm test -- --run && npm run build
scripts/docker_smoke.sh
```

## Required judge artifacts

- `release_invariant_checklist.json`
- `rule_evidence_segment_array.csv`
- `rule_evidence_segment_array.parquet`
- `graph_provenance_audit.csv`
- `molecular_evidence_report.html`
- `evidence_pack.zip`

The release invariant checklist currently reports release gate `review` with `0` blocking failures. Review/no-claim items are not proof obligations and should not be presented as external scientific validation.
