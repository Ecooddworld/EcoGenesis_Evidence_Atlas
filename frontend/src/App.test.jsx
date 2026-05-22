import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import App from './App.jsx';

const mockScenarios = [
  {
    id: 'invasive',
    label: 'Invasive watch',
    tag: 'recency weighted',
    form: {
      taxon: 'Aedes albopictus',
      region_name: 'Spain demo bbox',
      bbox: [-10, 35, 4.5, 44.5],
      purpose: 'invasive_watch',
      source_mode: 'online_with_empty_fallback',
      use_fixture: false,
      max_records: 300,
    },
  },
];

const mockRegions = [
  {
    id: 'iberian',
    label: 'Iberian Peninsula',
    region_name: 'Iberian Peninsula live bbox',
    bbox: [-10, 35, 4.5, 44.5],
    description: 'Useful for Iberian conservation tests.',
    type: 'research_region',
    group: 'Research regions',
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
];

const mockTaxa = [
  {
    usageKey: 2435261,
    canonicalName: 'Lynx pardinus',
    scientificName: 'Lynx pardinus (Temminck, 1827)',
    rank: 'SPECIES',
    family: 'Felidae',
  },
];

const mockRun = {
  run: {
    run_id: 'demo123',
    finished_at: '2026-04-26T10:00:00Z',
    source_mode: 'fixture',
    gbif_species_match: { usageKey: 1651430, confidence: 97 },
    request: {
      taxon: 'Aedes albopictus',
      taxon_key: null,
      region_name: 'Spain demo bbox',
      bbox: [-10, 35, 4.5, 44.5],
      purpose: 'invasive_watch',
      source_mode: 'fixture',
      max_records: 300,
    },
    steps: [
      { name: 'species_match', status: 'completed', duration_ms: 1.2 },
      { name: 'occurrence_fetch', status: 'completed', duration_ms: 2.4 },
      { name: 'exports', status: 'completed', duration_ms: 3.1 },
    ],
  },
  passport: {
    taxon: 'Aedes albopictus',
    region_name: 'Spain demo bbox',
    bbox: [-10, 35, 4.5, 44.5],
    records_used: 12,
    datasets_used: 4,
    taxonKey: 1651430,
    match_confidence: 97,
  },
  source_summary: {
    requested_source_mode: 'fixture',
    used_source_mode: 'fixture',
    gbif_api_status: 'not_called',
    fallback_used: false,
    warnings: [],
  },
  evidence_readiness: {
    purpose: 'invasive_watch',
    purpose_label: 'Invasive watch',
    score: 72,
    interpretation: 'Moderate readiness: useful evidence, but caveats and verification steps matter.',
    components: {
      spatial_accuracy: 96,
      temporal_recency: 60,
      taxonomic_confidence: 98,
      sampling_coverage: 57,
      citation_provenance: 100,
      issue_explainability: 100,
    },
    weights: {
      spatial_accuracy: 0.25,
      temporal_recency: 0.35,
      taxonomic_confidence: 0.15,
      sampling_coverage: 0.15,
      citation_provenance: 0.1,
      issue_explainability: 0,
    },
  },
  purpose_score_matrix: {
    conservation_brief: { purpose: 'conservation_brief', purpose_label: 'Conservation brief', score: 74, interpretation: 'Moderate readiness.' },
    invasive_watch: { purpose: 'invasive_watch', purpose_label: 'Invasive watch', score: 72, interpretation: 'Moderate readiness.' },
    sampling_gaps: { purpose: 'sampling_gaps', purpose_label: 'Sampling gap analysis', score: 58, interpretation: 'Limited readiness.' },
    dataset_quality_review: { purpose: 'dataset_quality_review', purpose_label: 'Dataset quality review', score: 84, interpretation: 'High readiness.' },
  },
  quality_metrics: {
    total_records: 12,
    valid_coordinate_rate: 1,
    date_present_rate: 0.83,
    recent_record_rate: 0.5,
    taxon_key_rate: 1,
    dataset_key_rate: 1,
    license_rate: 1,
    high_uncertainty_rate: 0.17,
    missing_date_count: 2,
    high_uncertainty_count: 2,
    invalid_coordinate_count: 0,
    country_coordinate_mismatch_count: 1,
  },
  grid_metrics: {
    type: 'FeatureCollection',
    meta: {
      cell_count: 16,
      occupied_cell_count: 1,
      empty_cell_count: 15,
      under_sampled_occupied_cells: 1,
      survey_priority_cells: 16,
      method: 'Taxon-focused grid: occurrence density and sampling coverage proxy.',
    },
    features: [
      {
        geometry: {
          type: 'Polygon',
          coordinates: [[[-10, 35], [-6.375, 35], [-6.375, 37.375], [-10, 37.375], [-10, 35]]],
        },
        properties: {
          cell_id: 'grid:4:0:0',
          occurrence_count: 0,
          sampling_coverage_proxy: 0,
          non_detection_risk: 1,
          empty_cell: true,
          under_sampled: false,
        },
      },
      {
        geometry: {
          type: 'Polygon',
          coordinates: [[[0.875, 39.75], [4.5, 39.75], [4.5, 42.125], [0.875, 42.125], [0.875, 39.75]]],
        },
        properties: {
          cell_id: 'grid:4:3:2',
          occurrence_count: 1,
          sampling_coverage_proxy: 0.2,
          non_detection_risk: 0.7,
          empty_cell: false,
          under_sampled: true,
        },
      },
    ],
  },
  main_risks: ['No GBIF download DOI is attached to this evidence pack yet.'],
  next_actions: ['Create a DOI-backed GBIF occurrence download or derived dataset before publication.'],
  claim_guardrails: {
    supported_claims: ['GBIF-mediated records matching the selected taxon and region are present.'],
    weak_claims: ['Record clusters can indicate areas of observation activity.'],
    unsupported_claims: ['Absence cannot be inferred from grid cells with no or few records.'],
    required_verification: ['Create a DOI-backed GBIF occurrence download before formal publication.'],
  },
  citation_autopilot: {
    citation_status: 'fixture_demo_not_for_publication',
    dataset_count: 1,
    gbif_download_warning: 'This evidence pack does not include a GBIF download DOI.',
    methods_text: 'Occurrence evidence was assembled from GBIF-mediated records.',
    derived_dataset_recipe: {
      group_by: 'datasetKey',
      include_counts: true,
      preserve_fields: ['datasetKey', 'gbifID', 'eventDate'],
    },
    doi_completion_flow: [
      { label: 'datasetKey provenance preserved', ready: true, action: 'Keep datasetKey in exports.' },
      { label: 'GBIF download DOI or derived dataset attached', ready: false, action: 'Create DOI-backed evidence before publication.' },
    ],
    journal_methods_text: 'GBIF-mediated occurrence-style records were queried and retained with datasetKey provenance.',
  },
  publisher_feedback: [
    {
      datasetKey: 'spain-mosquito-watch',
      fix_priority: 1,
      severity: 'medium',
      records_affected: 1,
      main_issue: 'High coordinate uncertainty',
      suggested_fix: 'Improve georeferencing.',
    },
  ],
  dataset_contributions: [
    {
      datasetKey: 'spain-mosquito-watch',
      record_count: 4,
      license: 'CC_BY_4_0',
      main_issues: 'none_detected',
    },
  ],
  decision_memo: {
    verdict: 'Usable for screening, but not enough for fine-scale or publication claims without review',
    verdict_tone: 'limited',
    review_time_seconds: 40,
    question: "Can GBIF-mediated occurrence evidence for Aedes albopictus in Spain demo bbox support the purpose 'Invasive watch'?",
    data_basis: '12 retained occurrence-style records from GBIF-style evidence.',
    fitness_for_purpose: 'The purpose-aware readiness score is 72/100.',
    safe_claims: ['GBIF-mediated records matching the selected taxon and region are present.'],
    blocked_claims: ['Absence cannot be inferred from grid cells with no or few records.'],
    main_limitations: ['No GBIF download DOI is attached to this evidence pack yet.'],
    recommended_next_action: 'Create a DOI-backed GBIF occurrence download or derived dataset before publication.',
    plain_language_summary: 'The passport is a decision memo, not a species distribution model.',
    user_value: ['A non-expert can see the safe conclusion.'],
    citation_gate: {
      publication_ready: false,
      status: 'fixture_demo_not_for_publication',
      message: 'This evidence pack does not include a GBIF download DOI.',
    },
    grid_gate: {
      no_evidence_cells: 15,
      survey_priority_cells: 16,
      under_sampled_occupied_cells: 1,
    },
  },
  validation_summary: {
    title: 'EcoGenesis Validation Summary',
    passed_checks: 5,
    total_checks: 5,
    checks: [
      { id: 'datasetkey_provenance', label: 'datasetKey provenance preserved', passed: true, metric: 1, why_it_matters: 'GBIF reuse needs lineage.' },
      { id: 'citation_flow', label: 'Citation completion flow generated', passed: true, metric: 2, why_it_matters: 'Users get DOI steps.' },
    ],
    recommended_demo_suite: [
      { id: 'invasive_watch', taxon: 'Aedes albopictus', region_name: 'Spain live GBIF bbox', purpose: 'invasive_watch', shows: 'Recent invasive screening.' },
      { id: 'sampling_gaps', taxon: 'Quercus robur', region_name: 'Western Europe live bbox', purpose: 'sampling_gaps', shows: 'Survey priorities.' },
      { id: 'dataset_quality_review', taxon: 'Lynx pardinus', region_name: 'Iberian Peninsula live bbox', purpose: 'dataset_quality_review', shows: 'Publisher fixes.' },
    ],
  },
  submission_readiness: {
    title: 'GBIF Ebbe Nielsen Challenge Submission Readiness',
    stage: 'Demo-ready MVP; publication-grade DOI case still pending',
    ready_count: 8,
    total_count: 9,
    ready_ratio: 0.889,
    blocking_items: ['doi_backed_case'],
    accepted_research_comments: [
      'Integrated Claim Guardrails as a first-class output.',
      'Integrated Graph Memory and an offline Markdown evidence vault.',
    ],
    checklist: [
      { id: 'clear_user_value', label: 'Clear end-user decision memo', ready: true, evidence: 'decision_memo.md exists.', next_step: 'Use it in the demo.' },
      { id: 'doi_backed_case', label: 'Publication-grade DOI-backed case', ready: false, evidence: 'fixture_demo_not_for_publication', next_step: 'Attach a DOI-backed case.' },
    ],
  },
  records_geojson: {
    type: 'FeatureCollection',
    features: [
      {
        geometry: { type: 'Point', coordinates: [2.16, 41.38] },
      properties: { gbif_id: '1001', datasetKey: 'spain-mosquito-watch', issues: [] },
      },
    ],
  },
  graph_memory: {
    graph: {
      summary: {
        run_id: 'demo123',
        taxon: 'Aedes albopictus',
        region_name: 'Spain demo bbox',
        purpose: 'invasive_watch',
        purpose_label: 'Invasive watch',
        score: 72,
      },
      node_counts: {
        runs: 1,
        taxa: 1,
        regions: 1,
        datasets: 1,
        issues: 1,
        claims: 4,
        actions: 1,
        artifacts: 5,
      },
      edges: [
        { source: 'run:demo123', relation: 'uses_taxon', target: 'taxon:1651430' },
        { source: 'run:demo123', relation: 'draws_from_dataset', target: 'dataset:spain-mosquito-watch' },
      ],
      memory_cards: [
        { title: 'Connected run memory', body: 'This run links records, datasets, claims and actions.' },
        { title: 'Judge-friendly vault', body: 'The vault can be opened offline.' },
      ],
    },
  },
  exports: [
    { name: 'evidence_pack.zip', url: '/api/evidence/runs/demo123/exports/evidence_pack.zip', size_bytes: 4096 },
    { name: 'evidence_vault.zip', url: '/api/evidence/runs/demo123/exports/evidence_vault.zip', size_bytes: 2048 },
    { name: 'passport.html', url: '/api/evidence/runs/demo123/exports/passport.html', size_bytes: 1024 },
    { name: 'decision_memo.md', url: '/api/evidence/runs/demo123/exports/decision_memo.md', size_bytes: 1024 },
    { name: 'submission_readiness.md', url: '/api/evidence/runs/demo123/exports/submission_readiness.md', size_bytes: 1024 },
    { name: 'validation_summary.md', url: '/api/evidence/runs/demo123/exports/validation_summary.md', size_bytes: 1024 },
    { name: 'impact_brief.md', url: '/api/evidence/runs/demo123/exports/impact_brief.md', size_bytes: 1024 },
    { name: 'video_script.md', url: '/api/evidence/runs/demo123/exports/video_script.md', size_bytes: 1024 },
    { name: 'decision_memo.json', url: '/api/evidence/runs/demo123/exports/decision_memo.json', size_bytes: 512 },
    { name: 'submission_readiness.json', url: '/api/evidence/runs/demo123/exports/submission_readiness.json', size_bytes: 512 },
    { name: 'validation_summary.json', url: '/api/evidence/runs/demo123/exports/validation_summary.json', size_bytes: 512 },
    { name: 'citations.md', url: '/api/evidence/runs/demo123/exports/citations.md', size_bytes: 512 },
    { name: 'claim_guardrails.md', url: '/api/evidence/runs/demo123/exports/claim_guardrails.md', size_bytes: 512 },
    { name: 'evidence_graph.json', url: '/api/evidence/runs/demo123/exports/evidence_graph.json', size_bytes: 512 },
    { name: 'graph_memory.md', url: '/api/evidence/runs/demo123/exports/graph_memory.md', size_bytes: 512 },
    { name: 'source_summary.json', url: '/api/evidence/runs/demo123/exports/source_summary.json', size_bytes: 512 },
    { name: 'readiness_scorecard.csv', url: '/api/evidence/runs/demo123/exports/readiness_scorecard.csv', size_bytes: 512 },
    { name: 'gap_priorities.csv', url: '/api/evidence/runs/demo123/exports/gap_priorities.csv', size_bytes: 512 },
    { name: 'methods_text.md', url: '/api/evidence/runs/demo123/exports/methods_text.md', size_bytes: 512 },
    { name: 'publisher_feedback.csv', url: '/api/evidence/runs/demo123/exports/publisher_feedback.csv', size_bytes: 512 },
    { name: 'derived_dataset_recipe.json', url: '/api/evidence/runs/demo123/exports/derived_dataset_recipe.json', size_bytes: 512 },
    { name: 'provenance.json', url: '/api/evidence/runs/demo123/exports/provenance.json', size_bytes: 512 },
  ],
};

function mockRunForRequest(request = mockRun.run.request) {
  const sourceMode = request.source_mode || (request.use_fixture ? 'fixture' : 'online_with_empty_fallback');
  const usedSource = sourceMode === 'fixture' ? 'fixture' : 'online';
  return {
    ...mockRun,
    run: {
      ...mockRun.run,
      source_mode: usedSource,
      request: {
        ...mockRun.run.request,
        ...request,
        source_mode: sourceMode,
      },
    },
    passport: {
      ...mockRun.passport,
      taxon: request.taxon || mockRun.passport.taxon,
      region_name: request.region_name || mockRun.passport.region_name,
      bbox: request.bbox || mockRun.passport.bbox,
      taxonKey: request.taxon_key || mockRun.passport.taxonKey,
    },
    source_summary: {
      ...mockRun.source_summary,
      requested_source_mode: sourceMode,
      used_source_mode: usedSource,
      gbif_api_status: sourceMode === 'fixture' ? 'not_called' : 'ok',
      selected_taxon_key: request.taxon_key || null,
    },
    request_fingerprint: `test-${request.taxon || 'taxon'}-${sourceMode}-${(request.bbox || []).join(',')}`,
  };
}

function installFetchMock() {
  const postBodies = [];
  vi.spyOn(global, 'fetch').mockImplementation(async (url, options = {}) => {
    const textUrl = String(url);
    if (textUrl.endsWith('/api/evidence/demo-scenarios')) {
      return { ok: true, json: async () => mockScenarios };
    }
    if (textUrl.endsWith('/api/evidence/region-presets')) {
      return { ok: true, json: async () => mockRegions };
    }
    if (textUrl.endsWith('/api/evidence/gbif-status')) {
      return {
        ok: true,
        json: async () => ({
          status: 'ok',
          base_url: 'https://api.gbif.org/v1',
          message: 'GBIF API reachable. Live occurrence runs use GBIF-mediated records.',
        }),
      };
    }
    if (textUrl.includes('/api/evidence/taxon-suggest')) {
      return { ok: true, json: async () => ({ query: 'lynx', source: 'gbif_api', warnings: [], results: mockTaxa }) };
    }
    if (textUrl.endsWith('/api/evidence/runs') && !options.method) {
      return { ok: true, json: async () => [] };
    }
    if (textUrl.endsWith('/api/evidence/run')) {
      postBodies.push(JSON.parse(options.body));
      return { ok: true, json: async () => ({ run_id: 'demo123', status: 'completed', exports: mockRun.exports }) };
    }
    if (textUrl.endsWith('/api/evidence/runs/demo123')) {
      return { ok: true, json: async () => mockRunForRequest(postBodies.at(-1) || mockRun.run.request) };
    }
    return { ok: false, status: 404, json: async () => ({}) };
  });
  return postBodies;
}

afterEach(() => {
  cleanup();
  window.localStorage.clear();
  vi.restoreAllMocks();
});

describe('EcoGenesis Evidence Atlas UI', () => {
  it('auto-runs and renders the minimal Presentation mode first', async () => {
    installFetchMock();
    render(<App />);

    expect(screen.getByRole('heading', { name: 'GBIF Evidence Passport' })).toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole('button', { name: 'Presentation' })).toBeInTheDocument());
    expect(screen.getByRole('button', { name: 'Work with GBIF' })).toBeInTheDocument();
    expect(screen.getByText('From occurrence records to a defensible decision memo')).toBeInTheDocument();
    expect(screen.getByText('Live GBIF status')).toBeInTheDocument();
    expect(screen.getByText('Decision memo')).toBeInTheDocument();
    expect(screen.getAllByText(/Usable for screening/i).length).toBeGreaterThan(0);
    expect(screen.getByText('Safe claims')).toBeInTheDocument();
    expect(screen.getByRole('img', { name: 'Scientific evidence map' })).toBeInTheDocument();
    expect(screen.getByText('OpenStreetMap base map with live GBIF occurrence points, quality halos, grid evidence and survey-priority cells.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Toggle Issues map layer' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Toggle Priority map layer' })).toBeInTheDocument();
    expect(screen.getByText('Advanced evidence files')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Download Evidence Pack/i })).toBeInTheDocument();
  });

  it('opens the GBIF workbench and submits live GBIF requests', async () => {
    const postBodies = installFetchMock();
    render(<App />);

    await waitFor(() => expect(screen.getByText('From occurrence records to a defensible decision memo')).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: 'Work with GBIF' }));
    expect(screen.getAllByText('Work with GBIF').length).toBeGreaterThan(0);
    expect(screen.getByText('Live GBIF status')).toBeInTheDocument();
    expect(screen.queryByText('Data source')).not.toBeInTheDocument();
    expect(screen.queryByText('Demo cases')).not.toBeInTheDocument();
    expect(screen.queryByText('Run evidence chain')).not.toBeInTheDocument();
    expect(screen.queryByText('Recent evidence passports')).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Max records'), { target: { value: '120' } });
    expect(screen.getByText('Not generated for this selection yet')).toBeInTheDocument();
    expect(screen.getByText('Pending changes')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Generate live Evidence Passport' }));

    await waitFor(() => expect(postBodies.length).toBeGreaterThan(1));
    expect(postBodies.at(-1).source_mode).toBe('online_with_empty_fallback');
    expect(postBodies.at(-1).use_fixture).toBe(false);
    expect(postBodies.at(-1).max_records).toBe(120);

    await waitFor(() => expect(screen.getByText('Key risks')).toBeInTheDocument());
    expect(screen.getByRole('button', { name: 'Toggle Cells map layer' })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByRole('button', { name: 'Toggle Records map layer' })).toHaveAttribute('aria-pressed', 'true');
    fireEvent.click(screen.getByText('Advanced evidence files'));
    expect(screen.getByRole('link', { name: /Evidence pack ZIP/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /evidence_vault.zip/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /evidence_graph.json/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /source_summary.json/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /gap_priorities.csv/i })).toBeInTheDocument();
    expect(screen.getAllByRole('link', { name: /decision_memo.md/i })).toHaveLength(1);
    expect(screen.getAllByRole('link', { name: /submission_readiness.md/i })).toHaveLength(1);
    fireEvent.change(screen.getByLabelText('West longitude'), { target: { value: '50' } });
    expect(screen.getByText(/Bounding box coordinates are not ordered/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Generate live Evidence Passport' })).toBeDisabled();
  });

  it('auto-runs when users select a GBIF taxon and saved region', async () => {
    const postBodies = installFetchMock();
    render(<App />);

    await waitFor(() => expect(screen.getByText('From occurrence records to a defensible decision memo')).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: 'Work with GBIF' }));
    const initialRuns = postBodies.length;
    fireEvent.change(screen.getByLabelText('Taxon'), { target: { value: 'lynx' } });
    expect(screen.getByText('Not generated for this selection yet')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Find taxon in GBIF' }));

    const lynx = await screen.findByRole('button', { name: /Lynx pardinus/i });
    fireEvent.click(lynx);
    await waitFor(() => expect(postBodies.length).toBeGreaterThan(initialRuns));
    expect(screen.getByText(/Using GBIF taxonKey 2435261/i)).toBeInTheDocument();
    expect(postBodies.at(-1).taxon).toBe('Lynx pardinus');
    expect(postBodies.at(-1).taxon_key).toBe(2435261);
    expect(postBodies.at(-1).source_mode).toBe('online_with_empty_fallback');

    expect(screen.getByLabelText('Search saved regions')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Show research region presets' }));
    const afterTaxonRuns = postBodies.length;
    fireEvent.click(screen.getByTestId('region-preset-iberian'));
    await waitFor(() => expect(postBodies.length).toBeGreaterThan(afterTaxonRuns));
    expect(screen.getByLabelText('Region')).toHaveValue('Iberian Peninsula live bbox');
    expect(screen.getByLabelText('West longitude')).toHaveValue('-10');
    expect(postBodies.at(-1).taxon).toBe('Lynx pardinus');
    expect(postBodies.at(-1).taxon_key).toBe(2435261);
    expect(postBodies.at(-1).bbox).toEqual([-10, 35, 4.5, 44.5]);
  });
});
