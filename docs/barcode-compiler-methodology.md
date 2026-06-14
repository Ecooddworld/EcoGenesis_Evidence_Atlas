# Molecular Evidence Conversion & Repair Engine Methodology

## Goal

The current Barcode-to-GBIF Evidence Compiler is the first working layer of the Molecular Evidence Conversion & Repair Engine for GBIF. It determines the maximum safe taxonomic rank for a DNA barcode or metabarcoding result and reports what must be fixed before the record can become GBIF-ready.

It does not prove that a species objectively exists at a site. It proves a narrower, reproducible statement:

```text
Given the supplied sequence, reference-hit metrics, taxonomy lineage, barcode gap,
diagnostic k-mer evidence and metadata, this is the safest candidate rank and publishable rank.
```

The global Evidence Conversion Problem is:

```text
How can a large stream of DNA / metabarcoding results be converted into the
maximum number of safe, reproducible and GBIF-ready occurrence records without
manual calibration and without false species-level claims?
```

The compiler therefore separates:

```text
TaxStatus(r_i) in {speciesSafe, genusSafe, higherRankSafe, ambiguous, weak, noMatch}
PubStatus(r_i) in {gbifReady, repairable, notReady}
```

A record can be taxonomically safe but still repairable or not ready for publication because required GBIF/DNA-derived metadata are missing.

## Inputs

Each sequence record contains:

- `sequence_id`
- `sequence`
- metadata for Darwin Core Occurrence and DNA-derived publication
- reference hits with identity, query coverage, aligned length, rank and lineage
- optional barcode gap evidence
- optional diagnostic k-mer evidence

## Match Type

The compiler uses the GBIF Sequence ID-style gates:

- `exact`: identity >= 99% and queryCoverage >= 80%
- `close`: 90% < identity < 99% and queryCoverage >= 80%
- `weak`: identity < 90% or queryCoverage < 80%
- `no-match`: no reference hit

Species-level output is impossible unless the top hit is `exact`.

## Ambiguity Test

For each hit:

```text
d = 1 - identity
SE = sqrt(d * (1 - d) / aligned_length)
```

A competitor is statistically indistinguishable from the top hit when:

```text
d_competitor - d_top <= 1.96 * sqrt(SE_top^2 + SE_competitor^2)
```

The `candidate_taxon` is the lowest common ancestor of all indistinguishable hits. The `published_taxon` is emitted only when the taxonomic evidence and publication gates allow the record to appear in publishable Darwin Core exports. Weak, ambiguous and metadata-blocked records remain in review exports, but their `published_taxon` is `none`.

## Barcode Gap

For a target taxon:

```text
barcode_gap = inter_min_distance - intra_max_distance
```

Species output requires:

```text
barcode_gap > 0
```

If barcode gap evidence is missing or non-positive, species-level publication is blocked.

## Diagnostic K-Mers

The compiler computes query k-mer support against supplied diagnostic k-mers. If `k` is not supplied:

```text
k = ceil(log4(reference_total_windows / epsilon))
```

The compiler also estimates the chance that at least one diagnostic k-mer support hit could appear by random collision:

```text
p_false_positive = 1 - (1 - diagnostic_kmer_count / 4^k) ^ query_window_count
```

Species output requires:

```text
support_count >= 1
p_false_positive <= alpha
```

The default `alpha` is `0.01`. This prevents a single very common or too-short diagnostic k-mer from unlocking a species claim.

## Publication Readiness

Required Occurrence core fields:

- `occurrenceID`
- `basisOfRecord`
- `scientificName`
- `eventDate`

Required DNA-derived evidence fields:

- `marker`
- `sequenceID`
- `referenceDatabase`
- `identity`
- `queryCoverage`
- `methodOrSOP`

If these are missing, the compiler may still report a taxonomic status such as `species-safe`, but the final decision class becomes `not-publishable`.

Publication stages:

- `record_not_ready`: required Occurrence core or DNA-derived fields are missing or invalid.
- `record_min_ready`: required fields pass, but recommended occurrence fields or dataset metadata are incomplete.
- `record_recommended_ready`: required and recommended record-level fields pass.
- `dataset_ready`: dataset metadata passes, but recommended record-level fields are incomplete.
- `gold_ready`: required fields, recommended fields and dataset metadata all pass.

## Outputs

The main output is an Evidence Pack with:

- sequence safety table with `candidate_taxon`, `published_taxon` and `publication_stage`
- blocked claims
- barcode gap report
- diagnostic k-mer report
- publishable Darwin Core Occurrence and DNA-derived extension templates
- review-only templates for weak, blocked or not-publishable records
- reference manifest
- molecular evidence HTML report
- methods and citations
- machine-readable evidence graph
- GSEG/GSIG proof artifacts: VSEA CSV/JSONL/Parquet, theorem checklist, graph provenance audit, roundtrip audit and AI guardrail audit

## Conversion Metrics

For a batch of molecular observations:

```text
MECY = N_gbifReady / N
RY   = N_repairable / N
SRY  = (N_species + N_genus + N_higher) / N
SSY  = N_species / N
```

Unsafe top-hit species claims are counted as:

```text
UnsafeTopSpecies =
  sum I(topHitRank_i = species AND TaxStatus_i != speciesSafe)

OR_naive = UnsafeTopSpecies / sum I(topHitRank_i = species)
OR_compiler = 0 under the frozen rules
```

The compiler does not make species-level claims when the gates fail, so unsafe top-hit species claims are blocked before export.

## Repair Optimizer Direction

Each record has blockers:

```text
B(r_i) = {b_i1, b_i2, ..., b_ik}
```

Each repair action unlocks a set of records:

```text
Unlock(a) = {r_i : action a removes a blocker for r_i}
```

The future optimizer ranks actions by maximum coverage:

```text
max over A' subset A, |A'| <= k
  | union over a in A' of Unlock(a) |
```

This is how the engine becomes useful to publishers and GBIF nodes: it can say which metadata repairs, reference-library curation tasks or workflow checks unlock the most GBIF-ready records.

## Protein And Assay Guardrails

Protein translation is a future quality-control layer for coding markers, not a species-identification shortcut:

```text
if marker_type != coding:
  amino_acid_layer = not_applicable

Frame* = argmin_f StopCodons(Translate(sequence, f))
pass if InternalStopCount = 0, length(sequence) mod 3 = 0 and FrameshiftRisk = 0
```

The assay layer will track controls, replicates, contamination flags and workflow metadata. The engine should not claim that eDNA proves a living organism is present at a site; it should say that sequence-derived molecular evidence was detected under the supplied sampling and workflow context.

## Molecular Evidence Graph Direction

The current `evidence_graph.json` is the seed for a broader graph:

```text
Fragment -> Taxon / clade -> GBIF occurrence context
Fragment -> Protein motif / domain, when coding and QC passes
Claim -> supported_by evidence
Claim -> blocked_by blocker
```

For a fragment `f`:

```text
T(f) = {taxa where f occurs}
SafeTaxon(f) = LCA(T(f))
```

Shared fragments are not discarded. They become genus-level, family-level or conserved-clade evidence instead of unsafe species claims.
