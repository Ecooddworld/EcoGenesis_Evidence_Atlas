# Molecular Evidence Conversion & Repair Engine Methodology

## Goal

The current Barcode-to-GBIF Evidence Compiler is the first working layer of the Molecular Evidence Conversion & Repair Engine for GBIF. It computes a bounded taxonomic rule result and reports what must be fixed before a record can become a candidate for external GBIF/IPT validation.

It does not prove that a species objectively exists at a site. It makes a narrower, reproducible statement:

```text
Given the supplied sequence, reference-hit metrics, taxonomy lineage, audited reference
evidence, sequence/assay QC and metadata, this is the ruleset-supported candidate rank
and the most conservative export state.
```

The global Evidence Conversion Problem is:

```text
How can a large stream of DNA / metabarcoding results be converted into the
maximum number of bounded, reproducible and externally validatable occurrence candidates without
manual calibration and without false species-level claims?
```

The compiler therefore separates:

```text
ScientificState(r_i) in {species-rule-pass, genus/higher-rank result, ambiguous, weak, no-match}
ExportState(r_i) in {candidate_for_gbif_validation, dwc_template_ready, review_only, not_exportable}
```

A record can be taxonomically safe but still repairable or not ready for publication because required GBIF/DNA-derived metadata are missing.

## Inputs

Each sequence record contains:

- `sequence_id`
- `sequence`
- metadata for Darwin Core Occurrence and DNA-derived publication
- reference hits with identity, query coverage, aligned length, rank and lineage
- barcode-gap sampling, alignment method, bootstrap and confidence-bound evidence
- conserved diagnostic k-mer evidence and its negative-universe scope
- explicit reference-completeness audit
- sequence/chimera QC evidence and assay controls where applicable

## Match Type

The compiler stores `identity` and `queryCoverage` as API/export percentages in `[0, 100]`.
The formulas below use normalized fractions:

```text
p_identity = identity / 100
p_coverage = queryCoverage / 100
```

The compiler uses the GBIF Sequence ID-style gates:

- `exact`: identity >= 99% and queryCoverage >= 80%
- `close`: 90% < identity < 99% and queryCoverage >= 80%
- `weak`: identity < 90% or queryCoverage < 80%
- `no-match`: no reference hit

Species-level output is impossible unless the top hit is `exact`.

## Ambiguity Test

For each hit:

```text
p_identity = identity / 100
d = 1 - p_identity
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

Species rule-pass output requires all of the following:

```text
barcode_gap > 0
target reference specimens >= 3
represented close-relative taxa >= 2
minimum aligned sites >= 80
bootstrap replicates >= 200
gap confidence interval lower bound > 0
```

Singleton taxa, unaligned distances and missing uncertainty evidence fail closed.

## Trusted Reference Completeness

Reference counts and `status=audited_sufficient` arrive through an untrusted request boundary and are therefore informational until verified. Species rule-pass requires a time-bounded HMAC-SHA256 attestation issued by a trusted server-side audit process. The canonical attestation payload binds the exact `sequence_id`, sequence SHA-256, reference-hit-set SHA-256 and candidate-species count together with the completeness inventory, barcode-gap values, diagnostic k-mers and chimera/QC evidence. Missing secrets, unsigned evidence, altered bundle fields, invalid signatures, wrong-purpose reuse and expired attestations all produce `gate_pass=false`.

The secret is supplied only through `ECOGENESIS_EVIDENCE_ATTESTATION_SECRET` (minimum 32 bytes); there is no repository or production fallback secret. `ECOGENESIS_EVIDENCE_ATTESTATION_KEY_ID` identifies the configured trust key without exposing it.

## Diagnostic K-Mers

The compiler computes query k-mer support against supplied diagnostic k-mers. If `k` is not supplied:

```text
k = ceil(log4(reference_total_windows / epsilon))
```

The compiler also estimates the chance that at least one diagnostic k-mer support hit could appear by random collision:

```text
p_false_positive = 1 - (1 - diagnostic_kmer_count / 4^k) ^ query_window_count
```

Species rule-pass output requires:

```text
support_count >= 2
p_false_positive <= alpha
target sequences >= 3
negative taxa >= 2
negative sequences >= 6
within-target conservation >= 0.95
reverse-complement canonicalization attested
at least one support remains under the exhaustive single-position substitution-loss bound
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

