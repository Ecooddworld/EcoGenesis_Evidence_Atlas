# EcoGenesis V2 scientific walkthrough

Evidence-first release video for the corrected V2 interface and claim boundary.

## Published deliverables

- `video/ecogenesis-v2-scientific-walkthrough-en-subs.mp4` — 1920×1080, 30 fps, H.264, AAC stereo 48 kHz, burned compact English captions.
- `video/ecogenesis-v2-scientific-walkthrough-en.srt` — separate English captions.
- `video/ecogenesis-v2-scientific-walkthrough-voiceover-en.txt` — exact English narration.
- `video/ecogenesis-v2-scientific-walkthrough-thumbnail.png` — presentation thumbnail.

## Scientific scope

The walkthrough uses the current fail-closed mixed demo: four processed records, zero species rule-passes, one genus rule-pass, three repair-required records, zero records that passed local metadata checks for external GBIF/IPT validation, and four species-ranked top hits blocked or downgraded.

The Evidence Map keeps occurrence context unlinked from molecular rule evidence. The Fragment Graph uses the bundled small NCBI GenBank rbcL workflow-validation pack: identical evidence for *Quercus robur* and *Quercus petraea* is bounded to the genus *Quercus*. Tests and integrity reports demonstrate run-local reproducibility and internal consistency; they are not independent scientific validation or GBIF acceptance.

## Rebuild

The source narration, captions, builder and brand mark are retained. Screen-capture and rendering intermediates are intentionally excluded from Git.

```bash
CAPTURE_SEQUENCE=workflow,run-input,run-results,pack,map,graph,methods \
OPENER_SECONDS=3.5 CLOSING_SECONDS=10.7 \
NARRATION_AUDIO=/absolute/path/to/voiceover.aiff \
./submission-assets/contest-video-v3/build_scientific_video.sh
```
