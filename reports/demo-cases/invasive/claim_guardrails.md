# Claim Guardrails

## Supported Claims

- GBIF-mediated records matching the selected taxon and region are present in the evidence pack.
- Dataset provenance is preserved through datasetKey-level contribution summaries.

## Weak Claims

- Record clusters can indicate areas of observation activity, but they may also reflect observer effort.
- The selected-purpose readiness score is 97.7/100 and should be interpreted with the component scores.

## Unsupported Claims

- Absence cannot be inferred from empty or low-evidence grid cells.
- Observed GBIF distribution must not be treated as the true species distribution.
- Population trend cannot be inferred without temporal sampling-bias correction.

## Required Verification

- Create a DOI-backed GBIF occurrence download or derived dataset before formal publication.
- Inspect high coordinate-uncertainty records before using them in fine-scale decisions.
- Treat undersampled occupied cells as survey priorities, not confirmed absences.
