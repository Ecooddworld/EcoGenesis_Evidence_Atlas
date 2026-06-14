# Demo Scenarios

## Primary Molecular CSV Scenarios

Use these in the final GBIF Challenge video and judge walkthrough.

| File | Expected result | What it proves |
| --- | --- | --- |
| `examples/aedes_good.csv` | `species-safe` | All species-level molecular and metadata gates pass. |
| `examples/aedes_ambiguous.csv` | `genus-safe` | A near-equivalent competitor blocks species-level overclaiming and downgrades to LCA genus. |
| `examples/aedes_missing_metadata.csv` | `not-publishable` | Taxonomic evidence can be safe while publication is blocked by missing required fields. |
| `examples/aedes_weak_coverage.csv` | `weak` | High identity is not enough when query coverage fails the gate. |

## UI Review Path

1. Open http://localhost:13100.
2. Open **Run compiler**.
3. Click **Download CSV template** to show the expected input format.
4. Upload `examples/aedes_good.csv`.
5. Confirm CSV preview and validation summary are visible.
6. Click **Generate from CSV**.
7. Review the decision memo, outcome cards, sequence table and filters.
8. Confirm `species-safe` appears for the good case.
9. Download `evidence_pack.zip` or open individual outputs such as `sequence_safety_table.csv`, `data_accounting_ledger.csv`, `state_machine_audit.csv`, `publication_blockers.csv`, `dwc_occurrence_core_publishable.csv` and `molecular_evidence_report.html`.
10. Repeat or describe the other three CSV examples to show downgrade, publication blocker and weak-match behavior.
11. Open **Math & proof** to show the deterministic gates and proof-by-failure-mode logic.
12. Open **Research audit** to show the live GBIF occurrence-audit layer and 1000-record / 100-claim validation.

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
- run returns `species_safe_records=1` and Evidence Pack export URLs.
- run exports the explicit ledger/state artifacts required for contest review: `data_accounting_ledger.csv`, `state_machine_audit.csv` and `reference_completeness_audit.csv`.

## Live GBIF Occurrence-Audit Scenarios

The occurrence-audit layer is not the molecular compiler. It validates live GBIF API use and safe claim language for occurrence evidence.

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

Fixture/offline data are kept for tests and deterministic regression only. The primary user-facing and submission-facing path is CSV Upload -> Score for molecular evidence and live GBIF status/audit for occurrence context.