If publication metadata are missing, molecular evidence can remain visible while the final decision class becomes `not-publishable` and `published_taxon` remains `none`. If required metabarcoding/qPCR assay evidence is missing or semantically invalid, the primary scientific state is assay-blocked rather than `species-rule-pass`.

Publication stages:

- `record_not_ready`: required Occurrence core or DNA-derived fields are missing or invalid.
- `record_min_ready`: required fields pass, but recommended occurrence fields or dataset metadata are incomplete.
- `record_recommended_ready`: required and recommended record-level fields pass.
- `dataset_ready`: dataset metadata passes, but recommended record-level fields are incomplete.
- `gold_ready`: required fields, recommended fields and dataset metadata all pass.

The important state-machine rule is:

```text
ScientificState(s) can preserve a molecular candidate while DecisionClass(s, M) is not-publishable.
published_taxon is emitted only when the safe taxonomic status and required publication gates both pass.
```

## Outputs

The main output is an Evidence Pack with:

- sequence safety table with `candidate_taxon`, `published_taxon` and `publication_stage`
- blocked claims
- barcode gap report
- diagnostic k-mer report
- secondary formula-consistency audit that reconciles formulas with generated decisions
- Darwin Core Occurrence and DNA-derived review templates
- a deterministic DwC-A candidate with Occurrence Core, registered DNA-derived extension, `meta.xml`, EML and local semantic/roundtrip validation when eligible rows and dataset metadata exist
- an explicit external IPT/GBIF release blocker that local validation cannot clear
- review-only templates for weak, blocked or not-publishable records
- reference manifest
- molecular evidence HTML report
- methods and citations
- machine-readable evidence graph
- GSEG/GSIG rule-evidence artifacts: rule-evidence CSV/JSONL/Parquet, release invariant checklist, graph provenance audit, roundtrip audit and AI guardrail audit

## Conversion Metrics

For a batch of molecular observations:

```text
MECY = N_validationCandidate / N
RY   = N_repairable / N
SRY  = (N_species + N_genus + N_higher) / N
SSY  = N_species / N
```

Unsafe top-hit species claims are counted as:

```text
UnsafeTopSpecies =
  sum I(topHitRank_i = species AND ScientificState_i != species-rule-pass)

OR_naive = UnsafeTopSpecies / sum I(topHitRank_i = species)
OR_compiler is measured only on an independent labelled holdout
```

Repeated fixtures check fail-closed code paths but do not estimate real-world error. Scientific release remains blocked until the external holdout contract passes Wilson confidence-bound, naive-baseline and stratified checks.

The external manifest is not trusted merely because those fields are present. The independent harness computes the dataset checksum and metrics, binds them to the ruleset scientific-gate contract, and emits a canonical HMAC-SHA256 attestation only when an operator-managed secret is configured. The API independently verifies the payload hash, signature, key id, purpose and validity window. Unsigned or unverifiable manifests remain visible as informational evidence but cannot set `release_eligible=true`.

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

This is how the engine becomes useful to publishers and GBIF nodes: it can say which metadata repairs, reference-library curation tasks or workflow checks unlock the most GBIF validation candidates.

## Protein And Assay Guardrails

Coding-marker ORF QC is implemented as a bounded quality gate, not a species-identification shortcut:

```text
if marker_type != coding:
  amino_acid_layer = not_applicable

Frame* = argmin_f StopCodons(Translate(sequence, f))
pass if a sufficiently long frame in either orientation has no internal stop codon
```

The assay layer semantically checks required controls, replicates, contamination, qPCR/ddPCR inhibition, LoD/LoQ, amplification efficiency and non-detect interpretation. It still cannot prove that eDNA represents a living organism at a site.

## Molecular Evidence Graph Direction

The current `evidence_graph.json` is the seed for a broader graph:

```text
Fragment -> Taxon / clade candidate
Claim -> supported_by evidence
Claim -> blocked_by blocker
```

GBIF occurrences remain separate run-level context unless a real shared event, material sample, specimen identifier or lineage establishes a record-level link. Protein/domain annotation remains a blocked roadmap claim.

For a fragment `f`:

```text
T(f) = {taxa where f occurs}
SafeTaxon(f) = LCA(T(f))
```

Shared fragments are not discarded. They become genus-level, family-level or conserved-clade evidence instead of unsafe species claims.
