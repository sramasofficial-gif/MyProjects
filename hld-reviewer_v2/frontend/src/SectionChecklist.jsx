import { colors, card } from "./theme.js";

export default function SectionChecklist({ sections, focusAreas, selectionState, onToggleSection, onToggleFocus }) {
  return (
    <div style={{ ...card, marginBottom: 20 }}>
      <h3 style={{ marginTop: 0, fontSize: 16 }}>Step 1 — Select sections and review focus</h3>
      <p style={{ color: colors.textMuted, fontSize: 13, marginTop: -6 }}>
        Check the sections you want reviewed, then pick which focus areas apply to each. Only
        checked sections and focus areas get sent to a model.
      </p>

      {sections.map((sec) => {
        const state = selectionState[sec.chunk_id] || { included: false, focus_areas: [] };
        return (
          <div
            key={sec.chunk_id}
            style={{
              borderTop: `1px solid ${colors.border}`,
              padding: "12px 0",
            }}
          >
            <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }}>
              <input
                type="checkbox"
                checked={state.included}
                onChange={() => onToggleSection(sec.chunk_id)}
              />
              <strong style={{ fontSize: 14 }}>{sec.heading}</strong>
              <span style={{ fontSize: 12, color: colors.textMuted }}>
                p.{sec.page_start}-{sec.page_end} · {sec.section_type.replace(/_/g, " ")}
              </span>
            </label>

            {state.included && (
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 10, marginLeft: 26 }}>
                {focusAreas.map((fa) => {
                  const active = state.focus_areas.includes(fa.key);
                  return (
                    <button
                      key={fa.key}
                      type="button"
                      onClick={() => onToggleFocus(sec.chunk_id, fa.key)}
                      title={fa.description}
                      style={{
                        padding: "4px 12px",
                        borderRadius: 999,
                        border: `1px solid ${active ? colors.primary : colors.border}`,
                        background: active ? colors.primary : "white",
                        color: active ? "white" : colors.text,
                        fontSize: 12,
                        cursor: "pointer",
                      }}
                    >
                      {fa.label}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
