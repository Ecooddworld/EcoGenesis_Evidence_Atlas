# GBIF 2026 Submission Draft

## Submission Name

Barcode-to-GBIF Evidence Compiler

## One-Liner

A deterministic workflow that turns DNA barcode and metabarcoding outputs into safe, rank-aware and GBIF-ready molecular occurrence evidence.

## Abstract And Rationale

DNA barcode and metabarcoding workflows increasingly produce biodiversity evidence, but users often face a difficult final step: deciding whether a sequence result can safely support a species-level occurrence, whether the claim must be downgraded to genus or higher rank, and which metadata are missing before publication through GBIF-aligned workflows.

Barcode-to-GBIF Evidence Compiler addresses this gap. It takes sequence records, reference-hit metrics and publication metadata, then applies frozen deterministic gates: identity, query coverage, statistical ambiguity, lowest common ancestor, barcode gap, diagnostic k-mer support and GBIF/DNA-derived metadata readiness. The output is not a vague score. It is an auditable decision class: `species-safe`, `genus-safe`, `higher-rank-safe`, `ambiguous`, `weak`, `no-match` or `not-publishable`.

The tool improves the utility and quality of GBIF-mediated and GBIF-ready data by preventing unsafe top-hit species claims, producing repairable blockers, and generating Darwin Core and DNA-derived export templates with methods, citations and an evidence graph.

## How It Uses GBIF

- It follows GBIF Sequence ID-style identity and coverage match gates.
- It maps molecular evidence into Occurrence core and DNA-derived publication templates.
- It preserves GBIF taxon keys where supplied in reference hits.
- It links outputs to GBIF Sequence ID, DNA-derived publishing guidance, occurrence data-quality requirements and challenge rules.

## Operating Instructions

1. Open the frontend.
2. Choose `Compiler workbench`.
3. Select a demo case or paste a JSON request exported from a lab/Sequence ID workflow.
4. Click `Generate Evidence Package`.
5. Review the decision memo, sequence table and blockers.
6. Download `evidence_pack.zip`.

## Key Outputs

- `sequence_safety_table.csv`
- `safe_taxonomic_assignments.csv`
- `ambiguous_sequences.csv`
- `barcode_gap_report.csv`
- `diagnostic_kmer_report.csv`
- `publication_blockers.csv`
- `dwc_occurrence_core_template.csv`
- `dna_derived_extension_template.csv`
- `molecular_evidence_report.html`
- `methods_text.md`
- `citations.md`
- `evidence_graph.json`

## Why This Is Novel

The novelty is the compiler layer between molecular identification and biodiversity publication. Existing tools can identify sequences. This project focuses on the downstream decision: what rank is safe, what is blocked, what is repairable, and what can be packaged for GBIF-ready publication review.

## Demo Script

Show four cases:

1. A species-safe Aedes COI record.
2. Ambiguous top hits that downgrade to genus.
3. A high-identity short fragment blocked by coverage.
4. A species-safe molecular match that becomes `not-publishable` because `occurrenceID` and `eventDate` are missing.

End by downloading the evidence pack and opening the molecular evidence report.
