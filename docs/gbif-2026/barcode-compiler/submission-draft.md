# GBIF 2026 Submission Draft

## Submission Name

Molecular Evidence Conversion & Repair Engine for GBIF

## One-Liner

A deterministic engine that turns DNA barcode and metabarcoding outputs into safe, rank-aware, repairable and GBIF-ready molecular occurrence evidence.

## Abstract And Rationale

DNA barcode and metabarcoding workflows increasingly produce biodiversity evidence, but users often face a difficult final step: deciding whether a sequence result can safely support a species-level occurrence, whether the claim must be downgraded to genus or higher rank, and which metadata are missing before publication through GBIF-aligned workflows.

The Molecular Evidence Conversion & Repair Engine addresses this as an Evidence Conversion Problem: how can a large stream of DNA / metabarcoding detections be converted into the maximum number of safe, reproducible and GBIF-ready occurrence records without manual calibration and without false species-level claims?

The first working layer is the Barcode-to-GBIF Evidence Compiler. It takes sequence records, reference-hit metrics and publication metadata, then applies frozen deterministic gates: identity, query coverage, statistical ambiguity, lowest common ancestor, barcode gap, diagnostic k-mer support, diagnostic false-positive probability and GBIF/DNA-derived metadata readiness. The output is not a vague score. It is an auditable decision class: `species-safe`, `genus-safe`, `higher-rank-safe`, `ambiguous`, `weak`, `no-match` or `not-publishable`, plus repairable blockers and publication exports.

The tool improves the utility and quality of GBIF-mediated and GBIF-ready data by preventing unsafe top-hit species claims, producing repairable blockers, separating `candidate_taxon` from `published_taxon`, and generating publishable/review Darwin Core and DNA-derived export templates with methods, citations, a reference manifest and an evidence graph.

## How It Uses GBIF

- It follows GBIF Sequence ID-style identity and coverage match gates.
- It maps molecular evidence into Occurrence core and DNA-derived publication templates.
- It preserves GBIF taxon keys where supplied in reference hits.
- It links outputs to GBIF Sequence ID, DNA-derived publishing guidance, occurrence data-quality requirements and challenge rules.

## Operating Instructions

```bash
docker compose up --build
```

Open http://localhost:13100.

1. Open `Run compiler`.
2. Upload a CSV exported from GBIF Sequence ID, BLAST, BOLD, UNITE or a lab pipeline.
3. Use `Download CSV template` if needed.
4. Review the CSV preview and validation summary.
5. Click `Generate from CSV`.
6. Review the decision memo, sequence table, filters and blockers.
7. Download `evidence_pack.zip` or individual CSV/HTML exports.

Advanced JSON remains available for developer workflows, but CSV Upload -> Score is the primary judge-facing path.

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
- `dwc_occurrence_core_publishable.csv`
- `dwc_occurrence_core_review.csv`
- `dna_derived_extension_template.csv`
- `dna_derived_extension_publishable.csv`
- `molecular_evidence_report.html`
- `methods_text.md`
- `citations.md`
- `evidence_graph.json`

## Conversion And Repair Metrics

- `MECY = N_gbifReady / N`: molecular evidence conversion yield.
- `RY = N_repairable / N`: records unlockable through repair.
- `SRY = (N_species + N_genus + N_higher) / N`: safe-rank yield.
- `SSY = N_species / N`: species-safe yield.
- `OR_naive`: expected unsafe top-hit species overclaim rate under a naive workflow.
- `OR_compiler = 0` under the frozen rules because species claims are not emitted when gates fail.

The future repair optimizer ranks actions by how many GBIF-ready records they unlock, while the reference-gap index highlights taxa, markers and regions where reference libraries block safe species-level conversion.

## Why This Is Novel

The novelty is the conversion and repair layer between molecular identification and biodiversity publication. Existing tools can identify sequences. This project focuses on the downstream decision: what rank is safe, what is blocked, what is repairable, what reference gaps prevent species-safe conversion, and what can be packaged for GBIF-ready publication review.

The project also deliberately avoids unsafe claims. Protein translation is treated as a future coding-marker quality-control layer, not as species truth. Geography is interpreted as GBIF occurrence context for taxa carrying a fragment, not proof that the fragment was directly sampled everywhere. Phenotype/function links are future hypotheses requiring curated external evidence.

## Demo Script

Show four cases:

1. `examples/aedes_good.csv`: a species-safe Aedes COI record.
2. `examples/aedes_ambiguous.csv`: ambiguous top hits that downgrade to genus.
3. `examples/aedes_weak_coverage.csv`: a high-identity short fragment blocked by coverage.
4. `examples/aedes_missing_metadata.csv`: a species-safe molecular match that becomes `not-publishable` because `occurrenceID` and `eventDate` are missing.

End by downloading the evidence pack and opening the molecular evidence report.
