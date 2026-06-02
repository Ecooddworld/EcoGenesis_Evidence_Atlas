# EcoGenesis Nexus V3 — scientific validation report

Verdict: **PASS**

This validation is an operational reality check, not a claim of universal biological truth. It tests whether the implemented gates prevent the most dangerous publication failure: copying the nearest top-hit species into GBIF when the evidence is ambiguous, weak, unsupported or missing publication metadata.

## Summary

```json
{
  "hard_gate_records": 4,
  "hard_gate_failures": 0,
  "naive_top_species_cases": 3,
  "naive_species_overclaims_prevented": 1,
  "leave_one_out_cases": 3,
  "leave_one_out_false_species_exports": 0,
  "decision_counts": {
    "species_safe": 2,
    "genus_safe": 1,
    "no_match": 1
  },
  "publication_counts": {
    "gbif_ready": 2,
    "repairable_metadata": 2
  }
}
```

## Interpretation

- `hard_gate_failures = 0` means the exported safe-rank decisions obey the internal invariants: no species-safe call without exact-match class, no species-safe call when multiple indistinguishable species remain, and no species-level export from non-species-safe decisions.
- `leave_one_out_false_species_exports = 0` means that, in this reference snapshot, removing the true reference record did not cause the engine to export a different species as if it were safe.
- `naive_species_overclaims_prevented` estimates how many top-hit species labels would have been copied by a naive workflow but were blocked, downgraded or sent to review by EcoGenesis.

## Remaining scientific limits

The prototype still needs external production matchers, frozen reference snapshots, GBIF backbone resolution, real laboratory controls, cross-marker calibration and large benchmark datasets before it can be presented as a production-grade taxonomic assignment service. Its strongest current claim is narrower and defensible: it is a conservative evidence-triage and publication-readiness layer.
