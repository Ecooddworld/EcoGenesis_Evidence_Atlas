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

const exportItem = (runId, name) => ({ name, url: `/api/barcode/runs/${runId}/exports/${name}` });

const coreExportNames = [
  'evidence_pack.zip',
  'sequence_safety_table.csv',
  'data_accounting_ledger.csv',
  'molecular_evidence_report.html',
  'methods_text.md',
  'citations.md',
  'hard_gate_audit.csv',
  'naive_top_hit_overclaims.csv',
];

const gsegGsigExportNames = [
  'theorem_checklist.json',
  'verified_segment_evidence_array.csv',
  'verified_segment_evidence_array.parquet',
  'gseg_graph_schema.json',
  'gsig_graph_schema.yaml',
  'graph_provenance_audit.csv',
  'graph_roundtrip_audit.json',
  'sharedness_overclaim_audit.csv',
  'function_claim_boundary_audit.csv',
  'ai_output_guardrail_audit.csv',
  'judge_reproducibility_report.md',
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
  exports: [...coreExportNames, ...gsegGsigExportNames].map((name) => exportItem('barcode123', name)),
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
    ...coreExportNames,
    'publication_blockers.csv',
    'dwc_occurrence_core_publishable.csv',
    ...gsegGsigExportNames,
  ].map((name) => exportItem('barcodecsv123', name)),
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
    not_supported: ['natural occurrence, absence, abundance or distribution', 'global species conclusion outside the selected reference dataset'],
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

const observatoryStatus = {
  status: 'ready',
  default_demo: {
    claim_boundary: 'GBIF occurrence records provide context only; molecular claims come from barcode/GSEG gates.',
  },
  latest_run: null,
};

const observatorySources = {
  registry_version: 'GSIG-OBS-SOURCES-1.0',
  audit: { status: 'pass' },
  sources: [
    {
      source_id: 'gbif_occurrence_api',
      name: 'GBIF Occurrence API and Download API',
      status: 'contest_integration',
      evidence_role: 'occurrence/sample/geography/context; not molecular proof by itself',
      allowed_claims: ['occurrence_context', 'dataset_context'],
      blocked_claims: ['species_truth_from_occurrence_without_molecular_gate'],
    },
    {
      source_id: 'project_user_uploads',
      name: 'User supplied barcode result tables',
      status: 'existing_foundation',
      evidence_role: 'molecular evidence after deterministic gates',
      allowed_claims: ['taxon_supported'],
      blocked_claims: ['phenotype_truth'],
    },
  ],
};

const observatoryCreated = {
  run_id: 'obs123',
  status: 'completed',
  summary: {
    taxon: 'Aedes albopictus',
    mode: 'live_gbif_small',
    source_mode: 'fixture_fallback',
    fallback_used: true,
    normalized_occurrence_records: 12,
    segments: 4,
    vsea_rows: 4,
    claim_states: { taxon_supported: 3, weak_hypothesis: 1 },
    gbif_export_states: { candidate_gbif_row: 2, excluded_or_repair_required: 2 },
    graph_nodes: 14,
    graph_edges: 17,
    hard_gate_status: 'pass',
    hard_gate_failures: 0,
  },
  exports: [
    'observatory_evidence_pack.zip',
    'observatory_report.md',
    'snapshot_manifest.json',
    'observatory_vsea.parquet',
    'observatory_graph.jsonld',
    'gbif_export_preview.csv',
    'ai_ready_dataset.jsonl',
    'proof_summary.json',
  ].map((name) => ({ name, url: `/api/observatory/runs/obs123/exports/${name}` })),
};

