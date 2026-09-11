const BASE_URL = "http://localhost:8000";

async function postFile(path, file) {
  const form = new FormData();
  form.append("file", file);
  const resp = await fetch(`${BASE_URL}${path}`, { method: "POST", body: form });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`Request failed (${resp.status}): ${text}`);
  }
  return resp.json();
}

export function reviewDocument(file) {
  return postFile("/api/review", file);
}

export function reviewDocumentDiff(docId, file) {
  return postFile(`/api/review/${docId}/diff`, file);
}

export function extractDocument(file) {
  return postFile("/api/extract", file);
}

export async function getFocusAreas() {
  const resp = await fetch(`${BASE_URL}/api/focus-areas`);
  if (!resp.ok) throw new Error(`Request failed (${resp.status})`);
  return resp.json();
}

export async function reviewSelected(docId, selections, modelAssignment) {
  const resp = await fetch(`${BASE_URL}/api/review-selected`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ doc_id: docId, selections, model_assignment: modelAssignment }),
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`Request failed (${resp.status}): ${text}`);
  }
  return resp.json();
}
