# Scientific Hypothesis Suite Report

This live suite tests whether EcoGenesis can convert GBIF-mediated occurrence data into safe scientific hypotheses.

## Acceptance

- minimum_1000_deduplicated_records: `True`
- minimum_10_successful_online_scenarios: `True`
- no_fixture_records_counted: `True`
- minimum_100_hypothesis_claims: `True`
- every_claim_has_status_evidence_and_caveat: `True`

## Totals

- Deduplicated live GBIF records: `1000`
- Successful online scenarios: `10`
- Hypothesis claims: `100`
- Duplicate records skipped: `149`
- Claim status counts: `{"blocked": 20, "requires_verification": 20, "supported": 48, "weak": 12}`

## Scenario Metrics

| Scenario | Source | GBIF | Downloaded | Deduped | Datasets | Top dataset share | Score | Missing dates | High uncertainty |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| aedes-spain | online | ok | 120 | 120 | 4 | 0.8417 | 94.69 | 0 | 6 |
| aedes-italy | online | ok | 120 | 120 | 3 | 0.75 | 89.17 | 0 | 2 |
| aedes-france | online | ok | 120 | 77 | 5 | 0.6167 | 94.91 | 0 | 3 |
| quercus-western-europe | online | ok | 120 | 120 | 7 | 0.3667 | 82.56 | 0 | 0 |
| quercus-germany | online | ok | 120 | 75 | 6 | 0.5667 | 83.12 | 0 | 0 |
| lynx-iberia | online | ok | 120 | 120 | 4 | 0.8083 | 85.8 | 0 | 97 |
| apis-western-europe | online | ok | 120 | 120 | 4 | 0.4917 | 95.08 | 0 | 4 |
| apis-france | online | ok | 120 | 59 | 4 | 0.6167 | 84.64 | 0 | 3 |
| passer-western-europe | online | ok | 120 | 120 | 2 | 0.95 | 66.25 | 0 | 0 |
| passer-united-states | online | ok | 120 | 120 | 1 | 1.0 | 95.78 | 0 | 15 |

## Interpretation

The suite supports limited evidence-context claims, weakens claims affected by sampling or metadata bias, blocks absence/distribution/trend overclaims, and marks DOI/citation completion as required verification.
