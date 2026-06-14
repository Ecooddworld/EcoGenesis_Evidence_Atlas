# GSEG / GSIG Production Layer

EcoGenesis now exports a contest-safe Genome Segment Evidence Graph / Genome Segment Interpretation Graph layer on top of the barcode compiler.

This layer is intentionally conservative. It does not claim phenotype prediction, functional interpretation, production RDF/GraphDB operation or absolute biological truth from barcode evidence alone. Those stronger claims remain blocked as `blocked_roadmap_no_claim` in `theorem_checklist.json`.

## Implemented Contract

Every barcode run now emits:

- `verified_segment_evidence_array.csv`
- `verified_segment_evidence_array.jsonl`
- `verified_segment_evidence_array.parquet`
- `evidence_graph.json`
- `evidence_graph.jsonld`
- `gseg_graph_schema.json`
- `gsig_graph_schema.yaml`
- `theorem_checklist.json`
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

The VSEA Parquet export is generated with `pyarrow` and is checked for Parquet magic bytes in the 100-sequence report generator.

## Guardrails

- Shared or ambiguous segments cannot become species-specific claims.
- Function and phenotype claims are blocked unless curated external trait/function evidence exists.
- AI-facing exports preserve claim states and cannot upgrade `blocked`, `weak_hypothesis`, `taxon_ambiguous` or `review_only` records.
- Every graph node and edge must carry `id`, `type`, `ruleset_version` and `provenance_hash`.
- Roundtrip and VSEA/graph reconciliation audits must pass before the theorem checklist release gate can pass.

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

Current expected report facts:

- `reports/competition-100-sequences/competition_100_sequence_report.md`: 100 records, 89 exports, expected decisions matched, hard-gate failures `0`, theorem release gate `pass`, graph roundtrip `pass`.
- `reports/adversarial-100-sequences/adversarial_100_sequence_report.md`: 100 records, 89 exports, expected decisions matched, false species-safe outside positive controls `0`, theorem release gate `pass`, graph roundtrip `pass`.
