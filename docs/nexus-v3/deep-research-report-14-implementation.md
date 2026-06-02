# Deep Research Report 14: что принято в EcoGenesis Nexus V3

Дата внедрения: 2026-06-02.

## Главный вывод

Свежий анализ принят как усиление проекта: EcoGenesis теперь позиционируется не как универсальный score и не как "определитель вида", а как **DNA-to-Taxon Evidence Router** и слой безопасности публикации для GBIF-ready molecular occurrence evidence.

Практически это означает:

- разные маркеры проходят разные профили;
- qPCR/ddPCR, eDNA/metabarcoding и single-specimen barcode больше не смешиваются в один workflow;
- DNA-derived metadata проверяется отдельно от обычного Darwin Core Occurrence core;
- species-safe остается fail-closed решением: если профиль маркера, assay gate или публикационные поля не проходят, species export блокируется или понижается.

## Что реализовано

### 1. Marker profiles

Добавлен backend-модуль `backend/app/barcode/profiles.py`:

- `coi_full_barcode`
- `coi_mini_barcode`
- `its_fungi`
- `s16_full_or_near_full`
- `s16_short_amplicon`
- `custom_research`

Ключевое изменение: короткий 16S amplicon не может автоматически стать species-level publication claim. Он маршрутизируется в safe-rank review.

### 2. Assay profiles

Добавлены assay gates:

- `single_specimen_barcode`
- `metabarcoding`
- `qpcr_ddpcr`
- `custom_targeted`
- `unknown`

Для qPCR/ddPCR `occurrenceStatus`, `contaminationAssessment` и `methodOrSOP` являются publication-blocking required fields. Это защищает targeted detections от публикации без контрольного слоя.

### 3. DNA-derived readiness

Добавлена проверка high-priority DNA-derived fields:

```text
eventID
materialSampleID
DNA_sequence
target_gene
target_subfragment
pcr_primer_forward
pcr_primer_reverse
seq_meth
otu_class_appr
otu_seq_comp_appr
otu_db
sop
```

Эти поля не всегда блокируют taxonomic decision, но попадают в repair actions и отдельный export.

### 4. Новые exports

В Evidence Pack добавлены:

```text
marker_profile_audit.csv
assay_gate_audit.csv
dna_extension_readiness.csv
repair_gain_estimates.csv
```

HTML report теперь показывает отдельную таблицу marker/assay/DNA-derived readiness.

### 5. UX/UI

В Workbench добавлена панель **Marker and assay gates**:

- какие marker profiles применились;
- какие assay types найдены;
- сколько records имеют complete DNA-derived high-priority metadata;
- сколько records переведены в safe-rank review из-за профиля маркера;
- какие DNA-extension поля нужно добавить.

### 6. Tests

Добавлены regression tests:

- short 16S marker profile forces safe-rank review;
- qPCR/ddPCR missing controls blocks publication;
- new marker/assay/DNA exports are created and included in ZIP.

## Что это решает

1. Проект больше не выглядит как произвольный универсальный score.
2. Species-safe теперь зависит не только от top hit, но и от marker profile.
3. qPCR/ddPCR targeted detections не публикуются без control/contamination metadata.
4. DNA-derived extension становится явной repair surface, а не скрытой частью отчета.
5. Пользователь видит, почему запись publishable, review-only или blocked.

## Что остается будущим слоем

- полноценный reference completeness gate по clade/marker;
- protein sanity gate: frame, stop codons, frameshift, NUMT/pseudogene warnings;
- calibration benchmark на BOLD/UNITE/SILVA/real GBIF DNA-derived examples;
- fragment sharedness atlas;
- Molecular Evidence Graph с taxon, fragment, geography, protein/domain и claim nodes.

## Проверенные источники GBIF

- GBIF Sequence ID: https://www.gbif.org/tools/sequence-id
- Publishing DNA-derived data through biodiversity data platforms: https://docs.gbif.org/publishing-dna-derived-data/en/
- Data quality requirements: Occurrence datasets: https://www.gbif.org/data-quality-requirements-occurrences
- 2026 GBIF Ebbe Nielsen Challenge rules: https://www.gbif.org/awards/ebbe-2026-rules
