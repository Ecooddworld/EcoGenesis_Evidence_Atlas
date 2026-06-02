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

## Quick Start

```bash
docker compose up --build
```

Open:

- Frontend: http://localhost:13100
- Backend health: http://localhost:18100/health
- Backend docs: http://localhost:18100/docs

### Main User Flow

1. Open `Run compiler`.
2. Upload a CSV exported from GBIF Sequence ID, BLAST, BOLD, UNITE or a lab pipeline.
3. Review the preview and validation summary.
4. Click `Generate from CSV`.
5. Inspect `species-safe`, `genus-safe`, `weak`, `not-publishable` and blocked claims.
6. Download `evidence_pack.zip` or individual CSV/HTML exports.

FASTA-only input is intentionally not enough for a species-safe decision. The compiler needs supplied match results or reference-hit metrics, because it is a downstream safety and publication-readiness compiler, not a replacement for GBIF Sequence ID.

## Barcode Compiler API

- `GET /api/barcode/demo-scenarios`
- `GET /api/barcode/default-request`
- `GET /api/barcode/reference-status`
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

CSV v1 expects `sequenceID` and `sequence`. Strongly recommended columns include `occurrenceID`, `basisOfRecord`, `scientificName`, `eventDate`, `marker`, `referenceDatabase`, `methodOrSOP`, `topTaxon`, `topIdentity`, `topCoverage`, `topAlignedLength`, optional competitor hit fields, barcode gap fields and pipe-separated `diagnosticKmers`.

The live GBIF occurrence-passport API remains available under `/api/evidence/*` for live API checks, regression and comparison.

The compiler separates `candidate_taxon` from `published_taxon`. A weak or blocked sequence can still be useful as a review hint, but it is never placed into the publishable Darwin Core exports as a species.

## Evidence Pack Artifacts

Each barcode run exports:

- `sequence_safety_table.csv`
- `safe_taxonomic_assignments.csv`
- `review_taxonomic_hints.csv`
- `ambiguous_sequences.csv`
- `barcode_gap_report.csv`
- `diagnostic_kmer_report.csv`
- `gbif_backbone_matches.csv`
- `publication_blockers.csv`
- `reference_manifest.json`
- `dwc_occurrence_core_template.csv`
- `dwc_occurrence_core_publishable.csv`
- `dwc_occurrence_core_review.csv`
- `dna_derived_extension_template.csv`
- `dna_derived_extension_publishable.csv`
- `molecular_evidence_report.html`
- `methods_text.md`
- `citations.md`
- `evidence_graph.json`
- `proof_by_failure_modes.md`
- `evidence_pack.json`
- `evidence_pack.zip`

## Examples

Fixture CSVs live in `examples/`:

- `examples/aedes_good.csv`
- `examples/aedes_ambiguous.csv`
- `examples/aedes_missing_metadata.csv`
- `examples/aedes_weak_coverage.csv`

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

## Operability Verification

```bash
cd backend
.venv/bin/python scripts/verify_barcode_operability.py
```

The verification script runs the compiler and API, checks expected decisions, validates the ZIP bundle and writes:

- `reports/barcode-operability/operability_report.md`
- `reports/barcode-operability/operability_report.json`

## Testing

```bash
cd backend
pytest

cd ../frontend
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
