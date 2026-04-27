import { useEffect, useMemo, useRef, useState } from 'react';
import 'leaflet/dist/leaflet.css';
import {
  exportUrl,
  getDemoScenarios,
  getEvidenceRun,
  getRegionPresets,
  listEvidenceRuns,
  runEvidencePassport,
  searchTaxa,
} from './api.js';

const purposeLabels = {
  conservation_brief: 'Conservation brief',
  invasive_watch: 'Invasive watch',
  sampling_gaps: 'Sampling gaps',
  dataset_quality_review: 'Dataset quality review',
};

const sourceModeLabels = {
  fixture: 'Offline sample data',
  online_with_fixture_fallback: 'Live GBIF, fallback if unavailable',
  online: 'Live GBIF only',
};

const fallbackPresets = [
  {
    id: 'invasive',
    label: 'Invasive risk',
    tag: 'Aedes albopictus · Spain',
    form: {
      taxon: 'Aedes albopictus',
      taxon_key: 1651430,
      region_name: 'Spain live GBIF bbox',
      bbox: '-10.0,35.0,4.5,44.5',
      purpose: 'invasive_watch',
      source_mode: 'online_with_fixture_fallback',
      use_fixture: false,
      max_records: 300,
    },
  },
  {
    id: 'gaps',
    label: 'Forest gaps',
    tag: 'Quercus robur · W Europe',
    form: {
      taxon: 'Quercus robur',
      taxon_key: 2878688,
      region_name: 'Western Europe live bbox',
      bbox: '-10.0,42.0,12.0,56.0',
      purpose: 'sampling_gaps',
      source_mode: 'online_with_fixture_fallback',
      use_fixture: false,
      max_records: 300,
    },
  },
  {
    id: 'quality',
    label: 'Data review',
    tag: 'Lynx pardinus · Iberia',
    form: {
      taxon: 'Lynx pardinus',
      taxon_key: 2435261,
      region_name: 'Iberian Peninsula live bbox',
      bbox: '-10.0,35.0,4.5,44.5',
      purpose: 'dataset_quality_review',
      source_mode: 'online_with_fixture_fallback',
      use_fixture: false,
      max_records: 300,
    },
  },
  {
    id: 'offline',
    label: 'Offline sample',
    tag: 'stable regression data',
    form: {
      taxon: 'Aedes albopictus',
      taxon_key: 1651430,
      region_name: 'Spain offline fixture bbox',
      bbox: '-10.0,35.0,4.5,44.5',
      purpose: 'invasive_watch',
      source_mode: 'fixture',
      use_fixture: true,
      max_records: 300,
    },
  },
];

const fallbackRegionPresets = [
  {
    id: 'spain',
    label: 'Spain',
    region_name: 'Spain live GBIF bbox',
    bbox: [-10, 35, 4.5, 44.5],
    description: 'Compact live GBIF test extent.',
  },
  {
    id: 'western-europe',
    label: 'Western Europe',
    region_name: 'Western Europe live bbox',
    bbox: [-10, 42, 12, 56],
    description: 'Broader sampling-gap experiments.',
  },
  {
    id: 'mediterranean',
    label: 'Western Mediterranean',
    region_name: 'Western Mediterranean live bbox',
    bbox: [-6.5, 34.5, 16, 46.5],
    description: 'Invasive-watch corridor tests.',
  },
];

const tabs = [
  { id: 'overview', label: 'Overview' },
  { id: 'map', label: 'Evidence Map' },
  { id: 'quality', label: 'Data Quality' },
  { id: 'gaps', label: 'Sampling Gaps' },
  { id: 'claims', label: 'Claim Guardrails' },
  { id: 'citation', label: 'Citation & Provenance' },
  { id: 'publisher', label: 'Publisher Feedback' },
  { id: 'exports', label: 'Export Pack' },
];

const qualityLabels = {
  total_records: 'Total records',
  valid_coordinate_rate: 'Valid coordinate rate',
  date_present_rate: 'Date present rate',
  recent_record_rate: 'Recent record rate',
  taxon_key_rate: 'Taxon key rate',
  dataset_key_rate: 'Dataset key rate',
  license_rate: 'License rate',
  high_uncertainty_rate: 'High uncertainty rate',
  missing_date_count: 'Missing date count',
  high_uncertainty_count: 'High uncertainty count',
  invalid_coordinate_count: 'Invalid coordinate count',
  country_coordinate_mismatch_count: 'Country-coordinate mismatch count',
};

function normalizeForm(form) {
  const sourceMode = form.source_mode || (form.use_fixture === false ? 'online_with_fixture_fallback' : 'fixture');
  return {
    taxon: form.taxon || 'Aedes albopictus',
    taxon_key: form.taxon_key || form.taxonKey || '',
    region_name: form.region_name || 'Spain live GBIF bbox',
    bbox: Array.isArray(form.bbox) ? form.bbox.join(',') : form.bbox || '-10.0,35.0,4.5,44.5',
    purpose: form.purpose || 'invasive_watch',
    source_mode: sourceMode,
    use_fixture: sourceMode === 'fixture',
    max_records: form.max_records || 300,
  };
}

function normalizePreset(preset) {
  return {
    ...preset,
    form: normalizeForm(preset.form || {}),
  };
}

const defaultForm = normalizeForm(fallbackPresets[0].form);

function parseBbox(text) {
  const parts = text.split(',').map((part) => Number(part.trim()));
  if (parts.length !== 4 || parts.some((part) => Number.isNaN(part))) {
    throw new Error('Bounding box must use four numbers: west,south,east,north');
  }
  const [west, south, east, north] = parts;
  if (west >= east || south >= north) {
    throw new Error('Bounding box coordinates are not ordered as west,south,east,north');
  }
  return parts;
}

function payloadFromForm(form) {
  const sourceMode = form.source_mode || 'fixture';
  const taxonKey = Number(form.taxon_key);
  return {
    ...form,
    bbox: parseBbox(form.bbox),
    taxon_key: Number.isFinite(taxonKey) && taxonKey > 0 ? taxonKey : null,
    max_records: Number(form.max_records),
    source_mode: sourceMode,
    use_fixture: sourceMode === 'fixture',
  };
}

function requestSignature(payload) {
  const bbox = Array.isArray(payload.bbox) ? payload.bbox : parseBbox(String(payload.bbox || ''));
  return JSON.stringify({
    taxon: String(payload.taxon || '').trim().toLowerCase(),
    taxon_key: payload.taxon_key ? Number(payload.taxon_key) : null,
    region_name: String(payload.region_name || '').trim().toLowerCase(),
    bbox: bbox.map((value) => Number(Number(value).toFixed(6))),
    purpose: payload.purpose || '',
    source_mode: payload.source_mode || '',
    max_records: Number(payload.max_records || 0),
  });
}

function requestSignatureFromForm(form) {
  try {
    return requestSignature(payloadFromForm(normalizeForm(form)));
  } catch {
    return 'invalid-current-selection';
  }
}

function requestSignatureFromRun(request) {
  if (!request) return '';
  try {
    return requestSignature(payloadFromForm(normalizeForm(request)));
  } catch {
    return '';
  }
}

function bboxValues(text) {
  const parts = String(text || '').split(',');
  return [0, 1, 2, 3].map((index) => parts[index]?.trim() || '');
}

