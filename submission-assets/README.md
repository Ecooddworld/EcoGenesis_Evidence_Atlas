# EcoGenesis Evidence Atlas Submission Assets

This folder contains the local materials prepared for the 2026 GBIF Ebbe Nielsen Challenge submission.

## Files to Upload or Link

- `video/ecogenesis-evidence-atlas-demo.mp4`: 1280x720 intro demo video with English voiceover and burned-in captions.
- `video/ecogenesis-evidence-atlas-demo.srt`: external captions for the same video.
- `video/demo-thumbnail.png`: thumbnail frame for video upload.
- `screenshots/*.png`: eight judge-facing screenshots of the live UI flow.
- `gbif-entry-form-draft.md`: copy-ready text for the entry form.
- `final-submission-checklist.md`: the remaining launch checklist before pressing submit.

## Recommended Submission Links

- Contest page: https://www.gbif.org/news/3DyM3tK5wgYipqyaHwG2c2/2026-ebbe-nielsen-challenge-open-for-submissions
- Official rules: https://www.gbif.org/article/4KY2Ct5v60rocbbjEiwlRN/official-rules-2026-gbif-ebbe-nielsen-challenge
- Repository: https://github.com/oddworld666/EcoGenesis_Evidence_Atlas

After uploading the MP4 to YouTube, Vimeo, Google Drive, Figshare, OSF or another no-cost public location, paste that public video URL into the entry form and replace the placeholder in `gbif-entry-form-draft.md`.

## Rebuild Video

```bash
submission-assets/build_submission_video.sh
```

The script expects the screenshots in `submission-assets/screenshots/` and writes the final MP4/SRT files to `submission-assets/video/`.
