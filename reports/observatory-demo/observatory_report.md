# EcoGenesis GSIG Observatory Demo Report

Run ID: `0026e96063174d8f96d6066a7d59c14c`

## Verdict

Hard gate status: `pass`; overall release status: `review`

The Observatory layer is active above the barcode/GSEG compiler. It captures and audits a GBIF occurrence snapshot as run-level geographic context. Molecular rows remain explicitly unlinked unless shared specimen/event identifiers are supplied. GBIF/AI previews cannot promote claim state.

## Run Summary

- Mode: `offline_demo`
- Source mode: `fixture`
- GBIF fallback used: `False`
- Occurrence context rows: `12`
- Rule-evidence rows: `4`
- Segments: `4`
- Graph: `14` nodes, `13` edges
- Claim states: `{"taxon_ambiguous": 2, "taxon_supported": 1, "weak_hypothesis": 1}`

## Claim Boundary

GBIF records are occurrence, geography and dataset context. They never turn a weak or blocked molecular record into a rule-supported taxon claim. Visualization, AI-ready exports and repair suggestions preserve the graph claim state.

## Release Checks

| Check | Severity | Status | Artifact |
| --- | --- | --- | --- |
| RC-01 | hard_gate | pass | `source_registry_audit.json` |
| RC-02 | hard_gate | pass | `snapshot_manifest.json` |
| RC-03 | hard_gate | pass | `api_policy_audit.csv` |
| RC-04 | review_gate | pass | `gbif_query_strategy_audit.csv` |
| RC-05 | hard_gate | pass | `source_provenance_manifest.json` |
| RC-06 | review_gate | pass | `vsea_provenance_audit.csv` |
| RC-07 | hard_gate | pass | `visualization_guardrail_audit.csv` |
| RC-08 | review_gate | pass | `blocked_claim_visibility_audit.csv` |
| RC-09 | hard_gate | pass | `sharedness_visual_overclaim_audit.csv` |
| RC-10 | hard_gate | pass | `ai_dataset_export_audit.csv` |
| RC-11 | review_gate | not_applicable_no_claim | `literature_claim_state_audit.csv` |
| RC-12 | review_gate | not_applicable_no_claim | `contradiction_visual_audit.csv` |
| RC-13 | hard_gate | pass | `gbif_export_claim_boundary_audit.csv` |
| RC-14 | hard_gate | pass | `repair_optimizer_guardrail_audit.csv` |
| RC-15 | review_gate | informational_self_check | `offline_demo_reproducibility.json` |
| RC-16 | review_gate | pass | `ui_ledger_consistency_audit.csv` |
| RC-17 | hard_gate | pass | `graph_roundtrip_audit.csv` |
| RC-18 | review_gate | pass | `source_freshness_claim_audit.csv` |
| RC-19 | hard_gate | pass | `license_blocker_audit.csv` |
| RC-20 | hard_gate | pass | `judge_mode_non_claims_audit.csv` |
