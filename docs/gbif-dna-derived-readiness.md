# GBIF DNA-Derived Readiness

This project is built as a downstream compiler for DNA barcode, metabarcoding or Sequence ID outputs. It does not replace GBIF Sequence ID. It turns molecular identification results into a publication-oriented package.

## GBIF Alignment

The compiler follows four official GBIF-facing ideas:

- Sequence ID-style match gates for identity and query coverage.
- Occurrence core readiness for molecular occurrence records.
- DNA-derived metadata readiness for sequence-based evidence.
- Transparent citations and reusable evidence package exports.

Official references:

- https://www.gbif.org/tools/sequence-id
- https://docs.gbif.org/publishing-dna-derived-data/en/
- https://www.gbif.org/data-quality-requirements-occurrences
- https://www.gbif.org/awards/ebbe-2026-rules

## Required Fields Used By The Compiler

Occurrence core:

- `occurrenceID`
- `basisOfRecord`
- `scientificName`
- `eventDate`

DNA-derived evidence:

- `marker`
- `sequenceID`
- `referenceDatabase`
- `identity`
- `queryCoverage`
- `methodOrSOP`

## Export Mapping

The compiler writes:

- `dwc_occurrence_core_template.csv`
- `dna_derived_extension_template.csv`
- `publication_blockers.csv`
- `methods_text.md`
- `citations.md`

These are templates for review and publication preparation, not an automatic GBIF upload.

## Why It Helps GBIF

The workflow can reduce unsafe molecular overclaims, make blocked records repairable, preserve reference provenance and help data publishers turn sequence-derived results into standardized, repeatable biodiversity evidence.
