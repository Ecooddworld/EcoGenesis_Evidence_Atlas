import { useEffect, useMemo, useRef, useState } from 'react';
import {
  Background,
  Controls,
  Handle,
  MarkerType,
  MiniMap,
  Position,
  ReactFlow,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import 'leaflet/dist/leaflet.css';
import {
  barcodeCsvTemplateUrl,
  buildBarcodeFragmentGraph,
  exportUrl,
  getBarcodeDemoScenarios,
  getCompetitionReports,
  getContestReadiness,
  getBarcodeReferenceStatus,
  getBarcodeReferenceDatasets,
  getBarcodeSearchStatus,
  getBarcodeRun,
  getObservatoryRun,
  getObservatoryRunVerification,
  getObservatorySources,
  getObservatoryStatus,
  importBarcodeCsv,
  runBarcodeCompiler,
  runBarcodeCsv,
  runObservatoryDemo,
  runBarcodeReferenceSearch,
  uploadBarcodeReferenceDataset,
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

const defaultReferenceSearchSequence = 'ACGTTGACCTAGGCTTACGATCGTACCGATGCTAGCTAGGATCCGATCGTACGATCGTAGCTAGCATCGGATCGTACCGTAGCTAGCTAGGCTAGCTAGGATCGATCGTACGAT';

const modeLabels = {
  overview: 'Judge overview',
  workbench: 'Run compiler',
  observatory: 'Observatory',
  fragmentGraph: 'Fragment graph',
  lecture: 'Visual lecture',
  research: 'Research audit',
  formulas: 'Math & proof',
};

const lectureAnchorIds = new Set([
  'analysis-animation',
  'analysis-picture-sequence',
  'sequence-picture',
  'safe-claim-picture',
  'animation-storyboard',
]);

function modeFromLocationHash(hash) {
  const anchorId = String(hash || '').replace(/^#/, '');
  if (anchorId === 'observatory' || anchorId === 'gsig-observatory') return 'observatory';
  return lectureAnchorIds.has(anchorId) ? 'lecture' : 'overview';
}

function scrollToCurrentAnchor() {
  if (typeof window === 'undefined' || typeof document === 'undefined') return;
  const anchorId = window.location.hash.replace(/^#/, '');
  if (!lectureAnchorIds.has(anchorId)) return;
  const schedule = window.requestAnimationFrame || ((callback) => window.setTimeout(callback, 0));
  const scrollToTarget = () => {
    const target = document.getElementById(anchorId);
    if (typeof target?.scrollIntoView === 'function') {
      target.scrollIntoView({ block: 'start' });
    }
  };
  schedule(scrollToTarget);
  [80, 240, 600].forEach((delay) => window.setTimeout(scrollToTarget, delay));
}

const scientificSuiteMetrics = [
  ['GBIF occurrence records', '1000', 'Deduplicated occurrence-audit records from 10 GBIF-backed scenarios.'],
  ['Hypothesis claims', '100', '48 supported, 12 weak, 20 blocked and 20 requiring verification.'],
  ['Duplicate records skipped', '149', 'The suite separates downloaded records from deduplicated records.'],
  ['High uncertainty records', '130', 'Fine-scale interpretation is weakened where coordinate uncertainty is high.'],
];

const architectureLevels = [
  ['Level A', 'Occurrence Evidence Audit Shell', 'GBIF occurrence context, dataset concentration, issue flags, coordinate/date risks and claim guardrails.'],
  ['Level B', 'Barcode-to-GBIF Evidence Compiler', 'The implemented molecular safety layer: identity, coverage, ambiguity, LCA, barcode gap, diagnostic k-mers and GBIF/DNA metadata.'],
  ['Level C', 'Molecular Evidence Graph', 'The expanded direction: fragments, taxa, geography, protein/domain context, function hypotheses and safe/blocked claims in one graph.'],
];

const userJourneySteps = [
  ['1', 'Upload or try demo', 'Start with Sequence ID / BLAST-style CSV, the built-in Aedes demo, or the mini reference search.'],
  ['2', 'Validate evidence', 'The app checks sequences, hit metrics, marker profile, assay type and required GBIF/DNA fields.'],
  ['3', 'Route safe claims', 'Species claims pass only through hard gates; unsafe top hits are downgraded or blocked.'],
  ['4', 'Export repair pack', 'Download publishable rows, review queues, methods, citations and audit CSVs.'],
];

const uploadExamples = [
  ['Best input', 'CSV from GBIF Sequence ID, BLAST, BOLD, UNITE or lab pipeline with sequenceID, sequence, topTaxon, identity and queryCoverage.'],
  ['Stronger input', 'Add eventID, materialSampleID, assayType, primers, target_gene, target_subfragment and contamination/QC fields.'],
  ['Not enough', 'FASTA-only can be searched, but without hit metrics it cannot become species-safe automatically.'],
];

const resultReadingGuide = [
  ['species-safe', 'Species claim passed every molecular and publication hard gate.'],
  ['genus-safe', 'Species is unsafe, but the shared genus is still useful evidence.'],
  ['weak', 'Identity, coverage or marker profile is too weak for safe publication.'],
  ['not-publishable', 'Taxonomy may be strong, but required GBIF/DNA metadata must be repaired first.'],
];

const scientificSuiteScenarios = [
  ['aedes-spain', '120', '120', '4', '0.842', '94.69', '6'],
  ['aedes-italy', '120', '120', '3', '0.750', '89.17', '2'],
  ['aedes-france', '120', '77', '5', '0.617', '94.91', '3'],
  ['quercus-western-europe', '120', '120', '7', '0.367', '82.56', '0'],
  ['quercus-germany', '120', '75', '6', '0.567', '83.12', '0'],
  ['lynx-iberia', '120', '120', '4', '0.808', '85.8', '97'],
  ['apis-western-europe', '120', '120', '4', '0.492', '95.08', '4'],
  ['apis-france', '120', '59', '4', '0.617', '84.64', '3'],
  ['passer-western-europe', '120', '120', '2', '0.950', '66.25', '0'],
  ['passer-united-states', '120', '120', '1', '1.000', '95.78', '15'],
];

const researchBottlenecks = [
  ['Readiness score overconfidence', 'Some scenarios have high score despite strong caveats, so the UI must lead with claim status and blockers.'],
  ['Single-dataset bias', 'Passer domesticus in the United States is dominated by one dataset; distribution-looking patterns may be publisher patterns.'],
  ['High coordinate uncertainty', 'Lynx pardinus in Iberia has many records above 10 km uncertainty, blocking fine-scale interpretation.'],
  ['Downloaded vs deduped mismatch', 'Reports now separate downloaded_records, deduped_records and records_used_for_metrics.'],
  ['Publisher metadata enrichment', 'Dataset provenance now uses GBIF dataset and organization APIs, with publisher, title, DOI and citation filled in the 1000-record CSV.'],
  ['Missing uncertainty fields', '154 records still lack coordinateUncertaintyInMeters, so fine-scale decisions must stay guarded even when coordinates exist.'],
  ['Molecular scope boundary', 'The 1000-record suite validates occurrence audit, not Sequence ID, protein or fragment truth.'],
];

const researchArtifacts = [
  ['records_1000.csv', '1000 deduplicated GBIF occurrence records with dataset and quality fields.'],
  ['theory_claims_100.csv', '100 safe scientific hypotheses with evidence fields, caveats and recommended actions.'],
  ['scenario_metrics.csv', 'Downloaded vs deduped counts, scores, dataset concentration and quality indicators.'],
  ['bottlenecks_and_errors.md', 'All known methodological and data-quality limitations.'],
  ['raw_packs/*.json', 'Full per-scenario evidence packs for audit and reproduction.'],
];

const claimStatusSummary = [
  ['supported', 48, 'Safe limited claims'],
  ['weak', 12, 'Usable only with caution'],
  ['blocked', 20, 'Overclaims prevented'],
  ['requires verification', 20, 'Needs DOI or review'],
];

const evidenceFunnelSteps = [
  ['GBIF API input', '1200 downloaded', 'Occurrence API records are audited separately from fixture/regression data.', 'pass'],
  ['Deduplication', '1000 retained', '149 duplicates were removed before the scientific claim report.', 'pass'],
  ['Provenance', '100% enriched', 'Dataset title, publisher, DOI and citation are present in the CSV.', 'pass'],
  ['Quality guardrails', '154 uncertainty gaps', 'Fine-scale claims stay guarded where uncertainty metadata is missing.', 'warn'],
  ['Claim compiler', '100 hypotheses', 'Claims are separated into supported, weak, blocked and requires verification.', 'pass'],
  ['Publication caveat', 'DOI required', 'API evidence needs a GBIF download DOI or derived dataset before formal use.', 'verify'],
];

const judgeClaimMatrix = [
  ['Occurrence evidence exists in selected region', 'supported', 'Supported as GBIF-mediated evidence context only.'],
  ['Empty cells prove absence', 'blocked', 'Blocked: empty or low-evidence cells are no-evidence cells, not absence.'],
  ['Observed points are true distribution', 'blocked', 'Blocked: GBIF records reflect data sharing and observer effort.'],
  ['Use as formal publication dataset', 'requires verification', 'Requires GBIF download DOI or derived dataset citation.'],
  ['Fine-scale local decisions', 'weak', 'Weak when high coordinate uncertainty or missing uncertainty fields appear.'],
];

const repairPriorities = [
  ['Create GBIF download DOI', '100 claims affected', 'Turns API-only evidence into publication-ready citation context.', 'verify'],
  ['Review coordinate uncertainty', '154 records', 'Protects local decisions from coarse or missing georeferencing metadata.', 'warn'],
  ['Reduce single-dataset bias', '2 scenarios', 'Prevents publisher/platform concentration from looking like ecology.', 'warn'],
  ['Move to fragment sharedness', 'next R&D layer', 'Shows all taxa carrying a fragment and derives safe LCA rank.', 'pass'],
];

const barcodeSourceCards = [
  ['Primary molecular input', 'Sequence ID / BLAST-style CSV', 'Use GBIF Sequence ID, NCBI BLAST, BOLD, UNITE or lab-pipeline tables with sequence, hit metrics, lineage and metadata.'],
  ['Reference search path', 'VSEARCH / BLAST+ over FASTA', 'Search bundled NCBI validation packs or a user-uploaded curated FASTA; the app records which backend was used.'],
  ['Taxonomy enrichment', 'GBIF Backbone match', 'Uploaded taxon names can be checked against GBIF backbone for lineage/provenance, without upgrading weak molecular evidence.'],
  ['Research context only', 'GBIF occurrence audit', 'Occurrence records support citation and bias review. They never turn a barcode hit into a species-safe claim.'],
];

const officialSourceLinks = [
  ['GBIF Sequence ID', 'https://www.gbif.org/tools/sequence-id'],
  ['GBIF DNA-derived publishing guide', 'https://docs.gbif.org/publishing-dna-derived-data/en/'],
  ['NCBI nucleotide BLAST', 'https://blast.ncbi.nlm.nih.gov/Blast.cgi?PAGE_TYPE=BlastSearch&PROGRAM=blastn'],
  ['BOLD v5 ID Engine', 'https://id.boldsystems.org/'],
  ['UNITE', 'https://unite.ut.ee/'],
];

const molecularGraphPreview = [
  ['DNA fragment', 'Input sequence, ASV or barcode window.'],
  ['Taxa carrying fragment', 'All matched taxa are visible, not only the top hit.'],
  ['LCA safe rank', 'Shared fragments become genus or clade evidence.'],
  ['GBIF context', 'Occurrence geography is shown as evidence context, not true distribution.'],
  ['Protein sanity', 'Coding markers get frame, stop-codon and pseudogene checks.'],
  ['Safe claims', 'Only supported claims without hard blockers enter export.'],
];

const lectureTakeaways = [
  ['DNA is a text', 'A sequence is a long word made from A, C, G and T. The tool compares that word with reference sequences.'],
  ['A match is evidence, not truth', 'A top hit can be close, short or shared by several species. That is why the compiler checks gates.'],
  ['Safe rank matters', 'If a fragment fits several species, the tool moves upward to the shared genus or family instead of inventing certainty.'],
  ['Publication is separate', 'A good taxon match still needs occurrenceID, date, method and DNA-derived metadata before GBIF-ready export.'],
];

const lectureWorkflow = [
  ['1', 'Input', 'Sequence, hits, lineage, metadata and reference evidence arrive together.'],
  ['2', 'Compare', 'Identity and coverage say how similar the query is to each reference.'],
  ['3', 'Challenge', 'Competitors are tested: is the second hit too close to ignore?'],
  ['4', 'Downgrade', 'If species are indistinguishable, LCA chooses the safe shared rank.'],
  ['5', 'Repair', 'Missing fields become actions, not hidden failures.'],
  ['6', 'Export', 'Only safe claims enter publishable templates; everything else goes to review.'],
];

const analysisSegments = [
  ['1-42 bp', 'Shared marker window', '100% match across 8 taxa', 'Safe rank: Culicidae family', 'shared'],
  ['43-96 bp', 'Species-informative window', '99.6% top hit, competitors checked', 'Candidate: Aedes albopictus', 'safe'],
  ['metadata', 'Publication layer', 'Occurrence core and DNA fields checked', 'Missing fields become repair actions', 'repair'],
];

const analysisReferenceHits = [
  ['Aedes albopictus', '99.6%', 'Top hit passes identity and coverage.', 'safe', '96%'],
  ['Aedes aegypti', '98.2%', 'Competitor is close enough to test.', 'warn', '86%'],
  ['Culicidae shared fragment', '100%', 'Short shared segment blocks lower-rank overclaim.', 'shared', '100%'],
];

const analysisGateTrail = [
  ['Identity', '99.6%', 'pass'],
  ['Coverage', '96%', 'pass'],
  ['Competitors', 'tested', 'pass'],
  ['LCA', 'safe rank', 'pass'],
  ['Metadata', 'separate', 'repair'],
  ['Claim', 'bounded', 'pass'],
];

const analysisProofCards = [
  ['Why the output is correct', 'Every species claim must pass identity, coverage, competitor, barcode-gap, diagnostic and metadata gates.'],
  ['Why overclaims are blocked', 'If a fragment is shared or incomplete, the decision moves upward to the lowest common ancestor instead of forcing a species.'],
  ['Why publication is separate', 'A strong taxon match still needs real occurrence and dataset metadata before formal GBIF-ready export.'],
  ['Why the graph layer is safe', 'GSEG/GSIG exports preserve claim states, provenance hashes and guardrail audits instead of upgrading evidence into unsupported function or phenotype claims.'],
];

const analysisPictureFrames = [
  ['01', 'Input sequence', 'A barcode row enters with DNA letters, marker profile and occurrence metadata.', 'Sequence + metadata', 'input'],
  ['02', 'Alignment scan', 'The query is aligned to references; identity and coverage are measured before any claim is made.', '99.6% identity / 96% coverage', 'alignment'],
  ['03', 'Reference hits', 'The top hit is challenged by close competitors and shared marker windows.', 'Top hit is not enough', 'hits'],
  ['04', 'Hard gates', 'Identity, coverage, LCA, barcode gap, diagnostic k-mers and metadata gates are checked in order.', 'Fail-closed gates', 'gates'],
  ['05', 'Safe claim', 'Unsafe species certainty is blocked; the output becomes a safe rank plus explicit repair blockers.', 'No hidden overclaim', 'claim'],
  ['06', 'Evidence pack', 'The result exports audit tables, publication blockers, VSEA rows, graph provenance and formal GBIF-ready status.', 'Reproducible export', 'pack'],
];

const sciencePurposeSteps = [
  ['Raw marker evidence', 'Thousands of barcode, metabarcoding or Sequence ID rows arrive from specimens, tissue, swabs, traps, museums and lab pipelines.'],
  ['Evidence conversion', 'The engine separates safe species claims, safe genus/family evidence, weak rows, missing metadata and blocked overclaims.'],
  ['Publication outputs', 'Publishable rows, review queues, methods text and citations become reusable biodiversity evidence.'],
  ['Scientific reuse', 'Researchers can audit data gaps, reference-library limits, sampling bias and repair priorities before making conclusions.'],
  ['Better decisions', 'Monitoring, conservation, invasion watch and data publishing become more reproducible and less vulnerable to false certainty.'],
];

const beforeAfterScience = [
  ['Before', 'A spreadsheet says “top hit = species”, but the user cannot see ambiguity, missing fields, reference gaps or unsafe claims.'],
  ['After', 'Every row has a safe rank, blockers, evidence pointers, repair actions and a clear boundary between supported and blocked claims.'],
];

const scienceUsers = [
  ['eDNA researcher', 'Knows which detections can be species-level and which must stay genus/family-level.'],
  ['GBIF publisher', 'Gets exact missing fields, candidate templates and formal GBIF-ready status instead of a vague error list.'],
  ['Taxonomist', 'Sees where markers or reference libraries fail to separate close taxa.'],
  ['Conservation team', 'Uses cautious evidence context without turning empty cells into false absence.'],
  ['Reviewer', 'Can reproduce why a record was accepted, downgraded or blocked.'],
  ['GBIF network', 'Receives cleaner, better cited and more reusable molecular occurrence evidence.'],
];

const futureImpactSteps = [
  ['V1', 'Barcode-to-GBIF Evidence Compiler', 'Working layer: CSV/search results become safe rank decisions and export packs.'],
  ['V2', 'Reference Gap Atlas', 'Shows taxa, markers and regions where species-safe conversion fails because references are incomplete.'],
  ['V3', 'Repair Optimizer', 'Ranks metadata and reference curation actions by how many records they unlock.'],
  ['V4', 'Molecular Evidence Graph', 'Connects fragments, taxa, GBIF geography, protein context, claims and blockers.'],
  ['V5', 'Hypothesis engine', 'Produces cautious, testable scientific hypotheses without claiming phenotype truth.'],
];

const natureCycleSteps = [
  ['01', 'Biodiversity source', 'Plants, insects, fungi, animals and microbes provide biological material: tissue, specimen, swab, trap sample or environmental trace.'],
  ['02', 'Marker selection', 'The workflow focuses on marker regions such as COI, ITS, rbcL, matK, 16S or other barcode/metabarcoding fragments.'],
  ['03', 'Lab sequencing', 'DNA is extracted and sequenced, producing marker results from GBIF Sequence ID, BLAST, BOLD, UNITE or lab pipelines.'],
  ['04', 'Reference comparison', 'Marker hits are compared against reference libraries and GBIF backbone taxonomy.'],
  ['05', 'Evidence compiler', 'EcoGenesis tests identity, coverage, ambiguity, LCA, barcode gap, k-mers and metadata.'],
  ['06', 'Publication evidence package', 'Safe records, repair queues, methods, citations and Darwin Core templates are exported.'],
  ['07', 'Scientific reuse', 'Researchers inspect gaps, weak evidence, reference limits, sampling bias and safe claims.'],
  ['08', 'Nature feedback', 'Better evidence supports monitoring, conservation, invasive watch and future sampling priorities.'],
];

const natureBenefitCards = [
  ['For science', 'Turns molecular detections into reproducible evidence categories instead of fragile top-hit claims.'],
  ['For GBIF', 'Improves publication readiness, citation discipline, metadata repair and reusable molecular occurrence data.'],
  ['For nature', 'Helps teams detect threats earlier, choose better sampling priorities and avoid decisions based on false certainty.'],
];

const animationStoryboardFrames = [
  ['01', 'Biological material becomes marker evidence', 'The input can begin as a specimen, tissue, trap, swab, bulk sample or environmental trace. EcoGenesis starts when that material becomes a marker record with evidence attached.', 'The viewer sees real biodiversity material become a DNA marker row.'],
  ['02', 'Reference search creates competing hits', 'A query marker is compared with reference records. The story does not stop at the best hit; it shows whether nearby hits make a species claim unsafe.', 'The viewer sees the top hit challenged by close competitors.'],
  ['03', 'Shared fragments become a taxonomic tree', 'Short fragments can fit several species. EcoGenesis moves the claim upward to the shared ancestor instead of inventing certainty at species level.', 'The viewer sees several species merge into one safer rank.'],
  ['04', 'Hard gates decide what can be claimed', 'Identity, coverage, ambiguity, barcode gap, diagnostic k-mers and metadata are checked as clear decision points. A failed gate becomes a visible blocker.', 'The viewer sees each gate either confirm, downgrade or send the row to repair.'],
  ['05', 'Publication evidence package is produced', 'Safe records, repair actions, methods text, citations and Darwin Core templates become one evidence package that a publisher or reviewer can inspect.', 'The viewer sees accepted rows and repair rows become a transparent Evidence Pack.'],
  ['06', 'Evidence returns to science and nature', 'The output helps researchers see sampling gaps, reference gaps and safer monitoring priorities without turning weak evidence into false certainty.', 'The viewer sees safer evidence return to maps, priorities and field decisions.'],
];

const markerSourceCards = [
  ['Tissue / specimen', 'A leaf, insect, fungal sample, museum specimen or collected biological material.'],
  ['Swab / trap / bulk sample', 'A mixed sample can contain marker fragments from several taxa and needs safe-rank handling.'],
  ['Sequence ID / BLAST table', 'The main v1 input: sequence, hit metrics, taxon, identity, coverage and metadata.'],
  ['Reference marker library', 'COI, ITS, rbcL, matK, 16S or another marker-specific reference context.'],
];

const dnaQuery = 'AACATTATACTTTATTTTCGGTATTTGATCTGGAATAGTC';
const dnaReference = 'AACATTATACTTTATTTTCGGTATTTGATCTGGAATAGTC';
const dnaCompetitor = 'AACTTTATATTTCATTTTTGGAGTATGATCTGGAATAGTC';
const kmerTiles = ['AACATTATACTTTAT', 'ACATTATACTTTATT', 'CATTATACTTTATTT', 'ATTATACTTTATTTT', 'TTATACTTTATTTTC'];
const gateCards = [
  ['Identity', '99.6%', 'How many letters match?'],
  ['Coverage', '96%', 'How much of the query was compared?'],
  ['Ambiguity', 'clear', 'Is another species too close?'],
  ['Barcode gap', 'pass', 'Does the marker separate species?'],
  ['k-mers', '27', 'Does the query contain diagnostic fragments?'],
  ['Metadata', 'repairable', 'Can this become a GBIF record?'],
];

const scenarioHeatmapRows = [
  ['aedes-spain', 'warn', 'warn', 'safe', 'verify'],
  ['aedes-italy', 'safe', 'safe', 'safe', 'verify'],
  ['aedes-france', 'safe', 'warn', 'safe', 'verify'],
  ['quercus-western-europe', 'safe', 'safe', 'safe', 'verify'],
  ['quercus-germany', 'safe', 'warn', 'safe', 'verify'],
  ['lynx-iberia', 'risk', 'warn', 'safe', 'verify'],
  ['apis-western-europe', 'warn', 'safe', 'safe', 'verify'],
  ['apis-france', 'warn', 'safe', 'safe', 'verify'],
  ['passer-western-europe', 'safe', 'risk', 'weak', 'verify'],
  ['passer-united-states', 'warn', 'risk', 'safe', 'verify'],
];

const heatmapColumns = ['Coordinate risk', 'Dataset bias', 'Sampling coverage', 'Citation'];

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
  ['GSEG/GSIG proof layer', 'Solved as a contest-safe extension', 'The compiler now emits VSEA CSV/JSONL/Parquet, theorem checklist, graph provenance, roundtrip and AI guardrail audits.'],
  ['GBIF-backed Observatory path', 'Solved for occurrence evidence', 'Aedes albopictus in Spain declares its source mode; GBIF API data are used when available and fixture fallback is explicit when used.'],
  ['Protein sanity and repair optimizer', 'Bounded in the current release', 'The release reports what can be checked from barcode evidence and marks deeper biological interpretation as roadmap only.'],
  ['Phenotype prediction', 'Deliberately not claimed', 'The project treats phenotype/function as future hypotheses requiring curated external evidence.'],
];

const testAnalysisRows = [
  ['Frontend unit tests', '14 passed', 'Overview, workbench, upload flow, reference search, proof pages and visual lecture render with the final export contract.'],
  ['Frontend production build', 'Passed', 'Vite build completed and the page can be shipped as a static frontend.'],
  ['Backend pytest', '77 passed, 1 skipped', 'API, compiler logic, exports, GSEG/GSIG checks, contest readiness and regression behavior remain operational.'],
  ['Barcode operability script', 'PASS', 'Expected decisions, API endpoint, ZIP bundle and required exports all passed.'],
  ['Browser smoke', '0 console errors', 'Proof page and workbench rendered locally; no horizontal overflow was detected in the tested viewport.'],
  ['GBIF-backed smoke', 'OK', 'Snapshot manifests preserve source mode, taxonKey 1651430, occurrence counts and explicit fixture fallback state when fallback is used.'],
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
  ['data_accounting_ledger.csv', 'Input, candidate, safe, publishable, GBIF-ready and repair denominators.'],
  ['sequence_safety_table.csv', 'Main decision table for every sequence.'],
  ['state_machine_audit.csv', 'Taxonomy, publication bucket and export-state separation.'],
  ['safe_taxonomic_assignments.csv', 'Only records with safe publishable taxonomic assignments.'],
  ['review_taxonomic_hints.csv', 'Blocked or weak records kept as repair/review hints.'],
  ['barcode_gap_report.csv', 'Marker/reference separability evidence.'],
  ['diagnostic_kmer_report.csv', 'Diagnostic support, expected random hits and p_false_positive.'],
  ['publication_blockers.csv', 'Exact field/gate blockers that must be repaired.'],
  ['claim_boundaries.csv', 'Supported and explicitly unsupported claims for each sequence.'],
  ['reference_completeness_audit.csv', 'Explicit RCI 2.0 status and reference-context caveats.'],
  ['segment_overlap_report.csv', 'Fragment coordinates, overlap evidence and safe LCA per segment.'],
  ['dwc_occurrence_core_publishable.csv', 'Darwin Core occurrence rows safe enough to publish.'],
  ['dna_derived_extension_publishable.csv', 'DNA-derived extension rows for publishable records.'],
  ['molecular_evidence_report.html', 'Human-readable report for judges, users and reviewers.'],
  ['evidence_graph.json', 'Machine-readable audit graph of sequence, hit, taxon, blocker and export.'],
  ['verified_segment_evidence_array.parquet', 'Typed VSEA export for downstream graph and analytical checks.'],
  ['theorem_checklist.json', 'GSEG/GSIG proof-obligation checklist with blocked roadmap claims kept explicit.'],
  ['graph_provenance_audit.csv', 'Node and edge provenance audit with claim-state and ruleset hashes.'],
  ['ai_output_guardrail_audit.csv', 'Guardrail table proving AI-facing exports cannot strengthen unsupported claims.'],
  ['source_provenance_manifest.json', 'Run-level source, backend and input-contract provenance.'],
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
  ['Functional interpretation from barcode alone', 'GSIG exports block function claims unless curated trait/function evidence is present.'],
];

const decisionCopy = {
  'species-safe': {
    title: 'Publish as species',
    body: 'All species-level gates passed. This record can enter the publishable candidate template at species rank.',
  },
  'genus-safe': {
    title: 'Publish as genus',
    body: 'Species is unsafe, but the shared genus is supported. The candidate template is downgraded instead of overclaiming.',
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
    match: ['molecular_evidence_report.html', 'sequence_safety_table.csv', 'data_accounting_ledger.csv', 'evidence_pack.zip', 'methods_text.md', 'citations.md'],
  },
  {
    title: 'Publishable templates',
    description: 'Only records with a non-empty published taxon are included here.',
    match: ['dwc_occurrence_core_gbif_ready.csv', 'dna_derived_extension_gbif_ready.csv', 'dwc_occurrence_core_publishable.csv', 'dna_derived_extension_publishable.csv', 'safe_taxonomic_assignments.csv'],
  },
  {
    title: 'Review and repair',
    description: 'Blocked records, ambiguity evidence, missing fields and molecular gates.',
    match: ['repair_plan.csv', 'repair_gain_estimates.csv', 'metadata_bottlenecks.csv', 'review_taxonomic_hints.csv', 'publication_blockers.csv', 'claim_boundaries.csv', 'state_machine_audit.csv', 'dwc_occurrence_core_review_or_repair.csv', 'ambiguous_sequences.csv', 'barcode_gap_report.csv', 'diagnostic_kmer_report.csv'],
  },
  {
    title: 'Nexus V3 audit',
    description: 'Hard-gate consistency, marker/assay profiles, prevented top-hit overclaims, reference gaps and adapter direction.',
    match: ['nexus_v3_summary.json', 'hard_gate_audit.csv', 'marker_profile_audit.csv', 'assay_gate_audit.csv', 'dna_extension_readiness.csv', 'naive_top_hit_overclaims.csv', 'reference_gap_index.csv', 'reference_completeness_audit.csv', 'segment_overlap_report.csv', 'external_tool_adapter_matrix.csv'],
  },
  {
    title: 'GSEG / GSIG proof layer',
    description: 'Segment evidence array, graph schema, provenance, theorem checklist and guardrails from the production specification.',
    match: ['theorem_checklist.json', 'verified_segment_evidence_array.csv', 'verified_segment_evidence_array.jsonl', 'verified_segment_evidence_array.parquet', 'gseg_graph_schema.json', 'gsig_graph_schema.yaml', 'evidence_graph.jsonld', 'graph_provenance_audit.csv', 'graph_roundtrip_audit.json', 'vsea_graph_reconciliation.csv', 'sharedness_overclaim_audit.csv', 'function_claim_boundary_audit.csv', 'ai_output_guardrail_audit.csv', 'ai_dataset_export_audit.csv', 'ruleset_diff_report.json', 'report_consistency_audit.csv', 'judge_reproducibility_report.md'],
  },
  {
    title: 'Audit trail',
    description: 'Machine-readable provenance for repeatability and contest review.',
    match: ['source_provenance_manifest.json', 'reference_manifest.json', 'evidence_graph.json', 'evidence_pack.json', 'run.json', 'gbif_backbone_matches.csv', 'dwc_occurrence_core_review.csv', 'dwc_occurrence_core_template.csv', 'dna_derived_extension_template.csv', 'proof_by_failure_modes.md'],
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
  const [mode, setMode] = useState(() => (
    typeof window === 'undefined' ? 'overview' : modeFromLocationHash(window.location.hash)
  ));
  const [scenarios, setScenarios] = useState([defaultScenario]);
  const [selectedScenarioId, setSelectedScenarioId] = useState(defaultScenario.id);
  const [referenceStatus, setReferenceStatus] = useState(null);
  const [jsonInput, setJsonInput] = useState(JSON.stringify(defaultScenario.request, null, 2));
  const [runSummary, setRunSummary] = useState(null);
  const [pack, setPack] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [csvFile, setCsvFile] = useState(null);
  const [csvImport, setCsvImport] = useState(null);
  const [csvLoading, setCsvLoading] = useState(false);
  const [searchStatus, setSearchStatus] = useState(null);
  const [referenceDatasets, setReferenceDatasets] = useState([]);
  const [searchSequence, setSearchSequence] = useState(defaultReferenceSearchSequence);
  const [selectedReferenceDataset, setSelectedReferenceDataset] = useState('aedes_coi_mini');
  const [searchResult, setSearchResult] = useState(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [referenceUploadFile, setReferenceUploadFile] = useState(null);
  const [referenceUploadTitle, setReferenceUploadTitle] = useState('');
  const [referenceUploadMarker, setReferenceUploadMarker] = useState('COI-5P');
  const [referenceUpload, setReferenceUpload] = useState(null);
  const [referenceUploadLoading, setReferenceUploadLoading] = useState(false);
  const [fragmentSequenceId, setFragmentSequenceId] = useState('fragment-001');
  const [fragmentSequence, setFragmentSequence] = useState(defaultReferenceSearchSequence);
  const [selectedFragmentDataset, setSelectedFragmentDataset] = useState('ncbi_aedes_coi_small');
  const [fragmentGraph, setFragmentGraph] = useState(null);
  const [fragmentGraphLoading, setFragmentGraphLoading] = useState(false);
  const [observatoryStatus, setObservatoryStatus] = useState(null);
  const [observatorySources, setObservatorySources] = useState(null);
  const [observatoryRun, setObservatoryRun] = useState(null);
  const [observatoryVerification, setObservatoryVerification] = useState(null);
  const [competitionReports, setCompetitionReports] = useState(null);
  const [contestReadiness, setContestReadiness] = useState(null);
  const [observatoryLoading, setObservatoryLoading] = useState(false);
  const [observatoryError, setObservatoryError] = useState('');
  const [observatoryScreen, setObservatoryScreen] = useState('home');

  useEffect(() => {
    if (typeof window === 'undefined') return undefined;
    function handleHashChange() {
      const nextMode = modeFromLocationHash(window.location.hash);
      if (nextMode === 'lecture') {
        setMode('lecture');
        scrollToCurrentAnchor();
      }
    }
    handleHashChange();
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  useEffect(() => {
    if (mode === 'lecture') scrollToCurrentAnchor();
  }, [mode]);

  useEffect(() => {
    let mounted = true;
    Promise.all([getBarcodeDemoScenarios(), getBarcodeReferenceStatus(), getBarcodeSearchStatus(), getBarcodeReferenceDatasets()])
      .then(([demoScenarios, status, backendStatus, datasets]) => {
        if (!mounted) return;
        setScenarios(demoScenarios);
        setSelectedScenarioId(demoScenarios[demoScenarios.length - 1]?.id || demoScenarios[0]?.id);
        setJsonInput(JSON.stringify(demoScenarios[demoScenarios.length - 1]?.request || demoScenarios[0]?.request, null, 2));
        setReferenceStatus(status);
        setSearchStatus(backendStatus);
        setReferenceDatasets(datasets);
        const preferredDataset = datasets.find((dataset) => dataset.id === 'ncbi_aedes_coi_small')
          || datasets.find((dataset) => dataset.source_type === 'bundled')
          || datasets[0];
        setSelectedReferenceDataset(preferredDataset?.id || 'aedes_coi_mini');
        if (preferredDataset?.example_queries?.[0]?.sequence) {
          setSearchSequence(preferredDataset.example_queries[0].sequence);
          setFragmentSequence(preferredDataset.example_queries[0].sequence);
          setFragmentSequenceId(preferredDataset.example_queries[0].sequence_id || preferredDataset.example_queries[0].id || 'fragment-001');
        }
        setSelectedFragmentDataset(preferredDataset?.id || 'aedes_coi_mini');
      })
      .catch((err) => {
        if (mounted) setError(err.message || 'Could not load compiler defaults');
      });
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    let mounted = true;
    Promise.all([getObservatoryStatus(), getObservatorySources(), getCompetitionReports(), getContestReadiness()])
      .then(([status, sources, reportIndex, readiness]) => {
        if (!mounted) return;
        setObservatoryStatus(status);
        setObservatorySources(sources);
        setCompetitionReports(reportIndex);
        setContestReadiness(readiness);
        if (status.latest_run?.run_id) {
          Promise.allSettled([
            getObservatoryRun(status.latest_run.run_id),
            getObservatoryRunVerification(status.latest_run.run_id),
          ])
            .then(([detailResult, verificationResult]) => {
              if (!mounted) return;
              setObservatoryRun(detailResult.status === 'fulfilled' ? detailResult.value : null);
              setObservatoryVerification(verificationResult.status === 'fulfilled' ? verificationResult.value : null);
            })
            .catch(() => {
              if (!mounted) return;
              setObservatoryRun(null);
              setObservatoryVerification(null);
            });
        } else {
          setObservatoryRun(null);
          setObservatoryVerification(null);
        }
      })
      .catch((err) => {
        if (mounted) setObservatoryError(err.message || 'Observatory status unavailable');
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

  async function previewCsvUpload(file) {
    if (!file) return;
    setCsvFile(file);
    setCsvImport(null);
    setError('');
    setCsvLoading(true);
    try {
      const imported = await importBarcodeCsv(file);
      setCsvImport(imported);
    } catch (err) {
      setError(err.message || 'CSV import failed');
    } finally {
      setCsvLoading(false);
    }
  }

  async function runCsvCompiler() {
    if (!csvFile) return;
    setLoading(true);
    setError('');
    try {
      const summary = await runBarcodeCsv(csvFile);
      setRunSummary(summary);
      const detail = await getBarcodeRun(summary.run_id);
      setPack(detail);
      setMode('workbench');
    } catch (err) {
      setError(err.message || 'CSV compiler run failed');
    } finally {
      setLoading(false);
    }
  }

  async function runReferenceSearch(overrides = {}) {
    setSearchLoading(true);
    setError('');
    const datasetId = overrides.reference_dataset || selectedReferenceDataset;
    const sequence = overrides.sequence || searchSequence;
    const sequenceId = overrides.sequence_id || 'UI_REFERENCE_SEARCH_QUERY';
    setSelectedReferenceDataset(datasetId);
    setSearchSequence(sequence);
    try {
      const payload = {
        sequence_id: sequenceId,
        sequence,
        reference_dataset: datasetId,
        backend: 'auto',
        compile: true,
        metadata: {
          countryCode: 'ES',
          decimalLatitude: 40.4168,
          decimalLongitude: -3.7038,
          geodeticDatum: 'WGS84',
          coordinateUncertaintyInMeters: 50,
        },
      };
      const result = await runBarcodeReferenceSearch(payload);
      setSearchResult(result.search);
      setRunSummary(result.run);
      setPack(result.pack);
      setMode('workbench');
    } catch (err) {
      setError(err.message || 'Reference search failed');
    } finally {
      setSearchLoading(false);
    }
  }

  async function uploadReferenceDataset() {
    if (!referenceUploadFile) return;
    setReferenceUploadLoading(true);
    setError('');
    try {
      const result = await uploadBarcodeReferenceDataset(referenceUploadFile, {
        title: referenceUploadTitle || referenceUploadFile.name.replace(/\.[^.]+$/, ''),
        marker: referenceUploadMarker,
        source: 'EcoGenesis UI reference FASTA upload',
      });
      setReferenceUpload(result);
      setReferenceDatasets(result.datasets || [result.dataset]);
      setSelectedReferenceDataset(result.dataset.id);
      setSelectedFragmentDataset(result.dataset.id);
      setSearchResult(null);
      setFragmentGraph(null);
    } catch (err) {
      setError(err.message || 'Reference dataset upload failed');
    } finally {
      setReferenceUploadLoading(false);
    }
  }

  async function runFragmentGraph(overrides = {}) {
    setFragmentGraphLoading(true);
    setError('');
    const datasetId = overrides.reference_dataset || selectedFragmentDataset || selectedReferenceDataset;
    const sequence = overrides.sequence || fragmentSequence;
    const sequenceId = overrides.sequence_id || fragmentSequenceId || 'fragment-001';
    setSelectedFragmentDataset(datasetId);
    setFragmentSequence(sequence);
    setFragmentSequenceId(sequenceId);
    try {
      const graph = await buildBarcodeFragmentGraph({
        sequence_id: sequenceId,
        sequence,
        reference_dataset: datasetId,
        backend: 'auto',
        max_hits: 50,
      });
      setFragmentGraph(graph);
      setMode('fragmentGraph');
    } catch (err) {
      setError(err.message || 'Fragment graph failed');
    } finally {
      setFragmentGraphLoading(false);
    }
  }

  async function runObservatory(modeOverride = 'live_gbif_small') {
    setObservatoryLoading(true);
    setObservatoryError('');
    setObservatoryVerification(null);
    try {
      const created = await runObservatoryDemo({
        mode: modeOverride,
        taxon: 'Aedes albopictus',
        taxon_key: 1651430,
        bbox: [-9.5, 35.5, 4.5, 44.5],
        limit: 50,
      });
      const [detail, verification] = await Promise.all([
        getObservatoryRun(created.run_id),
        getObservatoryRunVerification(created.run_id).catch(() => null),
      ]);
      setObservatoryRun(detail);
      setObservatoryVerification(verification);
      getContestReadiness()
        .then((readiness) => setContestReadiness(readiness))
        .catch(() => {});
      setObservatoryStatus((current) => ({
        ...(current || {}),
        latest_run: {
          run_id: detail.run.run_id,
          summary: detail.summary,
          exports: detail.exports,
        },
      }));
      setMode('observatory');
      setObservatoryScreen('home');
    } catch (err) {
      setObservatoryError(err.message || 'Observatory run failed');
    } finally {
      setObservatoryLoading(false);
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
      ) : mode === 'lecture' ? (
        <VisualLecture />
      ) : mode === 'observatory' ? (
        <ObservatoryPanel
          status={observatoryStatus}
          sources={observatorySources}
          run={observatoryRun}
          verification={observatoryVerification}
          competitionReports={competitionReports}
          contestReadiness={contestReadiness}
          loading={observatoryLoading}
          error={observatoryError}
          screen={observatoryScreen}
          setScreen={setObservatoryScreen}
          onRunLive={() => runObservatory('live_gbif_small')}
          onRunOffline={() => runObservatory('offline_demo')}
        />
      ) : mode === 'fragmentGraph' ? (
        <FragmentGraphExplorer
          searchStatus={searchStatus}
          referenceDatasets={referenceDatasets}
          selectedFragmentDataset={selectedFragmentDataset}
          setSelectedFragmentDataset={setSelectedFragmentDataset}
          fragmentSequenceId={fragmentSequenceId}
          setFragmentSequenceId={setFragmentSequenceId}
          fragmentSequence={fragmentSequence}
          setFragmentSequence={setFragmentSequence}
          fragmentGraph={fragmentGraph}
          fragmentGraphLoading={fragmentGraphLoading}
          runFragmentGraph={runFragmentGraph}
        />
      ) : mode === 'formulas' ? (
        <ProofAndFormulas />
      ) : mode === 'research' ? (
        <ResearchAudit />
      ) : (
        <CompilerWorkbench
          scenarios={scenarios}
          selectedScenario={selectedScenario}
          selectedScenarioId={selectedScenarioId}
          chooseScenario={chooseScenario}
          jsonInput={jsonInput}
          setJsonInput={setJsonInput}
          runCompiler={runCompiler}
          runCsvCompiler={runCsvCompiler}
          previewCsvUpload={previewCsvUpload}
          loading={loading}
          csvLoading={csvLoading}
          csvFile={csvFile}
          csvImport={csvImport}
          searchStatus={searchStatus}
          referenceDatasets={referenceDatasets}
          searchSequence={searchSequence}
          setSearchSequence={setSearchSequence}
          selectedReferenceDataset={selectedReferenceDataset}
          setSelectedReferenceDataset={setSelectedReferenceDataset}
          searchResult={searchResult}
          searchLoading={searchLoading}
          runReferenceSearch={runReferenceSearch}
          referenceUploadFile={referenceUploadFile}
          setReferenceUploadFile={setReferenceUploadFile}
          referenceUploadTitle={referenceUploadTitle}
          setReferenceUploadTitle={setReferenceUploadTitle}
          referenceUploadMarker={referenceUploadMarker}
          setReferenceUploadMarker={setReferenceUploadMarker}
          referenceUpload={referenceUpload}
          referenceUploadLoading={referenceUploadLoading}
          uploadReferenceDataset={uploadReferenceDataset}
          referenceStatus={referenceStatus}
          pack={pack}
          records={records}
          exports={exports}
        />
      )}
    </main>
  );
}

function ObservatoryPanel({ status, sources, run, verification, competitionReports, contestReadiness, loading, error, screen, setScreen, onRunLive, onRunOffline }) {
  const summary = run?.summary || status?.latest_run?.summary || {};
  const exports = run?.exports || status?.latest_run?.exports || [];
  const runId = run?.run?.run_id || status?.latest_run?.run_id;
  const vseaRows = run?.vsea || [];
  const occurrenceRows = run?.normalized_occurrence_context || [];
  const proofRows = run?.proof_summary?.rows || [];
  const sourceRows = sources?.sources || [];
  const auditRows = run?.audit_artifacts || {};
  const judgeNonClaimAudit = auditRows.judge_mode_non_claims_audit || auditRows['judge_mode_non_claims_audit.csv'];
  const evidencePack = exports.find((item) => item.name === 'observatory_evidence_pack.zip');
  const requestBbox = run?.request?.bbox || status?.default_demo?.bbox || [-9.5, 35.5, 4.5, 44.5];
  const screenTabs = [
    ['home', 'Overview'],
    ['sources', 'Sources'],
    ['vsea', 'VSEA'],
    ['graph', 'Graph'],
    ['exports', 'Exports'],
    ['judge', 'Judge'],
  ];
  const claimStates = summary.claim_states || {};
  const proofPass = summary.hard_gate_status === 'pass';

  return (
    <section className="page-grid observatory-page" id="observatory">
      <div className="hero-panel observatory-hero">
        <div>
          <p className="eyebrow">GSIG Observatory</p>
          <h2>Source snapshots, molecular segments and claim boundaries in one evidence graph.</h2>
          <p>
            The Observatory layer shows why the current Aedes Spain run is bounded and reproducible: GBIF supplies
            hashed occurrence context, the barcode compiler supplies molecular gates, and every export preserves the
            graph claim state without upgrading context into support.
          </p>
          <div className="hero-actions">
            <button className="primary" onClick={onRunLive} disabled={loading}>
              {loading ? 'Running...' : 'Run GBIF-backed Aedes Spain'}
            </button>
            <button onClick={onRunOffline} disabled={loading}>Run reproducible demo</button>
            {evidencePack && <a className="button-link" href={exportUrl(evidencePack.url)}>Download Observatory Pack</a>}
          </div>
        </div>
        <div className={`verdict-card ${proofPass ? 'observatory-pass' : 'observatory-waiting'}`}>
          <span>Release gate</span>
          <strong>{run ? `Hard gates ${summary.hard_gate_status}` : status?.status || 'Waiting for run'}</strong>
          <small>{run ? run.snapshot_manifest?.snapshot_id : status?.default_demo?.claim_boundary}</small>
        </div>
      </div>

      {error && <div className="alert">{error}</div>}

      <section className="panel observatory-flow-panel">
        <div className="panel-heading-row">
          <div>
            <p className="section-label">Why the run is auditable</p>
            <h2>Nothing is trusted until it is hashed, gated and exported with caveats.</h2>
          </div>
          <span className={`status-pill ${proofPass ? 'supported' : 'requires-verification'}`}>
            {run ? summary.hard_gate_status : 'ready'}
          </span>
        </div>
        <div className="observatory-flow">
          {[
            ['1', 'GBIF snapshot', run?.snapshot_manifest?.snapshot_hash?.slice(0, 12) || 'pending'],
            ['2', 'Normalize context', `${summary.normalized_occurrence_records ?? 0} rows`],
            ['3', 'Build VSEA', `${summary.vsea_rows ?? 0} segment claims`],
            ['4', 'Graph proof', `${summary.graph_nodes ?? 0} nodes`],
            ['5', 'Guard exports', `${proofRows.length || 20} OPO checks`],
          ].map(([step, label, value]) => (
            <article key={label} className="observatory-flow-step">
              <span>{step}</span>
              <strong>{label}</strong>
              <small>{value}</small>
            </article>
          ))}
        </div>
      </section>

      <ContestReadinessPanel dossier={contestReadiness} />

      <ObservatoryVisualSuite
        run={run}
        summary={summary}
        verification={verification}
        occurrenceRows={occurrenceRows}
        vseaRows={vseaRows}
        proofRows={proofRows}
        requestBbox={requestBbox}
      />

      <CompetitionReadinessPanel reports={competitionReports} />

      <section className="panel">
        <div className="observatory-tabs" role="tablist" aria-label="Observatory screens">
          {screenTabs.map(([id, label]) => (
            <button key={id} className={screen === id ? 'active' : ''} onClick={() => setScreen(id)} type="button">
              {label}
            </button>
          ))}
        </div>

        {screen === 'home' && (
          <div className="observatory-screen">
            <div className="metric-grid">
              {[
                ['Occurrence rows', summary.normalized_occurrence_records ?? 0],
                ['Segments', summary.segments ?? 0],
                ['VSEA rows', summary.vsea_rows ?? 0],
                ['Graph edges', summary.graph_edges ?? 0],
              ].map(([label, value]) => (
                <div className="metric-card" key={label}>
                  <span>{label}</span>
                  <strong>{value}</strong>
                </div>
              ))}
            </div>
            <div className="claim-state-grid">
              {Object.entries(claimStates).map(([state, count]) => (
                <article key={state} className="claim-state-card">
                  <span className={`pill ${state}`}>{state}</span>
                  <strong>{count}</strong>
                  <p>{state === 'taxon_supported' ? 'Molecular gates support the safe rank.' : 'Visible in judge mode and excluded from verified-positive labels.'}</p>
                </article>
              ))}
              {!Object.keys(claimStates).length && (
                <article className="claim-state-card">
                  <span className="pill weak">no run</span>
                  <strong>0</strong>
                  <p>Run the live or reproducible demo to fill the Observatory ledger.</p>
                </article>
              )}
            </div>
          </div>
        )}

        {screen === 'sources' && (
          <div className="observatory-source-grid">
            {sourceRows.map((source) => (
              <article key={source.source_id} className="observatory-source-card">
                <span className={`source-status ${source.status}`}>{source.status}</span>
                <h3>{source.name}</h3>
                <p>{source.evidence_role}</p>
                <dl>
                  <div><dt>Allowed</dt><dd>{source.allowed_claims?.join(', ')}</dd></div>
                  <div><dt>Blocked</dt><dd>{source.blocked_claims?.join(', ')}</dd></div>
                </dl>
              </article>
            ))}
          </div>
        )}

        {screen === 'vsea' && (
          <div className="observatory-screen">
            <VseaMatrixVisual rows={vseaRows} />
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Segment</th>
                    <th>Target</th>
                    <th>Claim state</th>
                    <th>GBIF export</th>
                    <th>Boundary</th>
                  </tr>
                </thead>
                <tbody>
                  {vseaRows.slice(0, 12).map((row) => (
                    <tr key={row.vsea_id}>
                      <td>{row.sequence_id}</td>
                      <td>{row.target_label} · {row.safe_rank}</td>
                      <td><span className={`pill ${row.claim_state}`}>{row.claim_state}</span></td>
                      <td>{row.gbif_export_state}</td>
                      <td>{row.context_claim_boundary}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {screen === 'graph' && (
          <div className="observatory-graph-grid">
            <EvidenceGraphVisual run={run} vseaRows={vseaRows} summary={summary} />
            <div className="observatory-proof-list">
              <h3>Graph guarantees</h3>
              {[
                'GBIF context cannot promote claim_state',
                'Blocked and weak rows remain visible',
                'AI labels preserve positive versus hypothesis boundaries',
                'Exports carry ruleset and provenance hashes',
              ].map((item) => <p key={item}>{item}</p>)}
            </div>
          </div>
        )}

        {screen === 'exports' && (
          <div className="export-grid observatory-export-grid">
            {runId && (
              <>
                <a href={exportUrl(`/api/observatory/runs/${runId}/verification/report.md`)}>observatory_run_verification.md</a>
                <a href={exportUrl(`/api/observatory/runs/${runId}/verification`)}>observatory_run_verification.json</a>
              </>
            )}
            {exports
              .filter((item) => [
                'observatory_evidence_pack.zip',
                'observatory_report.md',
                'snapshot_manifest.json',
                'observatory_vsea.parquet',
                'observatory_graph.jsonld',
                'gbif_export_preview.csv',
                'ai_ready_dataset.jsonl',
                'proof_summary.json',
              ].includes(item.name))
              .map((item) => (
                <a key={item.name} href={exportUrl(item.url)}>{item.name}</a>
              ))}
          </div>
        )}

        {screen === 'judge' && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>OPO</th>
                  <th>Severity</th>
                  <th>Status</th>
                  <th>Artifact</th>
                </tr>
              </thead>
              <tbody>
                {proofRows.map((row) => (
                  <tr key={row.id}>
                    <td>{row.id}</td>
                    <td>{row.severity}</td>
                    <td><span className={`pill ${row.status}`}>{row.status}</span></td>
                    <td>{row.artifact}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {judgeNonClaimAudit?.[0] && (
              <p className="observatory-judge-note">
                Planned sources visible: {judgeNonClaimAudit[0].planned_sources_visible}.
                Roadmap items are labeled no-claim and do not enter verified exports.
              </p>
            )}
          </div>
        )}
      </section>
    </section>
  );
}

function ContestReadinessPanel({ dossier }) {
  if (!dossier) return null;
  const summary = dossier.summary || {};
  const pass = dossier.status === 'pass';
  const primaryDownloads = [
    { name: 'contest_readiness.md', url: '/api/contest-readiness/report.md' },
    { name: 'contest_readiness.json', url: '/api/contest-readiness' },
    ...(dossier.downloads || []).filter((item) => item.name === 'latest_observatory_verification.md').slice(0, 1),
  ];
  return (
    <section className={`panel contest-readiness-dossier ${pass ? 'pass' : 'review'}`}>
      <div className="panel-heading-row">
        <div>
          <p className="section-label">Contest readiness dossier</p>
          <h2>{pass ? 'All current contest gates are passing.' : 'Contest dossier needs one more verified gate.'}</h2>
        </div>
        <span className={`status-pill ${pass ? 'supported' : 'requires-verification'}`}>{dossier.status}</span>
      </div>
      <div className="contest-dossier-grid">
        {[
          ['Checks', summary.checks ?? 0],
          ['Failed', summary.failed ?? 0],
          ['Competition', summary.competition_status || 'missing'],
          ['Observatory', summary.observatory_status || 'missing'],
          ['Reference', summary.reference_backend || 'missing'],
        ].map(([label, value]) => (
          <div key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
      <div className="contest-dossier-actions">
        {primaryDownloads.map((item) => (
          <a key={`${item.name}-${item.url}`} href={exportUrl(item.url)}>{item.name}</a>
        ))}
      </div>
    </section>
  );
}

function CompetitionReadinessPanel({ reports }) {
  const reportRows = reports?.reports || [];
  if (!reportRows.length) return null;
  return (
    <section className="panel competition-readiness-panel">
      <div className="panel-heading-row">
        <div>
          <p className="section-label">Competition readiness</p>
          <h2>Frozen 100-sequence contest runs are checked and downloadable.</h2>
        </div>
        <span className={`status-pill ${reports.status === 'pass' ? 'supported' : 'requires-verification'}`}>
          {reports.status}
        </span>
      </div>
      <div className="competition-report-grid">
        {reportRows.map((report) => (
          <article className="competition-report-card" key={report.report_id}>
            <div>
              <span className={`pill ${report.summary.status === 'pass' ? 'pass' : 'review_required'}`}>{report.summary.status}</span>
              <h3>{report.title}</h3>
            </div>
            <dl>
              <div><dt>Records</dt><dd>{report.summary.records}</dd></div>
              <div><dt>Failed</dt><dd>{report.summary.expected_failed}</dd></div>
              <div><dt>Exports</dt><dd>{report.summary.exports}</dd></div>
              <div><dt>ZIP entries</dt><dd>{report.summary.zip_entries}</dd></div>
            </dl>
            <div className="competition-class-strip">
              {Object.entries(report.decision_classes || {}).map(([label, count]) => (
                <span key={label}>{label}: {count}</span>
              ))}
            </div>
            <div className="competition-report-links">
              {(report.downloads || []).slice(0, 4).map((item) => (
                <a key={item.name} href={exportUrl(item.url)}>{item.name}</a>
              ))}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function ObservatoryVisualSuite({ run, summary, verification, occurrenceRows, requestBbox }) {
  const verificationSummary = verification?.summary || {};
  const verificationPass = verificationSummary.status === 'pass';
  const runId = run?.run?.run_id;
  return (
    <section className="panel observatory-visual-suite">
      <div className="panel-heading-row">
        <div>
          <p className="section-label">GSIG evidence graph explorer</p>
          <h2>Full source, snapshot, segment, claim and export graph for the current Observatory run.</h2>
        </div>
        <span className={`status-pill ${summary?.hard_gate_status === 'pass' ? 'supported' : 'requires-verification'}`}>
          {run ? 'interactive evidence graph' : 'waiting for graph'}
        </span>
      </div>
      {verification && (
        <div className={`output-verification-strip ${verificationPass ? 'pass' : 'review'}`} aria-label="Output verification">
          <div>
            <span>Output verification</span>
            <strong>{verificationPass ? 'Run files checked' : 'Review run files'}</strong>
            <p>
              {verificationPass
                ? 'Hashes, proof gates, tables, graph and ZIP contents agree for this exact run.'
                : `${verificationSummary.failed ?? 0} checks need review before export.`}
            </p>
            {runId && (
              <div className="verification-actions">
                <a href={exportUrl(`/api/observatory/runs/${runId}/verification/report.md`)}>Verification report</a>
                <a href={exportUrl(`/api/observatory/runs/${runId}/verification`)}>Verification data</a>
              </div>
            )}
          </div>
          <dl>
            <div><dt>Checks</dt><dd>{verificationSummary.checks ?? 0}</dd></div>
            <div><dt>Failed</dt><dd>{verificationSummary.failed ?? 0}</dd></div>
            <div><dt>ZIP entries</dt><dd>{verificationSummary.zip_entries ?? 0}</dd></div>
            <div><dt>Rows rechecked</dt><dd>{(verificationSummary.vsea_rows ?? 0) + (verificationSummary.occurrence_rows ?? 0)}</dd></div>
          </dl>
        </div>
      )}
      <ObservatoryGraphExplorer
        run={run}
        summary={summary}
        verification={verification}
        occurrenceRows={occurrenceRows}
        requestBbox={requestBbox}
      />
    </section>
  );
}

function ObservatoryGraphExplorer({ run, summary, verification, occurrenceRows, requestBbox }) {
  const flowGraph = useMemo(() => buildObservatoryFlowGraph(run, summary, verification), [run, summary, verification]);
  const [claimStateFilter, setClaimStateFilter] = useState('all');
  const [nodeTypeFilter, setNodeTypeFilter] = useState('all');
  const [edgeTypeFilter, setEdgeTypeFilter] = useState('all');
  const [showBlocked, setShowBlocked] = useState(true);
  const [showContext, setShowContext] = useState(true);
  const [focusSelected, setFocusSelected] = useState(false);
  const [selectedEvidence, setSelectedEvidence] = useState(null);
  const [layoutedNodes, setLayoutedNodes] = useState(flowGraph.nodes);

  const selectedNodeId = selectedEvidence?.kind === 'node' ? selectedEvidence.id : selectedEvidence?.source || null;
  const filteredGraph = useMemo(() => filterObservatoryFlowGraph(flowGraph, {
    claimStateFilter,
    nodeTypeFilter,
    edgeTypeFilter,
    showBlocked,
    showContext,
    focusSelected,
    selectedNodeId,
  }), [flowGraph, claimStateFilter, nodeTypeFilter, edgeTypeFilter, showBlocked, showContext, focusSelected, selectedNodeId]);

  useEffect(() => {
    let cancelled = false;
    setLayoutedNodes(filteredGraph.nodes);
    layoutObservatoryFlow(filteredGraph.nodes, filteredGraph.edges).then((nodes) => {
      if (!cancelled) setLayoutedNodes(nodes);
    });
    return () => {
      cancelled = true;
    };
  }, [filteredGraph.nodes, filteredGraph.edges]);

  useEffect(() => {
    if (!selectedEvidence && flowGraph.nodes[0]) {
      setSelectedEvidence({ kind: 'node', ...flowGraph.nodes[0].data });
    }
  }, [flowGraph.nodes, selectedEvidence]);

  const visibleNodeIds = new Set(filteredGraph.nodes.map((node) => node.id));
  const renderedNodes = layoutedNodes
    .filter((node) => visibleNodeIds.has(node.id))
    .map((node) => ({
      ...node,
      selected: selectedEvidence?.kind === 'node' && selectedEvidence.id === node.id,
    }));
  const renderedEdges = filteredGraph.edges.map((edge) => ({
    ...edge,
    selected: selectedEvidence?.kind === 'edge' && selectedEvidence.id === edge.id,
  }));

  return (
    <div className="observatory-graph-explorer">
      <div className="graph-filter-bar" aria-label="Evidence graph filters">
        <label>
          <span>Claim state</span>
          <select aria-label="Claim state" value={claimStateFilter} onChange={(event) => setClaimStateFilter(event.target.value)}>
            <option value="all">All states</option>
            {flowGraph.claimStates.map((state) => <option key={state} value={state}>{state}</option>)}
          </select>
        </label>
        <label>
          <span>Node type</span>
          <select aria-label="Node type" value={nodeTypeFilter} onChange={(event) => setNodeTypeFilter(event.target.value)}>
            <option value="all">All nodes</option>
            {flowGraph.nodeTypes.map((type) => <option key={type} value={type}>{type}</option>)}
          </select>
        </label>
        <label>
          <span>Edge type</span>
          <select aria-label="Edge type" value={edgeTypeFilter} onChange={(event) => setEdgeTypeFilter(event.target.value)}>
            <option value="all">All edges</option>
            {flowGraph.edgeTypes.map((type) => <option key={type} value={type}>{type}</option>)}
          </select>
        </label>
        <label className="graph-toggle">
          <input aria-label="Show blocked" type="checkbox" checked={showBlocked} onChange={(event) => setShowBlocked(event.target.checked)} />
          <span>Show blocked</span>
        </label>
        <label className="graph-toggle">
          <input aria-label="Show context" type="checkbox" checked={showContext} onChange={(event) => setShowContext(event.target.checked)} />
          <span>Show context</span>
        </label>
        <label className="graph-toggle">
          <input aria-label="Focus selected segment" type="checkbox" checked={focusSelected} onChange={(event) => setFocusSelected(event.target.checked)} />
          <span>Focus selected segment</span>
        </label>
      </div>

      <div className="graph-ledger-strip" aria-label="Evidence graph ledger">
        {[
          ['Graph nodes', flowGraph.ledger.graphNodes],
          ['Graph edges', flowGraph.ledger.graphEdges],
          ['Rendered nodes', renderedNodes.length],
          ['Rendered edges', renderedEdges.length],
          ['Merged ids', flowGraph.ledger.mergedDuplicateNodes],
          ['Verification', flowGraph.ledger.verificationStatus],
        ].map(([label, value]) => (
          <div key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>

      <div className="graph-object-index" aria-label="Evidence object index">
        <span>Evidence object index</span>
        {renderedNodes.slice(0, 14).map((node) => (
          <button
            key={`index-${node.id}`}
            type="button"
            className={claimStateClass(node.data.claimState)}
            onClick={() => setSelectedEvidence({ kind: 'node', ...node.data })}
          >
            <small>{node.data.type}</small>
            <strong>{node.data.label}</strong>
          </button>
        ))}
        {renderedEdges.slice(0, 8).map((edge) => (
          <button
            key={`index-${edge.id}`}
            type="button"
            className={`edge ${claimStateClass(edge.data.claimState)}`}
            onClick={() => setSelectedEvidence({ kind: 'edge', ...edge.data })}
          >
            <small>edge</small>
            <strong>{edge.data.type}</strong>
          </button>
        ))}
      </div>

      <div className="graph-workspace">
        <div className="graph-canvas-shell" aria-label="Interactive GSIG evidence graph">
          <div className="graph-canvas-heading">
            <strong>EcoGenesis GSIG Evidence Graph</strong>
            <span>Visible evidence, not complete world.</span>
          </div>
          {renderedNodes.length ? (
            <ReactFlow
              nodes={renderedNodes}
              edges={renderedEdges}
              nodeTypes={observatoryGraphNodeTypes}
              fitView
              minZoom={0.25}
              maxZoom={1.8}
              nodesDraggable
              onNodeClick={(_, node) => setSelectedEvidence({ kind: 'node', ...node.data })}
              onEdgeClick={(_, edge) => setSelectedEvidence({ kind: 'edge', ...edge.data })}
            >
              <Background color="#d7e5dd" gap={22} />
              <Controls showInteractive={false} />
              <MiniMap
                pannable
                zoomable
                nodeColor={(node) => claimStateColor(node.data?.claimState)}
                maskColor="rgba(246, 250, 247, 0.72)"
              />
            </ReactFlow>
          ) : (
            <div className="graph-empty-state">
              <strong>Run the Observatory demo to build the graph.</strong>
              <p>Source snapshots, VSEA rows and claim boundaries will appear here after a run.</p>
            </div>
          )}
        </div>

        <aside className="graph-inspector" aria-label="Evidence object inspector">
          <EvidenceObjectInspector selected={selectedEvidence} warnings={flowGraph.warnings} />
          <div className="graph-source-context-card">
            <SnapshotMapVisual rows={occurrenceRows} bbox={requestBbox} snapshot={run?.snapshot_manifest} summary={summary} />
          </div>
        </aside>
      </div>

      <div className="graph-legend-row" aria-label="Evidence graph guardrails">
        {[
          ['Supported', 'taxon_supported'],
          ['Weak / review', 'weak_hypothesis'],
          ['Blocked', 'blocked'],
          ['Context only', 'occurrence_context'],
          ['Repair', 'repair_required'],
        ].map(([label, state]) => (
          <span key={state}><i style={{ background: claimStateColor(state) }} /> {label}</span>
        ))}
        <strong>OPO-07: UI cannot upgrade claims.</strong>
        <strong>OPO-08: blocked claims stay visible.</strong>
      </div>
    </div>
  );
}

function ObservatoryGraphNode({ data }) {
  return (
    <div className="observatory-flow-node-inner">
      <Handle type="target" position={Position.Left} />
      <span>{data.type}</span>
      <strong>{data.label}</strong>
      <small>{data.subtitle}</small>
      {data.variantCount > 1 && <em>{data.variantCount} evidence variants merged</em>}
      <Handle type="source" position={Position.Right} />
    </div>
  );
}

const observatoryGraphNodeTypes = { evidenceNode: ObservatoryGraphNode };

function EvidenceObjectInspector({ selected, warnings }) {
  if (!selected) {
    return (
      <div className="inspector-empty">
        <h3>Evidence object inspector</h3>
        <p>Select a graph node or edge to inspect provenance, caveats and raw evidence.</p>
      </div>
    );
  }
  const raw = selected.raw || {};
  const variants = selected.variants || [];
  const inspectorValue = (value, fallback) => {
    if (Array.isArray(value)) {
      if (!value.length) return fallback;
      return value.map((item) => (typeof item === 'string' ? item : JSON.stringify(item))).join('; ');
    }
    return value != null && value !== '' ? value : fallback;
  };
  const fields = [
    ['Kind', inspectorValue(selected.kind, 'not supplied')],
    ['Type', inspectorValue(selected.type, 'not supplied')],
    ['Claim state', inspectorValue(selected.claimState, 'not supplied')],
    ['Provenance hash', inspectorValue(selected.provenanceHash || raw.provenance_hash, 'not supplied')],
    ['Ruleset', inspectorValue(raw.ruleset_version, 'not supplied')],
    ['Source object', inspectorValue(selected.source || raw.source, 'not supplied')],
    ['Target object', inspectorValue(selected.target || raw.target, 'not supplied')],
    ['Claim boundary', inspectorValue(raw.claim_boundary || raw.context_claim_boundary, 'not supplied')],
    ['Caveats', inspectorValue(raw.caveats || raw.caveat, 'none supplied')],
    ['Export state', inspectorValue(raw.gbif_export_state || raw.export_state || raw.export_status, 'not export object')],
  ];

  return (
    <div className="inspector-object">
      <p className="section-label">Evidence object</p>
      <h3>{selected.label || selected.id}</h3>
      <dl>
        {fields.map(([label, value]) => (
          <div key={label}>
            <dt>{label}</dt>
            <dd>{String(value)}</dd>
          </div>
        ))}
      </dl>
      {variants.length > 1 && (
        <div className="inspector-variants">
          <strong>Merged variants</strong>
          {variants.map((variant, index) => (
            <span key={`${variant.provenance_hash || variant.segment_id || variant.id}-${index}`}>
              {variant.segment_id || variant.id} · {variant.claim_state || 'no claim state'}
            </span>
          ))}
        </div>
      )}
      {!!warnings.length && (
        <div className="inspector-warnings">
          {warnings.map((warning) => <span key={warning}>{warning}</span>)}
        </div>
      )}
      <details>
        <summary>Raw evidence object</summary>
        <pre>{JSON.stringify(raw, null, 2)}</pre>
      </details>
    </div>
  );
}

function buildObservatoryFlowGraph(pack = {}, summary = {}, verification = {}) {
  const graphItems = Array.isArray(pack?.graph?.['@graph'])
    ? pack.graph['@graph']
    : [
        ...(Array.isArray(pack?.graph?.nodes) ? pack.graph.nodes : []),
        ...(Array.isArray(pack?.graph?.edges) ? pack.graph.edges : []),
      ];
  const nodeItems = [];
  const edgeItems = [];
  graphItems.forEach((item, index) => {
    const object = { ...(item || {}), __graph_index: index };
    if (object.source && object.target) edgeItems.push(object);
    else nodeItems.push(object);
  });

  const nodeMap = new Map();
  const registerNode = (raw, index = 0) => {
    const id = String(raw.id || `node:${index}`);
    const existing = nodeMap.get(id);
    if (existing) {
      existing.variants.push(raw);
      existing.claimStates.add(canonicalClaimState(raw));
      existing.types.add(raw.type || 'EvidenceObject');
      return existing;
    }
    const entry = {
      id,
      raw,
      variants: [raw],
      claimStates: new Set([canonicalClaimState(raw)]),
      types: new Set([raw.type || 'EvidenceObject']),
    };
    nodeMap.set(id, entry);
    return entry;
  };

  nodeItems.forEach((item, index) => registerNode(item, index));
  edgeItems.forEach((edge, index) => {
    if (!nodeMap.has(String(edge.source))) {
      registerNode({ id: edge.source, type: 'ExternalEvidenceObject', claim_state: edge.claim_state || 'context_only' }, index);
    }
    if (!nodeMap.has(String(edge.target))) {
      registerNode({ id: edge.target, type: 'ExternalEvidenceObject', claim_state: edge.claim_state || 'context_only' }, index);
    }
  });

  const typeOrder = ['Run', 'Source', 'Snapshot', 'Segment', 'Taxon', 'EvidenceClaim', 'Blocker', 'Repair', 'Export', 'Artifact', 'ExternalEvidenceObject'];
  const typeSlots = new Map();
  const nodes = Array.from(nodeMap.values()).map((entry, index) => {
    const type = primaryEvidenceType(entry);
    const claimState = strongestClaimState(Array.from(entry.claimStates));
    const typeIndex = typeOrder.findIndex((item) => type.toLowerCase().includes(item.toLowerCase()));
    const column = typeIndex >= 0 ? typeIndex : 5;
    const row = typeSlots.get(column) || 0;
    typeSlots.set(column, row + 1);
    return {
      id: entry.id,
      type: 'evidenceNode',
      position: { x: 40 + column * 230, y: 40 + row * 132 },
      data: {
        id: entry.id,
        type,
        label: evidenceNodeLabel(entry.raw, entry.id),
        subtitle: evidenceNodeSubtitle(entry.raw, claimState),
        claimState,
        raw: entry.raw,
        variants: entry.variants,
        variantCount: entry.variants.length,
        provenanceHash: entry.raw.provenance_hash,
      },
      className: `observatory-flow-node ${claimStateClass(claimState)} ${evidenceTypeClass(type)}`,
    };
  });

  const edges = edgeItems.map((edge, index) => {
    const claimState = canonicalClaimState(edge);
    const color = claimStateColor(claimState);
    return {
      id: `${edge.id || `${edge.source}->${edge.target}`}:${index}`,
      source: String(edge.source),
      target: String(edge.target),
      type: 'smoothstep',
      animated: claimState === 'occurrence_context' || claimState === 'context_only',
      markerEnd: { type: MarkerType.ArrowClosed, color },
      label: edge.type || 'RELATED_TO',
      style: { stroke: color, strokeWidth: isContextState(claimState) ? 1.7 : 2.4 },
      className: `observatory-flow-edge ${claimStateClass(claimState)}`,
      data: {
        id: `${edge.id || `${edge.source}->${edge.target}`}:${index}`,
        label: edge.type || 'RELATED_TO',
        type: edge.type || 'RELATED_TO',
        claimState,
        source: edge.source,
        target: edge.target,
        raw: edge,
        provenanceHash: edge.provenance_hash,
      },
    };
  });

  const mergedDuplicateNodes = nodeItems.length - nodeMap.size;
  const warnings = [
    'Visible evidence, not complete world.',
    mergedDuplicateNodes > 0 ? `${mergedDuplicateNodes} duplicate graph node ids merged into evidence variant stacks.` : '',
    summary?.graph_nodes != null && summary.graph_nodes !== nodeItems.length
      ? `Source graph node ledger reports ${summary.graph_nodes}; JSON-LD node objects found ${nodeItems.length}.`
      : '',
    summary?.graph_edges != null && summary.graph_edges !== edgeItems.length
      ? `Source graph edge ledger reports ${summary.graph_edges}; JSON-LD edge objects found ${edgeItems.length}.`
      : '',
  ].filter(Boolean);

  return {
    nodes,
    edges,
    ledger: {
      graphNodes: summary?.graph_nodes ?? nodeItems.length,
      graphEdges: summary?.graph_edges ?? edgeItems.length,
      sourceNodeObjects: nodeItems.length,
      sourceEdgeObjects: edgeItems.length,
      renderedNodeObjects: nodeMap.size,
      renderedEdgeObjects: edges.length,
      mergedDuplicateNodes,
      verificationStatus: verification?.summary?.status || 'pending',
    },
    warnings,
    claimStates: uniqueSorted([
      ...nodes.map((node) => node.data.claimState),
      ...edges.map((edge) => edge.data.claimState),
    ]),
    nodeTypes: uniqueSorted(nodes.map((node) => node.data.type)),
    edgeTypes: uniqueSorted(edges.map((edge) => edge.data.type)),
  };
}

function filterObservatoryFlowGraph(flowGraph, filters) {
  const focusSet = filters.focusSelected && filters.selectedNodeId
    ? focusedEvidenceNeighborhood(filters.selectedNodeId, flowGraph.edges)
    : null;
  const nodes = flowGraph.nodes.filter((node) => {
    if (filters.nodeTypeFilter !== 'all' && node.data.type !== filters.nodeTypeFilter) return false;
    if (filters.claimStateFilter !== 'all' && node.data.claimState !== filters.claimStateFilter) return false;
    if (!filters.showBlocked && isBlockedState(node.data.claimState)) return false;
    if (!filters.showContext && isContextState(node.data.claimState)) return false;
    if (focusSet && !focusSet.has(node.id)) return false;
    return true;
  });
  const visibleNodeIds = new Set(nodes.map((node) => node.id));
  const edges = flowGraph.edges.filter((edge) => {
    if (!visibleNodeIds.has(edge.source) || !visibleNodeIds.has(edge.target)) return false;
    if (filters.edgeTypeFilter !== 'all' && edge.data.type !== filters.edgeTypeFilter) return false;
    if (filters.claimStateFilter !== 'all' && edge.data.claimState !== filters.claimStateFilter) return false;
    if (!filters.showBlocked && isBlockedState(edge.data.claimState)) return false;
    if (!filters.showContext && isContextState(edge.data.claimState)) return false;
    return true;
  });
  return { nodes, edges };
}

async function layoutObservatoryFlow(nodes, edges) {
  if (!nodes.length) return nodes;
  try {
    const { default: ELK } = await import('elkjs/lib/elk.bundled.js');
    const elk = new ELK();
    const graph = await elk.layout({
      id: 'observatory-root',
      layoutOptions: {
        'elk.algorithm': 'layered',
        'elk.direction': 'RIGHT',
        'elk.layered.spacing.nodeNodeBetweenLayers': '72',
        'elk.spacing.nodeNode': '44',
        'elk.edgeRouting': 'ORTHOGONAL',
      },
      children: nodes.map((node) => ({
        id: node.id,
        width: 190,
        height: node.data.variantCount > 1 ? 112 : 92,
      })),
      edges: edges.map((edge) => ({
        id: edge.id,
        sources: [edge.source],
        targets: [edge.target],
      })),
    });
    const positions = new Map((graph.children || []).map((child) => [child.id, child]));
    return nodes.map((node) => {
      const position = positions.get(node.id);
      return {
        ...node,
        position: {
          x: position?.x ?? node.position.x,
          y: position?.y ?? node.position.y,
        },
      };
    });
  } catch {
    return nodes;
  }
}

function focusedEvidenceNeighborhood(selectedId, edges) {
  const visible = new Set([selectedId]);
  edges.forEach((edge) => {
    if (edge.source === selectedId) visible.add(edge.target);
    if (edge.target === selectedId) visible.add(edge.source);
  });
  return visible;
}

function canonicalClaimState(raw = {}) {
  const direct = raw.claim_state || raw.claimState || raw.ui_state || raw.status || '';
  const state = String(direct || '').toLowerCase();
  if (state) return state;
  const type = String(raw.type || '').toLowerCase();
  if (type.includes('block')) return 'blocked';
  if (type.includes('repair')) return 'repair_required';
  if (type.includes('source') || type.includes('snapshot')) return 'occurrence_context';
  return 'context_only';
}

function strongestClaimState(states) {
  const cleaned = states.filter(Boolean);
  if (cleaned.some(isBlockedState)) return cleaned.find(isBlockedState);
  if (cleaned.includes('weak_hypothesis')) return 'weak_hypothesis';
  if (cleaned.includes('taxon_supported')) return 'taxon_supported';
  if (cleaned.some((state) => state.includes('repair'))) return cleaned.find((state) => state.includes('repair'));
  if (cleaned.some(isContextState)) return cleaned.find(isContextState);
  return cleaned[0] || 'context_only';
}

function primaryEvidenceType(entry) {
  const types = Array.from(entry.types || []);
  if (types.includes('EvidenceClaim')) return 'EvidenceClaim';
  if (types.includes('Segment')) return 'Segment';
  if (types.includes('Taxon')) return 'Taxon';
  if (types.includes('Snapshot')) return 'Snapshot';
  if (types.includes('Source')) return 'Source';
  if (types.includes('Run')) return 'Run';
  return types[0] || 'EvidenceObject';
}

function evidenceNodeLabel(raw = {}, fallbackId = '') {
  if (raw.label) return raw.label;
  if (raw.segment_id) return compactSegmentLabel(raw.segment_id);
  if (raw.snapshot_id) return raw.snapshot_id.replace('gbif-aedes-spain-', 'GBIF snapshot ');
  if (raw.safe_rank && raw.type === 'Taxon') return `${raw.safe_rank}: ${raw.id?.split(':').pop() || fallbackId}`;
  if (raw.type === 'EvidenceClaim') return compactClaimLabel(raw);
  if (raw.type === 'Source') return String(raw.id || fallbackId).replace(/^source:/, '');
  if (raw.type === 'Run') return String(raw.id || fallbackId).replace(/^run:/, 'Run ');
  return String(raw.id || fallbackId).replace(/^[^:]+:/, '');
}

function evidenceNodeSubtitle(raw = {}, claimState = '') {
  if (raw.role) return raw.role;
  if (raw.source_mode) return raw.source_mode;
  if (raw.safe_rank) return raw.safe_rank;
  if (raw.ruleset_version) return raw.ruleset_version;
  return claimState || 'evidence object';
}

function compactSegmentLabel(segmentId = '') {
  return String(segmentId).replace(/^segment:/, '').replace(/:1-\d+$/, '');
}

function compactClaimLabel(raw = {}) {
  const id = String(raw.id || '').split(':taxon:').pop();
  if (id && id !== String(raw.id || '')) return `Claim: ${id}`;
  return 'Evidence claim';
}

function claimStateColor(state = '') {
  const normalized = String(state || '').toLowerCase();
  if (normalized === 'taxon_supported' || normalized.includes('supported')) return '#2d7d92';
  if (normalized.includes('weak') || normalized.includes('review')) return '#b8792f';
  if (isBlockedState(normalized)) return '#9d3f2c';
  if (normalized.includes('repair')) return '#6d5aa8';
  if (isContextState(normalized)) return '#2f6f88';
  return '#66756d';
}

function claimStateClass(state = '') {
  const normalized = String(state || '').toLowerCase().replace(/[^a-z0-9]+/g, '-');
  if (isBlockedState(normalized)) return 'blocked';
  if (normalized.includes('weak') || normalized.includes('review')) return 'weak';
  if (normalized.includes('supported')) return 'supported';
  if (normalized.includes('repair')) return 'repair';
  if (isContextState(normalized)) return 'context';
  return normalized || 'unknown';
}

function evidenceTypeClass(type = '') {
  return String(type || '').toLowerCase().replace(/[^a-z0-9]+/g, '-');
}

function isBlockedState(state = '') {
  const normalized = String(state || '').toLowerCase();
  return normalized.includes('blocked') || normalized.includes('not_publishable') || normalized.includes('not-publishable');
}

function isContextState(state = '') {
  const normalized = String(state || '').toLowerCase();
  return normalized.includes('context') || normalized === 'occurrence_context' || normalized === 'dataset_context';
}

function uniqueSorted(values) {
  return Array.from(new Set(values.filter(Boolean))).sort((a, b) => String(a).localeCompare(String(b)));
}

const OBSERVATORY_MAP_DATASET_COLORS = ['#0f6372', '#b56a2b', '#5d689e', '#557b44', '#8a5f94', '#b84b4b'];

function SnapshotMapVisual({ rows, bbox, snapshot, summary }) {
  const mapElementRef = useRef(null);
  const leafletMapRef = useRef(null);
  const leafletLayersRef = useRef([]);
  const mapBounds = useMemo(() => normalizeBbox(bbox), [bbox]);
  const datasetKeys = useMemo(() => uniqueSorted(rows.map((row) => row.datasetKey || 'unknown_dataset')), [rows]);
  const [selectedOccurrenceId, setSelectedOccurrenceId] = useState(null);
  const points = useMemo(() => rows
    .filter((row) => row.decimalLatitude != null && row.decimalLongitude != null)
    .map((row, index) => {
      const datasetKey = row.datasetKey || 'unknown_dataset';
      const datasetIndex = Math.max(0, datasetKeys.indexOf(datasetKey));
      const uncertaintyMeters = Number(row.coordinateUncertaintyInMeters) || 0;
      return {
        ...row,
        index,
        datasetKey,
        lat: Number(row.decimalLatitude),
        lon: Number(row.decimalLongitude),
        color: OBSERVATORY_MAP_DATASET_COLORS[datasetIndex % OBSERVATORY_MAP_DATASET_COLORS.length],
        review: occurrenceNeedsReview(row),
        recordId: occurrenceRecordId(row, index),
        uncertaintyMeters,
      };
    }), [rows, datasetKeys]);
  const selectedPoint = points.find((point) => point.recordId === selectedOccurrenceId) || points[0];
  const plottedRows = points.length;
  const hashShort = snapshot?.snapshot_hash?.slice(0, 12);
  const sourceMode = snapshot?.source_mode || summary?.source_mode || 'not run yet';
  const normalizedRows = summary?.normalized_occurrence_records ?? rows.length;
  const datasetCount = new Set(rows.map((row) => row.datasetKey).filter(Boolean)).size;
  const datedRows = rows.filter((row) => row.eventDate || row.year).length;
  const issueRows = rows.filter((row) => occurrenceNeedsReview(row)).length;
  const boundary = snapshot?.claim_boundary || summary?.claim_boundary || 'Use this map as source provenance only. Barcode, VSEA and GSEG proof gates decide molecular support.';
  const sourceModeLabel = observatorySourceModeLabel(sourceMode);
  const taxonKey = firstPresent(rows.map((row) => row.acceptedTaxonKey || row.taxonKey));
  const countryCode = firstPresent(rows.map((row) => row.countryCode));
  const gbifSearchUrl = buildGbifOccurrenceSearchUrl(taxonKey, countryCode);
  const mapSourceLabel = taxonKey ? `GBIF density layer · taxonKey ${taxonKey}${countryCode ? ` · ${countryCode}` : ''}` : 'GBIF density layer';

  useEffect(() => {
    if (!mapElementRef.current || isJsdomRuntime()) return undefined;
    let cancelled = false;

    async function renderGbifMap() {
      const { default: L } = await import('leaflet');
      if (cancelled || !mapElementRef.current) return;
      const pixelRatio = Math.max(1, Math.min(4, Math.floor(window.devicePixelRatio || 1)));
      const map = leafletMapRef.current || L.map(mapElementRef.current, {
        attributionControl: true,
        scrollWheelZoom: false,
        zoomControl: true,
      });
      leafletMapRef.current = map;
      leafletLayersRef.current.forEach((layer) => layer.remove());
      leafletLayersRef.current = [];

      const baseLayer = L.tileLayer(`https://tile.gbif.org/3857/omt/{z}/{x}/{y}@${pixelRatio}x.png?style=gbif-light`, {
        attribution: 'Base map © GBIF, OpenStreetMap contributors, OpenMapTiles',
        maxZoom: 17,
        minZoom: 1,
        tileSize: 512,
        zoomOffset: -1,
      });
      const densityParams = new URLSearchParams({
        srs: 'EPSG:3857',
        style: 'classic.point',
      });
      if (taxonKey) densityParams.set('taxonKey', taxonKey);
      if (countryCode) densityParams.set('country', countryCode);
      const densityLayer = L.tileLayer(`https://api.gbif.org/v2/map/occurrence/density/{z}/{x}/{y}@${pixelRatio}x.png?${densityParams.toString()}`, {
        attribution: 'Occurrence density © GBIF',
        maxZoom: 17,
        minZoom: 1,
        opacity: 0.72,
        tileSize: 512,
        zoomOffset: -1,
      });
      leafletLayersRef.current.push(baseLayer.addTo(map), densityLayer.addTo(map));

      const bboxRectangle = L.rectangle([[mapBounds.south, mapBounds.west], [mapBounds.north, mapBounds.east]], {
        color: '#123f47',
        dashArray: '6 6',
        fill: false,
        opacity: 0.78,
        weight: 1.5,
      });
      leafletLayersRef.current.push(bboxRectangle.addTo(map));

      const markerGroup = L.featureGroup();
      points.forEach((point) => {
        if (point.uncertaintyMeters > 0) {
          const uncertainty = L.circle([point.lat, point.lon], {
            color: point.review ? '#a85e27' : point.color,
            fillColor: point.review ? '#b36b2c' : point.color,
            fillOpacity: 0.12,
            opacity: 0.24,
            radius: Math.min(60000, Math.max(60, point.uncertaintyMeters)),
            weight: 1,
          });
          uncertainty.addTo(markerGroup);
        }
        const selected = point.recordId === selectedPoint?.recordId;
        const marker = L.circleMarker([point.lat, point.lon], {
          color: selected ? '#111b16' : '#ffffff',
          fillColor: point.review ? '#b36b2c' : point.color,
          fillOpacity: 0.92,
          radius: selected ? 7.8 : 5.8,
          weight: selected ? 2.8 : 1.5,
        });
        marker
          .bindTooltip(`${point.gbifID || `row ${point.row_index}`} · ${point.datasetTitle || point.datasetKey}`, { sticky: true })
          .on('click', () => setSelectedOccurrenceId(point.recordId))
          .addTo(markerGroup);
      });
      leafletLayersRef.current.push(markerGroup.addTo(map));

      const pointBounds = points.length ? L.latLngBounds(points.map((point) => [point.lat, point.lon])) : null;
      const targetBounds = pointBounds?.isValid() ? pointBounds.pad(0.22) : L.latLngBounds([[mapBounds.south, mapBounds.west], [mapBounds.north, mapBounds.east]]);
      map.fitBounds(targetBounds, { maxZoom: 7, padding: [18, 18] });
      setTimeout(() => map.invalidateSize(), 60);
    }

    renderGbifMap();
    return () => {
      cancelled = true;
    };
  }, [points, selectedPoint?.recordId, mapBounds, taxonKey, countryCode]);

  useEffect(() => () => {
    if (leafletMapRef.current) {
      leafletMapRef.current.remove();
      leafletMapRef.current = null;
    }
  }, []);

  return (
    <article className="observatory-visual-card snapshot-visual-card">
      <div className="visual-card-heading">
        <span>01</span>
        <div>
          <h3>GBIF occurrence context map</h3>
          <p>{hashShort ? `Proof ID ${hashShort}; ${sourceModeLabel}; map records are provenance context, not claim support.` : 'Run the demo to lock the source evidence before drawing records.'}</p>
        </div>
      </div>
      <div className="gbif-map-shell">
        <div className="gbif-map-toolbar">
          <strong>{mapSourceLabel}</strong>
          <a href={gbifSearchUrl} target="_blank" rel="noreferrer">Open in GBIF</a>
        </div>
        <div ref={mapElementRef} className="gbif-leaflet-map" aria-label="GBIF base map with occurrence density and snapshot records">
          <div className="gbif-map-loading">
            <strong>GBIF map layer</strong>
            <span>Base map + occurrence density; snapshot markers load in browser.</span>
          </div>
        </div>
        <div className="gbif-map-footer">
          <span>Snapshot bbox: {mapBounds.west.toFixed(1)}, {mapBounds.south.toFixed(1)}, {mapBounds.east.toFixed(1)}, {mapBounds.north.toFixed(1)}</span>
          <span>{plottedRows}/{rows.length || 0} source rows plotted as local proof markers</span>
        </div>
      </div>
      <div className="snapshot-dataset-legend" aria-label="Occurrence datasets plotted on map">
        {datasetKeys.map((datasetKey, index) => (
          <span key={datasetKey}>
            <i style={{ background: OBSERVATORY_MAP_DATASET_COLORS[index % OBSERVATORY_MAP_DATASET_COLORS.length] }} />
            {datasetKey}
          </span>
        ))}
      </div>
      {selectedPoint && (
        <div className="snapshot-selected-record" aria-label="Selected occurrence record">
          <div>
            <span>Selected occurrence</span>
            <strong>{selectedPoint.gbifID || `row ${selectedPoint.row_index}`}</strong>
          </div>
          <div>
            <span>Coordinates</span>
            <strong>{Number(selectedPoint.decimalLatitude).toFixed(4)}, {Number(selectedPoint.decimalLongitude).toFixed(4)}</strong>
          </div>
          <div>
            <span>Dataset</span>
            <strong>{selectedPoint.datasetTitle || selectedPoint.datasetKey}</strong>
          </div>
          <div>
            <span>Issue state</span>
            <strong>{selectedPoint.issues || 'clean'}</strong>
          </div>
        </div>
      )}
      <div className="snapshot-proof-grid" aria-label="Snapshot verification summary">
        <div>
          <span>Records shown</span>
          <strong>{normalizedRows}</strong>
        </div>
        <div>
          <span>Datasets</span>
          <strong>{datasetCount || 'pending'}</strong>
        </div>
        <div>
          <span>Dates checked</span>
          <strong>{datedRows}/{rows.length || 0}</strong>
        </div>
        <div>
          <span>Claim impact</span>
          <strong>none</strong>
        </div>
        <div>
          <span>Review flags</span>
          <strong>{issueRows}</strong>
        </div>
      </div>
      <div className="snapshot-legend">
        <span><i className="legend-dot context" /> Clean occurrence context</span>
        <span><i className="legend-dot review" /> Metadata or coordinate review</span>
        <span><i className="legend-ring" /> Coordinate uncertainty radius</span>
        <span><i className="legend-line" /> Claim decided by barcode + GSEG gates</span>
      </div>
      <p className="snapshot-boundary">{boundary}</p>
    </article>
  );
}

function normalizeBbox(bbox) {
  const fallback = [-9.5, 35.5, 4.5, 44.5];
  const safeBbox = Array.isArray(bbox) && bbox.length === 4 ? bbox.map(Number) : fallback;
  const [rawWest, rawSouth, rawEast, rawNorth] = safeBbox.every(Number.isFinite) ? safeBbox : fallback;
  return {
    west: Math.min(rawWest, rawEast),
    south: Math.min(rawSouth, rawNorth),
    east: Math.max(rawWest, rawEast),
    north: Math.max(rawSouth, rawNorth),
  };
}

function firstPresent(values) {
  const value = values.find((item) => item !== undefined && item !== null && String(item).trim() !== '');
  return value === undefined || value === null ? '' : String(value);
}

function buildGbifOccurrenceSearchUrl(taxonKey, countryCode) {
  const url = new URL('https://www.gbif.org/occurrence/map');
  if (taxonKey) url.searchParams.set('taxon_key', taxonKey);
  if (countryCode) url.searchParams.set('country', countryCode);
  return url.toString();
}

function isJsdomRuntime() {
  return typeof navigator !== 'undefined' && /jsdom/i.test(navigator.userAgent || '');
}

function occurrenceRecordId(row, index) {
  return String(row.gbifID || row.occurrenceID || row.row_index || `occurrence-${index}`);
}

function occurrenceNeedsReview(row) {
  return Boolean(row.issues) || !row.license || !(row.eventDate || row.year);
}

function observatorySourceModeLabel(mode = '') {
  const normalized = String(mode || '').toLowerCase();
  if (normalized === 'fixture') return 'reproducible snapshot';
  if (normalized === 'fixture_fallback') return 'fixture fallback';
  if (normalized === 'gbif_api') return 'GBIF API source';
  if (normalized === 'live_gbif_small') return 'small GBIF-backed run';
  if (normalized === 'offline_demo') return 'offline demo';
  return normalized.replaceAll('_', ' ') || 'not run yet';
}

function VseaMatrixVisual({ rows, compact = false }) {
  const visibleRows = rows.slice(0, compact ? 4 : 8);
  const columns = [
    ['segment_hash', 'seg'],
    ['snapshot_hash', 'lock'],
    ['claim_state', 'gate'],
    ['gbif_export_state', 'GBIF'],
    ['ai_label', 'AI'],
  ];
  return (
    <article className={`observatory-visual-card vsea-matrix-card ${compact ? 'compact' : ''}`}>
      <div className="visual-card-heading">
        <span>02</span>
        <div>
          <h3>Segment decision matrix</h3>
          <p>{rows.length ? `VSEA keeps ${rows.length} segment rows with snapshot, claim, GBIF export and AI-ready guardrail state.` : 'Claim states appear after run.'}</p>
        </div>
      </div>
      <div className="vsea-matrix" aria-label="Verified Segment Evidence Array matrix">
        <div className="vsea-matrix-head">
          <span>sequence</span>
          {columns.map(([, label]) => <span key={label}>{label}</span>)}
        </div>
        {visibleRows.length ? visibleRows.map((row, index) => (
          <div className="vsea-matrix-row" key={row.vsea_id || row.sequence_id}>
            <span title={row.sequence_id}>{visualSequenceLabel(row.sequence_id, index)}</span>
            {columns.map(([key, label]) => (
              <i
                key={`${row.sequence_id}-${key}`}
                className={`matrix-cell ${matrixCellClass(row, key)}`}
                title={`${label}: ${row[key] || 'not emitted for this row'}`}
              />
            ))}
          </div>
        )) : (
          <div className="vsea-matrix-empty">Run Observatory to emit VSEA rows.</div>
        )}
      </div>
    </article>
  );
}

function visualSequenceLabel(sequenceId = '', index = 0) {
  const normalized = String(sequenceId || '').toLowerCase();
  if (normalized.includes('metadata')) return 'metadata';
  if (normalized.includes('ambiguous')) return 'ambig.';
  if (normalized.includes('short')) return 'short';
  if (normalized.includes('good')) return 'strong';
  return `seq ${index + 1}`;
}

function EvidenceGraphVisual({ run, vseaRows, summary, compact = false }) {
  const supported = vseaRows.filter((row) => row.claim_state === 'taxon_supported').length;
  const review = Math.max(0, vseaRows.length - supported);
  const graphNodes = [
    { id: 'source', label: 'Data', detail: run ? 'GBIF/DNA' : 'pending', x: 42, y: 78 },
    { id: 'snapshot', label: 'Proof', detail: run?.snapshot_manifest?.snapshot_hash?.slice(0, 6) || 'hash', x: 142, y: 44 },
    { id: 'vsea', label: 'VSEA', detail: `${summary?.vsea_rows ?? 0} rows`, x: 142, y: 120 },
    { id: 'claim', label: 'Gates', detail: `${supported}/${vseaRows.length || supported + review}`, x: 242, y: 78 },
    { id: 'export', label: 'Pack', detail: summary?.hard_gate_status || 'guarded', x: 338, y: 78 },
  ];
  const edges = [
    ['source', 'snapshot'],
    ['source', 'vsea'],
    ['snapshot', 'claim'],
    ['vsea', 'claim'],
    ['claim', 'export'],
  ];
  return (
    <article className={`observatory-visual-card graph-visual-card ${compact ? 'compact' : ''}`}>
      <div className="visual-card-heading">
        <span>03</span>
        <div>
          <h3>Claim graph</h3>
          <p>{summary?.graph_nodes ? `Evidence graph: ${summary.graph_nodes} nodes · ${summary.graph_edges} edges.` : 'Graph forms after run.'}</p>
        </div>
      </div>
      <svg className="evidence-graph-svg" viewBox="0 0 390 180" role="img" aria-label="Evidence graph visualization">
        <defs>
          <marker id="observatory-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
            <path d="M0,0 L8,4 L0,8 Z" className="graph-arrow" />
          </marker>
        </defs>
        {edges.map(([from, to]) => {
          const a = graphNodes.find((node) => node.id === from);
          const b = graphNodes.find((node) => node.id === to);
          return <line key={`${from}-${to}`} x1={a.x} y1={a.y} x2={b.x} y2={b.y} className="graph-edge-line" markerEnd="url(#observatory-arrow)" />;
        })}
        {graphNodes.map((node) => (
          <g key={node.id} transform={`translate(${node.x - 39} ${node.y - 28})`}>
            <rect width="78" height="56" rx="9" className={`graph-svg-node ${node.id}`} />
            <text x="39" y="23" className="graph-svg-label">{node.label}</text>
            <text x="39" y="40" className="graph-svg-detail">{node.detail}</text>
          </g>
        ))}
      </svg>
    </article>
  );
}

function ProofWheelVisual({ rows }) {
  const visibleRows = rows.length ? rows : Array.from({ length: 20 }, (_, index) => ({
    id: `OPO-${String(index + 1).padStart(2, '0')}`,
    status: 'pending',
    severity: 'hard_gate',
  }));
  const passCount = visibleRows.filter((row) => row.status === 'pass').length;
  return (
    <article className="observatory-visual-card proof-wheel-card">
      <div className="visual-card-heading">
        <span>04</span>
        <div>
          <h3>Proof obligations</h3>
          <p>{passCount}/{visibleRows.length} Observatory checks passing.</p>
        </div>
      </div>
      <div className="proof-wheel" aria-label="Observatory proof obligation wheel">
        {visibleRows.map((row, index) => (
          <span
            key={row.id}
            className={`proof-dot ${row.status}`}
            style={{ '--angle': `${index * (360 / visibleRows.length)}deg` }}
            title={`${row.id}: ${row.status}`}
          />
        ))}
        <strong>{passCount}</strong>
        <small>passed</small>
      </div>
    </article>
  );
}

function clampPercent(value) {
  if (Number.isNaN(value)) return 50;
  return Math.max(0, Math.min(100, value));
}

function matrixCellClass(row, key) {
  if (!row[key]) return 'pending';
  if (key === 'claim_state') return row.claim_state === 'taxon_supported' ? 'safe' : 'review';
  if (key === 'gbif_export_state') return row.gbif_export_state === 'candidate_gbif_row' ? 'safe' : 'review';
  if (key === 'ai_label') return row.ai_label === 'positive_verified' ? 'safe' : 'review';
  return 'provenance';
}

function SubmissionOverview({ referenceStatus, metrics, exports, pack, onOpenWorkbench, onRunCompiler, loading }) {
  const evidencePack = exports.find((item) => item.name === 'evidence_pack.zip');
  const hasRun = Boolean(pack);

  return (
    <section className="page-grid">
      <div className="hero-panel">
        <div>
          <p className="eyebrow">Production judge view</p>
          <h2>Decision cockpit for safe molecular evidence, not another biodiversity dashboard.</h2>
          <p>
            EcoGenesis turns DNA barcode, metabarcoding and Sequence ID outputs into a clear decision:
            what can be claimed, what must be downgraded, what is blocked, and which repair actions convert the
            most evidence into GBIF-ready publication material.
          </p>
          <div className="hero-actions">
            <button className="primary" onClick={onOpenWorkbench}>Open Workbench</button>
            <button onClick={onRunCompiler} disabled={loading}>{loading ? 'Running...' : 'Run mixed demo'}</button>
            {evidencePack && (
              <a className="button-link" href={exportUrl(evidencePack.url)}>Download Evidence Pack</a>
            )}
          </div>
        </div>
        <div className="verdict-card production-verdict">
          <span>Contest verdict</span>
          <strong>{hasRun ? pack?.summary?.verdict : 'Ready for judge demo: deterministic barcode gates, source boundaries and exportable evidence pack.'}</strong>
          <small>{referenceStatus?.message || 'Loading compiler reference status...'}</small>
        </div>
      </div>

      <SourceBoundaryPanel />

      <JudgeDecisionDashboard metrics={metrics} hasRun={hasRun} />

      <section className="panel product-split">
        <EvidenceFunnel />
        <ClaimStatusDonut />
      </section>

      <section className="panel product-split">
        <ClaimMatrixPreview />
        <RepairOptimizer />
      </section>

      <section className="panel">
        <p className="section-label">Evidence path</p>
        <h2>Every claim moves through visible gates.</h2>
        <div className="pipeline">
          {['identity', 'coverage', 'ambiguity LCA', 'barcode gap', 'diagnostic k-mers', 'GBIF metadata', 'publication pack'].map((step) => (
            <div key={step}>{step}</div>
          ))}
        </div>
      </section>

      <MolecularGraphPreview />

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

function SourceBoundaryPanel() {
  return (
    <section className="panel source-boundary-panel">
      <div className="source-boundary-heading">
        <div>
          <p className="section-label">Barcode-source boundary</p>
          <h2>Connected sources are barcode inputs, not hidden biodiversity shortcuts.</h2>
          <p>
            The compiler evaluates supplied molecular hit evidence and selected reference FASTA. GBIF occurrence
            data remain an audit/citation layer and cannot override the molecular gates.
          </p>
        </div>
        <div className="source-link-stack" aria-label="Official source links">
          {officialSourceLinks.map(([label, href]) => (
            <a key={label} href={href} target="_blank" rel="noreferrer">{label}</a>
          ))}
        </div>
      </div>
      <div className="source-boundary-grid">
        {barcodeSourceCards.map(([label, title, body]) => (
          <article key={title}>
            <span>{label}</span>
            <strong>{title}</strong>
            <p>{body}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function JudgeDecisionDashboard({ metrics, hasRun }) {
  const processed = hasRun ? metrics.processed_records ?? 0 : 1000;
  const speciesSafe = hasRun ? metrics.species_safe_records ?? 0 : 48;
  const blocked = hasRun ? metrics.blocked_species_claims ?? 0 : 20;
  const ready = hasRun ? metrics.record_ready_records ?? 0 : 'DOI gated';

  return (
    <section className="judge-dashboard panel">
      <div className="decision-banner">
        <p className="section-label">Decision</p>
        <h2>{hasRun ? 'Compiler run completed with safe-rank outputs.' : 'Barcode compiler is ready; GBIF occurrence audit stays separate.'}</h2>
        <p>
          The product view leads with decisions instead of raw tables: supported claims, weak claims, blocked
          overclaims, required verification and the next repair action.
        </p>
      </div>
      <div className="decision-kpis">
        <Metric label={hasRun ? 'Processed in run' : 'Occurrence records audited'} value={processed} />
        <Metric label={hasRun ? 'Species-safe records' : 'Supported claims'} value={speciesSafe} />
        <Metric label={hasRun ? 'Blocked species claims' : 'Blocked overclaims'} value={blocked} />
        <Metric label={hasRun ? 'Record-ready' : 'Publication state'} value={ready} />
      </div>
      <div className="decision-cards">
        <article className="decision-card safe">
          <span>Safe to claim</span>
          <strong>Limited evidence-context statements</strong>
          <p>Occurrence evidence exists, safe-rank output is preserved, and export files keep provenance.</p>
        </article>
        <article className="decision-card blocked">
          <span>Do not claim</span>
          <strong>Absence, true distribution, trend or phenotype truth</strong>
          <p>These are explicitly blocked unless external models, bias correction or curated trait evidence exist.</p>
        </article>
        <article className="decision-card repair">
          <span>Repair first</span>
          <strong>DOI, uncertainty, source concentration</strong>
          <p>The interface points to the smallest fixes that unlock the most defensible reuse.</p>
        </article>
      </div>
    </section>
  );
}

function EvidenceFunnel() {
  return (
    <div className="product-panel">
      <p className="section-label">Evidence funnel</p>
      <h2>Where real data become usable evidence.</h2>
      <div className="funnel-list">
        {evidenceFunnelSteps.map(([label, value, detail, status], index) => (
          <article className={`funnel-step ${status}`} key={label}>
            <span>{String(index + 1).padStart(2, '0')}</span>
            <div>
              <strong>{label}</strong>
              <em>{value}</em>
              <p>{detail}</p>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}

function ClaimStatusDonut() {
  return (
    <div className="product-panel">
      <p className="section-label">Claim status</p>
      <h2>100 hypotheses are not treated equally.</h2>
      <div className="donut-wrap">
        <div className="claim-donut" aria-label="Claim status donut">
          <strong>100</strong>
          <span>claims</span>
        </div>
        <div className="claim-legend">
          {claimStatusSummary.map(([status, count, label]) => (
            <div className={`legend-row ${status.replaceAll(' ', '-')}`} key={status}>
              <span>{count}</span>
              <strong>{status}</strong>
              <small>{label}</small>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function ClaimMatrixPreview() {
  return (
    <div className="product-panel">
      <p className="section-label">Claim matrix</p>
      <h2>The interface answers “what can I decide?”</h2>
      <div className="prod-claim-matrix">
        <div><strong>Claim</strong><strong>Status</strong><strong>Decision</strong></div>
        {judgeClaimMatrix.map(([claimText, status, decision]) => (
          <div key={claimText}>
            <span>{claimText}</span>
            <span className={`status-pill ${status.replaceAll(' ', '-')}`}>{status}</span>
            <span>{decision}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function RepairOptimizer() {
  return (
    <div className="product-panel">
      <p className="section-label">Repair optimizer</p>
      <h2>Best next actions, ranked by evidence unlocked.</h2>
      <div className="repair-list">
        {repairPriorities.map(([title, impact, detail, status], index) => (
          <article className={`repair-card ${status}`} key={title}>
            <span>{index + 1}</span>
            <div>
              <strong>{title}</strong>
              <em>{impact}</em>
              <p>{detail}</p>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}

function MolecularGraphPreview() {
  return (
    <section className="panel graph-preview-panel">
      <div>
        <p className="section-label">Molecular Evidence Graph preview</p>
        <h2>Ambiguous fragments become visible clade knowledge.</h2>
        <p className="proof-copy">
          The production direction is a graph: a DNA fragment links to every taxon carrying it, the lowest common
          ancestor, GBIF geography context, protein sanity checks for coding markers and safe or blocked claims.
        </p>
      </div>
      <div className="graph-preview">
        {molecularGraphPreview.map(([title, body], index) => (
          <article key={title} className={index === 0 ? 'source-node' : ''}>
            <span>{index === 0 ? 'input' : `0${index}`}</span>
            <strong>{title}</strong>
            <p>{body}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function VisualLecture() {
  return (
    <section className="visual-lecture page-grid">
      <section className="lecture-hero panel">
        <div>
          <p className="section-label">Visual explanation</p>
          <h2>Sequence visual lab: from DNA letters to safe GBIF evidence.</h2>
          <p>
            This page explains the project like a guided science board. A DNA sequence is compared with reference
            sequences, competitors are checked, unsafe species claims are downgraded, and missing GBIF fields become
            repair actions instead of hidden failures.
          </p>
          <div className="lecture-actions">
            <a className="button-link" href="#analysis-animation">Watch analysis</a>
            <a className="button-link" href="#analysis-picture-sequence">Generated pictures</a>
            <a className="button-link" href="#sequence-picture">See sequence picture</a>
            <a className="button-link" href="#safe-claim-picture">See safe claims</a>
            <a className="button-link" href="#animation-storyboard">Story frames</a>
          </div>
        </div>
        <div className="sequence-card" aria-label="Decorative DNA sequence preview">
          <div className="helix-strip">
            {dnaQuery.slice(0, 28).split('').map((base, index) => (
              <span className={`base-tile ${base}`} key={`${base}-${index}`}>{base}</span>
            ))}
          </div>
          <strong>DNA letters are evidence inputs, not final truth.</strong>
          <p>The compiler asks: how strong is the match, who else is close, and what can be safely published?</p>
        </div>
      </section>

      <section className="lecture-grid">
        {lectureTakeaways.map(([title, body]) => (
          <article className="lecture-takeaway panel" key={title}>
            <strong>{title}</strong>
            <p>{body}</p>
          </article>
        ))}
      </section>

      <AnalysisAnimationVisual />

      <GeneratedAnalysisPictureSequence />

      <NatureCycleVisual />

      <SciencePurposeVisual />

      <section className="panel lecture-two-column">
        <BeforeAfterScienceVisual />
        <UserValueVisual />
      </section>

      <section className="panel">
        <p className="section-label">Process map</p>
        <h2>Six visible steps from input to export.</h2>
        <div className="lecture-workflow">
          {lectureWorkflow.map(([index, title, body]) => (
            <article key={title}>
              <span>{index}</span>
              <strong>{title}</strong>
              <p>{body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="panel lecture-two-column" id="sequence-picture">
        <div>
          <p className="section-label">DNA letters</p>
          <h2>A sequence is a long word made from A, C, G and T.</h2>
          <p className="lecture-copy">
            The first visual check is simple: compare the query sequence with a reference hit. Green positions match.
            Warm positions show differences. A high top hit is useful, but it is still only evidence.
          </p>
          <div className="formula-snapshot">
            <MathRow><Mi>identity</Mi><Op>=</Op><Frac top={<><Mi>matching letters</Mi></>} bottom={<><Mi>aligned letters</Mi></>} /></MathRow>
            <MathRow><Mi>coverage</Mi><Op>=</Op><Frac top={<><Mi>aligned letters</Mi></>} bottom={<><Mi>query length</Mi></>} /></MathRow>
          </div>
        </div>
        <AlignmentVisual />
      </section>

      <section className="panel">
        <p className="section-label">Hard gates</p>
        <h2>The tool does not trust one top hit blindly.</h2>
        <div className="gate-picture-grid">
          {gateCards.map(([title, value, body]) => (
            <article key={title} className={`gate-picture ${title === 'Metadata' ? 'repairable' : 'pass'}`}>
              <span>{title}</span>
              <strong>{value}</strong>
              <p>{body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="panel lecture-two-column">
        <TopHitTrapVisual />
        <LcaTreeVisual />
      </section>

      <section className="panel lecture-two-column">
        <BarcodeGapVisual />
        <KmerVisual />
      </section>

      <section className="panel lecture-two-column">
        <PublicationVisual />
        <ClaimBoundaryVisual />
      </section>

      <FutureImpactVisual />

      <section className="panel visual-summary" id="safe-claim-picture">
        <p className="section-label">Final mental model</p>
        <h2>EcoGenesis is a scientific checkpoint before GBIF publication.</h2>
        <div className="summary-road">
          <span>Sequence</span>
          <span>Match</span>
          <span>Competitors</span>
          <span>Safe rank</span>
          <span>Metadata</span>
          <span>Evidence pack</span>
        </div>
        <p>
          The result is not “the computer guessed a species”. The result is a reproducible evidence package:
          safe taxon, blocked claims, repair actions, methods text, citations and export tables.
        </p>
      </section>
    </section>
  );
}

function AnalysisAnimationVisual() {
  return (
    <section className="panel analysis-animation-panel" id="analysis-animation" aria-label="Compiler logic animation">
      <div className="analysis-animation-heading">
        <div>
          <p className="section-label">Compiler logic animation</p>
          <h2>How EcoGenesis reaches a bounded claim, step by step.</h2>
          <p>
            The animation shows the actual logic of the compiler: sequence evidence is segmented, reference hits are
            compared, hard gates are applied, unsafe species claims are downgraded, and publication blockers are kept
            separate from taxonomic evidence.
          </p>
        </div>
        <div className="analysis-verdict-card">
          <span>Bounded result</span>
          <strong>Safe rank + explicit blockers</strong>
          <small>Auditable because failed gates create downgrade or repair actions, not hidden confidence.</small>
        </div>
      </div>

      <div className="analysis-live-grid">
        <div className="analysis-stage">
          <div className="analysis-sequence-rail" aria-label="Animated DNA sequence scanner">
            <div className="analysis-scanner" />
            {dnaQuery.slice(0, 38).split('').map((base, index) => (
              <span className={`base-tile ${base}`} key={`analysis-base-${index}`}>{base}</span>
            ))}
          </div>
          <div className="analysis-segment-map">
            {analysisSegments.map(([range, title, evidence, verdict, tone]) => (
              <article className={tone} key={range}>
                <span>{range}</span>
                <strong>{title}</strong>
                <p>{evidence}</p>
                <em>{verdict}</em>
              </article>
            ))}
          </div>
        </div>

        <div className="analysis-hit-panel">
          <p className="section-label">Reference hits</p>
          {analysisReferenceHits.map(([taxon, score, detail, tone, width]) => (
            <article className={tone} key={taxon}>
              <div>
                <strong>{taxon}</strong>
                <span>{detail}</span>
              </div>
              <b>{score}</b>
              <i style={{ width }} />
            </article>
          ))}
        </div>
      </div>

      <div className="analysis-gate-trail" aria-label="Compiler gate trail">
        {analysisGateTrail.map(([gate, value, tone]) => (
          <article className={tone} key={gate}>
            <span>{gate}</span>
            <strong>{value}</strong>
          </article>
        ))}
      </div>

      <div className="analysis-proof-grid">
        {analysisProofCards.map(([title, body]) => (
          <article key={title}>
            <strong>{title}</strong>
            <p>{body}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function GeneratedAnalysisPictureSequence() {
  return (
    <section className="panel analysis-picture-panel" id="analysis-picture-sequence" aria-label="Generated analysis picture sequence">
      <div className="analysis-picture-heading">
        <div>
          <p className="section-label">Generated analysis pictures</p>
          <h2>The analysis is visible as a picture sequence.</h2>
          <p>
            The generated poster gives judges the fast visual story. The six controlled frames below show the exact
            logic used by EcoGenesis: evidence enters, references are challenged, gates fail closed and only bounded
            claims reach the Evidence Pack.
          </p>
        </div>
        <div className="analysis-picture-legend">
          <span>Generated overview</span>
          <span>Exact gate logic</span>
          <span>Contest presentation layer</span>
        </div>
      </div>

      <figure className="analysis-generated-poster">
        <img
          src="/assets/ecogenesis-analysis-sequence-clean.png"
          alt="Generated six-panel EcoGenesis analysis sequence from input sequence to evidence pack"
        />
        <figcaption>
          Generated overview image. The verified cards below keep the scientific text and decision logic exact.
        </figcaption>
      </figure>

      <div className="analysis-picture-grid">
        {analysisPictureFrames.map(([index, title, body, result, visual]) => (
          <article className={`analysis-picture-card ${visual}`} key={index}>
            <AnalysisPictureGraphic visual={visual} />
            <div className="analysis-picture-copy">
              <span>Picture {index}</span>
              <strong>{title}</strong>
              <p>{body}</p>
              <em>{result}</em>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function AnalysisPictureGraphic({ visual }) {
  if (visual === 'input') {
    return (
      <div className="analysis-picture-graphic input" aria-label="Input sequence visual">
        <div className="sample-tube"><span /></div>
        <div className="sample-leaf" />
        <div className="picture-dna-strip">
          {dnaQuery.slice(0, 18).split('').map((base, index) => (
            <span className={`base-tile ${base}`} key={`picture-input-${index}`}>{base}</span>
          ))}
        </div>
        <div className="picture-chip-stack">
          <span>COI-5P</span>
          <span>occurrenceID</span>
          <span>methodOrSOP</span>
        </div>
      </div>
    );
  }

  if (visual === 'alignment') {
    return (
      <div className="analysis-picture-graphic alignment" aria-label="Alignment scan visual">
        <div className="picture-scan-bar" />
        {[
          ['Query', dnaQuery],
          ['Ref A', dnaReference],
          ['Ref B', dnaCompetitor],
        ].map(([label, sequence]) => (
          <div className="picture-align-row" key={label}>
            <strong>{label}</strong>
            <div>
              {sequence.slice(0, 18).split('').map((base, index) => (
                <span className={`base-tile ${base} ${base === dnaQuery[index] ? 'match' : 'mismatch'}`} key={`${label}-${index}`}>
                  {base}
                </span>
              ))}
            </div>
          </div>
        ))}
        <div className="picture-metric-pair">
          <span>identity 99.6%</span>
          <span>coverage 96%</span>
        </div>
      </div>
    );
  }

  if (visual === 'hits') {
    return (
      <div className="analysis-picture-graphic hits" aria-label="Reference hits visual">
        {analysisReferenceHits.map(([taxon, score, detail, tone, width], index) => (
          <div className={`picture-hit-row ${tone}`} key={taxon}>
            <span>{index + 1}</span>
            <strong>{taxon}</strong>
            <b>{score}</b>
            <i style={{ width }} />
            <small>{detail}</small>
          </div>
        ))}
      </div>
    );
  }

  if (visual === 'gates') {
    return (
      <div className="analysis-picture-graphic gates" aria-label="Hard gate visual">
        {analysisGateTrail.map(([gate, value, tone]) => (
          <div className={tone} key={gate}>
            <span>{tone === 'repair' ? 'FIX' : 'PASS'}</span>
            <strong>{gate}</strong>
            <em>{value}</em>
          </div>
        ))}
      </div>
    );
  }

  if (visual === 'claim') {
    return (
      <div className="analysis-picture-graphic claim" aria-label="Safe claim boundary visual">
        <div className="overclaim-card">
          <strong>species overclaim?</strong>
          <span>blocked</span>
        </div>
        <div className="claim-arrow" />
        <div className="safe-rank-card">
          <strong>safe rank</strong>
          <span>bounded claim</span>
        </div>
        <div className="repair-note">metadata repair stays explicit</div>
      </div>
    );
  }

  return (
    <div className="analysis-picture-graphic pack" aria-label="Evidence pack export visual">
      {['CSV', 'audit', 'repair', 'DWC', 'DNA', 'ZIP'].map((label) => (
        <span key={label}>{label}</span>
      ))}
      <strong>Evidence Pack</strong>
      <em>methods + citations + exports</em>
    </div>
  );
}

function NatureCycleVisual() {
  return (
    <section className="panel nature-cycle-panel">
      <div className="nature-cycle-intro">
        <div>
          <p className="section-label">Nature-to-evidence cycle</p>
          <h2>The full cycle: nature produces signals, science turns them into safe evidence, and the evidence returns to nature as better decisions.</h2>
          <p>
            This is the bigger point of EcoGenesis. The tool is not only a DNA checker. It is a bridge between real
            biodiversity material, DNA marker evidence, molecular laboratories, GBIF publication and practical
            biodiversity decisions.
          </p>
        </div>
        <div className="nature-benefit-stack">
          {natureBenefitCards.map(([title, body]) => (
            <article key={title}>
              <strong>{title}</strong>
              <span>{body}</span>
            </article>
          ))}
        </div>
      </div>

      <figure className="nature-cycle-image-frame">
        <img
          src="/assets/nature-marker-cycle.png"
          alt="Nature to DNA marker evidence cycle showing biodiversity material, sequencing, compiler, open data map and conservation feedback"
        />
        <figcaption>
          Visual cycle: biological material and DNA marker regions move through sequencing, evidence compilation,
          GBIF-ready export and scientific feedback to biodiversity decisions.
        </figcaption>
      </figure>

      <AnimationStoryboardVisual />

      <div className="marker-source-board">
        <div>
          <p className="section-label">What enters the tool</p>
          <h3>DNA marker evidence, not one special sample type.</h3>
          <p>
            EcoGenesis evaluates marker results after identification/search: sequence, hit metrics, taxonomy,
            marker context and GBIF metadata. The sample source can vary; the core unit is the DNA marker record.
          </p>
        </div>
        <div className="marker-source-grid">
          {markerSourceCards.map(([title, body]) => (
            <article key={title}>
              <strong>{title}</strong>
              <span>{body}</span>
            </article>
          ))}
        </div>
      </div>

      <div className="cycle-ring" aria-label="DNA marker evidence lifecycle visualization">
        {natureCycleSteps.map(([index, title, body]) => (
          <article key={index}>
            <span>{index}</span>
            <strong>{title}</strong>
            <p>{body}</p>
          </article>
        ))}
      </div>

      <div className="nature-outcome-strip">
        <span>Less overclaiming</span>
        <span>Cleaner GBIF records</span>
        <span>Visible data gaps</span>
        <span>Better sampling priorities</span>
        <span>More reproducible biodiversity science</span>
      </div>
    </section>
  );
}

function AnimationStoryboardVisual() {
  return (
    <section className="animation-storyboard" id="animation-storyboard" aria-label="EcoGenesis analysis story frames">
      <div className="storyboard-heading">
        <div>
          <p className="section-label">Analysis story frames</p>
          <h3>Six visual moments that make the EcoGenesis workflow easy to understand.</h3>
          <p>
            The image above shows the big cycle. These frames turn the workflow into a clear judging story: DNA marker
            evidence is compared, uncertainty is made visible, unsafe claims are downgraded, repair needs stay explicit
            and the final Evidence Pack shows what can be published safely.
          </p>
        </div>
        <div className="storyboard-motion-key">
          <span>Visual story</span>
          <span>Safe decisions</span>
          <span>Ready to present</span>
        </div>
      </div>
      <div className="storyboard-grid">
        {animationStoryboardFrames.map(([index, title, body, motion]) => (
          <article className="storyboard-frame" data-animation-frame={index} key={index}>
            <figure className="storyboard-visual generated-storyboard-image">
              <img
                src={`/assets/storyboard-frame-${index}.png`}
                alt={`EcoGenesis visual story frame ${index}: ${title}`}
              />
            </figure>
            <div className="storyboard-caption">
              <span>Frame {index}</span>
              <strong>{title}</strong>
              <p>{body}</p>
              <em>{motion}</em>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function SciencePurposeVisual() {
  return (
    <section className="panel science-purpose-panel">
      <div>
        <p className="section-label">Why this matters in science</p>
        <h2>The project is about converting molecular signals into reusable evidence.</h2>
        <p>
          Modern biodiversity science produces enormous streams of molecular detections. The hard part is not only
          finding a similar sequence. The hard part is deciding what can be claimed safely, what must be downgraded,
          and what must be repaired before the record enters GBIF-mediated reuse.
        </p>
      </div>
      <div className="science-flow">
        {sciencePurposeSteps.map(([title, body], index) => (
          <article key={title}>
            <span>{String(index + 1).padStart(2, '0')}</span>
            <strong>{title}</strong>
            <p>{body}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function BeforeAfterScienceVisual() {
  return (
    <div className="visual-card science-comparison">
      <p className="section-label">Scientific change</p>
      <h3>From fragile top-hit spreadsheets to auditable evidence.</h3>
      <div className="before-after-grid">
        {beforeAfterScience.map(([title, body]) => (
          <article className={title.toLowerCase()} key={title}>
            <strong>{title}</strong>
            <p>{body}</p>
          </article>
        ))}
      </div>
      <div className="science-equation">
        <span>sequence match</span>
        <span>+</span>
        <span>safe rank</span>
        <span>+</span>
        <span>metadata</span>
        <span>=</span>
        <strong>reusable evidence</strong>
      </div>
    </div>
  );
}

function UserValueVisual() {
  return (
    <div className="visual-card">
      <p className="section-label">Who uses it</p>
      <h3>One workflow, several scientific audiences.</h3>
      <div className="user-value-grid">
        {scienceUsers.map(([title, body]) => (
          <article key={title}>
            <strong>{title}</strong>
            <span>{body}</span>
          </article>
        ))}
      </div>
    </div>
  );
}

function FutureImpactVisual() {
  return (
    <section className="panel future-impact-panel">
      <div>
        <p className="section-label">Where this leads</p>
        <h2>From one compiler to a Molecular Evidence Graph for GBIF.</h2>
        <p>
          The current project is the first working safety layer. The bigger scientific direction is a graph that
          connects DNA fragments, taxa, GBIF occurrence context, reference gaps, protein sanity checks, repair actions
          and cautious hypotheses in one reproducible evidence system.
        </p>
      </div>
      <div className="future-roadmap">
        {futureImpactSteps.map(([version, title, body]) => (
          <article key={version}>
            <span>{version}</span>
            <strong>{title}</strong>
            <p>{body}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function AlignmentVisual() {
  return (
    <div className="alignment-visual" aria-label="DNA sequence alignment visual">
      <SequenceRow label="Query" sequence={dnaQuery} reference={dnaQuery} />
      <SequenceRow label="Reference hit" sequence={dnaReference} reference={dnaQuery} />
      <SequenceRow label="Competitor hit" sequence={dnaCompetitor} reference={dnaQuery} />
      <div className="alignment-legend">
        <span><i className="match-swatch" /> match</span>
        <span><i className="mismatch-swatch" /> mismatch</span>
        <span><i className="coverage-swatch" /> aligned window</span>
      </div>
    </div>
  );
}

function SequenceRow({ label, sequence, reference }) {
  return (
    <div className="sequence-row">
      <strong>{label}</strong>
      <div className="sequence-strip">
        {sequence.split('').map((base, index) => {
          const match = base === reference[index];
          return (
            <span className={`base-tile ${base} ${match ? 'match' : 'mismatch'}`} key={`${label}-${index}`}>
              {base}
            </span>
          );
        })}
      </div>
    </div>
  );
}

function TopHitTrapVisual() {
  return (
    <div className="visual-card">
      <p className="section-label">Top-hit trap</p>
      <h3>High score is not enough if a competitor is too close.</h3>
      <div className="hit-stack">
        <div className="hit-row top">
          <span>Aedes albopictus</span>
          <strong>99.6%</strong>
        </div>
        <div className="hit-row competitor">
          <span>Aedes aegypti</span>
          <strong>98.2%</strong>
        </div>
        <div className="hit-row review">
          <span>Second hit boundary</span>
          <strong>tested</strong>
        </div>
      </div>
      <div className="formula-snapshot compact-formula">
        <MathRow><Mi>Delta</Mi><Sub>j</Sub><Op>=</Op><Mi>d</Mi><Sub>j</Sub><Op>-</Op><Mi>d</Mi><Sub>top</Sub></MathRow>
        <MathRow><Mi>B</Mi><Sub>j</Sub><Op>=</Op>1.96<Sqrt><Mi>SE</Mi><Sub>top</Sub><Sup>2</Sup><Op>+</Op><Mi>SE</Mi><Sub>j</Sub><Sup>2</Sup></Sqrt></MathRow>
      </div>
      <p>If the competitor is indistinguishable, species is blocked and LCA chooses the safe rank.</p>
    </div>
  );
}

function LcaTreeVisual() {
  return (
    <div className="visual-card">
      <p className="section-label">LCA tree</p>
      <h3>Shared fragments move upward to a safe taxon.</h3>
      <div className="tree-visual" aria-label="Taxonomic tree with safe LCA">
        <div>Arthropoda</div>
        <div>Insecta</div>
        <div>Diptera</div>
        <div>Culicidae</div>
        <div className="safe-node">Aedes genus: safe rank</div>
        <div className="species-branch">
          <span>A. albopictus</span>
          <span>A. aegypti</span>
        </div>
      </div>
      <div className="formula-snapshot compact-formula">
        <MathRow><Mi>SafeTaxon</Mi><Paren><Mi>f</Mi></Paren><Op>=</Op><Func>LCA</Func><Paren><Mi>T</Mi><Paren><Mi>f</Mi></Paren></Paren></MathRow>
      </div>
    </div>
  );
}

function BarcodeGapVisual() {
  return (
    <div className="visual-card">
      <p className="section-label">Barcode gap</p>
      <h3>The marker must separate inside-species and outside-species distance.</h3>
      <div className="gap-bars" aria-label="Barcode gap bars">
        <div>
          <span>Inside species variation</span>
          <i style={{ width: '42%' }} />
          <strong>D_intra = 0.009</strong>
        </div>
        <div>
          <span>Nearest outside species</span>
          <i style={{ width: '78%' }} />
          <strong>D_inter = 0.018</strong>
        </div>
      </div>
      <div className="formula-snapshot compact-formula">
        <MathRow><Mi>BG</Mi><Paren><Mi>t</Mi></Paren><Op>=</Op><Mi>D</Mi><Sub>inter</Sub><Paren><Mi>t</Mi></Paren><Op>-</Op><Mi>D</Mi><Sub>intra</Sub><Paren><Mi>t</Mi></Paren></MathRow>
        <MathRow><Mi>BG</Mi><Paren><Mi>t</Mi></Paren><Op>&gt;</Op>0<Op>=</Op><Mi>pass</Mi></MathRow>
      </div>
    </div>
  );
}

function KmerVisual() {
  return (
    <div className="visual-card">
      <p className="section-label">Diagnostic k-mers</p>
      <h3>The sequence is sliced into small windows and checked for unique signal.</h3>
      <div className="kmer-window-stack">
        {kmerTiles.map((tile, index) => (
          <div key={tile} style={{ marginLeft: `${index * 12}px` }}>
            <span>{tile}</span>
            <strong>{index === 0 ? 'diagnostic' : index === 3 ? 'shared' : 'checked'}</strong>
          </div>
        ))}
      </div>
      <div className="formula-snapshot compact-formula">
        <MathRow><Mi>DS</Mi><Paren><Mi>s</Mi>,<Mi>t</Mi></Paren><Op>=</Op><Frac top={<Abs><Mi>K</Mi><Sub>k</Sub><Paren><Mi>s</Mi></Paren><Op>cap</Op><Mi>D</Mi><Sub>k</Sub><Paren><Mi>t</Mi></Paren></Abs>} bottom={<Abs><Mi>K</Mi><Sub>k</Sub><Paren><Mi>s</Mi></Paren></Abs>} /></MathRow>
      </div>
    </div>
  );
}

function PublicationVisual() {
  const core = ['occurrenceID', 'basisOfRecord', 'scientificName', 'eventDate'];
  const dna = ['marker', 'sequenceID', 'referenceDatabase', 'identity', 'queryCoverage', 'methodOrSOP'];

  return (
    <div className="visual-card">
      <p className="section-label">GBIF readiness</p>
      <h3>A good taxon match still needs publication metadata.</h3>
      <div className="field-buckets">
        <div>
          <strong>Occurrence core</strong>
          {core.map((field) => <span key={field}>{field}</span>)}
        </div>
        <div>
          <strong>DNA-derived layer</strong>
          {dna.map((field) => <span key={field}>{field}</span>)}
        </div>
      </div>
      <p>Missing fields do not vanish. They become blockers and repair actions in the Evidence Pack.</p>
    </div>
  );
}

function ClaimBoundaryVisual() {
  return (
    <div className="visual-card">
      <p className="section-label">What can I claim?</p>
      <h3>The UI separates supported claims from tempting overclaims.</h3>
      <div className="claim-boundary-grid">
        <article className="safe">
          <strong>Safe</strong>
          <span>Sequence-derived evidence supports this safe rank under supplied references.</span>
        </article>
        <article className="repair">
          <strong>Repair first</strong>
          <span>Taxonomy may be useful, but date, DOI, method or occurrence fields are missing.</span>
        </article>
        <article className="blocked">
          <strong>Blocked</strong>
          <span>No absence, true distribution, trend or phenotype truth from these data alone.</span>
        </article>
      </div>
    </div>
  );
}

function ResearchAudit() {
  return (
    <section className="research-page">
      <section className="research-hero panel">
        <div>
          <p className="section-label">Research audit layer</p>
          <h2>What the 1000-record GBIF occurrence-audit suite really proves, and what it does not prove.</h2>
          <p>
            This layer keeps the project honest: the 1000-record suite validates occurrence evidence auditing,
            source concentration, metadata risks and safe scientific claim generation. It does not pretend to be
            the molecular fragment graph itself. The molecular compiler remains the core implemented engine, and
            the expanded Molecular Evidence Graph is the next research layer.
          </p>
        </div>
        <div className="proof-summary">
          <strong>Accepted separation</strong>
          <span>Occurrence audit is context. Barcode Compiler is the working molecular safety engine. Molecular Evidence Graph is the full direction.</span>
        </div>
      </section>

      <section className="metrics-grid">
        {scientificSuiteMetrics.map(([label, value, detail]) => (
          <article className="metric-card" key={label}>
            <strong>{value}</strong>
            <span>{label}</span>
            <small>{detail}</small>
          </article>
        ))}
      </section>

      <section className="panel">
        <p className="section-label">Product architecture</p>
        <h2>Three levels, no mixed promises.</h2>
        <div className="layer-grid">
          {architectureLevels.map(([level, title, body]) => (
            <article className="layer-card" key={level}>
              <span>{level.replace('Level ', '')}</span>
              <h3>{title}</h3>
              <p>{body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="panel">
        <p className="section-label">Occurrence suite result</p>
        <h2>Downloaded records are now separated from deduplicated records.</h2>
        <p className="proof-copy">
          The previous summary could look inconsistent because scenario metrics used retained/downloaded counts while
          `records_1000.csv` used deduplicated counts. The suite report now exposes both numbers so reviewers can see
          where duplicates and repeated records were removed.
        </p>
        <div className="analysis-table compact-analysis research-table">
          <div><strong>Scenario</strong><strong>Downloaded</strong><strong>Deduped</strong><strong>Datasets</strong><strong>Top share</strong><strong>Score</strong><strong>High uncertainty</strong></div>
          {scientificSuiteScenarios.map(([scenario, downloaded, deduped, datasets, share, score, uncertainty]) => (
            <div key={scenario}>
              <span>{scenario}</span>
              <span>{downloaded}</span>
              <span>{deduped}</span>
              <span>{datasets}</span>
              <span>{share}</span>
              <span>{score}</span>
              <span>{uncertainty}</span>
            </div>
          ))}
        </div>
      </section>

      <ScenarioHeatmap />

      <section className="panel two-column">
        <div>
          <p className="section-label">Main bottlenecks</p>
          <div className="stack-list">
            {researchBottlenecks.map(([title, body]) => (
              <article key={title}>
                <h3>{title}</h3>
                <p>{body}</p>
              </article>
            ))}
          </div>
        </div>
        <div>
          <p className="section-label">Report artifacts</p>
          <div className="artifact-table compact-artifacts">
            <div><strong>File</strong><strong>Meaning</strong></div>
            {researchArtifacts.map(([name, purpose]) => (
              <div key={name}>
                <strong>{name}</strong>
                <span>{purpose}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="panel final-proof">
        <p className="section-label">Upgrade direction</p>
        <h2>The next winning step is fragment-level evidence, not another abstract score.</h2>
        <p>
          The project should now evolve from occurrence audit into fragment sharedness: sequence fragment to all
          taxa carrying it, LCA safe rank, specificity, GBIF geography context, coding-marker protein sanity and
          safe/blocked claims. That turns ambiguous fragments into knowledge instead of hiding them behind a single
          top-hit label.
        </p>
      </section>
    </section>
  );
}

function ScenarioHeatmap() {
  return (
    <section className="panel">
      <p className="section-label">Risk heatmap</p>
      <h2>Reviewers see the weak spots before they trust the map.</h2>
      <div className="heatmap">
        <div className="heatmap-head">
          <strong>Scenario</strong>
          {heatmapColumns.map((column) => <strong key={column}>{column}</strong>)}
        </div>
        {scenarioHeatmapRows.map(([scenario, ...cells]) => (
          <div className="heatmap-row" key={scenario}>
            <strong>{scenario}</strong>
            {cells.map((status, index) => (
              <span className={`heat ${status}`} key={`${scenario}-${heatmapColumns[index]}`}>{status}</span>
            ))}
          </div>
        ))}
      </div>
      <p className="heatmap-note">
        Green means the limited evidence-context claim is usable. Yellow means caveated. Red means the UI should
        stop fine-scale or source-sensitive interpretation. Blue means the claim needs a DOI-backed GBIF download
        or derived dataset before publication.
      </p>
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
          reproducible evidence pack. The current contest build also exports the GSEG/GSIG proof layer: VSEA,
          theorem checklist, graph provenance, roundtrip checks and AI guardrails.
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
          gates plus the GSEG/GSIG graph-proof exports. Deeper protein, assay, repair and trait/function layers are
          kept as explicit roadmap or no-claim boundaries unless their evidence is present.
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
          evidence exports are generated, and GBIF-backed runs declare their source mode, including fixture fallback
          when network data are unavailable.
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

function FragmentGraphExplorer({
  searchStatus,
  referenceDatasets,
  selectedFragmentDataset,
  setSelectedFragmentDataset,
  fragmentSequenceId,
  setFragmentSequenceId,
  fragmentSequence,
  setFragmentSequence,
  fragmentGraph,
  fragmentGraphLoading,
  runFragmentGraph,
}) {
  const selectedDataset = referenceDatasets.find((dataset) => dataset.id === selectedFragmentDataset);
  const examples = referenceDatasets.flatMap((dataset) => (
    (dataset.example_queries || []).map((example) => ({ dataset, example }))
  ));
  const status = fragmentGraph?.classification?.status || 'not-run';

  return (
    <section className="fragment-graph-page">
      <div className="panel fragment-graph-hero">
        <div>
          <p className="eyebrow">Real fragment-to-taxa explorer</p>
          <h2>See where a DNA marker fragment appears in a reference dataset.</h2>
          <p>
            Paste a DNA marker fragment, choose a bundled or uploaded reference dataset, and EcoGenesis builds a
            taxonomic graph: fragment to reference hits, lineages, kingdoms and the safe LCA. The answer is bounded:
            it describes the selected reference evidence, not all of nature.
          </p>
        </div>
        <div className={`fragment-status-card ${safeClassName(status)}`}>
          <span>Current classification</span>
          <strong>{fragmentStatusTitle(status)}</strong>
          <p>{fragmentStatusExplanation(status)}</p>
        </div>
      </div>

      <div className="fragment-graph-layout">
        <aside className="panel fragment-control-panel">
          <p className="section-label">Input</p>
          <h3>Build a taxon graph</h3>
          <p>
            This is the right place to test “where does this exact marker region occur in my reference evidence?”
            Use curated FASTA references for serious work.
          </p>
          <label>
            Reference dataset
            <select
              aria-label="Fragment reference dataset"
              value={selectedFragmentDataset}
              onChange={(event) => {
                const dataset = referenceDatasets.find((item) => item.id === event.target.value);
                setSelectedFragmentDataset(event.target.value);
                if (dataset?.example_queries?.[0]?.sequence) {
                  setFragmentSequenceId(dataset.example_queries[0].sequence_id || dataset.example_queries[0].id || 'fragment-001');
                  setFragmentSequence(dataset.example_queries[0].sequence);
                }
              }}
            >
              {referenceDatasets.length ? referenceDatasets.map((dataset) => (
                <option key={dataset.id} value={dataset.id}>
                  {dataset.title}{dataset.source_type === 'uploaded' ? ' · uploaded' : ''}
                </option>
              )) : (
                <option value="ncbi_aedes_coi_small">NCBI Aedes COI small reference</option>
              )}
            </select>
          </label>
          {selectedDataset && (
            <div className="reference-dataset-note">
              <strong>{selectedDataset.marker || 'marker not declared'} · {selectedDataset.records} references</strong>
              <span>{selectedDataset.source_type === 'uploaded' ? 'Uploaded reference dataset' : 'Bundled reproducible reference dataset'}</span>
              {selectedDataset.usage_scope && <p>{selectedDataset.usage_scope}</p>}
            </div>
          )}
          <label>
            Fragment ID
            <input
              aria-label="Fragment sequence ID"
              type="text"
              value={fragmentSequenceId}
              onChange={(event) => setFragmentSequenceId(event.target.value)}
            />
          </label>
          <label>
            DNA marker fragment
            <textarea
              aria-label="DNA marker fragment"
              className="fragment-textarea"
              value={fragmentSequence}
              onChange={(event) => setFragmentSequence(event.target.value)}
              spellCheck="false"
            />
          </label>
          <button
            className="primary wide"
            type="button"
            onClick={() => runFragmentGraph()}
            disabled={fragmentGraphLoading || !fragmentSequence.trim()}
          >
            {fragmentGraphLoading ? 'Building graph...' : 'Build Taxon Graph'}
          </button>
          <div className="search-backend-status">
            <span>Search backend</span>
            <strong>{fragmentGraph?.backend_used || searchStatus?.preferred_backend || 'checking'}</strong>
            <small>{searchStatus?.message || 'Checking VSEARCH/BLAST+ and local fallback.'}</small>
          </div>

          {examples.length > 0 && (
            <div className="fragment-examples">
              <p className="section-label">Reference examples</p>
              {examples.map(({ dataset, example }) => (
                <button
                  key={`${dataset.id}-${example.id}`}
                  className="secondary"
                  type="button"
                  onClick={() => runFragmentGraph({
                    reference_dataset: dataset.id,
                    sequence: example.sequence,
                    sequence_id: example.sequence_id || example.id,
                  })}
                >
                  {example.label}
                </button>
              ))}
            </div>
          )}

          <div className="fragment-boundary-note">
            <strong>Boundary of the claim</strong>
            <span>This graph shows where the fragment appears inside the selected reference dataset.</span>
            <span>It does not prove natural occurrence, absence, phenotype or global distribution.</span>
            <span>To expand coverage, upload a larger curated reference FASTA in Run compiler.</span>
          </div>
        </aside>

        <section className="panel fragment-svg-panel">
          <div className="fragment-panel-heading">
            <div>
              <p className="section-label">Graph</p>
              <h3>Fragment → hits → lineages → safe LCA</h3>
            </div>
            {fragmentGraph?.classification && (
              <span className={`fragment-status-pill ${safeClassName(fragmentGraph.classification.status)}`}>
                {fragmentGraph.classification.status}
              </span>
            )}
          </div>
          <FragmentGraphSvg graph={fragmentGraph} loading={fragmentGraphLoading} />
        </section>

        <aside className="panel fragment-summary-panel">
          <p className="section-label">Result</p>
          <FragmentGraphSummary graph={fragmentGraph} loading={fragmentGraphLoading} />
        </aside>
      </div>
    </section>
  );
}

function FragmentGraphSummary({ graph, loading }) {
  if (loading) {
    return (
      <div className="fragment-empty-summary">
        <h3>Building graph...</h3>
        <p>EcoGenesis is searching the selected reference dataset and compiling safe-rank evidence.</p>
      </div>
    );
  }
  if (!graph) {
    return (
      <div className="fragment-empty-summary">
        <h3>No graph yet</h3>
        <p>Choose a reference dataset, paste a fragment and run the graph. Start with the bundled Aedes or Quercus examples.</p>
      </div>
    );
  }
  const { classification } = graph;
  const topHits = (graph.hits || []).slice(0, 8);
  const rankDistribution = Object.entries(classification.rank_distribution || {});

  return (
    <div className="fragment-summary-stack">
      <div className={`fragment-verdict ${safeClassName(classification.status)}`}>
        <span>Classification</span>
        <strong>{fragmentStatusTitle(classification.status)}</strong>
        <p>{fragmentStatusExplanation(classification.status)}</p>
      </div>
      <div className="fragment-safe-taxon">
        <span>Safe taxon through LCA</span>
        <strong>{classification.safe_taxon?.name || 'No safe taxon'}</strong>
        <small>{classification.safe_taxon?.rank || 'none'}{classification.safe_taxon?.taxon_key ? ` · GBIF ${classification.safe_taxon.taxon_key}` : ''}</small>
      </div>
      <div className="fragment-mini-metrics">
        <Metric label="Informative hits" value={classification.informative_hits} />
        <Metric label="Taxa" value={classification.taxa_count} />
        <Metric label="Query length" value={graph.query?.sequence_length} />
      </div>
      <SourceMonitor sources={graph.source_monitor || []} />
      <SegmentEvidenceList segments={graph.segments || []} />
      <div className="fragment-claim-box">
        <strong>Safe to claim</strong>
        <span>{graph.claim_boundary?.supported || safeClaimForStatus(classification.status, classification.safe_taxon)}</span>
      </div>
      <div className="fragment-claim-box blocked">
        <strong>Do not claim</strong>
        <span>{(graph.claim_boundary?.not_supported || ['absence, true distribution, phenotype, abundance or global presence claims']).join('; ')}</span>
      </div>
      <div>
        <h4>Kingdoms found</h4>
        <div className="chip-row">
          {(classification.kingdoms?.length ? classification.kingdoms : ['none']).map((kingdom) => (
            <span key={kingdom} className="chip">{kingdom}</span>
          ))}
        </div>
      </div>
      {rankDistribution.length > 0 && (
        <div>
          <h4>Rank distribution</h4>
          <div className="rank-distribution">
            {rankDistribution.map(([rank, count]) => (
              <span key={rank}><strong>{rank}</strong>{count}</span>
            ))}
          </div>
        </div>
      )}
      <div>
        <h4>Top hits</h4>
        {topHits.length ? (
          <ol className="ranked-list compact-list">
            {topHits.map((hit) => (
              <li key={hit.reference_id}>
                <strong>{hit.taxon}</strong>
                <span>{hit.identity}% identity · {hit.query_coverage}% coverage · {hit.reference_id}</span>
              </li>
            ))}
          </ol>
        ) : (
          <p className="hint">No hits returned for the selected reference dataset.</p>
        )}
      </div>
      <div className="fragment-caveat">
        <strong>Caveat</strong>
        <span>{classification.caveat}</span>
      </div>
    </div>
  );
}

function SourceMonitor({ sources }) {
  if (!sources.length) return null;
  return (
    <div className="source-monitor">
      <h4>Source monitor</h4>
      {sources.map((source) => (
        <div key={`${source.source}-${source.detail}`} className={source.status}>
          <strong>{source.source}</strong>
          <span>{source.status}</span>
          <small>{source.detail}</small>
        </div>
      ))}
    </div>
  );
}

function SegmentEvidenceList({ segments }) {
  if (!segments.length) return null;
  return (
    <div className="segment-evidence-list">
      <h4>Segment map</h4>
      {segments.slice(0, 5).map((segment) => {
        const summary = segment.match_summary || {};
        const safe = summary.safe_lca || {};
        return (
          <article key={segment.segment_id}>
            <div>
              <strong>{segment.segment_start}-{segment.segment_end} bp</strong>
              <span>{segment.segment_class?.replaceAll('_', ' ') || 'segment'}</span>
            </div>
            <div className="segment-evidence-metrics">
              <span>{formatPercent(summary.best_identity)} identity</span>
              <span>{formatPercent(summary.best_query_coverage)} coverage</span>
              <span>{safe.name || 'No safe taxon'} · {safe.rank || 'none'}</span>
            </div>
            {segment.known_annotations?.length > 0 && (
              <small>{segment.known_annotations.map((annotation) => annotation.label).slice(0, 2).join(' · ')}</small>
            )}
          </article>
        );
      })}
    </div>
  );
}

function FragmentGraphSvg({ graph, loading }) {
  if (loading) {
    return (
      <div className="fragment-graph-empty">
        <div className="graph-loader" />
        <strong>Searching reference hits and arranging taxonomy lanes...</strong>
      </div>
    );
  }
  if (!graph) {
    return (
      <div className="fragment-graph-empty">
        <strong>Run a fragment search to build the graph.</strong>
        <span>Nodes will appear as fragment, dataset, reference hits, taxonomic ranks and safe LCA.</span>
      </div>
    );
  }

  const speciesCount = (graph.nodes || []).filter((node) => node.type === 'species').length;
  const shouldUseSharedTree = speciesCount >= 5 || (
    graph.classification?.status === 'higher-rank-shared'
    && (graph.classification?.taxa_count || 0) >= 4
  );

  return (
    <ZoomableFragmentGraph>
      {shouldUseSharedTree ? <SharedFragmentTreeSvg graph={graph} /> : <StandardFragmentDashboardSvg graph={graph} />}
    </ZoomableFragmentGraph>
  );
}

const DEFAULT_GRAPH_ZOOM = 1.25;
const MIN_GRAPH_ZOOM = 0.8;
const MAX_GRAPH_ZOOM = 2.5;
const GRAPH_ZOOM_STEP = 0.25;

function ZoomableFragmentGraph({ children }) {
  const [zoom, setZoom] = useState(DEFAULT_GRAPH_ZOOM);
  const [fitMode, setFitMode] = useState(false);
  const zoomPercent = Math.round(zoom * 100);
  const zoomBy = (delta) => {
    setFitMode(false);
    setZoom((current) => {
      const baseZoom = fitMode ? 1 : current;
      return Number(Math.min(MAX_GRAPH_ZOOM, Math.max(MIN_GRAPH_ZOOM, baseZoom + delta)).toFixed(2));
    });
  };

  return (
    <div className="fragment-zoom-frame">
      <div className="fragment-zoom-toolbar" aria-label="Graph zoom controls">
        <div>
          <strong>Graph zoom</strong>
          <span>Use controls, then scroll inside the graph when it is enlarged.</span>
        </div>
        <div className="fragment-zoom-actions">
          <button
            type="button"
            className="secondary compact"
            aria-label="Zoom out graph"
            onClick={() => zoomBy(-GRAPH_ZOOM_STEP)}
            disabled={zoom <= MIN_GRAPH_ZOOM}
          >
            −
          </button>
          <span className="fragment-zoom-value" aria-live="polite">{fitMode ? 'Fit' : `${zoomPercent}%`}</span>
          <button
            type="button"
            className="secondary compact"
            aria-label="Zoom in graph"
            onClick={() => zoomBy(GRAPH_ZOOM_STEP)}
            disabled={zoom >= MAX_GRAPH_ZOOM}
          >
            +
          </button>
          <button type="button" className="secondary compact" onClick={() => setFitMode(true)} aria-label="Fit graph to panel">
            Fit
          </button>
          <button
            type="button"
            className="secondary compact"
            onClick={() => {
              setFitMode(false);
              setZoom(DEFAULT_GRAPH_ZOOM);
            }}
            aria-label="Reset graph zoom"
          >
            Reset
          </button>
        </div>
      </div>
      <div className="fragment-zoom-viewport" data-zoom-percent={fitMode ? 'fit' : zoomPercent}>
        <div
          className="fragment-zoom-content"
          style={{
            width: fitMode ? '100%' : `${Math.round(1080 * zoom)}px`,
            marginInline: fitMode || zoom < 1 ? 'auto' : 0,
          }}
        >
          {children}
        </div>
      </div>
    </div>
  );
}

function StandardFragmentDashboardSvg({ graph }) {
  const {
    fragmentNode,
    datasetNode,
    warningNode,
    safeLcaNode,
    hitNodes,
    lineageNodes,
    safeTaxon,
  } = buildStandardFragmentDashboard(graph);
  const status = graph.classification?.status || 'not-run';
  const safeName = safeTaxon?.name || safeLcaNode?.name || 'safe LCA';
  const safeRank = safeTaxon?.rank || safeLcaNode?.rank || 'rank';
  const queryLength = graph.query?.sequence_length || fragmentNode?.sequence_length || '-';
  const [selectedItem, setSelectedItem] = useState(() => standardSelectionDetail({
    type: 'safe',
    safeName,
    safeRank,
    status,
    hitCount: hitNodes.length,
  }));
  const topHit = hitNodes[0];
  const detailLines = wrapSvgText(selectedItem.description, 44).slice(0, 2);
  const actionLines = wrapSvgText(selectedItem.action, 58).slice(0, 2);
  const selectedHitId = selectedItem.hitId;
  const selectedTaxonId = selectedItem.taxonId;
  const activateItem = (item) => setSelectedItem(item);
  const keyboardSelect = (item) => (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      activateItem(item);
    }
  };
  const lineagePositions = buildLineageLayout(lineageNodes);

  return (
    <div className="fragment-svg-scroll standard-dashboard" aria-label="Fragment evidence decision dashboard">
      <svg className="fragment-graph-svg standard-dashboard-svg" viewBox="0 0 1080 650" role="img" aria-label="Fragment evidence decision dashboard">
        <defs>
          <filter id="standardCardShadow" x="-8%" y="-8%" width="116%" height="116%">
            <feDropShadow dx="0" dy="12" stdDeviation="14" floodColor="#254338" floodOpacity="0.12" />
          </filter>
          <filter id="standardSafeGlow" x="-40%" y="-40%" width="180%" height="180%">
            <feDropShadow dx="0" dy="0" stdDeviation="5" floodColor="#2b8a4b" floodOpacity="0.42" />
          </filter>
          <linearGradient id="standardDashWash" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#fbfdfb" />
            <stop offset="100%" stopColor="#eef6f3" />
          </linearGradient>
        </defs>
        <rect x="14" y="14" width="1052" height="618" rx="22" className="standard-dashboard-shell" />

        <g className="shared-card standard-summary-card" filter="url(#standardCardShadow)">
          <rect x="34" y="38" width="394" height="574" rx="16" />
          <text x="58" y="72" className="shared-card-title">Evidence decision</text>
          <text x="58" y="96" className="shared-muted">A compact reading of hits, safe rank and claim boundary.</text>

          <g className={`standard-status-orb ${safeClassName(status)}`} transform="translate(126 162)">
            <circle r="56" />
            <text y="-8" textAnchor="middle">{hitNodes.length}</text>
            <text y="15" textAnchor="middle">hits</text>
          </g>

          <text x="208" y="138" className="shared-kpi-label">Classification</text>
          <text x="208" y="166" className="standard-status-title">{fragmentStatusTitle(status)}</text>
          <text x="208" y="196" className="shared-kpi-small">{queryLength} bp query · {safeRank} safe rank</text>

          <g className="shared-fragment-strip" transform="translate(58 238)">
            <rect width="344" height="58" rx="12" />
            <text x="16" y="23">Query DNA fragment</text>
            <text x="16" y="43">{fragmentPreview(graph.query?.sequence || fragmentNode?.sequence || 'ACGTTGACCTAGGCTTACGATCGTACCGATGC')}</text>
          </g>

          <g
            className={`standard-safe-summary shared-click-target ${selectedItem.type === 'safe' ? 'selected' : ''}`}
            transform="translate(58 326)"
            role="button"
            tabIndex="0"
            aria-label={`Select safe LCA ${safeName}`}
            onClick={() => activateItem(standardSelectionDetail({ type: 'safe', safeName, safeRank, status, hitCount: hitNodes.length }))}
            onKeyDown={keyboardSelect(standardSelectionDetail({ type: 'safe', safeName, safeRank, status, hitCount: hitNodes.length }))}
          >
            <rect width="344" height="72" rx="12" />
            <text x="18" y="24">Safe LCA</text>
            <text x="18" y="48">{safeName}</text>
            <text x="238" y="48">{safeRank}</text>
          </g>

          <g className="shared-claim-lock" transform="translate(58 500)">
            <rect width="344" height="86" rx="12" />
            <text x="18" y="19">Selection detail</text>
            <text x="18" y="37">{shortenLabel(selectedItem.title, 36)}</text>
            <text x="18" y="55">{detailLines[0] || selectedItem.description}</text>
            {detailLines[1] && <text x="18" y="70">{detailLines[1]}</text>}
          </g>
        </g>

        <g className="shared-card lineage-card" filter="url(#standardCardShadow)">
          <rect x="454" y="38" width="592" height="258" rx="16" />
          <text x="482" y="72" className="shared-card-title">Lineage path</text>
          <text x="482" y="96" className="shared-muted">Clean rank order from broad clade to the candidate taxon.</text>
          {lineageNodes.slice(0, -1).map((node, index) => {
            const source = lineagePositions[node.id];
            const target = lineagePositions[lineageNodes[index + 1].id];
            if (!source || !target) return null;
            return (
              <line
                key={`${node.id}-lineage-${lineageNodes[index + 1].id}`}
                x1={source.x}
                y1={source.y}
                x2={target.x}
                y2={target.y}
                className={`standard-lineage-link ${selectedTaxonId === node.id || selectedTaxonId === lineageNodes[index + 1].id ? 'selected' : ''}`}
              />
            );
          })}
          {lineageNodes.map((node) => {
            const position = lineagePositions[node.id];
            if (!position) return null;
            const isSafe = node.label === safeName || node.id === safeLcaNode?.id || node.is_safe_taxon;
            return (
              <g
                key={node.id}
                className={`standard-lineage-node shared-click-target ${isSafe ? 'safe' : ''} ${selectedTaxonId === node.id ? 'selected' : ''}`}
                transform={`translate(${position.x} ${position.y})`}
                role="button"
                tabIndex="0"
                aria-label={`Select lineage taxon ${node.label}`}
                onClick={() => activateItem(standardSelectionDetail({ type: 'taxon', taxon: node, safeName, safeRank, status }))}
                onKeyDown={keyboardSelect(standardSelectionDetail({ type: 'taxon', taxon: node, safeName, safeRank, status }))}
              >
                <rect x="-58" y="-22" width="116" height="44" rx="10" />
                <text y="-3" textAnchor="middle">{shortenLabel(node.label, 16)}</text>
                <text y="14" textAnchor="middle">{node.rank || node.type}</text>
              </g>
            );
          })}
          <text x="482" y="276" className="shared-warning-line">Lineage is reference-backed context, not proof of global distribution.</text>
        </g>

        <g className="shared-card hit-card" filter="url(#standardCardShadow)">
          <rect x="454" y="322" width="592" height="290" rx="16" />
          <text x="482" y="356" className="shared-card-title">Hit comparison</text>
          <text x="482" y="380" className="shared-muted">The compiler compares top hits before allowing a safe rank.</text>
          {hitNodes.slice(0, 4).map((hit, index) => {
            const y = 410 + index * 45;
            const identityWidth = Math.max(12, Math.min(178, Number(hit.identity || 0) * 1.78));
            const coverageWidth = Math.max(12, Math.min(178, Number(hit.coverage || hit.query_coverage || 0) * 1.78));
            return (
              <g
                key={hit.id}
                className={`standard-hit-row shared-click-target ${selectedHitId === hit.id ? 'selected' : ''}`}
                transform={`translate(482 ${y})`}
                role="button"
                tabIndex="0"
                aria-label={`Select hit ${hit.label}`}
                onClick={() => activateItem(standardSelectionDetail({ type: 'hit', hit, safeName, safeRank, status, topHit }))}
                onKeyDown={keyboardSelect(standardSelectionDetail({ type: 'hit', hit, safeName, safeRank, status, topHit }))}
              >
                <rect width="244" height="36" rx="10" />
                <text x="14" y="15">{shortenLabel(hit.label, 25)}</text>
                <text x="14" y="29">{formatPercent(hit.identity)} id · {formatPercent(hit.coverage || hit.query_coverage)} cov</text>
                <rect x="150" y="11" width="78" height="5" rx="3" className="standard-hit-track" />
                <rect x="150" y="11" width={identityWidth * 0.43} height="5" rx="3" className="standard-hit-identity" />
                <rect x="150" y="23" width="78" height="5" rx="3" className="standard-hit-track" />
                <rect x="150" y="23" width={coverageWidth * 0.43} height="5" rx="3" className="standard-hit-coverage" />
              </g>
            );
          })}
          {hitNodes.slice(0, 4).map((hit, index) => {
            const y = 428 + index * 45;
            return (
              <line
                key={`${hit.id}-safe-connector`}
                x1="728"
                y1={y}
                x2="806"
                y2="462"
                className={`standard-hit-safe-link ${selectedHitId === hit.id || selectedItem.type === 'safe' ? 'selected' : ''}`}
              />
            );
          })}
          <g
            className={`standard-safe-node shared-click-target ${selectedItem.type === 'safe' ? 'selected' : ''}`}
            transform="translate(866 462)"
            filter="url(#standardSafeGlow)"
            role="button"
            tabIndex="0"
            aria-label={`Select safe LCA ${safeName}`}
            onClick={() => activateItem(standardSelectionDetail({ type: 'safe', safeName, safeRank, status, hitCount: hitNodes.length }))}
            onKeyDown={keyboardSelect(standardSelectionDetail({ type: 'safe', safeName, safeRank, status, hitCount: hitNodes.length }))}
          >
            <rect x="-86" y="-34" width="172" height="68" rx="14" />
            <text y="-7" textAnchor="middle">Safe claim</text>
            <text y="15" textAnchor="middle">{shortenLabel(safeName, 20)}</text>
          </g>
          {warningNode && (
            <g className="standard-warning-note" transform="translate(760 550)">
              <rect x="-124" y="-20" width="248" height="40" rx="12" />
              <text y="-2" textAnchor="middle">{shortenLabel(warningNode.label, 42)}</text>
              <text y="14" textAnchor="middle">review caveat before publication</text>
            </g>
          )}
        </g>

        <g className="shared-action-strip" transform="translate(454 614)">
          <rect width="592" height="24" rx="8" />
          <text x="14" y="16">{actionLines.join(' ')}</text>
        </g>

        {datasetNode && (
          <text x="226" y="632" className="shared-footer-note">
            Dataset: {shortenLabel(datasetNode.label, 42)}
          </text>
        )}
      </svg>
    </div>
  );
}

function buildStandardFragmentDashboard(graph) {
  const nodes = graph.nodes || [];
  const rankOrder = ['kingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species'];
  const fragmentNode = nodes.find((node) => node.type === 'fragment');
  const datasetNode = nodes.find((node) => node.type === 'reference_dataset');
  const warningNode = nodes.find((node) => node.type === 'warning');
  const safeLcaNode = nodes.find((node) => node.type === 'safe_lca');
  const hitNodes = nodes.filter((node) => node.type === 'reference_hit');
  const safeTaxon = graph.classification?.safe_taxon || {
    rank: safeLcaNode?.rank,
    name: safeLcaNode?.name || safeLcaNode?.label,
    taxon_key: safeLcaNode?.taxon_key,
  };
  const taxonNodes = nodes
    .filter((node) => rankOrder.includes(node.type))
    .sort((first, second) => rankOrder.indexOf(first.type) - rankOrder.indexOf(second.type));
  const hasSafeTaxonInLineage = taxonNodes.some((node) => node.label === safeTaxon?.name || node.name === safeTaxon?.name);
  const lineageNodes = hasSafeTaxonInLineage || !safeLcaNode
    ? taxonNodes
    : [...taxonNodes, { ...safeLcaNode, type: safeLcaNode.rank || 'safe_lca', rank: safeLcaNode.rank || safeTaxon?.rank }];

  return {
    fragmentNode,
    datasetNode,
    warningNode,
    safeLcaNode,
    hitNodes,
    lineageNodes,
    safeTaxon,
  };
}

function buildLineageLayout(nodes) {
  const positions = [
    { x: 528, y: 146 },
    { x: 660, y: 146 },
    { x: 792, y: 146 },
    { x: 924, y: 146 },
    { x: 594, y: 230 },
    { x: 746, y: 230 },
    { x: 898, y: 230 },
    { x: 974, y: 230 },
  ];
  return Object.fromEntries(nodes.map((node, index) => [node.id, positions[index] || positions[positions.length - 1]]));
}

function standardSelectionDetail({ type, hit, taxon, safeName, safeRank, status, hitCount, topHit }) {
  if (type === 'hit' && hit) {
    const isTopHit = !topHit || topHit.id === hit.id;
    return {
      type,
      hitId: hit.id,
      title: hit.label,
      description: `${isTopHit ? 'Top' : 'Alternative'} reference hit with ${formatPercent(hit.identity)} identity and ${formatPercent(hit.coverage || hit.query_coverage)} coverage. It supports the decision only after competitor and LCA checks.`,
      action: `Do not use this hit alone; the safe claim remains ${safeRank} ${safeName} inside this reference dataset.`,
    };
  }
  if (type === 'taxon' && taxon) {
    return {
      type,
      taxonId: taxon.id,
      title: `${taxon.label} (${taxon.rank || taxon.type})`,
      description: `This lineage node explains where the evidence sits in taxonomy. It is context for interpreting the fragment, not an occurrence or distribution claim.`,
      action: `The compiler uses the lineage to compute the lowest safe taxon, currently ${safeRank} ${safeName}.`,
    };
  }
  return {
    type: 'safe',
    title: `Safe claim: ${safeName}`,
    description: `${fragmentStatusTitle(status)} is the current bounded decision. ${hitCount || 0} informative hits were considered before the safe rank was chosen.`,
    action: `Click a hit or lineage node to inspect why the safe output is ${safeRank} ${safeName}.`,
  };
}

function SharedFragmentTreeSvg({ graph }) {
  const {
    fragmentNode,
    datasetNode,
    warningNode,
    safeLcaNode,
    groups,
    totalSpecies,
    totalHits,
  } = buildSharedFragmentDashboard(graph);
  const safeName = graph.classification?.safe_taxon?.name || safeLcaNode?.name || 'shared LCA';
  const safeRank = graph.classification?.safe_taxon?.rank || safeLcaNode?.rank || 'higher rank';
  const queryLength = graph.query?.sequence_length || fragmentNode?.sequence_length || '-';
  const [selectedItem, setSelectedItem] = useState(() => sharedSelectionDetail({
    type: 'safe',
    safeName,
    safeRank,
    totalSpecies,
    groups,
  }));
  const circumference = 2 * Math.PI * 49;
  let donutOffset = 0;
  const donutSegments = groups.map((group) => {
    const length = totalSpecies ? (group.species.length / totalSpecies) * circumference : circumference;
    const segment = {
      color: group.color,
      length,
      offset: donutOffset,
    };
    donutOffset += length;
    return segment;
  });
  const scatterPoints = groups.flatMap((group, groupIndex) => {
    const centers = [
      { x: 610, y: 152 },
      { x: 788, y: 194 },
      { x: 914, y: 126 },
      { x: 902, y: 220 },
      { x: 688, y: 104 },
    ];
    const offsets = [
      [-35, -24],
      [-14, 18],
      [18, -12],
      [35, 24],
      [-28, 30],
      [10, 34],
      [30, -34],
      [-4, -34],
    ];
    const center = centers[groupIndex % centers.length];
    return group.species.map((species, speciesIndex) => {
      const offset = offsets[speciesIndex % offsets.length];
      return {
        id: `${group.genus.id}-${species.id}-cluster`,
        x: center.x + offset[0],
        y: center.y + offset[1],
        color: group.color,
        label: species.label,
        genus: group.genus.label,
        species,
        group,
      };
    });
  });
  const network = buildSharedNetworkLayout(groups, safeName);
  const detailLines = wrapSvgText(selectedItem.description, 58).slice(0, 3);
  const leftDetailLines = wrapSvgText(selectedItem.description, 44).slice(0, 2);
  const actionLines = wrapSvgText(selectedItem.action, 58).slice(0, 2);
  const selectedGroupId = selectedItem.groupId;
  const selectedSpeciesId = selectedItem.speciesId;
  const activateItem = (item) => setSelectedItem(item);
  const keyboardSelect = (item) => (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      activateItem(item);
    }
  };

  return (
    <div className="fragment-svg-scroll shared-dashboard" aria-label="Shared short fragment dashboard">
      <svg className="fragment-graph-svg shared-dashboard-svg" viewBox="0 0 1080 650" role="img" aria-label="Shared short fragment dashboard">
        <defs>
          <filter id="sharedCardShadow" x="-8%" y="-8%" width="116%" height="116%">
            <feDropShadow dx="0" dy="12" stdDeviation="14" floodColor="#254338" floodOpacity="0.12" />
          </filter>
          <filter id="sharedSafeGlow" x="-40%" y="-40%" width="180%" height="180%">
            <feDropShadow dx="0" dy="0" stdDeviation="5" floodColor="#2b8a4b" floodOpacity="0.42" />
          </filter>
          <linearGradient id="sharedDashWash" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#fbfdfb" />
            <stop offset="100%" stopColor="#eef6f3" />
          </linearGradient>
        </defs>
        <rect x="14" y="14" width="1052" height="618" rx="22" className="shared-dashboard-shell" />

        <g className="shared-card summary-card" filter="url(#sharedCardShadow)">
          <rect x="34" y="38" width="394" height="574" rx="16" />
          <text x="58" y="72" className="shared-card-title">Short-fragment evidence</text>
          <text x="58" y="96" className="shared-muted">The same marker segment appears in several reference taxa.</text>

          <circle
            cx="126"
            cy="166"
            r="49"
            className="shared-donut-base shared-click-target"
            role="button"
            tabIndex="0"
            aria-label="Select all shared fragment evidence"
            onClick={() => activateItem(sharedSelectionDetail({ type: 'safe', safeName, safeRank, totalSpecies, groups }))}
            onKeyDown={keyboardSelect(sharedSelectionDetail({ type: 'safe', safeName, safeRank, totalSpecies, groups }))}
          />
          {donutSegments.map((segment, index) => (
            <circle
              key={`${segment.color}-${index}`}
              cx="126"
              cy="166"
              r="49"
              className="shared-donut-segment"
              stroke={segment.color}
              strokeDasharray={`${segment.length} ${circumference - segment.length}`}
              strokeDashoffset={-segment.offset}
              transform="rotate(-90 126 166)"
            />
          ))}
          <text x="126" y="158" textAnchor="middle" className="shared-donut-number">{totalSpecies}</text>
          <text x="126" y="181" textAnchor="middle" className="shared-donut-label">species</text>
          <text x="208" y="144" className="shared-kpi-label">Matched reference hits</text>
          <text x="208" y="176" className="shared-kpi-number">{totalHits}</text>
          <text x="208" y="205" className="shared-kpi-small">{groups.length} genera · {queryLength} bp query</text>

          <g className="shared-fragment-strip" transform="translate(58 240)">
            <rect width="344" height="58" rx="12" />
            <text x="16" y="23">Query DNA fragment</text>
            <text x="16" y="43">ACGTTGACCTAGGCTTACGATCGTACCGATGC</text>
          </g>

          {groups.map((group, index) => {
            const y = 334 + index * 55;
            const barWidth = totalSpecies ? Math.max(32, (group.species.length / totalSpecies) * 168) : 32;
            return (
              <g
                key={group.genus.id}
                className={`shared-genus-row shared-click-target ${selectedGroupId === group.genus.id ? 'selected' : ''}`}
                transform={`translate(58 ${y})`}
                role="button"
                tabIndex="0"
                aria-label={`Select summary genus ${group.genus.label}`}
                onClick={() => activateItem(sharedSelectionDetail({ type: 'genus', group, safeName, safeRank, totalSpecies }))}
                onKeyDown={keyboardSelect(sharedSelectionDetail({ type: 'genus', group, safeName, safeRank, totalSpecies }))}
              >
                <circle cx="9" cy="8" r="7" fill={group.color} />
                <text x="26" y="13" className="shared-genus-name">{group.genus.label}</text>
                <text x="260" y="13" className="shared-genus-count">{group.species.length} species</text>
                <rect x="0" y="25" width="286" height="9" rx="5" className="shared-bar-track" />
                <rect x="0" y="25" width={barWidth} height="9" rx="5" fill={group.color} />
              </g>
            );
          })}

          <g className="shared-claim-lock" transform="translate(58 500)">
            <rect width="344" height="86" rx="12" />
            <text x="18" y="19">Species claim blocked</text>
            <text x="18" y="37">{shortenLabel(selectedItem.title, 35)}</text>
            <text x="18" y="55">{leftDetailLines[0] || `Safe claim: ${safeRank} · ${safeName}`}</text>
            {leftDetailLines[1] && <text x="18" y="70">{leftDetailLines[1]}</text>}
          </g>
        </g>

        <g className="shared-card scatter-card" filter="url(#sharedCardShadow)">
          <rect x="454" y="38" width="592" height="258" rx="16" />
          <text x="482" y="72" className="shared-card-title">Taxonomic cluster map</text>
          <text x="482" y="96" className="shared-muted">Each point is one species hit; color groups points by genus.</text>
          <g transform="translate(506 116)">
            <rect width="456" height="150" rx="10" className="shared-plot-area" />
            {[0, 1, 2, 3, 4].map((tick) => (
              <line key={`v-${tick}`} x1={tick * 114} x2={tick * 114} y1="0" y2="150" className="shared-plot-grid" />
            ))}
            {[0, 1, 2, 3].map((tick) => (
              <line key={`h-${tick}`} x1="0" x2="456" y1={tick * 50} y2={tick * 50} className="shared-plot-grid" />
            ))}
          </g>
          {scatterPoints.map((point) => (
            <g
              key={point.id}
              className={`shared-cluster-point shared-click-target ${selectedSpeciesId === point.species.id ? 'selected' : ''}`}
              role="button"
              tabIndex="0"
              aria-label={`Select cluster species ${point.label}`}
              onClick={() => activateItem(sharedSelectionDetail({ type: 'species', group: point.group, species: point.species, safeName, safeRank, totalSpecies }))}
              onKeyDown={keyboardSelect(sharedSelectionDetail({ type: 'species', group: point.group, species: point.species, safeName, safeRank, totalSpecies }))}
            >
              <title>{point.label} · {point.genus}</title>
              <circle cx={point.x} cy={point.y} r="7" fill={point.color} />
            </g>
          ))}
          {groups.map((group, index) => {
            const labelPositions = [
              { x: 548, y: 250 },
              { x: 750, y: 252 },
              { x: 900, y: 74 },
              { x: 890, y: 270 },
              { x: 660, y: 74 },
            ];
            const position = labelPositions[index % labelPositions.length];
            return (
              <g
                key={`${group.genus.id}-cluster-label`}
                className={`shared-cluster-label shared-click-target ${selectedGroupId === group.genus.id ? 'selected' : ''}`}
                transform={`translate(${position.x} ${position.y})`}
                role="button"
                tabIndex="0"
                aria-label={`Select cluster genus ${group.genus.label}`}
                onClick={() => activateItem(sharedSelectionDetail({ type: 'genus', group, safeName, safeRank, totalSpecies }))}
                onKeyDown={keyboardSelect(sharedSelectionDetail({ type: 'genus', group, safeName, safeRank, totalSpecies }))}
              >
                <circle cx="0" cy="-4" r="5" fill={group.color} />
                <text x="13" y="0">{group.genus.label}</text>
              </g>
            );
          })}
          <text x="482" y="276" className="shared-warning-line">Reference evidence only: this is not a map of natural distribution.</text>
        </g>

        <g className="shared-card network-card" filter="url(#sharedCardShadow)">
          <rect x="454" y="322" width="592" height="290" rx="16" />
          <text x="482" y="356" className="shared-card-title">Safe LCA network</text>
          <text x="482" y="380" className="shared-muted">The fragment is shared, so the graph moves upward to the common clade.</text>
          {network.genusLinks.map((link) => (
            <line
              key={`${link.genus.id}-safe-link`}
              x1={network.safe.x}
              y1={network.safe.y}
              x2={link.x}
              y2={link.y}
              className={`shared-network-link safe ${selectedItem.type === 'safe' || selectedGroupId === link.genus.id ? 'selected' : ''}`}
            />
          ))}
          {network.speciesLinks.map((link) => (
            <line
              key={`${link.genus.id}-${link.species.id}-species-link`}
              x1={link.from.x}
              y1={link.from.y}
              x2={link.to.x}
              y2={link.to.y}
              className={`shared-network-link ${selectedGroupId === link.genus.id || selectedSpeciesId === link.species.id ? 'selected' : ''}`}
            />
          ))}
          <g
            className={`shared-safe-node shared-click-target ${selectedItem.type === 'safe' ? 'selected' : ''}`}
            transform={`translate(${network.safe.x} ${network.safe.y})`}
            filter="url(#sharedSafeGlow)"
            role="button"
            tabIndex="0"
            aria-label={`Select safe LCA ${safeName}`}
            onClick={() => activateItem(sharedSelectionDetail({ type: 'safe', safeName, safeRank, totalSpecies, groups }))}
            onKeyDown={keyboardSelect(sharedSelectionDetail({ type: 'safe', safeName, safeRank, totalSpecies, groups }))}
          >
            <rect x="-74" y="-30" width="148" height="60" rx="14" />
            <text y="-4" textAnchor="middle">Safe LCA</text>
            <text y="18" textAnchor="middle">{shortenLabel(safeName, 18)}</text>
          </g>
          {network.genusLinks.map((item) => (
            <g
              key={item.genus.id}
              className={`shared-network-genus shared-click-target ${selectedGroupId === item.genus.id ? 'selected' : ''}`}
              transform={`translate(${item.x} ${item.y})`}
              role="button"
              tabIndex="0"
              aria-label={`Select network genus ${item.genus.label}`}
              onClick={() => activateItem(sharedSelectionDetail({ type: 'genus', group: item, safeName, safeRank, totalSpecies }))}
              onKeyDown={keyboardSelect(sharedSelectionDetail({ type: 'genus', group: item, safeName, safeRank, totalSpecies }))}
            >
              <circle r="22" fill={item.color} />
              <text y="5" textAnchor="middle">{shortGenusNodeLabel(item.genus.label)}</text>
            </g>
          ))}
          {network.speciesLinks.map((item) => (
            <g
              key={item.species.id}
              className={`shared-network-species shared-click-target ${selectedSpeciesId === item.species.id ? 'selected' : ''}`}
              transform={`translate(${item.to.x} ${item.to.y})`}
              role="button"
              tabIndex="0"
              aria-label={`Select network species ${item.species.label}`}
              onClick={() => activateItem(sharedSelectionDetail({ type: 'species', group: item, species: item.species, safeName, safeRank, totalSpecies }))}
              onKeyDown={keyboardSelect(sharedSelectionDetail({ type: 'species', group: item, species: item.species, safeName, safeRank, totalSpecies }))}
            >
              <title>{item.species.label}</title>
              <circle r="7" fill={item.color} />
              <text x={item.labelAnchor === 'end' ? -12 : 12} y="4" textAnchor={item.labelAnchor}>
                {shortSpeciesLabel(item.species.label, item.genus.label, item.labelAnchor === 'start' ? 9 : 12)}
              </text>
            </g>
          ))}
        </g>

        <g className="shared-action-strip" transform="translate(454 614)">
          <rect width="592" height="24" rx="8" />
          <text x="14" y="16">{actionLines.join(' ')}</text>
        </g>

        {datasetNode && (
          <text x="226" y="632" className="shared-footer-note">
            Dataset: {shortenLabel(datasetNode.label, 42)}
          </text>
        )}
      </svg>
    </div>
  );
}

function buildSharedFragmentDashboard(graph) {
  const nodes = graph.nodes || [];
  const edges = graph.edges || [];
  const nodeById = Object.fromEntries(nodes.map((node) => [node.id, node]));
  const fragmentNode = nodes.find((node) => node.type === 'fragment');
  const datasetNode = nodes.find((node) => node.type === 'reference_dataset');
  const warningNode = nodes.find((node) => node.type === 'warning');
  const safeLcaNode = nodes.find((node) => node.type === 'safe_lca');
  const genusNodes = nodes.filter((node) => node.type === 'genus');
  const speciesNodes = nodes.filter((node) => node.type === 'species');
  const hitNodes = nodes.filter((node) => node.type === 'reference_hit');
  const genusToSpeciesIds = {};
  const speciesToGenusId = {};

  edges.forEach((edge) => {
    const source = nodeById[edge.source];
    const target = nodeById[edge.target];
    if (edge.type === 'parent_taxon' && source?.type === 'genus' && target?.type === 'species') {
      genusToSpeciesIds[source.id] = genusToSpeciesIds[source.id] || [];
      if (!genusToSpeciesIds[source.id].includes(target.id)) {
        genusToSpeciesIds[source.id].push(target.id);
      }
      speciesToGenusId[target.id] = source.id;
    }
  });

  const groups = genusNodes
    .map((genus, index) => ({
      genus,
      species: (genusToSpeciesIds[genus.id] || []).map((id) => nodeById[id]).filter(Boolean),
      color: sharedGenusColor(genus.label, index),
    }))
    .filter((group) => group.species.length > 0)
    .sort((first, second) => first.genus.label.localeCompare(second.genus.label));

  const ungroupedSpecies = speciesNodes.filter((species) => !speciesToGenusId[species.id]);
  if (ungroupedSpecies.length) {
    groups.push({
      genus: { id: 'genus:unresolved', type: 'genus', label: 'Unresolved genus', rank: 'genus' },
      species: ungroupedSpecies,
      color: '#7a6da8',
    });
  }

  return {
    fragmentNode,
    datasetNode,
    warningNode,
    safeLcaNode,
    groups,
    totalSpecies: groups.reduce((sum, group) => sum + group.species.length, 0),
    totalHits: graph.classification?.informative_hits || hitNodes.length,
  };
}

function buildSharedNetworkLayout(groups, safeName) {
  const safe = { x: 720, y: 482, label: safeName };
  const preferredPositions = {
    Aedes: { x: 622, y: 424, side: 'left' },
    Anopheles: { x: 622, y: 548, side: 'left' },
    Culex: { x: 858, y: 486, side: 'right' },
  };
  const genusLinks = groups.map((group, index) => {
    const preferred = preferredPositions[group.genus.label];
    if (preferred) {
      return { ...group, ...preferred };
    }
    const angle = -140 + index * (280 / Math.max(1, groups.length - 1));
    const radians = (angle * Math.PI) / 180;
    return {
      ...group,
      x: safe.x + Math.cos(radians) * 170,
      y: safe.y + Math.sin(radians) * 98,
      side: Math.cos(radians) < 0 ? 'left' : 'right',
    };
  });
  const speciesLinks = genusLinks.flatMap((group) => {
    const spread = Math.min(34, 92 / Math.max(1, group.species.length - 1 || 1));
    const leafX = group.side === 'left' ? group.x - 92 : group.x + 86;
    return group.species.map((species, speciesIndex) => {
      const offset = (speciesIndex - (group.species.length - 1) / 2) * spread;
      return {
        genus: group.genus,
        species,
        color: group.color,
        from: { x: group.x, y: group.y },
        to: { x: leafX, y: group.y + offset },
        labelAnchor: group.side === 'left' ? 'end' : 'start',
      };
    });
  });
  return { safe, genusLinks, speciesLinks };
}

function sharedGenusColor(label, index) {
  const colors = {
    Aedes: '#2f8a5f',
    Anopheles: '#5b72b7',
    Culex: '#d18a2d',
    Quercus: '#527d3b',
  };
  const fallback = ['#2f8a5f', '#5b72b7', '#d18a2d', '#7a6da8', '#3e8aa5'];
  return colors[label] || fallback[index % fallback.length];
}

function shortGenusNodeLabel(label) {
  const text = String(label || '');
  return text.length > 6 ? `${text.slice(0, 5)}.` : text;
}

function sharedSelectionDetail({ type, group, species, safeName, safeRank, totalSpecies, groups }) {
  if (type === 'species' && species) {
    const genusName = group?.genus?.label || group?.label || 'the genus';
    return {
      type,
      groupId: group?.genus?.id || group?.id,
      speciesId: species.id,
      title: species.label,
      description: `This reference species contains the fragment, but the same short fragment is also found in other taxa. It contributes evidence to the shared ${safeRank}, not a standalone species claim.`,
      action: `Use ${safeName} as the safe claim unless a longer or more diagnostic marker separates ${genusName} species.`,
    };
  }
  if (type === 'genus' && group) {
    return {
      type,
      groupId: group.genus?.id || group.id,
      title: `${group.genus?.label || group.label}: ${group.species?.length || 0} matched species`,
      description: `Several species in this genus share the fragment. That tells us the fragment is biologically useful as shared evidence, but not precise enough to choose one species.`,
      action: `Compare this genus with the other ${Math.max(0, (groups?.length || 0) - 1)} genera; the safe claim stays at ${safeRank} ${safeName}.`,
    };
  }
  return {
    type: 'safe',
    groupId: null,
    speciesId: null,
    title: `Safe LCA: ${safeName}`,
    description: `All informative hits meet at this lowest common ancestor. Because ${totalSpecies} species share the fragment, the tool blocks a species-level claim and raises the safe taxon.`,
    action: `Click any point, genus or species node to inspect why the fragment remains ${safeRank}-level evidence.`,
  };
}

function wrapSvgText(text, maxLength) {
  const words = String(text || '').split(/\s+/).filter(Boolean);
  const lines = [];
  let current = '';
  words.forEach((word) => {
    const next = current ? `${current} ${word}` : word;
    if (next.length > maxLength && current) {
      lines.push(current);
      current = word;
    } else {
      current = next;
    }
  });
  if (current) lines.push(current);
  return lines;
}

function shortSpeciesLabel(label, genus, limit = 12) {
  const text = String(label || '');
  const genusText = String(genus || '');
  const withoutGenus = genusText && text.startsWith(`${genusText} `)
    ? text.slice(genusText.length + 1)
    : text;
  return shortenLabel(withoutGenus, limit);
}

function fragmentPreview(sequence) {
  const clean = String(sequence || '').replace(/[^ACGTURYKMSWBDHVN]/gi, '').toUpperCase();
  if (!clean) return 'ACGTTGACCTAGGCTTACGATCGTACCGATGC';
  return clean.length > 34 ? `${clean.slice(0, 34)}...` : clean;
}

function GraphNode({ node, x, y }) {
  const width = node.type === 'fragment' ? 178 : node.type === 'safe_lca' ? 194 : node.type === 'reference_hit' ? 164 : node.type === 'warning' ? 168 : node.type === 'reference_dataset' ? 154 : 132;
  const height = node.type === 'fragment' ? 72 : node.type === 'safe_lca' ? 58 : node.type === 'reference_hit' ? 56 : node.type === 'warning' ? 50 : 44;
  const safeClass = node.is_safe_taxon ? ' safe-taxon-node' : '';
  const label = node.type === 'safe_lca' ? 'Safe LCA' : shortenLabel(node.label, node.type === 'reference_hit' ? 23 : 20);
  const detail = node.type === 'reference_hit'
    ? `${formatPercent(node.identity)} id · ${formatPercent(node.coverage)} cov`
    : node.type === 'safe_lca'
      ? `${shortenLabel(node.name || node.label, 24)} · ${node.rank || 'rank'}`
      : node.type === 'fragment'
      ? `${node.sequence_length || '-'} bp marker fragment`
      : node.marker || node.rank || node.status || '';
  const title = `${node.label}${detail ? ` · ${detail}` : ''}`;

  return (
    <g className={`graph-node ${safeClassName(node.type)}${safeClass}`} transform={`translate(${x - width / 2}, ${y - height / 2})`} filter={node.type === 'safe_lca' || node.is_safe_taxon ? 'url(#safeGlow)' : undefined}>
      <title>{title}</title>
      <rect width={width} height={height} rx="8" />
      {node.type === 'fragment' && (
        <g className="graph-dna-strip" transform={`translate(${width / 2 - 54}, 12)`}>
          {['A', 'C', 'G', 'T', 'T', 'G'].map((base, index) => (
            <text key={`${base}-${index}`} x={index * 18} y="0">{base}</text>
          ))}
        </g>
      )}
      <text x={width / 2} y={node.type === 'fragment' ? 42 : height / 2 - (detail ? 2 : -4)} textAnchor="middle" className="graph-node-label">{label}</text>
      {detail && <text x={width / 2} y={height - 10} textAnchor="middle" className="graph-node-detail">{detail}</text>}
    </g>
  );
}

function GraphLegend() {
  const items = [
    ['fragment', 'query'],
    ['reference_hit', 'hit'],
    ['genus', 'taxon'],
    ['safe_lca', 'safe LCA'],
    ['warning', 'warning'],
  ];
  return (
    <g className="graph-legend" transform="translate(42 592)">
      {items.map(([type, label], index) => (
        <g key={type} transform={`translate(${index * 116} 0)`}>
          <rect width="18" height="18" rx="5" className={safeClassName(type)} />
          <text x="25" y="14">{label}</text>
        </g>
      ))}
    </g>
  );
}

function curvedEdgePath(source, target, type) {
  const dx = target.x - source.x;
  const dy = target.y - source.y;
  const curve = type === 'parent_taxon' ? 0.34 : type === 'safe_lca_of' ? 0.52 : 0.44;
  const c1 = { x: source.x + dx * curve, y: source.y + dy * 0.08 };
  const c2 = { x: target.x - dx * curve, y: target.y - dy * 0.08 };
  return `M ${source.x} ${source.y} C ${c1.x} ${c1.y}, ${c2.x} ${c2.y}, ${target.x} ${target.y}`;
}

function formatPercent(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return '-';
  return `${number.toFixed(number >= 99.95 ? 0 : 1)}%`;
}

function fragmentStatusTitle(status) {
  const titles = {
    'not-run': 'Not run yet',
    'species-diagnostic': 'Species-diagnostic in this dataset',
    'genus-shared': 'Shared within a genus',
    'higher-rank-shared': 'Shared above genus',
    'cross-kingdom-conserved': 'Cross-kingdom / conserved signal',
    weak: 'Weak fragment evidence',
    'no-match': 'No match in selected dataset',
  };
  return titles[status] || status;
}

function fragmentStatusExplanation(status) {
  const explanations = {
    'not-run': 'Run a fragment search to see whether the marker is specific or shared.',
    'species-diagnostic': 'All informative hits resolve to the same species. This supports a species-level candidate only within the selected reference dataset.',
    'genus-shared': 'Informative hits span multiple species but share one genus. Species claims are blocked; genus-level evidence is safer.',
    'higher-rank-shared': 'The fragment is shared above genus, so it should be treated as clade-level context, not as a species identifier.',
    'cross-kingdom-conserved': 'Informative hits span more than one kingdom. Treat this as conserved, contaminated or too generic until reviewed.',
    weak: 'Hits exist, but identity or coverage is below the informative threshold.',
    'no-match': 'The selected reference dataset did not return hits for this fragment.',
  };
  return explanations[status] || 'Classification is bounded by the selected reference dataset.';
}

function safeClaimForStatus(status, safeTaxon) {
  if (status === 'species-diagnostic') {
    return `${safeTaxon?.name || 'The species'} can be used as a species-level candidate within this selected reference evidence.`;
  }
  if (status === 'genus-shared') {
    return `Use ${safeTaxon?.name || 'the shared genus'} as the safe taxonomic level; do not name one species from this fragment alone.`;
  }
  if (status === 'higher-rank-shared') {
    return `Use only the shared ${safeTaxon?.rank || 'higher rank'} context: ${safeTaxon?.name || 'the LCA'}.`;
  }
  if (status === 'cross-kingdom-conserved') {
    return 'Use this as a warning signal only; it is not taxonomically diagnostic inside this reference set.';
  }
  if (status === 'weak') {
    return 'No safe taxonomic claim. Improve fragment length, reference set or sequence quality.';
  }
  if (status === 'no-match') {
    return 'No claim from this selected reference dataset.';
  }
  return 'Run the graph first.';
}

function safeClassName(value) {
  return String(value || 'unknown').replace(/[^a-zA-Z0-9_-]+/g, '-');
}

function shortenLabel(value, limit) {
  const text = String(value || '');
  return text.length > limit ? `${text.slice(0, Math.max(0, limit - 1))}…` : text;
}

function EvidenceProcessFlow({ activeIndex = 0, compact = false }) {
  return (
    <div className={`process-flow ${compact ? 'compact' : ''}`} aria-label="Evidence compiler workflow">
      {userJourneySteps.map(([number, title, text], index) => (
        <article key={number} className={`process-step ${index <= activeIndex ? 'active' : ''}`}>
          <span>{number}</span>
          <div>
            <strong>{title}</strong>
            {!compact && <p>{text}</p>}
          </div>
        </article>
      ))}
    </div>
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
  runCsvCompiler,
  previewCsvUpload,
  loading,
  csvLoading,
  csvFile,
  csvImport,
  searchStatus,
  referenceDatasets,
  searchSequence,
  setSearchSequence,
  selectedReferenceDataset,
  setSelectedReferenceDataset,
  searchResult,
  searchLoading,
  runReferenceSearch,
  referenceUploadFile,
  setReferenceUploadFile,
  referenceUploadTitle,
  setReferenceUploadTitle,
  referenceUploadMarker,
  setReferenceUploadMarker,
  referenceUpload,
  referenceUploadLoading,
  uploadReferenceDataset,
  referenceStatus,
  pack,
  records,
  exports,
}) {
  const [decisionFilter, setDecisionFilter] = useState('all');
  const publishableRecords = records.filter((record) => record.published_taxon?.rank && record.published_taxon.rank !== 'none');
  const reviewRecords = records.filter((record) => !record.published_taxon?.rank || record.published_taxon.rank === 'none');
  const blockedRecords = records.filter((record) => record.blockers?.length || ['weak', 'ambiguous', 'not-publishable', 'no-match'].includes(record.decision_class));
  const filteredRecords = filterDecisionRecords(records, decisionFilter);
  const csvValidation = csvImport?.validation;
  const csvHasFatalErrors = csvValidation && !csvValidation.ok;
  const keyExports = ['evidence_pack.zip', 'molecular_evidence_report.html', 'sequence_safety_table.csv', 'methods_text.md', 'citations.md', 'hard_gate_audit.csv', 'marker_profile_audit.csv', 'assay_gate_audit.csv', 'repair_plan.csv', 'naive_top_hit_overclaims.csv', 'theorem_checklist.json', 'verified_segment_evidence_array.parquet', 'graph_provenance_audit.csv']
    .map((name) => exports.find((item) => item.name === name))
    .filter(Boolean);
  const selectedReferenceDatasetMeta = referenceDatasets.find((dataset) => dataset.id === selectedReferenceDataset);
  const referenceExamples = referenceDatasets.flatMap((dataset) => (
    (dataset.example_queries || []).map((example) => ({ dataset, example }))
  ));

  return (
    <section className={`workspace ${pack ? 'has-results' : ''}`}>
      <aside className="control-panel">
        <section className="quick-start-card">
          <p className="section-label">Start here</p>
          <h3>Use the demo first, then upload your CSV.</h3>
          <p>
            The fastest way to understand the tool is to run the mixed demo. It shows one species-safe record,
            one downgraded record, one weak record and one metadata-blocked record.
          </p>
          <div className="quick-start-actions">
            <button className="primary" onClick={runCompiler} disabled={loading}>
              {loading ? 'Running demo...' : 'Try mixed demo'}
            </button>
            <a className="button-link" href={barcodeCsvTemplateUrl()}>Get CSV template</a>
          </div>
        </section>

        <p className="section-label">Upload and score</p>
        <section
          className={`upload-card ${csvFile ? 'has-file' : ''}`}
          onDragOver={(event) => event.preventDefault()}
          onDrop={(event) => {
            event.preventDefault();
            previewCsvUpload(event.dataTransfer.files?.[0]);
          }}
        >
          <div>
            <h3>Upload CSV results</h3>
            <div className="upload-example-list">
              {uploadExamples.map(([label, text]) => (
                <div key={label}>
                  <strong>{label}</strong>
                  <span>{text}</span>
                </div>
              ))}
            </div>
            <p>
              Required columns: <strong>sequenceID</strong> and <strong>sequence</strong>. Match metrics unlock safe taxonomic decisions.
            </p>
          </div>
          <label className="file-picker">
            CSV file
            <input
              aria-label="CSV file"
              type="file"
              accept=".csv,text/csv"
              onChange={(event) => previewCsvUpload(event.target.files?.[0])}
            />
          </label>
          <div className="upload-actions">
            <a className="button-link" href={barcodeCsvTemplateUrl()}>Download CSV template</a>
            <button className="primary" onClick={runCsvCompiler} disabled={!csvFile || csvHasFatalErrors || loading || csvLoading}>
              {loading ? 'Generating...' : 'Generate from CSV'}
            </button>
          </div>
          <p className="hint">
            Not enough: FASTA-only without Sequence ID/BLAST-style hit results cannot produce species-safe claims.
          </p>
        </section>

        {csvFile && (
          <section className="validation-card">
            <p className="section-label">Validation</p>
            <h3>{csvLoading ? 'Reading CSV...' : csvValidation?.ok ? 'CSV ready to run' : 'CSV needs repair'}</h3>
            <div className="validation-grid">
              <Metric label="Rows" value={csvValidation?.records_found ?? '-'} />
              <Metric label="Invalid DNA" value={csvValidation?.invalid_sequence_count ?? '-'} />
              <Metric label="Weak/no-hit" value={csvValidation?.weak_or_no_hit_count ?? '-'} />
              <Metric label="Missing columns" value={csvValidation?.missing_required_columns?.length ?? '-'} />
            </div>
            {csvValidation?.errors?.length > 0 && (
              <ul className="plain-list blocked">
                {csvValidation.errors.map((item) => <li key={item}>{item}</li>)}
              </ul>
            )}
            {csvValidation?.warnings?.length > 0 && (
              <ul className="plain-list">
                {csvValidation.warnings.map((item) => <li key={item}>{item}</li>)}
              </ul>
            )}
          </section>
        )}

        {csvImport?.preview_rows?.length > 0 && (
          <details className="advanced-input" open>
            <summary>CSV preview</summary>
            <CsvPreview rows={csvImport.preview_rows} />
          </details>
        )}

        <section className="reference-search-card">
          <p className="section-label">Reference search</p>
          <h3>Search a real reference dataset</h3>
          <p>
            Paste a barcode sequence and run VSEARCH/BLAST+ when available. Local mode falls back to deterministic mini-search for these small bundled examples.
          </p>
          {referenceExamples.length > 0 && (
            <div className="reference-example-grid" aria-label="Real reference examples">
              {referenceExamples.map(({ dataset, example }) => (
                <article key={`${dataset.id}-${example.id}`} className="reference-example-card">
                  <div>
                    <strong>{example.label}</strong>
                    <span>{dataset.marker} · expected {example.expected_decision}</span>
                    <p>{example.explanation}</p>
                  </div>
                  <button
                    className="secondary"
                    type="button"
                    onClick={() => runReferenceSearch({
                      reference_dataset: dataset.id,
                      sequence: example.sequence,
                      sequence_id: example.sequence_id || example.id,
                    })}
                    disabled={searchLoading}
                  >
                    {searchLoading ? 'Running...' : 'Run real data'}
                  </button>
                </article>
              ))}
            </div>
          )}
          <div className="reference-upload-panel">
            <div>
              <strong>Bring your own reference FASTA</strong>
              <p>
                Upload a small curated FASTA to test real project data. Header format:
                <code>{' >ref_id|Taxon name|rank|gbifTaxonKey'}</code>
              </p>
            </div>
            <label>
              Dataset title
              <input
                type="text"
                value={referenceUploadTitle}
                placeholder="My COI reference set"
                onChange={(event) => setReferenceUploadTitle(event.target.value)}
              />
            </label>
            <label>
              Marker
              <input
                type="text"
                value={referenceUploadMarker}
                onChange={(event) => setReferenceUploadMarker(event.target.value)}
              />
            </label>
            <label className="file-picker">
              Reference FASTA
              <input
                aria-label="Reference FASTA"
                type="file"
                accept=".fasta,.fa,.fas,text/plain"
                onChange={(event) => setReferenceUploadFile(event.target.files?.[0] || null)}
              />
            </label>
            <button className="secondary wide" onClick={uploadReferenceDataset} disabled={!referenceUploadFile || referenceUploadLoading}>
              {referenceUploadLoading ? 'Uploading reference...' : 'Upload reference FASTA'}
            </button>
            {referenceUpload?.dataset && (
              <p className="upload-success">
                Uploaded <strong>{referenceUpload.dataset.title}</strong> · {referenceUpload.dataset.records} records · selected for search.
              </p>
            )}
          </div>
          <label>
            Reference dataset
            <select value={selectedReferenceDataset} onChange={(event) => setSelectedReferenceDataset(event.target.value)}>
              {referenceDatasets.length ? referenceDatasets.map((dataset) => (
                <option key={dataset.id} value={dataset.id}>
                  {dataset.title}{dataset.source_type === 'uploaded' ? ' · uploaded' : ''}
                </option>
              )) : (
                <option value="aedes_coi_mini">EcoGenesis mini COI reference dataset</option>
              )}
            </select>
          </label>
          {selectedReferenceDatasetMeta && (
            <div className="reference-dataset-note">
              <strong>{selectedReferenceDatasetMeta.source_type === 'uploaded' ? 'Uploaded reference' : 'Bundled reference'}</strong>
              <span>{selectedReferenceDatasetMeta.records} records · {selectedReferenceDatasetMeta.marker || 'marker not declared'}</span>
              {selectedReferenceDatasetMeta.usage_scope && <p>{selectedReferenceDatasetMeta.usage_scope}</p>}
              {selectedReferenceDatasetMeta.gbif_backbone_enrichment && (
                <small>
                  GBIF backbone: {selectedReferenceDatasetMeta.gbif_backbone_enrichment.status}
                  {' · '}
                  enriched {selectedReferenceDatasetMeta.gbif_backbone_enrichment.enriched_records ?? 0}
                  {' / fallback '}
                  {selectedReferenceDatasetMeta.gbif_backbone_enrichment.fallback_records ?? 0}
                </small>
              )}
            </div>
          )}
          <label>
            Query sequence
            <textarea
              className="compact-textarea"
              value={searchSequence}
              onChange={(event) => setSearchSequence(event.target.value)}
              spellCheck="false"
            />
          </label>
          <button className="primary wide" onClick={() => runReferenceSearch()} disabled={searchLoading || !searchSequence.trim()}>
            {searchLoading ? 'Searching reference...' : 'Search reference & compile'}
          </button>
          <div className="search-backend-status">
            <span>Backend</span>
            <strong>{searchResult?.backend_used || searchStatus?.preferred_backend || 'loading'}</strong>
            <small>{searchStatus?.message || 'Checking external search backend...'}</small>
          </div>
          {searchResult?.hits?.length > 0 && (
            <ol className="ranked-list compact-list">
              {searchResult.hits.slice(0, 3).map((hit) => (
                <li key={hit.reference_id}>
                  <strong>{hit.taxon}</strong>
                  <span>{hit.identity}% identity · {hit.query_coverage}% coverage · {hit.reference_id}</span>
                </li>
              ))}
            </ol>
          )}
        </section>

        <section className="source-note">
          <p className="section-label">Data source</p>
          <strong>{referenceStatus?.status === 'ready' ? 'Compiler ready' : 'Compiler status'}</strong>
          <span>
            Molecular scoring uses supplied Sequence ID / BLAST / BOLD / UNITE-style CSV rows or the selected FASTA reference dataset. GBIF occurrence audit is available in Research audit, but it is not used as hidden molecular evidence.
          </span>
        </section>

        <p className="section-label">Demo fallback</p>
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
          {loading ? 'Compiling evidence...' : 'Run selected demo'}
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
          <>
            <section className="empty-state onboarding-state">
              <p className="section-label">What happens after you click run</p>
              <h2>From a DNA match table to safe claims and repair actions.</h2>
              <p>
                EcoGenesis does not guess a species from the top hit. It checks whether the evidence is strong enough,
                downgrades unsafe claims, separates publication blockers, then builds a downloadable evidence pack.
              </p>
              <EvidenceProcessFlow activeIndex={loading ? 1 : 0} />
              <div className="empty-state-actions">
                <button className="primary" onClick={runCompiler} disabled={loading}>
                  {loading ? 'Compiling evidence...' : 'Run the mixed demo'}
                </button>
                <a className="button-link" href={barcodeCsvTemplateUrl()}>Get CSV template</a>
              </div>
            </section>

            <section className="panel">
              <p className="section-label">How to read the result</p>
              <div className="status-guide-grid">
                {resultReadingGuide.map(([status, meaning]) => (
                  <article key={status} className={`status-guide-card ${status}`}>
                    <span>{status}</span>
                    <p>{meaning}</p>
                  </article>
                ))}
              </div>
            </section>
          </>
        ) : (
          <>
            <section className="panel">
              <p className="section-label">Decision memo</p>
              <h2>{pack.summary.verdict}</h2>
              <p className="decision-lead">{buildRunExplanation(pack.metrics, publishableRecords.length, reviewRecords.length)}</p>
              <EvidenceProcessFlow activeIndex={4} compact />
              <div className="metrics-grid compact">
                <Metric label="Processed" value={pack.metrics.processed_records} />
                <Metric label="Species-safe" value={pack.metrics.species_safe_records} />
                <Metric label="Genus-safe" value={pack.metrics.genus_safe_records} />
                <Metric label="Record-ready" value={pack.metrics.record_ready_records} />
              </div>
            </section>

            <NexusAuditPanel pack={pack} />

            <ClaimBoundaryPanel records={records} pack={pack} />

            <DataAccountingLedgerPanel pack={pack} />

            <MarkerAssayPanel pack={pack} records={records} />

            <BenchmarkComparisonPanel pack={pack} records={records} />

            <OutcomeSummary records={records} />

            {keyExports.length > 0 && (
              <section className="panel">
                <p className="section-label">Download outputs</p>
                <div className="quick-downloads">
                  {keyExports.map((item) => (
                    <a key={item.name} className="button-link" href={exportUrl(item.url)}>{item.name}</a>
                  ))}
                </div>
              </section>
            )}

            <section className="panel two-column">
              <div>
                <p className="section-label">Publishable output</p>
                <h3>{publishableRecords.length} {pluralize('record', publishableRecords.length)} can enter publishable templates</h3>
                <p className="hint">
                  These records have a `published_taxon` and are included in publishable Darwin Core and DNA-derived review templates. Formal GBIF-ready rows are tracked separately.
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
              <div className="filter-tabs" aria-label="Sequence decision filters">
                {[
                  ['all', `All (${records.length})`],
                  ['publishable', `Publishable (${publishableRecords.length})`],
                  ['review', `Review (${reviewRecords.length})`],
                  ['blocked', `Blocked (${blockedRecords.length})`],
                ].map(([id, label]) => (
                  <button key={id} className={decisionFilter === id ? 'active' : ''} onClick={() => setDecisionFilter(id)}>
                    {label}
                  </button>
                ))}
              </div>
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
                    {filteredRecords.map((record) => (
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

function CsvPreview({ rows }) {
  const columns = ['sequenceID', 'scientificName', 'eventDate', 'marker', 'assayType', 'topTaxon', 'topIdentity', 'topCoverage'];
  return (
    <div className="csv-preview">
      <table>
        <thead>
          <tr>
            {columns.map((column) => <th key={column}>{column}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={`${row.sequenceID || 'row'}-${index}`}>
              {columns.map((column) => <td key={column}>{row[column] || '-'}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function MarkerAssayPanel({ pack, records }) {
  const profileCounts = records.reduce((acc, record) => {
    const profile = record.metadata_readiness?.marker_profile?.profile_id || 'unknown';
    acc[profile] = (acc[profile] || 0) + 1;
    return acc;
  }, {});
  const assayCounts = records.reduce((acc, record) => {
    const assay = record.metadata_readiness?.assay_gate?.assay_type || 'unknown';
    acc[assay] = (acc[assay] || 0) + 1;
    return acc;
  }, {});
  const dnaReady = pack.metrics?.dna_extension_ready_records ?? records.filter((record) => record.metadata_readiness?.dna_extension_high_priority_pass).length;
  const assayFailures = pack.metrics?.assay_gate_failures ?? records.filter((record) => record.metadata_readiness?.assay_gate?.assay_gate_pass === false).length;
  const speciesDisabled = pack.metrics?.marker_species_disabled_records ?? records.filter((record) => record.metadata_readiness?.marker_profile?.species_claim_allowed === false).length;
  const rows = records.slice(0, 6);

  return (
    <section className="panel profile-assay-panel">
      <div className="panel-heading-row">
        <div>
          <p className="section-label">Marker and assay gates</p>
          <h3>Profiles make the compiler less naive.</h3>
        </div>
        <span className={`audit-status ${assayFailures === 0 ? 'pass' : 'warn'}`}>
          {assayFailures === 0 ? 'assay gates ok' : `${assayFailures} assay gate warning`}
        </span>
      </div>
      <div className="nexus-kpi-grid">
        <Metric label="Marker profiles" value={Object.keys(profileCounts).length} detail={Object.entries(profileCounts).map(([key, value]) => `${key}: ${value}`).join(' · ')} />
        <Metric label="Assay types" value={Object.keys(assayCounts).length} detail={Object.entries(assayCounts).map(([key, value]) => `${key}: ${value}`).join(' · ')} />
        <Metric label="DNA extension ready" value={dnaReady} detail="records with all high-priority DNA-derived fields" />
        <Metric label="Species disabled" value={speciesDisabled} detail="marker profile forced safe-rank review" />
      </div>
      <div className="table-wrap compact-table">
        <table>
          <thead>
            <tr>
              <th>Sequence</th>
              <th>Marker profile</th>
              <th>Assay</th>
              <th>DNA extension gaps</th>
              <th>Caveat</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((record) => {
              const marker = record.metadata_readiness?.marker_profile || {};
              const assay = record.metadata_readiness?.assay_gate || {};
              const dnaGaps = record.metadata_readiness?.dna_extension_high_priority_missing || [];
              return (
                <tr key={record.sequence_id}>
                  <td>{record.sequence_id}</td>
                  <td>{marker.profile_id || 'unknown'} · {marker.species_gate_pass ? 'species gate pass' : 'safe-rank only'}</td>
                  <td>{assay.assay_type || 'unknown'} · {assay.assay_gate_pass ? 'pass' : 'review'}</td>
                  <td>{dnaGaps.length ? dnaGaps.slice(0, 4).join(', ') : 'none'}</td>
                  <td>{marker.claim_caveat || assay.claim_caveat || 'Review claim boundaries before publication.'}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function filterDecisionRecords(records, filter) {
  if (filter === 'publishable') {
    return records.filter((record) => record.published_taxon?.rank && record.published_taxon.rank !== 'none');
  }
  if (filter === 'review') {
    return records.filter((record) => !record.published_taxon?.rank || record.published_taxon.rank === 'none');
  }
  if (filter === 'blocked') {
    return records.filter((record) => record.blockers?.length || ['weak', 'ambiguous', 'not-publishable', 'no-match'].includes(record.decision_class));
  }
  return records;
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

function NexusAuditPanel({ pack }) {
  const metrics = pack.metrics || {};
  const conversion = pack.nexus_v3?.conversion_metrics || {};
  const audit = pack.nexus_v3?.audit || {};
  const repairPlan = pack.repair_plan || [];
  const overclaims = pack.naive_top_hit_overclaims || [];
  const hardGateFailures = metrics.hard_gate_failures ?? audit.hard_gate_failures ?? 0;
  const cards = [
    ['MECY', conversion.MECY_molecular_evidence_conversion_yield ?? metrics.molecular_evidence_conversion_yield ?? 0, 'records entering publishable templates'],
    ['SRY', conversion.SRY_safe_rank_yield ?? metrics.safe_rank_yield ?? 0, 'records useful at species/genus/higher rank'],
    ['OPR', conversion.OPR_overclaim_prevention_rate ?? metrics.overclaim_prevention_rate ?? 0, 'top-hit species overclaims blocked'],
    ['Hard gates', hardGateFailures, hardGateFailures === 0 ? 'no species-safe inconsistency' : 'review before publication'],
  ];

  return (
    <section className="panel nexus-audit-panel">
      <div className="panel-heading-row">
        <div>
          <p className="section-label">Nexus V3 audit</p>
          <h3>Molecular evidence conversion, not species guessing.</h3>
        </div>
        <span className={`audit-status ${hardGateFailures === 0 ? 'pass' : 'warn'}`}>
          {hardGateFailures === 0 ? 'Hard gates passed' : 'Hard-gate warning'}
        </span>
      </div>
      <div className="nexus-kpi-grid">
        {cards.map(([label, value, detail]) => (
          <Metric key={label} label={label} value={value} detail={detail} />
        ))}
      </div>
      <div className="two-column nexus-mini">
        <div>
          <p className="section-label">Top repair priorities</p>
          {repairPlan.length ? (
            <ol className="ranked-list">
              {repairPlan.slice(0, 4).map((item) => (
                <li key={item.repairAction}>
                  <strong>{item.repairAction}</strong>
                  <span>{item.unlockableRecords} {pluralize('record', item.unlockableRecords)} · {item.estimatedCost} cost</span>
                </li>
              ))}
            </ol>
          ) : (
            <p className="hint">No repair action is required in this run.</p>
          )}
        </div>
        <div>
          <p className="section-label">Overclaim prevention</p>
          {overclaims.length ? (
            <ol className="ranked-list blocked">
              {overclaims.slice(0, 4).map((item) => (
                <li key={item.sequenceID}>
                  <strong>{item.sequenceID}</strong>
                  <span>{item.naiveClaim} → {item.compilerDecision}; safe rank: {item.safeRank}</span>
                </li>
              ))}
            </ol>
          ) : (
            <p className="hint">No unsafe top-hit species claims were detected in this run.</p>
          )}
        </div>
      </div>
    </section>
  );
}

function ClaimBoundaryPanel({ records, pack }) {
  const buckets = records.reduce((acc, record) => {
    const bucket = record.publication_bucket || 'review_only';
    acc[bucket] = (acc[bucket] || 0) + 1;
    return acc;
  }, {});
  const examples = records.slice(0, 4);
  return (
    <section className="panel claim-boundary-panel">
      <div className="panel-heading-row">
        <div>
          <p className="section-label">Claim boundary</p>
          <h3>What can be claimed, what is blocked, and what remains repair work.</h3>
        </div>
        <span className="audit-status pass">bounded evidence</span>
      </div>
      <div className="nexus-kpi-grid">
        <Metric label="GBIF-ready" value={buckets.gbif_ready || 0} detail="dataset-level ready rows" />
        <Metric label="Candidates" value={buckets.publishable_candidate || 0} detail="safe rows needing dataset review" />
        <Metric label="Repair required" value={buckets.repair_required || 0} detail="blocked before publication" />
        <Metric label="Review only" value={buckets.review_only || 0} detail="not exportable as occurrence rows" />
      </div>
      <div className="claim-boundary-grid">
        {examples.map((record) => {
          const boundary = record.claim_boundary || {};
          return (
            <article key={record.sequence_id} className={claimBoundaryTone(record)}>
              <strong>{record.sequence_id} · {record.publication_bucket || 'review_only'}</strong>
              <span>{boundary.supported || decisionCopy[record.decision_class]?.body || record.decision_class}</span>
              <span>{boundary.publication || formatStage(record.publication_stage)}</span>
              {boundary.not_supported?.length > 0 && (
                <small>Not supported: {boundary.not_supported.slice(0, 2).join('; ')}</small>
              )}
            </article>
          );
        })}
      </div>
      {pack.source_provenance && (
        <div className="source-provenance-card">
          <strong>Source provenance</strong>
          <span>{pack.source_provenance.input_contract}</span>
          <small>
            Reference: {pack.source_provenance.reference_database || 'not supplied'}
            {' · '}
            backends: {(pack.source_provenance.reference_search_backends || []).join(', ') || 'supplied hit table'}
          </small>
        </div>
      )}
    </section>
  );
}

function DataAccountingLedgerPanel({ pack }) {
  const ledger = pack.data_accounting_ledger || [];
  if (!ledger.length) return null;
  const visibleRows = ledger.filter((row) => [
    'input_n',
    'candidate_n',
    'safe_n',
    'publishable_candidate_n',
    'gbif_ready_n',
    'repair_required_n',
    'blocked_top_species_claims_n',
    'hard_gate_failures_n',
  ].includes(row.metric));
  return (
    <section className="panel data-ledger-panel">
      <div className="panel-heading-row">
        <div>
          <p className="section-label">Data accounting ledger</p>
          <h3>Every contest KPI keeps its denominator visible.</h3>
        </div>
        <span className="audit-status pass">denominators shown</span>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Metric</th>
              <th>Value</th>
              <th>Denominator</th>
              <th>Rate</th>
              <th>Meaning</th>
            </tr>
          </thead>
          <tbody>
            {visibleRows.map((row) => (
              <tr key={row.metric}>
                <td>{row.metric}</td>
                <td>{row.value}</td>
                <td>{row.denominator}</td>
                <td>{row.rate ?? '-'}</td>
                <td>{row.meaning}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function claimBoundaryTone(record) {
  if (record.publication_bucket === 'gbif_ready' || record.publication_bucket === 'publishable_candidate') {
    return 'safe';
  }
  if (record.publication_bucket === 'repair_required') {
    return 'repair';
  }
  return 'blocked';
}

function BenchmarkComparisonPanel({ pack, records }) {
  const metrics = pack.metrics || {};
  const topSpecies = metrics.top_species_hits ?? records.filter((record) => record.top_hit?.rank === 'species').length;
  const ecoSpecies = metrics.species_safe_records ?? records.filter((record) => record.decision_class === 'species-safe').length;
  const blocked = metrics.blocked_or_downgraded_top_species_hits ?? metrics.blocked_species_claims ?? 0;
  const safeRank = metrics.safe_rank_records ?? records.filter((record) => ['species-safe', 'genus-safe', 'higher-rank-safe'].includes(record.decision_class)).length;
  const publishable = metrics.publishable_template_records ?? records.filter((record) => record.published_taxon?.rank && record.published_taxon.rank !== 'none').length;
  const maxValue = Math.max(topSpecies, ecoSpecies, blocked, safeRank, publishable, 1);
  const rows = [
    ['Naive top-hit species claims', topSpecies, 'Would publish every species-ranked top hit.', 'risk'],
    ['Unsafe claims blocked/downgraded', blocked, 'EcoGenesis prevents species overclaiming.', 'warn'],
    ['EcoGenesis species-safe', ecoSpecies, 'Species claims that passed all hard gates.', 'pass'],
    ['Safe-rank evidence', safeRank, 'Records still useful at species/genus/higher rank.', 'pass'],
    ['Publishable templates', publishable, 'Records emitted into publishable review templates; formal GBIF-ready is separate.', 'verify'],
  ];

  return (
    <section className="panel benchmark-panel">
      <div className="panel-heading-row">
        <div>
          <p className="section-label">Naive vs EcoGenesis</p>
          <h3>What the tool actually solved in this run.</h3>
        </div>
        <span className="audit-status pass">fail-closed comparison</span>
      </div>
      <div className="comparison-bars">
        {rows.map(([label, value, detail, tone]) => (
          <div className="comparison-row" key={label}>
            <div>
              <strong>{label}</strong>
              <span>{detail}</span>
            </div>
            <div className="bar-track" aria-label={`${label}: ${value}`}>
              <span className={`bar-fill ${tone}`} style={{ width: `${Math.max(4, (value / maxValue) * 100)}%` }} />
            </div>
            <b>{value}</b>
          </div>
        ))}
      </div>
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

function Metric({ label, value, detail }) {
  return (
    <div className="metric-card">
      <strong>{value}</strong>
      <span>{label}</span>
      {detail && <small>{detail}</small>}
    </div>
  );
}

function buildRunExplanation(metrics, publishableCount, reviewCount) {
  const species = metrics.species_safe_records || 0;
  const genus = metrics.genus_safe_records || 0;
  const blocked = metrics.blocked_species_claims || 0;
  return `This run produces ${publishableCount} publishable candidate ${pluralize('record', publishableCount)}: ${species} at species rank and ${genus} downgraded to genus or safer rank. ${reviewCount} ${pluralize('record', reviewCount)} stay in the review queue. ${blocked} unsafe species-level ${pluralize('claim', blocked)} were blocked before export. Formal GBIF-ready rows remain a separate dataset-metadata state.`;
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
