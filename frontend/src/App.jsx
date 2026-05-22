import { useEffect, useMemo, useRef, useState } from 'react';
import 'leaflet/dist/leaflet.css';
import {
  exportUrl,
  getDemoScenarios,
  getEvidenceRun,
  getGbifStatus,
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
  online_with_empty_fallback: 'Live GBIF',
  fixture: 'Offline sample',
};

const liveSourceMode = 'online_with_empty_fallback';

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
      source_mode: 'online_with_empty_fallback',
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
      source_mode: 'online_with_empty_fallback',
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
      source_mode: 'online_with_empty_fallback',
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
    type: 'country',
    group: 'Saved countries',
    country_code: 'ES',
    featured: true,
  },
  {
    id: 'portugal',
    label: 'Portugal',
    region_name: 'Portugal live GBIF bbox',
    bbox: [-9.6, 36.8, -6, 42.2],
    description: 'Country bbox for Iberian biodiversity checks.',
    type: 'country',
    group: 'Saved countries',
    country_code: 'PT',
    featured: true,
  },
  {
    id: 'france',
    label: 'France',
    region_name: 'France live GBIF bbox',
    bbox: [-5.2, 41.3, 9.7, 51.2],
    description: 'Country bbox for Western Europe workflows.',
    type: 'country',
    group: 'Saved countries',
    country_code: 'FR',
    featured: true,
  },
  {
    id: 'western-europe',
    label: 'Western Europe',
    region_name: 'Western Europe live bbox',
    bbox: [-10, 42, 12, 56],
    description: 'Broader sampling-gap experiments.',
    type: 'research_region',
    group: 'Research regions',
    featured: true,
  },
  {
    id: 'mediterranean',
    label: 'Western Mediterranean',
    region_name: 'Western Mediterranean live bbox',
    bbox: [-6.5, 34.5, 16, 46.5],
    description: 'Invasive-watch corridor tests.',
    type: 'research_region',
    group: 'Research regions',
    featured: true,
  },
];

