# Русская расшифровка нового конкурсного видео EcoGenesis

## 1. Проблема
Проблема в том, что biodiversity evidence часто раздроблена. Occurrence records могут лежать в одной системе, DNA barcode fragments — в другой, BLAST или Sequence ID tables — в лабораторном pipeline, а publication metadata — в spreadsheets. Когда эти части не связаны, полезное evidence теряется, а species-level claims могут становиться сильнее, чем реально поддерживают данные.

## 2. Что делает EcoGenesis
EcoGenesis — это Barcode-to-GBIF Evidence Compiler. Он принимает DNA barcode, metabarcoding, Sequence ID и BLAST-like outputs, затем применяет deterministic evidence gates. Результат — не просто label. Это safe taxonomic rank decision, publication-readiness state, repair plan и reproducible Evidence Pack.

## 3. Интерфейс сайта
В публичном demo site интерфейс организован вокруг полного evidence path. Судьи могут открыть overview, запустить compiler, посмотреть evidence map, fragment graph, validation, methods и скачать Evidence Pack. У каждого раздела есть public route, поэтому workflow удобно проверять и цитировать.

## 4. Загрузка DNA barcode / molecular evidence
Run Compiler — это экран, где molecular evidence входит в систему. Пользователь может загрузить CSV, запустить demo workflow или проверить reference fragment. Compiler валидирует required molecular fields, sequence context, reference-hit metrics и publication metadata до того, как record может двигаться дальше.

## 5. Пример результата
В mixed demo records не превращаются в один упрощённый ответ. Некоторые становятся species-safe, некоторые genus-safe, некоторые остаются weak, а некоторые not publishable, пока metadata не будут repaired. Главное поведение системы: useful molecular evidence сохраняется, но unsafe species exports и incomplete publication records блокируются.

## 6. Evidence Map
Evidence Map превращает результаты в spatial evidence atlas. Он связывает GBIF occurrence context с claim states, snapshot hashes, VSEA rows, graph objects и export boundaries. Карта сама по себе не является proof of presence; это способ проверить provenance, context и claim strength в одном месте.

## 7. Live Evidence Map
В live Evidence Map reviewers видят, какие rows safe, repair-required, review-only или blocked. Этот же экран показывает judge-mode checks, graph audits и export boundaries before download. Так spatial layer остаётся explanatory and auditable, а не visual shortcut.

## 8. Fragment Graph
Fragment Graph показывает, как marker fragments связаны с reference taxa и safe LCA decisions. Если fragment указывает на несколько близких taxa, EcoGenesis reports the most specific safe rank вместо forced species claim. Evidence, competitors и caveats остаются вместе.

## 9. Проверка неопределённости
Uncertainty обрабатывается через explicit gates: identity and coverage, ambiguity and LCA downgrade, barcode gap, diagnostic k-mer support, marker profile, publication readiness и graph provenance. Top hit не становится species-level output, пока не пройдены required gates.

## 10. Validation
Validation встроена в submission package. Проект включает backend tests, frontend tests, competition batches, adversarial batches, graph audits и contest-readiness checks. Главная цель validation — fail-closed behavior: weak coverage, close competitors, metadata gaps и unsafe exports должны быть blocked or downgraded.

## 11. Evidence Pack
Final deliverable — Evidence Pack. Он включает CSV, JSON, HTML, VSEA, graph и audit outputs для review, repair and reuse. Researchers могут проверять sequence safety tables, publication blockers, molecular evidence reports, graph provenance и machine-readable export artifacts.

## 12. Масштабирование и call to action
EcoGenesis уже является working contest prototype с live demo, public source code, reproducible outputs и downloadable evidence artifacts. Он может масштабироваться на larger reference libraries, institutional pipelines, richer GBIF publishing workflows и broader molecular evidence observatories. Call to action простой: открыть live demo, запустить workflow и проверить evidence before publication.
