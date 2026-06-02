# GBIF 2026 Submission Documentation

## Submission Name

Molecular Evidence Conversion & Repair Engine for GBIF

Working module: **Barcode-to-GBIF Evidence Compiler**

## Core Idea

The project turns DNA barcode, metabarcoding and Sequence ID-style outputs into safe, rank-aware and GBIF-ready molecular occurrence evidence.

It does not try to guess species from DNA in a black-box way. It answers:

> Can this molecular record safely support a species-level occurrence, must it be downgraded to genus or higher rank, or is it blocked from publication until evidence or metadata are repaired?

## Contest Fit

The 2026 GBIF Ebbe Nielsen Challenge accepts tools, workflows and analyses that improve the access, utility or quality of GBIF-mediated data. This compiler improves quality and utility by:

- preventing unsafe species-level overclaims from top-hit molecular matches;
- preserving ambiguous evidence at the safest supported taxonomic rank;
- separating taxonomic safety from GBIF publication readiness;
- exposing repair actions for publishers and data managers;
- producing repeatable CSV, HTML, JSON and ZIP Evidence Packs.

## What The Tool Produces

Each run produces:

- `sequence_safety_table.csv`
- `safe_taxonomic_assignments.csv`
- `review_taxonomic_hints.csv`
- `ambiguous_sequences.csv`
- `barcode_gap_report.csv`
- `diagnostic_kmer_report.csv`
- `gbif_backbone_matches.csv`
- `publication_blockers.csv`
- `dwc_occurrence_core_template.csv`
- `dwc_occurrence_core_publishable.csv`
- `dwc_occurrence_core_review.csv`
- `dna_derived_extension_template.csv`
- `dna_derived_extension_publishable.csv`
- `molecular_evidence_report.html`
- `methods_text.md`
- `citations.md`
- `evidence_graph.json`
- `evidence_pack.json`
- `evidence_pack.zip`

## Demo Flow For Judges

1. Open the app at http://localhost:13100.
2. Open `Run compiler`.
3. Upload `examples/aedes_good.csv`.
4. Show CSV preview and validation summary.
5. Click `Generate from CSV`.
6. Show `species-safe` decision and Evidence Pack exports.
7. Upload or explain `examples/aedes_ambiguous.csv` to show downgrade to `genus-safe`.
8. Upload or explain `examples/aedes_missing_metadata.csv` to show taxonomic evidence preserved while publication is blocked.
9. Open `Math & proof` to show the deterministic gates.
10. Open `Research audit` to show the live GBIF occurrence-audit layer and 100 evidence claims.

## Operating Instructions

```bash
docker compose up --build
```

Open:

- Frontend: http://localhost:13100
- Backend API docs: http://localhost:18100/docs

Run tests:

```bash
cd backend
.venv/bin/python -m pytest -q

cd ../frontend
npm test -- --run
npm run build
```

Run barcode operability verification:

```bash
cd backend
.venv/bin/python scripts/verify_barcode_operability.py
```

Run optional live GBIF occurrence-audit suite:

```bash
cd backend
.venv/bin/python scripts/run_scientific_hypothesis_suite.py --fresh --output-dir /tmp/ecogenesis-scientific-theory-suite
```

## Scope Boundaries

The compiler is a downstream safety and publication-readiness layer for Sequence ID / BLAST-style outputs. It does not replace GBIF Sequence ID and does not infer species from FASTA-only input.

The project does not claim:

- species absence from empty cells;
- true species distribution from GBIF occurrence points alone;
- population trends without a trend model and sampling-bias correction;
- phenotype truth from barcode evidence.

## Submission Assets

- Entry form draft: `submission-assets/gbif-entry-form-draft.md`
- Final checklist: `submission-assets/final-submission-checklist.md`
- Video script: `submission-assets/barcode-video-script.md`
- Final pack: `submission-assets/gbif-2026-final-submission-pack.md`
