# EcoGenesis V2 — Barcode-to-GBIF Evidence Compiler

**V2 is the evidence-bounded release:** it replaces overstated proof/validation/GBIF-ready language with explicit run-local rule results, external-validation blockers and locally validated publication candidates. The exact release source is tagged [`v2-evidence-bounded`](https://github.com/Ecooddworld/EcoGenesis_Evidence_Atlas/tree/v2-evidence-bounded).

EcoGenesis is now focused on a narrower, stronger GBIF Challenge tool:

> A deterministic compiler that turns DNA barcode, metabarcoding, Sequence ID and BLAST-like outputs into bounded taxonomic rule results, GBIF validation-candidate checks, repair actions and reproducible Evidence Packs.

The current **Barcode-to-GBIF Evidence Compiler** is the contest-facing molecular decision engine.

## Scientific Boundary

EcoGenesis is a conservative rule-based triage and metadata-repair prototype. It does not independently validate species truth or prove biological presence. The primary scientific state is `species-rule-pass`; the legacy `species-safe` value remains only as a deprecated API compatibility alias. A run can now produce a structurally complete, locally validated DwC-A candidate containing Occurrence Core, the registered DNA-derived extension, `meta.xml` and EML. It is still not a published or externally accepted GBIF dataset until it passes IPT/GBIF validation, organizational review and registration.

## Why This Exists

Many users can produce barcode or metabarcoding results, but still face a hard publication question:

> From a large stream of molecular detections, which records pass species-level rule gates, which must be downgraded to genus or higher rank, which are blocked by reference/library or sequence evidence, and which repair actions unlock the most GBIF validation candidates?

EcoGenesis produces a reproducible decision under frozen rules, supplied reference-hit metrics, taxonomy lineage, barcode gap evidence, diagnostic k-mer evidence and GBIF publication metadata.

## Evidence Conversion Problem

The global task is:

```text
How can a large stream of DNA / metabarcoding results be converted into the
maximum number of safe, reproducible and externally validatable occurrence-record candidates without
manual calibration and without false species-level claims?
```

The engine separates two decisions:

- `scientific_decision_state`: `species-rule-pass`, a conservative genus/higher-rank result, `ambiguous`, `weak`, or `no-match`
- `export_state`: `candidate_for_gbif_validation`, `dwc_template_ready`, `review_only`, or `not_exportable`

This matters because a sequence can pass taxonomic rule gates while still being blocked by missing `occurrenceID`, `eventDate`, workflow metadata or other GBIF validation-candidate fields.

## Decision Classes

- `species-rule-pass`: exact match plus the configured ambiguity/LCA, aligned barcode-gap sampling and CI, diagnostic k-mer, reference-completeness, sequence-QC and assay gates. It is a ruleset result, not species truth.
- `genus-safe`: species-level claim is unsafe, but indistinguishable hits share a genus.
- `higher-rank-safe`: the safe LCA is family or higher.
- `ambiguous`: the evidence cannot support a clear safe rank.
- `weak`: identity or coverage fails the basic match gate.
- `no-match`: no reference hit is available.
- `not-publishable`: taxonomic evidence may be safe, but required GBIF/DNA-derived metadata, assay or quality gates block publication.

## Mathematical Gates

The core flow is:

```text
identity
-> coverage
-> ambiguity / LCA
-> aligned barcode gap + sampling + bootstrap CI
-> conserved canonical diagnostic k-mers + error robustness
-> audited reference completeness
-> ambiguity / complexity / ORF / chimera sequence QC
-> assay controls and replicate semantics
-> diagnostic false-positive probability
-> GBIF Occurrence core metadata
-> DNA-derived metadata
-> publication package
```

The larger engine adds:

- conversion metrics: `MECY`, `RY`, `SRY`, `SSY`, and unsafe top-hit overclaim prevention
- marker profiles: COI full barcode, COI mini-barcode, ITS, 16S short/full and custom-marker fail-closed policies
- assay profiles: single-specimen barcode, metabarcoding/eDNA, qPCR/ddPCR and custom targeted workflows
- repair optimizer: rank actions by how many GBIF validation candidates they unlock
- reference gap index: find taxa/markers/regions where reference libraries block a species-level rule pass
- publisher bottleneck index: separate DNA problems from metadata problems
- coding-marker ORF sanity gate: orientation/frame search and internal stop-codon checks; NUMT/pseudogene inference remains outside the implemented claim scope
- assay evidence gate for eDNA/metabarcoding controls and replicates
- Molecular Evidence Graph linking fragments, taxa, claims and blockers; GBIF geography remains separate run-level context unless real specimen linkage exists
- advanced graph artifacts: rule-evidence segment arrays, release invariant checklist, graph provenance, roundtrip and AI guardrail audits
- Evidence Map layer: source registry, GBIF snapshot hashing, rule-evidence-to-graph visualization, audit checks, GBIF/AI export guardrails and Judge Mode

The frozen gates are documented in:

- `docs/barcode-compiler-methodology.md`
- `docs/proof-by-failure-modes.md`
- `docs/gbif-dna-derived-readiness.md`
- `docs/gseg-gsig-production.md`
- `docs/gsig-observatory.md`
- `docs/production-caddy-deployment.md`
- `docs/nexus-v3/EcoGenesis_Nexus_V3_FULL_PROJECT_RU.md`
- `docs/nexus-v3/EcoGenesis_Nexus_V3_scientific_validation_report.md`

## Quick Start

Live hosted demo:

- Production UI: https://ecooddworld.eu
- Health check: https://ecooddworld.eu/health

Local judge run:

```bash
docker compose up --build
```

Open:

- Frontend: http://localhost:13100
- Backend health: http://localhost:18100/health
- Backend docs: http://localhost:18100/docs

This local stack builds the same compiler runtime used for contest review: the backend image installs **VSEARCH** and **NCBI BLAST+**, bundles the example reference datasets, and stores generated evidence packs in `./data`. The frontend is a static production build served through a single URL with `/api` proxied to the backend inside Docker.

Hosted production deployment uses Caddy:

```bash
export API_AUTH_TOKEN="$(openssl rand -hex 32)"
docker compose -f docker-compose.caddy.yml up -d --build
```

The Caddy stack serves `https://ecooddworld.eu`, redirects HTTP to HTTPS, keeps the backend internal on the Docker network, persists TLS certificates in Docker volumes, and only allows CORS from the HTTPS domain pair. It defaults to authenticated mutations and protected run/export reads; without `API_AUTH_TOKEN` the API fails closed. An interactive public contest demo must deliberately set `API_AUTH_REQUIRED=false`, accepting the documented single-node demo boundary.

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

The smoke test builds the stack on ports `13200/18200`, checks backend health directly and through the frontend proxy, verifies that the Vite production frontend shell and JavaScript asset are served, requires the Docker backend to report `vsearch`, and runs both the mini Aedes reference-search compile path and the shared-fragment graph path through the `/api` proxy.

### Main User Flow

1. Open `Run Compiler`.
2. Upload a CSV exported from GBIF Sequence ID, BLAST, BOLD, UNITE or a lab pipeline.
3. Review the preview and validation summary.
4. Click `Generate from CSV`.
5. Inspect `scientific_decision_state`, rank downgrades, `weak`, `not-publishable` and blocked claims.
6. Download `evidence_pack.zip` or individual CSV/HTML exports.

### Evidence Map Flow

The `Evidence Map` tab runs a small Aedes Spain GBIF-backed snapshot alongside an independent molecular demo. Occurrences are attached only to the run as unlinked context: there is no per-record molecular↔GBIF edge without a shared `eventID`, `materialSampleID`, specimen identifier or dataset lineage. The UI visualizes the separate context, rule-evidence matrix, evidence graph and release checks without implying specimen linkage.

Claim strength remains bounded by molecular gates, publication gates and provenance. The Evidence Map UI, AI-ready dataset and GBIF export preview preserve `claim_state`, caveats and provenance hashes.

1. Open `Evidence Map`.
2. Click `Run judge demo` for the small GBIF path with source mode and any fixture fallback recorded in `snapshot_manifest.json`.
3. Click `Run offline fixture demo` for the deterministic-input judge path. Its self-check records an input fingerprint; it does not claim an independent clean-run reproducibility comparison.
4. Download `observatory_evidence_pack.zip`.

Regenerate the checked-in Evidence Map report pack:

```bash
cd backend
.venv/bin/python scripts/generate_observatory_demo_report.py
```

Generated outputs are written to `reports/observatory-demo/`. The generator also runs the output verifier and writes `observatory_output_verification.json` and `observatory_output_verification.md`.

Recheck an existing report directory without regenerating data:

```bash
cd backend
.venv/bin/python scripts/verify_observatory_outputs.py
```

FASTA-only input can be searched against a selected reference dataset, but it is intentionally not enough for a GBIF validation-candidate publication decision. The compiler needs occurrence metadata supplied by the user, and production publication requires VSEARCH, BLAST+ or an audited external reference workflow rather than the local deterministic mini-search fallback.

### Contest-Safe Source Connections

This project does not rely on the broader EcoGenesis source aggregator for molecular evidence. The barcode compiler accepts and audits these inputs:

- **GBIF Sequence ID / BLAST-style CSV**: export or prepare rows with `sequenceID`, `sequence`, top hit taxon, identity, coverage, lineage and GBIF/DNA metadata.
- **NCBI BLAST / local BLAST+ / VSEARCH**: use the built-in Docker backends or paste/export normalized hit tables into the compiler.
- **BOLD / UNITE / lab pipelines**: use their identification or export tables as external evidence, then preserve source, license, access date and method in the CSV or evidence pack.
- **User FASTA reference datasets**: upload a curated FASTA with headers like `>ref_id|Taxon name|rank|gbifTaxonKey`; the app computes local barcode-gap and diagnostic k-mer evidence.
- **GBIF Backbone enrichment**: uploaded taxon names can be matched to GBIF backbone for lineage/provenance only.
- **GBIF occurrence audit**: available under `/api/evidence/*` for run-level research context, citation and bias checks; it never upgrades a molecular result or creates an unsubstantiated specimen link.

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
6. Inspect the returned hits, the backend used (`vsearch`, `blastn` or `python-local`), segment map, source monitor, claim boundary and generated hard-gate decision dashboard.

For a no-setup real-data check, open `Run Compiler` and use the bundled quick actions:

- `Run real Aedes COI reference check` uses real NCBI GenBank COI accessions to exercise the search and provenance path. Because the small pack has singleton taxon sampling, no external completeness audit and no bootstrap gap CI, it is intentionally review-only and cannot unlock a species-level rule pass.
- `Run conserved Quercus rbcL safe-rank check` uses real NCBI GenBank rbcL accessions and should produce genus-level molecular evidence, because the shared rbcL window cannot safely distinguish `Quercus robur` from `Quercus petraea`.

Uploaded reference datasets are stored under `./data/reference-datasets` in Docker/local runs. During upload, EcoGenesis computes alignment-aware local distances and conserved canonical k-mers, but it does not invent an external completeness audit or barcode-gap bootstrap CI. Uploaded packs therefore remain review-only until those evidence fields are supplied from an audited workflow.

This validates the full sequence search path:

```text
query sequence
-> VSEARCH / BLAST+ / deterministic local mini-search
-> normalized reference hits
-> segment overlap map and source provenance
-> conservative hard-gate compiler
-> safe/blocked claims and Evidence Pack
```

Included reference examples:

- `references/aedes_coi_mini/`: synthetic smoke-test FASTA for deterministic regression.
- `references/ncbi_aedes_coi_small/`: real NCBI GenBank COI records for `Aedes albopictus` and `Aedes aegypti`, with GBIF backbone keys and manifest metadata. This demonstrates search/provenance and the fail-closed singleton/reference-completeness boundary, not species validation.
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

## Evidence Map API

- `GET /api/observatory/status`
- `GET /api/observatory/sources`
- `POST /api/observatory/run-demo`
- `GET /api/observatory/runs`
- `GET /api/observatory/runs/{run_id}`
- `GET /api/observatory/runs/{run_id}/exports`
- `GET /api/observatory/runs/{run_id}/exports/{artifact_name}`
- `GET /api/observatory/snapshots/{snapshot_id}`
- `GET /api/observatory/vsea`
- `GET /api/observatory/segments/{segment_id}`
- `GET /api/observatory/segments/{segment_id}/taxa`
- `GET /api/observatory/segments/{segment_id}/sharedness`
- `GET /api/observatory/segments/{segment_id}/annotations`
- `GET /api/observatory/segments/{segment_id}/publications`
- `GET /api/observatory/segments/{segment_id}/claim-boundary`
- `GET /api/observatory/taxa/{taxon_id}/segments`
- `GET /api/observatory/claims/{claim_id}/provenance`
- `POST /api/observatory/export/gbif`
- `POST /api/observatory/export/ai-ready`
- `GET /api/observatory/runs/{run_id}/verification`
- `GET /api/observatory/runs/{run_id}/verification/report.md`

## Competition Report API

- `GET /api/contest-readiness`
- `GET /api/contest-readiness/report.md`
- `GET /api/competition-reports`
- `GET /api/competition-reports/{report_id}`
- `GET /api/competition-reports/{report_id}/files/{file_name}`

The Docker backend image includes the frozen `competition-100-sequences` and `adversarial-100-sequences` report directories. These are explicitly repeated-fixture regression packs, not 100 independent specimens or empirical validation datasets.
The contest readiness endpoint aggregates backend capability, regression integrity and the latest Evidence Map integrity checks. It remains `review` while independent external validation is absent.

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

The GBIF occurrence-passport API remains available under `/api/evidence/*` for API checks, regression and comparison; live network use is recorded separately from fixture/regression data.

The compiler separates `scientific_decision_state`, legacy compatibility statuses, `candidate_taxon`, `published_taxon` and `export_state`. A weak or blocked sequence can still be useful as a review hint, but it is never placed into the DwC-A candidate as a species. Current packs use explicit `_validation_candidates.csv` names and do not emit the misleading `_gbif_ready.csv` filename aliases.

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
- `math_viability_audit.json`
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
- `dwc_occurrence_core_validation_candidates.csv`
- `dwc_occurrence_core_review.csv`
- `dwc_occurrence_core_review_or_repair.csv`
- `dna_derived_extension_template.csv`
- `dna_derived_extension_publishable.csv`
- `dna_derived_extension_validation_candidates.csv`
- `dwca.zip` (locally validated Occurrence Core + DNA-derived extension + `meta.xml` + EML candidate)
- `dwca_validation_report.json`
- `dwca_roundtrip_contract.json`
- `molecular_evidence_report.html`
- `methods_text.md`
- `citations.md`
- `evidence_graph.json`
- `nexus_v3_summary.json`
- `external_tool_adapter_matrix.csv`
- `proof_by_failure_modes.md`
- `release_invariant_checklist.json`
- `artifact_checksums.json`
- `query_smoke_report.md`
- `ci_math_oracle_report.json`
- `gseg_graph_schema.json`
- `gsig_graph_schema.yaml`
- `evidence_graph.jsonld`
- `rule_evidence_segment_array.csv`
- `rule_evidence_segment_array.jsonl`
- `rule_evidence_segment_array.parquet`
- `segment_canonicalization_audit.csv`
- `segment_cluster_audit.csv`
- `sharedness_overclaim_audit.csv`
- `function_claim_boundary_audit.csv`
- `graph_provenance_audit.csv`
- `ai_output_guardrail_audit.csv`
- `ai_dataset_export_audit.csv`
- `graph_roundtrip_audit.json`
- `vsea_graph_reconciliation.csv`
- `ruleset_diff_report.json`
- `report_consistency_audit.csv`
- `segment_taxon_matrix_audit.csv`
- `judge_reproducibility_report.md`
- `evidence_pack.json`
- `evidence_pack.zip`

Current packs and public file endpoints retire `_gbif_ready.csv`, `theorem_checklist.json` and `verified_segment_evidence_array.*`. Use `_validation_candidates.csv`, `release_invariant_checklist.json` and `rule_evidence_segment_array.*` respectively. Historical report directories may retain old filenames only as traceability records.

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

The built-in API demo also includes a mixed batch, but its scientific evidence is deliberately unsigned: the plausible species candidates stay review-only, alongside a genus downgrade, a weak result and metadata blockers. Trusted species-rule code paths are exercised only in tests and explicitly labelled synthetic report generators.

Prebuilt mixed-batch artifacts live in `reports/barcode-demo/`. Open `reports/barcode-demo/molecular_evidence_report.html` or inspect `reports/barcode-demo/sequence_safety_table.csv`.

Contest batch artifacts live in `reports/competition-100-sequences/` and `reports/adversarial-100-sequences/`. They are regenerated by `backend/scripts/generate_competition_reports.py` and currently contain export bundles per run, including rule-evidence Parquet files, formula-consistency audits, release invariant checklists and graph provenance audits.

## CLI Runner

```bash
cd backend
.venv/bin/python scripts/barcode_compiler_cli.py \
  --demo-id mixed-batch \
  --output-dir ../reports/barcode-demo
```

The CLI writes the same barcode Evidence Pack artifacts as the API.

## Synthetic Regression Stress Test

```bash
cd backend
.venv/bin/python scripts/run_synthetic_ambiguity_benchmark.py \
  --records 120 \
  --output-dir ../reports/synthetic-ambiguity-benchmark
```

This generator is a deterministic stress/regression fixture, not an independent benchmark. Its latest checked-in result is:

```text
Naive top-hit would emit 120 species claims.
EcoGenesis blocked or downgraded 90 unsafe species claims.
EcoGenesis emitted 30 internal species rule-pass fixture results.
Hard-gate failures: 0.
Overclaim prevention rate: 0.75.
```

Those pass-path rows carry the public key id `synthetic-regression-fixture-not-external-trust`. The key is intentionally reproducible and cannot authenticate evidence to a deployment that uses its own operator secret; the result is regression coverage, not external validation.

Regression artifacts:

- `reports/synthetic-ambiguity-benchmark/summary.md`
- `reports/synthetic-ambiguity-benchmark/benchmark_summary.json`
- `reports/synthetic-ambiguity-benchmark/synthetic_ambiguous_dataset.csv`
- `reports/synthetic-ambiguity-benchmark/naive_vs_ecogenesis.csv`
- `reports/synthetic-ambiguity-benchmark/evidence_pack.json`

## Independent Holdout Contract

No independent specimen-backed holdout is checked into this repository, so `scientific_release_gate.status` intentionally remains `blocked`. To inspect the required manifest and record schema:

```bash
cd backend
.venv/bin/python scripts/run_holdout_benchmark.py --print-contract
```

With an externally sourced holdout, the harness rejects ID-only fixture clones and reports Wilson confidence intervals, species precision/recall, genus precision, abstention, false species-rule-pass rate, a naive top-hit baseline, and strata by marker, taxonomic group and reference completeness. Release checks use the confidence bounds, not only point estimates.

Request-supplied audit fields are informational by default. A holdout manifest can unlock the scientific release gate only when the trusted harness and API server share an operator-managed HMAC secret of at least 32 bytes:

```bash
export ECOGENESIS_EVIDENCE_ATTESTATION_SECRET="$(openssl rand -hex 32)"
export ECOGENESIS_EVIDENCE_ATTESTATION_KEY_ID="holdout-auditor-2026-01"
cd backend
.venv/bin/python scripts/run_holdout_benchmark.py \
  --dataset /absolute/path/to/independent-holdout.json \
  --output-dir /absolute/path/to/holdout-report
```

The secret is never accepted as a CLI argument, written to an artifact or supplied through the compiler request. Without it, the harness still writes informational metrics, but emits no attestation and `release_eligible` remains `false`. Attestations are canonical-payload-bound, purpose-separated, ruleset-contract-bound and time-limited; altered payloads, wrong-purpose reuse and expired replays fail closed.

The HMAC establishes which configured audit process issued an unchanged payload; it does not prove that the specimens, labels or audit judgments are scientifically correct. Independent dataset provenance, specimen-backed ground truth and separation from threshold tuning remain mandatory, and no qualifying dataset is bundled here.

Per-record scientific evidence follows the same rule. `status=audited_sufficient`, counts, source and a checksum are not sufficient by themselves: a server-verifiable attestation binds the sequence, exact hit set, reference-completeness inventory, barcode-gap evidence, diagnostic k-mers and chimera/QC evidence. Altering any part blocks scientific use. Built-in demos and CSV examples are deliberately unsigned and therefore remain informational/review-only.

## Operability Verification

```bash
cd backend
.venv/bin/python scripts/verify_barcode_operability.py
```

The verification script runs the compiler and API, checks expected decisions, validates the ZIP bundle and writes:

- `reports/barcode-operability/operability_report.md`
- `reports/barcode-operability/operability_report.json`
- `reports/barcode-operability/browser-v3-reference-search-dashboard.png`

## Evidence Map Output Verification

```bash
cd backend
.venv/bin/python scripts/generate_observatory_demo_report.py
.venv/bin/python scripts/verify_observatory_outputs.py
```

The verifier recomputes SHA256 checksums from the copied report files, checks both Parquet exports for `PAR1`, reconciles CSV row counts with the JSON evidence pack, verifies graph provenance hashes, enforces the visualization/AI/GBIF guardrails and confirms that the ZIP contains the report artifacts listed in `observatory_demo_manifest.csv`. Checksums for `observatory_evidence_pack.json` and `observatory_evidence_pack.zip` are intentionally verified through the external manifest/API, because embedding their final hashes inside the JSON would change the JSON and ZIP themselves.

## Testing

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3.12 -m pytest backend/tests -q
backend/.venv/bin/python backend/scripts/verify_math_viability.py

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
- `submission-assets/contest-video-v3/video/ecogenesis-v2-scientific-walkthrough-en-subs.mp4`
