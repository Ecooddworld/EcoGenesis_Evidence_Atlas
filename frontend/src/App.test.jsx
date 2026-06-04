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
  records: [
    {
      sequence_id: 'AALB-COI-good',
      decision_class: 'species-safe',
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
    expect(screen.getByText('Publishable (1)')).toBeInTheDocument();
  });

  it('runs reference search and compiles the returned hits', async () => {
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
        return Promise.resolve(new Response(JSON.stringify(searchPayload), { status: 200 }));
      }
      return Promise.resolve(new Response('{}', { status: 404 }));
    });

    render(<App />);
    fireEvent.click(await screen.findByText('Run compiler'));
    fireEvent.click(screen.getByText('Search reference & compile'));

    await waitFor(() => expect(screen.getAllByText('species-safe').length).toBeGreaterThan(0));
    expect(screen.getByText('Naive vs EcoGenesis')).toBeInTheDocument();
    expect(screen.getByText('python-local')).toBeInTheDocument();
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

    expect(await screen.findByText(/Uploaded/)).toBeInTheDocument();
    expect(screen.getAllByText(/Custom Aedes COI/).length).toBeGreaterThan(0);
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
