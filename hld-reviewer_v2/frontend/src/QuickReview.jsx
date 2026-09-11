import { useState } from "react";
import { reviewDocument, reviewDocumentDiff } from "./api.js";
import FindingsDashboard from "./FindingsDashboard.jsx";

export default function QuickReview() {
  const [report, setReport] = useState(null);
  const [docId, setDocId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleFullReview(e) {
    const file = e.target.files[0];
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const result = await reviewDocument(file);
      setReport(result);
      setDocId(result.doc_id);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleDiffReview(e) {
    const file = e.target.files[0];
    if (!file || !docId) return;
    setLoading(true);
    setError(null);
    try {
      const result = await reviewDocumentDiff(docId, file);
      setReport(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <p style={{ color: "#666", marginTop: 0 }}>
        Upload an HLD PDF for a full checklist-driven review of every section (no per-section
        picking). Once reviewed, upload a revised version to re-review only changed sections.
      </p>

      <div style={{ display: "flex", gap: 16, marginBottom: 16 }}>
        <label style={{ border: "1px solid #ccc", padding: "8px 14px", borderRadius: 6, cursor: "pointer" }}>
          Full review
          <input type="file" accept="application/pdf" onChange={handleFullReview} style={{ display: "none" }} />
        </label>

        <label
          style={{
            border: "1px solid #ccc",
            padding: "8px 14px",
            borderRadius: 6,
            cursor: docId ? "pointer" : "not-allowed",
            opacity: docId ? 1 : 0.5,
          }}
        >
          Diff re-review (revised PDF)
          <input
            type="file"
            accept="application/pdf"
            onChange={handleDiffReview}
            disabled={!docId}
            style={{ display: "none" }}
          />
        </label>
      </div>

      {loading && <p>Reviewing… this calls the model per changed section, please wait.</p>}
      {error && <p style={{ color: "#c0392b" }}>{error}</p>}

      <FindingsDashboard report={report} />
    </div>
  );
}
