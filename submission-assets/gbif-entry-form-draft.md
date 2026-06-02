# GBIF Ebbe Nielsen Challenge 2026 Entry Form Draft

Submission deadline: **26 June 2026, 23:59 CEST (UTC+2)**
Official rules: https://www.gbif.org/awards/ebbe-2026-rules
Entry form: https://www.survey-xact.dk/LinkCollector?key=YCAEZQR4SPC1

## Submission Name / Title

Molecular Evidence Conversion & Repair Engine for GBIF

Short title: Barcode-to-GBIF Evidence Compiler

## Team Members and Affiliations

TODO: Add final submitter name, team members, affiliations, country and contact email.

## Abstract and Rationale

Molecular Evidence Conversion & Repair Engine for GBIF is an open, deterministic workflow that turns DNA barcode, metabarcoding and Sequence ID-style outputs into safe, rank-aware and GBIF-ready molecular occurrence evidence. Its first working module, Barcode-to-GBIF Evidence Compiler, receives CSV or JSON results from tools such as GBIF Sequence ID, BLAST, BOLD, UNITE or a laboratory pipeline, then decides what can be safely claimed, what must be downgraded, and what must be repaired before publication.

The problem is practical and common. Molecular workflows often produce a top taxonomic hit, but a top hit is not automatically a safe species-level occurrence record. A short sequence, weak coverage, ambiguous competitor, missing barcode gap, absent diagnostic k-mer support, incomplete reference evidence or missing metadata can turn an apparently strong species label into an unsafe claim. At the same time, weak or ambiguous molecular observations should not simply be discarded: they can remain useful at genus or higher rank, or as repair tasks for data publishers and GBIF nodes.

The compiler addresses this gap with explicit evidence gates. It checks identity, query coverage, statistical ambiguity between top and competitor hits, lowest common ancestor, barcode gap, diagnostic k-mer support, diagnostic false-positive risk and GBIF/DNA-derived publication metadata. It separates taxonomic safety from publication readiness, so a record can be taxonomically species-safe while still blocked from publication by missing `occurrenceID`, `eventDate`, method/SOP or reference database metadata. This avoids overclaiming while preserving useful evidence.

The output is not a black-box score. Each run produces decision classes such as `species-safe`, `genus-safe`, `higher-rank-safe`, `ambiguous`, `weak`, `no-match` and `not-publishable`. The generated Evidence Pack includes `sequence_safety_table.csv`, `safe_taxonomic_assignments.csv`, `publication_blockers.csv`, `barcode_gap_report.csv`, `diagnostic_kmer_report.csv`, Darwin Core Occurrence templates, DNA-derived extension templates, a molecular evidence HTML report, methods text, citations, an evidence graph, JSON and ZIP exports.

For data users, the tool answers: “Can I safely use this molecular detection as a species-level occurrence, or should I downgrade or review it?” For data publishers, it gives concrete repair actions such as adding required metadata, improving sequence coverage or attaching reference-set evidence. For GBIF nodes and reviewers, it provides a reproducible audit trail that separates supported claims from blocked claims and keeps publication templates aligned with GBIF-ready data practices.

The project uses GBIF in two complementary ways. The molecular compiler is designed as a downstream safety layer for GBIF Sequence ID-style or BLAST-style results and for DNA-derived publication workflows. The repository also includes a live GBIF occurrence audit layer that tests GBIF API access, uses GBIF-mediated occurrence data for evidence-context checks, and demonstrates safe claim language around no-evidence cells, sampling gaps and citation readiness. The system does not claim species absence, true distribution, trend or phenotype truth from occurrence points or molecular matches alone.

This submission matters to the GBIF community because it improves the utility and quality of biodiversity data before publication and reuse. It helps prevent unsafe species-level claims, keeps ambiguous molecular evidence usable at safe rank, makes blockers repairable, and creates transparent, repeatable evidence packages that judges, reviewers, publishers and future users can inspect at no cost.

## Operating Instructions

### Run with Docker

```bash
docker compose up --build
```

Open:

- Frontend: http://localhost:13100
- Backend health: http://localhost:18100/health
- Backend API docs: http://localhost:18100/docs

### Main UI Flow

1. Open `Run compiler`.
2. Upload a CSV exported from GBIF Sequence ID, BLAST, BOLD, UNITE or a laboratory pipeline.
3. Use `Download CSV template` if you need the expected format.
4. Review CSV preview and validation warnings.
5. Click `Generate from CSV`.
6. Inspect the decision dashboard, sequence table, safe/blocked claims and repair actions.
7. Download `evidence_pack.zip` or individual CSV/HTML exports.

### Example CSV Runs

The repository includes four small CSV examples:

- `examples/aedes_good.csv` -> `species-safe`
- `examples/aedes_ambiguous.csv` -> `genus-safe`
- `examples/aedes_missing_metadata.csv` -> taxonomic evidence preserved, publication blocked
- `examples/aedes_weak_coverage.csv` -> `weak`

### Local Development

```bash
cd backend
.venv/bin/python -m pytest -q
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 18100
```

In a second terminal:

```bash
cd frontend
npm install
npm test -- --run
npm run dev -- --host 127.0.0.1 --port 13100
```

### Verification

```bash
cd backend
.venv/bin/python scripts/verify_barcode_operability.py
.venv/bin/python scripts/run_scientific_hypothesis_suite.py --fresh --output-dir /tmp/ecogenesis-scientific-theory-suite
```

Expected current regression status:

- Backend: `35 passed, 1 skipped`
- Frontend: `5 passed`
- Frontend build: passes
- GBIF API status: `ok` when the GBIF API is reachable
- Live scientific suite: at least 1,000 deduplicated GBIF occurrence records and 100 evidence claims when network access is available

## Video URL

TODO: Upload the final CSV Upload -> Score demo video to YouTube, Vimeo, Google Drive, Figshare, OSF or another public no-cost location and paste the public URL here.

Local final video file prepared for upload:

`submission-assets/barcode-video/video/ecogenesis-barcode-to-gbif-english-voice-ru-subs.mp4`

Russian subtitles and English transcript are included in the same folder. Important: the older local MP4 in `submission-assets/video/` demonstrates the previous Evidence Atlas flow; do not use it as the final submission video.

## Source and Submission Documentation Links

- Repository: https://github.com/oddworld666/EcoGenesis_Evidence_Atlas
- Main README: https://github.com/oddworld666/EcoGenesis_Evidence_Atlas/blob/main/README.md
- Submission documentation: https://github.com/oddworld666/EcoGenesis_Evidence_Atlas/blob/main/docs/submission.md
- Methodology: https://github.com/oddworld666/EcoGenesis_Evidence_Atlas/blob/main/docs/barcode-compiler-methodology.md
- Proof by failure modes: https://github.com/oddworld666/EcoGenesis_Evidence_Atlas/blob/main/docs/proof-by-failure-modes.md
- GBIF DNA-derived readiness: https://github.com/oddworld666/EcoGenesis_Evidence_Atlas/blob/main/docs/gbif-dna-derived-readiness.md
- Testing: https://github.com/oddworld666/EcoGenesis_Evidence_Atlas/blob/main/docs/testing.md
- Final submission pack: https://github.com/oddworld666/EcoGenesis_Evidence_Atlas/blob/main/submission-assets/gbif-2026-final-submission-pack.md

## Notes Before Final Form Submission

- Confirm the GitHub repository is public.
- Confirm all public URLs work without login.
- Replace the TODO team details.
- Replace the TODO video URL.
- Create a GitHub release, for example `v1.0-gbif-2026`.
- Do not submit local file paths as the only evidence.
