# Molecular Evidence Conversion & Repair Engine for GBIF

EcoGenesis is now focused on a narrower, stronger GBIF Challenge tool:

> A deterministic engine that turns DNA barcode, metabarcoding and Sequence ID results into safe, rank-aware, repairable and GBIF-ready molecular occurrence evidence.

The current **Barcode-to-GBIF Evidence Compiler** is the first working layer of this engine. The old occurrence Atlas is preserved on branch `oddworld/archive-atlas-score-v1`. The `main` branch now treats the Atlas layer as an audit/export shell around a new molecular decision engine.

## Why This Exists

Many users can produce barcode or metabarcoding results, but still face a hard publication question:

> From a large stream of molecular detections, which records can safely support a species-level occurrence, which must be downgraded to genus or higher rank, which are blocked by reference/library or sequence evidence, and which repair actions unlock the most GBIF-ready records?

This compiler does not claim absolute biological truth. It produces a reproducible decision under frozen rules, supplied reference-hit metrics, a taxonomy lineage, barcode gap evidence, diagnostic k-mer evidence and GBIF publication metadata.

## Evidence Conversion Problem

The global task is not "guess the species from DNA". It is:

```text
How can a large stream of DNA / metabarcoding results be converted into the
maximum number of safe, reproducible and GBIF-ready occurrence records without
manual calibration and without false species-level claims?
```

The engine separates two decisions:

- `TaxStatus`: `speciesSafe`, `genusSafe`, `higherRankSafe`, `ambiguous`, `weak`, `noMatch`
- `PubStatus`: `gbifReady`, `repairable`, `notReady`

This matters because a sequence can be taxonomically safe while still blocked by missing `occurrenceID`, `eventDate`, workflow metadata or other GBIF-ready publication fields.

## Decision Classes

- `species-safe`: exact match, no indistinguishable competitor outside the species, positive barcode gap, diagnostic k-mer support with low false-positive probability and required GBIF/DNA metadata all pass.
- `genus-safe`: species-level claim is unsafe, but indistinguishable hits share a genus.
- `higher-rank-safe`: the safe LCA is family or higher.
- `ambiguous`: the evidence cannot support a clear safe rank.
- `weak`: identity or coverage fails the basic match gate.
- `no-match`: no reference hit is available.
- `not-publishable`: taxonomic evidence may be safe, but required GBIF/DNA-derived metadata is missing.

## Mathematical Gates

The core flow is:

```text
identity
-> coverage
-> ambiguity / LCA
-> barcode gap
-> diagnostic k-mers
-> diagnostic false-positive probability
-> GBIF Occurrence core metadata
-> DNA-derived metadata
-> publication package
```

The larger engine adds:

- conversion metrics: `MECY`, `RY`, `SRY`, `SSY`, and unsafe top-hit overclaim prevention
- marker profiles: COI full barcode, COI mini-barcode, ITS, 16S short/full and custom-marker fail-closed policies
- assay profiles: single-specimen barcode, metabarcoding/eDNA, qPCR/ddPCR and custom targeted workflows
- repair optimizer: rank actions by how many GBIF-ready records they unlock
- reference gap index: find taxa/markers/regions where reference libraries block species-safe conversion
- publisher bottleneck index: separate DNA problems from metadata problems
- protein sanity layer for coding markers: frame, stop codon, frameshift and pseudogene/NUMT warnings
- assay evidence gate for eDNA/metabarcoding controls and replicates
- Molecular Evidence Graph linking fragments, taxa, GBIF geography, protein context, claims and blockers

The frozen gates are documented in:

- `docs/barcode-compiler-methodology.md`
- `docs/proof-by-failure-modes.md`
- `docs/gbif-dna-derived-readiness.md`
- `docs/nexus-v3/EcoGenesis_Nexus_V3_FULL_PROJECT_RU.md`
- `docs/nexus-v3/EcoGenesis_Nexus_V3_scientific_validation_report.md`

## Quick Start

```bash
docker compose up --build
```

