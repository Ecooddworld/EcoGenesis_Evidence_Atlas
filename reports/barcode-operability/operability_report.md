# Barcode Compiler Operability Report

Status: **PASS**

## Real Results

| Sequence | Decision | Taxonomic status | Publication | Candidate | Published | Main blockers |
|---|---:|---:|---:|---|---|---|
| AALB-COI-good | species-safe | species-safe | record-ready / record_recommended_ready | Aedes albopictus (species) | Aedes albopictus (species) | none |
| AALB-COI-ambiguous | genus-safe | genus-safe | record-ready / record_recommended_ready | Aedes (genus) | Aedes (genus) | species claim blocked: statistically indistinguishable competitors collapse the safe rank to genus |
| AALB-COI-short | weak | weak | not-ready / record_recommended_ready | Aedes albopictus (species) | None (none) | species claim blocked: top hit does not pass exact match gate identity >= 99% and query coverage >= 80%; species claim blocked: query coverage < 80% |
| AALB-COI-metadata-gap | not-publishable | species-safe | not-ready / record_not_ready | Aedes albopictus (species) | None (none) | publication blocked: missing required Occurrence core field occurrenceID; publication blocked: missing required Occurrence core field eventDate |

## Metrics

```json
{
  "processed_records": 4,
  "processing_coverage": 1,
  "species_safe_records": 1,
  "genus_safe_records": 1,
  "higher_rank_safe_records": 0,
  "ambiguous_records": 0,
  "weak_records": 1,
  "no_match_records": 0,
  "not_publishable_records": 1,
  "record_ready_records": 2,
  "dataset_ready_records": 0,
  "publishable_template_records": 2,
  "safe_rank_records": 2,
  "repairable_records": 3,
  "top_species_hits": 4,
  "blocked_or_downgraded_top_species_hits": 3,
  "species_safe_yield": 0.25,
  "safe_rank_yield": 0.5,
  "molecular_evidence_conversion_yield": 0.5,
  "repairable_yield": 0.75,
  "blocked_species_claims": 3,
  "overclaim_prevention_rate": 0.75,
  "overclaim_prevention_proxy": 1,
  "publication_repair_efficiency": 1.0,
  "hard_gate_failures": 0
}
```

## Checks

- Direct compiler expected classes: `True`
- API expected classes: `True`
- ZIP valid: `True`
- Required exports present: `True`
- HTML report endpoint: `200`
