import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import App from './App.jsx';

const demoScenarios = [
  {
    id: 'aedes-good',
    label: 'Species-safe Aedes',
    description: 'All gates pass.',
    request: {
      project_title: 'Aedes albopictus species-safe COI record',
      marker: 'COI-5P',
      reference_database: 'COI Animals / BOLD public clustered reference',
      method_or_sop: 'GBIF Sequence ID-compatible BLAST workflow',
      ruleset_version: 'barcode-gbif-compiler-v2',
      records: [{ sequence_id: 'AALB-COI-good', sequence: 'ACGT', hits: [] }],
    },
  },
];

const createdRun = {
  run_id: 'barcode123',
  status: 'completed',
  summary: {
    processed_records: 1,
    species_safe_records: 1,
    genus_safe_records: 0,
    not_publishable_records: 0,
    blocked_species_claims: 0,
    publication_repair_efficiency: 1,
    record_ready_records: 1,
    verdict: 'At least one sequence is species-safe under the frozen molecular evidence gates; publication readiness is reported separately.',
  },
  exports: [{ name: 'evidence_pack.zip', url: '/api/barcode/runs/barcode123/exports/evidence_pack.zip' }],
};

const runDetail = {
  run: { run_id: 'barcode123', ruleset_version: 'barcode-gbif-compiler-v2' },
  summary: createdRun.summary,
  metrics: createdRun.summary,
  data_accounting_ledger: [
    { metric: 'input_n', value: 1, denominator: 1, rate: 1, unit: 'sequence_records', layer: 'input', meaning: 'Records received by the Barcode-to-GBIF compiler.' },
    { metric: 'candidate_n', value: 1, denominator: 1, rate: 1, unit: 'sequence_records', layer: 'taxonomy', meaning: 'Records with at least one supplied reference hit.' },
    { metric: 'safe_n', value: 1, denominator: 1, rate: 1, unit: 'sequence_records', layer: 'taxonomy', meaning: 'Records safe at species/genus/higher-rank level.' },
    { metric: 'publishable_candidate_n', value: 1, denominator: 1, rate: 1, unit: 'sequence_records', layer: 'publication', meaning: 'Safe records emitted into publishable review templates but not formal GBIF-ready.' },
    { metric: 'gbif_ready_n', value: 0, denominator: 1, rate: 0, unit: 'sequence_records', layer: 'publication', meaning: 'Records that passed dataset-level metadata checks for formal GBIF-ready export.' },
    { metric: 'repair_required_n', value: 0, denominator: 1, rate: 0, unit: 'sequence_records', layer: 'publication', meaning: 'Records blocked by molecular, occurrence, assay, backend or metadata gates.' },
    { metric: 'blocked_top_species_claims_n', value: 0, denominator: 1, rate: 0, unit: 'sequence_records', layer: 'safety', meaning: 'Species-ranked top hits that were blocked or downgraded by fail-closed gates.' },
    { metric: 'hard_gate_failures_n', value: 0, denominator: 1, rate: 0, unit: 'sequence_records', layer: 'safety', meaning: 'Species-safe records with any failed hard gate; must remain zero.' },
  ],
  records: [
    {
      sequence_id: 'AALB-COI-good',
      decision_class: 'species-safe',
      taxonomic_status: 'species-safe',
      publication_bucket: 'publishable_candidate',
      export_state: 'dwc_template_ready',
      candidate_taxon: { name: 'Aedes albopictus', rank: 'species' },
      published_taxon: { name: 'Aedes albopictus', rank: 'species' },
      publication_stage: 'record_recommended_ready',
      blockers: [],
    },
  ],
  exports: createdRun.exports,
};

const csvImportPayload = {
  request: {
    project_title: 'Uploaded molecular evidence CSV',
    marker: 'COI-5P',
    reference_database: 'COI Animals / BOLD public clustered reference',
    method_or_sop: 'GBIF Sequence ID-compatible BLAST workflow',
    records: [{ sequence_id: 'AALB-COI-good', sequence: 'ACGT', hits: [{ taxon: 'Aedes albopictus', identity: 99.6, query_coverage: 96 }] }],
  },
  preview_rows: [
    {
      sequenceID: 'AALB-COI-good',
      scientificName: 'Aedes albopictus',
      eventDate: '2026-04-18',
      marker: 'COI-5P',
      topTaxon: 'Aedes albopictus',
      topIdentity: '99.6',
      topCoverage: '96',
    },
  ],
  validation: {
    ok: true,
    errors: [],
    warnings: ['Some strongly recommended GBIF/DNA fields are missing; publication readiness may be blocked.'],
    records_found: 1,
    missing_required_columns: [],
    missing_recommended_fields: { occurrenceID: 1 },
    invalid_sequence_count: 0,
    weak_or_no_hit_count: 0,
    no_hit_count: 0,
  },
};

const createdCsvRun = {
  ...createdRun,
  run_id: 'barcodecsv123',
  exports: [
    { name: 'evidence_pack.zip', url: '/api/barcode/runs/barcodecsv123/exports/evidence_pack.zip' },
    { name: 'sequence_safety_table.csv', url: '/api/barcode/runs/barcodecsv123/exports/sequence_safety_table.csv' },
    { name: 'publication_blockers.csv', url: '/api/barcode/runs/barcodecsv123/exports/publication_blockers.csv' },
    { name: 'dwc_occurrence_core_publishable.csv', url: '/api/barcode/runs/barcodecsv123/exports/dwc_occurrence_core_publishable.csv' },
    { name: 'molecular_evidence_report.html', url: '/api/barcode/runs/barcodecsv123/exports/molecular_evidence_report.html' },
    { name: 'methods_text.md', url: '/api/barcode/runs/barcodecsv123/exports/methods_text.md' },
    { name: 'citations.md', url: '/api/barcode/runs/barcodecsv123/exports/citations.md' },
  ],
};

const csvRunDetail = {
  ...runDetail,
  run: { run_id: 'barcodecsv123', ruleset_version: 'barcode-gbif-compiler-v2' },
  exports: createdCsvRun.exports,
};

