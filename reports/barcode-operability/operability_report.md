# Barcode Compiler Operability Report

Status: **PASS**

## Real Results

| Sequence | Decision | Taxonomic status | Publication | Export state | Candidate | Published | Main blockers |
|---|---:|---:|---:|---:|---|---|---|
| AALB-COI-good | ambiguous | ambiguous | not-ready / record_recommended_ready / repair_required | review_only | Aedes albopictus (species) | None (none) | species claim blocked: reference completeness attestation blocked scientific use: unsigned; species claim blocked: reference completeness failed: server_attestation_verified |
| AALB-COI-ambiguous | genus-safe | genus-safe | record-ready / record_recommended_ready / publishable_candidate | dwc_template_ready | Aedes (genus) | Aedes (genus) | species claim blocked: statistically indistinguishable competitors collapse the safe rank to genus; species claim blocked: reference completeness attestation blocked scientific use: unsigned |
| AALB-COI-short | weak | weak | not-ready / record_recommended_ready / repair_required | review_only | Aedes albopictus (species) | None (none) | species claim blocked: top hit does not pass coi_full_barcode exact gate identity >= 99% and query coverage >= 80%; species claim blocked: query coverage < 80% |
| AALB-COI-metadata-gap | ambiguous | ambiguous | not-ready / record_not_ready / repair_required | review_only | Aedes albopictus (species) | None (none) | species claim blocked: reference completeness attestation blocked scientific use: unsigned; species claim blocked: reference completeness failed: server_attestation_verified |

## Metrics

```json
{
  "processed_records": 4,
  "input_records": 4,
  "eligible_records": 4,
  "candidate_records": 4,
  "safe_records": 1,
  "processing_coverage": 1,
  "species_safe_records": 0,
  "species_rule_pass_records": 0,
  "genus_safe_records": 1,
  "higher_rank_safe_records": 0,
  "ambiguous_records": 2,
  "weak_records": 1,
  "no_match_records": 0,
  "not_publishable_records": 0,
  "record_ready_records": 1,
  "dataset_ready_records": 0,
  "publishable_template_records": 1,
  "validation_candidate_records": 0,
  "gbif_ready_records": 0,
  "publishable_candidate_records": 1,
  "repair_required_records": 3,
  "review_only_records": 0,
  "safe_rank_records": 1,
  "repairable_records": 4,
  "top_species_hits": 4,
  "blocked_or_downgraded_top_species_hits": 4,
  "species_safe_yield": 0.0,
  "safe_rank_yield": 0.25,
  "molecular_evidence_conversion_yield": 0.25,
  "repairable_yield": 1.0,
  "blocked_species_claims": 4,
  "overclaim_prevention_rate": 1.0,
  "overclaim_prevention_proxy": 1,
  "publication_repair_efficiency": 1.0,
  "hard_gate_failures": 0,
  "assay_gate_failures": 0,
  "dna_extension_ready_records": 0,
  "marker_species_disabled_records": 0
}
```

## Checks

- Direct compiler expected classes: `True`
- API expected classes: `True`
- ZIP valid: `True`
- Required exports present: `True`
- HTML report endpoint: `200`
