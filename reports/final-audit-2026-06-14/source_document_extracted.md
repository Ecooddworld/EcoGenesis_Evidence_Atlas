# Extracted DOCX Content

- Source: `/Users/oddworld/Downloads/EcoGenesis_Molecular_Evidence_Graph_Full_Project_RU.docx`
- SHA256: `af1464a5c233ecdc9780f626208d3d21abcf4bf1f5c20248d76ec76c7ed3a4a8`
- Paragraph blocks: 172
- Tables: 30
- Media files: 0

## Body

EcoGenesis Molecular Evidence Graph
Полный проект развития приложения: Barcode-to-GBIF Evidence Compiler и будущая графовая система молекулярных доказательств

## Таблица 1

| Версия документа: 1.0 RU (14 июня 2026)
Статус: проектная спецификация + научно-методическая дорожная карта
Цель: превратить ДНК-фрагменты, баркоды, eDNA и метагеномные участки в проверяемые, воспроизводимые и безопасные таксономические доказательства
Ключевой принцип: система не угадывает вид; она сообщает самый узкий таксон, который честно поддержан данными и не опровергнут рисками |
| --- |
Подготовлено на основе загруженных материалов проекта, 100-sequence evidence pack и исследовательского аудита интерфейса. Документ не является peer-review публикацией; это проектная спецификация и научно-технический план развития.
## Содержание
1. Резюме проекта и главный вывод
2. Объяснение для любого пользователя
3. Реальная научная задача
4. Научная гипотеза и границы допустимых утверждений
5. Методологическое ядро и формулы
6. Архитектура системы
7. GBIF-публикация и readiness gates
8. Текущее состояние и результаты 100-sequence batch
9. Критические проблемы и конкретные исправления
10. Стратегия валидации
11. Данные, артефакты и Evidence Pack
12. Дорожная карта
13. UI/UX и пользовательские сценарии
14. Операционная реализация
15. Глоссарий
16. Источники и нормативная база
## 1. Резюме проекта и главный вывод

## Таблица 2

| Короткий вердикт
Проект жизнеспособен и имеет реальную научную ценность, но не как “определитель вида по одной строке ДНК”. Его сильная позиция - стать системой преобразования молекулярных сигналов в аудируемые доказательства: какой таксон можно безопасно заявить, какие утверждения заблокированы, чего не хватает для публикации и какие действия разблокируют максимум записей. Главный риск - перепутать высокий top-hit с научной истиной. Если это не устранить методически, приложение будет выглядеть сильнее, чем оно доказано. Если устранить - проект становится серьезной платформой для GBIF-ready публикаций, контроля переобъявлений и будущего графа фрагментов генома. |
| --- |
EcoGenesis должен быть представлен не как “искусственный интеллект, расшифровывающий геном”, а как строгий компилятор доказательств. Он принимает молекулярное наблюдение, результаты сопоставления с референсными базами, метаданные образца, метод лаборатории и контекст публикации. Затем система выдает не одно красивое название вида, а полный пакет: безопасный таксономический ранг, список конкурирующих таксонов, причины блокировки, поля для ремонта, GBIF/Darwin Core шаблоны и воспроизводимый Evidence Pack.
Стратегическая версия проекта: перейти от Barcode-to-GBIF Compiler к Molecular Evidence Graph - графовой базе, где каждый фрагмент ДНК, участок маркера, ген, континг, ASV/OTU, образец, регион, метод, референсная запись и публикационное утверждение представлены как отдельные узлы и связи. Такой граф позволит в будущем не “обещать расшифровку всех геномов”, а честно размечать все участки генома по их функции, происхождению, таксономической информативности, неопределенности и пригодности для публикации.

## Таблица 3

| Что уже сильно | Что опасно | Как исправить |
| --- | --- | --- |
| Fail-closed логика: небезопасные species claims не проходят | Порог 99% identity и 80% coverage может выглядеть универсальным, хотя он зависит от маркера и клады | Перевести пороги в marker/taxon profiles и калибровать на holdout-наборах |
| Разделение таксономического статуса и публикационного статуса | GBIF-ready, publishable_candidate и repair_required могут смешиваться в интерфейсе | Сделать конечный автомат состояний и отдельные счетчики для каждого слоя |
| Evidence Pack, CSV/JSON/HTML артефакты, ремонтный план | Текстовые claim-ы могут выглядеть шаблонными и не доказывать конкретную запись | Генерировать утверждения только из evidence graph: hit, LCA, gap, k-mers, metadata, blockers |
| Идея fragment sharedness: общий фрагмент не выбрасывается, а понижается до безопасного ранга | LCA может скрывать HGT, интрогрессию, NUMTs, неполную библиотеку и cryptic species | Добавить explicit caveats, reference completeness, conflict graph и экспертный review gate |
## 2. Объяснение для любого пользователя
Представьте, что ДНК-фрагмент - это не паспорт, а кусочек отпечатка пальца. Иногда он уникален для вида; иногда такой же кусочек встречается у нескольких близких видов; иногда кусочек слишком короткий; иногда у записи нет даты, координат или метода. EcoGenesis не должен насильно назвать вид. Он должен сказать: “этот фрагмент надежно ведет к виду”, “только к роду”, “нужна проверка”, “не хватает метаданных” или “публиковать нельзя”.

## Таблица 4

| Класс решения | Простое объяснение | Что делать пользователю |
| --- | --- | --- |
| species-safe | ДНК и все проверки достаточно уверенно поддерживают именно вид. | Можно готовить публикацию на уровне вида, если метаданные GBIF полные. |
| genus-safe / higher-rank-safe | Фрагмент похож на несколько близких видов, но все они входят в один род/семейство. | Публиковать на безопасном ранге или добавить более длинный/другой маркер. |
| weak | Совпадение слабое: мало покрытия, короткий фрагмент, низкая уверенность или плохой маркер. | Не публиковать как вид; улучшить последовательность или оставить в review. |
| no-match | Нет надежного совпадения с референсной базой. | Проверить качество, базу, маркер; возможно, это неизвестный/непредставленный таксон. |
| repairable | Биологический сигнал может быть полезен, но не хватает полей для публикации. | Добавить occurrenceID, eventDate, координаты, метод, праймеры, DOI/датасетные ссылки. |
| not-publishable | Не выполнены обязательные научные или публикационные условия. | Не экспортировать в GBIF-ready слой до устранения блокеров. |

