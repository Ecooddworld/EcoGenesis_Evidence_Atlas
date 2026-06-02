# EcoGenesis Nexus V3 — полный улучшенный проект



<!-- README.md -->

# EcoGenesis Nexus V3

## DNA-to-Taxon Evidence Engine for GBIF

EcoGenesis Nexus V3 is a conservative molecular evidence engine for DNA-derived biodiversity data. It receives raw FASTA sequences, ASVs, barcode hits or upstream matcher outputs and converts them into:

- safest taxonomic claim: species / genus / higher-rank / review / no-match
- GBIF publication readiness
- Darwin Core Occurrence export
- DNA-derived extension export
- repair plan
- reference gap report
- evidence passport
- validation audit

The project does **not** claim that a top DNA hit is automatically a species occurrence. It asks a safer question:

```text
What is the deepest taxonomic claim that the sequence, reference evidence,
assay/process context and GBIF metadata can support without overclaiming?
```

## What changed in V3

Compared with the previous Nexus draft, V3 adds:

```text
1. source metadata preserved in EvidencePassport
2. real occurrenceID/eventDate/coordinates used in DwC exports
3. gbif-ready export split from review/repair export
4. dataset metadata support in CLI
5. hard-gate audit
6. naive top-hit overclaim report
7. leave-one-out reference validation
8. operational confidence indicator that does not unlock species by itself
9. external tool adapter matrix
10. stronger scientific documentation and benchmark protocol
11. improved visual dashboard mockup
```

## Run the demo

```bash
python -m src.ecogenesis_nexus.cli \
  --reference examples/reference_mini.fasta \
  --query examples/query_sequences.fasta \
  --metadata examples/metadata.csv \
  --dataset-metadata examples/dataset_metadata.json \
  --out reports/demo_nexus_v3 \
  --run-validation
```

Expected summary:

```text
processed_records: 4
species_safe: 2
genus_safe: 1
gbif_ready_safe: 2
hard_gate_failures: 0
naive_species_overclaims_prevented: 1
leave_one_out_false_species_exports: 0
```

## Main outputs

```text
reports/demo_nexus_v3/
├── sequence_decisions.csv
├── evidence_passports.jsonl
├── dwc_occurrence_core.csv
├── dwc_occurrence_core_gbif_ready.csv
├── dwc_occurrence_core_review_or_repair.csv
├── dna_derived_extension.csv
├── dna_derived_extension_gbif_ready.csv
├── repair_plan.csv
├── metadata_bottlenecks.csv
├── reference_gap_index.csv
├── evidence_graph.json
├── hard_gate_audit.csv
├── naive_top_hit_overclaims.csv
├── leave_one_out_reference_validation.csv
├── scientific_validation_summary.json
├── scientific_validation_report.md
├── external_tool_adapter_matrix.csv
└── report.html
```

## Core formulas

```text
AmbiguousSet(q) = {h_j : d_j - d_1 <= z * sqrt(SE_1^2 + SE_j^2)}
SafeTaxon(q) = LCA(taxa in AmbiguousSet(q))
```

```text
SpeciesEvidencePass(q) =
  ExactMatchPass(q)
  AND SafeTaxon(q).rank = species
  AND AmbiguityResolved(q)
  AND ReferenceSupportPass(q)
  AND ProcessSupportPass(q)
```

```text
ReferenceSupportPass(q) =
  BarcodeGapPass(q)
  OR DiagnosticKmerPass(q)
  OR CuratedReferenceSingletonPass(q)
  OR AssaySpecificityPass(q)
  OR PhylogeneticPlacementPass(q)
```

```text
GBIFReady(q) =
  ClaimAllowed(q)
  AND DarwinCoreCorePass(q)
  AND DNAExtensionPass(q)
  AND DatasetMetadataPass(q)
```

See `docs/FORMULAS_V3_RU.md` for the full formula catalogue.

## Scientific position

Safe statement:

> EcoGenesis Nexus helps GBIF publish more DNA-derived biodiversity evidence without publishing more unsafe species-level claims.

Unsafe statement:

> EcoGenesis identifies all sequences to species.

## Documentation

