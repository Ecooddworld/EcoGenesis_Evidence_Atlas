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

| Scenario | Source | GBIF | Records | Datasets | Score | Missing dates | High uncertainty |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| aedes-spain | online | ok | 120 | 4 | 94.69 | 0 | 6 |
| aedes-italy | online | ok | 120 | 3 | 89.17 | 0 | 2 |
| aedes-france | online | ok | 120 | 5 | 94.91 | 0 | 3 |
| quercus-western-europe | online | ok | 120 | 7 | 82.56 | 0 | 0 |
| quercus-germany | online | ok | 120 | 6 | 83.12 | 0 | 0 |
| lynx-iberia | online | ok | 120 | 4 | 85.8 | 0 | 97 |
| apis-western-europe | online | ok | 120 | 4 | 95.08 | 0 | 4 |
| apis-france | online | ok | 120 | 4 | 84.64 | 0 | 3 |
| passer-western-europe | online | ok | 120 | 2 | 66.25 | 0 | 0 |
| passer-united-states | online | ok | 120 | 1 | 95.78 | 0 | 15 |

## Interpretation

The suite supports limited evidence-context claims, weakens claims affected by sampling or metadata bias, blocks absence/distribution/trend overclaims, and marks DOI/citation completion as required verification.