const observatoryRunDetail = {
  run: { run_id: 'obs123', mode: 'live_gbif_small', ruleset_version: 'GSIG-OBS-1.0+barcode-gbif-compiler-v2' },
  summary: observatoryCreated.summary,
  snapshot_manifest: {
    snapshot_id: 'gbif-aedes-spain-abc123',
    snapshot_hash: 'abc123def4567890',
    source_mode: 'fixture_fallback',
    claim_boundary: 'Claim strength is bounded by molecular gates, publication gates and source provenance.',
  },
  normalized_occurrence_context: [
    {
      row_index: 1,
      gbifID: 'gbif-1',
      datasetKey: 'dataset-a',
      license: 'CC_BY_4_0',
      decimalLatitude: 40.4,
      decimalLongitude: -3.7,
      eventDate: '2026-04-18',
    },
    {
      row_index: 2,
      gbifID: 'gbif-2',
      datasetKey: 'dataset-b',
      license: 'CC_BY_4_0',
      decimalLatitude: 41.4,
      decimalLongitude: 2.1,
      year: 2025,
    },
  ],
  vsea: [
    {
      vsea_id: 'obs-vsea:AALB-COI-good:1',
      sequence_id: 'AALB-COI-good',
      segment_id: 'segment:AALB-COI-good:1-650',
      target_label: 'Aedes albopictus',
      safe_rank: 'species',
      claim_state: 'taxon_supported',
      gbif_export_state: 'candidate_gbif_row',
      context_claim_boundary: 'GBIF context is linked after hashing; it does not promote claim_state.',
    },
    {
      vsea_id: 'obs-vsea:AALB-COI-short:2',
      sequence_id: 'AALB-COI-short',
      segment_id: 'segment:AALB-COI-short:1-650',
      target_label: 'Aedes albopictus',
      safe_rank: 'none',
      claim_state: 'weak_hypothesis',
      gbif_export_state: 'excluded_or_repair_required',
      context_claim_boundary: 'GBIF context is linked after hashing; it does not promote claim_state.',
    },
  ],
  proof_summary: {
    rows: [
      { id: 'OPO-01', severity: 'hard_gate', status: 'pass', artifact: 'source_registry_audit.json' },
      { id: 'OPO-07', severity: 'hard_gate', status: 'pass', artifact: 'visualization_guardrail_audit.csv' },
      { id: 'OPO-20', severity: 'hard_gate', status: 'pass', artifact: 'judge_mode_non_claims_audit.csv' },
    ],
  },
  graph: {
    '@context': { ecogenesis: 'https://example.org/ecogenesis#' },
    '@graph': [
      { id: 'run:obs123', type: 'Run', mode: 'live_gbif_small', ruleset_version: 'GSIG-OBS-1.0+barcode-gbif-compiler-v2', provenance_hash: 'runhash' },
      { id: 'source:gbif_occurrence_api', type: 'Source', role: 'occurrence_context', claim_state: 'occurrence_context', provenance_hash: 'sourcehash1' },
      { id: 'source:project_user_uploads', type: 'Source', role: 'molecular_evidence', claim_state: 'taxon_supported', provenance_hash: 'sourcehash2' },
      { id: 'snapshot:gbif-aedes-spain-abc123', type: 'Snapshot', snapshot_id: 'gbif-aedes-spain-abc123', snapshot_hash: 'abc123def4567890', source_mode: 'fixture_fallback', claim_state: 'occurrence_context', provenance_hash: 'snaphash' },
      { id: 'segment:good', type: 'Segment', segment_id: 'segment:AALB-COI-good:1-650', claim_state: 'taxon_supported', ruleset_version: 'GSIG-OBS-1.0+barcode-gbif-compiler-v2', provenance_hash: 'seghash1' },
      { id: 'segment:good', type: 'Segment', segment_id: 'segment:AALB-COI-good-copy:1-650', claim_state: 'taxon_supported', ruleset_version: 'GSIG-OBS-1.0+barcode-gbif-compiler-v2', provenance_hash: 'seghash1b' },
      { id: 'segment:short', type: 'Segment', segment_id: 'segment:AALB-COI-short:1-650', claim_state: 'weak_hypothesis', ruleset_version: 'GSIG-OBS-1.0+barcode-gbif-compiler-v2', provenance_hash: 'seghash2' },
      { id: 'taxon:species:Aedes albopictus', type: 'Taxon', label: 'Aedes albopictus', safe_rank: 'species', claim_state: 'taxon_supported', provenance_hash: 'taxhash1' },
      { id: 'taxon:genus:Aedes', type: 'Taxon', label: 'Aedes', safe_rank: 'genus', claim_state: 'taxon_supported', provenance_hash: 'taxhash2' },
      { id: 'claim:good', type: 'EvidenceClaim', claim_state: 'taxon_supported', claim_boundary: 'Species-level molecular assignment candidate for Aedes albopictus within the supplied reference context.', caveats: 'not a distribution claim', provenance_hash: 'claimhash1' },
      { id: 'claim:short', type: 'EvidenceClaim', claim_state: 'weak_hypothesis', claim_boundary: 'Review-only molecular hint; sequence is too short for a safe taxonomic claim.', caveats: 'not publishable as a verified positive', provenance_hash: 'claimhash2' },
      { id: 'blocker:short-read', type: 'Blocker', label: 'Short fragment blocker', claim_state: 'blocked', claim_boundary: 'Blocked claims remain visible and queryable.', provenance_hash: 'blockhash' },
      { id: 'export:gbif-preview', type: 'Export', label: 'GBIF export preview', claim_state: 'taxon_supported', provenance_hash: 'exporthash' },
      { id: 'edge:run:snapshot', type: 'USES_SNAPSHOT', source: 'run:obs123', target: 'snapshot:gbif-aedes-spain-abc123', claim_state: 'occurrence_context', provenance_hash: 'edgehash1' },
      { id: 'edge:snapshot:source', type: 'FROM_SOURCE', source: 'snapshot:gbif-aedes-spain-abc123', target: 'source:gbif_occurrence_api', claim_state: 'occurrence_context', provenance_hash: 'edgehash2' },
      { id: 'edge:good:source', type: 'FROM_SOURCE', source: 'segment:good', target: 'source:project_user_uploads', claim_state: 'taxon_supported', provenance_hash: 'edgehash3' },
      { id: 'edge:short:source', type: 'FROM_SOURCE', source: 'segment:short', target: 'source:project_user_uploads', claim_state: 'weak_hypothesis', provenance_hash: 'edgehash4' },
      { id: 'edge:good:species', type: 'COLLAPSES_TO_LCA', source: 'segment:good', target: 'taxon:species:Aedes albopictus', claim_state: 'taxon_supported', provenance_hash: 'edgehash5' },
      { id: 'edge:short:genus', type: 'COLLAPSES_TO_LCA', source: 'segment:short', target: 'taxon:genus:Aedes', claim_state: 'weak_hypothesis', provenance_hash: 'edgehash6' },
      { id: 'edge:good:claim', type: 'SUPPORTS_CLAIM', source: 'segment:good', target: 'claim:good', claim_state: 'taxon_supported', provenance_hash: 'edgehash7' },
      { id: 'edge:short:claim', type: 'SUPPORTS_CLAIM', source: 'segment:short', target: 'claim:short', claim_state: 'weak_hypothesis', provenance_hash: 'edgehash8' },
      { id: 'edge:short:blocker', type: 'BLOCKED_BY', source: 'claim:short', target: 'blocker:short-read', claim_state: 'blocked', provenance_hash: 'edgehash9' },
      { id: 'edge:claim:export', type: 'EXPORTS_TO', source: 'claim:good', target: 'export:gbif-preview', claim_state: 'taxon_supported', provenance_hash: 'edgehash10' },
    ],
  },
  audit_artifacts: {
    judge_mode_non_claims_audit: [{ planned_sources_visible: 5 }],
  },
  exports: observatoryCreated.exports,
};

