# Расшифровка EcoGenesis V2 — evidence-bounded release

## 1. Проблема
EcoGenesis V2 — это evidence-bounded release Barcode-to-GBIF Evidence Compiler. Он решает проблему раздробленного biodiversity evidence: occurrence records могут лежать в одной системе, DNA barcode fragments — в другой, BLAST или Sequence ID tables — в лабораторном pipeline, а publication metadata — в spreadsheets. Когда эти части не связаны, полезное evidence теряется, а species-level claims могут становиться сильнее, чем реально поддерживают данные.

## 2. Что делает EcoGenesis
EcoGenesis — это Barcode-to-GBIF Evidence Compiler. Он принимает DNA barcode, metabarcoding, Sequence ID и BLAST-like outputs, затем применяет configured evidence gates. Результат не является species truth. Это bounded rank result, publication-readiness check, repair plan и reproducible Evidence Pack для review.

## 3. Интерфейс сайта
В публичном demo site судьи могут открыть overview, запустить compiler, посмотреть Evidence Map и Fragment Graph, открыть Regression & Audits и Methods & Audits, а затем скачать GBIF Repair Pack. Постоянный prototype notice прямо говорит, что инструмент не является independently validated taxonomic identifier или GBIF publisher.

## 4. Загрузка DNA barcode / molecular evidence
Run Compiler — это экран, где molecular evidence входит в систему. Пользователь может загрузить CSV, запустить demo workflow или проверить reference fragment. Compiler проверяет required molecular fields, sequence context, reference-hit metrics, reference and sequence-quality evidence и publication metadata до маршрутизации record.

## 5. Пример результата
При текущей fail-closed reference attestation bundled mixed demo не выдаёт ни одного species rule-pass. AALB-COI-good и AALB-COI-metadata-gap получают состояние ambiguous, AALB-COI-ambiguous ограничивается уровнем genus, а AALB-COI-short получает состояние weak. У metadata-gap row также есть publication blockers. Это run-local rule results и validation candidates, а не independently confirmed identifications или принятые GBIF records.

## 6. Evidence Map
Evidence Map показывает hashed GBIF occurrence context рядом с molecular rule-evidence rows, graph objects и export boundaries. Occurrence rows явно не связаны с molecular rows без общих specimen или event identifiers. Карта не может усилить molecular claim и сама по себе не является evidence of presence.

## 7. Live Evidence Map
В Evidence Map reviewers видят rule-supported candidates, repair-required rows, review-only hypotheses и blocked exports. Этот же экран показывает release checks, graph audits и export boundaries before download. Pass означает согласованность файлов конкретного run, а не external scientific validity.

## 8. Fragment Graph
Fragment Graph показывает, как marker fragments связаны с reference taxa и LCA-bounded rank. Если fragment указывает на несколько близких taxa, EcoGenesis сообщает наиболее конкретный rank, разрешённый configured rules, вместо forced species claim. Evidence, competitors и caveats остаются вместе.

## 9. Проверка неопределённости
Uncertainty обрабатывается через explicit gates: identity and coverage, ambiguity and LCA downgrade, barcode gap, locally unique k-mer support в выбранном reference set, marker profile, publication checks и graph provenance. Top hit не становится species-level validation candidate, пока не пройдены все configured requirements.

## 10. Regression и integrity checks
Regression и integrity checks встроены в submission package. Проект включает backend и frontend tests, repeated-fixture competition batches, adversarial cases, graph audits и contest-readiness checks. Они проверяют fail-closed behavior и internal consistency; independent multi-taxon scientific validation остаётся future work.

## 11. Evidence Pack
Final deliverable — Evidence Pack. Он включает CSV, JSON, HTML, rule-evidence, graph и audit outputs для review, repair and reuse. Researchers могут проверять sequence decision tables, blockers, validation-candidate templates, molecular evidence reports, graph provenance и machine-readable artifacts.

## 12. Масштабирование и call to action
EcoGenesis — working contest prototype с live demo, public source code, reproducible run-local outputs и downloadable evidence artifacts. Это ещё не validated scientific identifier и не complete GBIF publishing pipeline. Call to action простой: запустить workflow, проверить его boundaries и externally validate candidate records before publication.
