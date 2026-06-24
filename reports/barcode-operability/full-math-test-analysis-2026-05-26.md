# Full Math Notebook And Test Analysis - 2026-05-26

## What Was Added

The `Proof & formulas` page now exposes the project as a complete mathematical workflow, not a short formula summary.

It includes:

- complete input contract: `r_i = (s_i, H_i, T_i, M_i, R_i, A_i)`
- compiler output contract: `tau_safe`, `tax_status`, `pub_status`, blockers, actions and exports
- identity and coverage gates
- ambiguity boundary and LCA downgrade
- barcode gap
- diagnostic k-mers with `p_false_positive`
- reference completeness gate
- protein sanity gate for coding markers
- assay evidence gate for eDNA/metabarcoding
- publication readiness
- two-axis taxonomic/publication decision function
- batch decomposition and loss accounting
- conversion metrics: `MECY`, `RY`, `SRY`, `SSY`, `OR_naive`, `OR_compiler`
- repair optimizer
- reference gap and publisher bottleneck indices
- fragment sharedness and specificity
- geography-as-context caveat
- multi-marker consensus
- Molecular Evidence Graph

## What The Current Tests Prove

The tests prove that the current implementation behaves fail-closed. They do not prove absolute biological truth.

Current solved behavior:

- unsafe top-hit species claims are blocked before publishable export
- ambiguous species matches can be downgraded to genus
- short or incomplete fragments are classified as `weak`
- taxonomic safety is separated from publication readiness
- metadata gaps keep otherwise useful records out of publishable exports
- evidence packs are generated with CSV, JSON, HTML, Darwin Core, DNA-derived templates, methods and citations
- GBIF occurrence API integration works with explicit fixture-fallback state

## Mixed Batch Result

| Record | Decision | Published output | Meaning |
|---|---|---|---|
| `AALB-COI-good` | `species-safe` | `Aedes albopictus` / species | All species gates and publication fields passed. |
| `AALB-COI-ambiguous` | `genus-safe` | `Aedes` / genus | Indistinguishable competitors collapsed the safe rank to genus. |
| `AALB-COI-short` | `weak` | review only | Coverage below 80% blocked the species-level claim. |
| `AALB-COI-metadata-gap` | `not-publishable` | review only | Taxonomy was species-safe, but `occurrenceID` and `eventDate` were missing. |

## Verification Status

- Frontend unit tests: `3 passed`
- Frontend production build: passed
- Backend pytest: `23 passed, 1 skipped`
- Barcode operability script: `PASS`
- Browser smoke: `0` console errors, `20` math notebook sections, no horizontal overflow
- GBIF-backed Observatory smoke: `ok`, `taxonKey=1651430`, source mode recorded in `snapshot_manifest.json`; fixture fallback is explicit when used

## What Is Specified But Not Fully Implemented Yet

- Reference Completeness Gate
- Protein Sanity Gate
- Assay Evidence Gate
- Repair Optimizer
- Reference Gap Dashboard
- Publisher Bottleneck Dashboard
- Fragment Sharedness Explorer
- Multi-marker consensus

These are now written as explicit formulas and UI-facing proof requirements, so the next development step is implementation rather than conceptual design.
