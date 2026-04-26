const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:18100';

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
