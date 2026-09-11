import { useEffect, useState } from "react";
import { extractDocument, getFocusAreas, reviewSelected } from "./api.js";
import SectionChecklist from "./SectionChecklist.jsx";
import ModelAssignmentPanel from "./ModelAssignmentPanel.jsx";
import EnterpriseReviewSummary from "./EnterpriseReviewSummary.jsx";
import { colors, card, button } from "./theme.js";

export default function ReviewWizard() {
  const [focusMeta, setFocusMeta] = useState(null); // { focus_areas, available_models }
  const [docId, setDocId] = useState(null);
  const [sections, setSections] = useState([]);
  const [selectionState, setSelectionState] = useState({}); // chunk_id -> {included, focus_areas}
  const [modelAssignment, setModelAssignment] = useState({}); // focus_area -> model key
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    getFocusAreas()
      .then((meta) => {
        setFocusMeta(meta);
        const defaults = {};
        meta.focus_areas.forEach((fa) => (defaults[fa.key] = fa.default_model));
        setModelAssignment(defaults);
      })
      .catch((err) => setError(err.message));
  }, []);

  async function handleUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    setLoading(true);
    setError(null);
    setReport(null);
    try {
      const result = await extractDocument(file);
      setDocId(result.doc_id);
      setSections(result.sections);
      setSelectionState({});
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function toggleSection(chunkId) {
    setSelectionState((prev) => {
      const current = prev[chunkId] || { included: false, focus_areas: [] };
      return { ...prev, [chunkId]: { ...current, included: !current.included } };
    });
  }

  function toggleFocus(chunkId, focusKey) {
    setSelectionState((prev) => {
      const current = prev[chunkId] || { included: true, focus_areas: [] };
      const has = current.focus_areas.includes(focusKey);
      const next = has
        ? current.focus_areas.filter((k) => k !== focusKey)
        : [...current.focus_areas, focusKey];
      return { ...prev, [chunkId]: { ...current, focus_areas: next } };
    });
  }

  function updateModelAssignment(focusKey, modelKey) {
    setModelAssignment((prev) => ({ ...prev, [focusKey]: modelKey }));
  }

  const selections = Object.entries(selectionState)
    .filter(([, v]) => v.included && v.focus_areas.length > 0)
    .map(([chunk_id, v]) => ({ chunk_id, focus_areas: v.focus_areas }));

  async function handleRunReview() {
    if (selections.length === 0) {
      setError("Select at least one section and one focus area before running the review.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await reviewSelected(docId, selections, modelAssignment);
      setReport(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div style={{ ...card, marginBottom: 20 }}>
        <h3 style={{ marginTop: 0, fontSize: 16 }}>Step 0 — Upload HLD</h3>
        <label style={{ ...button(false), display: "inline-block" }}>
          {docId ? "Re-upload a different PDF" : "Choose PDF"}
          <input type="file" accept="application/pdf" onChange={handleUpload} style={{ display: "none" }} />
        </label>
        {docId && <span style={{ marginLeft: 12, fontSize: 12, color: colors.textMuted }}>doc_id: {docId}</span>}
      </div>

      {sections.length > 0 && focusMeta && (
        <>
          <SectionChecklist
            sections={sections}
            focusAreas={focusMeta.focus_areas}
            selectionState={selectionState}
            onToggleSection={toggleSection}
            onToggleFocus={toggleFocus}
          />
          <ModelAssignmentPanel
            focusAreas={focusMeta.focus_areas}
            availableModels={focusMeta.available_models}
            modelAssignment={modelAssignment}
            onChange={updateModelAssignment}
          />
          <button type="button" style={button(true)} onClick={handleRunReview} disabled={loading}>
            {loading ? "Running review…" : `Run review (${selections.length} section(s) selected)`}
          </button>
        </>
      )}

      {error && <p style={{ color: colors.high, marginTop: 16 }}>{error}</p>}

      <EnterpriseReviewSummary report={report} />
    </div>
  );
}
