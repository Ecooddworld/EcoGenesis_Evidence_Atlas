# Barcode-to-GBIF Final Explainer Video

This folder contains the current final video package for the CSV Upload -> Score workflow.

## Final Local Video

- `video/ecogenesis-barcode-to-gbif-english-voice-ru-subs.mp4`
- `video/ecogenesis-barcode-to-gbif-english-voice-ru-subs.srt`
- `video/ecogenesis-barcode-to-gbif-english-voiceover.txt`
- `video/demo-thumbnail-english-voice-ru-subs.png`

The MP4 has English system voiceover and burned Russian subtitles. The external SRT is included for platforms that support captions.

## Rebuild

```bash
submission-assets/barcode-video/build_english_voice_ru_subs_video.sh
```

The build uses local app screenshots in `screenshots/`, macOS `say`, and `ffmpeg`. No copyrighted music or third-party media are used.

## Message

The video explains the project from first principles:

- why a top DNA hit is not automatically a safe GBIF occurrence record;
- what CSV data the user uploads;
- how the compiler separates taxonomic evidence from publication readiness;
- what the user receives: safe claims, blocked claims, repair actions and Evidence Pack exports;
- what GBIF and data publishers gain;
- what the platform deliberately does not overclaim.
