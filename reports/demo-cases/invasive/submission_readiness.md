# Submission Readiness

Stage: **Demo-ready MVP; publication-grade DOI case still pending**
Ready checks: **8/9**

## Checklist

| Ready | Item | Evidence | Next step |
| --- | --- | --- | --- |
| yes | Clear end-user decision memo | decision_memo.md explains the question, evidence basis, safe claims and next action. | Use the decision memo as the first 30 seconds of the demo video. |
| yes | Live GBIF mode or safe empty fallback | Used source mode: online. | Keep empty fallback behavior so old fixture records are never confused with a failed live query. |
| yes | Claim Guardrails present | Unsupported claims and required verification are exported to claim_guardrails.md. | Highlight absence/trend/distribution guardrails in the pitch. |
| yes | Citation Autopilot and derived dataset recipe | citations.md and derived_dataset_recipe.json are generated. | Attach a real DOI-backed download or derived dataset for the strongest final case. |
| not yet | Publication-grade DOI-backed case | online_api_without_download_doi | Create a DOI-backed GBIF occurrence download or derived dataset before formal paper/policy reuse. |
| yes | Publisher Feedback Pack | 1 prioritized feedback row(s). | Use publisher_feedback.md as a data-manager handoff artifact. |
| yes | Three-scenario validation suite defined | validation_summary.md lists invasive watch, sampling gaps and dataset review scenarios. | Generate and preserve all three passports as release assets before submission. |
| yes | Offline review bundle | passport.html, evidence_pack.zip, evidence_vault.zip and Markdown exports are generated. | Attach the ZIP files to the release so judges can review without running the app. |
| yes | Video-ready story script | video_script.md is generated from the current evidence pack. | Record the screen capture after final UI polish. |

## Accepted Research Comments

- Narrowed the product to a GBIF Evidence Passport instead of a broad abstract platform.
- Integrated Claim Guardrails as a first-class output.
- Integrated Citation Autopilot with DOI completion flow and derived dataset recipe.
- Integrated Publisher Feedback with severity and fix priority.
- Integrated Graph Memory and an offline Markdown evidence vault.
- Added decision memo, validation summary, submission readiness and video-script artifacts.

## Next 72 Hours

- Generate the three validation passports and keep them as release assets.
- Create or document one DOI-backed GBIF download/derived dataset pathway.
- Record a three-minute screen capture centered on the decision memo, safe claims, citations and exports.