- `docs/SCIENTIFIC_REALITY_AUDIT_RU.md`
- `docs/FORMULAS_V3_RU.md`
- `docs/TOOLS_STACK_RU.md`
- `docs/BENCHMARK_PROTOCOL_RU.md`
- `docs/GBIF_WINNING_STRATEGY_RU.md`
- `web/nexus_v3_dashboard.html`

## Production adapter direction

The pure-Python matcher is only a small transparent prototype. For large production data, keep the EvidencePassport and hard gates, but plug in:

```text
GBIF Sequence ID
BLAST+
VSEARCH
DADA2 / QIIME 2
Kraken2 / Bracken
sourmash / Mash
MAFFT + IQ-TREE / EPA-ng
Cutadapt / fastp
```

EcoGenesis should normalize their outputs into one contract and decide safe GBIF claims.


---



<!-- docs/SCIENTIFIC_REALITY_AUDIT_RU.md -->

# EcoGenesis Nexus V3 — научная перепроверка реальности

## Вывод

V3 — более сильная и более честная версия, чем простая “barcode-to-GBIF проверялка”. Но это не магический определитель видов. Научно защищаемое ядро проекта такое:

> EcoGenesis Nexus не обещает абсолютную истину о виде. Он вычисляет самый безопасный публикуемый таксономический ранг и показывает, какие доказательства или метаданные нужны, чтобы запись стала GBIF-ready.

Это реалистичная и выигрышная позиция, потому что она совпадает с реальными проблемами GBIF: sequence-based search, continuous taxonomic reinterpretation, reference library catalogue, scalable DNA-derived publishing pipelines, metadata quality and FAIR reuse.

## Что было проверено на текущей реализации

Я прогнал локальный прототип на synthetic reference/query set и включил новый `--run-validation` режим.

Результат демонстрационного прогона:

```text
processed_records: 4
species_safe: 2
genus_safe: 1
gbif_ready_safe: 2
OPR_overclaim_prevention_rate: 0.333333
hard_gate_failures: 0
naive_species_overclaims_prevented: 1
leave_one_out_false_species_exports: 0
```

Интерпретация:

- 2 записи стали GBIF-ready безопасными occurrence records.
- 1 запись была намеренно понижена с top-hit species до genus, потому что участок не различает конкурирующие виды.
- 1 запись осталась repairable/no-match.
- При leave-one-out тесте удаление истинного reference record не привело к ложному species export.
- Внутренние hard gates не нарушены.

## Научно сильная часть

### 1. Отделение taxonomic evidence от publication readiness

Это главный сильный ход. Видовой top hit может быть биологически интересен, но не должен автоматически становиться GBIF occurrence. В V3 движок отдельно считает:

```text
TaxonomicDecision(q)
PublicationDecision(q)
ClaimAllowed(q)
RepairActions(q)
```

### 2. LCA вместо копирования top hit

Если несколько видов статистически неотличимы по участку, EcoGenesis публикует безопасный общий ранг:

```text
SafeTaxon(q) = LCA(AmbiguousSet(q))
```

Это лучше для GBIF, чем ложная точность.

### 3. Reference support как отдельный слой

Видовой output разрешен только при независимой поддержке:

```text
ReferenceSupportPass =
  BarcodeGapPass
  OR DiagnosticKmerPass
  OR CuratedReferenceSingletonPass
  OR AssaySpecificityPass
  OR PhylogeneticPlacementPass
```

То есть exact identity сам по себе не дает species claim.

### 4. Repair optimizer

Проект говорит не только “ошибка”, а “какое исправление разблокирует максимум записей”. Это делает его полезным для publishers, GBIF nodes и лабораторий.

### 5. Evidence Passport

Каждая запись получает машинно-читаемый паспорт: hits, safe taxon, blockers, repairs, metadata readiness, confidence, segment atlas, export status.

## Что было слабым и исправлено в V3

### Проблема 1 — в прежнем demo не было GBIF-ready records

Причина: dataset metadata не были переданы в CLI, поэтому записи оставались `record_ready_dataset_incomplete`.

Исправление: добавлен `--dataset-metadata` и `--demo-dataset-metadata`.

### Проблема 2 — exports не использовали исходные occurrence metadata

Исправление: EvidencePassport теперь хранит `source_metadata`, а DwC/DNA export использует реальные `occurrenceID`, `eventDate`, координаты, target gene, reference database/version.