## Таблица 5

| Что приложение должно обещать пользователю
1) “Я покажу, насколько безопасно утверждать таксон по молекулярному фрагменту.”
2) “Я не спрячу сомнения: конкуренты, пробелы в референсах и отсутствующие метаданные будут видны.”
3) “Я выдам файлы, которые можно проверить, исправить и процитировать.”
4) “Я не доказываю отсутствие организма, численность популяции, фенотип, распространение в природе или эволюционную роль по одному фрагменту.” |
| --- |
## 3. Реальная научная задача
Реальная проблема не в том, что ученые не умеют запускать BLAST. Проблема в том, что результаты молекулярных поисков часто превращаются в небезопасные species claims: верхний hit механически становится видом, хотя ближайший конкурент статистически неотличим, база неполная, маркер короткий, а для публикации нет обязательных полей. EcoGenesis должен решать задачу “evidence conversion”: из молекулярного сигнала сделать проверяемое, машинно-читаемое и публикационно безопасное доказательство.

## Таблица 6

| Научная боль | Почему это важно | Как отвечает проект |
| --- | --- | --- |
| Top-hit overclaim | Высокий процент identity не равен виду, если близкие виды не разделяются. | LCA downgrade, barcode-gap gate, diagnostic k-mers, explicit blockers. |
| Неполные референсные библиотеки | Отсутствие конкурента в базе не значит отсутствие конкурента в природе. | Reference Completeness Index и caveat “reference-limited”. |
| Плохая воспроизводимость | Через год база и taxonomy изменятся, а старый вывод невозможно проверить. | Evidence Pack: hits, parameters, reference manifest, source provenance. |
| Слабая публикационная дисциплина | GBIF/DwC требует структуру, идентификаторы, дату, место, метод и цитирование. | Occurrence core + DNA-derived extension + publication blockers. |
| Потеря неоднозначных фрагментов | Ambiguous фрагменты тоже несут знание на уровне рода/семейства/клады. | Fragment sharedness превращает неоднозначность в безопасный LCA-уровень. |
| Будущая интерпретация геномных участков | Фрагменты будут появляться из shotgun, MAG, pangenome, long-read и mixed samples. | Graph model: fragment -> segment -> marker/gene -> taxon -> sample -> claim -> publication state. |

## Таблица 7

| Формулировка большой научной цели
Создать открываемый, воспроизводимый и расширяемый граф молекулярных доказательств, который для каждого ДНК-участка показывает: где он найден, к каким таксонам он привязан, на каком ранге это безопасно утверждать, какая неопределенность остается, какие источники и методы поддерживают вывод, и какие действия нужны для публикации или научной проверки. |
| --- |
## 4. Научная гипотеза и границы допустимых утверждений
### 4.1. Исходная гипотеза
Исходная идея - ДНК-фрагменты можно безопасно сопоставлять с таксономическими рангами species -> genus -> family на основе их распределения среди известных таксонов. В слабой форме эта гипотеза верна и научно полезна. В сильной форме она опасна: “фрагмент указывает на вид” нельзя утверждать без маркерного контекста, полноты референсов, конкурентов, качества выравнивания, лабораторных контролей и независимой валидации.
### 4.2. Усиленная, защищаемая гипотеза

## Таблица 8

| Рекомендуемая научная формулировка
При заданном маркере, заданной референсной библиотеке, явной таксономической версии, известном методе сопоставления и проверенных QC-метаданных ДНК-фрагмент может поддерживать самый узкий таксономический ранг, для которого: (a) все статистически неотличимые совпадения входят в этот таксон; (b) маркер имеет эмпирическую разделяющую способность в данной кладе; (c) риск неполноты референсов явно измерен; (d) публикационные поля не противоречат выводу; (e) система сохраняет все caveats и не превращает отсутствие данных в доказательство отсутствия вида. |
| --- |
### 4.3. Что категорически нельзя обещать
Нельзя обещать “полную расшифровку всех геномов” в смысле полной биологической истины. Можно обещать сегментацию, аннотацию, таксономическую привязку, функциональные подсказки и уровень уверенности для каждого участка.
Нельзя считать geography context прямым доказательством присутствия, если молекулярная проба не имеет координат или связанного события отбора.
Нельзя делать вывод об отсутствии вида по no-match или отсутствию GBIF occurrence.
Нельзя выводить фенотип, численность, распределение или тренд популяции из одиночного barcode hit без внешних данных.
Нельзя считать белковую трансляцию видовым доказательством: protein sanity - QC-слой для coding markers, а не независимый species discriminator.
### 4.4. Основные биологические edge cases

## Таблица 9

| Edge case | Почему ломает простую логику | Защитный механизм |
| --- | --- | --- |
| Cryptic species | Разные виды могут иметь почти одинаковый barcode. | LCA downgrade, expert review, multi-marker consensus. |
| Incomplete reference library | Близкого вида нет в базе, поэтому top-hit выглядит уникальным. | RCI, leave-one-out validation, “reference-limited” caveat. |
| Introgression / hybridization | Митохондриальный marker может перейти между видами. | Marker-specific caveat, nuclear markers, conflict graph. |
| Horizontal gene transfer | Особенно важно для микробов и мобильных элементов. | Do not force species by single locus; use genome-context and gene-family warnings. |
| NUMTs / pseudogenes | Митохондриальные фрагменты могут быть ядерными копиями. | Protein sanity, stop codons, frameshift risk, coverage/profile checks. |
| Contamination / index hopping | Фрагмент может быть лабораторным шумом. | Controls, blanks, replicates, assay gate, read-count caveats. |
| Taxonomic synonymy | Имя в базе и backbone могут расходиться. | Taxon resolver, acceptedNameUsage, taxonID provenance. |
## 5. Методологическое ядро и формулы
Текущие формулы проекта правильны по духу: они пытаются не просто выбрать лучший hit, а проверить identity, coverage, ambiguity boundary, barcode gap, diagnostic k-mers, reference completeness, protein sanity и publication readiness. Главная доработка - перевести фиксированные пороги и бинарные флаги в калиброванные профили по маркеру, кладе и типу данных, не теряя детерминированной воспроизводимости.
### 5.1. Минимальный входной контракт

