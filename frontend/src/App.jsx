import { useEffect, useMemo, useState } from 'react';
import {
  exportUrl,
  getBarcodeDemoScenarios,
  getBarcodeReferenceStatus,
  getBarcodeRun,
  runBarcodeCompiler,
} from './api.js';

const defaultScenario = {
  id: 'fallback',
  label: 'Mixed batch',
  description: 'Fallback demo containing species-safe, ambiguous, weak and metadata-blocked cases.',
  request: {
    project_title: 'Aedes COI batch: safe, ambiguous, weak and metadata cases',
    marker: 'COI-5P',
    reference_database: 'COI Animals / BOLD public clustered reference',
    method_or_sop: 'GBIF Sequence ID-compatible BLAST workflow with deterministic rank gates',
    ruleset_version: 'barcode-gbif-compiler-v2',
    records: [
      {
        sequence_id: 'fallback-sequence',
        sequence: 'ACGTTGACCTAGGCTTACGATCGTACCGA',
        metadata: {
          occurrenceID: 'urn:ecogenesis:fallback:1',
          basisOfRecord: 'MaterialSample',
          scientificName: 'Unresolved molecular sample',
          eventDate: '2026-04-18',
          methodOrSOP: 'Fallback local request',
        },
        hits: [],
      },
    ],
  },
};

const modeLabels = {
  overview: 'Submission overview',
  workbench: 'Compiler workbench',
  formulas: 'Proof & formulas',
};

const formulaSections = [
  {
    label: 'Compiler function',
    title: 'The tool is a deterministic compiler, not a vague score',
    formula: `Compiler(s, H, T, M, R)
  -> (tau_safe, status, blockers, actions, exports)

Implemented output:
  candidate_taxon, published_taxon,
  decision_class, publication_stage,
  blockers, actions, evidence_pack

s = query sequence
H = reference hits:
  identity, coverage, bitScore, evalue, taxon, lineage
T = taxonomy / GBIF backbone lineage
M = occurrence and DNA-derived metadata
R = reference evidence for barcode gap and diagnostic k-mers
tau_safe = maximum safe taxonomic rank`,
    proof: 'Every output is derived from supplied inputs and frozen gates. There is no hidden weighting step, so a judge can reproduce why a sequence was published, downgraded, reviewed or blocked.',
  },
  {
    label: 'Match gates',
    title: 'Species claims require an exact Sequence ID-style match',
    formula: `h_i = (taxon_i, identity_i, coverage_i, evalue_i, bitScore_i, L_i)

Exact(h_i) = I(identity_i >= 0.99) * I(coverage_i >= 0.80)
Close(h_i) = I(0.90 < identity_i < 0.99) * I(coverage_i >= 0.80)
Weak(h_i)  = I(identity_i < 0.90 OR coverage_i < 0.80)

First species gate:
G1(s) = Exact(h_1)

If G1(s) = 0:
species-level claim is forbidden`,
    proof: 'If the top hit is not exact, the compiler cannot emit species-safe. This blocks short fragments and weak matches from becoming species-level occurrences.',
  },
  {
    label: 'Ambiguity test',
    title: 'A top hit must be distinguishable from competitors',
    formula: `d_i = 1 - identity_i
SE_i = sqrt(d_i * (1 - d_i) / aligned_length_i)

Delta_j = d_j - d_top
Boundary_j = 1.96 * sqrt(SE_top^2 + SE_j^2)

Indistinguishable if:
Delta_j <= Boundary_j`,
    proof: 'If another species is statistically indistinguishable from the top hit, the species claim is blocked. The compiler then uses the shared lineage instead of blindly trusting the top hit.',
  },
  {
    label: 'Safe rank',
    title: 'The safe taxon is the LCA of indistinguishable hits',
    formula: `U(s) = { h_j in H : Delta_j <= Boundary_j }
candidate_taxon = LCA({ taxon_j : h_j in U(s) })

If U contains Aedes albopictus and Aedes aegypti:
candidate_taxon = Aedes / genus`,
    proof: 'This is the downgrade rule. When species cannot be separated, the compiler preserves useful evidence at genus or higher rank instead of overclaiming.',
  },
  {
    label: 'Barcode gap',
    title: 'The reference library must separate the target species',
    formula: `D_intra(t) = max distance between references inside taxon t
D_inter(t) = min distance between t and outside taxa

BarcodeGap(t) = D_inter(t) - D_intra(t)

Species gate passes only if:
BarcodeGap(t) > 0`,
    proof: 'If the interspecific distance is not larger than the intraspecific distance, the marker/reference library cannot defend a species-level claim. The compiler blocks species-safe.',
  },
  {
    label: 'Diagnostic k-mers',
    title: 'Diagnostic support must have low random-collision risk',
    formula: `K_k(s) = all k-length windows in sequence s
D_k(t) = k-mers unique to taxon t in the reference set

DS(s,t) = |K_k(s) intersection D_k(t)| / |K_k(s)|

If DS(s,t) = 0:
the query has no unique k-mer signal for this taxon

k = ceil(log_4(N_ref / epsilon))

support_count = |K_k(s) intersection D_k(t)|
p_false_positive = 1 - (1 - |D_k(t)| / 4^k) ^ |K_k(s)|

Diagnostic gate passes only if:
support_count >= 1 AND p_false_positive <= alpha

Default alpha = 0.01`,
    proof: 'A single diagnostic k-mer is not enough if it is too short or too common. The false-positive gate blocks accidental random support from unlocking a species claim.',
  },
  {
    label: 'Publication readiness',
    title: 'Taxonomic evidence and GBIF publication readiness are separate',
    formula: `F_core = {occurrenceID, basisOfRecord, scientificName, eventDate}
CorePass(M) = product over f in F_core of I(M_f != empty)

F_dna = {marker, sequenceID, referenceDatabase,
         identity, queryCoverage, methodOrSOP}
DNAPass(M) = product over f in F_dna of I(M_f != empty)

Publishable(M, s) =
  CorePass(M) AND DNAPass(M) AND TaxonomicSafe(s)`,
    proof: 'A sequence may be taxonomically strong but still not publishable. Missing occurrenceID or eventDate changes the final decision to not-publishable and keeps published_taxon empty.',
  },
  {
    label: 'Decision function',
    title: 'Final classes are fail-closed',
    formula: `Decision(s,M) =
  species-safe      if Exact(h_1)=1
                    AND rank(LCA(U(s))) = species
                    AND BG(t) > 0
                    AND DS(s,t) > 0
                    AND Publishable = 1

  genus-safe        if rank(LCA(U(s))) = genus
                    AND CorePass = 1
                    AND DNAPass = 1

  higher-rank-safe  if rank(LCA(U(s))) in {family, order, class, ...}

  ambiguous         if |U(s)| > 1
                    AND rank(LCA(U(s))) > species

  weak              if identity_1 < 0.90 OR coverage_1 < 0.80

  not-publishable   if CorePass = 0 OR DNAPass = 0

  no-match          if H(s) = empty`,
    proof: 'The species-safe path is the narrowest path. Any failed species gate either downgrades the rank, moves the record to review, or blocks publication.',
  },
  {
    label: 'Utility metrics',
    title: 'The project measures workflow value, not vague confidence',
    formula: `K_process = N_processed / N_input
K_species = N_species_safe / N_input

K_block =
  N_blocked_unsafe_top_hit_species_claims
  / N_unsafe_top_hit_species_claims

K_repair =
  N_not_ready_records_with_explicit_blockers
  / N_not_ready_records

Ready_before = N_already_publishable / N_input
Ready_after  = N_publishable_after_repair / N_input
Gain = Ready_after - Ready_before`,
    proof: 'These metrics show whether the tool actually improves a publishing workflow: every record is processed, unsafe species claims are blocked, and not-ready records receive repairable blockers.',
  },
];

const engineFormulaSections = [
  {
    label: 'Global problem',
    title: 'Evidence Conversion Problem',
    formula: `Omega = {r_1, r_2, ..., r_N}
r_i = (s_i, H_i, T_i, M_i, R_i)

Goal:
convert the largest possible stream of DNA / metabarcoding results into
safe, reproducible and GBIF-ready occurrence evidence

without:
  manual calibration
  blind top-hit species claims
  hidden confidence weights`,
    proof: 'The project is not trying to guess life from a sequence. It classifies every molecular observation into safe taxonomic evidence, publication readiness, blockers and repair actions.',
  },
  {
    label: 'Two-axis output',
    title: 'Taxonomy and publication readiness must be separated',
    formula: `TaxStatus(r_i) in {
  speciesSafe,
  genusSafe,
  higherRankSafe,
  ambiguous,
  weak,
  noMatch
}

PubStatus(r_i) in {
  gbifReady,
  repairable,
  notReady
}

Example:
TaxStatus = speciesSafe
PubStatus = repairable

Meaning:
the taxon is defensible, but GBIF fields are missing`,
    proof: 'A strong sequence match can still be blocked by missing occurrenceID, eventDate or method metadata. Separating the axes preserves useful evidence instead of collapsing everything into one vague status.',
  },
  {
    label: 'Conversion funnel',
    title: 'The engine shows where molecular evidence is lost',
    formula: `N =
  N_species
  + N_genus
  + N_higher
  + N_ambiguous
  + N_weak
  + N_noMatch

and separately:

N =
  N_gbifReady
  + N_repairable
  + N_notReady`,
    proof: 'This makes the result understandable to GBIF reviewers and publishers: the output is a funnel of safe evidence, downgraded evidence, weak evidence, missing metadata and reference-library problems.',
  },
  {
    label: 'Conversion metrics',
    title: 'Project value is measured as workflow conversion',
    formula: `MECY = N_gbifReady / N
RY   = N_repairable / N
SRY  = (N_species + N_genus + N_higher) / N
SSY  = N_species / N

UnsafeTopSpecies =
  sum I(topHitRank_i = species AND TaxStatus_i != speciesSafe)

OR_naive =
  UnsafeTopSpecies / sum I(topHitRank_i = species)

OR_compiler = 0 under the frozen rules,
because the compiler never emits species when gates fail`,
    proof: 'The metric that matters is not a cosmetic score. It is how many records become GBIF-ready, how many are repairable and how many unsafe species claims are prevented.',
  },
  {
    label: 'Repair optimizer',
    title: 'Find the smallest actions that unlock the most records',
    formula: `B(r_i) = {b_i1, b_i2, ..., b_ik}

Unlock(a) = {r_i : action a removes a blocker for r_i}

Maximum coverage objective:

max over A' subset A, |A'| <= k
  | union over a in A' of Unlock(a) |

Examples:
add eventDate -> unlocks 430 records
add occurrenceID -> unlocks 430 records
curate reference pair A/B -> unlocks 85 species-level claims`,
    proof: 'This turns the tool from a passive report into a prioritization engine for publishers, GBIF nodes and labs: fix the bottlenecks that unlock the most publishable evidence first.',
  },
  {
    label: 'Reference gap index',
    title: 'Show where reference libraries block species-safe conversion',
    formula: `Attempts(t,m,g) =
  sum I(topTaxon_i = t AND marker_i = m AND region_i = g)

Blocked_ref(t,m,g) =
  sum I(reason_i in {
    ambiguous,
    LCA_downgrade,
    barcode_gap <= 0,
    diagnostic_support = 0,
    noMatch
  })

RGI(t,m,g) = Blocked_ref(t,m,g) / Attempts(t,m,g)

Reference completeness:
RCI(clade,marker) =
  species_with_reference / accepted_species_in_clade`,
    proof: 'When RGI is high, the problem is not necessarily the user. It may be the reference library, marker choice or taxonomic coverage. That is actionable for GBIF communities.',
  },
  {
    label: 'Publisher bottleneck',
    title: 'Separate DNA problems from metadata problems',
    formula: `PBI(dataset) =
  count(records in dataset where PubStatus != gbifReady)
  / count(records in dataset)

FieldLoss(field,dataset) =
  count(records in dataset missing field)
  / count(records in dataset)

Example:
72% of records are blocked by missing eventDate,
not by weak sequence evidence`,
    proof: 'This helps publishers see whether they need new lab work, metadata repair or reference curation. Many records can be unlocked without resequencing.',
  },
  {
    label: 'Protein sanity',
    title: 'Amino acids are a QC layer, not species truth',
    formula: `marker_type in {coding, noncoding, rRNA, unknown}

if marker_type != coding:
  amino_acid_layer = not_applicable

For coding markers:
Frame* = argmin_f StopCodons(Translate(s, f))

Pass if:
  InternalStopCount = 0
  length(s) mod 3 = 0
  FrameshiftRisk = 0

DNA-level evidence -> taxonomy / barcode safety
Protein-level evidence -> coding QC, pseudogene / NUMT warnings`,
    proof: 'DNA to protein translation loses information because multiple codons can encode the same amino acid. Protein checks are useful for frameshifts, stop codons and pseudogene risk, not for claiming species by themselves.',
  },
  {
    label: 'Fragment sharedness',
    title: 'Turn ambiguous fragments into knowledge instead of throwing them away',
    formula: `For fragment f:
T(f) = {taxa where f occurs}
G(f) = occurrence context of those taxa through GBIF

c(f,t) = count of fragment f in taxon t
p(t|f) = c(f,t) / sum_u c(f,u)

H_tax(f) = - sum_t p(t|f) log p(t|f)
Spec(f) = 1 - H_tax(f) / log |T(f)|

SafeTaxon(f) = LCA(T(f))

If f occurs in multiple Aedes species:
SafeTaxon(f) = Aedes / genus`,
    proof: 'A fragment shared by several species is not useless. It becomes genus-level or clade-level evidence, and the UI can show all taxa carrying it instead of pretending one top species is enough.',
  },
  {
    label: 'Evidence graph',
    title: 'The compiler is the ingestion layer for a broader Molecular Evidence Graph',
    formula: `Nodes:
  Fragment
  DNA k-mer / window
  Amino acid motif
  Protein domain
  Taxon / clade
  Occurrence region
  Dataset
  Claim
  Blocker

Edges:
  fragment_occurs_in_taxon
  fragment_shared_by_clade
  fragment_diagnostic_for_taxon
  fragment_maps_to_protein
  taxon_observed_in_region
  claim_supported_by
  claim_blocked_by`,
    proof: 'This is the larger research direction: taxonomy, geography, protein context and safe claims in one auditable graph. The current Barcode Compiler is the first working safety layer.',
  },
];

