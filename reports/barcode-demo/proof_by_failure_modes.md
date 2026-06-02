# Proof By Failure Modes

The compiler blocks species-level claims when any required gate fails:

- identity below 99% or coverage below 80%;
- statistically indistinguishable competitor collapses the safe taxon to genus or higher;
- barcode gap is missing or non-positive;
- diagnostic k-mer support is missing, zero or above the configured false-positive probability threshold;
- marker profile disallows species export for the supplied marker/span;
- qPCR/ddPCR required assay evidence is missing;
- required Occurrence core or DNA-derived metadata is missing.

Therefore `species-safe` is not a blind top-hit label. It means the record passed all frozen molecular evidence and GBIF-readiness gates in this run.

## Nexus V3 Hard-Gate Audit

The `hard_gate_audit.csv` export verifies the contradiction condition explicitly:

If a record is emitted as `species-safe`, then the marker exact-match gate, ambiguity/LCA gate, barcode gap gate, diagnostic k-mer gate, marker profile gate, Occurrence core gate, DNA metadata gate and assay gate must all pass.

If any of those gates fail while `species-safe` is emitted, `hardGateViolation=true`. A valid run must have zero hard-gate failures.