## Таблица 10

| Слой | Обязательные данные | Зачем нужны |
| --- | --- | --- |
| Sequence layer | sequenceID, sequence/ASV/fragment, marker/locus, aligned length, hit table | Чтобы проверить совпадение, покрытие, длину и конкурентов. |
| Reference layer | reference database name/version, accession, taxonomy, lineage, source quality | Чтобы вывод был воспроизводимым и ограниченным версией базы. |
| Sample layer | eventID, materialSampleID, basisOfRecord, eventDate, coordinates/uncertainty | Чтобы молекулярный сигнал стал occurrence evidence, а не абстрактной последовательностью. |
| Assay layer | primers, method, controls, replicates, read counts, contamination flags | Чтобы отличить наличие молекулярного сигнала от шума/контаминации. |
| Publication layer | dataset title, publisher, DOI/citation, license, EML/methods | Чтобы экспорт мог быть проверен, процитирован и переиспользован. |
### 5.2. Базовые gate-правила
Exact(h_i) = I(identity_i >= theta_identity(marker, clade)) * I(queryCoverage_i >= theta_coverage(marker, clade)) * I(length_i within marker_profile)
Close(h_i) = I(identity_i close to top within statistical boundary) * I(coverage_i sufficient)
Weak(h_i)  = I(identity_i or coverage_i below calibrated threshold) OR I(marker profile fails)
Species claim is forbidden if top hit is not exact or if any close competitor cannot be separated.
Порог identity >= 99% и query coverage >= 80% можно оставить только как дефолтный профиль для демонстрации COI full barcode. В продуктовой и научной версии пороги должны жить в таблице marker_profile: markerFamily, taxonomicScope, minLength, identitySpeciesMin, coverageSpeciesMin, barcodeGapMin, diagnosticKmerMin, empiricalValidationSet, falsePositiveCeiling.
### 5.3. SafeTaxon через LCA
U(s) = {hit h in H(s): hit h is statistically indistinguishable from top hit}
SafeTaxon(s) = LCA({taxon(h): h in U(s)})
PublishedTaxon = SafeTaxon only if publication gates pass; otherwise review/repair.
LCA-понижение научно защищаемо: если два вида неразделимы, нельзя публиковать один вид, но можно сохранить знание на уровне их общего предка. Однако LCA не должен быть единственной защитой. Нужно явно показывать список конкурентов, расстояние до top hit, taxonomic entropy, RCI и тип референсной неполноты.
### 5.4. Рекомендуемая вероятностная надстройка
For every candidate taxon t:
weight(t) = exp(-lambda * distance_to_query) * coverage_score * marker_quality * reference_quality * assay_quality
p(t | evidence) = weight(t) / sum(weight(all candidates))
H_rank = - sum_{taxa at rank} p(t) * log(p(t)) / log(number_of_candidate_taxa)
Specificity = 1 - H_rank
Safe rank = deepest rank where P(clade | evidence) >= tau_rank and RCI >= tau_RCI and no hard blocker exists.
Эта надстройка не заменяет deterministic fail-closed gate. Она нужна для прозрачного ранжирования неопределенности и для объяснения пользователю, почему species-safe отличается от genus-safe не только названием, но и измеримой энтропией.
### 5.5. Barcode gap
D_intra(t) = max distance between references inside taxon t
D_inter(t) = min distance between t and nearest outside taxon
BarcodeGap(t) = D_inter(t) - D_intra(t)
Species gate passes only if lower_CI(BarcodeGap(t)) > delta and reference set has enough close relatives.
Текущая идея “BG > 0” недостаточна для реального мира. Нужно требовать доверительный интервал или bootstrap по референсам; иначе один слабый/ошибочный референс может искусственно создать gap.
### 5.6. Diagnostic k-mers
K_s = k-mers in sequence s
D_k(t) = k-mers present in taxon t and absent from close competitors
DiagnosticSupport(s,t) = |K_s intersect D_k(t)| / |K_s|
Reject species claim if empirical_false_positive(D_k, holdout) > alpha.
Диагностические k-mers полезны как дополнительный слой, но они легко переобучаются на неполной базе. Поэтому нужен holdout-тест: скрыть часть референсов, проверить ложноположительные species claims и хранить результат в marker_profile_audit.
### 5.7. Reference Completeness Index 2.0
Текущая формула RCI через долю видов GBIF, представленных в референсной библиотеке маркера, лучше чем ничего, но она слишком грубая. Она не видит качество последовательностей, близких родственников, географию, типовые экземпляры, количество референсов на вид и synonymy.

## Таблица 11