function formatBbox(bbox) {
  return bbox.map((value) => Number(value).toFixed(Number(value) % 1 === 0 ? 0 : 2)).join(',');
}

function readRecentRuns() {
  if (typeof window === 'undefined') return [];
  try {
    return JSON.parse(window.localStorage.getItem('evidenceAtlasRecentRuns') || '[]');
  } catch {
    return [];
  }
}

function writeRecentRuns(runs) {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem('evidenceAtlasRecentRuns', JSON.stringify(runs.slice(0, 8)));
}

function runToRecent(detail) {
  return {
    run_id: detail.run.run_id,
    taxon: detail.passport.taxon,
    region_name: detail.passport.region_name,
    purpose: detail.evidence_readiness.purpose_label,
    score: detail.evidence_readiness.score,
    finished_at: detail.run.finished_at,
    source_mode: detail.source_summary?.used_source_mode || detail.run.source_mode,
    fallback_used: detail.source_summary?.fallback_used || false,
  };
}

export default function App() {
  const [presets, setPresets] = useState(fallbackPresets.map(normalizePreset));
  const [regionPresets, setRegionPresets] = useState(fallbackRegionPresets);
  const [form, setForm] = useState(defaultForm);
  const [run, setRun] = useState(null);
  const [created, setCreated] = useState(null);
  const [loading, setLoading] = useState(false);
  const [booting, setBooting] = useState(true);
  const [loadingRunId, setLoadingRunId] = useState('');
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('overview');
  const [recentRuns, setRecentRuns] = useState(readRecentRuns);
  const [progressSteps, setProgressSteps] = useState([]);
  const [taxonSuggestions, setTaxonSuggestions] = useState([]);
  const [taxonSearchStatus, setTaxonSearchStatus] = useState('');
  const bboxParts = bboxValues(form.bbox);
  const formSignature = requestSignatureFromForm(form);
  const runSignature = requestSignatureFromRun(run?.run?.request);
  const selectionChanged = Boolean(run && formSignature && runSignature && formSignature !== runSignature);

  function rememberRun(detail) {
    const item = runToRecent(detail);
    setRecentRuns((previous) => {
      const recent = [item, ...previous.filter((row) => row.run_id !== item.run_id)].slice(0, 8);
      writeRecentRuns(recent);
      return recent;
    });
  }

  async function refreshRecentRuns() {
    try {
      const rows = await listEvidenceRuns();
      if (rows.length) {
        setRecentRuns(rows);
        writeRecentRuns(rows);
        return rows;
      }
    } catch {
      return readRecentRuns();
    }
    return readRecentRuns();
  }

  async function loadRun(runId) {
    const detail = await getEvidenceRun(runId);
    setCreated({ run_id: runId, status: 'completed', exports: detail.exports });
    setRun(detail);
    if (detail.run?.request) {
      setForm(normalizeForm(detail.run.request));
    }
    setActiveTab('overview');
    rememberRun(detail);
    return detail;
  }

  async function runPassport(formLike) {
    const normalized = normalizeForm(formLike);
    const payload = payloadFromForm(normalized);
    setProgressSteps(buildProgressSteps('running'));
    const createdRun = await runEvidencePassport(payload);
    const detail = await getEvidenceRun(createdRun.run_id);
    setCreated(createdRun);
    setRun(detail);
    setActiveTab('overview');
    rememberRun(detail);
    await refreshRecentRuns();
    setProgressSteps(buildProgressSteps('completed', detail.run?.steps || []));
    return detail;
  }

  useEffect(() => {
    let cancelled = false;
    async function boot() {
      setBooting(true);
      setError('');
      let scenarioList = fallbackPresets.map(normalizePreset);
      try {
        const remoteScenarios = await getDemoScenarios();
        if (!cancelled && Array.isArray(remoteScenarios) && remoteScenarios.length) {
          scenarioList = remoteScenarios.map(normalizePreset);
          setPresets(scenarioList);
          setForm(scenarioList[0].form);
        }
      } catch {
        if (!cancelled) {
          setPresets(scenarioList);
        }
      }
      try {
        const remoteRegions = await getRegionPresets();
        if (!cancelled && Array.isArray(remoteRegions) && remoteRegions.length) {
          setRegionPresets(remoteRegions);
        }
      } catch {
        if (!cancelled) setRegionPresets(fallbackRegionPresets);
      }
      const backendRuns = await refreshRecentRuns();
      const cachedRunId = backendRuns[0]?.run_id || readRecentRuns()[0]?.run_id;
      if (cachedRunId) {
        try {
          await loadRun(cachedRunId);
          if (!cancelled) setBooting(false);
          return;
        } catch {
          // Fall through to the live preset, which can still use fixture fallback.
        }
      }

      try {
        await runPassport(scenarioList[0].form);
      } catch (err) {
        if (!cancelled) setError(err.message || 'Automatic passport failed');
      } finally {
        if (!cancelled) setBooting(false);
      }
    }
    boot();
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleSubmit(event) {
    event.preventDefault();
    await runCurrentSelection();
  }

  async function runCurrentSelection() {
    setError('');
    setLoading(true);
    try {
      await runPassport(form);
    } catch (err) {
      setProgressSteps(buildProgressSteps('failed'));
      setError(err.message || 'Evidence run failed');
    } finally {
      setLoading(false);
      setBooting(false);
    }
  }

  async function handleLoadRun(runId) {
    setError('');
    setLoadingRunId(runId);
    try {
      await loadRun(runId);
    } catch (err) {
      setError(err.message || 'Run could not be loaded');
    } finally {
      setLoadingRunId('');
    }
  }

  function applyPreset(preset) {
    setForm(normalizeForm(preset.form));
    setError('');
  }

  function updateSourceMode(sourceMode) {
    setForm({ ...form, source_mode: sourceMode, use_fixture: sourceMode === 'fixture' });
  }

  async function handleTaxonSearch() {
    if (form.taxon.trim().length < 2) {
      setTaxonSearchStatus('Type at least two letters or choose a curated taxon below.');
      return;
    }
    setTaxonSearchStatus('Searching GBIF...');
    try {
      const payload = await searchTaxa(form.taxon, 10);
      setTaxonSuggestions(payload.results || []);
      setTaxonSearchStatus((payload.results || []).length ? '' : 'No GBIF taxon suggestions found. Try a scientific name.');
    } catch (err) {
      setTaxonSearchStatus(err.message || 'GBIF taxon search failed');
    }
  }

  function selectTaxonSuggestion(suggestion) {
    const name = suggestion.canonicalName || suggestion.scientificName || form.taxon;
    setForm({
      ...form,
      taxon: name,
      taxon_key: suggestion.usageKey || '',
    });
    setTaxonSearchStatus(`Selected GBIF taxonKey ${suggestion.usageKey || 'unknown'}`);
  }

  function applyRegionPreset(region) {
    setForm({
      ...form,
      region_name: region.region_name,
      bbox: formatBbox(region.bbox),
    });
    setError('');
  }

  function updateBboxPart(index, value) {
    const next = [...bboxParts];
    next[index] = value;
    setForm({ ...form, bbox: next.join(',') });
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">EcoGenesis Evidence Atlas</p>
          <h1>GBIF Evidence Passport</h1>
          <p className="topbar-subtitle">Build a map-backed evidence pack for any GBIF taxon and region, with data-quality checks, citations and claim guardrails.</p>
        </div>
      </header>

      <section className="workspace">
        <aside className="run-rail" aria-label="Evidence run controls">
          <form className="rail-section run-form" onSubmit={handleSubmit}>
            <div className="form-intro">
              <p className="section-label">New Passport</p>
              <p className="rail-copy">Choose a species and area, then generate the passport. The map updates only after generation.</p>
            </div>
            <div className="taxon-picker">
              <label>
                Taxon
                <input
                  placeholder="Type a species, genus or scientific name"
                  value={form.taxon}
                  onChange={(event) => setForm({ ...form, taxon: event.target.value, taxon_key: '' })}
                />
              </label>
              <button className="secondary-action" type="button" onClick={handleTaxonSearch}>
                Search GBIF taxon
              </button>
              <div className="selected-taxon" aria-live="polite">
                {form.taxon_key ? (
                  <span>Locked to GBIF taxonKey {form.taxon_key}</span>
                ) : (
                  <span>Custom name will be matched by GBIF during the run.</span>
                )}
              </div>
              {taxonSearchStatus ? <p className="helper-note">{taxonSearchStatus}</p> : null}
              {taxonSuggestions.length ? (
                <div className="taxon-suggestion-list" aria-label="GBIF taxon suggestions">
                  {taxonSuggestions.map((suggestion) => (
                    <button
                      key={`${suggestion.usageKey}-${suggestion.scientificName}`}
                      onClick={() => selectTaxonSuggestion(suggestion)}
                      type="button"
                    >
                      <span>{suggestion.canonicalName || suggestion.scientificName}</span>
                      <small>
                        {suggestion.rank || 'taxon'} · key {suggestion.usageKey || 'unknown'}
                        {suggestion.family ? ` · ${suggestion.family}` : ''}
                      </small>
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
            <label>
              Region
              <input
                value={form.region_name}
                onChange={(event) => setForm({ ...form, region_name: event.target.value })}
              />
            </label>
            <details className="inline-drawer">
              <summary>Saved regions</summary>
              <div className="region-preset-list" aria-label="Region presets">
                {regionPresets.map((region) => (
                  <button key={region.id} onClick={() => applyRegionPreset(region)} type="button">
                    <span>{region.label}</span>
                    <small>{region.description}</small>
                  </button>
                ))}
              </div>
            </details>
            <fieldset className="bbox-grid">
              <legend>Bounding box</legend>
              <label>
                West
                <input
                  aria-label="West longitude"
                  value={bboxParts[0]}
                  onChange={(event) => updateBboxPart(0, event.target.value)}
                />
              </label>
              <label>
                South
                <input
                  aria-label="South latitude"
                  value={bboxParts[1]}
                  onChange={(event) => updateBboxPart(1, event.target.value)}
                />
              </label>
              <label>
                East
                <input
                  aria-label="East longitude"
                  value={bboxParts[2]}
                  onChange={(event) => updateBboxPart(2, event.target.value)}
                />
              </label>
              <label>
                North
                <input
                  aria-label="North latitude"
                  value={bboxParts[3]}
                  onChange={(event) => updateBboxPart(3, event.target.value)}
                />
              </label>
            </fieldset>
            <div className="field-pair">
              <label>
                Purpose
                <select
                  value={form.purpose}
                  onChange={(event) => setForm({ ...form, purpose: event.target.value })}
                >
                  {Object.entries(purposeLabels).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Max records
                <input
                  min="1"
                  type="number"
                  value={form.max_records}
                  onChange={(event) => setForm({ ...form, max_records: event.target.value })}
                />
              </label>
            </div>
            <details className="inline-drawer">
              <summary>Data source</summary>
              <label>
                Source
                <select value={form.source_mode} onChange={(event) => updateSourceMode(event.target.value)}>
                  {Object.entries(sourceModeLabels).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
            </details>
            <button className="primary-action" type="submit" disabled={loading || booting}>
              {loading ? 'Generating passport...' : booting ? 'Preparing passport...' : 'Generate Evidence Passport'}
            </button>
            {error ? <p className="error">{error}</p> : null}
            {created ? <p className="run-id">Run {created.run_id}</p> : null}
          </form>

          <details className="rail-section drawer-section">
            <summary>Example studies</summary>
            <div className="preset-grid">
              {presets.filter((preset) => preset.id !== 'offline').map((preset) => (
                <button
                  className={form.purpose === preset.form.purpose ? 'preset active' : 'preset'}
                  key={preset.id}
                  onClick={() => applyPreset(preset)}
                  type="button"
                >
                  <span>{preset.label}</span>
                  <small>{preset.tag}</small>
                </button>
              ))}
            </div>
          </details>

          <PipelineProgress steps={progressSteps.length ? progressSteps : run?.run?.steps} loading={loading || booting} />

          <RecentRuns runs={recentRuns} loadingRunId={loadingRunId} onLoad={handleLoadRun} />
        </aside>

        <Passport
          run={run}
          booting={booting}
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          selectionChanged={selectionChanged}
          loading={loading}
          onRunCurrent={runCurrentSelection}
        />
      </section>
    </main>
  );
}

function RecentRuns({ runs, loadingRunId, onLoad }) {
  return (
    <details className="rail-section drawer-section recent-runs">
      <summary>Recent passports</summary>
      {runs.length ? (
        <div className="recent-list">
          {runs.map((item) => (
            <button key={item.run_id} type="button" onClick={() => onLoad(item.run_id)}>
              <span>{item.taxon}</span>
              <small>
                {loadingRunId === item.run_id
                  ? 'Loading...'
                  : `${item.purpose} · ${item.score}/100 · ${shortStatus(item.source_mode)}`}
              </small>
            </button>
          ))}
        </div>
      ) : (
        <p className="empty-note">Your generated passports will appear here.</p>
      )}
    </details>
  );
}

function PipelineProgress({ steps, loading }) {
  const rows = steps?.length ? steps : buildProgressSteps(loading ? 'running' : 'pending');
  return (
    <details className="rail-section drawer-section pipeline-panel" open={loading}>
      <summary>Run details</summary>
      <div className="pipeline-list">
        {rows.map((step) => (
          <div className={`pipeline-step ${step.status}`} key={step.name}>
            <span>{pipelineLabel(step.name)}</span>
            <small>{step.status}{step.duration_ms ? ` · ${step.duration_ms} ms` : ''}</small>
          </div>
        ))}
      </div>
    </details>
  );
}

function Passport({ run, booting, activeTab, setActiveTab, selectionChanged = false, loading = false, onRunCurrent }) {
  if (!run) {
    return <LoadingWorkbench booting={booting} />;
  }

  const readiness = run.evidence_readiness;
  const zip = run.exports?.find((item) => item.name === 'evidence_pack.zip');
  const status = readinessStatus(readiness.score);
  return (
    <section className="result-stack" aria-label="Evidence Passport result">
      {selectionChanged ? (
        <div className="draft-banner" role="status">
          <div>
            <strong>Selection changed</strong>
            <p>The map and score still show the previous passport. Generate a new passport to update the evidence for this taxon and region.</p>
          </div>
          <button className="primary-action" type="button" onClick={onRunCurrent} disabled={loading}>
            {loading ? 'Generating...' : 'Generate updated passport'}
          </button>
        </div>
      ) : null}
      <div className={`score-band ${scoreClass(readiness.score)}`}>
        <div>
          <p className="eyebrow">{readiness.purpose_label}</p>
          <h2>{run.passport.taxon}</h2>
          <p>{run.passport.region_name} · {status.label}</p>
        </div>
        <div className="score-readout">
          <strong>{readiness.score}</strong>
          <span>/100</span>
        </div>
        {zip ? (
          <a className="zip-action" href={exportUrl(zip.url)}>
            Download Evidence Pack
          </a>
        ) : null}
      </div>

      <KpiStrip run={run} />

      <div className="analysis-grid">
        <MapPreview run={run} />
        <ScientificInterpretation run={run} />
        <GapPriorityPanel run={run} compact />
        <ReadinessBreakdown readiness={readiness} />
        <PurposeComparison matrix={run.purpose_score_matrix} current={readiness.purpose} />
        <SourceProvenance run={run} compact />
      </div>

      <nav className="tab-strip" aria-label="Passport sections">
        {tabs.map((tab) => (
          <button
            className={activeTab === tab.id ? 'active' : ''}
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            type="button"
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <TabPanel run={run} activeTab={activeTab} />
    </section>
  );
}

function LoadingWorkbench({ booting }) {
  return (
    <section className="empty-workbench">
      <div>
        <p className="eyebrow">Evidence workspace</p>
        <h2>{booting ? 'Preparing the default Evidence Passport' : 'Evidence Passport is ready to run'}</h2>
        <p>
          The default flow attempts live GBIF data first and keeps offline sample data only as a safe fallback,
          while preserving provenance, claim guardrails, citation guidance and a complete export bundle.
        </p>
      </div>
      <div className="skeleton-grid" aria-label="Loading Evidence Passport">
        {['Readiness score', 'Live map', 'Real GBIF records', 'Source provenance', 'Claim Guardrails', 'Evidence pack'].map(
          (item) => (
            <span key={item}>{item}</span>
          ),
        )}
      </div>
    </section>
  );
}

function KpiStrip({ run }) {
  const quality = run.quality_metrics;
  const gridMeta = run.grid_metrics?.meta || {};
  const items = [
    { label: 'Records used', value: run.passport.records_used },
    { label: 'Datasets', value: run.passport.datasets_used },
    { label: 'No-evidence cells', value: gridMeta.empty_cell_count ?? 0 },
    { label: 'Survey priorities', value: gridMeta.survey_priority_cells ?? 0 },
    { label: 'High uncertainty', value: quality.high_uncertainty_count },
    { label: 'Source', value: shortStatus(run.source_summary?.used_source_mode) },
  ];
  return (
    <div className="kpi-strip">
      {items.map((item) => (
        <div className="kpi" key={item.label}>
          <span>{item.label}</span>
          <strong>{item.value}</strong>
        </div>
      ))}
    </div>
  );
}

function ReadinessBreakdown({ readiness }) {
  return (
    <section className="panel readiness-panel">
      <div className="panel-title">
        <h3>Purpose weights</h3>
        <span>{readiness.interpretation}</span>
      </div>
      <div className="component-bars">
        {Object.entries(readiness.components).map(([key, value]) => (
          <div className="component-row" key={key}>
            <div>
              <span>{humanize(key)}</span>
              <small>weight {Math.round((readiness.weights[key] || 0) * 100)}%</small>
            </div>
            <div className="bar-track" aria-label={`${humanize(key)} score ${value}`}>
              <span style={{ width: `${Math.max(0, Math.min(100, value))}%` }} />
            </div>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}

function PurposeComparison({ matrix, current }) {
  const rows = Object.values(matrix || {});
  return (
    <section className="panel purpose-panel">
      <div className="panel-title">
        <h3>Purpose comparison</h3>
        <span>same records, different decision weights</span>
      </div>
      <div className="purpose-list">
        {rows.map((row) => (
          <div className={row.purpose === current ? 'purpose-row active' : 'purpose-row'} key={row.purpose}>
            <div>
              <span>{row.purpose_label}</span>
              <small>{row.interpretation}</small>
            </div>
            <strong>{row.score}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}

function ScientificInterpretation({ run }) {
  const meta = run.grid_metrics?.meta || {};
  const quality = run.quality_metrics || {};
  const thesis = buildScientificThesis(run);
  const findings = [
    {
      label: 'Evidence basis',
      value: `${run.passport.records_used} records`,
      detail: `${run.passport.datasets_used} datasets; taxon match ${run.passport.match_confidence || 'unknown'}%`,
      tone: 'evidence',
    },
    {
      label: 'No-evidence cells',
      value: meta.empty_cell_count ?? 0,
      detail: 'empty grid cells are treated as unknown, not absence',
      tone: 'unknown',
    },
    {
      label: 'Survey priority',
      value: meta.survey_priority_cells ?? 0,
      detail: `${meta.under_sampled_occupied_cells ?? 0} occupied cells need stronger sampling`,
      tone: 'priority',
    },
    {
      label: 'Quality caveat',
      value: quality.high_uncertainty_count ?? 0,
      detail: 'records above 10 km coordinate uncertainty',
      tone: 'caveat',
    },
  ];

  return (
    <section className="panel scientific-panel">
      <div className="panel-title">
        <h3>Scientific interpretation</h3>
        <span>{run.evidence_readiness.interpretation}</span>
      </div>
      <div className="thesis-block">
        <span>Evidence thesis</span>
        <strong>{thesis}</strong>
      </div>
      <div className="finding-grid">
        {findings.map((finding) => (
          <div className={`finding-card ${finding.tone}`} key={finding.label}>
            <span>{finding.label}</span>
            <strong>{finding.value}</strong>
            <small>{finding.detail}</small>
          </div>
        ))}
      </div>
      <div className="method-strip">
        <span>Method: GBIF species match</span>
        <span>quality triage</span>
        <span>4x4 sampling grid</span>
        <span>claim guardrails</span>
      </div>
    </section>
  );
}

function SourceProvenance({ run, compact = false }) {
  const source = run.source_summary || {};
  const match = run.run?.gbif_species_match || {};
  const rows = [
    ['Requested', shortStatus(source.requested_source_mode)],
    ['Used', shortStatus(source.used_source_mode)],
    ['GBIF API status', shortStatus(source.gbif_api_status)],
    ['Fallback used', source.fallback_used ? 'yes' : 'no'],
    ['GBIF total matches', source.gbif_result_count ?? 'unknown'],
    ['Returned records', source.gbif_returned_records ?? run.passport.records_used],
    ['Taxon key', run.passport.taxonKey || match.usageKey || 'unknown'],
    ['Match confidence', run.passport.match_confidence || match.confidence || 'unknown'],
  ];
  return (
    <section className={compact ? 'panel source-panel compact' : 'panel source-panel'}>
      <div className="panel-title">
        <h3>Source & provenance</h3>
        <span>{source.warnings?.length ? `${source.warnings.length} warning(s)` : 'no source warnings'}</span>
      </div>
      <div className="source-grid">
        {rows.map(([label, value]) => (
          <div key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
      {source.warnings?.length ? (
        <ul className="warning-list">
          {source.warnings.map((warning) => (
            <li key={warning}>{warning}</li>
          ))}
        </ul>
      ) : null}
      {!compact ? <RunSteps steps={run.run?.steps || []} /> : null}
    </section>
  );
}

function RunSteps({ steps }) {
  return (
    <div className="step-list">
      <h4>Run Steps</h4>
      {steps.map((step) => (
        <div className={step.status === 'failed' ? 'step-row failed' : 'step-row'} key={step.name}>
          <span>{humanize(step.name)}</span>
          <strong>{step.status}</strong>
          <small>{step.duration_ms} ms</small>
        </div>
      ))}
    </div>
  );
}

function TabPanel({ run, activeTab }) {
  if (activeTab === 'map') {
    return (
      <div className="map-tab-stack">
        <MapPreview run={run} />
        <GapPriorityPanel run={run} />
      </div>
    );
  }
  if (activeTab === 'claims') return <ClaimsPanel guardrails={run.claim_guardrails} />;
  if (activeTab === 'quality') return <QualityPanel run={run} />;
  if (activeTab === 'gaps') return <GapPriorityPanel run={run} />;
  if (activeTab === 'citation') return <CitationPanel run={run} />;
  if (activeTab === 'publisher') return <PublisherPanel feedback={run.publisher_feedback} />;
  if (activeTab === 'exports') return <ExportsPanel exports={run.exports || []} />;
  return <OverviewPanel run={run} />;
}

function OverviewPanel({ run }) {
  const status = readinessStatus(run.evidence_readiness.score);
  const supported = run.claim_guardrails.supported_claims.slice(0, 2);
  const unsupported = run.claim_guardrails.unsupported_claims.slice(0, 2);
  return (
    <div className="overview-grid">
      <section className={`panel readiness-status ${scoreClass(run.evidence_readiness.score)}`}>
        <div className="panel-title">
          <h3>Evidence summary</h3>
          <span>{status.label}</span>
        </div>
        <p>{status.description}</p>
        <p className="score-caveat">This score is a decision-support heuristic, not a biological truth or model prediction.</p>
      </section>
      <ListPanel title="What this supports" rows={supported} tone="supported" />
      <ListPanel title="What this does not support" rows={unsupported} tone="unsupported" />
      <ListPanel title="Main risks" rows={run.main_risks} tone="risk" />
      <ListPanel title="Next actions" rows={run.next_actions} tone="action" />
      <section className="panel span-two">
        <div className="panel-title">
          <h3>Dataset contributors</h3>
          <span>{run.dataset_contributions.length} contributing datasets</span>
        </div>
        <DatasetTable rows={run.dataset_contributions} />
      </section>
    </div>
  );
}

function ListPanel({ title, rows, tone }) {
  return (
    <section className={`panel list-panel ${tone || ''}`}>
      <h3>{title}</h3>
      <ul>
        {rows.map((row) => (
          <li key={row}>{row}</li>
        ))}
      </ul>
    </section>
  );
}

function ClaimsPanel({ guardrails }) {
  const sections = [
    { title: 'Supported claims', rows: guardrails.supported_claims, tone: 'supported' },
    { title: 'Weak claims', rows: guardrails.weak_claims, tone: 'weak' },
    { title: 'Unsupported claims', rows: guardrails.unsupported_claims, tone: 'unsupported' },
    { title: 'Required verification', rows: guardrails.required_verification, tone: 'required' },
  ];
  return (
    <div className="claims-grid">
      {sections.map((section) => (
        <ListPanel key={section.title} title={section.title} rows={section.rows} tone={section.tone} />
      ))}
    </div>
  );
}

function QualityPanel({ run }) {
  const cells = run.grid_metrics?.features || [];
  const meta = run.grid_metrics?.meta || {};
  const metaRows = [
    ['Total cells', meta.cell_count],
    ['Occupied cells', meta.occupied_cell_count],
    ['No-evidence cells', meta.empty_cell_count],
    ['Under-sampled occupied', meta.under_sampled_occupied_cells],
    ['Survey priorities', meta.survey_priority_cells],
  ];
  return (
    <div className="quality-grid">
      <section className="panel">
        <div className="panel-title">
          <h3>Quality metrics</h3>
          <span>{run.quality_metrics.total_records} normalized records</span>
        </div>
        <div className="quality-metas">
          {metaRows.map(([label, value]) => (
            <div key={label}>
              <span>{label}</span>
              <strong>{value ?? 0}</strong>
            </div>
          ))}
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Metric</th>
                <th>Value</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(run.quality_metrics).map(([key, value]) => (
                <tr key={key}>
                  <td>{qualityLabels[key] || humanize(key)}</td>
                  <td>{formatValue(key, value)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <RecordsExplorer records={run.normalized_records || []} />
      <section className="panel">
        <div className="panel-title">
          <h3>Sampling grid</h3>
          <span>{run.grid_metrics?.meta?.method}</span>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Cell</th>
                <th>Records</th>
                <th>Coverage</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {cells.map((feature) => (
                <tr key={feature.properties.cell_id}>
                  <td>{feature.properties.cell_id}</td>
                  <td>{feature.properties.occurrence_count}</td>
                  <td>{formatPercent(feature.properties.sampling_coverage_proxy)}</td>
                  <td>{cellStatus(feature.properties)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function RecordsExplorer({ records }) {
  const rows = records.slice(0, 12).map((record) => {
    const severity = recordStatus(record);
    return { ...record, severity };
  });
  return (
    <section className="panel span-two">
      <div className="panel-title">
        <h3>Records Explorer</h3>
        <span>{records.length} normalized records · flagged records remain visible</span>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Status</th>
              <th>gbifID</th>
              <th>Date</th>
              <th>Dataset</th>
              <th>Basis</th>
              <th>Uncertainty</th>
              <th>Issues</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((record) => (
              <tr key={record.gbif_id}>
                <td><span className={`record-status ${record.severity}`}>{record.severity}</span></td>
                <td>{record.gbif_id}</td>
                <td>{record.event_date || record.year || 'missing'}</td>
                <td>{record.dataset_key}</td>
                <td>{record.basis_of_record || 'unknown'}</td>
                <td>{record.coordinate_uncertainty_m ? `${Math.round(record.coordinate_uncertainty_m)} m` : 'unknown'}</td>
                <td>{record.issues?.length ? record.issues.join(', ') : 'none detected'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function GapPriorityPanel({ run, compact = false }) {
  const features = run.grid_metrics?.features || [];
  const priorityCells = features
    .filter((feature) => feature.properties.survey_priority)
    .sort((a, b) => b.properties.gap_priority_score - a.properties.gap_priority_score);
  const rows = compact ? priorityCells.slice(0, 3) : priorityCells;
  return (
    <section className={compact ? 'panel gap-panel compact' : 'panel gap-panel'}>
      <div className="panel-title">
        <h3>Sampling Gap Engine</h3>
        <span>{priorityCells.length} survey-priority cells · no evidence is not absence</span>
      </div>
      <div className="gap-list">
        {rows.map((feature) => {
          const props = feature.properties;
          return (
            <div className="gap-row" key={props.cell_id}>
              <div>
                <span>{props.cell_id}</span>
                <small>{(props.gap_priority_reasons || []).slice(0, compact ? 2 : 4).join('; ')}</small>
              </div>
              <strong>{props.gap_priority_score}</strong>
              <em>{props.gap_priority_label}</em>
            </div>
          );
        })}
      </div>
      {!rows.length ? <p className="empty-note">No survey-priority cells were generated for this run.</p> : null}
    </section>
  );
}

function CitationPanel({ run }) {
  const citation = run.citation_autopilot;
  return (
    <div className="citation-grid">
      <section className="panel citation-card">
        <div className="panel-title">
          <h3>Citation Autopilot</h3>
          <span>{shortStatus(citation.citation_status)}</span>
        </div>
        <p className="warning-box">{citation.gbif_download_warning}</p>
        <h4>Methods text</h4>
        <p>{citation.methods_text}</p>
        <h4>Derived dataset recipe</h4>
        <div className="recipe-grid">
          <span>Group by</span>
          <strong>{citation.derived_dataset_recipe.group_by}</strong>
          <span>Include counts</span>
          <strong>{citation.derived_dataset_recipe.include_counts ? 'yes' : 'no'}</strong>
          <span>Preserve fields</span>
          <strong>{citation.derived_dataset_recipe.preserve_fields.join(', ')}</strong>
        </div>
      </section>
      <SourceProvenance run={run} compact />
      <section className="panel">
        <div className="panel-title">
          <h3>Contribution table</h3>
          <span>{citation.dataset_count} datasets</span>
        </div>
        <DatasetTable rows={run.dataset_contributions} />
      </section>
    </div>
  );
}

function PublisherPanel({ feedback }) {
  return (
    <section className="panel">
      <div className="panel-title">
        <h3>Publisher Feedback Pack</h3>
        <span>{feedback.length} grouped issues</span>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>datasetKey</th>
              <th>Records affected</th>
              <th>Main issue</th>
              <th>Suggested fix</th>
            </tr>
          </thead>
          <tbody>
            {feedback.map((row) => (
              <tr key={`${row.datasetKey}-${row.main_issue}`}>
                <td>{row.datasetKey}</td>
                <td>{row.records_affected}</td>
                <td>{row.main_issue}</td>
                <td>{row.suggested_fix}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {!feedback.length ? <p className="empty-note">No publisher feedback rows were generated.</p> : null}
    </section>
  );
}

function ExportsPanel({ exports }) {
  const groups = groupExports(exports);
  const checklist = [
    ['Standalone report', 'passport.html'],
    ['Citation pack', 'citations.md'],
    ['Map data', 'records.geojson'],
    ['Gap priorities', 'gap_priorities.csv'],
    ['Publisher feedback', 'publisher_feedback.md'],
    ['Provenance manifest', 'provenance.json'],
  ];
  const names = new Set(exports.map((item) => item.name));
  return (
    <section className="panel exports-panel">
      <div className="panel-title">
        <h3>Evidence pack exports</h3>
        <span>{exports.length} files</span>
      </div>
      <div className="export-checklist">
        {checklist.map(([label, name]) => (
          <span className={names.has(name) ? 'ready' : ''} key={name}>{label}</span>
        ))}
      </div>
      {groups.map((group) => (
        <div className="export-group" key={group.title}>
          <h4>{group.title}</h4>
          <div className="export-list">
            {group.files.map((item) => (
              <a className={item.name === 'evidence_pack.zip' ? 'zip-download' : ''} key={item.name} href={exportUrl(item.url)}>
                <span>{item.name === 'evidence_pack.zip' ? 'Evidence pack ZIP' : item.name}</span>
                <small>{formatBytes(item.size_bytes)}</small>
              </a>
            ))}
          </div>
        </div>
      ))}
    </section>
  );
}

function DatasetTable({ rows }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>datasetKey</th>
            <th>Records</th>
            <th>License</th>
            <th>Main issues</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.datasetKey}>
              <td>{row.datasetKey}</td>
              <td>{row.record_count}</td>
              <td>{row.license || 'unknown'}</td>
              <td>{row.main_issues}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function MapPreview({ run }) {
  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);
  const overlayRef = useRef(null);
  const [layers, setLayers] = useState({ cells: true, records: true, issues: true, priority: true });
  const features = run.records_geojson?.features || [];
  const bbox = run.passport.bbox;
  const cells = run.grid_metrics?.features || [];
  const points = useMemo(() => {
    return features.map((feature) => {
      const [lon, lat] = feature.geometry.coordinates;
      const uncertainty = Number(feature.properties.coordinateUncertaintyInMeters || 0);
      return {
        id: feature.properties.gbif_id,
        lon,
        lat,
        issue: (feature.properties.issues || []).length > 0,
        highUncertainty: uncertainty > 10000,
        uncertainty,
        dataset: feature.properties.datasetKey,
        eventDate: feature.properties.eventDate,
        scientificName: feature.properties.scientificName,
        issues: feature.properties.issues || [],
      };
    });
  }, [features]);
  const gridCells = useMemo(() => {
    return cells.map((feature) => {
      const coordinates = feature.geometry.coordinates[0];
      const cellWest = coordinates[0][0];
      const cellSouth = coordinates[0][1];
      const cellEast = coordinates[1][0];
      const cellNorth = coordinates[2][1];
      return {
        id: feature.properties.cell_id,
        bounds: [[cellSouth, cellWest], [cellNorth, cellEast]],
        center: [(cellSouth + cellNorth) / 2, (cellWest + cellEast) / 2],
        status: cellStatus(feature.properties),
        empty: feature.properties.empty_cell,
        underSampled: feature.properties.under_sampled,
        coverage: feature.properties.sampling_coverage_proxy,
        count: feature.properties.occurrence_count,
        priorityScore: feature.properties.gap_priority_score,
        priorityLabel: feature.properties.gap_priority_label,
        reasons: feature.properties.gap_priority_reasons || [],
      };
    });
  }, [cells]);
  const issuePoints = points.filter((point) => point.issue || point.highUncertainty);

  useEffect(() => {
    let cancelled = false;
    async function renderLeafletMap() {
      if (!mapContainerRef.current) return;
      const leaflet = await import('leaflet');
      const L = leaflet.default || leaflet;
      if (cancelled) return;

      if (!mapRef.current) {
        mapRef.current = L.map(mapContainerRef.current, {
          attributionControl: true,
          scrollWheelZoom: false,
          zoomControl: true,
        });
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '&copy; OpenStreetMap contributors',
          maxZoom: 18,
        }).addTo(mapRef.current);
      }

      const map = mapRef.current;
      if (overlayRef.current) {
        overlayRef.current.remove();
      }
      const overlays = L.layerGroup().addTo(map);
      overlayRef.current = overlays;

      const queryBounds = [[bbox[1], bbox[0]], [bbox[3], bbox[2]]];
      L.rectangle(queryBounds, {
        color: '#1f5268',
        dashArray: '8 6',
        fillOpacity: 0,
        weight: 2,
      }).bindTooltip(`Query bbox: ${bbox.join(', ')}`).addTo(overlays);

      if (layers.cells) {
        gridCells.forEach((cell) => {
          L.rectangle(cell.bounds, leafletCellStyle(cell))
            .bindPopup(cellPopupHtml(cell))
            .bindTooltip(`${cell.id}: ${cell.status}; gap ${cell.priorityScore}`)
            .addTo(overlays);
          if (layers.priority && cell.priorityScore >= 60) {
            L.marker(cell.center, {
              icon: L.divIcon({
                className: 'priority-marker',
                html: `<span>${Math.round(cell.priorityScore)}</span>`,
                iconSize: [34, 34],
                iconAnchor: [17, 17],
              }),
            }).bindPopup(cellPopupHtml(cell)).addTo(overlays);
          }
        });
      }

      if (layers.records) {
        points.forEach((point) => {
          const marker = L.circleMarker([point.lat, point.lon], {
            color: '#ffffff',
            fillColor: point.issue || point.highUncertainty ? '#b94e38' : '#176b4f',
            fillOpacity: 0.92,
            radius: point.issue || point.highUncertainty ? 6 : 5,
            weight: 1.4,
          })
            .bindPopup(recordPopupHtml(point))
            .bindTooltip(`${point.id || 'GBIF record'} · ${point.dataset || 'dataset unknown'}`);
          marker.addTo(overlays);
        });
      }

      if (layers.issues) {
        issuePoints.forEach((point) => {
          L.circle([point.lat, point.lon], {
            color: '#b94e38',
            fillColor: '#fff0ea',
            fillOpacity: 0.16,
            radius: Math.max(6000, Math.min(40000, point.uncertainty || 12000)),
            weight: 1.2,
          }).bindTooltip(`Quality caveat: ${Math.round(point.uncertainty || 0)} m uncertainty`).addTo(overlays);
        });
      }

      map.fitBounds(queryBounds, { padding: [20, 20] });
      setTimeout(() => map.invalidateSize(), 0);
    }
    renderLeafletMap();
    return () => {
      cancelled = true;
      if (overlayRef.current) {
        overlayRef.current.remove();
        overlayRef.current = null;
      }
    };
  }, [bbox, gridCells, issuePoints, layers, points]);

  useEffect(() => () => {
    if (mapRef.current) {
      mapRef.current.remove();
      mapRef.current = null;
    }
  }, []);

  function toggleLayer(name) {
    setLayers((current) => ({ ...current, [name]: !current[name] }));
  }

  return (
    <section className="panel map-panel scientific-map-panel">
      <div className="panel-title">
        <h3>Live evidence map</h3>
        <span>{features.length} mapped GBIF records · {gridCells.filter((cell) => cell.empty).length} no-evidence cells</span>
      </div>
      <div className="map-controls" aria-label="Map layers">
        {[
          ['cells', 'Cells'],
          ['records', 'Records'],
          ['issues', 'Issues'],
          ['priority', 'Priority'],
        ].map(([name, label]) => (
          <button className={layers[name] ? 'active' : ''} key={name} onClick={() => toggleLayer(name)} type="button">
            {label}
          </button>
        ))}
      </div>
      <div className="map-stage">
        <div ref={mapContainerRef} className="leaflet-map" role="img" aria-label="Scientific evidence map" />
        <div className="map-callout">
          <strong>Map thesis</strong>
          <span>OpenStreetMap base map with live GBIF occurrence points, quality halos, grid evidence and survey-priority cells.</span>
        </div>
      </div>
      <div className="map-legend">
        <span><i className="legend-dot" /> occurrence record</span>
        <span><i className="legend-dot issue" /> quality caveat</span>
        <span><i className="legend-ring" /> high uncertainty</span>
        <span><i className="legend-cell empty" /> no evidence</span>
        <span><i className="legend-cell priority" /> survey priority</span>
      </div>
    </section>
  );
}

function groupExports(exports) {
  const groupDefs = [
    { title: 'ZIP', names: ['evidence_pack.zip'] },
    { title: 'Passport', names: ['passport.html', 'passport.md'] },
    { title: 'Data', names: ['records.geojson', 'quality_metrics.csv', 'gap_priorities.csv', 'dataset_contributions.csv', 'readiness_scorecard.csv'] },
    { title: 'Citation & Claims', names: ['citations.md', 'claim_guardrails.md', 'methods_text.md'] },
    { title: 'Publisher', names: ['publisher_feedback.md', 'publisher_feedback.csv'] },
    { title: 'Machine-readable', names: ['evidence_pack.json', 'run.json', 'source_summary.json', 'demo_scenario.json', 'derived_dataset_recipe.json', 'provenance.json'] },
  ];
  const byName = new Map(exports.map((item) => [item.name, item]));
  const used = new Set();
  const groups = groupDefs
    .map((group) => {
      const files = group.names.map((name) => byName.get(name)).filter(Boolean);
      files.forEach((file) => used.add(file.name));
      return { ...group, files };
    })
    .filter((group) => group.files.length);
  const other = exports.filter((item) => !used.has(item.name));
  if (other.length) groups.push({ title: 'Other', files: other });
  return groups;
}

function scoreClass(score) {
  if (score >= 80) return 'high';
  if (score >= 60) return 'moderate';
  return 'limited';
}

function readinessStatus(score) {
  if (score >= 80) {
    return {
      label: 'High readiness',
      description: 'Good for the selected purpose, with citation and caveat checks still required.',
    };
  }
  if (score >= 60) {
    return {
      label: 'Moderate readiness',
      description: 'Usable evidence, but quality risks or sampling gaps require attention before stronger claims.',
    };
  }
  if (score >= 40) {
    return {
      label: 'Limited readiness',
      description: 'Useful for exploration and survey planning, weak for policy, absence or trend claims.',
    };
  }
  return {
    label: 'Insufficient readiness',
    description: 'Do not use for decision-making without additional verification and better evidence.',
  };
}

function buildProgressSteps(mode = 'pending', completedSteps = []) {
  const names = ['species_match', 'occurrence_fetch', 'normalize', 'score', 'exports'];
  const completedByName = new Map(completedSteps.map((step) => [step.name, step]));
  return names.map((name, index) => {
    if (completedByName.has(name)) return completedByName.get(name);
    if (mode === 'failed') return { name, status: index === 0 ? 'failed' : 'pending' };
    if (mode === 'completed') return { name, status: 'completed' };
    if (mode === 'running') return { name, status: index <= 1 ? 'running' : 'pending' };
    return { name, status: 'pending' };
  });
}

function pipelineLabel(name) {
  return {
    species_match: 'GBIF taxonomy match',
    occurrence_fetch: 'Occurrence retrieval',
    normalize: 'Record normalization',
    score: 'Quality, gaps and claims',
    exports: 'Evidence Pack export',
  }[name] || humanize(name);
}

function cellStatus(properties) {
  if (properties.empty_cell) return 'no evidence';
  if (properties.under_sampled) return 'under-sampled occupied';
  return 'sampled occupied';
}

function mapCellClass(cell) {
  const base = cell.empty ? 'map-cell-svg empty' : cell.underSampled ? 'map-cell-svg under' : 'map-cell-svg occupied';
  if (cell.priorityScore >= 60) return `${base} priority-high`;
  if (cell.priorityScore >= 35) return `${base} priority-medium`;
  return base;
}

function leafletCellStyle(cell) {
  if (cell.priorityScore >= 60) {
    return {
      color: '#9a5c13',
      dashArray: cell.empty ? '6 5' : undefined,
      fillColor: '#c98720',
      fillOpacity: 0.36,
      weight: 1.8,
    };
  }
  if (cell.empty) {
    return {
      color: '#6e8491',
      dashArray: '6 5',
      fillColor: '#8ca0ad',
      fillOpacity: 0.2,
      weight: 1.2,
    };
  }
  if (cell.underSampled) {
    return {
      color: '#af681e',
      fillColor: '#e4a24e',
      fillOpacity: 0.24,
      weight: 1.4,
    };
  }
  return {
    color: '#206b4f',
    fillColor: '#2b765b',
    fillOpacity: 0.18,
    weight: 1.2,
  };
}

function cellPopupHtml(cell) {
  const reasons = cell.reasons?.length ? cell.reasons.join('<br />') : 'No priority reason generated';
  return `
    <div class="popup-card">
      <strong>${escapeHtml(cell.id)}</strong>
      <span>${escapeHtml(cell.status)}</span>
      <dl>
        <dt>Records</dt><dd>${cell.count}</dd>
        <dt>Coverage</dt><dd>${formatPercent(cell.coverage)}</dd>
        <dt>Gap priority</dt><dd>${cell.priorityScore} · ${escapeHtml(cell.priorityLabel)}</dd>
      </dl>
      <p>${reasons}</p>
      <small>No-evidence cells are survey targets, not absence observations.</small>
    </div>
  `;
}

function recordPopupHtml(point) {
  const issues = point.issues?.length ? point.issues.join(', ') : 'none detected';
  return `
    <div class="popup-card">
      <strong>${escapeHtml(point.scientificName || 'GBIF occurrence')}</strong>
      <span>gbifID ${escapeHtml(point.id || 'unknown')}</span>
      <dl>
        <dt>Dataset</dt><dd>${escapeHtml(point.dataset || 'unknown')}</dd>
        <dt>Date</dt><dd>${escapeHtml(point.eventDate || 'missing')}</dd>
        <dt>Coordinates</dt><dd>${point.lon.toFixed(4)}, ${point.lat.toFixed(4)}</dd>
        <dt>Uncertainty</dt><dd>${Math.round(point.uncertainty || 0)} m</dd>
      </dl>
      <p>Issues: ${escapeHtml(issues)}</p>
    </div>
  `;
}

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function recordStatus(record) {
  if (!record.has_valid_coordinate || !record.accepted_taxon_key) return 'severe';
  if (!record.event_date && !record.year) return 'caution';
  if ((record.coordinate_uncertainty_m || 0) > 10000) return 'caution';
  if ((record.issues || []).length) return 'caution';
  return 'good';
}

function buildScientificThesis(run) {
  const meta = run.grid_metrics?.meta || {};
  const quality = run.quality_metrics || {};
  const score = run.evidence_readiness?.score ?? 0;
  if ((meta.empty_cell_count || 0) > (meta.occupied_cell_count || 0)) {
    return `The dataset is suitable for presence evidence and survey planning, but ${meta.empty_cell_count} no-evidence cells prevent absence or trend claims without additional sampling.`;
  }
  if ((quality.high_uncertainty_count || 0) > 0) {
    return `The evidence is usable for regional screening, while ${quality.high_uncertainty_count} high-uncertainty records need geospatial review before policy use.`;
  }
  if (score >= 80) {
    return 'The evidence pack is strong for the selected purpose, with citation and provenance still required before formal publication.';
  }
  return 'The evidence pack supports a bounded biodiversity claim and highlights the verification work needed before stronger conclusions.';
}

function shortStatus(value) {
  return String(value || 'unknown').replaceAll('_', ' ');
}

function humanize(value) {
  return String(value).replaceAll('_', ' ').replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatValue(key, value) {
  if (key.endsWith('_rate')) return formatPercent(value);
  return value;
}

function formatPercent(value) {
  if (typeof value !== 'number') return value;
  return `${Math.round(value * 100)}%`;
}

function formatBytes(value) {
  if (!value && value !== 0) return '';
  if (value < 1024) return `${value} B`;
  return `${(value / 1024).toFixed(1)} KB`;
}

function clamp(value) {
  return Math.max(0, Math.min(100, value));
}

function projectPoint(lon, lat, bbox, mapHeight = 68) {
  const [west, south, east, north] = bbox;
  return {
    x: clamp(((lon - west) / (east - west)) * 100),
    y: Math.max(0, Math.min(mapHeight, mapHeight - ((lat - south) / (north - south)) * mapHeight)),
  };
}

function projectPolygon(points, bbox, mapHeight) {
  return points
    .map(([lon, lat]) => {
      const projected = projectPoint(lon, lat, bbox, mapHeight);
      return `${projected.x.toFixed(2)},${projected.y.toFixed(2)}`;
    })
    .join(' ');
}

function buildBasemap(bbox, mapHeight) {
  const shapes = [
    {
      id: 'iberian-peninsula',
      title: 'Iberian Peninsula',
      className: 'basemap-land',
      coordinates: [
        [-9.5, 43.7],
        [-8.1, 43.35],
        [-6.2, 43.72],
        [-2.5, 43.47],
        [0.7, 42.75],
        [3.15, 41.95],
        [3.25, 40.45],
        [1.15, 39.25],
        [0.0, 38.62],
        [-0.65, 37.78],
        [-2.25, 36.75],
        [-5.0, 36.08],
        [-6.65, 36.02],
        [-7.38, 37.05],
        [-8.85, 37.0],
        [-9.3, 38.5],
        [-9.15, 40.15],
        [-9.62, 41.6],
        [-9.5, 43.7],
      ],
    },
    {
      id: 'france-context',
      title: 'Southern France context',
      className: 'basemap-neighbor',
      coordinates: [
        [-1.9, 44.5],
        [4.5, 44.5],
        [4.5, 42.12],
        [3.15, 41.95],
        [0.7, 42.75],
        [-1.9, 43.15],
        [-1.9, 44.5],
      ],
    },
    {
      id: 'north-africa-context',
      title: 'North Africa context',
      className: 'basemap-neighbor africa',
      coordinates: [
        [-10.0, 35.0],
        [4.5, 35.0],
        [4.5, 35.92],
        [2.0, 35.75],
        [-1.5, 35.86],
        [-4.8, 35.65],
        [-7.3, 35.95],
        [-10.0, 35.72],
        [-10.0, 35.0],
      ],
    },
    {
      id: 'balearic-islands',
      title: 'Balearic Islands',
      className: 'basemap-land island',
      coordinates: [
        [1.15, 39.98],
        [1.7, 40.12],
        [2.35, 39.82],
        [3.25, 39.95],
        [3.52, 39.48],
        [2.65, 39.28],
        [1.92, 39.42],
        [1.28, 39.3],
        [1.15, 39.98],
      ],
    },
  ];
  return shapes.map((shape) => ({ ...shape, points: projectPolygon(shape.coordinates, bbox, mapHeight) }));
}

function buildMapLabels(bbox, mapHeight) {
  const labels = [
    ['Spain', -3.5, 40.05, 'country'],
    ['Portugal', -8.1, 39.4, 'country'],
    ['France', 2.0, 43.72, 'neighbor'],
    ['North Africa', -3.1, 35.45, 'neighbor'],
    ['Atlantic Ocean', -8.1, 42.3, 'water'],
    ['Mediterranean Sea', 2.3, 38.25, 'water'],
    ['Iberian Peninsula', -4.5, 41.55, 'region'],
  ];
  return labels.map(([text, lon, lat, className]) => ({
    text,
    className,
    ...projectPoint(lon, lat, bbox, mapHeight),
  }));
}

function buildTicks(min, max, count) {
  const step = (max - min) / (count - 1);
  return Array.from({ length: count }, (_, index) => Number((min + step * index).toFixed(2)));
}

function formatCoord(value, axis) {
  const suffix = axis === 'lat' ? (value >= 0 ? 'N' : 'S') : value >= 0 ? 'E' : 'W';
  return `${Math.abs(value).toFixed(value % 1 === 0 ? 0 : 1)}°${suffix}`;
}
