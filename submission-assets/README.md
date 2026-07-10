# GBIF 2026 Submission Assets

This folder contains the materials prepared for the 2026 GBIF Ebbe Nielsen Challenge submission. Current copy describes EcoGenesis as a rule-based contest prototype: outputs are validation candidates, not independently validated identifications or accepted GBIF publications. The canonical product and testing boundaries are in `../README.md`, `../docs/submission.md`, `../docs/barcode-compiler-methodology.md` and `../docs/testing.md`.

## Canonical Files

- `gbif-entry-form-draft.md`: copy-ready text for the official entry form.
- `gbif-2026-final-submission-pack.md`: compact final package with dates, links, summary, instructions and readiness status.
- `final-submission-checklist.md`: remaining actions before pressing submit.
- `judge-walkthrough.md`: compact video/demo script for judges and release notes.
- `barcode-video-script.md`: final video script for the current CSV Upload -> Score workflow.
- `barcode-entry-form-draft.md`: shorter project-specific entry text.
- `../docs/nexus-v3/`: historical Nexus V3 design material; current claims are governed by the canonical docs above.
- `../docs/gsig-observatory.md` and `../reports/observatory-demo/`: Evidence Map contract/API documentation and generated release-check pack.
- `../references/aedes_coi_mini/` and `../reports/synthetic-ambiguity-benchmark/`: V3 reference-search example, mini FASTA manifest, and naive top-hit vs EcoGenesis benchmark evidence.

## Final Local Video

- `contest-video-v2/video/ecogenesis-gbif-contest-demo-en-subs.mp4`: current contest submission video, with voiceover and burned subtitles.
- `contest-video-v2/video/ecogenesis-gbif-contest-demo-en.srt`: external subtitle file.
- `contest-video-v2/video/ecogenesis-gbif-contest-demo-english-voiceover.txt`: voiceover transcript.
- `contest-video-v2/video/ecogenesis-gbif-contest-demo-transcript.md`: additional transcript.
- `contest-video-v2/video/demo-thumbnail-contest-en.png`: local thumbnail.

The current MP4 is regenerated from the adjacent voiceover and SRT. If those files and the MP4 do not share the same remediation commit, treat the MP4 as stale and do not submit it.

## ARCHIVED Pre-Remediation Materials

Do not submit the following as current product copy. They predate the bounded-claim and validation-candidate terminology:

- `gbif-submission-assets.zip`: archived repository snapshot; see `gbif-submission-assets.zip.ARCHIVED.md`.
- `video-voiceover.txt`, `demo-video-captions.srt` and `build_submission_video.sh`: archived first-generation occurrence-audit video materials.
- `contest-video-v2/pptx-slides/` and `contest-video-v2/site-screens/`: historical visual captures; use the current transcript and live product for authoritative wording.

## Recommended Public Links

- Hosted demo: https://ecooddworld.eu
- Submission video: https://ecooddworld.eu/submission-video/
- Contest page: https://www.gbif.org/news/3DyM3tK5wgYipqyaHwG2c2/2026-ebbe-nielsen-challenge-open-for-submissions
- Official rules: https://www.gbif.org/awards/ebbe-2026-rules
- Entry form: https://www.survey-xact.dk/LinkCollector?key=YCAEZQR4SPC1
- Source repository: https://github.com/Ecooddworld/EcoGenesis_Evidence_Atlas

## Before Submission

1. Confirm the public repository URL remains reachable for judges.
2. Enter team/member details in the official GBIF form or approved private submission document.
3. Paste the public video URL into the official GBIF form: https://ecooddworld.eu/submission-video/
4. Keep the direct MP4 URL available if the form requires a file link: https://ecooddworld.eu/submission-video/ecogenesis-gbif-contest-demo-en-subs.mp4
5. Create a release tag, for example `v1.0-gbif-2026`.
6. Re-run backend tests, frontend tests, build, Observatory report generation, operability verification and browser smoke.