| Компонент RCI 2.0 | Как считать | Зачем |
| --- | --- | --- |
| Taxon coverage | Доля accepted species в кладе, имеющих marker m | Общий риск отсутствующих конкурентов. |
| Close-relative coverage | Доля ближайших родственных видов с качественными референсами | Самый важный слой для species-safe. |
| Sequence quality | Длина, N-content, voucher, accession status, curated flag | Плохие референсы опаснее отсутствующих. |
| Geographic coverage | Наличие референсов из региона/экозоны образца | Локальные lineage могут быть не представлены. |
| Per-species depth | Количество независимых референсов на вид | Один референс не описывает внутривидовую вариацию. |
| Taxonomic stability | Синонимы, disputed taxa, recent split/merge | Снижает риск устаревшего имени. |
### 5.8. Protein sanity и genome-wide расширение
Для coding markers проверка рамки считывания, внутренних стоп-кодонов, frameshift и NUMT/pseudogene warnings является QC-слоем. Она не должна повышать species confidence сама по себе. Для будущей “расшифровки участков генома” нужно расширить модель: каждый участок получает тип segment_class: coding_gene, rRNA, tRNA, ITS/spacer, intron, UTR, promoter/regulatory, repeat, mobile_element, mitochondrial, chloroplast, nuclear, plasmid, viral, unknown. Для каждого класса нужны разные правила evidence и разные ограничения claims.

## Таблица 12

| Тип участка | Что можно утверждать | Что нельзя утверждать без дополнительных данных |
| --- | --- | --- |
| COI/ITS/16S/18S barcode | Таксономический safe rank и маркерную принадлежность | Фенотип, численность, отсутствие вида. |
| Coding gene | ORF sanity, gene family, possible function, taxonomic signal | Точную функцию in vivo без аннотационной базы/эксперимента. |
| Noncoding spacer/intron | Вариативность, lineage signal, primer/region identity | Видовой claim без калибрации и референсов. |
| Repeats/mobile elements | Тип повторов/элементов, possible origin | Таксономическую принадлежность как species truth. |
| Metagenomic contig/MAG | Набор gene hits, completeness/contamination, taxonomic placement | Чистый вид без binning/phylogeny/QC. |
| Unknown segment | Наличие и координаты фрагмента, similarity hints | Биологическую роль или распространение. |
## 6. Архитектура системы
Текущая трехуровневая структура правильная, если явно разделить обязанности. Occurrence Evidence Audit отвечает за качество GBIF/occurrence данных. Barcode Compiler отвечает за молекулярную безопасность таксономического вывода. Molecular Evidence Graph объединяет фрагменты, таксоны, пробы, методы, источники, блокеры и публикационные утверждения. Ошибка архитектуры возникает, когда UI смешивает эти уровни в один readiness score.

## Таблица 13

| Уровень | Роль | Не должен делать |
| --- | --- | --- |
| A. Occurrence Evidence Audit | Проверяет записи GBIF: occurrenceID, дата, координаты, uncertainty, publisher, DOI, dataset bias, duplicates. | Не должен доказывать molecular species identity. |
| B. Barcode-to-GBIF Evidence Compiler | Проверяет sequence hit, coverage, ambiguity, LCA, marker profile, blockers, export pack. | Не должен притворяться полным genome annotator. |
| C. Molecular Evidence Graph | Хранит все связи: fragment, segment, taxon, sample, method, geography, reference, claim, blocker, export. | Не должен скрывать неопределенность за одним score. |
### 6.1. Рекомендуемый поток данных
Input CSV / FASTA / BLAST / Sequence ID
-> Normalize fields and validate schema
-> Resolve taxonomy and reference provenance
-> Build hit set and competitor set
-> Run marker profile gates
-> Run ambiguity boundary + LCA safe rank
-> Run barcode gap and diagnostic k-mer support
-> Attach assay/QC and occurrence metadata gates
-> Generate taxonomic status and publication status separately
-> Write Evidence Graph + Evidence Pack + repair plan + GBIF/DwC exports
-> UI displays supported claim, blockers, repair actions, and caveats.
### 6.2. Модульная архитектура

## Таблица 14

| Модуль | Вход | Выход | Критический тест |
| --- | --- | --- | --- |
| Input Normalizer | CSV, FASTA, BLAST, Sequence ID, local reference FASTA | Canonical SequenceEvidenceRecord | Ошибки схемы объясняются до запуска. |
| Reference Resolver | NCBI/BOLD/UNITE/GBIF backbone/local refs | ReferenceManifest + taxon lineage | Версия базы и источник сохраняются. |
| Hit Processor | Hit table, alignment metrics | Candidate set + top/close/weak hits | Top-hit не может стать species claim без gates. |
| Taxon Safety Engine | Candidates, marker profile, RCI | SafeTaxon, entropy, blockers | Ambiguous competitors понижают rank. |
| Publication Gate | Occurrence core + DNA extension fields | publishable_candidate / repair_required / GBIF-ready | Поля publication не влияют на taxonomic truth. |
| Repair Optimizer | Blockers and counts | Ranked repair_plan.csv | Действия ранжируются по unlockable records. |
| Evidence Graph Writer | All entities and decisions | JSON/RDF/GraphDB-ready representation | Каждый claim имеет source edges. |
| Report Builder | Evidence graph + exports | HTML/CSV/ZIP/methods/citations | Отчет воспроизводим без UI. |
### 6.3. Графовая модель

## Таблица 15

| Узел | Примеры полей | Ключевые связи |
| --- | --- | --- |
| Fragment / Segment | sequenceID, raw sequence/hash, length, segment_class, markerProfile | MATCHES ReferenceHit; DERIVED_FROM Sample; SUPPORTS Claim |
| ReferenceHit | accession, identity, coverage, aligned_length, evalue, databaseVersion | BELONGS_TO Taxon; FROM ReferenceDatabase |
| Taxon | taxonID, scientificName, rank, lineage, acceptedNameUsage | PARENT_OF; LCA_OF candidates |
| Sample / Occurrence | occurrenceID, eventID, materialSampleID, eventDate, coordinates | HAS_FRAGMENT; IN_DATASET; HAS_METHOD |
| Assay / Method | primers, controls, replicates, seq_meth, SOP | VALIDATES or WARNS Claim |
| Claim | claimID, claimedTaxon, safeRank, status, caveat | SUPPORTED_BY hits/gates; BLOCKED_BY blockers |
| Blocker | type, severity, field, action | BLOCKS Claim or Export; UNLOCKED_BY RepairAction |
| ExportArtifact | CSV/JSON/HTML/ZIP, checksum, schema | GENERATED_FROM run/provenance |
## 7. GBIF-публикация и readiness gates
GBIF-публикация должна быть вторым измерением решения, а не подтверждением вида. Последовательность может быть taxonomically species-safe, но не publishable из-за отсутствующего occurrenceID или eventDate. И наоборот, occurrence может быть формально полным, но molecular species claim может быть unsafe. Эти два состояния должны жить раздельно.