Open:

- Frontend: http://localhost:13100
- Backend health: http://localhost:18100/health
- Backend docs: http://localhost:18100/docs

This is the contest-facing production stack: the backend image installs **VSEARCH** and **NCBI BLAST+**, bundles the example reference datasets, and stores generated evidence packs in `./data`. The frontend is a static production build served by Nginx; `/api` is proxied to the backend inside Docker, so the UI works from one URL.

The legacy V3 compose file is kept as an alias for older instructions:

```bash
docker compose -f docker-compose.v3.yml up --build
```

Local development can still run without Docker or without those binaries; `/api/barcode/search-status` will report `python-local` as a degraded but deterministic mini-search backend for tests and small reference examples. The Docker stack should report `vsearch` or `blastn` as the preferred external backend.

To avoid port conflicts with an already running local dev server:

```bash
FRONTEND_PORT=13200 BACKEND_PORT=18200 docker compose up --build
```

Automated Docker smoke test:

```bash
scripts/docker_smoke.sh
```

The smoke test builds the stack on ports `13200/18200`, checks backend health directly and through the frontend proxy, verifies that the Vite/Nginx frontend shell and JavaScript asset are served, requires the Docker backend to report `vsearch`, and runs both the mini Aedes reference-search compile path and the shared-fragment graph path through the Nginx `/api` proxy.

### Main User Flow

1. Open `Run compiler`.
2. Upload a CSV exported from GBIF Sequence ID, BLAST, BOLD, UNITE or a lab pipeline.
3. Review the preview and validation summary.
4. Click `Generate from CSV`.
5. Inspect `species-safe`, `genus-safe`, `weak`, `not-publishable` and blocked claims.
6. Download `evidence_pack.zip` or individual CSV/HTML exports.

FASTA-only input can be searched against a selected reference dataset, but it is intentionally not enough for a GBIF-ready publication decision. The compiler needs occurrence metadata supplied by the user, and production publication requires VSEARCH, BLAST+ or an audited external reference workflow rather than the local deterministic mini-search fallback.

### Contest-Safe Source Connections

This project does not rely on the broader EcoGenesis source aggregator for molecular evidence. The barcode compiler accepts and audits these inputs:

- **GBIF Sequence ID / BLAST-style CSV**: export or prepare rows with `sequenceID`, `sequence`, top hit taxon, identity, coverage, lineage and GBIF/DNA metadata.
- **NCBI BLAST / local BLAST+ / VSEARCH**: use the built-in Docker backends or paste/export normalized hit tables into the compiler.
- **BOLD / UNITE / lab pipelines**: use their identification or export tables as external evidence, then preserve source, license, access date and method in the CSV or evidence pack.
- **User FASTA reference datasets**: upload a curated FASTA with headers like `>ref_id|Taxon name|rank|gbifTaxonKey`; the app computes local barcode-gap and diagnostic k-mer evidence.
- **GBIF Backbone enrichment**: uploaded taxon names can be matched to GBIF backbone for lineage/provenance only.
- **GBIF occurrence audit**: available under `/api/evidence/*` for research context, citation and bias checks; it never upgrades a weak molecular hit into a species-safe barcode claim.

Manual connection links:

- GBIF Sequence ID: https://www.gbif.org/tools/sequence-id
- GBIF DNA-derived publishing guide: https://docs.gbif.org/publishing-dna-derived-data/en/
- NCBI nucleotide BLAST: https://blast.ncbi.nlm.nih.gov/Blast.cgi?PAGE_TYPE=BlastSearch&PROGRAM=blastn
- BOLD v5 ID Engine: https://id.boldsystems.org/
- UNITE: https://unite.ut.ee/

### Reference Search Flow

The Workbench also has a `Reference search` panel. It supports both bundled reference examples and user-uploaded FASTA reference datasets.

