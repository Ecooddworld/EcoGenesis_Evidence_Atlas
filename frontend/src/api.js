const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:18100';

export function exportUrl(path) {
  if (!path) return '#';
  return `${API_BASE_URL}${path}`;
}

export async function runEvidencePassport(payload) {
  const response = await fetch(`${API_BASE_URL}/api/evidence/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`Evidence run failed: ${response.status}`);
  }
  return response.json();
}

export async function getBarcodeDemoScenarios() {
  const response = await fetch(`${API_BASE_URL}/api/barcode/demo-scenarios`);
  if (!response.ok) {
    throw new Error(`Barcode demo scenarios could not be loaded: ${response.status}`);
  }
  return response.json();
}

export async function getBarcodeReferenceStatus() {
  const response = await fetch(`${API_BASE_URL}/api/barcode/reference-status`);
  if (!response.ok) {
    throw new Error(`Barcode reference status could not be loaded: ${response.status}`);
  }
  return response.json();
}

export async function getBarcodeSearchStatus() {
  const response = await fetch(`${API_BASE_URL}/api/barcode/search-status`);
  if (!response.ok) {
    throw new Error(`Barcode search status could not be loaded: ${response.status}`);
  }
  return response.json();
}

export async function getBarcodeReferenceDatasets() {
  const response = await fetch(`${API_BASE_URL}/api/barcode/reference-datasets`);
  if (!response.ok) {
    throw new Error(`Reference datasets could not be loaded: ${response.status}`);
  }
  return response.json();
}

export async function uploadBarcodeReferenceDataset(file, fields = {}) {
  const formData = new FormData();
  formData.append('file', file);
  Object.entries(fields).forEach(([key, value]) => {
    if (value !== undefined && value !== null && String(value).trim() !== '') {
      formData.append(key, value);
    }
  });
  const response = await fetch(`${API_BASE_URL}/api/barcode/reference-datasets/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!response.ok) {
    throw new Error(`Reference dataset upload failed: ${response.status}`);
  }
  return response.json();
}

export async function runBarcodeReferenceSearch(payload) {
  const response = await fetch(`${API_BASE_URL}/api/barcode/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`Reference search failed: ${response.status}`);
  }
  return response.json();
}

export async function buildBarcodeFragmentGraph(payload) {
  const response = await fetch(`${API_BASE_URL}/api/barcode/fragment-graph`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`Fragment graph failed: ${response.status}`);
  }
  return response.json();
}

export async function runBarcodeCompiler(payload) {
  const response = await fetch(`${API_BASE_URL}/api/barcode/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`Barcode compiler run failed: ${response.status}`);
  }
  return response.json();
}

export function barcodeCsvTemplateUrl() {
  return `${API_BASE_URL}/api/barcode/csv-template`;
}

function barcodeCsvForm(file, fields = {}) {
  const formData = new FormData();
  formData.append('file', file);
  Object.entries(fields).forEach(([key, value]) => {
    if (value !== undefined && value !== null && String(value).trim() !== '') {
      formData.append(key, value);
    }
  });
  return formData;
}

export async function importBarcodeCsv(file, fields = {}) {
  const response = await fetch(`${API_BASE_URL}/api/barcode/import-csv`, {
    method: 'POST',
    body: barcodeCsvForm(file, fields),
  });
  if (!response.ok) {
    throw new Error(`Barcode CSV import failed: ${response.status}`);
  }
  return response.json();
}

export async function runBarcodeCsv(file, fields = {}) {
  const response = await fetch(`${API_BASE_URL}/api/barcode/run-csv`, {
    method: 'POST',
    body: barcodeCsvForm(file, fields),
  });
  if (!response.ok) {
    throw new Error(`Barcode CSV run failed: ${response.status}`);
  }
  return response.json();
}

export async function getBarcodeRun(runId) {
  const response = await fetch(`${API_BASE_URL}/api/barcode/runs/${runId}`);
  if (!response.ok) {
    throw new Error(`Barcode compiler run not found: ${response.status}`);
  }
  return response.json();
}

export async function getEvidenceRun(runId) {
  const response = await fetch(`${API_BASE_URL}/api/evidence/runs/${runId}`);
  if (!response.ok) {
    throw new Error(`Evidence run not found: ${response.status}`);
  }
  return response.json();
}

export async function listEvidenceRuns() {
  const response = await fetch(`${API_BASE_URL}/api/evidence/runs`);
  if (!response.ok) {
    throw new Error(`Evidence runs could not be listed: ${response.status}`);
  }
  return response.json();
}

export async function getDemoScenarios() {
  const response = await fetch(`${API_BASE_URL}/api/evidence/demo-scenarios`);
  if (!response.ok) {
    throw new Error(`Demo scenarios could not be loaded: ${response.status}`);
  }
  return response.json();
}

export async function getRegionPresets() {
  const response = await fetch(`${API_BASE_URL}/api/evidence/region-presets`);
  if (!response.ok) {
    throw new Error(`Region presets could not be loaded: ${response.status}`);
  }
  return response.json();
}

export async function getGbifStatus() {
  const response = await fetch(`${API_BASE_URL}/api/evidence/gbif-status`);
  if (!response.ok) {
    throw new Error(`GBIF status could not be loaded: ${response.status}`);
  }
  return response.json();
}

export async function searchTaxa(query, limit = 10) {
  const params = new URLSearchParams({ q: query || '', limit: String(limit) });
  const response = await fetch(`${API_BASE_URL}/api/evidence/taxon-suggest?${params.toString()}`);
  if (!response.ok) {
    throw new Error(`GBIF taxon search failed: ${response.status}`);
  }
  return response.json();
}
