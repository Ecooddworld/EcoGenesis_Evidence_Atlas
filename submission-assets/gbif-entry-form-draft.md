# GBIF Ebbe Nielsen Challenge 2026 Entry Form Copy

Submission deadline: **26 June 2026, 23:59 CEST (UTC+2)**
Official rules: https://www.gbif.org/awards/ebbe-2026-rules
Entry form: https://www.survey-xact.dk/LinkCollector?key=YCAEZQR4SPC1

## Submission Name / Title

Molecular Evidence Conversion & Repair Engine for GBIF

Short title: Barcode-to-GBIF Evidence Compiler

## Team Members and Affiliations

Enter final submitter name, team members, affiliations, country and contact email in the official GBIF form. Personal contact details are not stored in this repository copy.

## Abstract and Rationale

Molecular Evidence Conversion & Repair Engine for GBIF is an open, deterministic workflow that turns DNA barcode, metabarcoding and Sequence ID-style outputs into safe, rank-aware and GBIF-ready molecular occurrence evidence. Its first working module, Barcode-to-GBIF Evidence Compiler, receives CSV or JSON results from tools such as GBIF Sequence ID, BLAST, BOLD, UNITE or a laboratory pipeline, then decides what can be safely claimed, what must be downgraded, and what must be repaired before publication.

The problem is practical and common. Molecular workflows often produce a top taxonomic hit, but a top hit is not automatically a safe species-level occurrence record. A short sequence, weak coverage, ambiguous competitor, missing barcode gap, absent diagnostic k-mer support, incomplete reference evidence or missing metadata can turn an apparently strong species label into an unsafe claim. At the same time, weak or ambiguous molecular observations should not simply be discarded: they can remain useful at genus or higher rank, or as repair tasks for data publishers and GBIF nodes.

The compiler addresses this gap with explicit evidence gates. It checks identity, query coverage, statistical ambiguity between top and competitor hits, lowest common ancestor, barcode gap, diagnostic k-mer support, diagnostic false-positive risk and GBIF/DNA-derived publication metadata. It separates taxonomic safety from publication readiness, so a record can be taxonomically species-safe while still blocked from publication by missing `occurrenceID`, `eventDate`, method/SOP or reference database metadata. This avoids overclaiming while preserving useful evidence.

The output is not a black-box score. Each run produces decision classes such as `species-safe`, `genus-safe`, `higher-rank-safe`, `ambiguous`, `weak`, `no-match` and `not-publishable`. The generated Evidence Pack includes `sequence_safety_table.csv`, `safe_taxonomic_assignments.csv`, `publication_blockers.csv`, `barcode_gap_report.csv`, `diagnostic_kmer_report.csv`, `math_viability_audit.json`, Darwin Core Occurrence templates, DNA-derived extension templates, a molecular evidence HTML report, methods text, citations, an evidence graph, JSON and ZIP exports.

The current Nexus V3 + GSEG/GSIG implementation also adds a hard-gate audit, naive top-hit overclaim report, reference gap index, metadata bottleneck table, repair plan, external tool adapter matrix, split GBIF-ready versus review/repair exports, Verified Segment Evidence Array, theorem checklist, graph provenance audit, graph roundtrip audit and AI output guardrails. The GSIG Observatory adds source-registry audits, hashed GBIF Aedes Spain snapshots, VSEA-to-graph visualization, Observatory proof obligations, GBIF export preview and AI-ready export guardrails. These files make the system useful not only as a classifier, but as a publication repair and evidence-conversion engine. Unsupported function, phenotype and production GraphDB/RDF claims remain explicitly blocked rather than implied.

For data users, the tool answers: “Can I safely use this molecular detection as a species-level occurrence, or should I downgrade or review it?” For data publishers, it gives concrete repair actions such as adding required metadata, improving sequence coverage or attaching reference-set evidence. For GBIF nodes and reviewers, it provides a reproducible audit trail that separates supported claims from blocked claims and keeps publication templates aligned with GBIF-ready data practices.