1. Optional: upload a curated FASTA in `Bring your own reference FASTA`.
2. Use FASTA headers like `>ref_id|Taxon name|rank|gbifTaxonKey` or `>ref_id Taxon name`.
3. Select the uploaded dataset or `EcoGenesis mini COI reference dataset for Aedes smoke tests`.
4. Paste a barcode sequence.
5. Click `Search reference & compile`.
6. Inspect the returned hits, the backend used (`vsearch`, `blastn` or `python-local`), segment map, source monitor, claim boundary and generated Nexus V3 decision dashboard.

For a no-setup real-data check, open `Run compiler` and use the bundled quick actions:

- `Run real Aedes COI species-safe check` uses real NCBI GenBank COI accessions and should produce species-level molecular evidence for `Aedes albopictus` when the marker separates the taxa. If the runtime falls back to `python-local` or occurrence metadata is missing, the taxonomic status can be `species-safe` while the publication decision remains `not-publishable`.
- `Run conserved Quercus rbcL safe-rank check` uses real NCBI GenBank rbcL accessions and should produce genus-level molecular evidence, because the shared rbcL window cannot safely distinguish `Quercus robur` from `Quercus petraea`.

Uploaded reference datasets are stored under `./data/reference-datasets` in Docker/local runs. During upload, EcoGenesis computes lightweight barcode-gap and diagnostic k-mer evidence from the supplied FASTA so the same hard gates are used as in CSV scoring. This is still a pre-publication safety workflow: large production studies should use curated, versioned reference libraries and preserve licenses, source URLs and access dates.

This validates the full sequence search path:

```text
query sequence
-> VSEARCH / BLAST+ / deterministic local mini-search
-> normalized reference hits
-> segment overlap map and source provenance
-> Nexus V3 hard-gate compiler
-> safe/blocked claims and Evidence Pack
```

Included reference examples:

- `references/aedes_coi_mini/`: synthetic smoke-test FASTA for deterministic regression.
- `references/ncbi_aedes_coi_small/`: real NCBI GenBank COI records for `Aedes albopictus` and `Aedes aegypti`, with GBIF backbone keys and manifest metadata. This demonstrates the real-data species-level molecular-evidence path when the marker separates the taxa.
- `references/ncbi_quercus_rbcl_small/`: real NCBI GenBank rbcL records for `Quercus robur` and `Quercus petraea`, cropped to a shared overlapping rbcL window. This intentionally demonstrates safe-rank downgrade: a conserved marker window can support `Quercus` genus evidence but must not become a species-level claim.

These packs are reproducible workflow examples, not replacements for curated production reference databases.

For uploaded FASTA reference datasets, EcoGenesis tries to enrich taxon names against the GBIF backbone via `/species/match`. If GBIF is unavailable or the match confidence is low, upload still succeeds with a deterministic header-derived lineage and a warning in `manifest.json`. Set `GBIF_BACKBONE_ENRICH_UPLOADS=false` to disable this live enrichment in offline test environments.

## Barcode Compiler API

- `GET /api/barcode/demo-scenarios`
- `GET /api/barcode/default-request`
- `GET /api/barcode/reference-status`
- `GET /api/barcode/search-status`
- `GET /api/barcode/reference-datasets`
- `POST /api/barcode/reference-datasets/upload`
- `POST /api/barcode/search`
- `POST /api/barcode/fragment-graph`
- `GET /api/barcode/csv-template`
- `POST /api/barcode/import-csv`
- `POST /api/barcode/run-csv`
- `POST /api/barcode/run`
- `GET /api/barcode/runs`
- `GET /api/barcode/runs/{run_id}`
- `GET /api/barcode/runs/{run_id}/report`
- `GET /api/barcode/runs/{run_id}/exports`
- `GET /api/barcode/runs/{run_id}/exports/{artifact_name}`

Minimal request shape:

