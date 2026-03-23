const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function parseResponse(response) {
  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    throw new Error(errorBody.detail || "Request failed");
  }
  return response.json();
}

export async function fetchCases() {
  const response = await fetch(`${API_BASE}/case/list`);
  return parseResponse(response);
}

export async function fetchCaseDetail(caseId) {
  const response = await fetch(`${API_BASE}/case/${caseId}`);
  return parseResponse(response);
}

export async function createCase(caseName) {
  const response = await fetch(`${API_BASE}/case/create`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ case_name: caseName })
  });
  return parseResponse(response);
}

export async function uploadFiles(caseId, files) {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));
  const response = await fetch(`${API_BASE}/upload?case_id=${caseId}`, {
    method: "POST",
    body: formData
  });
  return parseResponse(response);
}

export async function sendQuery(caseId, message) {
  const response = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ case_id: caseId, message })
  });
  return parseResponse(response);
}

export async function fetchEntityDrilldown(caseId, entity) {
  const response = await fetch(`${API_BASE}/entity/drilldown?case_id=${encodeURIComponent(caseId)}&entity=${encodeURIComponent(entity)}`);
  return parseResponse(response);
}

export async function fetchTimeline(caseId, entity) {
  const url = entity
    ? `${API_BASE}/timeline?case_id=${encodeURIComponent(caseId)}&entity=${encodeURIComponent(entity)}`
    : `${API_BASE}/timeline?case_id=${encodeURIComponent(caseId)}`;
  const response = await fetch(url);
  return parseResponse(response);
}

export async function downloadReport(caseId) {
  const response = await fetch(`${API_BASE}/report/generate?case_id=${encodeURIComponent(caseId)}`);
  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    throw new Error(errorBody.detail || "Report generation failed");
  }
  return response.blob();
}

export async function removeDataset(caseId, fileName) {
  const response = await fetch(`${API_BASE}/dataset?case_id=${encodeURIComponent(caseId)}&file_name=${encodeURIComponent(fileName)}`, {
    method: "DELETE"
  });
  return parseResponse(response);
}