const tabs = [
  { id: 'overview', label: 'Decision Memo' },
  { id: 'map', label: 'Evidence Map' },
  { id: 'quality', label: 'Quality & Limits' },
  { id: 'gaps', label: 'Survey Priorities' },
  { id: 'claims', label: 'Safe Claims' },
  { id: 'citation', label: 'Citation & Lineage' },
  { id: 'publisher', label: 'Publisher Fixes' },
  { id: 'graph', label: 'Evidence Memory' },
  { id: 'submission', label: 'Submission Check' },
  { id: 'exports', label: 'Download Pack' },
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

const regionModeLabels = {
  country: 'Countries',
  research_region: 'Research',
  custom: 'Custom',
};

function normalizeForm(form) {
  const sourceMode = form.source_mode || (form.use_fixture === false ? 'online_with_empty_fallback' : 'fixture');
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
  if (west < -180 || east > 180 || south < -90 || north > 90) {
    throw new Error('Bounding box values must stay within longitude [-180, 180] and latitude [-90, 90]');
  }
  if (west >= east || south >= north) {
    throw new Error('Bounding box coordinates are not ordered as west,south,east,north');
  }
  return parts;
}

function bboxValidationMessage(text) {
  try {
    parseBbox(String(text || ''));
    return '';
  } catch (err) {
    return err.message || 'Bounding box is invalid';
  }
}

function payloadFromForm(form) {
  const sourceMode = form.source_mode || liveSourceMode;
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

function liveForm(form) {
  return normalizeForm({ ...form, source_mode: liveSourceMode, use_fixture: false });
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

function requestFingerprint(payload) {
  return requestSignature(payload);
}

function requestSignatureFromForm(form) {
  try {
    return requestFingerprint(payloadFromForm(normalizeForm(form)));
  } catch {
    return 'invalid-current-selection';
  }
}

function requestSignatureFromRun(request) {
  if (!request) return '';
  try {
    return requestFingerprint(payloadFromForm(normalizeForm(request)));
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

function bboxKey(value) {
  try {
    const bbox = Array.isArray(value) ? value : parseBbox(String(value || ''));
    return bbox.map((item) => Number(Number(item).toFixed(4))).join(',');
  } catch {
    return '';
  }
}

function regionType(region) {
  return region.type || (region.country_code ? 'country' : 'research_region');
}

function selectedRegionPreset(regions, form) {
  const key = bboxKey(form.bbox);
  const name = String(form.region_name || '').trim().toLowerCase();
  return regions.find((region) => bboxKey(region.bbox) === key && String(region.region_name || '').trim().toLowerCase() === name)
    || regions.find((region) => bboxKey(region.bbox) === key);
}

function regionMatchesQuery(region, query) {
  const cleanQuery = query.trim().toLowerCase();
  if (!cleanQuery) return true;
  return [region.label, region.region_name, region.description, region.country_code, region.group]
    .filter(Boolean)
    .some((value) => String(value).toLowerCase().includes(cleanQuery));
}

function regionBboxLabel(region) {
  return Array.isArray(region.bbox) ? formatBbox(region.bbox) : String(region.bbox || '');
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
  const [workspaceMode, setWorkspaceMode] = useState('presentation');
  const [gbifStatus, setGbifStatus] = useState({ status: 'degraded', message: 'Checking GBIF API status...', base_url: '' });
  const [recentRuns, setRecentRuns] = useState(readRecentRuns);
  const [progressSteps, setProgressSteps] = useState([]);
  const [taxonSuggestions, setTaxonSuggestions] = useState([]);
  const [taxonSearchStatus, setTaxonSearchStatus] = useState('');
  const [regionMode, setRegionMode] = useState('country');
  const [regionQuery, setRegionQuery] = useState('');
  const activeRunTokenRef = useRef(0);
  const bboxParts = bboxValues(form.bbox);
  const formSignature = requestSignatureFromForm(form);
  const runSignature = requestSignatureFromRun(run?.run?.request);
  const resultIsCurrent = Boolean(run && formSignature && runSignature && formSignature === runSignature);
  const selectionChanged = Boolean(run && !resultIsCurrent);
  const selectedRegion = selectedRegionPreset(regionPresets, form);
  const bboxError = bboxValidationMessage(form.bbox);
  const pendingSelection = selectionChanged || (!run && !loading && !booting);

  function clearVisibleResult() {
    setRun(null);
    setCreated(null);
    setProgressSteps([]);
    setActiveTab('overview');
  }

  function updateDraftForm(nextForm) {
    nextRunToken();
    setLoading(false);
    setBooting(false);
    setForm(normalizeForm(nextForm));
    clearVisibleResult();
    setError('');
  }

  function nextRunToken() {
    activeRunTokenRef.current += 1;
    return activeRunTokenRef.current;
  }

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
    nextRunToken();
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

  async function runPassport(formLike, options = {}) {
    const runToken = options.token || nextRunToken();
    const normalized = normalizeForm(formLike);
    const payload = payloadFromForm(normalized);
    setForm(normalized);
    if (options.clearBeforeRun) {
      clearVisibleResult();
    }
    setProgressSteps(buildProgressSteps('running'));
    const createdRun = await runEvidencePassport(payload);
    const detail = await getEvidenceRun(createdRun.run_id);
    if (runToken !== activeRunTokenRef.current) {
      return null;
    }
    setCreated(createdRun);
    setRun(detail);
    setActiveTab('overview');
    rememberRun(detail);
    await refreshRecentRuns();
    setProgressSteps(buildProgressSteps('completed', detail.run?.steps || []));
    return detail;
  }

  async function runSelection(nextForm) {
    const runToken = nextRunToken();
    const normalized = normalizeForm(nextForm);
    setError('');
    setLoading(true);
    setBooting(false);
    setForm(normalized);
    clearVisibleResult();
    try {
      return await runPassport(normalized, { token: runToken });
    } catch (err) {
      if (runToken === activeRunTokenRef.current) {
        setProgressSteps(buildProgressSteps('failed'));
        setError(err.message || 'Evidence run failed');
      }
      return null;
    } finally {
      if (runToken === activeRunTokenRef.current) {
        setLoading(false);
      }
    }
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
          // Fall through to the live preset, which can still produce an empty no-evidence fallback.
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
    await runSelection(liveForm(form));
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
    updateDraftForm(liveForm(preset.form));
  }

  function updateSourceMode(sourceMode) {
    updateDraftForm({ ...form, source_mode: sourceMode, use_fixture: sourceMode === 'fixture' });
  }

  useEffect(() => {
    let cancelled = false;
    async function loadGbifStatus() {
      try {
        const status = await getGbifStatus();
        if (!cancelled) setGbifStatus(status);
      } catch (err) {
        if (!cancelled) {
          setGbifStatus({
            status: 'unavailable',
            message: err.message || 'GBIF API status could not be checked.',
            base_url: '',
          });
        }
      }
    }
    loadGbifStatus();
    return () => {
      cancelled = true;
    };
  }, []);

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
    const nextForm = normalizeForm({
      ...form,
      taxon: name,
      taxon_key: suggestion.usageKey || '',
      source_mode: 'online_with_empty_fallback',
      use_fixture: false,
    });
    setTaxonSearchStatus(`Selected GBIF taxonKey ${suggestion.usageKey || 'unknown'}`);
    setTaxonSuggestions([]);
    void runSelection(nextForm);
  }

  function applyRegionPreset(region) {
    const nextForm = normalizeForm({
      ...form,
      region_name: region.region_name,
      bbox: formatBbox(region.bbox),
      source_mode: liveSourceMode,
      use_fixture: false,
    });
    setError('');
    setRegionMode(regionType(region));
    void runSelection(nextForm);
  }

  function updateBboxPart(index, value) {
    const next = [...bboxParts];
    next[index] = value;
    setRegionMode('custom');
    updateDraftForm({ ...liveForm(form), bbox: next.join(',') });
  }

  return (
    <main className="app-shell minimal-shell">
      <header className="topbar minimal-topbar">
        <div>
          <p className="eyebrow">EcoGenesis Evidence Atlas</p>
          <h1>GBIF Evidence Passport</h1>
          <p className="topbar-subtitle">
            A minimal GBIF-first tool that turns occurrence records into a decision memo, an evidence map and a downloadable review pack.
          </p>
        </div>
        <ModeSwitch mode={workspaceMode} onChange={setWorkspaceMode} />
      </header>

      {workspaceMode === 'presentation' ? (
        <PresentationView
          run={run}
          booting={booting || loading}
          gbifStatus={gbifStatus}
          onOpenWorkbench={() => setWorkspaceMode('work')}
          onRunCurrent={runCurrentSelection}
        />
      ) : (
        <section className="workspace workbench-layout">
          <aside className="run-rail minimal-rail" aria-label="Live GBIF workbench controls" data-testid="workbench-controls">
            <form className="rail-section run-form" onSubmit={handleSubmit}>
              <div className="form-intro">
                <p className="section-label">Work with GBIF</p>
                <p className="rail-copy">Search a GBIF taxon, choose a region, then generate a fresh live Evidence Passport.</p>
              </div>
              <SourceStatusCard status={gbifStatus} run={run} />
              <div className="taxon-picker">
                <label>
                  Taxon
                  <input
                    data-testid="taxon-input"
                    placeholder="Enter a species, genus or scientific name"
                    value={form.taxon}
                    onChange={(event) => {
                      setTaxonSuggestions([]);
                      setTaxonSearchStatus('');
                      updateDraftForm({ ...liveForm(form), taxon: event.target.value, taxon_key: '' });
                    }}
                  />
                </label>
                <button className="secondary-action" data-testid="taxon-search-button" type="button" onClick={handleTaxonSearch}>
                  Find taxon in GBIF
                </button>
                <div className="selected-taxon" aria-live="polite">
                  {form.taxon_key ? (
                    <span>Using GBIF taxonKey {form.taxon_key}</span>
                  ) : (
                    <span>The name will be matched by GBIF during the run.</span>
                  )}
                </div>
                {taxonSearchStatus ? <p className="helper-note">{taxonSearchStatus}</p> : null}
                {taxonSuggestions.length ? (
                  <div className="taxon-suggestion-list" aria-label="GBIF taxon suggestions">
                    {taxonSuggestions.map((suggestion) => (
                      <button
                        aria-label={`Select GBIF taxon ${suggestion.canonicalName || suggestion.scientificName} taxonKey ${suggestion.usageKey || 'unknown'}`}
                        data-testid={`taxon-suggestion-${suggestion.usageKey || 'unknown'}`}
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
                  data-testid="region-name-input"
                  value={form.region_name}
                  onChange={(event) => {
                    setRegionMode('custom');
                    updateDraftForm({ ...liveForm(form), region_name: event.target.value });
                  }}
                />
              </label>
              <RegionPicker
                form={form}
                mode={regionMode}
                onModeChange={setRegionMode}
                onPick={applyRegionPreset}
                query={regionQuery}
                regions={regionPresets}
                selectedRegion={selectedRegion}
                setQuery={setRegionQuery}
              />
              <fieldset className="bbox-grid">
                <legend>Bounding box</legend>
                <label>
                  West
                  <input
                    aria-label="West longitude"
                    data-testid="bbox-west"
                    value={bboxParts[0]}
                    onChange={(event) => updateBboxPart(0, event.target.value)}
                  />
                </label>
                <label>
                  South
                  <input
                    aria-label="South latitude"
                    data-testid="bbox-south"
                    value={bboxParts[1]}
                    onChange={(event) => updateBboxPart(1, event.target.value)}
                  />
                </label>
                <label>
                  East
                  <input
                    aria-label="East longitude"
                    data-testid="bbox-east"
                    value={bboxParts[2]}
                    onChange={(event) => updateBboxPart(2, event.target.value)}
                  />
                </label>
                <label>
                  North
                  <input
                    aria-label="North latitude"
                    data-testid="bbox-north"
                    value={bboxParts[3]}
                    onChange={(event) => updateBboxPart(3, event.target.value)}
                  />
                </label>
              </fieldset>
              {bboxError ? <p className="field-error" data-testid="bbox-error">{bboxError}</p> : null}
              <div className="field-pair">
                <label>
                  Purpose
                  <select
                    data-testid="purpose-select"
                    value={form.purpose}
                    onChange={(event) => updateDraftForm({ ...liveForm(form), purpose: event.target.value })}
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
                    data-testid="max-records-input"
                    min="1"
                    type="number"
                    value={form.max_records}
                    onChange={(event) => updateDraftForm({ ...liveForm(form), max_records: event.target.value })}
                  />
                </label>
              </div>
              {pendingSelection && !bboxError ? (
                <div className="pending-change-bar" data-testid="pending-change-bar">
                  <span>Pending changes</span>
                  <strong>Generate to refresh the map and memo.</strong>
                </div>
              ) : null}
              <button className="primary-action" data-testid="generate-live-button" type="submit" disabled={loading || booting || Boolean(bboxError)}>
                {loading ? 'Generating live passport...' : booting ? 'Preparing passport...' : 'Generate live Evidence Passport'}
              </button>
              {error ? <p className="error">{error}</p> : null}
              {created ? <p className="run-id">Run {created.run_id}</p> : null}
            </form>

            <details className="rail-section drawer-section" data-testid="developer-testing-drawer">
              <summary aria-label="Developer testing details">Developer/testing</summary>
              <p className="rail-copy">Offline fixture mode remains available through the API and tests. The public workbench always sends live GBIF requests.</p>
            </details>
          </aside>

          <MinimalPassport
            run={run}
            booting={booting}
            selectionChanged={selectionChanged}
            loading={loading}
            onRunCurrent={runCurrentSelection}
          />
        </section>
      )}
    </main>
  );
}

function ModeSwitch({ mode, onChange }) {
  return (
    <nav className="mode-switch" aria-label="Workspace mode">
      {[
        ['presentation', 'Presentation'],
        ['work', 'Work with GBIF'],
      ].map(([value, label]) => (
        <button
          aria-pressed={mode === value}
          className={mode === value ? 'active' : ''}
          data-testid={`mode-${value}`}
          key={value}
          onClick={() => onChange(value)}
          type="button"
        >
          {label}
        </button>
      ))}
    </nav>
  );
}

function PresentationView({ run, booting, gbifStatus, onOpenWorkbench, onRunCurrent }) {
  if (booting) {
    return <LoadingWorkbench booting live />;
  }
  if (!run) {
    return (
      <section className="presentation-page">
        <DraftWorkbench onRunCurrent={onRunCurrent} />
      </section>
    );
  }
  const zip = run.exports?.find((item) => item.name === 'evidence_pack.zip');
  const memo = run.decision_memo;
  return (
    <section className="presentation-page" aria-label="Contest presentation">
      <div className="presentation-hero">
        <div>
          <p className="eyebrow">GBIF-first evidence tool</p>
          <h2>From occurrence records to a defensible decision memo</h2>
          <p>
            EcoGenesis Evidence Atlas helps judges, researchers and data managers see what GBIF-mediated records can
            support, what they cannot support, and what must be cited or checked next.
          </p>
          <div className="hero-actions">
            <button className="primary-action" type="button" onClick={onOpenWorkbench}>Open Workbench</button>
            {zip ? <a className="zip-action" href={exportUrl(zip.url)}>Download Evidence Pack</a> : null}
          </div>
        </div>
        <div className="presentation-verdict">
          <span>Current verdict</span>
          <strong>{memo?.verdict || readinessStatus(run.evidence_readiness.score).label}</strong>
          <small>{run.passport.taxon} · {run.passport.region_name}</small>
        </div>
      </div>

      <div className="presentation-grid">
        <SourceStatusCard status={gbifStatus} run={run} />
        <DecisionMemoPanel run={run} />
        <MapPreview run={run} />
        <ClaimSnapshot run={run} />
        <AdvancedEvidenceFiles exports={run.exports || []} />
      </div>
    </section>
  );
}

function MinimalPassport({ run, booting, selectionChanged = false, loading = false, onRunCurrent }) {
  if (loading) {
    return <LoadingWorkbench booting={false} live />;
  }
  if (!run) {
    return booting ? <LoadingWorkbench booting={booting} /> : <DraftWorkbench onRunCurrent={onRunCurrent} />;
  }
  if (selectionChanged) {
    return <DraftWorkbench onRunCurrent={onRunCurrent} />;
  }

  const readiness = run.evidence_readiness;
  const zip = run.exports?.find((item) => item.name === 'evidence_pack.zip');
  const status = readinessStatus(readiness.score);
  return (
    <section className="result-stack minimal-result" aria-label="Live GBIF Evidence Passport result">
      <div className={`score-band ${scoreClass(readiness.score)}`}>
        <div>
          <p className="eyebrow">Live GBIF result</p>
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
      <DecisionMemoPanel run={run} />
      <MapPreview run={run} />
      <div className="workbench-summary-grid">
        <ListPanel title="Key risks" rows={run.main_risks.slice(0, 4)} tone="risk" />
        <ClaimSnapshot run={run} />
        <SourceProvenance run={run} compact />
        <GapPriorityPanel run={run} compact />
      </div>
      <AdvancedEvidenceFiles exports={run.exports || []} />
    </section>
  );
}

function SourceStatusCard({ status, run }) {
  const source = run?.source_summary || {};
  const taxonKey = run?.passport?.taxonKey || source.selected_taxon_key || source.matched_taxon_key || 'not selected';
  const fallbackUsed = Boolean(source.fallback_used);
  const message = fallbackUsed && source.used_source_mode === 'online_empty_fallback'
    ? 'GBIF unavailable: no fixture records reused.'
    : status?.message || 'GBIF status is being checked.';
  const rows = [
    ['GBIF status', status?.status || 'checking'],
    ['Source used', shortStatus(source.used_source_mode || liveSourceMode)],
    ['Returned records', source.gbif_returned_records ?? run?.passport?.records_used ?? 'pending'],
    ['Fallback used', fallbackUsed ? 'yes' : 'no'],
    ['Selected taxonKey', taxonKey],
  ];
  return (
    <section className={`panel source-status-card ${status?.status || 'degraded'}`}>
      <div className="panel-title">
        <h3>Live GBIF status</h3>
        <span>{status?.base_url || source.gbif_base_url || 'api.gbif.org'}</span>
      </div>
      <p className={fallbackUsed ? 'fallback-note' : 'source-status-message'}>{message}</p>
      <div className="source-grid compact-source-grid">
        {rows.map(([label, value]) => (
          <div key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}

function ClaimSnapshot({ run }) {
  const supported = run.claim_guardrails?.supported_claims?.slice(0, 2) || [];
  const blocked = run.claim_guardrails?.unsupported_claims?.slice(0, 3) || [];
  return (
    <section className="panel claim-snapshot">
      <div className="panel-title">
        <h3>Safe and blocked claims</h3>
        <span>bounded interpretation</span>
      </div>
      <div className="claim-columns">
        <div>
          <h4>Safe claims</h4>
          <ul>{supported.map((claim) => <li key={claim}>{claim}</li>)}</ul>
        </div>
        <div>
          <h4>Blocked claims</h4>
          <ul>{blocked.map((claim) => <li key={claim}>{claim}</li>)}</ul>
        </div>
      </div>
      <p className="provenance-note">No-evidence cells are survey targets, not absence observations.</p>
    </section>
  );
}

function AdvancedEvidenceFiles({ exports }) {
  const primaryNames = ['evidence_pack.zip', 'passport.html', 'decision_memo.md', 'citations.md'];
  const primary = primaryNames.map((name) => exports.find((item) => item.name === name)).filter(Boolean);
  const groups = groupExports(exports).map((group) => ({
    ...group,
    files: group.files.filter((item) => !primaryNames.includes(item.name)),
  })).filter((group) => group.files.length);
  return (
    <details className="panel advanced-files" data-testid="advanced-evidence-files">
      <summary aria-label="Advanced evidence files">Advanced evidence files</summary>
      <h4>Quick downloads</h4>
      <div className="quick-export-list">
        {primary.map((item) => (
          <a
            className={item.name === 'evidence_pack.zip' ? 'zip-download' : ''}
            data-testid={`export-${item.name}`}
            key={item.name}
            href={exportUrl(item.url)}
          >
            <span>{item.name === 'evidence_pack.zip' ? 'Evidence pack ZIP' : item.name}</span>
            <small>{formatBytes(item.size_bytes)}</small>
          </a>
        ))}
      </div>
      <h4>All evidence files</h4>
      <div className="advanced-export-groups">
        {groups.map((group) => (
          <div className="export-group" key={group.title}>
            <h4>{group.title}</h4>
            <div className="export-list compact">
              {group.files.map((item) => (
                <a data-testid={`export-${item.name}`} key={item.name} href={exportUrl(item.url)}>
                  <span>{item.name}</span>
                  <small>{formatBytes(item.size_bytes)}</small>
                </a>
              ))}
            </div>
          </div>
        ))}
      </div>
    </details>
  );
}

function RecentRuns({ runs, loadingRunId, onLoad }) {
  return (
    <details className="rail-section drawer-section recent-runs">
      <summary>Recent evidence passports</summary>
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
      <summary>Run evidence chain</summary>
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

function RegionPicker({ form, mode, onModeChange, onPick, query, regions, selectedRegion, setQuery }) {
  const customActive = !selectedRegion || mode === 'custom';
  const visibleRegions = regions
    .filter((region) => regionType(region) === mode)
    .filter((region) => regionMatchesQuery(region, query))
    .sort((a, b) => Number(Boolean(b.featured)) - Number(Boolean(a.featured)) || String(a.label).localeCompare(String(b.label)));

  return (
    <section className="region-picker" aria-label="Region manager">
      <div className="region-current">
        <div>
          <span>{selectedRegion ? selectedRegion.group || 'Saved region' : 'Custom area'}</span>
          <strong>{selectedRegion?.label || form.region_name || 'Custom bbox'}</strong>
          <small>{regionBboxLabel(selectedRegion || form)}</small>
        </div>
        <em>{customActive ? 'custom' : 'saved'}</em>
      </div>
      <div className="region-tabs" aria-label="Region source">
        {Object.entries(regionModeLabels).map(([value, label]) => (
          <button
            aria-label={`Show ${label.toLowerCase()} region presets`}
            aria-pressed={mode === value}
            className={mode === value ? 'active' : ''}
            data-testid={`region-tab-${value}`}
            key={value}
            onClick={() => onModeChange(value)}
            type="button"
          >
            {label}
          </button>
        ))}
      </div>
      {mode === 'custom' ? (
        <div className="custom-region-note">
          <strong>Custom area selected</strong>
          <span>Edit the region name and bbox fields below, then generate the passport. Saved presets stay untouched.</span>
        </div>
      ) : (
        <>
          <input
            aria-label="Search saved regions"
            className="region-search"
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search countries or saved regions"
            value={query}
          />
          <div className="region-preset-list" aria-label="Region presets">
            {visibleRegions.map((region) => {
              const active = selectedRegion?.id === region.id;
              return (
                <button
                  aria-label={`Select region ${region.label} (${region.region_name})`}
                  className={active ? 'active' : ''}
                  data-testid={`region-preset-${region.id}`}
                  key={region.id}
                  onClick={() => onPick(region)}
                  type="button"
                >
                  <span>
                    {region.country_code ? `${region.country_code} · ` : ''}
                    {region.label}
                  </span>
                  <small>{region.description}</small>
                  <em>{regionBboxLabel(region)}</em>
                </button>
              );
            })}
          </div>
          {!visibleRegions.length ? <p className="empty-note">No saved regions match this search.</p> : null}
        </>
      )}
    </section>
  );
}

function Passport({ run, booting, activeTab, setActiveTab, selectionChanged = false, loading = false, onRunCurrent }) {
  if (loading) {
    return <LoadingWorkbench booting={false} live />;
  }
  if (!run) {
    return booting ? <LoadingWorkbench booting={booting} /> : <DraftWorkbench onRunCurrent={onRunCurrent} />;
  }
  if (selectionChanged) {
    return <DraftWorkbench onRunCurrent={onRunCurrent} />;
  }

  const readiness = run.evidence_readiness;
  const zip = run.exports?.find((item) => item.name === 'evidence_pack.zip');
  const status = readinessStatus(readiness.score);
  return (
    <section className="result-stack" aria-label="Evidence Passport result">
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
        <GraphMemorySummary run={run} />
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

function DraftWorkbench({ onRunCurrent }) {
  return (
    <section className="empty-workbench draft-workbench" role="status">
      <div>
        <p className="eyebrow">Not generated for this selection yet</p>
        <h2>Generate a fresh passport to update the map</h2>
        <p>
          The previous map has been hidden so old points and records cannot be confused with the current taxon or region.
        </p>
      </div>
      <button className="primary-action" type="button" onClick={onRunCurrent}>
        Generate this selection
      </button>
      <div className="skeleton-grid" aria-label="Pending Evidence Passport">
        {['New run id', 'Fresh GBIF match', 'Updated map', 'Updated records', 'New score', 'New exports'].map((item) => (
          <span key={item}>{item}</span>
        ))}
      </div>
    </section>
  );
}

function LoadingWorkbench({ booting, live = false }) {
  return (
    <section className="empty-workbench">
      <div>
        <p className="eyebrow">{live ? 'Live GBIF run' : 'Evidence workspace'}</p>
        <h2>
          {live
            ? 'Generating live GBIF passport for this selection'
            : booting
              ? 'Preparing the default Evidence Passport'
              : 'Evidence Passport is ready to run'}
        </h2>
        <p>
          {live
            ? 'The old result is hidden while the app builds a new map, score, citations and exports for the selected taxon and region.'
            : 'The default flow uses live GBIF data and keeps offline sample data as a separate reproducible example.'}
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
      {source.used_source_mode === 'online_empty_fallback' ? (
        <p className="provenance-note">No old fixture records were reused for this live query.</p>
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
  if (activeTab === 'graph') return <GraphMemoryPanel run={run} />;
  if (activeTab === 'submission') return <SubmissionPanel run={run} />;
  if (activeTab === 'exports') return <ExportsPanel exports={run.exports || []} />;
  return <OverviewPanel run={run} />;
}

function OverviewPanel({ run }) {
  const status = readinessStatus(run.evidence_readiness.score);
  const supported = run.claim_guardrails.supported_claims.slice(0, 2);
  const unsupported = run.claim_guardrails.unsupported_claims.slice(0, 2);
  return (
    <div className="overview-grid">
      <DecisionMemoPanel run={run} />
      <section className={`panel readiness-status ${scoreClass(run.evidence_readiness.score)}`}>
        <div className="panel-title">
          <h3>Fitness summary</h3>
          <span>{status.label}</span>
        </div>
        <p>{status.description}</p>
        <p className="score-caveat">This score is a decision-support heuristic, not a biological truth or model prediction.</p>
      </section>
      <ListPanel title="What this supports" rows={supported} tone="supported" />
      <ListPanel title="What this does not support" rows={unsupported} tone="unsupported" />
      <ListPanel title="Main risks" rows={run.main_risks} tone="risk" />
      <ListPanel title="Next actions" rows={run.next_actions} tone="action" />
      <GraphMemorySummary run={run} />
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

function DecisionMemoPanel({ run }) {
  const memo = run.decision_memo;
  if (!memo) return null;
  const gate = memo.citation_gate || {};
  const grid = memo.grid_gate || {};
  return (
    <section className={`panel decision-memo-panel span-two ${memo.verdict_tone || ''}`}>
      <div className="panel-title">
        <h3>Decision memo</h3>
        <span>{memo.review_time_seconds || 40}-second review</span>
      </div>
      <div className="decision-verdict">
        <span>{humanize(memo.verdict_tone || 'verdict')}</span>
        <strong>{memo.verdict}</strong>
      </div>
      <div className="decision-grid">
        <div>
          <span>Question</span>
          <p>{memo.question}</p>
        </div>
        <div>
          <span>Evidence basis</span>
          <p>{memo.data_basis}</p>
        </div>
        <div>
          <span>Fitness</span>
          <p>{memo.fitness_for_purpose}</p>
        </div>
        <div>
          <span>Next action</span>
          <p>{memo.recommended_next_action}</p>
        </div>
      </div>
      <div className="decision-footer">
        <span>{gate.publication_ready ? 'Publication citation ready' : 'DOI/derived dataset still needed'}</span>
        <span>{grid.no_evidence_cells ?? 0} no-evidence cells</span>
        <span>{grid.survey_priority_cells ?? 0} survey priorities</span>
      </div>
    </section>
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
        <h4>DOI completion flow</h4>
        <div className="doi-flow">
          {(citation.doi_completion_flow || []).map((item) => (
            <div className={item.ready ? 'ready' : 'pending'} key={item.label}>
              <span>{item.ready ? 'Ready' : 'Needs action'}</span>
              <strong>{item.label}</strong>
              <small>{item.action}</small>
            </div>
          ))}
        </div>
        {citation.journal_methods_text ? (
          <>
            <h4>Journal-ready methods text</h4>
            <p>{citation.journal_methods_text}</p>
          </>
        ) : null}
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
              <th>Priority</th>
              <th>Severity</th>
              <th>Records affected</th>
              <th>Main issue</th>
              <th>Suggested fix</th>
            </tr>
          </thead>
          <tbody>
            {feedback.map((row) => (
              <tr key={`${row.datasetKey}-${row.main_issue}`}>
                <td>{row.datasetKey}</td>
                <td>{row.fix_priority || 'n/a'}</td>
                <td><span className={`severity-pill ${row.severity || 'unknown'}`}>{row.severity || 'unknown'}</span></td>
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

function GraphMemorySummary({ run }) {
  const graph = run.graph_memory?.graph;
  if (!graph) return null;
  const counts = graph.node_counts || {};
  const items = [
    ['Datasets', counts.datasets || 0],
    ['Issues', counts.issues || 0],
    ['Claims', counts.claims || 0],
    ['Actions', counts.actions || 0],
  ];
  return (
    <section className="panel graph-summary-panel">
      <div className="panel-title">
        <h3>Graph Memory</h3>
        <span>this run is stored as a connected evidence node</span>
      </div>
      <div className="graph-count-grid">
        {items.map(([label, value]) => (
          <div key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
      <p className="graph-note">The vault links this run to taxa, region, datasets, issues, claims, actions and citation methods.</p>
    </section>
  );
}

function GraphMemoryPanel({ run }) {
  const graph = run.graph_memory?.graph;
  const vaultExport = run.exports?.find((item) => item.name === 'evidence_vault.zip');
  const graphExport = run.exports?.find((item) => item.name === 'evidence_graph.json');
  if (!graph) {
    return (
      <section className="panel">
        <h3>Graph Memory</h3>
        <p className="empty-note">This run does not include graph memory yet.</p>
      </section>
    );
  }
  return (
    <div className="graph-memory-grid">
      <section className="panel graph-hero">
        <div className="panel-title">
          <h3>Connected evidence memory</h3>
          <span>{graph.edges.length} graph edges</span>
        </div>
        <p>
          This passport is stored as a portable evidence graph, so later runs can reuse its datasets, issues,
          blocked claims, citation state and next actions instead of starting from a blank report.
        </p>
        <div className="graph-actions">
          {vaultExport ? <a href={exportUrl(vaultExport.url)}>Download evidence vault</a> : null}
          {graphExport ? <a href={exportUrl(graphExport.url)}>Download evidence graph</a> : null}
        </div>
      </section>
      <section className="panel">
        <div className="panel-title">
          <h3>Node counts</h3>
          <span>human-readable memory model</span>
        </div>
        <div className="graph-count-grid expanded">
          {Object.entries(graph.node_counts || {}).map(([label, value]) => (
            <div key={label}>
              <span>{humanize(label)}</span>
              <strong>{value}</strong>
            </div>
          ))}
        </div>
      </section>
      <section className="panel span-two">
        <div className="panel-title">
          <h3>Memory cards</h3>
          <span>what the graph adds</span>
        </div>
        <div className="memory-card-grid">
          {(graph.memory_cards || []).map((card) => (
            <article key={card.title}>
              <h4>{card.title}</h4>
              <p>{card.body}</p>
            </article>
          ))}
        </div>
      </section>
      <section className="panel span-two">
        <div className="panel-title">
          <h3>Key relationships</h3>
          <span>{graph.edges.length} total edges</span>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Source</th>
                <th>Relation</th>
                <th>Target</th>
              </tr>
            </thead>
            <tbody>
              {graph.edges.slice(0, 18).map((edge) => (
                <tr key={`${edge.source}-${edge.relation}-${edge.target}`}>
                  <td>{edge.source}</td>
                  <td>{humanize(edge.relation)}</td>
                  <td>{edge.target}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function SubmissionPanel({ run }) {
  const readiness = run.submission_readiness;
  const validation = run.validation_summary;
  const memo = run.decision_memo;
  if (!readiness || !validation) {
    return (
      <section className="panel">
        <h3>Submission check</h3>
        <p className="empty-note">This run does not include submission readiness metadata yet.</p>
      </section>
    );
  }
  const readyPct = Math.round((readiness.ready_ratio || 0) * 100);
  return (
    <div className="submission-grid">
      <section className="panel submission-hero">
        <div className="panel-title">
          <h3>Submission readiness</h3>
          <span>{readiness.ready_count}/{readiness.total_count} checks ready</span>
        </div>
        <div className="submission-score">
          <strong>{readyPct}%</strong>
          <span>{readiness.stage}</span>
        </div>
        <p>{memo?.plain_language_summary}</p>
      </section>
      <section className="panel">
        <div className="panel-title">
          <h3>Accepted research comments</h3>
          <span>{readiness.accepted_research_comments?.length || 0} integrated</span>
        </div>
        <ul className="compact-list">
          {(readiness.accepted_research_comments || []).map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>
      <section className="panel span-two">
        <div className="panel-title">
          <h3>Contest checklist</h3>
          <span>{readiness.blocking_items?.length ? `${readiness.blocking_items.length} blocker(s)` : 'ready for demo review'}</span>
        </div>
        <div className="checklist-grid">
          {(readiness.checklist || []).map((item) => (
            <article className={item.ready ? 'ready' : 'pending'} key={item.id}>
              <span>{item.ready ? 'Ready' : 'Needs work'}</span>
              <h4>{item.label}</h4>
              <p>{item.evidence}</p>
              <small>{item.next_step}</small>
            </article>
          ))}
        </div>
      </section>
      <section className="panel">
        <div className="panel-title">
          <h3>Validation checks</h3>
          <span>{validation.passed_checks}/{validation.total_checks} passed</span>
        </div>
        <div className="doi-flow validation-flow">
          {(validation.checks || []).map((check) => (
            <div className={check.passed ? 'ready' : 'pending'} key={check.id}>
              <span>{check.passed ? 'Passed' : 'Review'}</span>
              <strong>{check.label}</strong>
              <small>{check.why_it_matters}</small>
            </div>
          ))}
        </div>
      </section>
      <section className="panel">
        <div className="panel-title">
          <h3>Demo suite</h3>
          <span>three judge-friendly cases</span>
        </div>
        <div className="demo-suite-list">
          {(validation.recommended_demo_suite || []).map((scenario) => (
            <article key={scenario.id}>
              <strong>{scenario.taxon}</strong>
              <span>{scenario.region_name}</span>
              <small>{scenario.shows}</small>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}

function ExportsPanel({ exports }) {
  const groups = groupExports(exports);
  const checklist = [
    ['Decision memo', 'decision_memo.md'],
    ['Standalone report', 'passport.html'],
    ['Citation pack', 'citations.md'],
    ['Map data', 'records.geojson'],
    ['Gap priorities', 'gap_priorities.csv'],
    ['Publisher feedback', 'publisher_feedback.md'],
    ['Provenance manifest', 'provenance.json'],
    ['Graph memory', 'evidence_graph.json'],
    ['Submission check', 'submission_readiness.md'],
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
          <button
            aria-label={`Toggle ${label} map layer`}
            aria-pressed={layers[name]}
            className={layers[name] ? 'active' : ''}
            data-testid={`map-layer-${name}`}
            key={name}
            onClick={() => toggleLayer(name)}
            type="button"
          >
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
    { title: 'Graph Memory', names: ['evidence_vault.zip', 'evidence_graph.json', 'graph_memory.md'] },
    { title: 'Submission Kit', names: ['decision_memo.md', 'submission_readiness.md', 'validation_summary.md', 'impact_brief.md', 'video_script.md'] },
    { title: 'Machine-readable', names: ['evidence_pack.json', 'decision_memo.json', 'submission_readiness.json', 'validation_summary.json', 'run.json', 'source_summary.json', 'demo_scenario.json', 'derived_dataset_recipe.json', 'provenance.json'] },
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
  const labels = {
    fixture: 'offline sample',
    online: 'live GBIF',
    online_with_empty_fallback: 'live GBIF',
    online_empty_fallback: 'empty live fallback',
    online_with_fixture_fallback: 'legacy fixture fallback',
    fixture_fallback: 'fixture fallback',
  };
  if (labels[value]) return labels[value];
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
