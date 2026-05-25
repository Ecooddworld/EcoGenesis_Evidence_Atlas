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
};

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
  return (
    <section className="workspace">
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
        <label>
          Compiler request JSON
          <textarea value={jsonInput} onChange={(event) => setJsonInput(event.target.value)} spellCheck="false" />
        </label>
        <button className="primary wide" onClick={runCompiler} disabled={loading}>
          {loading ? 'Compiling evidence...' : 'Generate Evidence Package'}
        </button>
        <details>
          <summary>Accepted input shape</summary>
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
              <div className="metrics-grid compact">
                <Metric label="Processed" value={pack.metrics.processed_records} />
                <Metric label="Species-safe" value={pack.metrics.species_safe_records} />
                <Metric label="Genus-safe" value={pack.metrics.genus_safe_records} />
                <Metric label="Record-ready" value={pack.metrics.record_ready_records} />
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
                        <td>{record.publication_stage}</td>
                        <td>{record.blockers.length ? record.blockers.slice(0, 2).join('; ') : 'none'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="panel">
              <p className="section-label">Evidence pack</p>
              <div className="export-grid">
                {exports.map((item) => (
                  <a key={item.name} href={exportUrl(item.url)}>{item.name}</a>
                ))}
              </div>
            </section>
          </>
        )}
      </div>
    </section>
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

export default App;
