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
  },
  publisher_feedback: [
    {
      datasetKey: 'spain-mosquito-watch',
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
  records_geojson: {
    type: 'FeatureCollection',
    features: [
      {
        geometry: { type: 'Point', coordinates: [2.16, 41.38] },
        properties: { gbif_id: '1001', datasetKey: 'spain-mosquito-watch', issues: [] },
      },
    ],
  },
  exports: [
    { name: 'evidence_pack.zip', url: '/api/evidence/runs/demo123/exports/evidence_pack.zip', size_bytes: 4096 },
    { name: 'passport.html', url: '/api/evidence/runs/demo123/exports/passport.html', size_bytes: 1024 },
    { name: 'citations.md', url: '/api/evidence/runs/demo123/exports/citations.md', size_bytes: 512 },
    { name: 'claim_guardrails.md', url: '/api/evidence/runs/demo123/exports/claim_guardrails.md', size_bytes: 512 },
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
  it('auto-runs the default evidence passport on first render', async () => {
    installFetchMock();
    render(<App />);

    expect(screen.getByRole('heading', { name: 'GBIF Evidence Passport' })).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText('Purpose comparison')).toBeInTheDocument());
    expect(screen.getByText('Scientific interpretation')).toBeInTheDocument();
    expect(screen.getByText('Source & provenance')).toBeInTheDocument();
    expect(screen.getByRole('img', { name: 'Scientific evidence map' })).toBeInTheDocument();
    expect(screen.getByText('OpenStreetMap base map with live GBIF occurrence points, quality halos, grid evidence and survey-priority cells.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Issues' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Priority' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Download Evidence Pack/i })).toBeInTheDocument();
  });

  it('changes source mode and renders grouped passport sections', async () => {
    const postBodies = installFetchMock();
    render(<App />);

    await waitFor(() => expect(screen.getByText('Purpose comparison')).toBeInTheDocument());
    fireEvent.click(screen.getByText('Data source'));
    fireEvent.change(screen.getByLabelText('Source'), { target: { value: 'fixture' } });
    expect(screen.getByText('Not generated for this selection yet')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Generate Evidence Passport' }));

    await waitFor(() => expect(postBodies.length).toBeGreaterThan(1));
    expect(postBodies.at(-1).source_mode).toBe('fixture');
    await waitFor(() => expect(screen.getByRole('button', { name: 'Citation & Provenance' })).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'Citation & Provenance' }));
    expect(screen.getAllByText('Source & provenance').length).toBeGreaterThan(0);

    fireEvent.click(screen.getByRole('button', { name: 'Data Quality' }));
    expect(screen.getAllByText('No-evidence cells').length).toBeGreaterThan(0);

    fireEvent.click(screen.getByRole('button', { name: 'Sampling Gaps' }));
    expect(screen.getAllByText('Sampling Gap Engine').length).toBeGreaterThan(0);

    fireEvent.click(screen.getByRole('button', { name: 'Export Pack' }));
    expect(screen.getByText('ZIP')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Evidence pack ZIP/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /source_summary.json/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /gap_priorities.csv/i })).toBeInTheDocument();
  });

  it('auto-runs when users select a GBIF taxon and saved region', async () => {
    const postBodies = installFetchMock();
    render(<App />);

    await waitFor(() => expect(screen.getByText('Purpose comparison')).toBeInTheDocument());
    const initialRuns = postBodies.length;
    fireEvent.change(screen.getByLabelText('Taxon'), { target: { value: 'lynx' } });
    expect(screen.getByText('Not generated for this selection yet')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Search GBIF taxon' }));

    const lynx = await screen.findByRole('button', { name: /Lynx pardinus/i });
    fireEvent.click(lynx);
    await waitFor(() => expect(postBodies.length).toBeGreaterThan(initialRuns));
    expect(screen.getByText(/Locked to GBIF taxonKey 2435261/i)).toBeInTheDocument();
    expect(postBodies.at(-1).taxon).toBe('Lynx pardinus');
    expect(postBodies.at(-1).taxon_key).toBe(2435261);
    expect(postBodies.at(-1).source_mode).toBe('online_with_empty_fallback');

    fireEvent.click(screen.getByText('Saved regions'));
    const afterTaxonRuns = postBodies.length;
    fireEvent.click(screen.getByRole('button', { name: /Iberian Peninsula/i }));
    await waitFor(() => expect(postBodies.length).toBeGreaterThan(afterTaxonRuns));
    expect(screen.getByLabelText('Region')).toHaveValue('Iberian Peninsula live bbox');
    expect(screen.getByLabelText('West longitude')).toHaveValue('-10');
    expect(postBodies.at(-1).taxon).toBe('Lynx pardinus');
    expect(postBodies.at(-1).taxon_key).toBe(2435261);
    expect(postBodies.at(-1).bbox).toEqual([-10, 35, 4.5, 44.5]);
  });
});
