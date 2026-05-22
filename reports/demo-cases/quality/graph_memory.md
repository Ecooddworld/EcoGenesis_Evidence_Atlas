# Evidence Graph Memory

Run: `51e12c0fb76d42f9ad818be4af84857f`
Taxon: **Lynx pardinus (Temminck, 1827)**
Region: **Iberian Peninsula live bbox**
Purpose: **Dataset quality review**
Readiness: **86.65/100**

## What This Adds

This graph memory turns the passport from a one-off report into a connected evidence node. It links the run to taxa, regions, datasets, quality issues, claims, actions and export artifacts.

## Node Counts

| Node type | Count |
| --- | ---: |
| runs | 1 |
| taxa | 1 |
| regions | 1 |
| datasets | 5 |
| issues | 1 |
| claims | 11 |
| actions | 6 |
| artifacts | 8 |

## Memory Cards

### Connected run memory

This run links 300 records, 5 datasets, 3 blocked claims and 6 next actions.

### Dataset memory

1 publisher feedback rows are connected to datasetKey-level provenance, so recurring quality blockers can be tracked across future runs.

### Claim memory

Blocked absence, distribution and trend claims are stored as graph nodes instead of disappearing into a static report.

### Judge-friendly vault

The vault is a normal Markdown bundle that can be opened offline and reviewed without running the web application.

## Key Edges

| Source | Relation | Target |
| --- | --- | --- |
| run:51e12c0fb76d42f9ad818be4af84857f | uses_taxon | taxon:2435261 |
| run:51e12c0fb76d42f9ad818be4af84857f | covers_region | region:iberian-peninsula-live-bbox |
| run:51e12c0fb76d42f9ad818be4af84857f | serves_purpose | purpose:dataset_quality_review |
| run:51e12c0fb76d42f9ad818be4af84857f | draws_from_dataset | dataset:50c9509d-22c7-4a22-a47d-8c48425ef4a7 |
| run:51e12c0fb76d42f9ad818be4af84857f | draws_from_dataset | dataset:626c16d0-c37e-4b1f-9337-09d58c9eb9ff |
| run:51e12c0fb76d42f9ad818be4af84857f | draws_from_dataset | dataset:aa67ebd4-a094-4200-bb3b-55775128a670 |
| run:51e12c0fb76d42f9ad818be4af84857f | draws_from_dataset | dataset:460daf52-49b6-4206-84b9-62a23b181f37 |
| run:51e12c0fb76d42f9ad818be4af84857f | draws_from_dataset | dataset:3ccfe992-043a-4fff-951d-1e6e158854da |
| run:51e12c0fb76d42f9ad818be4af84857f | detects_issue | issue:high-coordinate-uncertainty |
| dataset:50c9509d-22c7-4a22-a47d-8c48425ef4a7 | has_quality_issue | issue:high-coordinate-uncertainty |
| run:51e12c0fb76d42f9ad818be4af84857f | supported_claim | claim:supported-gbif-mediated-records-matching-the-selected-taxon-and-region-are-present-in-th |
| run:51e12c0fb76d42f9ad818be4af84857f | supported_claim | claim:supported-dataset-provenance-is-preserved-through-datasetkey-level-contribution-summarie |
| run:51e12c0fb76d42f9ad818be4af84857f | weak_claim | claim:weak-record-clusters-can-indicate-areas-of-observation-activity-but-they-may-also-reflec |
| run:51e12c0fb76d42f9ad818be4af84857f | weak_claim | claim:weak-the-selected-purpose-readiness-score-is-86-65-100-and-should-be-interpreted-with-th |
| run:51e12c0fb76d42f9ad818be4af84857f | blocked_claim | claim:blocked-absence-cannot-be-inferred-from-empty-or-low-evidence-grid-cells |
| issue:high-coordinate-uncertainty | limits_claim | claim:blocked-absence-cannot-be-inferred-from-empty-or-low-evidence-grid-cells |
| run:51e12c0fb76d42f9ad818be4af84857f | blocked_claim | claim:blocked-observed-gbif-distribution-must-not-be-treated-as-the-true-species-distribution |
| issue:high-coordinate-uncertainty | limits_claim | claim:blocked-observed-gbif-distribution-must-not-be-treated-as-the-true-species-distribution |
| run:51e12c0fb76d42f9ad818be4af84857f | blocked_claim | claim:blocked-population-trend-cannot-be-inferred-without-temporal-sampling-bias-correction |
| issue:high-coordinate-uncertainty | limits_claim | claim:blocked-population-trend-cannot-be-inferred-without-temporal-sampling-bias-correction |
| run:51e12c0fb76d42f9ad818be4af84857f | requires_verification_claim | claim:requires-verification-create-a-doi-backed-gbif-occurrence-download-or-derived-dataset-be |
| issue:high-coordinate-uncertainty | limits_claim | claim:requires-verification-create-a-doi-backed-gbif-occurrence-download-or-derived-dataset-be |
| run:51e12c0fb76d42f9ad818be4af84857f | requires_verification_claim | claim:requires-verification-inspect-high-coordinate-uncertainty-records-before-using-them-in-f |
| issue:high-coordinate-uncertainty | limits_claim | claim:requires-verification-inspect-high-coordinate-uncertainty-records-before-using-them-in-f |

## Vault

Open `evidence_vault.zip` to inspect the Markdown memory bundle. It is Obsidian-compatible, but every note is a normal Markdown file.