```json
{
  "project_title": "Aedes albopictus COI publication check",
  "marker": "COI-5P",
  "reference_database": "COI Animals / BOLD public clustered reference",
  "method_or_sop": "GBIF Sequence ID-compatible BLAST workflow with deterministic rank gates",
  "records": [
    {
      "sequence_id": "AALB-COI-good",
      "sequence": "ACGTTGACCTAGGCT...",
      "metadata": {
        "occurrenceID": "urn:example:1",
        "basisOfRecord": "MaterialSample",
        "scientificName": "Aedes albopictus",
        "eventDate": "2026-04-18",
        "methodOrSOP": "GBIF Sequence ID-compatible COI workflow"
      },
      "hits": [
        {
          "taxon": "Aedes albopictus",
          "rank": "species",
          "identity": 99.6,
          "query_coverage": 96,
          "aligned_length": 658,
          "lineage": [
            {"rank": "family", "name": "Culicidae"},
            {"rank": "genus", "name": "Aedes"},
            {"rank": "species", "name": "Aedes albopictus", "taxon_key": 1651430}
          ]
        }
      ],
      "barcode_gap": {"intra_max_distance": 0.009, "inter_min_distance": 0.018},
      "diagnostic": {
        "diagnostic_kmers": ["ACGTTGACCTAGGCT"],
        "reference_total_windows": 5000000,
        "epsilon": 0.01
      }
    }
  ]
}
```

CSV v1 expects `sequenceID` and `sequence`. Strongly recommended columns include `occurrenceID`, `eventID`, `materialSampleID`, `basisOfRecord`, `scientificName`, `eventDate`, `marker`, `assayType`, `referenceDatabase`, `methodOrSOP`, `topTaxon`, `topIdentity`, `topCoverage`, `topAlignedLength`, optional competitor hit fields, barcode gap fields and pipe-separated `diagnosticKmers`.

Long-format hit tables are also accepted: repeated `sequenceID` rows with columns such as `hitTaxon`, `hitIdentity`, `hitCoverage`, `hitRank`, `hitAlignedLength`, `hitReferenceId`, `taxon`, `identity`, `queryCoverage` or BLAST-style aliases are grouped into one sequence record with multiple reference hits.

For stronger DNA-derived publication review, the CSV can also include `target_gene`, `target_subfragment`, `pcr_primer_forward`, `pcr_primer_reverse`, `seq_meth`, `contaminationAssessment`, `occurrenceStatus`, `experimentalVariance`, `quantificationCycle`, `estimatedNumberOfCopies`, `readCount` and `totalReads`.

The live GBIF occurrence-passport API remains available under `/api/evidence/*` for live API checks, regression and comparison.

The compiler separates `taxonomic_status`, `decision_class`, `candidate_taxon`, `published_taxon` and `publication_bucket`. A weak or blocked sequence can still be useful as a review hint, but it is never placed into publishable Darwin Core exports as a species. `dwc_occurrence_core_publishable.csv` contains safe publishable candidates; `dwc_occurrence_core_gbif_ready.csv` is stricter and only contains rows whose `publication_bucket` is `gbif_ready`.

## Evidence Pack Artifacts

Each barcode run exports:

- `sequence_safety_table.csv`
- `data_accounting_ledger.csv`
- `state_machine_audit.csv`
- `claim_boundaries.csv`
- `segment_overlap_report.csv`
- `safe_taxonomic_assignments.csv`
- `review_taxonomic_hints.csv`
- `ambiguous_sequences.csv`
- `barcode_gap_report.csv`
- `diagnostic_kmer_report.csv`
- `gbif_backbone_matches.csv`
- `publication_blockers.csv`
- `repair_plan.csv`
- `metadata_bottlenecks.csv`
- `reference_gap_index.csv`
- `reference_completeness_audit.csv`
- `marker_profile_audit.csv`
- `assay_gate_audit.csv`
- `dna_extension_readiness.csv`
- `repair_gain_estimates.csv`
- `hard_gate_audit.csv`
- `naive_top_hit_overclaims.csv`
- `reference_manifest.json`
- `source_provenance_manifest.json`
- `dwc_occurrence_core_template.csv`
- `dwc_occurrence_core_publishable.csv`
- `dwc_occurrence_core_gbif_ready.csv`
- `dwc_occurrence_core_review.csv`
- `dwc_occurrence_core_review_or_repair.csv`
- `dna_derived_extension_template.csv`
- `dna_derived_extension_publishable.csv`
- `dna_derived_extension_gbif_ready.csv`
- `molecular_evidence_report.html`
- `methods_text.md`
- `citations.md`
- `evidence_graph.json`
- `nexus_v3_summary.json`
- `external_tool_adapter_matrix.csv`
- `proof_by_failure_modes.md`
- `evidence_pack.json`
- `evidence_pack.zip`

