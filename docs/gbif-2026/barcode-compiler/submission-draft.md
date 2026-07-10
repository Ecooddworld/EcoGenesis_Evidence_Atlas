# GBIF 2026 Submission Copy

## Submission Name

Molecular Evidence Conversion & Repair Engine for GBIF

## One-Liner

A deterministic, rule-based compiler that turns DNA barcode and metabarcoding outputs into bounded rank decisions, repair actions and GBIF validation-candidate packages.

## Abstract And Rationale

DNA barcode and metabarcoding workflows increasingly produce biodiversity evidence, but users often face a difficult final step: deciding whether a sequence result can safely support a species-level occurrence, whether the claim must be downgraded to genus or higher rank, and which metadata are missing before publication through GBIF-aligned workflows.

The Molecular Evidence Conversion & Repair Engine addresses this as an Evidence Conversion Problem: how can a stream of DNA / metabarcoding detections be triaged into reproducible rule results, explicit review states and structurally testable GBIF candidates without silently promoting a top hit to species truth?

The first working layer is the Barcode-to-GBIF Evidence Compiler. It takes sequence records, reference-hit metrics and publication metadata, then applies deterministic gates for identity, query coverage, ambiguity, lowest common ancestor, sampling-aware barcode gap, locally conserved k-mer support, sequence QC, audited reference completeness, assay semantics and GBIF/DNA-derived metadata readiness. Its primary scientific output is `species-rule-pass`, `genus-rule-result`, `higher-rank-rule-result`, `ambiguous`, `weak` or `no-match`, accompanied by blockers and evidence exports. These states report that configured rules passed; they are not independently validated taxonomic truth. Legacy `*-safe` values remain only as API compatibility tokens.

The tool is intended to improve review quality by blocking unsupported top-hit species promotion, producing repairable blockers, separating `candidate_taxon` from `published_taxon`, and generating review/validation-candidate Darwin Core artifacts with methods, citations, a reference manifest and an evidence graph. It can build a locally validated DwC-A, but IPT ingestion, publisher review and GBIF acceptance remain external release gates.

The repeated 100-row fixtures are regression suites, not biological validation datasets. No independent specimen-backed holdout is bundled, so the scientific release gate intentionally remains blocked.

## How It Uses GBIF

- It follows GBIF Sequence ID-style identity and coverage match gates.
- It maps molecular evidence into Occurrence core and DNA-derived publication templates.
- It preserves GBIF taxon keys where supplied in reference hits.
- It links outputs to GBIF Sequence ID, DNA-derived publishing guidance, occurrence data-quality requirements and challenge rules.

## Operating Instructions

Hosted demo: https://ecooddworld.eu

```bash
docker compose up --build
```

Open the hosted demo or local http://localhost:13100.

1. Open `Run compiler`.
2. Upload a CSV exported from GBIF Sequence ID, BLAST, BOLD, UNITE or a lab pipeline.
3. Use `Download CSV template` if needed.
4. Review the CSV preview and validation summary.
5. Click `Generate from CSV`.
6. Review the decision memo, sequence table, filters and blockers.
7. Download `evidence_pack.zip` or individual CSV/HTML exports.

Advanced JSON remains available for developer workflows, but CSV upload → compile is the primary judge-facing path.

## Key Outputs

- `sequence_safety_table.csv`
- `safe_taxonomic_assignments.csv`
- `review_taxonomic_hints.csv`
- `ambiguous_sequences.csv`
- `barcode_gap_report.csv`
- `diagnostic_kmer_report.csv`
- `publication_blockers.csv`
- `reference_manifest.json`
- `dwc_occurrence_core_template.csv`
- `dwc_occurrence_core_validation_candidates.csv`
- `dwc_occurrence_core_review.csv`
- `dna_derived_extension_template.csv`
- `dna_derived_extension_validation_candidates.csv`
- `dwca.zip`
- `dwca_validation_report.json`
- `dwca_roundtrip_contract.json`
- `molecular_evidence_report.html`
- `methods_text.md`
- `citations.md`
- `evidence_graph.json`

## Conversion And Repair Metrics

- `VCY = N_validationCandidate / N`: local validation-candidate yield; it is not a GBIF acceptance rate.
- `RY = N_repairable / N`: records unlockable through repair.
- `RRY = (N_speciesRulePass + N_genusRuleResult + N_higherRuleResult) / N`: configured rank-rule result yield.
- `SPY = N_speciesRulePass / N`: species-rule-pass yield.
- `OR_naive_fixture`: top-hit promotion rate within the explicitly synthetic regression fixtures.
- `OR_compiler_fixture`: blocked promotion rate within those fixtures; it is not an empirical false-positive estimate.

The repair optimizer ranks actions by how many local validation candidates they may unlock, while the reference-gap index highlights taxa, markers and regions where reference libraries block a species-level rule result.

## Why This Is Novel

The novelty is the conversion and repair layer between molecular identification and biodiversity publication. Existing tools can identify sequences. This project focuses on the downstream decision: which rank the configured evidence rules support, what is blocked, what is repairable, which reference gaps prevent a stronger result, and what can be packaged for external GBIF/IPT validation.

The project also deliberately avoids unsafe claims. Protein translation is treated as a future coding-marker quality-control layer, not as species truth. Geography is interpreted as GBIF occurrence context for taxa carrying a fragment, not proof that the fragment was directly sampled everywhere. Phenotype/function links are future hypotheses requiring curated external evidence.

## Demo Script

Show four cases:

1. `examples/aedes_good.csv`: a user CSV that remains review-only because it lacks an audited reference-completeness/QC evidence bundle.
2. `examples/aedes_ambiguous.csv`: ambiguous top hits that produce a genus-level rule result.
3. `examples/aedes_weak_coverage.csv`: a high-identity short fragment blocked by coverage.
4. `examples/aedes_missing_metadata.csv`: a molecular candidate whose scientific and publication blockers remain explicit.
5. The clearly labelled built-in regression fixture: demonstrates `species-rule-pass` mechanics without presenting the fixture as external validation.

End by downloading the evidence pack and opening the molecular evidence report.