## Таблица 16

| Слой | Минимально блокирующие поля/условия | Рекомендуемые поля/условия |
| --- | --- | --- |
| Occurrence core | basisOfRecord, occurrenceID, eventDate, scientificName, taxonRank, country/coordinates where applicable | recordedBy, materialSampleID, eventID, coordinateUncertaintyInMeters, geodeticDatum, occurrenceStatus. |
| DNA-derived extension | Связь с core record; target marker where applicable; sequence or stable sequence identifier when possible | DNA_sequence/ASV hash, sop, target_gene, target_subfragment, pcr_primer_forward/reverse, seq_meth, database/protocol references. |
| Dataset metadata | Dataset title, publisher/organization, license, citation path for formal publication | DOI, EML methods, dataset contact, provenance, external repository accessions. |
| Evidence report | Taxonomic status, publication status, blockers, source references | claim boundaries, reference gap index, diagnostic k-mer report, source provenance manifest. |

## Таблица 17

| Операциональное различие repairable и not-publishable
repairable: запись имеет потенциально полезный биологический сигнал, а блокеры относятся к исправимым полям или методическим метаданным. Пример: нет occurrenceID/eventDate, не заполнены праймеры, нет SOP.
not-publishable: запись не должна входить в publication export как поддержанное утверждение, потому что species/rank claim не поддержан, нарушает hard gates или отсутствуют неустранимые в текущем запуске доказательства. В UI это нужно показывать как “не публиковать сейчас”, а не как “данные плохие навсегда”. |
| --- |
В документации GBIF актуальный подход для DNA-derived data поддерживает публикацию через Occurrence core с DNA derived data extension, потому что core хранит “что, где и когда”, а extension хранит молекулярные детали. Проект должен использовать именно эту модель, но не делать все highly recommended поля hard blockers. Hard blockers - только то, без чего запись не может быть корректной или воспроизводимой. Recommended blockers - отдельный quality tier.
## 8. Текущее состояние и результаты 100-sequence batch
Загруженный 100-sequence пакет показывает, что текущий backend способен выполнить batch run и выдать проверяемые артефакты. Это важный MVP-сигнал: система не только принимает “хорошие” записи, но и корректно понижает ambiguity, блокирует weak coverage и отделяет метаданные от биологического вывода.

## Таблица 18

| Метрика 100-sequence run | Значение |
| --- | --- |
| Records submitted | 100 |
| API status | completed |
| Exports returned | 39 |
| Decision classes | genus-safe: 25, not-publishable: 25, species-safe: 25, weak: 25 |
| Publication buckets | publishable_candidate: 50, repair_required: 50 |
| Hard gate audit | 100 rows, all “pass: fail-closed rules preserved” |
| Publishable Darwin Core rows | 50 |
| GBIF-ready Darwin Core rows | 0 (пустой файл: формальная publication-ready стадия не достигнута) |
| Naive top-hit overclaims prevented | 75 rows |
| Publication blockers | 125 rows |
| Repair plan actions | 7 actions |
### 8.1. Expected vs actual

## Таблица 19

| Expected input bucket | Actual decisionClass | Count |
| --- | --- | --- |
| genus_safe_ambiguous | genus-safe | 25 |
| metadata_blocked | not-publishable | 25 |
| species_safe | species-safe | 25 |
| weak_coverage | weak | 25 |
### 8.2. Hard gate profile

## Таблица 20

| Gate | Counts |
| --- | --- |
| exactMatchGate | pass: 75, fail: 25 |
| ambiguityLcaGate | pass: 75, fail: 25 |
| barcodeGapGate | pass: 100 |
| diagnosticKmerGate | pass: 100 |
| markerProfileGate | pass: 100 |
| occurrenceCoreGate | pass: 75, fail: 25 |
| dnaMetadataGate | pass: 100 |
| assayGate | pass: 100 |
### 8.3. Что уже MVP-ready
Запуск batch API на 100 последовательностях с воспроизводимым output inventory.
Детерминированная классификация species-safe, genus-safe, weak, not-publishable.
Fail-closed overclaim prevention: 75 потенциальных naive top-hit overclaims вынесены из species-safe публикации.
Разделение publishable_candidate и repair_required.
Evidence Pack с sequence_safety_table, hard_gate_audit, publication_blockers, repair_plan, Darwin Core exports и JSON/HTML отчетами.
UI объясняет пользователю, что ДНК-буквы являются evidence input, а не final truth.
### 8.4. Что требует фундаментальной доработки
Калибровка порогов по маркеру/кладе вместо единого 99/80.
Реальная Reference Completeness Index 2.0 с close-relative coverage и качеством референсов.
Валидация на внешних референсных наборах и leave-one-species-out тестах.
Graph backend как первая сущность, а не только JSON export.
Явное разделение downloaded records, deduplicated records, hypotheses, candidate claims, safe claims и GBIF-ready records во всех UI-метриках.
Фрагментно-геномное расширение: segment ontology, multi-marker consensus, functional annotation, conflict graph.
Реальные eDNA/assay gates: negative controls, positive controls, replicates, read count thresholds, contamination model.
### 8.5. 1000-record live GBIF audit: как правильно трактовать
Исследовательский аудит интерфейса на 1000 live GBIF records полезен как occurrence evidence audit, но он не доказывает молекулярную классификацию, потому что валидирует occurrenceID, географию, дубликаты, dataset concentration, publisher/citation metadata и uncertainty, а не истинность sequence-to-species. Поэтому в продукте нужно жестко отделить “GBIF occurrence audit” от “barcode compiler”.