const searchStatus = {
  status: 'degraded',
  preferred_backend: 'python-local',
  available_backends: { vsearch: false, blastn: false, 'python-local': true },
  message: 'External VSEARCH/BLAST+ binary was not found; deterministic local mini-search is available.',
};

const referenceDatasets = [
  {
    id: 'aedes_coi_mini',
    title: 'EcoGenesis mini COI reference dataset for Aedes smoke tests',
    marker: 'COI-5P',
    records: 3,
    source_type: 'bundled',
    example_queries: [],
  },
  {
    id: 'ncbi_aedes_coi_small',
    title: 'NCBI GenBank small COI reference pack for Aedes workflow validation',
    marker: 'COI-5P',
    records: 2,
    source_type: 'bundled',
    usage_scope: 'Small real open reference example for EcoGenesis workflow validation.',
    gbif_backbone_enrichment: {
      status: 'pre_enriched_manifest',
      enriched_records: 2,
      fallback_records: 0,
    },
    example_queries: [
      {
        id: 'LC881945_1_AALB_COI',
        label: 'Run real Aedes COI species-safe check',
        sequence_id: 'LC881945_1_AALB_COI',
        sequence: 'ACGTTGACCTAGGCTTACGATCGTACCGATGCTAGCTAGGATCCGATCGTACGATCGTAGCTAGCATCG',
        expected_decision: 'species-safe',
        explanation: 'Real Aedes albopictus COI query should pass species-safe gates.',
      },
    ],
  },
  {
    id: 'culicidae_short_shared_marker',
    title: 'EcoGenesis shared short-fragment reference tree for Culicidae',
    marker: 'COI-short',
    records: 8,
    source_type: 'bundled',
    usage_scope: 'Short-fragment graph validation only.',
    gbif_backbone_enrichment: {
      status: 'pre_enriched_manifest',
      enriched_records: 3,
      fallback_records: 5,
    },
    example_queries: [
      {
        id: 'CULICIDAE_SHARED_SHORT_QUERY',
        label: 'Run shared short-fragment tree',
        sequence_id: 'CULICIDAE_SHARED_SHORT_QUERY',
        sequence: 'ACGTTGACCTAGGCTTACGATCGTACCGATGC',
        expected_decision: 'higher-rank-shared',
        explanation: 'A short conserved marker fragment matches several mosquito species.',
      },
    ],
  },
];

const searchPayload = {
  search: {
    backend_used: 'python-local',
    hits: [
      {
        reference_id: 'AALB_COI_MINI_REF',
        taxon: 'Aedes albopictus',
        identity: 100,
        query_coverage: 100,
      },
    ],
  },
  run: createdCsvRun,
  pack: csvRunDetail,
};

const fragmentGraphPayload = {
  query: {
    sequence_id: 'LC881945_1_AALB_COI',
    sequence_length: 72,
    sequence_md5: 'abc123',
  },
  reference_dataset: {
    id: 'ncbi_aedes_coi_small',
    title: 'NCBI GenBank small COI reference pack for Aedes workflow validation',
    marker: 'COI-5P',
  },
  backend_used: 'python-local',
  source_monitor: [
    { source: 'local_reference_dataset', status: 'done', detail: 'ncbi_aedes_coi_small', cached: true },
    { source: 'python-local', status: 'review_only', detail: 'deterministic mini-search', cached: false },
  ],
  classification: {
    status: 'genus-shared',
    safe_taxon: { rank: 'genus', name: 'Aedes', taxon_key: 7924646 },
    kingdoms: ['Animalia'],
    taxa_count: 2,
    informative_hits: 2,
    rank_distribution: {
      kingdom: 1,
      phylum: 1,
      class: 1,
      order: 1,
      family: 1,
      genus: 1,
      species: 2,
    },
    caveat: 'Graph is limited to the selected reference dataset.',
  },
  claim_boundary: {
    supported: 'Genus-level fragment evidence for Aedes; species-level claims are blocked.',
    not_supported: ['natural occurrence, absence, abundance or distribution', 'phenotype/function/ecological role'],
  },
  segments: [
    {
      segment_id: 'LC881945_1_AALB_COI:1-72',
      segment_start: 1,
      segment_end: 72,
      segment_length: 72,
      segment_class: 'mini_fragment',
      match_summary: {
        best_identity: 100,
        best_query_coverage: 100,
        safe_lca: { rank: 'genus', name: 'Aedes', taxon_key: 7924646 },
      },
      known_annotations: [{ type: 'marker_region', label: 'COI-5P matched region' }],
    },
  ],
  nodes: [
    { id: 'fragment:LC881945_1_AALB_COI', type: 'fragment', label: 'Query fragment', sequence_length: 72 },
    { id: 'reference_dataset:ncbi_aedes_coi_small', type: 'reference_dataset', label: 'NCBI GenBank small COI reference pack for Aedes workflow validation', marker: 'COI-5P' },
    { id: 'hit:AALB', type: 'reference_hit', label: 'Aedes albopictus', identity: 100, coverage: 100, informative: true },
    { id: 'hit:AAEG', type: 'reference_hit', label: 'Aedes aegypti', identity: 99.2, coverage: 100, informative: true },
    { id: 'taxon:kingdom:Animalia', type: 'kingdom', label: 'Animalia', rank: 'kingdom' },
    { id: 'taxon:genus:Aedes', type: 'genus', label: 'Aedes', rank: 'genus', is_safe_taxon: true },
    { id: 'taxon:species:Aedes_albopictus', type: 'species', label: 'Aedes albopictus', rank: 'species' },
    { id: 'taxon:species:Aedes_aegypti', type: 'species', label: 'Aedes aegypti', rank: 'species' },
    { id: 'safe_lca:genus:Aedes', type: 'safe_lca', label: 'Safe LCA: Aedes', rank: 'genus', name: 'Aedes', taxon_key: 7924646 },
    { id: 'warning:genus-shared', type: 'warning', label: 'Fragment is shared across species; use the genus-level claim.', status: 'genus-shared' },
  ],
  edges: [
    { source: 'fragment:LC881945_1_AALB_COI', target: 'reference_dataset:ncbi_aedes_coi_small', type: 'searched_against' },
    { source: 'fragment:LC881945_1_AALB_COI', target: 'hit:AALB', type: 'matches_reference' },
    { source: 'fragment:LC881945_1_AALB_COI', target: 'hit:AAEG', type: 'matches_reference' },
    { source: 'hit:AALB', target: 'taxon:species:Aedes_albopictus', type: 'belongs_to_taxon' },
    { source: 'hit:AAEG', target: 'taxon:species:Aedes_aegypti', type: 'belongs_to_taxon' },
    { source: 'safe_lca:genus:Aedes', target: 'taxon:genus:Aedes', type: 'safe_lca_of' },
  ],
  hits: [
    { reference_id: 'AALB', taxon: 'Aedes albopictus', identity: 100, query_coverage: 100 },
    { reference_id: 'AAEG', taxon: 'Aedes aegypti', identity: 99.2, query_coverage: 100 },
  ],
};