const observatoryVerification = {
  schema: 'ecogenesis.gsig.observatory.run_output_verification.v1',
  run_id: 'obs123',
  summary: {
    status: 'pass',
    checks: 67,
    failed: 0,
    exports: 43,
    vsea_rows: 4,
    occurrence_rows: 12,
    zip_entries: 42,
  },
  checks: [
    { name: 'visualization_no_promotion', status: 'pass', observed: { pass: 4 } },
    { name: 'zip_entry_checksums_match_manifest', status: 'pass', observed: '42 entries checked' },
  ],
};

const competitionReports = {
  schema: 'ecogenesis.competition_reports.index.v1',
  status: 'pass',
  reports: [
    {
      schema: 'ecogenesis.competition_reports.summary.v1',
      report_id: 'competition-100-sequences',
      title: 'Competition 100-sequence verification batch',
      summary: {
        status: 'pass',
        records: 100,
        expected_matched: 100,
        expected_failed: 0,
        exports: 89,
        zip_entries: 88,
      },
      decision_classes: {
        'species-safe': 25,
        'genus-safe': 25,
        weak: 25,
        'not-publishable': 25,
      },
      downloads: [
        {
          name: 'competition_100_sequence_report.md',
          url: '/api/competition-reports/competition-100-sequences/files/competition_100_sequence_report.md',
        },
        {
          name: 'competition_100_sequence_results.csv',
          url: '/api/competition-reports/competition-100-sequences/files/competition_100_sequence_results.csv',
        },
      ],
    },
    {
      schema: 'ecogenesis.competition_reports.summary.v1',
      report_id: 'adversarial-100-sequences',
      title: 'Adversarial 100-sequence fail-closed stress batch',
      summary: {
        status: 'pass',
        records: 100,
        expected_matched: 100,
        expected_failed: 0,
        exports: 89,
        zip_entries: 88,
      },
      decision_classes: {
        'species-safe': 10,
        'genus-safe': 20,
        ambiguous: 20,
        'no-match': 10,
        weak: 10,
        'not-publishable': 30,
      },
      downloads: [
        {
          name: 'adversarial_100_sequence_report.md',
          url: '/api/competition-reports/adversarial-100-sequences/files/adversarial_100_sequence_report.md',
        },
      ],
    },
  ],
};

