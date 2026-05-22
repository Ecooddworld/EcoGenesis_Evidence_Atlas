# Evidence Graph Memory

Run: `3a809b00d7944721a9364dcb5b3d0459`
Taxon: **Quercus robur L.**
Region: **Western Europe live bbox**
Purpose: **Sampling gap analysis**
Readiness: **82.56/100**

## What This Adds

This graph memory turns the passport from a one-off report into a connected evidence node. It links the run to taxa, regions, datasets, quality issues, claims, actions and export artifacts.

## Node Counts

| Node type | Count |
| --- | ---: |
| runs | 1 |
| taxa | 1 |
| regions | 1 |
| datasets | 7 |
| issues | 0 |
| claims | 11 |
| actions | 4 |
| artifacts | 8 |

## Memory Cards

### Connected run memory

This run links 300 records, 7 datasets, 3 blocked claims and 4 next actions.

### Dataset memory

0 publisher feedback rows are connected to datasetKey-level provenance, so recurring quality blockers can be tracked across future runs.

### Claim memory

Blocked absence, distribution and trend claims are stored as graph nodes instead of disappearing into a static report.

### Judge-friendly vault

The vault is a normal Markdown bundle that can be opened offline and reviewed without running the web application.

## Key Edges

| Source | Relation | Target |
| --- | --- | --- |
| run:3a809b00d7944721a9364dcb5b3d0459 | uses_taxon | taxon:2878688 |
| run:3a809b00d7944721a9364dcb5b3d0459 | covers_region | region:western-europe-live-bbox |
| run:3a809b00d7944721a9364dcb5b3d0459 | serves_purpose | purpose:sampling_gaps |
| run:3a809b00d7944721a9364dcb5b3d0459 | draws_from_dataset | dataset:8a863029-f435-446a-821e-275f4f641165 |
| run:3a809b00d7944721a9364dcb5b3d0459 | draws_from_dataset | dataset:50c9509d-22c7-4a22-a47d-8c48425ef4a7 |
| run:3a809b00d7944721a9364dcb5b3d0459 | draws_from_dataset | dataset:6ac3f774-d9fb-4796-b3e9-92bf6c81c084 |
| run:3a809b00d7944721a9364dcb5b3d0459 | draws_from_dataset | dataset:0a013f89-5381-4578-9d82-5f28fd5f1ef6 |
| run:3a809b00d7944721a9364dcb5b3d0459 | draws_from_dataset | dataset:83fdfd3d-3a25-4705-9fbe-3db1d1892b13 |
| run:3a809b00d7944721a9364dcb5b3d0459 | draws_from_dataset | dataset:963a6b96-4d22-4428-86e4-afee52cf4a8e |
| run:3a809b00d7944721a9364dcb5b3d0459 | draws_from_dataset | dataset:cef450df-7155-4c9d-9eb3-7b9b4d868bfa |
| run:3a809b00d7944721a9364dcb5b3d0459 | supported_claim | claim:supported-gbif-mediated-records-matching-the-selected-taxon-and-region-are-present-in-th |
| run:3a809b00d7944721a9364dcb5b3d0459 | supported_claim | claim:supported-dataset-provenance-is-preserved-through-datasetkey-level-contribution-summarie |
| run:3a809b00d7944721a9364dcb5b3d0459 | weak_claim | claim:weak-record-clusters-can-indicate-areas-of-observation-activity-but-they-may-also-reflec |
| run:3a809b00d7944721a9364dcb5b3d0459 | weak_claim | claim:weak-the-selected-purpose-readiness-score-is-82-56-100-and-should-be-interpreted-with-th |
| run:3a809b00d7944721a9364dcb5b3d0459 | blocked_claim | claim:blocked-absence-cannot-be-inferred-from-empty-or-low-evidence-grid-cells |
| run:3a809b00d7944721a9364dcb5b3d0459 | blocked_claim | claim:blocked-observed-gbif-distribution-must-not-be-treated-as-the-true-species-distribution |
| run:3a809b00d7944721a9364dcb5b3d0459 | blocked_claim | claim:blocked-population-trend-cannot-be-inferred-without-temporal-sampling-bias-correction |
| run:3a809b00d7944721a9364dcb5b3d0459 | requires_verification_claim | claim:requires-verification-create-a-doi-backed-gbif-occurrence-download-or-derived-dataset-be |
| run:3a809b00d7944721a9364dcb5b3d0459 | requires_verification_claim | claim:requires-verification-inspect-high-coordinate-uncertainty-records-before-using-them-in-f |
| run:3a809b00d7944721a9364dcb5b3d0459 | requires_verification_claim | claim:requires-verification-treat-undersampled-occupied-cells-as-survey-priorities-not-confirm |
| run:3a809b00d7944721a9364dcb5b3d0459 | requires_verification_claim | claim:requires-verification-treat-empty-grid-cells-as-no-evidence-cells-not-absence-evidence |
| run:3a809b00d7944721a9364dcb5b3d0459 | recommends_action | action:create-a-doi-backed-gbif-occurrence-download-or-derived-dataset-before-publication |
| run:3a809b00d7944721a9364dcb5b3d0459 | recommends_action | action:preserve-datasetkey-and-run-json-with-any-downstream-analysis |
| run:3a809b00d7944721a9364dcb5b3d0459 | recommends_action | action:avoid-absence-claims-for-empty-or-low-effort-grid-cells |

## Vault

Open `evidence_vault.zip` to inspect the Markdown memory bundle. It is Obsidian-compatible, but every note is a normal Markdown file.
