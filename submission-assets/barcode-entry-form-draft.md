# Barcode-to-GBIF Evidence Compiler Entry Form Copy

Use `submission-assets/gbif-entry-form-draft.md` as the canonical copy-ready form text. This file keeps the shorter project-specific version for quick reference.

## Submission Name

Molecular Evidence Conversion & Repair Engine for GBIF

Short title: Barcode-to-GBIF Evidence Compiler

## One-Liner

A deterministic workflow that turns DNA barcode, metabarcoding and Sequence ID-style outputs into bounded rank results, GBIF validation candidates and explicit repair actions.

## Abstract

Barcode-to-GBIF Evidence Compiler receives CSV or JSON results from GBIF Sequence ID, BLAST, BOLD, UNITE or laboratory pipelines and determines whether each molecular record passes the configured species-level rules, must be downgraded to genus or higher rank, or is blocked from a validation-candidate export by sequence, reference or metadata gaps.

It applies explicit gates for identity, query coverage, ambiguity, lowest common ancestor, barcode gap, locally unique k-mer support, false-positive risk and GBIF/DNA-derived publication checks. It separates the molecular rule result from metadata readiness and export eligibility, preventing unsupported species-level overclaims while preserving repairable molecular evidence. Passing these local rules is not independent taxonomic validation.

Each run exports an Evidence Pack with sequence decision tables, bounded taxonomic candidates, publication blockers, barcode-gap and k-mer reports, Darwin Core validation-candidate templates, DNA-derived extension templates, a molecular evidence report, methods text, citations, a rule-evidence array, a release-invariant checklist, provenance audits and machine-readable JSON/ZIP/Parquet files.

The advanced audit layer adds hard-gate consistency checks, naive top-hit overclaim prevention, reference-gap analysis, metadata bottlenecks, repair plans, validation-candidate/review exports, graph roundtrip checks and AI output guardrails. The Evidence Map adds a source registry, hashed GBIF snapshots, rule-evidence visualization, release checks, a GBIF validation-candidate preview and AI-export guardrails. These are run-local consistency and provenance checks, not proof of biological truth or external GBIF acceptance.

The tool benefits GBIF data users, publishers, nodes and reviewers by making molecular occurrence candidates more transparent, repeatable and easier to repair before external validation and publication.

## Operating Instructions

Hosted demo: https://ecooddworld.eu

```bash
docker compose up --build
```

Open the hosted demo or local http://localhost:13100, go to `Run Compiler`, upload one of the CSV examples in `examples/`, review the input checks, click `Generate from CSV`, inspect the decision table and download `evidence_pack.zip`. Then open `Evidence Map`, run the reproducible judge demo, inspect the source snapshot, rule-evidence rows, graph, exports and Judge tabs, and download `observatory_evidence_pack.zip`.

## Required Final Links

- Hosted demo: https://ecooddworld.eu
- Public video URL: https://ecooddworld.eu/submission-video/
- Source repository URL: https://github.com/Ecooddworld/EcoGenesis_Evidence_Atlas
- `docs/submission.md`
- `docs/barcode-compiler-methodology.md`
- `docs/nexus-v3/EcoGenesis_Nexus_V3_FULL_PROJECT_RU.md`
- `docs/testing.md`