### Проблема 3 — не было формального validation output

Исправление: добавлен `validation.py` и файлы:

```text
hard_gate_audit.csv
naive_top_hit_overclaims.csv
leave_one_out_reference_validation.csv
scientific_validation_summary.json
scientific_validation_report.md
```

### Проблема 4 — не было карты внешних инструментов

Исправление: добавлен `tool_adapters.py` и `external_tool_adapter_matrix.csv`.

### Проблема 5 — confidence мог бы звучать как “истина”

Исправление: confidence в V3 называется `posterior_like_confidence` и явно не используется как gate. Species claim все равно требует hard evidence gates.

## Что все еще нельзя утверждать

Нельзя писать:

> EcoGenesis reliably identifies every DNA sequence to species.

Нужно писать:

> EcoGenesis converts DNA-derived evidence into the safest defensible GBIF publication claim, with transparent blockers and repairs.

Нельзя писать:

> Absence is inferred from no reads.

Нужно писать:

> Absence claims are blocked by default unless targeted assay controls, detection limit, sampling effort and replicate rules pass.

Нельзя писать:

> Reference gap equals species absence.

Нужно писать:

> Reference gap means the available library cannot support the claim at the requested rank.

## Следующая реальная проверка на больших данных

Для production-grade claims нужен benchmark на настоящих reference snapshots:

1. GBIF Sequence ID/BOLD COI animal snapshot.
2. UNITE ITS fungi snapshot.
3. SILVA/GTDB 16S/18S microbial/eukaryotic snapshot.
4. Mock communities with known composition.
5. Leave-one-species-out and leave-one-genus-out tests.
6. Negative control and contamination injection tests.
7. Cross-marker agreement tests.
8. Published GBIF DNA-derived datasets replay.

## Конкурсный вывод

V3 теперь ближе к выигрышной версии: это не просто UI и не просто формулы, а проверяемый workflow, который:

- работает на локальном примере;
- генерирует GBIF-ready and review exports;
- показывает, где naive top-hit дал бы overclaim;
- проверяет hard gates;
- готов к подключению внешних production matchers;
- совпадает с направлением GBIF DNA/eDNA infrastructure.


---



<!-- docs/FORMULAS_V3_RU.md -->

# EcoGenesis Nexus V3 — новые формулы и функции

## 1. Evidence state

Для каждой записи `q`:

```text
E(q) = {
  QC(q),
  CandidateHits(q),
  AmbiguousSet(q),
  SafeTaxon(q),
  ReferenceSupport(q),
  ProcessSupport(q),
  PublicationReadiness(q),
  RepairActions(q)
}
```

Главная функция:

```text
Decision(q) = argmax safe useful claim under hard gates
```

Не `argmax species score`, а максимальный безопасный claim.

## 2. Sequence QC

```text
valid_fraction(q) = count(base in IUPAC_DNA) / length(q)
N_rate(q) = count(N) / length(q)
H(q) = -Σ_b p_b log2(p_b)
H_norm(q) = H(q) / log2(4)
```

```text
QC_pass(q) =
  L_min(marker) <= length(q) <= L_max(marker)
  AND N_rate(q) <= N_max(marker)
  AND valid_fraction(q) >= 0.995
```

## 3. Candidate retrieval

```text
K(q) = set of canonical unambiguous k-mers in q
J(q,r) = |K(q) ∩ K(r)| / |K(q) ∪ K(r)|
C(q,r) = |K(q) ∩ K(r)| / |K(q)|
RetrievalScore(q,r) = w_J J(q,r) + w_C C(q,r) + w_M MinimizerContainment(q,r)
```

Production adapters may replace this with BLAST/VSEARCH/MMseqs2/Kraken2, but output must normalize into the same `MatchHit` contract.

## 4. Alignment metrics

```text
identity(q,r) = matches / aligned_positions
queryCoverage(q,r) = aligned_query_bases / length(q)
targetCoverage(q,r) = aligned_reference_bases / length(r)
d(q,r) = 1 - identity(q,r)
SE(q,r) = sqrt(d(q,r) * (1 - d(q,r)) / aligned_length(q,r))
```

## 5. Ambiguity set and safe LCA

```text
h_j indistinguishable from h_1 iff:
  d_j - d_1 <= z * sqrt(SE_1^2 + SE_j^2)
```

