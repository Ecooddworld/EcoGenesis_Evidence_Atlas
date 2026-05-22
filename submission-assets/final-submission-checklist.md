# Final GBIF Submission Checklist

## Already Prepared

- [x] Two-mode English UI: `Presentation` and `Work with GBIF`.
- [x] Live GBIF is the default user path.
- [x] Empty fallback is honest: no fixture records reused when GBIF is unavailable.
- [x] GBIF API status is visible in the UI.
- [x] Taxon search preserves selected `taxonKey`.
- [x] Region presets and editable bbox are available.
- [x] Evidence Pack includes decision memo, map data, quality metrics, claim guardrails, citations, publisher feedback, graph memory and machine-readable JSON.
- [x] CLI runner exists for repeatable script use.
- [x] JSON schema exists for the Evidence Passport.
- [x] Three live demo cases exist in `reports/demo-cases/`.
- [x] Intro demo video exists at `submission-assets/video/ecogenesis-evidence-atlas-demo.mp4`.
- [x] Screenshots exist in `submission-assets/screenshots/`.
- [x] Entry form draft exists at `submission-assets/gbif-entry-form-draft.md`.

## Must Do Before Submit

- [ ] Make the GitHub repository public and confirm judges can access it without login.
- [ ] Upload `submission-assets/video/ecogenesis-evidence-atlas-demo.mp4` to YouTube, Vimeo, Google Drive, Figshare, OSF or another public no-cost location.
- [ ] Confirm the uploaded video plays without login and has captions/transcript available.
- [ ] Replace the TODO video URL in `submission-assets/gbif-entry-form-draft.md`.
- [ ] Fill final team member names, affiliations and contact details.
- [ ] Create a GitHub release, e.g. `v2026-gbif-submission`, with the video, screenshots and evidence pack attached or linked.
- [ ] Optional but strong: deploy the frontend/backend publicly, then add the public demo URL to the form.
- [ ] Optional but strong: create one DOI-backed GBIF occurrence download or derived dataset example and link it in `docs/gbif-data-use-and-citation.md`.
- [ ] Re-run tests after the final release commit.

## Final Verification Commands

```bash
backend/.venv/bin/python -m pytest backend/tests
cd frontend && npm test -- --run && npm run build
cd ..
backend/.venv/bin/python backend/scripts/generate_demo_report.py
submission-assets/build_submission_video.sh
```

## Entry Form Fields

- Submission name/title: ready in `gbif-entry-form-draft.md`.
- Team member(s): TODO.
- Abstract and rationale: ready in `gbif-entry-form-draft.md`.
- Operating instructions: ready in `gbif-entry-form-draft.md`.
- Video link: TODO after upload.
- Source/docs links: ready, but confirm repo visibility.

## Risk Notes

- Do not submit only local file paths. The form needs public URLs.
- Do not claim species absence from no-evidence cells.
- Do not claim population trend without a separate trend model and sampling-bias treatment.
- Do not present API-only evidence as publication-ready if no GBIF download DOI or derived dataset is attached.
