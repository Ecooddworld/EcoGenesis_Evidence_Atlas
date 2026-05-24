# Barcode-to-GBIF Evidence Compiler Video Script

## 0:00-0:15 — Problem

DNA barcode and metabarcoding results often produce a top species hit, but top hit is not the same as a safe GBIF-ready occurrence record.

## 0:15-0:35 — Tool

Barcode-to-GBIF Evidence Compiler applies deterministic gates: identity, coverage, ambiguity, lowest common ancestor, barcode gap, diagnostic k-mers and publication metadata.

## 0:35-1:10 — Demo Run

Open the Compiler workbench. Select the mixed Aedes batch. Click `Generate Evidence Package`.

Show four outcomes:

- `species-safe`
- `genus-safe`
- `weak`
- `not-publishable`

## 1:10-1:45 — Why It Matters

The tool blocks unsafe species-level claims, downgrades ambiguous matches and separates taxonomic evidence from GBIF publication readiness.

## 1:45-2:15 — Evidence Pack

Open the export list:

- sequence safety table
- barcode gap report
- diagnostic k-mer report
- publication blockers
- Darwin Core template
- DNA-derived template
- molecular evidence report
- methods and citations

## 2:15-2:30 — Closing

The result is not another score. It is a reproducible compiler from molecular evidence to GBIF-ready publication review.