## Таблица 21

| Из UI-аудита | Правильная интерпретация |
| --- | --- |
| 1000 live GBIF records | Загруженный корпус occurrence-записей для аудита качества и источников. |
| 149 duplicates skipped | Deduplication влияет на denominators; нельзя сравнивать с downloaded count без явной метки. |
| 100 hypotheses / claims | Это научные гипотезы или проверяемые claims, а не обязательно 100 молекулярных последовательностей. |
| 130 high uncertainty records | Географическая/координатная неопределенность блокирует fine-scale conclusions, но не всегда общий occurrence context. |
| records_1000.csv, theory_claims_100.csv, scenario_metrics.csv | Отдельные артефакты разных уровней, которые нельзя сливать в один readiness score. |
## 9. Критические проблемы и конкретные исправления

## Таблица 22

| Принцип приоритезации
P0 - все, что может привести к ложному species claim, ложной GBIF-ready метке или невоспроизводимому выводу. P1 - все, что повышает научную надежность и валидируемость. P2 - расширение в граф и genome-wide платформу. |
| --- |

## Таблица 23

| Issue | Симптом | Почему критично | Fix | Acceptance criteria |
| --- | --- | --- | --- | --- |
| P0-1. Смешение счетчиков | Downloaded, deduped, hypotheses, safe claims, publishable candidates и GBIF-ready rows могут звучать как один показатель. | Пользователь и ревьюер не понимают denominators; можно случайно завысить успех. | Ввести DataAccountingLedger: input_n, downloaded_n, deduped_n, eligible_n, candidate_n, safe_n, publishable_candidate_n, gbif_ready_n. Каждый KPI обязан иметь numerator и denominator. | UI и CSV показывают одинаковые denominators; regression test падает при расхождении. |
| P0-2. GBIF-ready путается с publishable_candidate | В batch есть 50 publishable Darwin Core rows, но GBIF-ready file пустой. | Пользователь может думать, что уже готово к GBIF, хотя финальные DOI/metadata gates не пройдены. | Сделать три состояния: evidence_publishable, dwc_template_ready, formal_gbif_ready. Пустой GBIF-ready export объяснять явно. | Нет кнопки “GBIF-ready export” при hard blockers; есть “publishable candidate export”. |
| P0-3. Fixed threshold overconfidence | identity>=99 и coverage>=80 выглядят универсально. | Для разных маркеров и клад это может дать ложные виды или чрезмерные блокировки. | Создать marker_profile_registry.yaml: пороги, minLength, validation set, taxonomic scope, empirical FPR. | Каждое решение хранит profile_id и версию профиля. |
| P0-4. Readiness score слабее gate logic | Один score может скрыть критический blocker. | Суммарный балл допускает “80% ready” при missing occurrenceID. | Заменить score на state machine + blocker taxonomy; score оставить только как secondary progress индикатор. | Любой hard blocker принудительно переводит export state в repair_required. |
| P0-5. Templated claims | Фразы “supported by gates” могут повторяться без записи конкретных доказательств. | Рецензент не видит, какие hits/competitors реально доказали claim. | Claim generator должен брать текст из graph edges: topHit, competitors, LCA, barcodeGap, kmerCount, RCI, metadata fields. | Каждый claim имеет machine-readable claim_boundaries row и human-readable rationale. |
| P0-6. Publisher/DOI metadata как биология | Пустой publisher/DOI блокирует публикацию, но не таксономическую интерпретацию. | Смешение scientific evidence и publication citation создает неверную диагностику. | Разделить blocker.kind: taxonomic, molecular_qc, occurrence_core, dna_extension, dataset_metadata, citation. | UI показывает “taxonomy safe, publication metadata missing” вместо “not species”. |
| P0-7. Reference incompleteness hidden | RCI слишком грубый и может создавать ложное чувство безопасности. | Непредставленный close competitor не попадет в LCA. | RCI 2.0 + leave-one-species-out + close-relative coverage; при низком RCI species-safe становится species-candidate/reference-limited. | Species-safe запрещен при RCI ниже порога или неизвестной полноте. |
| P0-8. Genome-wide overclaim | Фраза “расшифровка всех участков геномов” может звучать как полная биологическая интерпретация. | Научно уязвимо и ударит по доверию. | Переименовать в Genome Segment Evidence Graph: annotation, function hints, taxonomic signal, uncertainty, not final truth. | В продукте есть “do not claim” guardrails для genome segments. |
| P0-9. External database provenance | Если версия базы/параметры не сохранены, вывод не воспроизводим. | Через обновление NCBI/BOLD/GBIF тот же sequence даст другой результат. | ReferenceManifest + run.json + checksum + parameters + database snapshot/hash. | Evidence Pack позволяет повторить/объяснить решение спустя время. |
| P0-10. No real negative/no-match stress suite | Демонстрационный batch сбалансирован, но не содержит достаточно плохих/обманных кейсов. | Система может хорошо проходить ожидаемые сценарии и ломаться на реальных данных. | Добавить 100-record adversarial batch: no-match, chimeras, contamination, wrong taxonomy, short conserved fragments, HGT, NUMT, close relatives missing. | False species claim rate измеряется и публикуется. |
## 10. Стратегия валидации
Валидация должна доказать не то, что система часто выдает красивое имя, а то, что она редко делает опасный species overclaim и умеет честно сохранять полезную информацию на более высоком ранге. Главная метрика - false safe species rate, а не средний readiness score.
### 10.1. 100-record mixed batch v2

## Таблица 24

| Класс теста | Количество | Ожидаемый результат |
| --- | --- | --- |
| True species-safe positive controls | 15 | Species-safe только при полной цепочке gates. |
| Close sibling ambiguity | 15 | Downgrade to genus/family, no species export. |
| Weak coverage/short fragment | 10 | Weak/review, no species-safe. |
| No-match / novel lineage | 10 | No-match или higher-rank only, never forced species. |
| Reference missing competitor | 10 | Reference-limited caveat, species-safe blocked. |
| Contamination/control failure | 10 | Assay gate blocks publication. |
| Metadata blocked but taxonomy safe | 10 | Taxonomy safe, publication repair_required. |
| Wrong taxonomy/synonym conflict | 10 | Taxon resolver warning/review. |
| Genome segment non-barcode | 10 | Segment annotation, no barcode-style species claim unless profile allows. |
### 10.2. Validation metrics