const sharedFragmentGraphPayload = {
  query: {
    sequence_id: 'CULICIDAE_SHARED_SHORT_QUERY',
    sequence_length: 32,
    sequence_md5: 'shared123',
  },
  reference_dataset: {
    id: 'culicidae_short_shared_marker',
    title: 'EcoGenesis shared short-fragment reference tree for Culicidae',
    marker: 'COI-short',
  },
  backend_used: 'python-local',
  source_monitor: [
    { source: 'local_reference_dataset', status: 'done', detail: 'culicidae_short_shared_marker', cached: true },
    { source: 'python-local', status: 'review_only', detail: 'deterministic mini-search', cached: false },
  ],
  classification: {
    status: 'higher-rank-shared',
    safe_taxon: { rank: 'family', name: 'Culicidae', taxon_key: 3346 },
    kingdoms: ['Animalia'],
    taxa_count: 8,
    informative_hits: 8,
    rank_distribution: {
      kingdom: 1,
      phylum: 1,
      class: 1,
      order: 1,
      family: 1,
      genus: 3,
      species: 8,
    },
    caveat: 'Graph is limited to the selected reference dataset.',
  },
  claim_boundary: {
    supported: 'Family-level fragment evidence for Culicidae; lower-rank claims are blocked.',
    not_supported: ['natural occurrence, absence, abundance or distribution', 'global species truth outside the selected reference dataset'],
  },
  segments: [
    {
      segment_id: 'CULICIDAE_SHARED_SHORT_QUERY:1-32',
      segment_start: 1,
      segment_end: 32,
      segment_length: 32,
      segment_class: 'mini_fragment',
      match_summary: {
        best_identity: 100,
        best_query_coverage: 100,
        safe_lca: { rank: 'family', name: 'Culicidae', taxon_key: 3346 },
      },
      known_annotations: [{ type: 'marker_region', label: 'COI-short matched region' }],
    },
  ],
  nodes: [
    { id: 'fragment:CULICIDAE_SHARED_SHORT_QUERY', type: 'fragment', label: 'Query fragment', sequence_length: 32 },
    { id: 'reference_dataset:culicidae_short_shared_marker', type: 'reference_dataset', label: 'EcoGenesis shared short-fragment reference tree for Culicidae', marker: 'COI-short' },
    { id: 'warning:higher-rank-shared', type: 'warning', label: 'Short fragment is shared across several mosquito genera.', status: 'higher-rank-shared' },
    { id: 'safe_lca:family:Culicidae', type: 'safe_lca', label: 'Safe LCA: Culicidae', rank: 'family', name: 'Culicidae', taxon_key: 3346 },
    { id: 'taxon:genus:Aedes', type: 'genus', label: 'Aedes', rank: 'genus' },
    { id: 'taxon:genus:Anopheles', type: 'genus', label: 'Anopheles', rank: 'genus' },
    { id: 'taxon:genus:Culex', type: 'genus', label: 'Culex', rank: 'genus' },
    { id: 'taxon:species:Aedes_albopictus', type: 'species', label: 'Aedes albopictus', rank: 'species' },
    { id: 'taxon:species:Aedes_aegypti', type: 'species', label: 'Aedes aegypti', rank: 'species' },
    { id: 'taxon:species:Aedes_japonicus', type: 'species', label: 'Aedes japonicus', rank: 'species' },
    { id: 'taxon:species:Anopheles_stephensi', type: 'species', label: 'Anopheles stephensi', rank: 'species' },
    { id: 'taxon:species:Anopheles_gambiae', type: 'species', label: 'Anopheles gambiae', rank: 'species' },
    { id: 'taxon:species:Culex_pipiens', type: 'species', label: 'Culex pipiens', rank: 'species' },
    { id: 'taxon:species:Culex_quinquefasciatus', type: 'species', label: 'Culex quinquefasciatus', rank: 'species' },
    { id: 'taxon:species:Culex_perexiguus', type: 'species', label: 'Culex perexiguus', rank: 'species' },
  ],
  edges: [
    { source: 'fragment:CULICIDAE_SHARED_SHORT_QUERY', target: 'reference_dataset:culicidae_short_shared_marker', type: 'searched_against' },
    { source: 'fragment:CULICIDAE_SHARED_SHORT_QUERY', target: 'warning:higher-rank-shared', type: 'limited_by' },
    { source: 'safe_lca:family:Culicidae', target: 'taxon:genus:Aedes', type: 'safe_lca_of' },
    { source: 'safe_lca:family:Culicidae', target: 'taxon:genus:Anopheles', type: 'safe_lca_of' },
    { source: 'safe_lca:family:Culicidae', target: 'taxon:genus:Culex', type: 'safe_lca_of' },
    { source: 'taxon:genus:Aedes', target: 'taxon:species:Aedes_albopictus', type: 'parent_taxon' },
    { source: 'taxon:genus:Aedes', target: 'taxon:species:Aedes_aegypti', type: 'parent_taxon' },
    { source: 'taxon:genus:Aedes', target: 'taxon:species:Aedes_japonicus', type: 'parent_taxon' },
    { source: 'taxon:genus:Anopheles', target: 'taxon:species:Anopheles_stephensi', type: 'parent_taxon' },
    { source: 'taxon:genus:Anopheles', target: 'taxon:species:Anopheles_gambiae', type: 'parent_taxon' },
    { source: 'taxon:genus:Culex', target: 'taxon:species:Culex_pipiens', type: 'parent_taxon' },
    { source: 'taxon:genus:Culex', target: 'taxon:species:Culex_quinquefasciatus', type: 'parent_taxon' },
    { source: 'taxon:genus:Culex', target: 'taxon:species:Culex_perexiguus', type: 'parent_taxon' },
  ],
  hits: [
    { reference_id: 'AALB_SHARED_SHORT', taxon: 'Aedes albopictus', identity: 100, query_coverage: 100 },
    { reference_id: 'AAEG_SHARED_SHORT', taxon: 'Aedes aegypti', identity: 100, query_coverage: 100 },
    { reference_id: 'AJAP_SHARED_SHORT', taxon: 'Aedes japonicus', identity: 100, query_coverage: 100 },
    { reference_id: 'ASTEP_SHARED_SHORT', taxon: 'Anopheles stephensi', identity: 100, query_coverage: 100 },
    { reference_id: 'AGAM_SHARED_SHORT', taxon: 'Anopheles gambiae', identity: 100, query_coverage: 100 },
    { reference_id: 'CPIX_SHARED_SHORT', taxon: 'Culex pipiens', identity: 100, query_coverage: 100 },
    { reference_id: 'CQUI_SHARED_SHORT', taxon: 'Culex quinquefasciatus', identity: 100, query_coverage: 100 },
    { reference_id: 'CPER_SHARED_SHORT', taxon: 'Culex perexiguus', identity: 100, query_coverage: 100 },
  ],
};

