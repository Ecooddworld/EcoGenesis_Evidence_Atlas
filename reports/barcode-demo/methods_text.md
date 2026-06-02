# Methods

This run used **EcoGenesis Nexus V3 / Barcode-to-GBIF Evidence Compiler** ruleset `barcode-gbif-compiler-v2`.

## Purpose

The workflow converts DNA barcode, metabarcoding or Sequence ID / BLAST-style results into rank-aware molecular occurrence evidence for GBIF-oriented review. It is a downstream evidence compiler, not a replacement for GBIF Sequence ID, BOLD, UNITE, PR2, GTDB, BLAST+ or VSEARCH.

## Input Evidence

For each DNA sequence, the compiler consumed:

- sequence identifier and nucleotide sequence;
- reference-hit metrics: taxon, rank, lineage, percent identity, query coverage, aligned length, bit score and e-value when supplied;
- barcode-gap evidence: maximum within-taxon distance and minimum outside-taxon distance;
- diagnostic k-mer evidence and false-positive threshold;
- Darwin Core Occurrence metadata and DNA-derived workflow metadata.

Reference context: **COI Animals / BOLD public clustered reference**. Marker: **COI-5P**.

## Deterministic Gates

For each DNA barcode/metabarcoding sequence, the compiler evaluated percent identity, query coverage, a 95% ambiguity test over mismatch-rate standard errors, lowest common ancestor of indistinguishable hits, barcode gap, diagnostic k-mer support, diagnostic false-positive probability and GBIF publication metadata readiness.

Species-level output is fail-closed: a sequence is `species-safe` only when the exact match gate, ambiguity/LCA gate, positive barcode gap gate, diagnostic k-mer gate and publication-readiness gates all pass.

The pack separates `candidate_taxon` from `published_taxon`: blocked or weak records can remain useful as review hints, but they are not emitted as publishable Darwin Core species records.

## Naive Top-Hit Comparison

The `naive_top_hit_overclaims.csv` export lists records where a naive workflow would have published the top hit as a species, but EcoGenesis blocked, downgraded or moved the record to review. This is the core overclaim-prevention audit.

## Repair Optimization

The `repair_plan.csv` export ranks repair actions by unlockable record count. Metadata repairs are separated from molecular/reference blockers so publishers can see whether records need field repair, reference curation or new laboratory work.

Nexus V3 audit files in this Evidence Pack add:

- `hard_gate_audit.csv` for species-safe consistency checks;
- `naive_top_hit_overclaims.csv` for overclaim prevention evidence;
- `reference_gap_index.csv` for marker/reference bottlenecks;
- `repair_plan.csv` for publisher repair prioritization;
- `metadata_bottlenecks.csv` for field-level publication blockers.

## Claim Boundaries

The output is sequence-derived occurrence evidence under supplied reference context. It does not prove living presence, absence, population trend, true distribution, phenotype truth or ecological causality. Empty or low-evidence cells must be treated as no-evidence cells, not absence.
