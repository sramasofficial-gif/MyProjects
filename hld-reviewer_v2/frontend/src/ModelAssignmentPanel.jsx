import { colors, card } from "./theme.js";

export default function ModelAssignmentPanel({ focusAreas, availableModels, modelAssignment, onChange }) {
  return (
    <div style={{ ...card, marginBottom: 20 }}>
      <h3 style={{ marginTop: 0, fontSize: 16 }}>Step 2 — Assign a model per focus area</h3>
      <p style={{ color: colors.textMuted, fontSize: 13, marginTop: -6 }}>
        Route lighter checks to a cheap model and reasoning-heavy checks (security,
        vulnerability) to a stronger one. This is what keeps per-review credit spend down.
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px 24px" }}>
        {focusAreas.map((fa) => (
          <div key={fa.key} style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <label style={{ fontSize: 13, fontWeight: 600 }}>{fa.label}</label>
            <span style={{ fontSize: 12, color: colors.textMuted }}>{fa.description}</span>
            <select
              value={modelAssignment[fa.key] || fa.default_model}
              onChange={(e) => onChange(fa.key, e.target.value)}
              style={{
                marginTop: 4,
                padding: "6px 8px",
                borderRadius: 6,
                border: `1px solid ${colors.border}`,
                fontSize: 13,
              }}
            >
              {availableModels.map((m) => (
                <option key={m.key} value={m.key}>
                  {m.label}
                </option>
              ))}
            </select>
          </div>
        ))}
      </div>
    </div>
  );
}