const engineLayers = [
  ['1', 'Taxonomic Evidence Compiler', 'Current working module: identity, coverage, ambiguity/LCA, barcode gap and diagnostic k-mers produce safe rank decisions.'],
  ['2', 'Publication Repair Optimizer', 'Ranks blockers by how many GBIF-ready records each repair can unlock.'],
  ['3', 'Reference Gap Dashboard', 'Shows taxa, markers and regions where reference libraries prevent species-safe conversion.'],
  ['4', 'Protein Sanity Layer', 'For coding markers only: reading frame, stop codons, frameshift and pseudogene/NUMT warnings.'],
  ['5', 'Assay Evidence Gate', 'For eDNA/metabarcoding: controls, replicates, contamination flags and workflow metadata.'],
  ['6', 'Molecular Evidence Graph', 'Connects fragments, taxa, GBIF geography, protein context, datasets, claims and blockers.'],
];

const fullMathSections = [
  {
    label: '01',
    title: 'Complete input contract',
    formula: `Omega = {r_1, r_2, ..., r_N}

r_i = (s_i, H_i, T_i, M_i, R_i, A_i)

s_i = DNA sequence, ASV, barcode, amplicon or fragment

H_i = {h_1, h_2, ..., h_n}
h_j = (
  taxon_j,
  rank_j,
  lineage_j,
  identity_j,
  coverage_j,
  aligned_length_j,
  bitScore_j,
  evalue_j
)

T_i = taxonomy tree / GBIF backbone lineage
M_i = occurrence + DNA-derived metadata
R_i = reference evidence:
  barcode gap,
  diagnostic k-mers,
  reference completeness
A_i = assay evidence:
  controls,
  replicates,
  read counts,
  contamination flags`,
    meaning: 'A row is not only a sequence. It is sequence evidence plus hits, taxonomy, metadata, reference-library context and optional assay context. That is why the output can explain why a record is safe, downgraded, repairable or blocked.',
  },
  {
    label: '02',
    title: 'Compiler output contract',
    formula: `Compiler(s, H, T, M, R, A)
  -> (
    tau_safe,
    tax_status,
    pub_status,
    candidate_taxon,
    published_taxon,
    blockers,
    actions,
    exports
  )

tau_safe = maximum defensible taxonomic level

tax_status in {
  speciesSafe,
  genusSafe,
  higherRankSafe,
  ambiguous,
  weak,
  noMatch
}

pub_status in {
  gbifReady,
  repairable,
  notReady
}

candidate_taxon = safest biological interpretation
published_taxon = taxon allowed into publishable export

If publication gates fail:
  candidate_taxon may exist
  published_taxon = none`,
    meaning: 'The key design choice is separating biological interpretation from publication readiness. A sequence can be species-safe but still not publishable because GBIF-required fields are missing.',
  },
  {
    label: '03',
    title: 'Match gates: identity and coverage',
    formula: `For hit h_j:

Exact(h_j) =
  I(identity_j >= 0.99) * I(coverage_j >= 0.80)

Close(h_j) =
  I(0.90 < identity_j < 0.99) * I(coverage_j >= 0.80)

Weak(h_j) =
  I(identity_j < 0.90 OR coverage_j < 0.80)

NoMatch(s) =
  I(|H(s)| = 0)

SpeciesGate_1(s) = Exact(h_top)

If SpeciesGate_1(s) = 0:
  species-level publication is forbidden`,
    meaning: 'This blocks the most common mistake: taking a high-looking but incomplete hit and calling it a species. Coverage matters as much as identity.',
  },
  {
    label: '04',
    title: 'Ambiguity boundary: top hit must be distinguishable',
    formula: `d_j = 1 - identity_j

SE_j = sqrt(d_j * (1 - d_j) / aligned_length_j)

Delta_j = d_j - d_top

Boundary_j =
  1.96 * sqrt(SE_top^2 + SE_j^2)

Competitor h_j is indistinguishable from top hit if:

Delta_j <= Boundary_j

U(s) = {
  h_j in H(s) :
  d_j - d_top <= 1.96 * sqrt(SE_top^2 + SE_j^2)
}`,
    meaning: 'If another taxon is statistically too close to the top hit, the top species is not enough. The compiler gathers indistinguishable competitors before deciding the safe rank.',
  },
  {
    label: '05',
    title: 'Safe taxonomic rank through LCA',
    formula: `tau_safe(s) =
  LCA({taxon_j : h_j in U(s)})

rank_safe(s) = rank(tau_safe(s))

If:
  U(s) = {
    Aedes albopictus,
    Aedes aegypti
  }

Then:
  tau_safe(s) = Aedes
  rank_safe(s) = genus

Species claim is blocked,
but genus-level evidence is preserved.`,
    meaning: 'This is the downgrade rule. The system does not throw away useful evidence just because species is unsafe; it moves to the lowest common ancestor.',
  },
  {
    label: '06',
    title: 'Barcode gap: marker/reference separability',
    formula: `For candidate species t:

D_intra(t) =
  max distance(a,b)
  for a,b in reference sequences of t

D_inter(t) =
  min distance(a,b)
  for a in references of t
  and b outside t

BG(t) = D_inter(t) - D_intra(t)

BarcodeGapPass(t) =
  I(BG(t) > 0)

If BG(t) <= 0:
  species-level claim is blocked`,
    meaning: 'Even an exact top hit is unsafe if the marker does not separate the species from close relatives in the reference library.',
  },
  {
    label: '07',
    title: 'Diagnostic k-mers with random-collision control',
    formula: `K_k(s) =
  {s[1:k], s[2:k+1], ..., s[L-k+1:L]}

D_k(t) =
  K_k(R_t) \\ union_{u != t} K_k(R_u)

DS(s,t) =
  |K_k(s) intersection D_k(t)| / |K_k(s)|

k =
  ceil(log_4(N_ref / epsilon))

support_count =
  |K_k(s) intersection D_k(t)|

query_windows =
  max(L - k + 1, 0)

p_false_positive =
  1 - (1 - |D_k(t)| / 4^k) ^ query_windows

DiagnosticPass(s,t) =
  I(support_count >= 1)
  * I(p_false_positive <= alpha)

Default alpha = 0.01`,
    meaning: 'This prevents a short or common k-mer from unlocking a species claim by accident. Diagnostic support must exist and its random-collision risk must be low.',
  },
  {
    label: '08',
    title: 'Reference Completeness Gate',
    formula: `For candidate species t inside genus g and marker m:

Species_GBIF(g) =
  accepted species in genus g from GBIF backbone

Species_ref(g,m) =
  species in genus g represented in the reference library for marker m

RC(g,m) =
  |Species_GBIF(g) intersection Species_ref(g,m)|
  / |Species_GBIF(g)|

If RC(g,m) = 1:
  species-safe-A

If gates pass but RC(g,m) < 1:
  species-safe-B with reference-incomplete caveat

If a missing close species could change LCA:
  downgrade or require review`,
    meaning: 'No competitor in the database does not mean no competitor in nature. This gate makes reference-library incompleteness visible instead of hidden.',
  },
  {
    label: '09',
    title: 'Protein Sanity Gate for coding markers',
    formula: `marker_type in {
  coding,
  noncoding,
  rRNA,
  unknown
}

If marker_type != coding:
  amino_acid_layer = not_applicable

For coding marker:

codon_j = s[3j : 3j+2]
aa_j = GeneticCode(codon_j)

Frame* =
  argmin over f in {0,1,2}
  StopCodons(Translate(s, f))

ProteinSanityPass =
  I(InternalStopCount = 0)
  * I(length(s) mod 3 = 0)
  * I(FrameshiftRisk = 0)

If ProteinSanityPass = 0:
  add blocker:
  possible frameshift / stop codon / pseudogene / NUMT`,
    meaning: 'Amino acids are not the main species-discriminator. Translation loses nucleotide information. The protein layer is a quality-control layer for coding markers.',
  },
  {
    label: '10',
    title: 'Assay Evidence Gate for eDNA and metabarcoding',
    formula: `A_i = {
  positive_replicates,
  pcr_replicates,
  negative_control_detected,
  blank_control_detected,
  read_count,
  relative_abundance,
  chimera_flag,
  primer_set,
  workflow_version
}

ControlPass =
  I(negative_control_detected = false)
  * I(blank_control_detected = false)

ReplicateEvidence =
  positive_replicates / pcr_replicates

If control metadata missing:
  assay_status = not_evaluated

If negative or blank control is positive:
  assay_status = contamination_risk

Do not infer:
  living organism present here now

Say instead:
  sequence-derived molecular evidence was detected
  under the supplied assay context`,
    meaning: 'For eDNA, detection is not the same as direct living presence. Controls and replicates matter, and the UI must keep this caveat explicit.',
  },
  {
    label: '11',
    title: 'Publication readiness',
    formula: `F_core = {
  occurrenceID,
  basisOfRecord,
  scientificName,
  eventDate
}

CorePass(M) =
  product over f in F_core of I(M_f != empty)

F_dna = {
  marker,
  sequenceID,
  referenceDatabase,
  identity,
  queryCoverage,
  methodOrSOP
}

DNAPass(M) =
  product over f in F_dna of I(M_f != empty)

PubDecision(M, s) =
  gbifReady   if CorePass = 1 AND DNAPass = 1
  repairable  if TaxDecision != noMatch
              AND (CorePass = 0 OR DNAPass = 0)
  notReady    if no usable sequence evidence
              OR no usable metadata`,
    meaning: 'This is the repair layer. It tells the user whether the problem is biology, reference evidence or simply missing GBIF publication fields.',
  },
  {
    label: '12',
    title: 'Two-axis decision function',
    formula: `TaxDecision(s) =
  speciesSafe if
    Exact(h_top)=1
    AND rank(LCA(U(s))) = species
    AND BG(t) > 0
    AND DiagnosticPass(s,t)=1
    AND reference caveat is acceptable
    AND ProteinSanityPass is not failed

  genusSafe if
    rank(LCA(U(s))) = genus

  higherRankSafe if
    rank(LCA(U(s))) in {family, order, class, ...}

  weak if
    identity_top < 0.90 OR coverage_top < 0.80

  noMatch if
    H(s) is empty

Final export rule:

If TaxDecision is safe rank
AND PubDecision = gbifReady:
  published_taxon = tau_safe

Else:
  published_taxon = none
  record goes to review / repair queue`,
    meaning: 'The current implementation already applies the core fail-closed version of this. The planned protein/reference/assay layers strengthen it without changing the principle.',
  },
  {
    label: '13',
    title: 'Batch decomposition: where the data go',
    formula: `N =
  N_species
  + N_genus
  + N_higher
  + N_ambiguous
  + N_weak
  + N_noMatch

N =
  N_gbifReady
  + N_repairable
  + N_notReady

Loss_by_reason(b) =
  sum_i I(b in blockers(r_i))

Repairable_by_field(f) =
  sum_i I(f in missing_fields(r_i)
          AND TaxDecision(r_i) != noMatch)`,
    meaning: 'The engine becomes a loss-accounting system. It shows whether records are lost to weak sequence, ambiguity, reference gaps, assay caveats or metadata gaps.',
  },
  {
    label: '14',
    title: 'Conversion and overclaim metrics',
    formula: `MECY =
  N_gbifReady / N

RY =
  N_repairable / N

SRY =
  (N_species + N_genus + N_higher) / N

SSY =
  N_species / N

TopSpecies_i =
  I(topHitRank_i = species)

SpeciesSafe_i =
  I(TaxDecision_i = speciesSafe)

UnsafeTopSpecies =
  sum_i I(TopSpecies_i = 1 AND SpeciesSafe_i = 0)

OR_naive =
  UnsafeTopSpecies / sum_i TopSpecies_i

OR_compiler = 0
under the export rules because unsafe species
claims are not emitted as published species`,
    meaning: 'This answers "what did we solve?" quantitatively: records are processed, useful safe-rank evidence is kept, and naive top-hit overclaiming is blocked.',
  },
  {
    label: '15',
    title: 'Repair optimizer',
    formula: `For record r_i:

B(r_i) =
  {b_i1, b_i2, ..., b_ik}

Each action a removes one or more blockers:

Unlock(a) =
  {r_i : a removes at least one blocking condition
        and all remaining conditions allow GBIF-ready export}

Budgeted maximum coverage:

maximize over A' subset A, |A'| <= k:

  | union over a in A' of Unlock(a) |

Weighted version:

maximize:
  sum_{r_i unlocked by A'} value(r_i)

subject to:
  sum_{a in A'} cost(a) <= Budget`,
    meaning: 'This is the next strongest product feature: not only "what is broken?", but "what should I fix first to unlock the most GBIF-ready records?".',
  },
  {
    label: '16',
    title: 'Reference and publisher bottleneck indices',
    formula: `Attempts(t,m,g) =
  sum_i I(topTaxon_i = t
          AND marker_i = m
          AND region_i = g)

Blocked_ref(t,m,g) =
  sum_i I(reason_i in {
    ambiguous,
    LCA_downgrade,
    BG <= 0,
    DiagnosticPass = 0,
    noMatch,
    reference_incomplete
  })

RGI(t,m,g) =
  Blocked_ref(t,m,g) / Attempts(t,m,g)

For dataset d:

PBI(d) =
  sum_i I(dataset_i=d AND PubStatus_i != gbifReady)
  / sum_i I(dataset_i=d)

FieldLoss(f,d) =
  sum_i I(dataset_i=d AND f in MissingFields_i)
  / sum_i I(dataset_i=d)`,
    meaning: 'Reference Gap Index points curators to missing molecular references. Publisher Bottleneck Index tells data publishers which metadata fields block their records.',
  },
  {
    label: '17',
    title: 'Fragment sharedness and specificity',
    formula: `For fragment f:

T(f) =
  {t_1, t_2, ..., t_n}
  taxa where f occurs

c(f,t) =
  count of fragment f in taxon t

p(t|f) =
  c(f,t) / sum_u c(f,u)

H_tax(f) =
  - sum_t p(t|f) * log(p(t|f))

Spec(f) =
  1 - H_tax(f) / log(|T(f)|)

SafeTaxon(f) =
  LCA(T(f))

If Spec(f) ~= 1:
  fragment is taxonomically specific

If Spec(f) ~= 0:
  fragment is broadly shared`,
    meaning: 'This answers the deeper idea: when a fragment occurs in several species, do not hide it as "ambiguous". Show all taxa, entropy, specificity and safe LCA.',
  },
  {
    label: '18',
    title: 'Geography is evidence context, not direct proof',
    formula: `For fragment f and region g:

G(f) =
  occurrence regions of taxa in T(f)
  through GBIF-mediated evidence

c(f,g) =
  sum over t in T(f) of Occurrences(t,g)

P(g|f) =
  c(f,g) / sum_v c(f,v)

GeoScore(f,g) =
  log((P(g|f) + epsilon) / (P(g|not f) + epsilon))

Allowed wording:
  taxa carrying this fragment have GBIF occurrence
  evidence in region g

Blocked wording:
  this fragment definitely occurs in region g`,
    meaning: 'This protects the project from a common geographic overclaim. GBIF occurrences provide context unless the molecular sample itself has coordinates.',
  },
  {
    label: '19',
    title: 'Multi-marker consensus',
    formula: `For markers m_1, m_2, ..., m_k:

tau_1 = SafeTaxon(s, m_1)
tau_2 = SafeTaxon(s, m_2)
...
tau_k = SafeTaxon(s, m_k)

ConsensusSafeTaxon =
  LCA({tau_1, tau_2, ..., tau_k})

If markers disagree deeply:
  status = conflict
  action = review taxonomy, contamination,
           primer specificity or reference library`,
    meaning: 'This is how the engine can grow beyond one barcode marker without pretending that one marker has absolute authority.',
  },
  {
    label: '20',
    title: 'Molecular Evidence Graph',
    formula: `Graph G = (V, E)

V includes:
  Sequence
  Fragment
  K-mer
  AminoAcidMotif
  ProteinDomain
  Taxon
  Clade
  Region
  Dataset
  Claim
  Blocker
  RepairAction

E includes:
  sequence_has_hit
  hit_maps_to_taxon
  fragment_occurs_in_taxon
  fragment_shared_by_clade
  fragment_diagnostic_for_taxon
  fragment_maps_to_protein
  taxon_observed_in_region
  claim_supported_by
  claim_blocked_by
  action_repairs_blocker

Every published claim must have:
  at least one supported_by path
  zero unresolved hard blockers`,
    meaning: 'This is the big direction for GBIF: an auditable graph that turns molecular fragments into safe taxonomic, publication, geographic and protein-context evidence.',
  },
];