const uploadedReferencePayload = {
  status: 'created',
  dataset: {
    id: 'custom_aedes_coi',
    title: 'Custom Aedes COI',
    marker: 'COI-5P',
    records: 2,
    source_type: 'uploaded',
  },
  datasets: [
    ...referenceDatasets,
    {
      id: 'custom_aedes_coi',
      title: 'Custom Aedes COI',
      marker: 'COI-5P',
      records: 2,
      source_type: 'uploaded',
    },
  ],
};

afterEach(() => {
  cleanup();
  window.history.pushState({}, '', '/');
  vi.restoreAllMocks();
});

describe('Barcode compiler UI', () => {
  it('renders overview and runs a compiler demo', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation((url, options) => {
      const textUrl = String(url);
      if (textUrl.endsWith('/api/barcode/demo-scenarios')) {
        return Promise.resolve(new Response(JSON.stringify(demoScenarios), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/reference-status')) {
        return Promise.resolve(new Response(JSON.stringify({ status: 'ready', message: 'Compiler ready.' }), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/search-status')) {
        return Promise.resolve(new Response(JSON.stringify(searchStatus), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/reference-datasets')) {
        return Promise.resolve(new Response(JSON.stringify(referenceDatasets), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/run') && options?.method === 'POST') {
        return Promise.resolve(new Response(JSON.stringify(createdRun), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/runs/barcode123')) {
        return Promise.resolve(new Response(JSON.stringify(runDetail), { status: 200 }));
      }
      return Promise.resolve(new Response('{}', { status: 404 }));
    });

    render(<App />);

    expect(await screen.findByText('Molecular Evidence Conversion & Repair Engine for GBIF')).toBeInTheDocument();
    expect(screen.getByText('Judge overview')).toBeInTheDocument();
    expect(screen.getByText('Decision cockpit for safe molecular evidence, not another biodiversity dashboard.')).toBeInTheDocument();
    expect(screen.getByText('Evidence funnel')).toBeInTheDocument();
    expect(screen.getByText('Claim matrix')).toBeInTheDocument();
    expect(screen.getByText('Repair optimizer')).toBeInTheDocument();
    expect(screen.getByText('Research audit')).toBeInTheDocument();

    fireEvent.click(screen.getByText('Run mixed demo'));

    await waitFor(() => expect(screen.getAllByText('AALB-COI-good').length).toBeGreaterThan(0));
    expect(screen.getByText('species-safe')).toBeInTheDocument();
    expect(screen.getAllByText('evidence_pack.zip').length).toBeGreaterThan(0);
    expect(screen.getByText('Data accounting ledger')).toBeInTheDocument();
    expect(screen.getByText('publishable_candidate_n')).toBeInTheDocument();
  });

  it('opens the workbench and exposes the request editor', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation((url) => {
      const textUrl = String(url);
      if (textUrl.endsWith('/api/barcode/demo-scenarios')) {
        return Promise.resolve(new Response(JSON.stringify(demoScenarios), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/reference-status')) {
        return Promise.resolve(new Response(JSON.stringify({ status: 'ready', message: 'Compiler ready.' }), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/search-status')) {
        return Promise.resolve(new Response(JSON.stringify(searchStatus), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/reference-datasets')) {
        return Promise.resolve(new Response(JSON.stringify(referenceDatasets), { status: 200 }));
      }
      return Promise.resolve(new Response('{}', { status: 404 }));
    });

    render(<App />);
    fireEvent.click(await screen.findByText('Run compiler'));

    expect(screen.getByLabelText('Demo case')).toBeInTheDocument();
    expect(screen.getByText('Run selected demo')).toBeInTheDocument();
    expect(screen.getByText('Search a real reference dataset')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Advanced request JSON'));
    expect(screen.getByLabelText('Compiler request JSON')).toBeInTheDocument();
  });

  it('imports a CSV, shows validation preview, and runs the compiler from upload', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation((url, options) => {
      const textUrl = String(url);
      if (textUrl.endsWith('/api/barcode/demo-scenarios')) {
        return Promise.resolve(new Response(JSON.stringify(demoScenarios), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/reference-status')) {
        return Promise.resolve(new Response(JSON.stringify({ status: 'ready', message: 'Compiler ready.' }), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/search-status')) {
        return Promise.resolve(new Response(JSON.stringify(searchStatus), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/reference-datasets')) {
        return Promise.resolve(new Response(JSON.stringify(referenceDatasets), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/import-csv') && options?.method === 'POST') {
        return Promise.resolve(new Response(JSON.stringify(csvImportPayload), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/run-csv') && options?.method === 'POST') {
        return Promise.resolve(new Response(JSON.stringify(createdCsvRun), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/runs/barcodecsv123')) {
        return Promise.resolve(new Response(JSON.stringify(csvRunDetail), { status: 200 }));
      }
      return Promise.resolve(new Response('{}', { status: 404 }));
    });

    render(<App />);
    fireEvent.click(await screen.findByText('Run compiler'));

    expect(screen.getByText('Upload CSV results')).toBeInTheDocument();
    expect(screen.getByText('Download CSV template')).toBeInTheDocument();
    const file = new File(['sequenceID,sequence\nAALB-COI-good,ACGT\n'], 'aedes_good.csv', { type: 'text/csv' });
    fireEvent.change(screen.getByLabelText('CSV file'), { target: { files: [file] } });

    expect(await screen.findByText('CSV ready to run')).toBeInTheDocument();
    expect(screen.getByText('AALB-COI-good')).toBeInTheDocument();
    expect(screen.getByText('Some strongly recommended GBIF/DNA fields are missing; publication readiness may be blocked.')).toBeInTheDocument();

    fireEvent.click(screen.getByText('Generate from CSV'));

    await waitFor(() => expect(screen.getAllByText('species-safe').length).toBeGreaterThan(0));
    expect(screen.getAllByText('sequence_safety_table.csv').length).toBeGreaterThan(0);
    expect(screen.getAllByText('molecular_evidence_report.html').length).toBeGreaterThan(0);
    expect(screen.getAllByText('methods_text.md').length).toBeGreaterThan(0);
    expect(screen.getAllByText('citations.md').length).toBeGreaterThan(0);
    expect(screen.getByText('Publishable (1)')).toBeInTheDocument();
  });

  it('runs reference search and compiles the returned hits', async () => {
    let searchRequestBody = null;
    vi.spyOn(globalThis, 'fetch').mockImplementation((url, options) => {
      const textUrl = String(url);
      if (textUrl.endsWith('/api/barcode/demo-scenarios')) {
        return Promise.resolve(new Response(JSON.stringify(demoScenarios), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/reference-status')) {
        return Promise.resolve(new Response(JSON.stringify({ status: 'ready', message: 'Compiler ready.' }), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/search-status')) {
        return Promise.resolve(new Response(JSON.stringify(searchStatus), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/reference-datasets')) {
        return Promise.resolve(new Response(JSON.stringify(referenceDatasets), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/search') && options?.method === 'POST') {
        searchRequestBody = JSON.parse(options.body);
        return Promise.resolve(new Response(JSON.stringify(searchPayload), { status: 200 }));
      }
      return Promise.resolve(new Response('{}', { status: 404 }));
    });

    render(<App />);
    fireEvent.click(await screen.findByText('Run compiler'));
    expect(await screen.findByText('Run real Aedes COI species-safe check')).toBeInTheDocument();
    expect(await screen.findByText('GBIF backbone: pre_enriched_manifest · enriched 2 / fallback 0')).toBeInTheDocument();
    fireEvent.click(screen.getAllByText('Run real data')[0]);

    await waitFor(() => expect(screen.getAllByText('species-safe').length).toBeGreaterThan(0));
    expect(searchRequestBody.reference_dataset).toBe('ncbi_aedes_coi_small');
    expect(searchRequestBody.sequence_id).toBe('LC881945_1_AALB_COI');
    expect(screen.getByText('Naive vs EcoGenesis')).toBeInTheDocument();
    expect(screen.getByText('python-local')).toBeInTheDocument();
  });

  it('builds a real fragment-to-taxa graph from selected reference evidence', async () => {
    let graphRequestBody = null;
    vi.spyOn(globalThis, 'fetch').mockImplementation((url, options) => {
      const textUrl = String(url);
      if (textUrl.endsWith('/api/barcode/demo-scenarios')) {
        return Promise.resolve(new Response(JSON.stringify(demoScenarios), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/reference-status')) {
        return Promise.resolve(new Response(JSON.stringify({ status: 'ready', message: 'Compiler ready.' }), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/search-status')) {
        return Promise.resolve(new Response(JSON.stringify(searchStatus), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/reference-datasets')) {
        return Promise.resolve(new Response(JSON.stringify(referenceDatasets), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/fragment-graph') && options?.method === 'POST') {
        graphRequestBody = JSON.parse(options.body);
        const payload = graphRequestBody.reference_dataset === 'culicidae_short_shared_marker'
          ? sharedFragmentGraphPayload
          : fragmentGraphPayload;
        return Promise.resolve(new Response(JSON.stringify(payload), { status: 200 }));
      }
      return Promise.resolve(new Response('{}', { status: 404 }));
    });

    render(<App />);
    fireEvent.click(await screen.findByText('Fragment graph'));

    expect(screen.getByText('Real fragment-to-taxa explorer')).toBeInTheDocument();
    expect(screen.getByLabelText('Fragment reference dataset')).toBeInTheDocument();
    expect(screen.getByLabelText('DNA marker fragment')).toBeInTheDocument();
    expect(screen.getByText('Build Taxon Graph')).toBeInTheDocument();
    expect(screen.getByText('Run shared short-fragment tree')).toBeInTheDocument();
    expect(screen.getByText('This graph shows where the fragment appears inside the selected reference dataset.')).toBeInTheDocument();

    fireEvent.click(screen.getByText('Build Taxon Graph'));

    await waitFor(() => expect(screen.getAllByText('Shared within a genus').length).toBeGreaterThan(0));
    expect(graphRequestBody.reference_dataset).toBe('ncbi_aedes_coi_small');
    expect(graphRequestBody.sequence_id).toBe('LC881945_1_AALB_COI');
    expect(screen.getAllByText('Animalia').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Aedes').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Safe LCA').length).toBeGreaterThan(0);
    expect(screen.getByText('Evidence decision')).toBeInTheDocument();
    expect(screen.getByText('Lineage path')).toBeInTheDocument();
    expect(screen.getByText('Hit comparison')).toBeInTheDocument();
    expect(screen.getByText('Graph zoom')).toBeInTheDocument();
    expect(screen.getByText('Source monitor')).toBeInTheDocument();
    expect(screen.getByText('Segment map')).toBeInTheDocument();
    expect(screen.getByText('1-72 bp')).toBeInTheDocument();
    expect(screen.getByText('COI-5P matched region')).toBeInTheDocument();
    expect(screen.getByText('125%')).toBeInTheDocument();
    fireEvent.click(screen.getByLabelText('Zoom in graph'));
    expect(screen.getByText('150%')).toBeInTheDocument();
    fireEvent.click(screen.getByLabelText('Fit graph to panel'));
    expect(document.querySelector('.fragment-zoom-value')?.textContent).toBe('Fit');
    expect(screen.getByText('Graph is limited to the selected reference dataset.')).toBeInTheDocument();
    expect(screen.getAllByText('Aedes albopictus').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Aedes aegypti').length).toBeGreaterThan(0);

    fireEvent.click(screen.getByLabelText('Select hit Aedes aegypti'));
    expect(document.querySelector('.shared-claim-lock')?.textContent).toContain('Aedes aegypti');
    expect(document.querySelector('.shared-claim-lock')?.textContent).toContain('Alternative reference hit');
    expect(document.querySelectorAll('.standard-hit-row.selected').length).toBe(1);
    expect(document.querySelectorAll('.standard-hit-safe-link.selected').length).toBeGreaterThan(0);

    fireEvent.click(screen.getByLabelText('Select lineage taxon Animalia'));
    expect(document.querySelector('.shared-claim-lock')?.textContent).toContain('Animalia');
    expect(document.querySelectorAll('.standard-lineage-node.selected').length).toBe(1);
  });

  it('renders the short-fragment shared dashboard without collapsing taxa into a tangled tree', async () => {
    let graphRequestBody = null;
    vi.spyOn(globalThis, 'fetch').mockImplementation((url, options) => {
      const textUrl = String(url);
      if (textUrl.endsWith('/api/barcode/demo-scenarios')) {
        return Promise.resolve(new Response(JSON.stringify(demoScenarios), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/reference-status')) {
        return Promise.resolve(new Response(JSON.stringify({ status: 'ready', message: 'Compiler ready.' }), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/search-status')) {
        return Promise.resolve(new Response(JSON.stringify(searchStatus), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/reference-datasets')) {
        return Promise.resolve(new Response(JSON.stringify(referenceDatasets), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/fragment-graph') && options?.method === 'POST') {
        graphRequestBody = JSON.parse(options.body);
        return Promise.resolve(new Response(JSON.stringify(sharedFragmentGraphPayload), { status: 200 }));
      }
      return Promise.resolve(new Response('{}', { status: 404 }));
    });

    render(<App />);
    fireEvent.click(await screen.findByText('Fragment graph'));
    fireEvent.click(screen.getByText('Run shared short-fragment tree'));

    await waitFor(() => expect(screen.getByText('Short-fragment evidence')).toBeInTheDocument());
    expect(graphRequestBody.reference_dataset).toBe('culicidae_short_shared_marker');
    expect(screen.getByText('Graph zoom')).toBeInTheDocument();
    expect(screen.getByText('125%')).toBeInTheDocument();
    expect(screen.getByText('Taxonomic cluster map')).toBeInTheDocument();
    expect(screen.getByText('Safe LCA network')).toBeInTheDocument();
    expect(screen.getByText('Species claim blocked')).toBeInTheDocument();
    expect(screen.getByText('Source monitor')).toBeInTheDocument();
    expect(screen.getByText('Segment map')).toBeInTheDocument();
    expect(screen.getByText('1-32 bp')).toBeInTheDocument();
    expect(screen.getAllByText('Culicidae').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Aedes').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Anopheles').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Culex').length).toBeGreaterThan(0);

    fireEvent.click(screen.getByLabelText('Select network species Culex quinquefasciatus'));
    expect(screen.getAllByText('Culex quinquefasciatus').length).toBeGreaterThan(0);
    expect(document.querySelector('.shared-claim-lock')?.textContent).toContain('Culex quinquefasciatus');
    expect(document.querySelector('.shared-claim-lock')?.textContent).toContain('reference species');
    expect(document.querySelectorAll('.shared-network-species.selected').length).toBe(1);
    expect(document.querySelectorAll('.shared-network-link.selected').length).toBeGreaterThan(0);

    fireEvent.click(screen.getByLabelText('Select network genus Culex'));
    expect(document.querySelector('.shared-claim-lock')?.textContent).toContain('Culex: 3 matched species');
    expect(document.querySelector('.shared-claim-lock')?.textContent).toContain('Several species in this genus');
  });

  it('uploads a custom reference FASTA and selects it for real-data search', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation((url, options) => {
      const textUrl = String(url);
      if (textUrl.endsWith('/api/barcode/demo-scenarios')) {
        return Promise.resolve(new Response(JSON.stringify(demoScenarios), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/reference-status')) {
        return Promise.resolve(new Response(JSON.stringify({ status: 'ready', message: 'Compiler ready.' }), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/search-status')) {
        return Promise.resolve(new Response(JSON.stringify(searchStatus), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/reference-datasets')) {
        return Promise.resolve(new Response(JSON.stringify(referenceDatasets), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/reference-datasets/upload') && options?.method === 'POST') {
        return Promise.resolve(new Response(JSON.stringify(uploadedReferencePayload), { status: 200 }));
      }
      return Promise.resolve(new Response('{}', { status: 404 }));
    });

    render(<App />);
    fireEvent.click(await screen.findByText('Run compiler'));

    fireEvent.change(screen.getByLabelText('Dataset title'), { target: { value: 'Custom Aedes COI' } });
    const fasta = new File(['>AALB|Aedes albopictus|species|1651430\nACGT\n'], 'custom_aedes.fasta', { type: 'text/plain' });
    fireEvent.change(screen.getByLabelText('Reference FASTA'), { target: { files: [fasta] } });
    fireEvent.click(screen.getByText('Upload reference FASTA'));

    expect((await screen.findAllByText(/Uploaded/)).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Custom Aedes COI/).length).toBeGreaterThan(0);
  });

  it('opens the visual lecture page with sequence and decision illustrations', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation((url) => {
      const textUrl = String(url);
      if (textUrl.endsWith('/api/barcode/demo-scenarios')) {
        return Promise.resolve(new Response(JSON.stringify(demoScenarios), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/reference-status')) {
        return Promise.resolve(new Response(JSON.stringify({ status: 'ready', message: 'Compiler ready.' }), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/search-status')) {
        return Promise.resolve(new Response(JSON.stringify(searchStatus), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/reference-datasets')) {
        return Promise.resolve(new Response(JSON.stringify(referenceDatasets), { status: 200 }));
      }
      return Promise.resolve(new Response('{}', { status: 404 }));
    });

    render(<App />);
    fireEvent.click(await screen.findByText('Visual lecture'));

    expect(screen.getByText('Sequence visual lab: from DNA letters to safe GBIF evidence.')).toBeInTheDocument();
    expect(screen.getByText('Live analysis animation')).toBeInTheDocument();
    expect(screen.getByText('How EcoGenesis reaches a bounded claim, step by step.')).toBeInTheDocument();
    expect(screen.getByText('Generated analysis pictures')).toBeInTheDocument();
    expect(screen.getByText('The whole analysis is now visible as a picture sequence.')).toBeInTheDocument();
    expect(screen.getByAltText('Generated six-panel EcoGenesis analysis sequence from input sequence to evidence pack')).toBeInTheDocument();
    expect(screen.getByText('Input sequence')).toBeInTheDocument();
    expect(screen.getByText('Alignment scan')).toBeInTheDocument();
    expect(screen.getAllByText('Evidence pack').length).toBeGreaterThan(0);
    expect(screen.getByText('Why the output is correct')).toBeInTheDocument();
    expect(screen.getByText('Why overclaims are blocked')).toBeInTheDocument();
    expect(screen.getByText('Why publication is separate')).toBeInTheDocument();
    expect(screen.getByText('DNA letters')).toBeInTheDocument();
    expect(screen.getAllByText('Query').length).toBeGreaterThan(0);
    expect(screen.getByText('Reference hit')).toBeInTheDocument();
    expect(screen.getByText('Nature-to-evidence cycle')).toBeInTheDocument();
    expect(screen.getByAltText('Nature to DNA marker evidence cycle showing biodiversity material, sequencing, compiler, open data map and conservation feedback')).toBeInTheDocument();
    expect(screen.getByText('The full cycle: nature produces signals, science turns them into safe evidence, and the evidence returns to nature as better decisions.')).toBeInTheDocument();
    expect(screen.getByText('DNA marker evidence, not one special sample type.')).toBeInTheDocument();
    expect(screen.getByText('Analysis story frames')).toBeInTheDocument();
    expect(screen.getByText('Six visual moments that make the EcoGenesis workflow easy to understand.')).toBeInTheDocument();
    expect(screen.getByText('Ready to present')).toBeInTheDocument();
    expect(screen.getByText('Biological material becomes marker evidence')).toBeInTheDocument();
    expect(screen.getByText('Reference search creates competing hits')).toBeInTheDocument();
    expect(screen.getByText('Shared fragments become a taxonomic tree')).toBeInTheDocument();
    expect(screen.getByText('Publication evidence package is produced')).toBeInTheDocument();
    expect(screen.getByText('Biodiversity source')).toBeInTheDocument();
    expect(screen.getByText('Marker selection')).toBeInTheDocument();
    expect(screen.getByText('Nature feedback')).toBeInTheDocument();
    expect(screen.getByText('For nature')).toBeInTheDocument();
    expect(screen.getByText('Why this matters in science')).toBeInTheDocument();
    expect(screen.getByText('The project is about converting molecular signals into reusable evidence.')).toBeInTheDocument();
    expect(screen.getByText('Scientific change')).toBeInTheDocument();
    expect(screen.getByText('Who uses it')).toBeInTheDocument();
    expect(screen.getByText('Top-hit trap')).toBeInTheDocument();
    expect(screen.getByText('LCA tree')).toBeInTheDocument();
    expect(screen.getAllByText('Barcode gap').length).toBeGreaterThan(0);
    expect(screen.getByText('Diagnostic k-mers')).toBeInTheDocument();
    expect(screen.getByText('What can I claim?')).toBeInTheDocument();
    expect(screen.getByText('Where this leads')).toBeInTheDocument();
    expect(screen.getByText('From one compiler to a Molecular Evidence Graph for GBIF.')).toBeInTheDocument();
  });

  it('opens the safe-claim picture directly from the URL hash', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation((url) => {
      const textUrl = String(url);
      if (textUrl.endsWith('/api/barcode/demo-scenarios')) {
        return Promise.resolve(new Response(JSON.stringify(demoScenarios), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/reference-status')) {
        return Promise.resolve(new Response(JSON.stringify({ status: 'ready', message: 'Compiler ready.' }), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/search-status')) {
        return Promise.resolve(new Response(JSON.stringify(searchStatus), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/reference-datasets')) {
        return Promise.resolve(new Response(JSON.stringify(referenceDatasets), { status: 200 }));
      }
      return Promise.resolve(new Response('{}', { status: 404 }));
    });

    window.history.pushState({}, '', '/#safe-claim-picture');
    render(<App />);

    expect(await screen.findByText('Final mental model')).toBeInTheDocument();
    expect(screen.getByText('EcoGenesis is a scientific checkpoint before GBIF publication.')).toBeInTheDocument();
    expect(screen.getAllByText('Evidence pack').length).toBeGreaterThan(0);
  });

  it('opens the live analysis animation directly from the URL hash', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation((url) => {
      const textUrl = String(url);
      if (textUrl.endsWith('/api/barcode/demo-scenarios')) {
        return Promise.resolve(new Response(JSON.stringify(demoScenarios), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/reference-status')) {
        return Promise.resolve(new Response(JSON.stringify({ status: 'ready', message: 'Compiler ready.' }), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/search-status')) {
        return Promise.resolve(new Response(JSON.stringify(searchStatus), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/reference-datasets')) {
        return Promise.resolve(new Response(JSON.stringify(referenceDatasets), { status: 200 }));
      }
      return Promise.resolve(new Response('{}', { status: 404 }));
    });

    window.history.pushState({}, '', '/#analysis-animation');
    render(<App />);

    expect(await screen.findByText('Live analysis animation')).toBeInTheDocument();
    expect(screen.getByText('Safe taxon + explicit blockers')).toBeInTheDocument();
    expect(screen.getByText('Final claim')).toBeInTheDocument();
  });

  it('opens the generated analysis picture sequence directly from the URL hash', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation((url) => {
      const textUrl = String(url);
      if (textUrl.endsWith('/api/barcode/demo-scenarios')) {
        return Promise.resolve(new Response(JSON.stringify(demoScenarios), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/reference-status')) {
        return Promise.resolve(new Response(JSON.stringify({ status: 'ready', message: 'Compiler ready.' }), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/search-status')) {
        return Promise.resolve(new Response(JSON.stringify(searchStatus), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/reference-datasets')) {
        return Promise.resolve(new Response(JSON.stringify(referenceDatasets), { status: 200 }));
      }
      return Promise.resolve(new Response('{}', { status: 404 }));
    });

    window.history.pushState({}, '', '/#analysis-picture-sequence');
    render(<App />);

    expect(await screen.findByText('Generated analysis pictures')).toBeInTheDocument();
    expect(screen.getByText('Contest presentation ready')).toBeInTheDocument();
    expect(screen.getByText('No hidden overclaim')).toBeInTheDocument();
    expect(screen.getByText('Reproducible export')).toBeInTheDocument();
  });

  it('opens the proof and formulas page', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation((url) => {
      const textUrl = String(url);
      if (textUrl.endsWith('/api/barcode/demo-scenarios')) {
        return Promise.resolve(new Response(JSON.stringify(demoScenarios), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/reference-status')) {
        return Promise.resolve(new Response(JSON.stringify({ status: 'ready', message: 'Compiler ready.' }), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/search-status')) {
        return Promise.resolve(new Response(JSON.stringify(searchStatus), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/reference-datasets')) {
        return Promise.resolve(new Response(JSON.stringify(referenceDatasets), { status: 200 }));
      }
      return Promise.resolve(new Response('{}', { status: 404 }));
    });

    render(<App />);
    fireEvent.click(await screen.findByText('Math & proof'));

    expect(screen.getByText('Evidence basis')).toBeInTheDocument();
    expect(screen.getAllByText('Evidence Conversion Problem').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Repair optimizer').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Protein sanity').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Evidence graph').length).toBeGreaterThan(0);
    expect(screen.getByText('Full mathematical notebook')).toBeInTheDocument();
    expect(screen.getByText('Rendered mathematical notation')).toBeInTheDocument();
    expect(screen.getByText('Reference completeness')).toBeInTheDocument();
    expect(screen.getByText('Reference Completeness Gate')).toBeInTheDocument();
    expect(screen.getByText('Assay Evidence Gate for eDNA and metabarcoding')).toBeInTheDocument();
    expect(screen.getByText('Conversion and overclaim metrics')).toBeInTheDocument();
    expect(screen.getByText('Test analysis')).toBeInTheDocument();
    expect(screen.getByText('Live GBIF smoke')).toBeInTheDocument();
    expect(screen.getByText('Decision function')).toBeInTheDocument();
    expect(screen.getByText('Proof by contradiction')).toBeInTheDocument();
    expect(screen.getAllByText(/p_false_positive/).length).toBeGreaterThan(0);
  });

  it('opens the research audit page', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation((url) => {
      const textUrl = String(url);
      if (textUrl.endsWith('/api/barcode/demo-scenarios')) {
        return Promise.resolve(new Response(JSON.stringify(demoScenarios), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/reference-status')) {
        return Promise.resolve(new Response(JSON.stringify({ status: 'ready', message: 'Compiler ready.' }), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/search-status')) {
        return Promise.resolve(new Response(JSON.stringify(searchStatus), { status: 200 }));
      }
      if (textUrl.endsWith('/api/barcode/reference-datasets')) {
        return Promise.resolve(new Response(JSON.stringify(referenceDatasets), { status: 200 }));
      }
      return Promise.resolve(new Response('{}', { status: 404 }));
    });

    render(<App />);
    fireEvent.click(await screen.findByText('Research audit'));

    expect(screen.getByText('Research audit layer')).toBeInTheDocument();
    expect(screen.getByText('Occurrence Evidence Audit Shell')).toBeInTheDocument();
    expect(screen.getByText('Downloaded records are now separated from deduplicated records.')).toBeInTheDocument();
    expect(screen.getByText('Risk heatmap')).toBeInTheDocument();
    expect(screen.getByText('theory_claims_100.csv')).toBeInTheDocument();
    expect(screen.getByText('The next winning step is fragment-level evidence, not another abstract score.')).toBeInTheDocument();
  });
});