The project uses GBIF in two complementary ways. The molecular compiler is designed as a downstream safety layer for GBIF Sequence ID-style or BLAST-style results and for DNA-derived publication workflows. The repository also includes a GBIF occurrence-audit layer that tests API access when live network mode is enabled, uses GBIF-mediated occurrence data for evidence-context checks, and demonstrates safe claim language around no-evidence cells, sampling gaps and citation readiness. The system does not claim species absence, true distribution, trend or phenotype truth from occurrence points or molecular matches alone.

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

The Docker stack is the recommended judge-facing run path. It builds the frontend as static production assets, serves them with Nginx, proxies `/api` to the backend service, installs VSEARCH and NCBI BLAST+ in the backend image, and bundles the example reference dataset required for the reference-search workflow.

### Main UI Flow

1. Open `Run compiler`.
2. Upload a CSV exported from GBIF Sequence ID, BLAST, BOLD, UNITE or a laboratory pipeline.
3. Use `Download CSV template` if you need the expected format.
4. Review CSV preview and validation warnings.
5. Click `Generate from CSV`.
6. Inspect the decision dashboard, sequence table, safe/blocked claims and repair actions.
7. Download `evidence_pack.zip` or individual CSV/HTML exports.
8. Open `Observatory`, run `Run GBIF-backed Aedes Spain`, inspect source snapshot, VSEA, graph, exports and Judge tabs, then download `observatory_evidence_pack.zip`.

For sequence-search validation rather than CSV scoring, use the `Reference search` panel. Judges can upload a small curated FASTA reference dataset with headers like `>ref_id|Taxon name|rank|gbifTaxonKey`, select it in the dropdown, paste a query sequence, and run VSEARCH/BLAST+/fallback search through the same hard-gate compiler.

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

- Backend: `79 passed, 1 skipped`
- Math viability verifier: `pass`, `142 checks`, `0 failed`
- Frontend: `14 passed`
- Frontend build: passes
- Contest readiness API: `pass`, 17 checks, 0 failed
- Competition packs: two frozen 100-sequence reports pass with theorem and graph roundtrip checks
- Observatory verifier: passes with zero failed checks
- GBIF API status: checked when live network mode is enabled

## Video URL

Upload the final CSV Upload -> Score demo video to YouTube, Vimeo, Google Drive, Figshare, OSF or another public no-cost location, then paste that URL into the official GBIF form.

Local final video file prepared for upload:

`submission-assets/barcode-video/video/ecogenesis-barcode-to-gbif-english-voice-ru-subs.mp4`

Russian subtitles and English transcript are included in the same folder. Important: the older local MP4 in `submission-assets/video/` demonstrates the previous Evidence Atlas flow; do not use it as the final submission video.

## Source and Submission Documentation Links

- Repository: https://github.com/oddworld666/EcoGenesis_Evidence_Atlas
- Main README: https://github.com/oddworld666/EcoGenesis_Evidence_Atlas/blob/main/README.md
- Submission documentation: https://github.com/oddworld666/EcoGenesis_Evidence_Atlas/blob/main/docs/submission.md
- Methodology: https://github.com/oddworld666/EcoGenesis_Evidence_Atlas/blob/main/docs/barcode-compiler-methodology.md
- Nexus V3 full project: https://github.com/oddworld666/EcoGenesis_Evidence_Atlas/blob/main/docs/nexus-v3/EcoGenesis_Nexus_V3_FULL_PROJECT_RU.md
- Proof by failure modes: https://github.com/oddworld666/EcoGenesis_Evidence_Atlas/blob/main/docs/proof-by-failure-modes.md
- GBIF DNA-derived readiness: https://github.com/oddworld666/EcoGenesis_Evidence_Atlas/blob/main/docs/gbif-dna-derived-readiness.md
- Testing: https://github.com/oddworld666/EcoGenesis_Evidence_Atlas/blob/main/docs/testing.md
- Final submission pack: https://github.com/oddworld666/EcoGenesis_Evidence_Atlas/blob/main/submission-assets/gbif-2026-final-submission-pack.md

## Notes Before Final Form Submission

- Confirm the GitHub repository visibility follows the final contest review path.
- Confirm all public URLs work without login.
- Enter team details only in the official form or an approved private submission document.
- Paste the public video URL into the official form after upload.
- Create a GitHub release, for example `v1.0-gbif-2026`.
- Do not submit local file paths as the only evidence.