Default:

```text
z = 1.96
```

```text
AmbiguousSet(q) = {h_j : h_j indistinguishable from top hit h_1}
SafeTaxon(q) = LCA(taxa in AmbiguousSet(q))
```

## 6. Match classes

```text
exact = identity >= 99% AND queryCoverage >= 80%
ambiguous = exact AND conflicting equally good taxonomy exists
close = 90% < identity < 99% AND queryCoverage >= 80%
weak = identity < 90% OR queryCoverage < 80%
no_match = no hit
```

## 7. Species gate

```text
SpeciesEvidencePass(q) =
  ExactMatchPass(q)
  AND SafeTaxon(q).rank = species
  AND AmbiguityResolved(q)
  AND ReferenceSupportPass(q)
  AND ProcessSupportPass(q)
```

```text
ReferenceSupportPass(q) =
  BarcodeGapPass(q)
  OR DiagnosticKmerPass(q)
  OR CuratedReferenceSingletonPass(q)
  OR AssaySpecificityPass(q)
  OR PhylogeneticPlacementPass(q)
```

## 8. Barcode gap

```text
barcode_gap(t) = inter_min_distance(t) - intra_max_distance(t)
BarcodeGapPass(t) = barcode_gap(t) > 0
BarcodeGapStrength(t) = max(0, barcode_gap(t)) / max(inter_min_distance(t), ε)
```

## 9. Diagnostic k-mer evidence

```text
D_k(t) = k-mers present in taxon t and absent outside the comparison scope
support(q,t) = |K(q) ∩ D_k(t)|
query_window_count = |K(q)|
p_false_positive = 1 - (1 - |D_k(t)| / 4^k) ^ query_window_count
```

```text
DiagnosticKmerPass(q,t) =
  support(q,t) >= s_min(marker, assay)
  AND p_false_positive <= α
```

## 10. Operational confidence — not a gate

V3 adds transparent decision-support confidence:

```text
AlignmentComponent = identity * queryCoverage
MarginComponent = sigmoid(λ * (ScoreMarginRatio - τ_margin))
AmbiguityPenalty = 1 / max(1, number_of_ambiguous_species)
ReferenceComponent = 1 if independent reference support else 0.55
QCComponent = 1 if QC_pass else 0.2
MetadataComponent = 1 if gbif_ready else 0.7 or 0.35
```

```text
C_operational(q) =
  AlignmentComponent
  * MarginComponent
  * AmbiguityPenalty
  * ReferenceComponent
  * QCComponent
  * MetadataComponent
```

Important:

```text
C_operational(q) cannot unlock species output by itself.
```

## 11. Ensemble support from external tools

For tool `m` and taxon `t`:

```text
S_m(q,t) in [0,1]
Cal_m(S_m) = P(correct at rank r | score bin, marker, clade, database version)
WeightedSupport(q,t) = Σ_m w_m * Cal_m(S_m(q,t))
```

Discordance:

```text
ToolTaxonDistribution(q) = normalized support over taxa
H_tools(q) = -Σ_t p_t log(p_t)
DiscordancePenalty(q) = 1 - H_tools(q) / log(number_of_candidate_taxa)
```

Consensus gate:

```text
EnsembleSupportPass(q,t) =
  WeightedSupport(q,t) >= τ_rank(marker, clade)
  AND DiscordancePenalty(q) >= δ
```

This can support review priority or reference support, but species export still needs LCA and hard gates.

## 12. Segment atlas

For a window `w = q[i:j]`:

```text
T(w) = {taxa with supported hits/k-mers in window w}
SafeTaxon(w) = LCA(T(w))
DiagnosticDensity(w,t) = |K(w) ∩ D_k(t)| / |K(w)|
ConservationScore(w) = number_of_taxa_covering_w / total_candidate_taxa
```

Classification:

```text
diagnostic_species_or_genus if DiagnosticDensity >= τ_diag
conserved_clade if ConservationScore >= τ_conserved
low_information if |K(w)| = 0 or entropy low
mixed_information otherwise
```

## 13. eDNA sample-level presence model

For sample `s`, taxon `t`, replicate `r`:

