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
  ['Absolute biological truth', 'All decisions are reproducible under supplied evidence and reference context.'],
  ['Replacement for GBIF Sequence ID', 'The compiler is a downstream decision layer after Sequence ID / BLAST-style matching.'],
  ['Universal readiness score', 'The project uses deterministic gates and blockers, not arbitrary weights.'],
  ['Presence or absence in nature', 'The output is molecular occurrence evidence with caveats, not a distribution truth model.'],
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
          <h1>Barcode-to-GBIF Evidence Compiler</h1>
          <p className="topbar-subtitle">
            A deterministic workflow that turns DNA barcode, metabarcoding or Sequence ID results into safe, rank-aware and GBIF-ready molecular occurrence evidence.
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
          <h2>Not an abstract atlas score. A fail-closed compiler for molecular evidence.</h2>
          <p>
            The tool answers a narrow, judge-readable question: can this barcode-derived record safely support a species-level occurrence, or must it be downgraded to genus, higher rank, ambiguous, weak, no-match or not-publishable?
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
          <span>Current verdict</span>
          <strong>{pack?.summary?.verdict || 'Ready to compile a molecular evidence package.'}</strong>
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
          <h2>Why the compiler can say "publish", "downgrade" or "block".</h2>
          <p>
            This page exposes the full decision logic behind the Barcode-to-GBIF Evidence Compiler. The key point is simple:
            species-level output is allowed only when every molecular and publication gate passes. Otherwise the record is
            downgraded, kept for review or blocked from publishable exports.
          </p>
        </div>
        <div className="proof-summary">
          <strong>Fail-closed rule</strong>
          <span>No arbitrary score. No hidden weights. No blind top-hit species claims.</span>
        </div>
      </section>

      <section className="panel">
        <p className="section-label">Plain-language contract</p>
        <h2>Technical quality control before DNA-derived records become GBIF-ready evidence.</h2>
        <p className="proof-copy">
          A sequence match is not automatically a species occurrence. The compiler checks whether the match is strong,
          whether close species are indistinguishable, whether the marker separates the taxon, whether diagnostic sequence
          signal exists, and whether the record has the metadata needed for publication.
        </p>
        <div className="status-strip" aria-label="Decision classes">
          {['species-safe', 'genus-safe', 'higher-rank-safe', 'ambiguous', 'weak', 'no-match', 'not-publishable'].map((status) => (
            <span key={status}>{status}</span>
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
