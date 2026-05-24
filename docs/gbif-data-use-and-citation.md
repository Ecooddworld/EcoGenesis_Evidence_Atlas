# GBIF Data Use and Citation

Barcode-to-GBIF Evidence Compiler helps users preserve the information needed for responsible GBIF-aligned molecular evidence publication. The legacy occurrence Atlas citation flow is preserved on the archive branch and in `/api/evidence/*`, but the current `main` submission focuses on barcode/metabarcoding evidence.

## What The Current Compiler Preserves

- `sequenceID`
- sequence MD5
- marker and reference database
- identity and query coverage
- GBIF taxon keys when supplied by reference hits
- accepted safe rank and decision class
- barcode gap evidence
- diagnostic k-mer support
- Occurrence core publication blockers
- DNA-derived metadata blockers
- Darwin Core and DNA-derived export templates
- evidence graph links between run, sequence, hits, assignments and artifacts

## Legacy Occurrence Atlas Preserves

- `datasetKey`
- record counts per dataset
- license values when present
- publisher and dataset title when present
- request parameters and run timestamp
- source mode, GBIF API status and fallback warnings
- quality filters and derived metrics
- decision memo, validation checks and submission-readiness state
- evidence graph links between runs, datasets, issues, claims, actions and artifacts

## Citation Guidance

For publication, policy reports or formal reuse, do not cite a screenshot or a copied API response alone. Create a DOI-backed GBIF occurrence download or derived dataset record where appropriate, and cite GBIF-mediated data according to GBIF guidance:

- https://www.gbif.org/citation-guidelines
- https://www.gbif.org/derived-dataset/about

## Evidence Passport Warning

If a passport was generated from fixture, fallback or API mode without a GBIF download DOI, the Citation Autopilot marks citation status as incomplete and provides a DOI completion flow.

Fixture and fallback packs are reproducible demo artifacts. They are useful for judging, testing and methods review, but they should not be treated as publication-ready GBIF evidence. Online/API packs still require a DOI-backed GBIF occurrence download or derived dataset before formal publication.

## Generated Citation Files

Each run includes:

- `citations.md`: citation status, GBIF DOI warning, suggested methods text and dataset contribution table
- `decision_memo.md`: the user-facing decision answer, safe claims, blocked claims and next action
- `submission_readiness.md`: contest-readiness checklist and accepted research comments
- `validation_summary.md`: validation checks and recommended demo suite
- `impact_brief.md` and `video_script.md`: submission narrative artifacts
- `claim_guardrails.md`: supported, weak, unsupported and verification-required claims
- `dataset_contributions.csv`: `datasetKey`, title, publisher, license, record count and detected issues
- `publisher_issue_templates.md`: polite issue messages that preserve `datasetKey`, affected records, issue type and suggested fix
- `readiness_scorecard.csv`: purpose-aware readiness scores for all supported purposes
- `evidence_graph.json`: machine-readable evidence memory graph
- `graph_memory.md`: human-readable graph summary and memory cards
- `evidence_vault.zip`: portable Markdown vault for offline review
- `source_summary.json`: requested/used source mode, GBIF API status, fallback flag and warnings
- `demo_scenario.json`: compact scenario metadata and request payload
- `run.json`: request, timestamp, source mode and GBIF species match metadata
- `evidence_pack.zip`: the complete export bundle for review and sharing

The main JSON artifact can be checked against `schemas/evidence_passport.schema.json`. The schema is not a replacement for GBIF DOI workflows; it is a stability contract for reviewers and downstream tools that need to confirm what a passport contains.
