# GSEG / GSIG Production Layer

EcoGenesis now exports a contest-safe Genome Segment Evidence Graph / Genome Segment Interpretation Graph layer on top of the barcode compiler.

This layer is intentionally conservative. It does not claim phenotype prediction, functional interpretation, production RDF/GraphDB operation or absolute biological truth from barcode evidence alone. Those stronger claims remain blocked or marked external-validation-missing in `release_invariant_checklist.json`.

## Implemented Contract

Every barcode run now emits:

- `rule_evidence_segment_array.csv`
- `rule_evidence_segment_array.jsonl`
- `rule_evidence_segment_array.parquet`
- `evidence_graph.json`
- `evidence_graph.jsonld`
- `gseg_graph_schema.json`
- `gsig_graph_schema.yaml`
- `release_invariant_checklist.json`
- `graph_provenance_audit.csv`
- `graph_roundtrip_audit.json`
- `vsea_graph_reconciliation.csv`
- `sharedness_overclaim_audit.csv`
- `function_claim_boundary_audit.csv`
- `ai_output_guardrail_audit.csv`
- `ai_dataset_export_audit.csv`
- `segment_canonicalization_audit.csv`
- `segment_cluster_audit.csv`
- `segment_taxon_matrix_audit.csv`
- `segment_trait_matrix_audit.csv`
- `ruleset_diff_report.json`
- `report_consistency_audit.csv`
- `judge_reproducibility_report.md`

The rule-evidence Parquet export is generated with `pyarrow` and is checked for Parquet magic bytes in the report generator.

The former `theorem_checklist.json` and `verified_segment_evidence_array.*` aliases are not emitted. Current consumers must use `release_invariant_checklist.json` and `rule_evidence_segment_array.*`.

## Guardrails

- Shared or ambiguous segments cannot become species-specific claims.
- `segment_safe_taxa.csv` recomputes the expected safe LCA from the uncertainty-hit lineages and marker profile. It reports `not_independently_recomputed` instead of `pass` when those source fields are unavailable.
- Function and phenotype claims are blocked unless curated external trait/function evidence exists.
- AI-facing exports preserve claim states and cannot upgrade `blocked`, `weak_hypothesis`, `taxon_ambiguous` or `review_only` records.
- Every graph node and edge must carry `id`, `type`, `ruleset_version` and `provenance_hash`.
- Roundtrip and rule-evidence/graph reconciliation audits must pass before the release invariant checklist can pass. Missing external validation leaves the release gate in `review`.

## Reproducible Checks

Run backend tests:

```bash
cd backend
.venv/bin/pytest tests/test_gseg_gsig_reference_checks.py tests/test_barcode_compiler.py -q
.venv/bin/pytest -q
```

Regenerate the contest reports:

```bash
cd backend
.venv/bin/python scripts/generate_competition_reports.py
```

Current expected report boundaries:

- The historical 100-row competition/adversarial suites are regression fixtures, not independent empirical validation; duplicated fixture rows must never be reported as 100 independent observations.
- Internal invariant and graph-roundtrip checks may pass, while the overall release gate remains `review` or `blocked` until specimen-backed external holdout validation and CI evidence are attached.
- Accuracy metrics such as precision, recall and false species rule-pass rate remain `null`/`external_validation_missing` when independent ground truth is absent.
