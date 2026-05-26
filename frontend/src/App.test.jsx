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
    expect(screen.getByText('Submission overview')).toBeInTheDocument();
    expect(screen.getByText('Research audit')).toBeInTheDocument();

    fireEvent.click(screen.getByText('Run mixed demo'));

    await waitFor(() => expect(screen.getAllByText('AALB-COI-good').length).toBeGreaterThan(0));
    expect(screen.getByText('species-safe')).toBeInTheDocument();
    expect(screen.getByText('evidence_pack.zip')).toBeInTheDocument();
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
      return Promise.resolve(new Response('{}', { status: 404 }));
    });

    render(<App />);
    fireEvent.click(await screen.findByText('Compiler workbench'));

    expect(screen.getByLabelText('Demo case')).toBeInTheDocument();
    expect(screen.getByText('Generate Evidence Package')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Advanced request JSON'));
    expect(screen.getByLabelText('Compiler request JSON')).toBeInTheDocument();
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
      return Promise.resolve(new Response('{}', { status: 404 }));
    });

    render(<App />);
    fireEvent.click(await screen.findByText('Proof & formulas'));

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
      return Promise.resolve(new Response('{}', { status: 404 }));
    });

    render(<App />);
    fireEvent.click(await screen.findByText('Research audit'));

    expect(screen.getByText('Research audit layer')).toBeInTheDocument();
    expect(screen.getByText('Occurrence Evidence Audit Shell')).toBeInTheDocument();
    expect(screen.getByText('Downloaded records are now separated from deduplicated records.')).toBeInTheDocument();
    expect(screen.getByText('theory_claims_100.csv')).toBeInTheDocument();
    expect(screen.getByText('The next winning step is fragment-level evidence, not another abstract score.')).toBeInTheDocument();
  });
});