```text
read_rate(s,t,r) = reads(s,t,r) / total_reads(s,r)
neg95(t) = 95th percentile negative-control read_rate for t
control_adjusted_rate(s,t,r) = max(0, read_rate(s,t,r) - neg95(t))
```

```text
ReplicatePass(s,t) = count_r(control_adjusted_rate(s,t,r) >= τ_reads) >= R_min
```

```text
DetectionProbability(s,t) = 1 - Π_r (1 - p_detect(s,t,r))
```

```text
PresenceClaimAllowed(s,t) =
  SafeTaxonPass(t)
  AND controls_pass
  AND ReplicatePass(s,t)
  AND contamination_flag = false
```

## 14. qPCR/ddPCR targeted assay gate

```text
AssaySupportPass =
  primer_specificity_pass
  AND positive_controls_pass
  AND negative_controls_pass
  AND extraction_blanks_pass
  AND replicate_rule_pass
  AND LOD_reported
```

```text
AbsenceClaimAllowed =
  targeted_assay
  AND occurrenceStatus = absent
  AND AssaySupportPass
  AND detection_limit_reported
  AND sampling_effort_reported
  AND inhibition_check_pass
```

Default:

```text
Metabarcoding no-read result != absence
```

## 15. Novel / unnamed molecular unit

When no named species is safe but sequences cluster reproducibly:

```text
MOTU_cluster(q) = connected component under distance <= τ_marker
MOTU_ID = marker + ":" + MD5(centroid_sequence)
NearestNamedParent = LCA(nearest supported named taxa)
```

Publishable claim:

```text
scientificName = NearestNamedParent
verbatimIdentification = MOTU_ID
identificationRemarks = molecular unit; no safe named species claim
```

## 16. Repair optimizer

```text
B(q) = set of blockers for q
Unlock(a) = {q : action a removes at least one blocker and all remaining gates pass}
RepairGain(a) = Σ_q UsefulWeight(q) / Cost(a), q in Unlock(a)
```

Top-k planning:

```text
BestRepairs(k) = argmax_{A', |A'| <= k} |∪_{a in A'} Unlock(a)|
```

## 17. Reference Gap Index

```text
RGI(taxon, marker, region) =
  N_records_blocked_by_reference_evidence / N_records_with_top_hit
```

Add quality dimensions:

```text
VoucherCoverage(t,m) = species_with_vouchered_refs / known_species_in_scope
GeoCoverage(t,m,g) = refs_from_region_g / expected_taxa_region_g
VersionDrift(t,m) = disagreement(new_snapshot, old_snapshot)
```

## 18. Validation metrics

```text
HardGateFailureRate = hard_gate_failures / N
NaiveOverclaimPreventionRate = prevented_naive_species_overclaims / top_species_cases
LOOFalseSpeciesRate = false_species_exports_after_self_removed / LOO_cases
```

A strong demo should show:

```text
HardGateFailureRate = 0
LOOFalseSpeciesRate = 0
NaiveOverclaimPreventionRate > 0 on ambiguous test cases
```


---



<!-- docs/TOOLS_STACK_RU.md -->

# EcoGenesis Nexus V3 — какие инструменты наложить сверху

EcoGenesis должен быть не заменой BLAST/QIIME/GBIF, а orchestration layer. Лучший вариант — сделать “federated evidence engine”: разные инструменты дают сигналы, а EcoGenesis нормализует их в Evidence Passport и решает, какой claim можно публиковать.

## 1. Upstream preprocessing

### Cutadapt / fastp

Роль: trimming primers/adapters, read QC.

Зачем: неправильные праймеры и адаптеры ломают downstream identity/coverage.

Выход в EcoGenesis:

```text
primer_forward, primer_reverse, trim_status, mean_quality, read_length_distribution
```

## 2. ASV / OTU generation

### DADA2

Роль: inference of exact amplicon sequence variants from Illumina reads.

Выход:

```text
ASV sequence, ASV table, chimera flags, denoising parameters
```

EcoGenesis использует ASV как объективный sequence handle, но не считает ASV автоматически видом.

### QIIME 2

Роль: reproducible pipeline/provenance layer.

Выход:

```text
representative sequences, feature table, taxonomy table, provenance
```

EcoGenesis должен импортировать QIIME 2 artifacts или TSV exports.

### VSEARCH