## Таблица 25

| Metric | Формула/смысл | Цель |
| --- | --- | --- |
| False species-safe rate | Unsafe species claims / all species-safe claims by gold review | Должно стремиться к 0; критический KPI. |
| Downgrade correctness | Ambiguous cases correctly downgraded / all ambiguous cases | Проверяет LCA logic. |
| Repair precision | Repair actions that truly unlock export / suggested actions | Проверяет repair optimizer. |
| Reference-limited detection | Known missing-reference cases flagged / all hidden competitor cases | Проверяет RCI. |
| GBIF validation pass | Exports passing DwC/IPT/schema validation / all formal exports | Проверяет publication layer. |
| Reproducibility | Same input + same manifests -> same output hash | Проверяет auditability. |
| Claim explainability | Claims with full evidence path / all claims | Проверяет graph-backed claims. |
### 10.3. Validation protocol
Собрать gold reference set по 3-5 группам организмов: животные COI, fungi ITS, bacteria 16S, plants rbcL/matK, mixed eDNA ASV.
Для каждой группы создать profile_id с документированными порогами и источниками.
Провести leave-one-species-out и leave-one-genus-out тесты, чтобы измерить риск отсутствующих конкурентов.
Запустить adversarial batch с короткими фрагментами, chimeras, contamination, synonymy и HGT-подобными cases.
Отдать blind subset таксономисту или доменному эксперту: он не должен видеть ожидаемый bucket.
Сравнить compiler output с gold labels по метрикам выше.
Опубликовать validation report в Evidence Pack: не только successes, но и failure modes.
Зафиксировать пороги в marker_profile_registry и включить их в CI regression tests.
## 11. Данные, артефакты и Evidence Pack
Проект должен оцениваться по тому, какие файлы он отдает ревьюеру и издателю, а не только по экранной карточке. Evidence Pack - это научный продукт: он должен быть читаем человеком и машиной.

## Таблица 26

| Артефакт | Назначение | Обязательные поля/проверки |
| --- | --- | --- |
| sequence_safety_table.csv | Главная таблица решений по каждой последовательности. | decisionClass, safeTaxon, rank, identity, coverage, blockers, caveats. |
| safe_taxonomic_assignments.csv | Только поддержанные безопасные таксономические назначения. | acceptedScientificName, taxonRank, basis, profile_id. |
| review_taxonomic_hints.csv | Слабые/заблокированные записи для эксперта. | reason, candidates, recommended review action. |
| publication_blockers.csv | Field/gate блокеры публикации. | blocker.kind, severity, field, action, unlockable. |
| repair_plan.csv | Ранжированный список ремонтов. | repairAction, unlockableRecords, cost, examples. |
| reference_gap_index.csv | Пробелы референсных библиотек. | marker, clade, RCI components, close-relative coverage. |
| diagnostic_kmer_report.csv | Поддержка уникальными k-mers. | k, support_count, empirical FPR. |
| claim_boundaries.csv | Что можно и нельзя утверждать. | supportedClaim, unsupportedClaim, reason. |
| evidence_graph.json | Полный graph для машинной проверки. | nodes, edges, checksums, provenance. |
| dwc_occurrence_core_publishable.csv | Candidate occurrence export. | Only rows with supported publishable state, not necessarily formal GBIF-ready. |
| dna_derived_extension_publishable.csv | Molecular extension export. | Sequence/marker/method fields linked to core records. |
| methods_text.md + citations.md | Текст для публикации и ревью. | Versioned methods, sources, database versions. |
| source_provenance_manifest.json | Воспроизводимость запуска. | Input hashes, ref database versions, parameters, runtime. |
## 12. Дорожная карта

## Таблица 27

| Период | Цель | Конкретные задачи | Результат |
| --- | --- | --- | --- |
| 0-2 недели / P0 | Снять риск неверных claims и счетчиков | DataAccountingLedger; state machine; explicit GBIF-ready vs publishable_candidate; graph-backed claim text; blocker taxonomy; reference/run manifests. | Интерфейс и отчеты больше не завышают готовность. |
| 2-6 недель / P0-P1 | Сделать методологию валидируемой | marker_profile_registry; threshold provenance; RCI 2.0 draft; adversarial 100 batch; CI regression tests. | Каждый species-safe имеет profile_id и валидационный контекст. |
| 6-12 недель / P1 | Укрепить научную защиту | Leave-one-out validation; empirical FPR for k-mers; bootstrap barcode gap; taxonomic synonym resolver; reviewer mode. | Можно показать рецензенту не только demos, но и failure-mode proof. |
| 3-6 месяцев / P2 | Molecular Evidence Graph v1 | Graph schema; graph storage; API query; fragment sharedness atlas; reference gap dashboard; repair optimizer v2. | Проект становится исследовательской платформой, а не только CSV compiler. |
| 6-12 месяцев / P3 | Genome Segment Evidence Graph | Segment ontology; multi-marker consensus; coding/noncoding rules; protein/ORF layer; metagenome contig/MAG adapter; function hints. | Появляется честная “расшифровка участков генома” как доказательная аннотация с uncertainty. |
| 12+ месяцев / P4 | Комьюнити и публикационная инфраструктура | Public validation datasets; DOI-ready reports; integrations with GBIF/IPT/MDT; curator dashboards; journal/reviewer templates. | Проект готов к внешнему научному использованию. |
## 13. UI/UX и пользовательские сценарии
UI должен быть не “дашбордом уверенности”, а cockpit решений. Главный вопрос пользователя: “Что я могу честно утверждать и что нужно исправить, чтобы опубликовать?”

