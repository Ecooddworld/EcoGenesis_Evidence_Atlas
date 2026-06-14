# EcoGenesis GSIG Observatory Demo Report

Run ID: `856f7bfa66814ce785b2bd809a252715`

## Verdict

Hard gate status: `pass`

The Observatory layer is active above the barcode/GSEG compiler. It captures a GBIF occurrence snapshot for Aedes in Spain, hashes and audits the snapshot, links it to the molecular segment evidence graph, and exports GBIF/AI previews without promoting any claim state.

## Run Summary

- Mode: `offline_demo`
- Source mode: `fixture`
- GBIF fallback used: `False`
- Occurrence context rows: `12`
- VSEA rows: `4`
- Segments: `4`
- Graph: `14` nodes, `17` edges
- Claim states: `{"taxon_supported": 3, "weak_hypothesis": 1}`

## Claim Boundary

GBIF records are occurrence, geography and dataset context. They never turn a weak or blocked molecular record into a verified taxon claim. Visualization, AI-ready exports and repair suggestions preserve the graph claim state.

## Proof Obligations

| OPO | Severity | Status | Artifact |
| --- | --- | --- | --- |
| OPO-01 | hard_gate | pass | `source_registry_audit.json` |
| OPO-02 | hard_gate | pass | `snapshot_manifest.json` |
| OPO-03 | hard_gate | pass | `api_policy_audit.csv` |
| OPO-04 | review_gate | pass | `gbif_query_strategy_audit.csv` |
| OPO-05 | hard_gate | pass | `source_provenance_manifest.json` |
| OPO-06 | review_gate | pass | `vsea_provenance_audit.csv` |
| OPO-07 | hard_gate | pass | `visualization_guardrail_audit.csv` |
| OPO-08 | review_gate | pass | `blocked_claim_visibility_audit.csv` |
| OPO-09 | hard_gate | pass | `sharedness_visual_overclaim_audit.csv` |
| OPO-10 | hard_gate | pass | `ai_dataset_export_audit.csv` |
| OPO-11 | review_gate | pass | `literature_claim_state_audit.csv` |
| OPO-12 | review_gate | pass | `contradiction_visual_audit.csv` |
| OPO-13 | hard_gate | pass | `gbif_export_claim_boundary_audit.csv` |
| OPO-14 | hard_gate | pass | `repair_optimizer_guardrail_audit.csv` |
| OPO-15 | hard_gate | pass | `offline_demo_reproducibility.json` |
| OPO-16 | review_gate | pass | `ui_ledger_consistency_audit.csv` |
| OPO-17 | hard_gate | pass | `graph_roundtrip_audit.csv` |
| OPO-18 | review_gate | pass | `source_freshness_claim_audit.csv` |
| OPO-19 | hard_gate | pass | `license_blocker_audit.csv` |
| OPO-20 | hard_gate | pass | `judge_mode_non_claims_audit.csv` |
