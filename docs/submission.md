# GBIF 2026 Submission Documentation

## Submission Name

Molecular Evidence Conversion & Repair Engine for GBIF

Working module: **Barcode-to-GBIF Evidence Compiler**

## Core Idea

The project turns DNA barcode, metabarcoding and Sequence ID-style outputs into safe, rank-aware and GBIF-ready molecular occurrence evidence.

It does not try to guess species from DNA in a black-box way. It answers:

> Can this molecular record safely support a species-level occurrence, must it be downgraded to genus or higher rank, or is it blocked from publication until evidence or metadata are repaired?

## Contest Fit

The 2026 GBIF Ebbe Nielsen Challenge accepts tools, workflows and analyses that improve the access, utility or quality of GBIF-mediated data. This compiler improves quality and utility by:

- preventing unsafe species-level overclaims from top-hit molecular matches;
- preserving ambiguous evidence at the safest supported taxonomic rank;
- separating taxonomic safety from GBIF publication readiness;
- exposing repair actions for publishers and data managers;
- producing repeatable CSV, HTML, JSON and ZIP Evidence Packs.
- adding a GSEG/GSIG proof layer with VSEA, graph provenance, theorem checklist and AI guardrail audits while unsupported function/phenotype claims remain blocked.
- adding a GSIG Observatory layer that hashes GBIF source snapshots, visualizes VSEA-to-graph evidence, preserves claim boundaries in GBIF/AI exports and ships all 20 OPO proof-obligation artifacts.

## What The Tool Produces

Each run produces:

- `sequence_safety_table.csv`
- `data_accounting_ledger.csv`
- `state_machine_audit.csv`
- `claim_boundaries.csv`
- `segment_overlap_report.csv`
- `safe_taxonomic_assignments.csv`
- `review_taxonomic_hints.csv`
- `ambiguous_sequences.csv`
- `barcode_gap_report.csv`
- `diagnostic_kmer_report.csv`
- `math_viability_audit.json`
- `gbif_backbone_matches.csv`
- `publication_blockers.csv`
- `repair_plan.csv`
- `metadata_bottlenecks.csv`
- `reference_gap_index.csv`
- `reference_completeness_audit.csv`
- `marker_profile_audit.csv`
- `assay_gate_audit.csv`
- `dna_extension_readiness.csv`
- `hard_gate_audit.csv`
- `naive_top_hit_overclaims.csv`
- `source_provenance_manifest.json`
- `reference_manifest.json`
- `dwc_occurrence_core_template.csv`
- `dwc_occurrence_core_publishable.csv`
- `dwc_occurrence_core_gbif_ready.csv`
- `dwc_occurrence_core_review.csv`
- `dwc_occurrence_core_review_or_repair.csv`
- `dna_derived_extension_template.csv`
- `dna_derived_extension_publishable.csv`
- `dna_derived_extension_gbif_ready.csv`
- `molecular_evidence_report.html`
- `methods_text.md`
- `citations.md`
- `evidence_graph.json`
- `evidence_graph.jsonld`
- `nexus_v3_summary.json`
- `proof_by_failure_modes.md`
- `theorem_checklist.json`
- `artifact_checksums.json`
- `query_smoke_report.md`
- `ci_math_oracle_report.json`
- `gseg_graph_schema.json`
- `gsig_graph_schema.yaml`
- `verified_segment_evidence_array.csv`
- `verified_segment_evidence_array.jsonl`
- `verified_segment_evidence_array.parquet`
- `graph_provenance_audit.csv`
- `graph_roundtrip_audit.json`
- `vsea_graph_reconciliation.csv`
- `sharedness_overclaim_audit.csv`
- `function_claim_boundary_audit.csv`
- `ai_output_guardrail_audit.csv`
- `ai_dataset_export_audit.csv`
- `judge_reproducibility_report.md`
- `evidence_pack.json`
- `evidence_pack.zip`

The Observatory run additionally produces:

- `observatory_evidence_pack.zip`
- `observatory_report.md`
- `source_registry_audit.json`
- `snapshot_manifest.json`
- `source_provenance_manifest.json`
- `observatory_vsea.csv`
- `observatory_vsea.parquet`
- `observatory_graph.jsonld`
- `gbif_export_preview.csv`
- `ai_ready_dataset.jsonl`
- `observatory_output_verification.json`
- `observatory_output_verification.md`
- all 20 `OPO-*` audit artifacts from `ecogenesis_gsig_observatory_proof_obligations_v4.json`

## Demo Flow For Judges

1. Open the hosted app at https://ecooddworld.eu, or run it locally at http://localhost:13100.
2. Open `Run compiler`.
3. Upload `examples/aedes_good.csv`.
4. Show CSV preview and validation summary.
5. Click `Generate from CSV`.
6. Show `species-safe` decision and Evidence Pack exports.
7. Upload or explain `examples/aedes_ambiguous.csv` to show downgrade to `genus-safe`.
8. Upload or explain `examples/aedes_missing_metadata.csv` to show taxonomic evidence preserved while publication is blocked.
9. Open `Math & proof` to show the deterministic gates.
10. Show the `GSEG / GSIG proof layer` export group: `theorem_checklist.json`, VSEA Parquet and graph provenance.
11. Open `Observatory`, run `Run GBIF-backed Aedes Spain`, and show the GBIF occurrence context map, VSEA matrix, Evidence Graph Explorer and proof wheel before opening the source snapshot, VSEA, graph, exports and Judge tabs.
12. Open `Research audit` to show the GBIF occurrence-audit layer and 100 evidence claims.

## Operating Instructions

Hosted demo:

- https://ecooddworld.eu
- https://www.ecooddworld.eu

Local Docker run:

```bash
docker compose up --build
```

Open:

- Frontend: http://localhost:13100
- Backend API docs: http://localhost:18100/docs

This command builds the local contest-review stack: static production frontend, `/api` proxy, FastAPI backend, bundled example reference datasets, VSEARCH and NCBI BLAST+ installed in the backend image, and generated evidence packs persisted in `./data`.

Hosted production uses `docker-compose.caddy.yml` with Caddy. HTTP redirects to HTTPS, TLS is handled automatically, and the backend is exposed only inside the Docker network.

Run tests:

```bash
cd backend
.venv/bin/python -m pytest -q
.venv/bin/python scripts/generate_competition_reports.py
.venv/bin/python scripts/generate_observatory_demo_report.py
.venv/bin/python scripts/verify_observatory_outputs.py

cd ../frontend
npm test -- --run
npm run build
```

Run barcode operability verification:

```bash
cd backend
.venv/bin/python scripts/verify_barcode_operability.py
```

Run the optional GBIF occurrence-audit suite in live network mode:

```bash
cd backend
.venv/bin/python scripts/run_scientific_hypothesis_suite.py --fresh --output-dir /tmp/ecogenesis-scientific-theory-suite
```

## Scope Boundaries

The compiler is a downstream safety and publication-readiness layer for Sequence ID / BLAST-style outputs. It does not replace GBIF Sequence ID and does not infer species from FASTA-only input.

The project does not claim:

- species absence from empty cells;
- true species distribution from GBIF occurrence points alone;
- population trends without a trend model and sampling-bias correction;
- phenotype truth from barcode evidence.

## Submission Assets

- Entry form copy: `submission-assets/gbif-entry-form-draft.md`
- Final checklist: `submission-assets/final-submission-checklist.md`
- Video script: `submission-assets/barcode-video-script.md`
- Final pack: `submission-assets/gbif-2026-final-submission-pack.md`
