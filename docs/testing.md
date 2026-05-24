# Testing Plan

## Backend

Run:

```bash
cd backend
pytest
```

Required barcode compiler tests:

- identity 99.6%, coverage 96% -> `species-safe`
- identity 99.5%, coverage 72% -> `weak`
- top 99.4%, second 99.3% -> ambiguity LCA -> `genus-safe`
- positive barcode gap and diagnostic k-mers required for species
- missing `occurrenceID` or `eventDate` -> `not-publishable`
- export endpoints return Evidence Pack artifacts

Legacy `/api/evidence/*` tests remain active to guarantee the archived Atlas layer still works as a regression/audit shell.

## Frontend

Run:

```bash
cd frontend
npm test
npm run build
```

Expected UI checks:

- `Submission overview` renders the new project title.
- `Compiler workbench` opens from the mode switch.
- Demo selector is visible.
- JSON request editor is visible.
- `Generate Evidence Package` calls `/api/barcode/run`.
- Result table shows sequence decisions.
- Evidence Pack links render.

## Browser Smoke

1. Start the stack:

```bash
docker compose up --build
```

2. Open http://localhost:13100.
3. Click `Run mixed demo`.
4. Confirm:
   - no console errors;
   - `species-safe`, `genus-safe`, `weak` and `not-publishable` are visible;
   - `evidence_pack.zip` is downloadable;
   - `/api/barcode/runs/{run_id}/report` opens the HTML report.

## Live GBIF Context

The barcode compiler itself is deterministic over supplied reference-hit results. It links to official GBIF Sequence ID and DNA-derived publishing guidance, but it does not call GBIF Sequence ID directly in the default demo. This keeps the demo repeatable for judges while remaining compatible with GBIF Sequence ID CSV or BLAST-style outputs.
