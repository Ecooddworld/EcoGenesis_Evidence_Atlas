# Proof By Failure Modes

The compiler is designed to fail closed. A species-level claim is allowed only if every species gate passes.

## Species-Safe Theorem

If the compiler outputs `species-safe`, then:

- the top hit is an exact match;
- no statistically indistinguishable competitor collapses the safe LCA above species;
- the reference set has a positive barcode gap;
- the query contains diagnostic k-mer support;
- required Occurrence core and DNA-derived metadata are present.

Assume the compiler outputs `species-safe`, but the species claim is unsafe within the supplied reference context.

At least one failure mode must exist:

- weak or incomplete top hit;
- indistinguishable competitor from another species;
- non-positive barcode gap;
- missing diagnostic signal;
- missing publication metadata.

Each of those failure modes is an explicit blocker in the code. Therefore the compiler could not have emitted `species-safe`. Contradiction.

## Downgrade Principle

If two or more hits are statistically indistinguishable, the safe taxon is not the top hit. It is the lowest common ancestor of the indistinguishable set.

That means:

```text
Aedes albopictus + Aedes aegypti indistinguishable -> Aedes genus-safe
```

## Metadata Separation

Taxonomic evidence and publication readiness are separate.

Example:

```text
taxonomic_status = species-safe
decision_class = not-publishable
reason = missing occurrenceID or eventDate
```

This prevents a good sequence match from being treated as a complete GBIF publication record.