## Examples

Fixture CSVs live in `examples/`:

- `examples/aedes_good.csv`
- `examples/aedes_ambiguous.csv`
- `examples/aedes_missing_metadata.csv`
- `examples/aedes_weak_coverage.csv`
- `examples/aedes_search_query.fasta`

Reference dataset example:

- `references/aedes_coi_mini/aedes_coi_mini.fasta`
- `references/aedes_coi_mini/manifest.json`

The built-in API demo also includes a mixed batch with species-safe, genus-safe, weak and metadata-blocked records.

Prebuilt mixed-batch artifacts live in `reports/barcode-demo/`. Open `reports/barcode-demo/molecular_evidence_report.html` or inspect `reports/barcode-demo/sequence_safety_table.csv`.

## CLI Runner

```bash
cd backend
.venv/bin/python scripts/barcode_compiler_cli.py \
  --demo-id mixed-batch \
  --output-dir ../reports/barcode-demo
```

The CLI writes the same barcode Evidence Pack artifacts as the API.

## Synthetic Ambiguous Benchmark

```bash
cd backend
.venv/bin/python scripts/run_synthetic_ambiguity_benchmark.py \
  --records 120 \
  --output-dir ../reports/synthetic-ambiguity-benchmark
```

Latest benchmark result:

```text
Naive top-hit would emit 120 species claims.
EcoGenesis blocked or downgraded 90 unsafe species claims.
EcoGenesis emitted 30 species-safe claims.
Hard-gate failures: 0.
Overclaim prevention rate: 0.75.
```

Benchmark artifacts:

- `reports/synthetic-ambiguity-benchmark/summary.md`
- `reports/synthetic-ambiguity-benchmark/benchmark_summary.json`
- `reports/synthetic-ambiguity-benchmark/synthetic_ambiguous_dataset.csv`
- `reports/synthetic-ambiguity-benchmark/naive_vs_ecogenesis.csv`
- `reports/synthetic-ambiguity-benchmark/evidence_pack.json`

## Operability Verification

```bash
cd backend
.venv/bin/python scripts/verify_barcode_operability.py
```

The verification script runs the compiler and API, checks expected decisions, validates the ZIP bundle and writes:

- `reports/barcode-operability/operability_report.md`
- `reports/barcode-operability/operability_report.json`
- `reports/barcode-operability/browser-v3-reference-search-dashboard.png`

## Testing

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3.12 -m pytest backend/tests -q

cd frontend
npm test
npm run build
```

## Official GBIF Context

- GBIF Sequence ID: https://www.gbif.org/tools/sequence-id
- Publishing DNA-derived data through biodiversity data platforms: https://docs.gbif.org/publishing-dna-derived-data/en/
- Occurrence dataset quality requirements: https://www.gbif.org/data-quality-requirements-occurrences
- 2026 GBIF Ebbe Nielsen Challenge rules: https://www.gbif.org/awards/ebbe-2026-rules

## 2026 GBIF Challenge Submission

Submission deadline: **26 June 2026, 23:59 CEST (UTC+2)**.

Prepared submission materials live in `submission-assets/`, especially:

- `submission-assets/gbif-2026-final-submission-pack.md`
- `submission-assets/gbif-entry-form-draft.md`
- `submission-assets/barcode-video-script.md`
- `submission-assets/final-submission-checklist.md`
- `submission-assets/barcode-video/video/ecogenesis-barcode-to-gbif-english-voice-ru-subs.mp4`
