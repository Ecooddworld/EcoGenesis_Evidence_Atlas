# Barcode-to-GBIF Evidence Compiler Methodology

## Goal

The compiler determines the maximum safe taxonomic rank for a DNA barcode or metabarcoding result and reports what must be fixed before the record can become GBIF-ready.

It does not prove that a species objectively exists at a site. It proves a narrower, reproducible statement:

```text
Given the supplied sequence, reference-hit metrics, taxonomy lineage, barcode gap,
diagnostic k-mer evidence and metadata, this is the safest publication rank.
```

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

The safe taxon is the lowest common ancestor of all indistinguishable hits.

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

Species output requires at least one diagnostic k-mer hit in the query sequence.

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

## Outputs

The main output is an Evidence Pack with:

- safe rank table
- blocked claims
- barcode gap report
- diagnostic k-mer report
- Darwin Core Occurrence template
- DNA-derived extension template
- molecular evidence HTML report
- methods and citations
- machine-readable evidence graph
