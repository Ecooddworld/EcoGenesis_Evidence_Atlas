# Demo Scenarios

## Primary Molecular CSV Scenarios

Use these in the final GBIF Challenge video and judge walkthrough.

| File | Expected result | What it proves |
| --- | --- | --- |
| `examples/aedes_good.csv` | `ambiguous` / review-only | A plausible top hit cannot pass species rules without server-attested sampling/reference completeness, barcode-gap CI and sequence QC evidence. |
| `examples/aedes_ambiguous.csv` | `genus-safe` | A near-equivalent competitor blocks species-level overclaiming and downgrades to LCA genus. |
| `examples/aedes_missing_metadata.csv` | `ambiguous` / review-only | Missing publication metadata and missing scientific gate evidence remain explicit. |
| `examples/aedes_weak_coverage.csv` | `weak` | High identity is not enough when query coverage fails the gate. |

## UI Review Path

1. Open `https://ecooddworld.eu` or local http://localhost:13100.
2. Open **Run compiler**.
3. Click **Download CSV template** to show the expected input format.
4. Upload `examples/aedes_good.csv`.
5. Confirm CSV preview and validation summary are visible.
6. Click **Generate from CSV**.
7. Review the decision memo, outcome cards, sequence table and filters.
8. Confirm the uploaded CSV stays review-only and lists the missing scientific evidence instead of claiming a species result.
9. Download `evidence_pack.zip` or open individual outputs such as `sequence_safety_table.csv`, `data_accounting_ledger.csv`, `state_machine_audit.csv`, `publication_blockers.csv`, `dwc_occurrence_core_publishable.csv` and `molecular_evidence_report.html`.
10. Repeat or describe the other three CSV examples to show downgrade, publication blocker and weak-match behavior.
11. Run the built-in mixed demo to show that unsigned plausible candidates remain review-only alongside downgrade and weak/blocker cases.
12. Open **Methods & Audits** to show executable release invariants and the external-validation blocker.
13. Open **Validation** to show the GBIF occurrence-audit layer separately from molecular evidence.

## API Review Path

```bash
curl http://127.0.0.1:18100/health
curl http://127.0.0.1:18100/api/evidence/gbif-status
curl http://127.0.0.1:18100/api/barcode/csv-template
curl -F file=@examples/aedes_good.csv http://127.0.0.1:18100/api/barcode/import-csv
curl -F file=@examples/aedes_good.csv http://127.0.0.1:18100/api/barcode/run-csv
```

Expected:

- health returns `ok`;
- GBIF status returns `ok` when the GBIF API is reachable;
- CSV template returns the expected header;
- import returns normalized request, preview rows and validation summary;
- run returns `species_rule_pass_records=0`, explicit reference/QC blockers and Evidence Pack export URLs.
- run exports the explicit ledger/state artifacts required for contest review: `data_accounting_ledger.csv`, `state_machine_audit.csv` and `reference_completeness_audit.csv`.

## GBIF Occurrence-Audit Scenarios

The occurrence-audit layer is not the molecular compiler and is not a species benchmark. It checks GBIF API use in live network mode and bounded claim language for occurrence context.

Run:

```bash
cd backend
.venv/bin/python scripts/run_scientific_hypothesis_suite.py --fresh --output-dir /tmp/ecogenesis-scientific-theory-suite
```

Acceptance:

- at least 1,000 deduplicated GBIF occurrence records;
- at least 10 successful online scenarios;
- no fixture records counted;
- at least 100 hypothesis/claim rows;
- every claim has status, evidence pointer and caveat.

## Fixture Scope

Fixture/offline data are kept for tests and deterministic regression only. The primary user-facing path is CSV Upload → rule-based review plus a separate GBIF status/audit layer for occurrence context. Independent specimen-backed validation remains a release requirement.
