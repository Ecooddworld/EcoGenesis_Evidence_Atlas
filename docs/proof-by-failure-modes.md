# Proof By Failure Modes

The compiler is designed to fail closed. A published species-level claim is allowed only if every species and required publication gate passes.

## Species-Safe Theorem

If the compiler outputs final `decision_class = species-safe`, then:

- the top hit is an exact match;
- no statistically indistinguishable competitor collapses the safe LCA above species;
- the reference set has a positive barcode gap;
- the query contains diagnostic k-mer support with false-positive probability at or below the configured alpha;
- the marker profile allows species export and aligned-length limits pass;
- required Occurrence core and DNA-derived metadata are present;
- assay and quality gates do not block publication.

Assume the compiler outputs final `decision_class = species-safe`, but the species claim is unsafe within the supplied reference context.

At least one failure mode must exist:

- weak or incomplete top hit;
- indistinguishable competitor from another species;
- non-positive barcode gap;
- missing diagnostic signal or high diagnostic false-positive risk;
- marker-profile length/species-export block;
- missing publication metadata or assay/quality block.

Each of those failure modes is an explicit blocker in the code. Therefore the compiler could not have emitted `species-safe`. Contradiction.

## Downgrade Principle

If two or more hits are statistically indistinguishable, the safe taxon is not the top hit. It is the lowest common ancestor of the indistinguishable set.

That means:

```text
Aedes albopictus + Aedes aegypti indistinguishable -> Aedes genus-safe
```

## Metadata Separation

Taxonomic evidence and publication readiness are separate. The compiler also separates `candidate_taxon` from `published_taxon`, so review hints never silently become publishable Darwin Core taxa.

Example:

```text
taxonomic_status = species-safe
decision_class = not-publishable
reason = missing occurrenceID or eventDate
```

This prevents a good sequence match from being treated as a complete GBIF publication record.
