# Evidence Graph Memory

Run: `ca871495e66e482d9013a39ace873dcc`
Taxon: **Aedes albopictus (Skuse, 1894)**
Region: **Spain live GBIF bbox**
Purpose: **Invasive watch**
Readiness: **97.7/100**

## What This Adds

This graph memory turns the passport from a one-off report into a connected evidence node. It links the run to taxa, regions, datasets, quality issues, claims, actions and export artifacts.

## Node Counts

| Node type | Count |
| --- | ---: |
| runs | 1 |
| taxa | 1 |
| regions | 1 |
| datasets | 8 |
| issues | 1 |
| claims | 10 |
| actions | 6 |
| artifacts | 8 |

## Memory Cards

### Connected run memory

This run links 300 records, 8 datasets, 3 blocked claims and 6 next actions.

### Dataset memory

1 publisher feedback rows are connected to datasetKey-level provenance, so recurring quality blockers can be tracked across future runs.

### Claim memory

Blocked absence, distribution and trend claims are stored as graph nodes instead of disappearing into a static report.

### Judge-friendly vault

The vault is a normal Markdown bundle that can be opened offline and reviewed without running the web application.

## Key Edges

| Source | Relation | Target |
| --- | --- | --- |
| run:ca871495e66e482d9013a39ace873dcc | uses_taxon | taxon:1651430 |
| run:ca871495e66e482d9013a39ace873dcc | covers_region | region:spain-live-gbif-bbox |
| run:ca871495e66e482d9013a39ace873dcc | serves_purpose | purpose:invasive_watch |
| run:ca871495e66e482d9013a39ace873dcc | draws_from_dataset | dataset:50c9509d-22c7-4a22-a47d-8c48425ef4a7 |
| run:ca871495e66e482d9013a39ace873dcc | draws_from_dataset | dataset:b2390da7-9704-4215-b038-3727df6e7fee |
| run:ca871495e66e482d9013a39ace873dcc | draws_from_dataset | dataset:04939588-db37-4806-bb09-a95886f7741e |
| run:ca871495e66e482d9013a39ace873dcc | draws_from_dataset | dataset:8a863029-f435-446a-821e-275f4f641165 |
| run:ca871495e66e482d9013a39ace873dcc | draws_from_dataset | dataset:040c5662-da76-4782-a48e-cdea1892d14c |
| run:ca871495e66e482d9013a39ace873dcc | draws_from_dataset | dataset:1fef1ead-3d02-495e-8ff1-6aeb01123408 |
| run:ca871495e66e482d9013a39ace873dcc | draws_from_dataset | dataset:99cb9e37-4cf6-4525-977d-10080fb9e094 |
| run:ca871495e66e482d9013a39ace873dcc | draws_from_dataset | dataset:6ac3f774-d9fb-4796-b3e9-92bf6c81c084 |
| run:ca871495e66e482d9013a39ace873dcc | detects_issue | issue:high-coordinate-uncertainty |
| dataset:50c9509d-22c7-4a22-a47d-8c48425ef4a7 | has_quality_issue | issue:high-coordinate-uncertainty |
| run:ca871495e66e482d9013a39ace873dcc | supported_claim | claim:supported-gbif-mediated-records-matching-the-selected-taxon-and-region-are-present-in-th |
| run:ca871495e66e482d9013a39ace873dcc | supported_claim | claim:supported-dataset-provenance-is-preserved-through-datasetkey-level-contribution-summarie |
| run:ca871495e66e482d9013a39ace873dcc | weak_claim | claim:weak-record-clusters-can-indicate-areas-of-observation-activity-but-they-may-also-reflec |
| run:ca871495e66e482d9013a39ace873dcc | weak_claim | claim:weak-the-selected-purpose-readiness-score-is-97-7-100-and-should-be-interpreted-with-the |
| run:ca871495e66e482d9013a39ace873dcc | blocked_claim | claim:blocked-absence-cannot-be-inferred-from-empty-or-low-evidence-grid-cells |
| issue:high-coordinate-uncertainty | limits_claim | claim:blocked-absence-cannot-be-inferred-from-empty-or-low-evidence-grid-cells |
| run:ca871495e66e482d9013a39ace873dcc | blocked_claim | claim:blocked-observed-gbif-distribution-must-not-be-treated-as-the-true-species-distribution |
| issue:high-coordinate-uncertainty | limits_claim | claim:blocked-observed-gbif-distribution-must-not-be-treated-as-the-true-species-distribution |
| run:ca871495e66e482d9013a39ace873dcc | blocked_claim | claim:blocked-population-trend-cannot-be-inferred-without-temporal-sampling-bias-correction |
| issue:high-coordinate-uncertainty | limits_claim | claim:blocked-population-trend-cannot-be-inferred-without-temporal-sampling-bias-correction |
| run:ca871495e66e482d9013a39ace873dcc | requires_verification_claim | claim:requires-verification-create-a-doi-backed-gbif-occurrence-download-or-derived-dataset-be |

## Vault

Open `evidence_vault.zip` to inspect the Markdown memory bundle. It is Obsidian-compatible, but every note is a normal Markdown file.