const contestReadiness = {
  schema: 'ecogenesis.contest_readiness.dossier.v1',
  status: 'pass',
  summary: {
    checks: 17,
    failed: 0,
    competition_reports: 2,
    competition_status: 'pass',
    observatory_run_id: 'obs123',
    observatory_status: 'pass',
    reference_backend: 'vsearch',
  },
  checks: [{ name: 'observatory_run_verification_pass', status: 'pass', observed: 'pass' }],
  downloads: [
    { name: 'contest_readiness.json', url: '/api/contest-readiness' },
    { name: 'contest_readiness.md', url: '/api/contest-readiness/report.md' },
    { name: 'latest_observatory_verification.md', url: '/api/observatory/runs/obs123/verification/report.md' },
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

    expect(await screen.findByText('Barcode-to-GBIF Evidence Compiler')).toBeInTheDocument();
    expect(screen.getByText('Overview')).toBeInTheDocument();
    expect(screen.getByText('Safe molecular evidence. Rank-aware decisions. GBIF-ready exports.')).toBeInTheDocument();
    expect(screen.getByText('What it does')).toBeInTheDocument();
    expect(screen.getByText('Evidence funnel')).toBeInTheDocument();
    expect(screen.getByText('Claim matrix')).toBeInTheDocument();
    expect(screen.getByText('Repair optimizer')).toBeInTheDocument();
    expect(screen.getByText('Validation')).toBeInTheDocument();
    expect(screen.getByText('Evidence Pack')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Run Compiler' })).toHaveAttribute('href', '/run-compiler');
    expect(screen.getByRole('link', { name: 'Evidence Map' })).toHaveAttribute('href', '/evidence-map');
    expect(screen.getByRole('link', { name: 'Fragment Graph' })).toHaveAttribute('href', '/fragment-graph');
    expect(screen.getByRole('link', { name: 'Validation' })).toHaveAttribute('href', '/validation');
    expect(screen.getByRole('link', { name: 'Methods & Audits' })).toHaveAttribute('href', '/methods');
    expect(screen.getByRole('link', { name: 'Workflow' })).toHaveAttribute('href', '/workflow');
    expect(screen.getByRole('link', { name: 'Evidence Pack' })).toHaveAttribute('href', '/evidence-pack');
    expect(screen.getByRole('link', { name: 'Privacy' })).toHaveAttribute('href', '/privacy');
    expect(screen.getByRole('link', { name: 'Visitor Metrics' })).toHaveAttribute('href', '/analytics');
    expect(screen.getByRole('link', { name: 'Video Presentation' })).toHaveAttribute('href', '/submission-video/');
    expect(screen.getAllByRole('link', { name: 'Source repository' })[0]).toHaveAttribute(
      'href',
      'https://github.com/Ecooddworld/EcoGenesis_Evidence_Atlas',
    );

    fireEvent.click(screen.getByText('Run mixed demo'));

    await waitFor(() => expect(screen.getAllByText('AALB-COI-good').length).toBeGreaterThan(0));
    expect(screen.getByText('species-safe')).toBeInTheDocument();
    expect(screen.getAllByText('evidence_pack.zip').length).toBeGreaterThan(0);
    expect(screen.getByText('Advanced graph artifacts')).toBeInTheDocument();
    expect(screen.getAllByText('theorem_checklist.json').length).toBeGreaterThan(0);
    expect(screen.getAllByText('verified_segment_evidence_array.parquet').length).toBeGreaterThan(0);
    expect(screen.getByText('Data accounting ledger')).toBeInTheDocument();
    expect(screen.getByText('publishable_candidate_n')).toBeInTheDocument();
  });

  it('opens privacy notice and token-protected visitor metrics', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation((url, options) => {
      const textUrl = String(url);
      if (textUrl.endsWith('/api/analytics/pageview')) {
        return Promise.resolve(new Response(JSON.stringify({ tracked: true }), { status: 200 }));
      }
      if (textUrl.endsWith('/api/analytics/summary')) {
        expect(options?.headers?.['X-Analytics-Token']).toBe('test-token');
        return Promise.resolve(new Response(JSON.stringify({
          privacy_mode: 'first-party, no cookies, raw IP not stored',
          retention_days: 90,
          totals: {
            pageviews_24h: 4,
            visitors_24h: 2,
            pageviews_7d: 9,
            visitors_7d: 5,
            stored_pageviews: 9,
          },
          top_pages: [{ path: '/workflow', pageviews: 4, visitors: 2 }],
          referrers: [{ referrer_host: 'direct', pageviews: 4 }],
          daily: [{ day: '2026-06-27', pageviews: 4, visitors: 2 }],
          devices: [{ device_type: 'desktop', pageviews: 4 }],
          browsers: [{ user_agent_family: 'safari', pageviews: 4 }],
          recent: [{
            ts: '2026-06-27T10:00:00+00:00',
            path: '/workflow',
            referrer_host: 'direct',
            device_type: 'desktop',
            user_agent_family: 'safari',
            language: 'en',
          }],
        }), { status: 200 }));
      }
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

    fireEvent.click(await screen.findByRole('link', { name: 'Privacy' }));
    expect(await screen.findByText('Privacy-first contest site analytics and data handling.')).toBeInTheDocument();
    expect(screen.getByText('No raw IP address in the application analytics database.')).toBeInTheDocument();
    expect(screen.getByText('No cookie identifiers, advertising identifiers or third-party tracking pixels.')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('link', { name: 'Visitor Metrics' }));
    expect(await screen.findByText('Private first-party traffic dashboard.')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Admin token'), { target: { value: 'test-token' } });
    fireEvent.click(screen.getByText('Load metrics'));

    expect(await screen.findByText('Metrics loaded.')).toBeInTheDocument();
    expect(screen.getByText('Views / 24h')).toBeInTheDocument();
    expect(screen.getAllByText('/workflow').length).toBeGreaterThan(0);
    expect(document.body.textContent).toContain('Privacy mode: first-party, no cookies, raw IP not stored');
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
    fireEvent.click(await screen.findByText('Run Compiler'));

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
    fireEvent.click(await screen.findByText('Run Compiler'));

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
    expect(screen.getAllByText('graph_provenance_audit.csv').length).toBeGreaterThan(0);
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
    fireEvent.click(await screen.findByText('Run Compiler'));
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
    fireEvent.click(await screen.findByText('Fragment Graph'));

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
    fireEvent.click(await screen.findByText('Fragment Graph'));
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
    fireEvent.click(await screen.findByText('Run Compiler'));

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
    fireEvent.click(await screen.findByText('Workflow'));

    expect(window.location.pathname).toBe('/workflow');
    expect(screen.getByText('From molecular input to Evidence Pack, map and graph.')).toBeInTheDocument();
    expect(screen.getByText('Compiler logic animation')).toBeInTheDocument();
    expect(screen.getByText('How EcoGenesis reaches a bounded claim, step by step.')).toBeInTheDocument();
    expect(screen.getByText('Generated analysis pictures')).toBeInTheDocument();
    expect(screen.getByText('The analysis is visible as a picture sequence.')).toBeInTheDocument();
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

  it('opens shareable section routes directly', async () => {
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

    window.history.pushState({}, '', '/workflow');
    render(<App />);
    expect(await screen.findByText('From molecular input to Evidence Pack, map and graph.')).toBeInTheDocument();

    cleanup();
    window.history.pushState({}, '', '/evidence-pack');
    render(<App />);
    expect(await screen.findByText('Downloadable artifacts for rank decisions, publication readiness, repairs and audits.')).toBeInTheDocument();
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

    expect(await screen.findByText('Compiler logic animation')).toBeInTheDocument();
    expect(screen.getByText('Safe rank + explicit blockers')).toBeInTheDocument();
    expect(screen.getByText('Bounded result')).toBeInTheDocument();
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
    expect(screen.getByText('Contest presentation layer')).toBeInTheDocument();
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
    fireEvent.click(await screen.findByText('Methods & Audits'));

    expect(screen.getAllByText('Methods & Audits').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Evidence Conversion Problem').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Repair optimizer').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Protein sanity').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Evidence graph').length).toBeGreaterThan(0);
    expect(screen.getByText('Audit notebook')).toBeInTheDocument();
    expect(screen.getByText('Rendered mathematical notation')).toBeInTheDocument();
    expect(screen.getByText('Reference completeness')).toBeInTheDocument();
    expect(screen.getByText('Reference Completeness Gate')).toBeInTheDocument();
    expect(screen.getByText('Assay Evidence Gate for eDNA and metabarcoding')).toBeInTheDocument();
    expect(screen.getByText('Conversion and overclaim metrics')).toBeInTheDocument();
    expect(screen.getByText('Test analysis')).toBeInTheDocument();
    expect(screen.getByText('GBIF-backed smoke')).toBeInTheDocument();
    expect(screen.getByText('Decision function')).toBeInTheDocument();
    expect(screen.getByText('Invariant check')).toBeInTheDocument();
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
    fireEvent.click(await screen.findByText('Validation'));

    expect(screen.getAllByText('Validation').length).toBeGreaterThan(0);
    expect(screen.getByText('Occurrence Evidence Audit Shell')).toBeInTheDocument();
    expect(screen.getByText('Downloaded records are now separated from deduplicated records.')).toBeInTheDocument();
    expect(screen.getByText('Risk heatmap')).toBeInTheDocument();
    expect(screen.getByText('theory_claims_100.csv')).toBeInTheDocument();
    expect(screen.getByText('The next winning step is fragment-level evidence with audit-ready graph artifacts.')).toBeInTheDocument();
  });

  it('runs the Evidence Map layer and exposes the contest audit screens', async () => {
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
      if (textUrl.endsWith('/api/observatory/status')) {
        return Promise.resolve(new Response(JSON.stringify(observatoryStatus), { status: 200 }));
      }
      if (textUrl.endsWith('/api/observatory/sources')) {
        return Promise.resolve(new Response(JSON.stringify(observatorySources), { status: 200 }));
      }
      if (textUrl.endsWith('/api/competition-reports')) {
        return Promise.resolve(new Response(JSON.stringify(competitionReports), { status: 200 }));
      }
      if (textUrl.endsWith('/api/contest-readiness')) {
        return Promise.resolve(new Response(JSON.stringify(contestReadiness), { status: 200 }));
      }
      if (textUrl.endsWith('/api/observatory/run-demo') && options?.method === 'POST') {
        return Promise.resolve(new Response(JSON.stringify(observatoryCreated), { status: 200 }));
      }
      if (textUrl.endsWith('/api/observatory/runs/obs123/verification')) {
        return Promise.resolve(new Response(JSON.stringify(observatoryVerification), { status: 200 }));
      }
      if (textUrl.endsWith('/api/observatory/runs/obs123')) {
        return Promise.resolve(new Response(JSON.stringify(observatoryRunDetail), { status: 200 }));
      }
      return Promise.resolve(new Response('{}', { status: 404 }));
    });

    render(<App />);
    fireEvent.click(await screen.findByText('Evidence Map'));

    expect(screen.getAllByText('Evidence Map').length).toBeGreaterThan(0);
    expect(screen.getByText('Spatial context, molecular claim states, blockers and export boundaries in one evidence view.')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Run reproducible judge demo'));

    await waitFor(() => expect(screen.getByText('Hard gates pass')).toBeInTheDocument());
    expect(screen.getByText('Download Evidence Map Pack')).toBeInTheDocument();
    expect(screen.getByText('Evidence Atlas controls')).toBeInTheDocument();
    expect(screen.getByText('GBIF-ready / export candidate')).toBeInTheDocument();
    expect(screen.getByText('GBIF snapshot')).toBeInTheDocument();
    expect(screen.getByText('Output verification')).toBeInTheDocument();
    expect(screen.getByText('Run files checked')).toBeInTheDocument();
    expect(screen.getByText('Hashes, audit gates, tables, graph and ZIP contents agree for this exact run.')).toBeInTheDocument();
    expect(screen.getByText('Verification report')).toBeInTheDocument();
    expect(screen.getByText('Verification data')).toBeInTheDocument();
    expect(screen.getByText('67')).toBeInTheDocument();
    expect(screen.getAllByText('0').length).toBeGreaterThan(0);
    expect(screen.getByText('Evidence graph explorer')).toBeInTheDocument();
    expect(screen.getByText('Source, snapshot, segment, claim and export graph for the current map run.')).toBeInTheDocument();
    expect(screen.getAllByText('EcoGenesis Evidence Graph').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Claim states, blockers, provenance and export boundaries.').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Evidence Map').length).toBeGreaterThan(0);
    expect(screen.getByText('Open in GBIF')).toBeInTheDocument();
    expect(screen.getByText('Review flags')).toBeInTheDocument();
    expect(screen.queryByText('Source evidence map')).not.toBeInTheDocument();
    expect(screen.getByText('Graph nodes')).toBeInTheDocument();
    expect(screen.getAllByText('Graph edges').length).toBeGreaterThan(0);
    expect(screen.getByText('Merged ids')).toBeInTheDocument();
    await waitFor(() => expect(screen.getAllByText('AALB-COI-good').length).toBeGreaterThan(0));
    expect(screen.getAllByText('AALB-COI-short').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Short fragment blocker').length).toBeGreaterThan(0);
    expect(screen.getByText('Guardrail: UI preserves claim states.')).toBeInTheDocument();
    expect(screen.getByText('Guardrail: blocked rows stay visible.')).toBeInTheDocument();
    fireEvent.click(screen.getAllByRole('button', { name: /AALB-COI-good/i })[0]);
    expect(screen.getByText('Merged variants')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Claim state'), { target: { value: 'weak_hypothesis' } });
    expect(screen.getAllByText('AALB-COI-short').length).toBeGreaterThan(0);
    expect(screen.getByText('none')).toBeInTheDocument();
    expect(screen.getAllByText(/Claim strength is bounded by molecular gates, publication gates and source provenance/i).length).toBeGreaterThan(0);
    expect(screen.getByText('Contest readiness dossier')).toBeInTheDocument();
    expect(screen.getByText('All current contest gates are passing.')).toBeInTheDocument();
    expect(screen.getByText('contest_readiness.md')).toBeInTheDocument();
    expect(screen.getByText('latest_observatory_verification.md')).toBeInTheDocument();
    expect(screen.getByText('Competition readiness')).toBeInTheDocument();
    expect(screen.getByText('Competition 100-sequence verification batch')).toBeInTheDocument();
    expect(screen.getByText('Adversarial 100-sequence fail-closed stress batch')).toBeInTheDocument();
    expect(screen.getAllByText('100').length).toBeGreaterThan(0);
    expect(screen.getByText('competition_100_sequence_report.md')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'VSEA' }));
    expect(screen.getAllByText('AALB-COI-good').length).toBeGreaterThan(0);
    expect(screen.getAllByText('taxon_supported').length).toBeGreaterThan(0);
    expect(screen.getAllByText('weak_hypothesis').length).toBeGreaterThan(0);

    fireEvent.click(screen.getByRole('button', { name: 'Exports' }));
    expect(screen.getByText('observatory_run_verification.md')).toBeInTheDocument();
    expect(screen.getByText('observatory_run_verification.json')).toBeInTheDocument();

    fireEvent.click(screen.getByText('Judge'));
    expect(screen.getByText('OPO-01')).toBeInTheDocument();
    expect(screen.getByText('visualization_guardrail_audit.csv')).toBeInTheDocument();
    expect(screen.getByText(/Planned sources visible: 5/)).toBeInTheDocument();
  });
});