Роль: high-throughput dereplication, clustering, search.

Выход:

```text
centroids, clusters, identity tables, chimera checks
```

## 3. Candidate matching

### GBIF Sequence ID

Роль: GBIF-native exact/ambiguous/close/weak match context.

EcoGenesis добавляет поверх него:

```text
safe LCA, publication readiness, repair queue, DwC/DNA export
```

### BLAST+

Роль: transparent alignment against frozen reference snapshots.

EcoGenesis требует:

```text
reference snapshot manifest, database version, query coverage, identity, e-value, bit score
```

### MMseqs2 / minimap2

Роль: speed at scale for huge sequence volumes.

Применение: when millions of sequences or long contigs are processed.

## 4. k-mer / LCA classifiers

### Kraken2 / Bracken

Роль: fast k-mer/LCA signal and abundance estimates.

EcoGenesis uses it as ensemble evidence, not as sole species gate.

### sourmash / Mash

Роль: sketching and fast similarity screening.

Useful for huge references, metagenomic bins, near-duplicate detection and dataset-level search.

## 5. Reference library layer

### BOLD / GBIF reference library catalogue

Роль: animal COI and broader barcode references.

Need:

```text
voucher status, license, taxonomic scope, target gene, version, citation
```

### UNITE

Роль: fungal ITS species hypotheses and curated ITS references.

EcoGenesis must support species hypotheses / molecular units, not only Latin binomials.

### SILVA / PR2 / GTDB

Роль: 16S/18S/prokaryotic/eukaryotic references.

EcoGenesis must use marker/clade-specific thresholds.

## 6. Phylogenetic confirmation

### MAFFT + IQ-TREE / FastTree / EPA-ng

Роль: tree placement when top-hit similarity is insufficient.

EcoGenesis can unlock `phylogenetic_placement` support when:

```text
placement_likelihood >= τ
branch_distance <= β
sister_clade_support >= σ
```

## 7. Contamination and replicate checks

### decontam-style logic

Роль: identify contaminants from negative controls and prevalence/frequency patterns.

EcoGenesis should export:

```text
contamination_flag, negative_control_read_rate, adjusted_read_rate
```

## 8. Standards and publishing

### Darwin Core / DNA-derived extension / MIxS / MIQE

Роль: metadata completeness, reproducibility and publication safety.

EcoGenesis maps lab evidence to biodiversity data terms.

## 9. Visual layer

Must include:

```text
1. sequence-to-taxon Sankey
2. ambiguity/LCA tree
3. reference gap heatmap
4. repair gain board
5. per-sequence evidence passport
6. segment atlas along the sequence
7. GBIF export readiness cards
8. validation report page
```

## 10. Winning architecture

```text
Raw reads / ASVs / barcodes
→ preprocessing adapters
→ candidate match adapters
→ normalized MatchHit table
→ hard safety gates
→ ensemble confidence only for review priority
→ evidence passport
→ validation audit
→ GBIF-ready export
→ reference gap and repair dashboard
```


---



<!-- docs/BENCHMARK_PROTOCOL_RU.md -->

# EcoGenesis Nexus V3 — протокол реальной проверки

## Цель

Доказать не “мы идеально определяем виды”, а более сильное и честное:

> EcoGenesis уменьшает unsafe species-level overclaims и увеличивает количество safely publishable GBIF-ready DNA-derived records.

## Benchmark A — synthetic failure modes

Минимальный набор:

1. exact species, full metadata → species_safe + gbif_ready
2. exact but shared by two species → genus_safe + gbif_ready
3. exact species but missing eventDate/occurrenceID → species_safe + repairable_metadata
4. weak identity/coverage → weak/no public claim
5. no reference → no_match
6. negative control contaminant → blocked assay/process
7. qPCR absent with no LOD → absence blocked

Expected:

```text
HardGateFailureRate = 0
NaiveOverclaimPreventionRate > 0
```

## Benchmark B — leave-one-out reference test

Для каждого reference record:

```text
1. remove reference r_i from DB
2. run sequence(r_i) as query
3. check whether engine exports wrong species
```

Metric:

```text
LOOFalseSpeciesRate = false_species_exports / tested_references
```

Target:

```text
LOOFalseSpeciesRate = 0 under conservative gates
```

