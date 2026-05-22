# Русский пакет EcoGenesis Evidence Atlas

Этот каталог объясняет проект на русском языке так, чтобы его понял человек без знания GBIF, biodiversity informatics и внутренней архитектуры приложения.

## Что внутри

- `plain-language-description-ru.md` - самое простое объяснение проекта.
- `project-plan-ru.md` - полный план: проблема, пользователи, функции, польза, roadmap.
- `presentation-speaker-notes-ru.md` - заметки к русской презентации.
- `presentation/EcoGenesis_Evidence_Atlas_RU.pptx` - редактируемая PowerPoint-презентация.
- `presentation/EcoGenesis_Evidence_Atlas_RU.pdf` - PDF-версия презентации.
- `video/ecogenesis-evidence-atlas-demo-ru.mp4` - русское видео с озвучкой.
- `video/ecogenesis-evidence-atlas-demo-ru.srt` - русские субтитры.
- `video/demo-thumbnail-ru.png` - обложка видео.

## Главная идея проекта

EcoGenesis Evidence Atlas превращает GBIF-данные из “точек на карте” в проверяемое решение:

- что можно утверждать;
- что нельзя утверждать;
- какие данные слабые;
- какие источники надо цитировать;
- где нужны новые наблюдения;
- что можно отправить владельцам данных как feedback.

## Для чего этот русский пакет

Он нужен для обсуждений с командой, партнерами, инвесторами, наставниками и людьми, которые не обязаны понимать GBIF с первого взгляда. Английская конкурсная подача остается основной для GBIF, а этот пакет помогает быстро объяснять смысл проекта на русском.

## Как пересобрать русское видео

```bash
submission-assets/ru/build_russian_video.sh
```

Скрипт использует существующие screenshots из `submission-assets/screenshots/`, системный голос `Milena` и `ffmpeg`.
