# EcoGenesis Nexus — визуальная и UX-доработка

## 1. Визуальная идея

Проект должен выглядеть не как форма загрузки CSV, а как **молекулярная командная панель для научного решения**.

Главная метафора:

```text
DNA evidence stream → decision gates → safe taxon → GBIF export → scientific insights
```

Цветовая система:

```text
Dark forest / deep teal background
light evidence cards
green = safe publishable
amber = review/repairable
red = blocked claim
blue = reference/science insight
purple = novel/unknown cluster
```

## 2. Главный экран

### Hero block

```text
EcoGenesis Nexus
DNA-to-Taxon Evidence Engine for GBIF

From raw sequences to safe taxonomic claims, segment evidence,
reference gaps, repair actions and GBIF-ready exports.
```

CTA:

```text
Run sequence classification
Import hit table
Open demo evidence pack
Build reference index
```

### KPI cards

```text
Processed sequences: 10,000
GBIF-ready safe records: 6,420
Species overclaims blocked: 1,480
Downgraded but usable: 2,100
Repairable records: 1,020
Reference gaps found: 37
```

## 3. Workbench layout

```text
Left sidebar:
  Project
  Data input
  Reference fabric
  Ruleset profile
  Sequence decisions
  Segment atlas
  Evidence graph
  Repair planner
  GBIF exports

Main panel:
  selected run / selected sequence / charts

Right inspector:
  formula values
  blockers
  evidence passport
  export preview
```

## 4. Record decision waterfall

Each record gets a vertical pipeline:

```text
1. Sequence QC                 pass / warning / fail
2. Candidate retrieval          top 50 candidates
3. Alignment                    identity, coverage, length
4. Ambiguity / LCA              safe rank
5. Reference support            barcode gap / diagnostic k-mer / curated ref
6. Process support              controls / replicates / assay
7. GBIF metadata                required/recommended
8. Bounded result               species/genus/higher/review
```

Each step must show:

```text
formula
input values
threshold
result
explanation in plain language
```

Example card:

```text
Ambiguity gate
Formula: d₂ - d₁ ≤ 1.96 * sqrt(SE₁² + SE₂²)
Observed: 0.0007 ≤ 0.0013 → competitor indistinguishable
Decision: species claim blocked, safe taxon downgraded to genus Aedes
```

## 5. Sequence segment atlas

A horizontal DNA viewer:

```text
0bp ├──── conserved clade ────┤
120 ├──── genus diagnostic ───┤
280 ├──── species diagnostic ─┤
410 ├──── low information ────┤
580 ├──── primer region ──────┤ 658bp
```

Hover/click output:

```text
Window: 280-340 bp
Best taxon: Aedes albopictus
Diagnostic k-mers: 4
False-positive probability: 0.003
Window type: species diagnostic
```

## 6. Evidence graph

Nodes:

```text
Sequence → Hit → Taxon → Claim → Blocker → RepairAction → Export
```

Graph interactions:

```text
click taxon → all sequences supporting it
click blocker → all records blocked by same problem
click repair action → expected unlock count
click reference DB → version, checksum, marker scope
```

## 7. Repair planner view

### Top action cards

```text
#1 Add eventDate
Unlocks: 890 records
Gain: high
Cost: low
Affected exports: Occurrence core
```

```text
#2 Add referenceDatabaseVersion
Unlocks: 430 records
Gain: medium
Cost: low
Affected exports: DNA-derived extension
```

### Table

```text
Action | Blocker removed | Unlocks | Rank gain | Cost | Priority | Example records
```

## 8. GBIF export preview

Tabs:

```text
Occurrence core
DNA-derived extension
Review-only records
Methods text
Citations
Reference manifest
```

Every row should have:

```text
claim_allowed
safe_taxon
decision_class
evidence_passport_link
```

## 9. Visual language for decisions

```text
species_safe          green badge: Species-safe
species_candidate     amber badge: Species candidate, review
geus_safe             green/teal badge: Genus-safe
higher_rank_safe      blue badge: Higher-rank safe
molecular_signal      gray/blue badge: Molecular signal only
weak_match            red/gray badge: Weak match
no_match              gray badge: No reference match
repairable_metadata   amber badge: Repair metadata
reference_gap         purple badge: Reference gap
```

## 10. Demo storyboard

Slide/video sequence:

1. Problem: top hit is not enough.
2. Upload sequences or hit table.
3. Watch pipeline classify each sequence.
4. Show ambiguous Aedes case collapsed to genus.
5. Show segment atlas: the fragment is shared by several species.
6. Show repair planner: one metadata fix unlocks hundreds of records.
7. Show GBIF exports.
8. End with impact: more DNA-derived data, fewer unsafe species claims.