const renderedFormulaSections = [
  {
    label: '01',
    title: 'Input space',
    equations: [
      <MathRow key="omega"><Mi>Omega</Mi><Op>=</Op><MathSet><Mi>r</Mi><Sub>1</Sub>, <Mi>r</Mi><Sub>2</Sub>, ..., <Mi>r</Mi><Sub>N</Sub></MathSet></MathRow>,
      <MathRow key="ri"><Mi>r</Mi><Sub>i</Sub><Op>=</Op><Paren><Mi>s</Mi><Sub>i</Sub>, <Mi>H</Mi><Sub>i</Sub>, <Mi>T</Mi><Sub>i</Sub>, <Mi>M</Mi><Sub>i</Sub>, <Mi>R</Mi><Sub>i</Sub>, <Mi>A</Mi><Sub>i</Sub></Paren></MathRow>,
    ],
    explanation: 'Each molecular observation is sequence evidence plus hits, taxonomy, metadata, reference context and assay context.',
  },
  {
    label: '02',
    title: 'Compiler mapping',
    equations: [
      <MathRow key="compiler"><Func>Compiler</Func><Paren><Mi>s</Mi>, <Mi>H</Mi>, <Mi>T</Mi>, <Mi>M</Mi>, <Mi>R</Mi>, <Mi>A</Mi></Paren><Op>to</Op><Paren><Mi>tau</Mi><Sub>safe</Sub>, <Mi>TaxStatus</Mi>, <Mi>PubStatus</Mi>, <Mi>B</Mi>, <Mi>Actions</Mi>, <Mi>Exports</Mi></Paren></MathRow>,
    ],
    explanation: 'The output is not a score. It is a safe taxon, publication status, blockers, repair actions and exports.',
  },
  {
    label: '03',
    title: 'Identity and coverage gates',
    equations: [
      <MathRow key="exact"><Func>Exact</Func><Paren><Mi>h</Mi><Sub>i</Sub></Paren><Op>=</Op><Indicator><Mi>identity</Mi><Sub>i</Sub><Op>&gt;=</Op>0.99</Indicator><Op>*</Op><Indicator><Mi>coverage</Mi><Sub>i</Sub><Op>&gt;=</Op>0.80</Indicator></MathRow>,
      <MathRow key="close"><Func>Close</Func><Paren><Mi>h</Mi><Sub>i</Sub></Paren><Op>=</Op><Indicator>0.90<Op>&lt;</Op><Mi>identity</Mi><Sub>i</Sub><Op>&lt;</Op>0.99</Indicator><Op>*</Op><Indicator><Mi>coverage</Mi><Sub>i</Sub><Op>&gt;=</Op>0.80</Indicator></MathRow>,
      <MathRow key="weak"><Func>Weak</Func><Paren><Mi>h</Mi><Sub>i</Sub></Paren><Op>=</Op><Indicator><Mi>identity</Mi><Sub>i</Sub><Op>&lt;</Op>0.90<Op>or</Op><Mi>coverage</Mi><Sub>i</Sub><Op>&lt;</Op>0.80</Indicator></MathRow>,
    ],
    explanation: 'Species-level claims are forbidden unless the top hit passes the exact identity and coverage gate.',
  },
  {
    label: '04',
    title: 'Ambiguity boundary',
    equations: [
      <MathRow key="d"><Mi>d</Mi><Sub>i</Sub><Op>=</Op>1<Op>-</Op><Mi>identity</Mi><Sub>i</Sub></MathRow>,
      <MathRow key="se"><Mi>SE</Mi><Sub>i</Sub><Op>=</Op><Sqrt><Frac top={<><Mi>d</Mi><Sub>i</Sub><Paren>1<Op>-</Op><Mi>d</Mi><Sub>i</Sub></Paren></>} bottom={<><Mi>L</Mi><Sub>i</Sub></>} /></Sqrt></MathRow>,
      <MathRow key="boundary"><Mi>Delta</Mi><Sub>j</Sub><Op>=</Op><Mi>d</Mi><Sub>j</Sub><Op>-</Op><Mi>d</Mi><Sub>top</Sub><Op>,</Op><Mi>B</Mi><Sub>j</Sub><Op>=</Op>1.96<Sqrt><Mi>SE</Mi><Sub>top</Sub><Sup>2</Sup><Op>+</Op><Mi>SE</Mi><Sub>j</Sub><Sup>2</Sup></Sqrt></MathRow>,
      <MathRow key="ambiguous"><Mi>h</Mi><Sub>j</Sub><Op>in</Op><Mi>U</Mi><Paren><Mi>s</Mi></Paren><Op>iff</Op><Mi>Delta</Mi><Sub>j</Sub><Op>&lt;=</Op><Mi>B</Mi><Sub>j</Sub></MathRow>,
    ],
    explanation: 'A species competitor that is too close to the top hit collapses the safe rank through LCA.',
  },
  {
    label: '05',
    title: 'Safe taxon through LCA',
    equations: [
      <MathRow key="u"><Mi>U</Mi><Paren><Mi>s</Mi></Paren><Op>=</Op><MathSet><Mi>h</Mi><Sub>j</Sub><Op>in</Op><Mi>H</Mi><Paren><Mi>s</Mi></Paren><Op>:</Op><Mi>Delta</Mi><Sub>j</Sub><Op>&lt;=</Op><Mi>B</Mi><Sub>j</Sub></MathSet></MathRow>,
      <MathRow key="lca"><Mi>tau</Mi><Sub>safe</Sub><Paren><Mi>s</Mi></Paren><Op>=</Op><Func>LCA</Func><Paren><MathSet><Mi>taxon</Mi><Sub>j</Sub><Op>:</Op><Mi>h</Mi><Sub>j</Sub><Op>in</Op><Mi>U</Mi><Paren><Mi>s</Mi></Paren></MathSet></Paren></MathRow>,
    ],
    explanation: 'If species cannot be separated, the record is preserved at genus, family or another safe ancestor.',
  },
  {
    label: '06',
    title: 'Barcode gap',
    equations: [
      <MathRow key="dintra"><Mi>D</Mi><Sub>intra</Sub><Paren><Mi>t</Mi></Paren><Op>=</Op><Func>max</Func><Sub><Mi>a</Mi>,<Mi>b</Mi><Op>in</Op><Mi>R</Mi><Sub>t</Sub></Sub><Mi>d</Mi><Paren><Mi>a</Mi>,<Mi>b</Mi></Paren></MathRow>,
      <MathRow key="dinter"><Mi>D</Mi><Sub>inter</Sub><Paren><Mi>t</Mi></Paren><Op>=</Op><Func>min</Func><Sub><Mi>a</Mi><Op>in</Op><Mi>R</Mi><Sub>t</Sub>, <Mi>b</Mi><Op>notin</Op><Mi>R</Mi><Sub>t</Sub></Sub><Mi>d</Mi><Paren><Mi>a</Mi>,<Mi>b</Mi></Paren></MathRow>,
      <MathRow key="bg"><Mi>BG</Mi><Paren><Mi>t</Mi></Paren><Op>=</Op><Mi>D</Mi><Sub>inter</Sub><Paren><Mi>t</Mi></Paren><Op>-</Op><Mi>D</Mi><Sub>intra</Sub><Paren><Mi>t</Mi></Paren></MathRow>,
    ],
    explanation: 'Species-level output requires a positive barcode gap.',
  },
  {
    label: '07',
    title: 'Diagnostic k-mer support',
    equations: [
      <MathRow key="dk"><Mi>D</Mi><Sub>k</Sub><Paren><Mi>t</Mi></Paren><Op>=</Op><Mi>K</Mi><Sub>k</Sub><Paren><Mi>R</Mi><Sub>t</Sub></Paren><Op>setminus</Op><BigUnion lower={<><Mi>u</Mi><Op>!=</Op><Mi>t</Mi></>}><Mi>K</Mi><Sub>k</Sub><Paren><Mi>R</Mi><Sub>u</Sub></Paren></BigUnion></MathRow>,
      <MathRow key="ds"><Mi>DS</Mi><Paren><Mi>s</Mi>,<Mi>t</Mi></Paren><Op>=</Op><Frac top={<Abs><Mi>K</Mi><Sub>k</Sub><Paren><Mi>s</Mi></Paren><Op>cap</Op><Mi>D</Mi><Sub>k</Sub><Paren><Mi>t</Mi></Paren></Abs>} bottom={<Abs><Mi>K</Mi><Sub>k</Sub><Paren><Mi>s</Mi></Paren></Abs>} /></MathRow>,
      <MathRow key="pfalse"><Mi>p</Mi><Sub>false-positive</Sub><Op>=</Op>1<Op>-</Op><Paren>1<Op>-</Op><Frac top={<Abs><Mi>D</Mi><Sub>k</Sub><Paren><Mi>t</Mi></Paren></Abs>} bottom={<>4<Sup>k</Sup></>} /></Paren><Sup><Abs><Mi>K</Mi><Sub>k</Sub><Paren><Mi>s</Mi></Paren></Abs></Sup></MathRow>,
    ],
    explanation: 'Diagnostic k-mer evidence must exist and the random-collision probability must stay below alpha.',
  },
  {
    label: '08',
    title: 'Reference completeness',
    equations: [
      <MathRow key="rc"><Mi>RC</Mi><Paren><Mi>g</Mi>,<Mi>m</Mi></Paren><Op>=</Op><Frac top={<Abs><Mi>Species</Mi><Sub>GBIF</Sub><Paren><Mi>g</Mi></Paren><Op>cap</Op><Mi>Species</Mi><Sub>ref</Sub><Paren><Mi>g</Mi>,<Mi>m</Mi></Paren></Abs>} bottom={<Abs><Mi>Species</Mi><Sub>GBIF</Sub><Paren><Mi>g</Mi></Paren></Abs>} /></MathRow>,
    ],
    explanation: 'This is the exact form you pointed to: species-safe claims need a visible reference completeness caveat when the clade is not fully represented.',
  },
  {
    label: '09',
    title: 'Protein sanity',
    equations: [
      <MathRow key="frame"><Mi>Frame</Mi><Sup>*</Sup><Op>=</Op><Func>arg min</Func><Sub><Mi>f</Mi><Op>in</Op><MathSet>0,1,2</MathSet></Sub><Func>StopCodons</Func><Paren><Func>Translate</Func><Paren><Mi>s</Mi>,<Mi>f</Mi></Paren></Paren></MathRow>,
      <MathRow key="protein-pass"><Mi>ProteinSanityPass</Mi><Op>=</Op><Indicator><Mi>InternalStopCount</Mi><Op>=</Op>0</Indicator><Op>*</Op><Indicator><Mi>Length</Mi><Paren><Mi>s</Mi></Paren><Op>mod</Op>3<Op>=</Op>0</Indicator><Op>*</Op><Indicator><Mi>FrameshiftRisk</Mi><Op>=</Op>0</Indicator></MathRow>,
    ],
    explanation: 'Protein translation is a coding-marker QC layer, not a species-truth layer.',
  },
  {
    label: '10',
    title: 'Publication readiness',
    equations: [
      <MathRow key="core"><Mi>CorePass</Mi><Paren><Mi>M</Mi></Paren><Op>=</Op><Product><Sub><Mi>f</Mi><Op>in</Op><Mi>F</Mi><Sub>core</Sub></Sub><Indicator><Mi>M</Mi><Sub>f</Sub><Op>!=</Op><Empty /></Indicator></Product></MathRow>,
      <MathRow key="dna"><Mi>DNAPass</Mi><Paren><Mi>M</Mi></Paren><Op>=</Op><Product><Sub><Mi>f</Mi><Op>in</Op><Mi>F</Mi><Sub>dna</Sub></Sub><Indicator><Mi>M</Mi><Sub>f</Sub><Op>!=</Op><Empty /></Indicator></Product></MathRow>,
    ],
    explanation: 'Taxonomic evidence and GBIF publication readiness are calculated separately.',
  },
  {
    label: '11',
    title: 'Taxonomic decision',
    equations: [
      <Cases key="tax-decision" lhs={<><Mi>TaxDecision</Mi><Paren><Mi>s</Mi></Paren></>} rows={[
        [<><Mi>speciesSafe</Mi></>, <><Func>Exact</Func><Paren><Mi>h</Mi><Sub>top</Sub></Paren><Op>=</Op>1 <Op>and</Op> <Func>rank</Func><Paren><Func>LCA</Func><Paren><Mi>U</Mi><Paren><Mi>s</Mi></Paren></Paren></Paren><Op>=</Op><Mi>species</Mi> <Op>and</Op> <Mi>BG</Mi><Paren><Mi>t</Mi></Paren><Op>&gt;</Op>0</>],
        [<><Mi>genusSafe</Mi></>, <><Func>rank</Func><Paren><Func>LCA</Func><Paren><Mi>U</Mi><Paren><Mi>s</Mi></Paren></Paren></Paren><Op>=</Op><Mi>genus</Mi></>],
        [<><Mi>weak</Mi></>, <><Mi>identity</Mi><Sub>top</Sub><Op>&lt;</Op>0.90 <Op>or</Op> <Mi>coverage</Mi><Sub>top</Sub><Op>&lt;</Op>0.80</>],
        [<><Mi>noMatch</Mi></>, <><Mi>H</Mi><Paren><Mi>s</Mi></Paren><Op>=</Op><Empty /></>],
      ]} />,
    ],
    explanation: 'The decision function is fail-closed: failed species gates never produce a published species.',
  },
  {
    label: '12',
    title: 'Conversion metrics',
    equations: [
      <MathRow key="mecy"><Mi>MECY</Mi><Op>=</Op><Frac top={<><Mi>N</Mi><Sub>gbifReady</Sub></>} bottom={<Mi>N</Mi>} /></MathRow>,
      <MathRow key="ry"><Mi>RY</Mi><Op>=</Op><Frac top={<><Mi>N</Mi><Sub>repairable</Sub></>} bottom={<Mi>N</Mi>} /><Op>,</Op><Mi>SSY</Mi><Op>=</Op><Frac top={<><Mi>N</Mi><Sub>species</Sub></>} bottom={<Mi>N</Mi>} /></MathRow>,
      <MathRow key="or"><Mi>OR</Mi><Sub>naive</Sub><Op>=</Op><Frac top={<><Sum><Sub><Mi>i</Mi></Sub></Sum><Indicator><Mi>TopSpecies</Mi><Sub>i</Sub><Op>=</Op>1 <Op>and</Op> <Mi>SpeciesSafe</Mi><Sub>i</Sub><Op>=</Op>0</Indicator></>} bottom={<><Sum><Sub><Mi>i</Mi></Sub></Sum><Indicator><Mi>TopSpecies</Mi><Sub>i</Sub><Op>=</Op>1</Indicator></>} /><Op>,</Op><Mi>OR</Mi><Sub>compiler</Sub><Op>=</Op>0</MathRow>,
    ],
    explanation: 'These metrics show conversion yield, repairability and prevented species overclaiming.',
  },
  {
    label: '13',
    title: 'Repair optimizer',
    equations: [
      <MathRow key="unlock"><Func>Unlock</Func><Paren><Mi>a</Mi></Paren><Op>=</Op><MathSet><Mi>r</Mi><Sub>i</Sub><Op>in</Op><Mi>Omega</Mi><Op>:</Op><Func>Fix</Func><Paren><Mi>a</Mi></Paren><Op>cap</Op><Mi>B</Mi><Paren><Mi>r</Mi><Sub>i</Sub></Paren><Op>!=</Op><Empty /></MathSet></MathRow>,
      <MathRow key="max"><Func>maximize</Func><Sub><Mi>A</Mi><Sup>'</Sup><Op>subset</Op><Mi>A</Mi>, <Abs><Mi>A</Mi><Sup>'</Sup></Abs><Op>&lt;=</Op><Mi>k</Mi></Sub><Abs><BigUnion lower={<><Mi>a</Mi><Op>in</Op><Mi>A</Mi><Sup>'</Sup></>}><Func>Unlock</Func><Paren><Mi>a</Mi></Paren></BigUnion></Abs></MathRow>,
    ],
    explanation: 'The optimizer asks which repairs unlock the largest number of GBIF-ready records.',
  },
  {
    label: '14',
    title: 'Reference and publisher bottlenecks',
    equations: [
      <MathRow key="rgi"><Mi>RGI</Mi><Paren><Mi>t</Mi>,<Mi>m</Mi>,<Mi>g</Mi></Paren><Op>=</Op><Frac top={<><Mi>Blocked</Mi><Sub>ref</Sub><Paren><Mi>t</Mi>,<Mi>m</Mi>,<Mi>g</Mi></Paren></>} bottom={<><Mi>Attempts</Mi><Paren><Mi>t</Mi>,<Mi>m</Mi>,<Mi>g</Mi></Paren></>} /></MathRow>,
      <MathRow key="pbi"><Mi>PBI</Mi><Paren><Mi>d</Mi></Paren><Op>=</Op><Frac top={<><Sum><Sub><Mi>i</Mi></Sub></Sum><Indicator><Mi>dataset</Mi><Sub>i</Sub><Op>=</Op><Mi>d</Mi> <Op>and</Op> <Mi>PubStatus</Mi><Sub>i</Sub><Op>!=</Op><Mi>gbifReady</Mi></Indicator></>} bottom={<><Sum><Sub><Mi>i</Mi></Sub></Sum><Indicator><Mi>dataset</Mi><Sub>i</Sub><Op>=</Op><Mi>d</Mi></Indicator></>} /></MathRow>,
    ],
    explanation: 'These indices separate reference-library problems from publisher metadata problems.',
  },
  {
    label: '15',
    title: 'Fragment sharedness',
    equations: [
      <MathRow key="entropy"><Mi>H</Mi><Sub>tax</Sub><Paren><Mi>f</Mi></Paren><Op>=</Op><Op>-</Op><Sum><Sub><Mi>t</Mi></Sub></Sum><Mi>p</Mi><Paren><Mi>t</Mi><Op>|</Op><Mi>f</Mi></Paren><Func>log</Func><Mi>p</Mi><Paren><Mi>t</Mi><Op>|</Op><Mi>f</Mi></Paren></MathRow>,
      <MathRow key="spec"><Mi>Spec</Mi><Paren><Mi>f</Mi></Paren><Op>=</Op>1<Op>-</Op><Frac top={<><Mi>H</Mi><Sub>tax</Sub><Paren><Mi>f</Mi></Paren></>} bottom={<><Func>log</Func><Abs><Mi>T</Mi><Paren><Mi>f</Mi></Paren></Abs></>} /></MathRow>,
      <MathRow key="safe-frag"><Mi>SafeTaxon</Mi><Paren><Mi>f</Mi></Paren><Op>=</Op><Func>LCA</Func><Paren><Mi>T</Mi><Paren><Mi>f</Mi></Paren></Paren></MathRow>,
    ],
    explanation: 'Shared fragments become clade evidence instead of unsafe species claims.',
  },
  {
    label: '16',
    title: 'Geography as context',
    equations: [
      <MathRow key="geo"><Mi>GeoScore</Mi><Paren><Mi>f</Mi>,<Mi>g</Mi></Paren><Op>=</Op><Func>log</Func><Frac top={<><Mi>P</Mi><Paren><Mi>g</Mi><Op>|</Op><Mi>f</Mi></Paren><Op>+</Op><Mi>epsilon</Mi></>} bottom={<><Mi>P</Mi><Paren><Mi>g</Mi><Op>|</Op><Op>not</Op><Mi>f</Mi></Paren><Op>+</Op><Mi>epsilon</Mi></>} /></MathRow>,
    ],
    explanation: 'This is geographic association or evidence context, not proof that a DNA fragment was directly sampled in every region.',
  },
  {
    label: '17',
    title: 'Multi-marker consensus',
    equations: [
      <MathRow key="consensus"><Mi>ConsensusSafeTaxon</Mi><Op>=</Op><Func>LCA</Func><Paren><MathSet><Mi>tau</Mi><Sub>m1</Sub>, <Mi>tau</Mi><Sub>m2</Sub>, ..., <Mi>tau</Mi><Sub>mk</Sub></MathSet></Paren></MathRow>,
    ],
    explanation: 'Multiple markers converge by LCA, and deep disagreement becomes a conflict that requires review.',
  },
  {
    label: '18',
    title: 'Graph claim rule',
    equations: [
      <MathRow key="graph"><Mi>G</Mi><Op>=</Op><Paren><Mi>V</Mi>,<Mi>E</Mi></Paren></MathRow>,
      <MathRow key="claim"><Mi>PublishedClaim</Mi><Paren><Mi>c</Mi></Paren><Op>iff</Op><Abs><Func>supported_by</Func><Paren><Mi>c</Mi></Paren></Abs><Op>&gt;</Op>0<Op>and</Op><Abs><Func>hard_blockers</Func><Paren><Mi>c</Mi></Paren></Abs><Op>=</Op>0</MathRow>,
    ],
    explanation: 'A claim must have evidence support and no unresolved hard blockers before it can appear in publishable output.',
  },
];

const solvedRows = [
  ['Unsafe top-hit species claims', 'Solved in the current compiler', 'The mixed batch blocked 3 unsafe species-level claims before export.'],
  ['Safe-rank downgrade', 'Solved in the current compiler', 'Ambiguous Aedes hits are exported at genus rank instead of forcing species.'],
  ['Weak short fragments', 'Solved in the current compiler', 'A high-identity but low-coverage record becomes `weak` and stays out of publishable species exports.'],
  ['Metadata vs taxonomy separation', 'Solved in the current compiler', 'A species-safe record with missing occurrenceID/eventDate becomes `not-publishable`, not a false published species.'],
  ['Evidence pack generation', 'Solved in the current compiler', 'CSV, JSON, HTML, Darwin Core, DNA-derived templates, methods, citations and ZIP exports are generated.'],
  ['Live GBIF API path', 'Solved for occurrence evidence', 'Aedes albopictus in Spain used live GBIF API, not fixture fallback.'],
  ['Protein sanity, assay gate, repair optimizer', 'Designed and documented, not fully implemented yet', 'The formulas and UX now expose the next layers; backend implementation is the next milestone.'],
  ['Phenotype prediction', 'Deliberately not claimed', 'The project treats phenotype/function as future hypotheses requiring curated external evidence.'],
];

const testAnalysisRows = [
  ['Frontend unit tests', '3 passed', 'Overview renders, workbench opens, proof/formulas page exposes key formulas and p_false_positive.'],
  ['Frontend production build', 'Passed', 'Vite build completed and the page can be shipped as a static frontend.'],
  ['Backend pytest', '23 passed, 1 skipped', 'API, compiler logic, exports and existing regression behavior remain operational.'],
  ['Barcode operability script', 'PASS', 'Expected decisions, API endpoint, ZIP bundle and required exports all passed.'],
  ['Browser smoke', '0 console errors', 'Proof page and workbench rendered locally; no horizontal overflow was detected in the tested viewport.'],
  ['Live GBIF smoke', 'OK', 'GBIF API reachable; taxonKey 1651430 preserved; 50 live records returned from 19,713 GBIF results; fallback_used=false.'],
];

const mixedBatchRows = [
  ['AALB-COI-good', 'species-safe', 'Aedes albopictus / species', 'All species gates and publication fields passed.'],
  ['AALB-COI-ambiguous', 'genus-safe', 'Aedes / genus', 'Indistinguishable competitors collapsed the safe rank to genus.'],
  ['AALB-COI-short', 'weak', 'Review only', 'Coverage below 80% blocked the species-level claim.'],
  ['AALB-COI-metadata-gap', 'not-publishable', 'Review only', 'Taxonomy was species-safe, but occurrenceID and eventDate were missing.'],
];

const proofSteps = [
  'Assume the compiler emits species-safe.',
  'Then Exact(top), species-level LCA, positive barcode gap, diagnostic support with low p_false_positive, and publication metadata must all be true.',
  'If the top hit were weak, Exact(top) would be false, so species-safe could not be emitted.',
  'If a competitor were indistinguishable, LCA(U) would collapse to genus or higher, so species-safe could not be emitted.',
  'If the reference library did not separate the species, BarcodeGap <= 0, so species-safe could not be emitted.',
  'If diagnostic support were missing or random-collision risk were high, the diagnostic gate would fail.',
  'If required GBIF/DNA metadata were missing, published_taxon would be none and the decision would be not-publishable.',
  'Therefore species-safe is not a blind top-hit claim. It is a record that survived every failure mode in the frozen ruleset.',
];

const userTaskRows = [
  ['eDNA / metabarcoding researcher', 'Which ASVs can be called species?', 'Sequence safety table with species-safe, genus-safe, weak and no-match outcomes.'],
  ['Data publisher', 'What blocks GBIF publication?', 'Publication blockers and Darwin Core / DNA-derived templates.'],
  ['GBIF node or data manager', 'How do I explain that top hit is not always a species?', 'Formula cards, failure-mode proof and plain-language blockers.'],
  ['Taxonomist', 'Where does the marker fail to separate close taxa?', 'Ambiguity/LCA logic, barcode gap report and diagnostic k-mer evidence.'],
  ['Reference library curator', 'Which taxon/marker/region combinations need new references?', 'Reference Gap Index and ranked curation targets.'],
  ['Lab or monitoring team', 'Which fixes unlock the most records?', 'Repair optimizer with record counts per action.'],
  ['Reviewer or journal', 'Can the sequence-to-occurrence decision be reproduced?', 'Methods text, citations, evidence graph and complete evidence pack.'],
];

const numericExamples = [
  {
    title: 'Aedes good case: species-safe',
    interpretation: 'The competitor is distinguishable, barcode gap is positive, diagnostic support is present and required metadata passes.',
    formula: `identity_1 = 0.996, coverage_1 = 0.96
Exact(h_1) = 1

d_1 = 1 - 0.996 = 0.004
d_2 = 1 - 0.982 = 0.018
SE_1 ~= 0.00246
SE_2 ~= 0.00532
B = 1.96 * sqrt(SE_1^2 + SE_2^2) ~= 0.01149
Delta = 0.018 - 0.004 = 0.014

Delta > B, so competitor is distinguishable
BG = 0.018 - 0.009 = 0.009 > 0

Result: species-safe`,
  },
  {
    title: 'Aedes ambiguous case: genus-safe',
    interpretation: 'The competitor is statistically indistinguishable, so the safe rank collapses from species to genus.',
    formula: `identity_1 = 0.994
identity_2 = 0.993

d_1 = 0.006
d_2 = 0.007
Delta = 0.001

SE_1 ~= 0.00301
SE_2 ~= 0.00325
B ~= 0.00868

Delta < B, so the competitor is indistinguishable
LCA(Aedes albopictus, Aedes sp.) = Aedes / genus

Result: genus-safe, not species-safe`,
  },
];

const evidencePackRows = [
  ['sequence_safety_table.csv', 'Main decision table for every sequence.'],
  ['safe_taxonomic_assignments.csv', 'Only records with safe publishable taxonomic assignments.'],
  ['review_taxonomic_hints.csv', 'Blocked or weak records kept as repair/review hints.'],
  ['barcode_gap_report.csv', 'Marker/reference separability evidence.'],
  ['diagnostic_kmer_report.csv', 'Diagnostic support, expected random hits and p_false_positive.'],
  ['publication_blockers.csv', 'Exact field/gate blockers that must be repaired.'],
  ['dwc_occurrence_core_publishable.csv', 'Darwin Core occurrence rows safe enough to publish.'],
  ['dna_derived_extension_publishable.csv', 'DNA-derived extension rows for publishable records.'],
  ['molecular_evidence_report.html', 'Human-readable report for judges, users and reviewers.'],
  ['evidence_graph.json', 'Machine-readable audit graph of sequence, hit, taxon, blocker and export.'],
];

const nonClaims = [
  ['Gene to phenotype prediction', 'The project only makes safe taxonomic assignments and publication checks.'],
  ['Protein sequence as species truth', 'Protein translation is a coding-quality layer; nucleotide evidence remains the taxonomic discriminator.'],
  ['Absolute biological truth', 'All decisions are reproducible under supplied evidence and reference context.'],
  ['Replacement for GBIF Sequence ID', 'The compiler is a downstream decision layer after Sequence ID / BLAST-style matching.'],
  ['Universal readiness score', 'The project uses deterministic gates and blockers, not arbitrary weights.'],
  ['Presence or absence in nature', 'The output is molecular occurrence evidence with caveats, not a distribution truth model.'],
  ['Geography of a fragment as direct sampling proof', 'GBIF geography is occurrence context for taxa carrying the fragment unless the molecular sample itself has coordinates.'],
  ['Automatic phenotype proof', 'Future trait/function links are hypotheses unless supported by curated external evidence.'],
];

const decisionCopy = {
  'species-safe': {
    title: 'Publish as species',
    body: 'All species-level gates passed. This record can enter the publishable Darwin Core export at species rank.',
  },
  'genus-safe': {
    title: 'Publish as genus',
    body: 'Species is unsafe, but the shared genus is supported. The export is downgraded instead of overclaiming.',
  },
  'higher-rank-safe': {
    title: 'Publish at higher rank',
    body: 'The safest shared taxon is above genus. Keep the record, but publish only at the supported rank.',
  },
  ambiguous: {
    title: 'Review ambiguity',
    body: 'The evidence cannot support a clear publishable rank. Keep it in review until additional evidence resolves it.',
  },
  weak: {
    title: 'Do not publish yet',
    body: 'The match is too weak or incomplete for publication. Improve coverage, sequence quality or reference evidence.',
  },
  'no-match': {
    title: 'No reference match',
    body: 'No usable reference hit was supplied. Run identification again with a marker-appropriate reference database.',
  },
  'not-publishable': {
    title: 'Fix metadata first',
    body: 'The taxonomic evidence may be strong, but required GBIF/DNA-derived publication fields are missing.',
  },
};

const exportGroups = [
  {
    title: 'Open first',
    description: 'Human-readable decision, methods and the complete zipped evidence pack.',
    match: ['molecular_evidence_report.html', 'sequence_safety_table.csv', 'evidence_pack.zip', 'methods_text.md', 'citations.md'],
  },
  {
    title: 'Publishable templates',
    description: 'Only records with a non-empty published taxon are included here.',
    match: ['dwc_occurrence_core_publishable.csv', 'dna_derived_extension_publishable.csv', 'safe_taxonomic_assignments.csv'],
  },
  {
    title: 'Review and repair',
    description: 'Blocked records, ambiguity evidence, missing fields and molecular gates.',
    match: ['review_taxonomic_hints.csv', 'publication_blockers.csv', 'ambiguous_sequences.csv', 'barcode_gap_report.csv', 'diagnostic_kmer_report.csv'],
  },
  {
    title: 'Audit trail',
    description: 'Machine-readable provenance for repeatability and contest review.',
    match: ['reference_manifest.json', 'evidence_graph.json', 'evidence_pack.json', 'run.json', 'gbif_backbone_matches.csv', 'dwc_occurrence_core_review.csv', 'dwc_occurrence_core_template.csv', 'dna_derived_extension_template.csv', 'proof_by_failure_modes.md'],
  },
];

const mathOperatorMap = {
  '<=': '≤',
  '>=': '≥',
  '!=': '≠',
  and: '∧',
  cap: '∩',
  in: '∈',
  not: '¬',
  notin: '∉',
  or: '∨',
  subset: '⊆',
  to: '→',
  iff: '⇔',
  cup: '∪',
  setminus: '∖',
  '*': '·',
};

function MathRow({ children }) {
  return <div className="math-row">{children}</div>;
}

function Mi({ children }) {
  return <span className="math-mi">{children}</span>;
}

function Func({ children }) {
  return <span className="math-func">{children}</span>;
}

function Op({ children }) {
  return <span className="math-op">{mathOperatorMap[children] || children}</span>;
}

function Sub({ children }) {
  return <sub>{children}</sub>;
}

function Sup({ children }) {
  return <sup>{children}</sup>;
}

function MathSet({ children }) {
  return <><span className="math-paren">{'{'}</span><span>{children}</span><span className="math-paren">{'}'}</span></>;
}

function Paren({ children }) {
  return <><span className="math-paren">(</span><span>{children}</span><span className="math-paren">)</span></>;
}

function Frac({ top, bottom }) {
  return (
    <span className="math-frac">
      <span className="math-frac-top">{top}</span>
      <span className="math-frac-bottom">{bottom}</span>
    </span>
  );
}

function Abs({ children }) {
  return <span className="math-abs"><span>|</span><span>{children}</span><span>|</span></span>;
}

function Sqrt({ children }) {
  return <span className="math-sqrt"><span className="sqrt-symbol">√</span><span className="sqrt-body">{children}</span></span>;
}

function Indicator({ children }) {
  return <span className="math-indicator"><span>I</span><span>[</span><span>{children}</span><span>]</span></span>;
}

function Product({ children }) {
  return <span className="math-bigop"><span className="bigop-symbol">∏</span>{children}</span>;
}

function Sum({ children }) {
  return <span className="math-bigop"><span className="bigop-symbol">∑</span>{children}</span>;
}

function BigUnion({ lower, children }) {
  return (
    <span className="math-bigunion">
      <span className="bigunion-stack">
        <span className="bigop-symbol">∪</span>
        <span className="bigunion-lower">{lower}</span>
      </span>
      <span>{children}</span>
    </span>
  );
}

function Empty() {
  return <span className="math-empty">∅</span>;
}

function Cases({ lhs, rows }) {
  return (
    <div className="math-cases">
      <div className="cases-left">{lhs}<Op>=</Op></div>
      <div className="case-brace">{'{'}</div>
      <div className="case-rows">
        {rows.map(([value, condition], index) => (
          <div className="case-row" key={index}>
            <span className="case-value">{value}</span>
            <span className="case-condition">{condition}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function App() {
  const [mode, setMode] = useState('overview');
  const [scenarios, setScenarios] = useState([defaultScenario]);
  const [selectedScenarioId, setSelectedScenarioId] = useState(defaultScenario.id);
  const [referenceStatus, setReferenceStatus] = useState(null);
  const [jsonInput, setJsonInput] = useState(JSON.stringify(defaultScenario.request, null, 2));
  const [runSummary, setRunSummary] = useState(null);
  const [pack, setPack] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let mounted = true;
    Promise.all([getBarcodeDemoScenarios(), getBarcodeReferenceStatus()])
      .then(([demoScenarios, status]) => {
        if (!mounted) return;
        setScenarios(demoScenarios);
        setSelectedScenarioId(demoScenarios[demoScenarios.length - 1]?.id || demoScenarios[0]?.id);
        setJsonInput(JSON.stringify(demoScenarios[demoScenarios.length - 1]?.request || demoScenarios[0]?.request, null, 2));
        setReferenceStatus(status);
      })
      .catch((err) => {
        if (mounted) setError(err.message || 'Could not load compiler defaults');
      });
    return () => {
      mounted = false;
    };
  }, []);

  const selectedScenario = useMemo(
    () => scenarios.find((scenario) => scenario.id === selectedScenarioId) || scenarios[0] || defaultScenario,
    [scenarios, selectedScenarioId],
  );

  const metrics = pack?.metrics || runSummary?.summary || {};
  const records = pack?.records || [];
  const exports = pack?.exports || runSummary?.exports || [];

  function chooseScenario(id) {
    const scenario = scenarios.find((item) => item.id === id) || scenarios[0];
    setSelectedScenarioId(scenario.id);
    setJsonInput(JSON.stringify(scenario.request, null, 2));
    setError('');
  }

  async function runCompiler() {
    setLoading(true);
    setError('');
    try {
      const payload = JSON.parse(jsonInput);
      const summary = await runBarcodeCompiler(payload);
      setRunSummary(summary);
      const detail = await getBarcodeRun(summary.run_id);
      setPack(detail);
      setMode('workbench');
    } catch (err) {
      setError(err.message || 'Compiler run failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">EcoGenesis for GBIF Ebbe Nielsen Challenge 2026</p>
          <h1>Molecular Evidence Conversion & Repair Engine for GBIF</h1>
          <p className="topbar-subtitle">
            The Barcode-to-GBIF Evidence Compiler is the first working layer: it turns DNA barcode, metabarcoding or Sequence ID results into safe, rank-aware and GBIF-ready molecular occurrence evidence.
          </p>
        </div>
        <nav className="mode-switch" aria-label="View mode">
          {Object.entries(modeLabels).map(([id, label]) => (
            <button key={id} className={mode === id ? 'active' : ''} onClick={() => setMode(id)}>
              {label}
            </button>
          ))}
        </nav>
      </header>

      {error && <div className="alert">{error}</div>}

      {mode === 'overview' ? (
        <SubmissionOverview
          referenceStatus={referenceStatus}
          metrics={metrics}
          exports={exports}
          pack={pack}
          onOpenWorkbench={() => setMode('workbench')}
          onRunCompiler={runCompiler}
          loading={loading}
        />
      ) : mode === 'formulas' ? (
        <ProofAndFormulas />
      ) : (
        <CompilerWorkbench
          scenarios={scenarios}
          selectedScenario={selectedScenario}
          selectedScenarioId={selectedScenarioId}
          chooseScenario={chooseScenario}
          jsonInput={jsonInput}
          setJsonInput={setJsonInput}
          runCompiler={runCompiler}
          loading={loading}
          pack={pack}
          records={records}
          exports={exports}
        />
      )}
    </main>
  );
}

function SubmissionOverview({ referenceStatus, metrics, exports, pack, onOpenWorkbench, onRunCompiler, loading }) {
  return (
    <section className="page-grid">
      <div className="hero-panel">
        <div>
          <p className="eyebrow">Final project direction</p>
          <h2>From molecular detections to safe, repairable GBIF evidence.</h2>
          <p>
            The engine answers the Evidence Conversion Problem: from a large stream of DNA and metabarcoding results, which records are safe to publish, which must be downgraded, which are blocked, and which repair actions unlock the most GBIF-ready evidence?
          </p>
          <div className="hero-actions">
            <button className="primary" onClick={onOpenWorkbench}>Open Workbench</button>
            <button onClick={onRunCompiler} disabled={loading}>{loading ? 'Running...' : 'Run mixed demo'}</button>
            {exports.find((item) => item.name === 'evidence_pack.zip') && (
              <a className="button-link" href={exportUrl(exports.find((item) => item.name === 'evidence_pack.zip')?.url)}>Download Evidence Pack</a>
            )}
          </div>
        </div>
        <div className="verdict-card">
          <span>Working module</span>
          <strong>{pack?.summary?.verdict || 'Barcode Compiler ready: deterministic gates, safe rank decisions and repairable blockers.'}</strong>
          <small>{referenceStatus?.message || 'Loading compiler reference status...'}</small>
        </div>
      </div>

      <div className="metrics-grid">
        <Metric label="Processed" value={metrics.processed_records ?? '0'} />
        <Metric label="Species-safe" value={metrics.species_safe_records ?? '0'} />
        <Metric label="Blocked species claims" value={metrics.blocked_species_claims ?? '0'} />
        <Metric label="Record-ready" value={metrics.record_ready_records ?? '0'} />
      </div>

      <section className="panel">
        <p className="section-label">What the compiler does</p>
        <div className="pipeline">
          {['identity', 'coverage', 'ambiguity LCA', 'barcode gap', 'diagnostic k-mers', 'GBIF metadata', 'publication pack'].map((step) => (
            <div key={step}>{step}</div>
          ))}
        </div>
      </section>

      <section className="panel">
        <p className="section-label">Engine roadmap</p>
        <h2>One working compiler now, six layers in the full engine.</h2>
        <div className="layer-grid">
          {engineLayers.map(([index, title, body]) => (
            <article className="layer-card" key={title}>
              <span>{index}</span>
              <h3>{title}</h3>
              <p>{body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="panel two-column">
        <div>
          <p className="section-label">Safe claims</p>
          <ul className="plain-list">
            <li>Species-level output is allowed only when molecular gates pass and the record is publication-ready.</li>
            <li>Ambiguous top hits are downgraded to the lowest common ancestor.</li>
            <li>Candidate taxonomy is separated from the taxon that can actually be published.</li>
          </ul>
        </div>
        <div>
          <p className="section-label">Blocked claims</p>
          <ul className="plain-list blocked">
            <li>Top hit alone is never treated as enough for a species claim.</li>
            <li>Short coverage, missing barcode gap or missing diagnostic k-mers block species output.</li>
            <li>Missing occurrenceID or eventDate blocks GBIF-ready publication.</li>
          </ul>
        </div>
      </section>
    </section>
  );
}

function ProofAndFormulas() {
  return (
    <section className="proof-page">
      <section className="proof-hero panel">
        <div>
          <p className="section-label">Evidence basis</p>
          <h2>Why the engine can say "publish", "repair", "downgrade" or "block".</h2>
          <p>
            This page exposes the mathematical basis behind the Molecular Evidence Conversion & Repair Engine for GBIF.
            The Barcode-to-GBIF Evidence Compiler is the first implemented layer: species-level output is allowed only
            when every molecular and publication gate passes. Otherwise the record is downgraded, kept for repair or
            blocked from publishable exports.
          </p>
        </div>
        <div className="proof-summary">
          <strong>Evidence Conversion Problem</strong>
          <span>Maximize GBIF-ready evidence and safe-rank reuse while preventing unsafe species claims.</span>
        </div>
      </section>

      <section className="panel">
        <p className="section-label">Plain-language contract</p>
        <h2>Technical quality control before DNA-derived detections become GBIF-ready evidence.</h2>
        <p className="proof-copy">
          A sequence match is not automatically a species occurrence. The engine checks whether the match is strong,
          whether close species are indistinguishable, whether the marker separates the taxon, whether diagnostic sequence
          signal exists, whether a coding marker passes protein sanity checks, and whether the record has the metadata
          needed for GBIF publication.
        </p>
        <div className="status-strip" aria-label="Decision classes">
          {['species-safe', 'genus-safe', 'higher-rank-safe', 'ambiguous', 'weak', 'no-match', 'not-publishable'].map((status) => (
            <span key={status}>{status}</span>
          ))}
        </div>
      </section>

      <section className="panel">
        <p className="section-label">Final project goal</p>
        <h2>Molecular Evidence Conversion & Repair Engine for GBIF</h2>
        <p className="proof-copy">
          The current Barcode Compiler is the first working version of a larger engine. Its job is to stop unsafe
          top-hit species claims, preserve useful safe-rank evidence, expose publication blockers and generate a
          reproducible evidence pack. The full engine extends this with repair optimization, reference-gap analytics,
          protein sanity for coding markers, assay evidence checks and a Molecular Evidence Graph.
        </p>
        <div className="engine-equation">
          <span>maximize</span>
          <strong>N_gbifReady + N_safeRank</strong>
          <span>while minimizing</span>
          <strong>N_unsafeSpeciesClaims</strong>
        </div>
      </section>

      <section className="panel">
        <p className="section-label">Full mathematical notebook</p>
        <h2>Complete formulas and explanations behind the engine.</h2>
        <p className="proof-copy">
          This is the full evidence logic, not just a summary. Each block shows the formula, the variables it uses,
          and what the formula protects against in the workflow. The current backend implements the core compiler
          gates; the reference completeness, protein sanity, assay evidence, repair optimizer and graph layers are
          now explicitly specified as the next implementation targets.
        </p>
      </section>

      <section className="panel">
        <p className="section-label">Rendered mathematical notation</p>
        <h2>The same formulas in mathematical form.</h2>
        <p className="proof-copy">
          These are the judge-facing formulas: fractions are rendered with bars, indices are real subscripts, and
          set operations are shown as mathematical operators. The text notebook below remains as the implementation
          contract, but this section is the visual proof layer.
        </p>
      </section>

      <section className="rendered-math-grid">
        {renderedFormulaSections.map((section) => (
          <article className="rendered-math-card" key={section.label}>
            <div className="math-heading">
              <span>{section.label}</span>
              <h3>{section.title}</h3>
            </div>
            <div className="math-display" aria-label={section.title}>
              {section.equations}
            </div>
            <p>{section.explanation}</p>
          </article>
        ))}
      </section>

      <section className="math-notebook">
        {fullMathSections.map((section) => (
          <article className="math-section" key={section.label}>
            <div className="math-heading">
              <span>{section.label}</span>
              <h3>{section.title}</h3>
            </div>
            <pre className="formula-code"><code>{section.formula}</code></pre>
            <p>{section.meaning}</p>
          </article>
        ))}
      </section>

      <section className="formula-grid">
        {engineFormulaSections.map((section) => (
          <article className="formula-card engine-card" key={section.label}>
            <p className="section-label">{section.label}</p>
            <h3>{section.title}</h3>
            <pre className="formula-code"><code>{section.formula}</code></pre>
            <p>{section.proof}</p>
          </article>
        ))}
      </section>

      <section className="panel">
        <p className="section-label">Engine layers</p>
        <h2>What is implemented now and what the contest story leads to.</h2>
        <div className="layer-grid">
          {engineLayers.map(([index, title, body]) => (
            <article className="layer-card" key={title}>
              <span>{index}</span>
              <h3>{title}</h3>
              <p>{body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="panel">
        <p className="section-label">User tasks solved</p>
        <h2>What the formulas do for real users.</h2>
        <div className="task-table">
          <div><strong>User</strong><strong>Question</strong><strong>Compiler output</strong></div>
          {userTaskRows.map(([user, question, output]) => (
            <div key={user}>
              <span>{user}</span>
              <span>{question}</span>
              <span>{output}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="formula-grid">
        {formulaSections.map((section) => (
          <article className="formula-card" key={section.label}>
            <p className="section-label">{section.label}</p>
            <h3>{section.title}</h3>
            <pre className="formula-code"><code>{section.formula}</code></pre>
            <p>{section.proof}</p>
          </article>
        ))}
      </section>

      <section className="panel">
        <p className="section-label">Numerical examples</p>
        <h2>Two Aedes cases show why top hit alone is not enough.</h2>
        <div className="example-grid">
          {numericExamples.map((example) => (
            <article className="example-card" key={example.title}>
              <h3>{example.title}</h3>
              <p>{example.interpretation}</p>
              <pre className="formula-code"><code>{example.formula}</code></pre>
            </article>
          ))}
        </div>
      </section>

      <section className="panel">
        <p className="section-label">Test analysis</p>
        <h2>What we actually solved and proved with the current implementation.</h2>
        <p className="proof-copy">
          The tests do not prove biological truth. They prove that the implemented workflow behaves fail-closed:
          unsafe species claims are blocked, ambiguous records are downgraded, missing metadata prevents publication,
          evidence exports are generated, and the live GBIF path can run without fixture reuse.
        </p>
        <div className="analysis-table">
          <div><strong>Problem</strong><strong>Status</strong><strong>Evidence from tests</strong></div>
          {solvedRows.map(([problem, status, evidence]) => (
            <div key={problem}>
              <span>{problem}</span>
              <span>{status}</span>
              <span>{evidence}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="panel">
        <p className="section-label">Mixed-batch result</p>
        <h2>The current compiler reaches concrete, inspectable outcomes.</h2>
        <div className="analysis-table compact-analysis">
          <div><strong>Record</strong><strong>Decision</strong><strong>Published output</strong><strong>Why</strong></div>
          {mixedBatchRows.map(([record, decision, output, why]) => (
            <div key={record}>
              <span>{record}</span>
              <span>{decision}</span>
              <span>{output}</span>
              <span>{why}</span>
            </div>
          ))}
        </div>
        <div className="test-metrics">
          <Metric label="Processed records" value="4" />
          <Metric label="Species-safe" value="1" />
          <Metric label="Genus-safe" value="1" />
          <Metric label="Blocked species claims" value="3" />
          <Metric label="Record-ready exports" value="2" />
          <Metric label="Repair efficiency" value="1.0" />
        </div>
      </section>

      <section className="panel">
        <p className="section-label">Verification matrix</p>
        <h2>How the implementation was checked.</h2>
        <div className="analysis-table">
          <div><strong>Check</strong><strong>Result</strong><strong>Meaning</strong></div>
          {testAnalysisRows.map(([check, result, meaning]) => (
            <div key={check}>
              <span>{check}</span>
              <span>{result}</span>
              <span>{meaning}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="panel proof-theorem">
        <p className="section-label">Proof by contradiction</p>
        <h2>If the compiler emits species-safe, the species claim is not a blind top-hit claim.</h2>
        <ol className="proof-steps">
          {proofSteps.map((step) => (
            <li key={step}>{step}</li>
          ))}
        </ol>
      </section>

      <section className="panel">
        <p className="section-label">Failure mode matrix</p>
        <div className="claim-matrix">
          <div><strong>Failure mode</strong><strong>Compiler response</strong></div>
          <div><span>Identity below 99% or coverage below 80%</span><span>`weak`, no published species</span></div>
          <div><span>Indistinguishable species competitor</span><span>Downgrade to LCA, usually genus</span></div>
          <div><span>Barcode gap missing or non-positive</span><span>Block species-safe</span></div>
          <div><span>Diagnostic k-mer missing or high p_false_positive</span><span>Block species-safe</span></div>
          <div><span>Required Occurrence/DNA metadata missing</span><span>`not-publishable`, published_taxon = none</span></div>
          <div><span>Safe genus or higher rank remains</span><span>Export at the supported rank, not at species rank</span></div>
        </div>
      </section>

      <section className="panel">
        <p className="section-label">Evidence pack contract</p>
        <h2>The formulas must produce files a user can inspect, repair and cite.</h2>
        <div className="artifact-table">
          <div><strong>Artifact</strong><strong>Purpose</strong></div>
          {evidencePackRows.map(([name, purpose]) => (
            <div key={name}>
              <strong>{name}</strong>
              <span>{purpose}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="panel">
        <p className="section-label">Claim guardrails</p>
        <h2>What the project deliberately does not claim.</h2>
        <div className="claim-matrix">
          <div><strong>Do not promise</strong><strong>Say this instead</strong></div>
          {nonClaims.map(([badClaim, replacement]) => (
            <div key={badClaim}>
              <span>{badClaim}</span>
              <span>{replacement}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="panel final-proof">
        <p className="section-label">Final conclusion</p>
        <h2>The core contribution is not species guessing. It is evidence conversion with repairable loss accounting.</h2>
        <p>
          The strongest version of the project is a deterministic GBIF-facing engine that receives molecular evidence,
          prevents unsafe species overclaiming, keeps safe genus or higher-rank evidence, identifies metadata and
          reference-library blockers, and tells users which repairs will convert the most records into publishable
          biodiversity evidence. Protein and phenotype layers remain carefully scoped: protein translation is a
          quality-control and context layer for coding markers, while phenotype links are future hypotheses that require
          curated external evidence.
        </p>
      </section>
    </section>
  );
}

function CompilerWorkbench({
  scenarios,
  selectedScenario,
  selectedScenarioId,
  chooseScenario,
  jsonInput,
  setJsonInput,
  runCompiler,
  loading,
  pack,
  records,
  exports,
}) {
  const publishableRecords = records.filter((record) => record.published_taxon?.rank && record.published_taxon.rank !== 'none');
  const reviewRecords = records.filter((record) => !record.published_taxon?.rank || record.published_taxon.rank === 'none');

  return (
    <section className={`workspace ${pack ? 'has-results' : ''}`}>
      <aside className="control-panel">
        <p className="section-label">Input</p>
        <label>
          Demo case
          <select value={selectedScenarioId} onChange={(event) => chooseScenario(event.target.value)}>
            {scenarios.map((scenario) => (
              <option key={scenario.id} value={scenario.id}>{scenario.label}</option>
            ))}
          </select>
        </label>
        <p className="hint">{selectedScenario?.description}</p>
        <button className="primary wide" onClick={runCompiler} disabled={loading}>
          {loading ? 'Compiling evidence...' : 'Generate Evidence Package'}
        </button>
        <details className="advanced-input">
          <summary>Advanced request JSON</summary>
          <label>
            Compiler request JSON
            <textarea value={jsonInput} onChange={(event) => setJsonInput(event.target.value)} spellCheck="false" />
          </label>
          <p className="hint">
            Use records with sequence, metadata, reference hits, barcode gap evidence and optional diagnostic k-mers. This can be produced from GBIF Sequence ID CSV, BLAST-like outputs or lab pipelines.
          </p>
        </details>
      </aside>

      <div className="result-stack">
        {!pack ? (
          <section className="empty-state">
            <h2>Run a demo or paste a request to see rank-safe molecular decisions.</h2>
            <p>The compiler will produce CSV, JSON, HTML, Darwin Core templates, DNA-derived extension templates, methods text and citations.</p>
          </section>
        ) : (
          <>
            <section className="panel">
              <p className="section-label">Decision memo</p>
              <h2>{pack.summary.verdict}</h2>
              <p className="decision-lead">{buildRunExplanation(pack.metrics, publishableRecords.length, reviewRecords.length)}</p>
              <div className="metrics-grid compact">
                <Metric label="Processed" value={pack.metrics.processed_records} />
                <Metric label="Species-safe" value={pack.metrics.species_safe_records} />
                <Metric label="Genus-safe" value={pack.metrics.genus_safe_records} />
                <Metric label="Record-ready" value={pack.metrics.record_ready_records} />
              </div>
            </section>

            <OutcomeSummary records={records} />

            <section className="panel two-column">
              <div>
                <p className="section-label">Publishable output</p>
                <h3>{publishableRecords.length} {pluralize('record', publishableRecords.length)} can be exported now</h3>
                <p className="hint">
                  These records have a `published_taxon` and are included in the publishable Darwin Core and DNA-derived templates.
                </p>
                <ul className="record-list">
                  {publishableRecords.map((record) => (
                    <li key={record.sequence_id}>
                      <strong>{record.sequence_id}</strong>
                      <span>{record.published_taxon.name} / {record.published_taxon.rank}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <p className="section-label">Review queue</p>
                <h3>{reviewRecords.length} {pluralize('record', reviewRecords.length)} need attention</h3>
                <p className="hint">
                  These stay out of publishable templates. They remain useful as repair tasks with explicit blockers.
                </p>
                <ul className="record-list blocked">
                  {reviewRecords.map((record) => (
                    <li key={record.sequence_id}>
                      <strong>{record.sequence_id}</strong>
                      <span>{record.blockers[0] || decisionCopy[record.decision_class]?.body}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </section>

            <section className="panel">
              <p className="section-label">Sequence decisions</p>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Sequence</th>
                      <th>Decision</th>
                      <th>Candidate</th>
                      <th>Published</th>
                      <th>Stage</th>
                      <th>Meaning</th>
                      <th>Blockers</th>
                    </tr>
                  </thead>
                  <tbody>
                    {records.map((record) => (
                      <tr key={record.sequence_id}>
                        <td>{record.sequence_id}</td>
                        <td><span className={`pill ${record.decision_class}`}>{record.decision_class}</span></td>
                        <td>{record.candidate_taxon.name} <span className="muted">({record.candidate_taxon.rank})</span></td>
                        <td>{record.published_taxon.rank === 'none' ? 'Review only' : `${record.published_taxon.name} (${record.published_taxon.rank})`}</td>
                        <td>{formatStage(record.publication_stage)}</td>
                        <td>{decisionCopy[record.decision_class]?.title || record.decision_class}</td>
                        <td>{record.blockers.length ? record.blockers.slice(0, 2).join('; ') : 'none'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="panel">
              <p className="section-label">Evidence pack</p>
              <GroupedExports exports={exports} />
            </section>
          </>
        )}
      </div>
    </section>
  );
}

function OutcomeSummary({ records }) {
  const counts = records.reduce((acc, record) => {
    acc[record.decision_class] = (acc[record.decision_class] || 0) + 1;
    return acc;
  }, {});
  const cards = [
    ['species-safe', counts['species-safe'] || 0],
    ['genus-safe', (counts['genus-safe'] || 0) + (counts['higher-rank-safe'] || 0)],
    ['weak', (counts.weak || 0) + (counts.ambiguous || 0) + (counts['no-match'] || 0)],
    ['not-publishable', counts['not-publishable'] || 0],
  ];

  return (
    <section className="outcome-grid">
      {cards.map(([decision, count]) => (
        <article key={decision} className={`outcome-card ${decision}`}>
          <span>{count}</span>
          <h3>{decisionCopy[decision].title}</h3>
          <p>{decisionCopy[decision].body}</p>
        </article>
      ))}
    </section>
  );
}

function GroupedExports({ exports }) {
  const remaining = new Set(exports.map((item) => item.name));
  return (
    <div className="export-groups">
      {exportGroups.map((group) => {
        const items = group.match
          .map((name) => exports.find((item) => item.name === name))
          .filter(Boolean);
        items.forEach((item) => remaining.delete(item.name));
        if (!items.length) return null;
        return (
          <section key={group.title} className="export-group">
            <div>
              <h3>{group.title}</h3>
              <p>{group.description}</p>
            </div>
            <div className="export-grid">
              {items.map((item) => (
                <a key={item.name} href={exportUrl(item.url)}>{item.name}</a>
              ))}
            </div>
          </section>
        );
      })}
      {[...remaining].length > 0 && (
        <section className="export-group">
          <div>
            <h3>Other files</h3>
            <p>Additional generated artifacts.</p>
          </div>
          <div className="export-grid">
            {exports.filter((item) => remaining.has(item.name)).map((item) => (
              <a key={item.name} href={exportUrl(item.url)}>{item.name}</a>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div className="metric-card">
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  );
}

function buildRunExplanation(metrics, publishableCount, reviewCount) {
  const species = metrics.species_safe_records || 0;
  const genus = metrics.genus_safe_records || 0;
  const blocked = metrics.blocked_species_claims || 0;
  return `This run produces ${publishableCount} publishable ${pluralize('record', publishableCount)}: ${species} at species rank and ${genus} downgraded to genus or safer rank. ${reviewCount} ${pluralize('record', reviewCount)} stay in the review queue. ${blocked} unsafe species-level ${pluralize('claim', blocked)} were blocked before export.`;
}

function formatStage(stage) {
  return String(stage || '')
    .replaceAll('_', ' ')
    .replace('record ', 'record: ')
    .replace('dataset ', 'dataset: ')
    .replace('gold ', 'gold: ');
}

function pluralize(word, count) {
  return Number(count) === 1 ? word : `${word}s`;
}

export default App;
