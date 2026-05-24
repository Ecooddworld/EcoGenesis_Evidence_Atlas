# Barcode-to-GBIF Evidence Compiler Submission Kit

## Submission Name

Barcode-to-GBIF Evidence Compiler

## Core Idea

The project turns DNA barcode, metabarcoding or Sequence ID outputs into safe, rank-aware and GBIF-ready molecular occurrence evidence.

Instead of a broad Atlas score, the tool answers:

> Can this sequence safely support a species-level occurrence, must it be downgraded, or is it blocked from publication?

## Contest Fit

The 2026 GBIF Ebbe Nielsen Challenge accepts tools, workflows and analyses that improve the access, utility or quality of GBIF-mediated data. The compiler improves quality and utility by preventing unsafe species overclaims, making molecular publication blockers explicit and generating reusable GBIF-ready templates.

The official submission requires a written description, operating instructions, source/documentation links and a video showing inputs, process and outputs. This repository now contains the code, tests, examples, methodology and demo cases for that package.

## What The Tool Produces

- sequence safety table
- safe taxonomic assignments
- ambiguous sequence table
- barcode gap report
- diagnostic k-mer report
- publication blockers
- Darwin Core Occurrence template
- DNA-derived extension template
- molecular evidence HTML report
- methods text
- citations
- evidence graph
- zipped Evidence Pack

## Demo Flow

1. Open the app.
2. Show the `Submission overview`.
3. Click `Run mixed demo`.
4. Show the sequence table:
   - `species-safe`
   - `genus-safe`
   - `weak`
   - `not-publishable`
5. Open the Evidence Pack export list.
6. Download `evidence_pack.zip`.
7. Explain that this is a downstream compiler for GBIF Sequence ID-style outputs, not a replacement for GBIF Sequence ID.

## Operating Instructions

```bash
docker compose up --build
```

Open:

- http://localhost:13100
- http://localhost:18100/docs

Run tests:

```bash
cd backend
pytest

cd ../frontend
npm test
npm run build
```

## Legacy Atlas

The older occurrence Evidence Atlas has been preserved on branch `oddworld/archive-atlas-score-v1`. The legacy `/api/evidence/*` endpoints remain in `main` for regression and comparison, but the primary submission narrative is now Barcode-to-GBIF Evidence Compiler.
