# Barcode Compiler Operability Report

Status: **PASS**

## Real Results

| Sequence | Decision | Taxonomic status | Publication status | Safe taxon | Main blockers |
|---|---:|---:|---:|---|---|
| AALB-COI-good | species-safe | species-safe | gbif-ready | Aedes albopictus (species) | none |
| AALB-COI-ambiguous | genus-safe | genus-safe | gbif-ready | Aedes (genus) | species claim blocked: statistically indistinguishable competitors collapse the safe rank to genus |
| AALB-COI-short | weak | weak | not-ready | Aedes albopictus (species) | species claim blocked: top hit does not pass exact match gate identity >= 99% and query coverage >= 80%; species claim blocked: query coverage < 80% |
| AALB-COI-metadata-gap | not-publishable | species-safe | not-ready | Aedes albopictus (species) | publication blocked: missing required Occurrence core field occurrenceID; publication blocked: missing required Occurrence core field eventDate |

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
  "species_safe_yield": 0.25,
  "blocked_species_claims": 3,
  "overclaim_prevention_proxy": 1,
  "publication_repair_efficiency": 1.0
}
```

## Checks

- Direct compiler expected classes: `True`
- API expected classes: `True`
- ZIP valid: `True`
- Required exports present: `True`
- HTML report endpoint: `200`
