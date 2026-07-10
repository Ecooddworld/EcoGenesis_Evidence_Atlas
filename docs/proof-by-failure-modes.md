# Failure-Mode Release Invariants

This document describes executable ruleset invariants, not a mathematical proof and not external scientific validation. The compiler is designed to fail closed: a species rule-pass is allowed only if every configured molecular and assay gate passes, and publication eligibility is evaluated separately.

## Species Rule-Pass Invariant

If the compiler outputs primary `scientific_decision_state = species-rule-pass`, then:

- the top hit is an exact match;
- no statistically indistinguishable competitor collapses the safe LCA above species;
- the reference set has a positive barcode gap;
- the query contains diagnostic k-mer support with false-positive probability at or below the configured alpha;
- the marker profile allows species export and aligned-length limits pass;
- audited reference completeness and sequence/chimera QC pass;
- assay and quality gates do not block the scientific state.

The implementation recomputes these conditions in `hard_gate_audit.csv`. A mismatch is a release-blocking software inconsistency. Passing the invariant only shows that the output agrees with the frozen rules; it does not show that the rules are biologically calibrated for a taxon or marker.

At least one failure mode must exist:

- weak or incomplete top hit;
- indistinguishable competitor from another species;
- non-positive barcode gap;
- missing diagnostic signal or high diagnostic false-positive risk;
- marker-profile length/species-export block;
- missing publication metadata or assay/quality block.

Each of those failure modes is an explicit blocker in the code. The primary scientific state must therefore be downgraded or blocked. The legacy `species-safe` value is retained only as a deprecated compatibility token.

## Downgrade Principle

If two or more hits are statistically indistinguishable, the safe taxon is not the top hit. It is the lowest common ancestor of the indistinguishable set.

That means:

```text
Aedes albopictus + Aedes aegypti indistinguishable -> Aedes genus-level rule result
```

## Metadata Separation

Taxonomic evidence and publication readiness are separate. The compiler also separates `candidate_taxon` from `published_taxon`, so review hints never silently become publishable Darwin Core taxa.

Example:

```text
scientific_decision_state = species-rule-pass
decision_class = not-publishable
reason = missing occurrenceID or eventDate
```

This prevents a good sequence match from being treated as a complete GBIF publication record.
