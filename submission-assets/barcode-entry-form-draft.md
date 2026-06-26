# Barcode-to-GBIF Evidence Compiler Entry Form Copy

Use `submission-assets/gbif-entry-form-draft.md` as the canonical copy-ready form text. This file keeps the shorter project-specific version for quick reference.

## Submission Name

Molecular Evidence Conversion & Repair Engine for GBIF

Short title: Barcode-to-GBIF Evidence Compiler

## One-Liner

A deterministic workflow that turns DNA barcode, metabarcoding and Sequence ID-style outputs into safe, rank-aware and GBIF-ready molecular occurrence evidence.

## Abstract

Barcode-to-GBIF Evidence Compiler receives CSV or JSON results from GBIF Sequence ID, BLAST, BOLD, UNITE or laboratory pipelines and determines whether each molecular record can safely support a species-level occurrence, must be downgraded to genus or higher rank, or is blocked from publication by sequence, reference or metadata gaps.

It applies explicit gates for identity, query coverage, ambiguity, lowest common ancestor, barcode gap, diagnostic k-mer support, false-positive risk and GBIF/DNA-derived publication readiness. It separates taxonomic safety from publication readiness, preventing unsafe species-level overclaims while preserving repairable molecular evidence.

Each run exports an Evidence Pack with sequence safety tables, safe taxonomic assignments, publication blockers, barcode gap and diagnostic k-mer reports, Darwin Core Occurrence templates, DNA-derived extension templates, a molecular evidence report, methods text, citations, an evidence graph, VSEA, theorem checklist, provenance audits and machine-readable JSON/ZIP/Parquet files.

The Nexus V3 + GSEG/GSIG layer adds hard-gate consistency audit, naive top-hit overclaim prevention, reference gap index, metadata bottleneck analysis, repair plan, split GBIF-ready/review exports, graph roundtrip checks and AI output guardrails. The GSIG Observatory adds a source registry, hashed GBIF Aedes Spain snapshots, VSEA-to-graph visualization, OPO proof audits, GBIF export preview and AI-ready export guardrails. This turns the tool into a reproducible publication-repair workflow while keeping unsupported function and phenotype claims blocked.

The tool benefits GBIF data users, publishers, nodes and reviewers by making molecular occurrence evidence more transparent, repeatable and publication-ready.

## Operating Instructions

Hosted demo: https://ecooddworld.eu

```bash
docker compose up --build
```

Open the hosted demo or local http://localhost:13100, go to `Run compiler`, upload one of the CSV examples in `examples/`, review validation, click `Generate from CSV`, inspect the decision table and download `evidence_pack.zip`. Then open `Observatory`, run `Run GBIF-backed Aedes Spain`, inspect source snapshot, VSEA, graph, exports and Judge tabs, and download `observatory_evidence_pack.zip`.

## Required Final Links

- Hosted demo: https://ecooddworld.eu
- Public video URL: paste into the official form after upload
- Source repository URL: https://github.com/Ecooddworld/EcoGenesis_Evidence_Atlas
- `docs/submission.md`
- `docs/barcode-compiler-methodology.md`
- `docs/nexus-v3/EcoGenesis_Nexus_V3_FULL_PROJECT_RU.md`
- `docs/testing.md`