## Таблица 28

| Пользователь | Вопрос | Что должен показать интерфейс |
| --- | --- | --- |
| eDNA / metabarcoding researcher | Какие ASV можно назвать видом? | Safe ranks, competitors, controls/replicate caveats, review queue. |
| Data publisher | Что блокирует GBIF? | Required vs recommended fields, exact repair actions, DwC templates. |
| GBIF node / data manager | Почему top-hit не всегда species? | Formula cards, LCA path, overclaim prevention proof. |
| Taxonomist | Где нужны новые reference sequences? | Reference Gap Index by marker/clade/region. |
| Lab team | Какие поля QC надо добавить? | Assay gate: primers, controls, replicates, SOP, contamination flags. |
| Reviewer / journal | Можно ли воспроизвести решение? | Evidence Pack, methods, citations, source provenance, graph export. |
### 13.1. Обязательные UI-состояния
Supported claim: что можно публиковать и на каком ранге.
Blocked claim: какой tempting overclaim был предотвращен.
Repair first: какие поля/методы добавить, чтобы запись стала пригодной.
Reference-limited: когда база не позволяет безопасный species claim.
Review only: когда запись полезна для эксперта, но не для автоматического экспорта.
Not a claim: явное предупреждение, что geography/GBIF context, protein sanity и read counts не являются самостоятельной species truth.
## 14. Операционная реализация
### 14.1. Backend contracts
POST /compile
input: sequences, hit tables or Sequence IDs, metadata, reference settings
output: run_id, status, evidence_pack_links
GET /runs/{run_id}
output: run status, counts ledger, decision summary, blocker summary
GET /runs/{run_id}/evidence-graph
output: graph JSON with nodes, edges, provenance
GET /runs/{run_id}/exports/{artifact}
output: CSV/JSON/HTML/ZIP artifact with checksum
POST /validate
input: evidence pack or run_id
output: schema validation, GBIF/DwC validation, claim proof checks
### 14.2. Storage recommendation
Object storage for Evidence Pack ZIPs and immutable run artifacts.
Relational database for run ledger, user jobs, export metadata and repair actions.
Graph database or RDF/JSON-LD layer for long-term Molecular Evidence Graph queries.
Versioned registry files for marker profiles, reference profiles, thresholds and validation reports.
Checksum every input and reference manifest to support reproducibility.
### 14.3. Security and ethics
Do not expose sensitive locality data for endangered taxa without controlled redaction.
Do not publish raw sequence material that violates repository/license/access constraints.
Do not infer phenotypes, traits or conservation status unless explicitly supported by curated external evidence.
Retain provenance so data originators and publishers receive credit through citation/DOI paths.
For human-associated samples, enforce privacy review and reject human-identifiable genomic content from biodiversity workflow.
## 15. Глоссарий

## Таблица 29

| Термин | Пояснение |
| --- | --- |
| ASV | Amplicon Sequence Variant: уникальная последовательность после denoising; лучше сохраняет исходный сигнал, чем грубо кластеризованный OTU. |
| Barcode | Короткий участок ДНК, который часто помогает отличать таксоны, но не всегда до вида. |
| BLAST/top hit | Лучшее найденное совпадение в базе; не равно автоматическому species claim. |
| Coverage | Какая доля query-фрагмента покрыта выравниванием. Высокий identity при малом coverage опасен. |
| Diagnostic k-mer | Короткое слово длины k в последовательности, которое поддерживает таксон и отсутствует у близких конкурентов в референсной базе. |
| DwC-A | Darwin Core Archive: пакет таблиц и метаданных для публикации биоразнообразия. |
| Evidence Pack | Набор CSV/JSON/HTML/MD/ZIP файлов, позволяющий проверить решения системы. |
| LCA | Lowest Common Ancestor: самый узкий общий таксон для набора неразделимых кандидатов. |
| Marker profile | Правила для конкретного маркера: длина, identity/coverage thresholds, допустимые claims, validation evidence. |
| No-match | Нет надежного совпадения; это не доказательство отсутствия вида. |
| RCI | Reference Completeness Index: оценка риска, что близкие таксоны отсутствуют или плохо представлены в референсах. |
| SafeTaxon | Самый узкий таксон, который поддержан evidence и не разрушен конкурентами, неполнотой базы или hard blockers. |
| Species-safe | Состояние, в котором species claim разрешен только после прохождения hard gates. |
| Weak | Сигнал ниже порога надежности; обычно review/repair, а не публикация. |
## 16. Источники и нормативная база
Внутренние материалы проекта: загруженные скриншоты интерфейса EcoGenesis Molecular Evidence Conversion & Repair Engine for GBIF, вкладки Judge overview, Run compiler, Fragment graph, Visual lecture, Research audit, Math & proof; пакет competition-100-sequences.zip с 100-sequence evidence pack, CSV/JSON/HTML артефактами и отчетом запуска.
Внешняя нормативная база, использованная для проектной привязки:

## Таблица 30

| Источник | Как используется в проекте |
| --- | --- |
| GBIF Secretariat / DNA-derived data guide | Publishing DNA-derived data through biodiversity data platforms, version 1.3.3, 27 Feb 2025. Важные принципы: DNA-derived occurrence data должны быть стандартизованы и воспроизводимы; для DNA-derived datasets рекомендована Occurrence core + DNA derived data extension; sequence/ASV является объективным handle для будущей переинтерпретации. |
| Darwin Core / TDWG | Darwin Core terms and quick reference: стандартные поля для occurrence, event, taxon, materialSampleID, scientificName, basisOfRecord и связанных сущностей. |
| GBIF / DwC-A model | Darwin Core Archive как star schema: core table + extension tables + metadata; важен для publication exports и GBIF/IPT совместимости. |
| MIxS / GSC, MIQE, GGBN | Семейство стандартов и рекомендаций для молекулярных, лабораторных и sample metadata, используемых в DNA-derived extension. |
