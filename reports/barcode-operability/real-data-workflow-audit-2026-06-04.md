# Real Data Workflow Audit - 2026-06-04

## Summary

- total_checks: 10
- passed_checks: 10
- failed_checks: 0
- csv_runs: 4
- reference_runs: 2
- weak_spots: 2
- resolved_findings: 1

## CSV Upload -> Score Runs

- `aedes_ambiguous.csv`: expected `genus-safe`, got `genus-safe`; ok=True; run_id=1f94e4dbc76f40afbd667082233255f5
- `aedes_good.csv`: expected `species-safe`, got `species-safe`; ok=True; run_id=d76d416f38734ab3bc4fbeea7ccd70ea
- `aedes_missing_metadata.csv`: expected `not-publishable`, got `not-publishable`; ok=True; run_id=bf7ca102cec34deab9e88c08c430051f
- `aedes_weak_coverage.csv`: expected `weak`, got `weak`; ok=True; run_id=218778d93d784027ba86dcde5871a363

## Uploaded Reference FASTA Runs

- `audit_exact_31ae919a`: decision `species-safe`, top/candidate `Aedes albopictus`; ok=True
- `audit_ambiguous_31ae919a`: decision `genus-safe`, top/candidate `{'rank': 'genus', 'name': 'Aedes', 'taxon_key': None}`; ok=True

## Checks

- PASS: backend health
- PASS: CSV workflow aedes_ambiguous.csv
- PASS: CSV workflow aedes_good.csv
- PASS: CSV workflow aedes_missing_metadata.csv
- PASS: CSV workflow aedes_weak_coverage.csv
- PASS: CSV invalid DNA is rejected at validation
- PASS: CSV missing sequenceID is fatal
- PASS: Uploaded FASTA exact search becomes species-safe
- PASS: Uploaded FASTA ambiguous identical species downgrade to genus-safe
- PASS: Live GBIF API status

## Resolved During Audit

- **uploaded_reference_lineage**: Binomial uploaded references now infer genus lineage, so identical Aedes species downgrade to genus-safe instead of unranked ambiguous.

## Remaining Weak Spots

- **medium / local_reference_search**: Local runtime is using python-local mini-search, not VSEARCH/BLAST+. Impact: Good for validation and small references, but not enough for large production sequence search outside Docker. Fix: Use Docker stack or install vsearch/blastn locally; keep CSV scoring as the primary real-data path.
- **medium / docker_runtime**: Docker runtime smoke cannot be confirmed in this session: TimeoutExpired. Impact: Compose config is valid, but end-to-end Docker build/up still needs a Docker Desktop restart or healthy daemon. Fix: Restart Docker Desktop and run scripts/docker_smoke.sh.
