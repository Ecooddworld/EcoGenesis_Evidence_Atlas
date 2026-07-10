# Failure-Mode Invariants

The compiler blocks species-level claims when any required gate fails:

- identity or coverage below the selected marker profile threshold;
- statistically indistinguishable competitor collapses the safe taxon to genus or higher;
- barcode gap is missing or non-positive;
- diagnostic k-mer support is missing, zero or above the configured false-positive probability threshold;
- marker profile disallows species export for the supplied marker/span;
- qPCR/ddPCR or eDNA/metabarcoding required assay evidence is missing;
- required Occurrence core or DNA-derived metadata is missing.

Therefore `species-rule-pass` is not a blind top-hit label and not an external validation result. It means the record passed the current molecular and assay rules in this run.

## Nexus V3 Hard-Gate Audit

The `hard_gate_audit.csv` export verifies the contradiction condition explicitly:

If a record is emitted with primary state `species-rule-pass`, then the marker exact-match gate, ambiguity/LCA gate, barcode gap gate, diagnostic k-mer gate, reference-completeness gate, sequence-QC gate, marker profile gate and assay gate must all pass. Publication metadata is checked separately.

If any required gate fails while a final species rule-pass publication decision is emitted, `hardGateViolation=true`. A valid run must have zero hard-gate failures.

These checks demonstrate internal rule consistency. They do not prove that the thresholds are biologically calibrated for every taxon, marker, laboratory workflow or reference database.
