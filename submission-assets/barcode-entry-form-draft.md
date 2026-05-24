# Barcode-to-GBIF Evidence Compiler Entry Form Draft

## Submission Name

Barcode-to-GBIF Evidence Compiler

## Abstract And Rationale

Barcode-to-GBIF Evidence Compiler is a deterministic workflow that turns DNA barcode, metabarcoding and Sequence ID-style outputs into safe, rank-aware and GBIF-ready molecular occurrence evidence.

The problem is simple: a top sequence hit is not automatically a safe species-level occurrence record. Users must know whether a sequence can support a species claim, whether the evidence should be downgraded to genus or higher rank, and which metadata are missing before publication through GBIF-aligned workflows.

The compiler applies frozen gates for identity, query coverage, statistical ambiguity, lowest common ancestor, barcode gap, diagnostic k-mer support and publication readiness. It outputs clear classes: `species-safe`, `genus-safe`, `higher-rank-safe`, `ambiguous`, `weak`, `no-match` and `not-publishable`.

The Evidence Pack includes CSV tables, Darwin Core Occurrence and DNA-derived templates, a molecular evidence HTML report, methods text, citations and an evidence graph. This helps laboratories, data publishers, GBIF nodes and reviewers prevent unsafe molecular overclaims and repair records before publication.

## Operating Instructions

```bash
docker compose up --build
```

Open http://localhost:13100.

Use `Submission overview` for the short judge explanation. Use `Compiler workbench` to select a demo case or paste a JSON request with sequences, metadata, reference hits, barcode gap evidence and diagnostic k-mers. Click `Generate Evidence Package` and download `evidence_pack.zip`.

## Source And Documentation Links

- Repository README: `README.md`
- Methodology: `docs/barcode-compiler-methodology.md`
- Proof by failure modes: `docs/proof-by-failure-modes.md`
- GBIF DNA-derived readiness: `docs/gbif-dna-derived-readiness.md`
- Testing plan: `docs/testing.md`
