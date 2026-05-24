# Barcode-to-GBIF Evidence Compiler

EcoGenesis is now focused on a narrower, stronger GBIF Challenge tool:

> A deterministic workflow that turns DNA barcode, metabarcoding and Sequence ID results into safe, rank-aware and GBIF-ready molecular occurrence evidence.

The old occurrence Atlas is preserved on branch `oddworld/archive-atlas-score-v1`. The `main` branch now treats the Atlas layer as an audit/export shell around a new molecular decision engine.

## Why This Exists

Many users can produce barcode or metabarcoding results, but still face a hard publication question:

> Which sequences can safely support a species-level occurrence, which must be downgraded to genus or higher rank, and what is missing before the data can become GBIF-ready?

This compiler does not claim absolute biological truth. It produces a reproducible decision under frozen rules, supplied reference-hit metrics, a taxonomy lineage, barcode gap evidence, diagnostic k-mer evidence and GBIF publication metadata.

## Decision Classes

- `species-safe`: exact match, no indistinguishable competitor outside the species, positive barcode gap, diagnostic k-mer support and required GBIF/DNA metadata all pass.
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
-> GBIF Occurrence core metadata
-> DNA-derived metadata
-> publication package
```

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

## Barcode API

- `GET /api/barcode/demo-scenarios`
- `GET /api/barcode/default-request`
- `GET /api/barcode/reference-status`
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

The legacy occurrence-passport API remains available under `/api/evidence/*` for regression and comparison.

## Evidence Pack Artifacts

Each barcode run exports:

- `sequence_safety_table.csv`
- `safe_taxonomic_assignments.csv`
- `ambiguous_sequences.csv`
- `barcode_gap_report.csv`
- `diagnostic_kmer_report.csv`
- `gbif_backbone_matches.csv`
- `publication_blockers.csv`
- `dwc_occurrence_core_template.csv`
- `dna_derived_extension_template.csv`
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