## Benchmark C — leave-one-species-out

Удалить все reference sequences of true species.

Expected:

```text
species claim should be blocked or downgraded to genus/family/no_match
```

This tests reference-library incompleteness.

## Benchmark D — mock community

Use known mock community sequences and compare:

```text
true positives at safe rank
false species exports
false genus exports
blocked useful records
repairable records
```

Metrics:

```text
Precision_species_safe = true_species_safe / exported_species_safe
Recall_safe_rank = records_safe_at_any_rank / known_present_taxa
OverclaimRate = false_species_exports / top_species_hits
```

## Benchmark E — reference version drift

Run same queries against two frozen reference versions:

```text
VersionDrift(q) = Decision_v2(q) != Decision_v1(q)
```

Important exports:

```text
reference_manifest.json
reference_database
reference_version
citation
```

## Benchmark F — controls and contamination

Inject low-level reads into negative controls.

Expected:

```text
PresenceClaimAllowed = false unless adjusted read rate and replicate rule pass
```

## Benchmark G — GBIF replay

Take already published DNA-derived GBIF datasets, re-run the evidence compiler, and report:

```text
records already GBIF-ready
records with missing DNA extension fields
records with taxonomic overclaim risk
records repairable by metadata
reference gaps by marker/taxon/region
```

## Current V3 demo validation

The bundled demo writes:

```text
reports/demo_nexus_v3/scientific_validation_summary.json
reports/demo_nexus_v3/hard_gate_audit.csv
reports/demo_nexus_v3/leave_one_out_reference_validation.csv
reports/demo_nexus_v3/naive_top_hit_overclaims.csv
```

Run:

```bash
python -m src.ecogenesis_nexus.cli \
  --reference examples/reference_mini.fasta \
  --query examples/query_sequences.fasta \
  --metadata examples/metadata.csv \
  --dataset-metadata examples/dataset_metadata.json \
  --out reports/demo_nexus_v3 \
  --run-validation
```


---



<!-- docs/GBIF_WINNING_STRATEGY_RU.md -->

# EcoGenesis Nexus V3 — выигрышная стратегия для GBIF Ebbe Nielsen Challenge

## Главный pitch

> EcoGenesis Nexus is a conservative DNA-to-GBIF evidence engine that turns raw sequences, ASVs, barcode hits and Sequence ID results into safe taxonomic claims, explicit uncertainty, repair actions and GBIF-ready Darwin Core / DNA-derived exports.

## Почему это полезно именно GBIF

GBIF сейчас двигается в сторону sequence-based occurrence search, taxonomic reinterpretation, reference library catalogue, DNA-derived data publishing pipelines and eDNA integration. EcoGenesis закрывает “предпубликационный разрыв”: до того, как запись попадет в GBIF, он показывает, можно ли ее публиковать как species, надо ли понизить до genus/family, или нужно исправить metadata/reference/process evidence.

## Критерии конкурса и ответ проекта

### Applicability

Пользователи:

```text
GBIF nodes
DNA/eDNA publishers
molecular monitoring projects
reference library curators
labs with barcode/metabarcoding outputs
```

### Benefit for GBIF network

```text
more GBIF-ready DNA-derived records
fewer unsafe species-level claims
clear repair queue for publishers
reference gap intelligence for library builders
standardized Darwin Core / DNA-derived exports
```

### Innovation

Новизна не в том, что мы делаем BLAST. Новизна в том, что мы превращаем molecular match output into safe publication decisions and repair optimization.

### Quality of implementation

V3 already has:

```text
working pure-Python prototype
CLI
FASTA + metadata import
k-mer retrieval
local alignment fallback
safe LCA
reference support gates
GBIF readiness
exports
validation audit
adapter matrix
visual dashboard mockup
```

## Что показать в видео

1. Загрузить FASTA + metadata.
2. Показать, что exact top hit может быть downgraded to genus.
3. Показать `gbif_ready_safe = 2`.
4. Открыть `naive_top_hit_overclaims.csv`.
5. Открыть `dwc_occurrence_core_gbif_ready.csv`.
6. Открыть `leave_one_out_reference_validation.csv`.
7. Завершить фразой:

> EcoGenesis helps GBIF publish more DNA-derived biodiversity evidence without publishing more unsafe species claims.
