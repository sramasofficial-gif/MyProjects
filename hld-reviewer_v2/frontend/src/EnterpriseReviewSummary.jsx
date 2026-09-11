import { colors, card, badge } from "./theme.js";

const SEVERITY_ORDER = { high: 0, medium: 1, low: 2 };
const SEVERITY_COLOR = { high: colors.high, medium: colors.medium, low: colors.low };

function SeverityBadge({ severity }) {
  return <span style={badge(SEVERITY_COLOR[severity] || colors.low)}>{severity}</span>;
}

export default function EnterpriseReviewSummary({ report }) {
  if (!report) return null;

  const { severity_summary, results } = report;
  const totalFindings = (severity_summary?.high || 0) + (severity_summary?.medium || 0) + (severity_summary?.low || 0);

  return (
    <div style={{ marginTop: 28 }}>
      <div style={{ ...card, marginBottom: 20 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <h2 style={{ margin: 0, fontSize: 20 }}>Review summary</h2>
            <p style={{ margin: "4px 0 0", color: colors.textMuted, fontSize: 13 }}>
              {report.sections_reviewed} section(s) reviewed · {totalFindings} finding(s)
            </p>
          </div>
          <div style={{ display: "flex", gap: 10 }}>
            {["high", "medium", "low"].map((sev) => (
              <div key={sev} style={{ textAlign: "center" }}>
                <div style={{ fontSize: 22, fontWeight: 700, color: SEVERITY_COLOR[sev] }}>
                  {severity_summary?.[sev] || 0}
                </div>
                <div style={{ fontSize: 11, color: colors.textMuted, textTransform: "uppercase" }}>{sev}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {results.map((r) => {
        const sorted = [...r.findings].sort(
          (a, b) => (SEVERITY_ORDER[a.severity] ?? 3) - (SEVERITY_ORDER[b.severity] ?? 3)
        );
        return (
          <div key={r.chunk_id} style={{ ...card, marginBottom: 16 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", flexWrap: "wrap", gap: 8 }}>
              <h3 style={{ margin: 0, fontSize: 16 }}>{r.section}</h3>
              <span style={{ fontSize: 12, color: colors.textMuted }}>
                models: {r.models_used?.join(", ")}
              </span>
            </div>
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap", margin: "8px 0 14px" }}>
              {r.focus_areas_reviewed?.map((fa) => (
                <span
                  key={fa}
                  style={{
                    fontSize: 11,
                    padding: "2px 8px",
                    borderRadius: 999,
                    background: "#eef1f6",
                    color: colors.textMuted,
                  }}
                >
                  {fa.replace(/_/g, " ")}
                </span>
              ))}
            </div>

            {sorted.length === 0 && (
              <p style={{ color: colors.success, fontSize: 13, margin: 0 }}>
                No findings for the selected focus areas.
              </p>
            )}

            {sorted.map((f, i) => (
              <div
                key={i}
                style={{
                  borderLeft: `3px solid ${SEVERITY_COLOR[f.severity] || colors.low}`,
                  padding: "8px 12px",
                  marginBottom: 8,
                  background: colors.bg,
                  borderRadius: 4,
                }}
              >
                <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 4 }}>
                  <SeverityBadge severity={f.severity} />
                  <span style={{ fontSize: 12, color: colors.textMuted }}>
                    {f.focus_area?.replace(/_/g, " ")}
                  </span>
                </div>
                <div style={{ fontSize: 14 }}>{f.finding}</div>
                {f.reasoning && (
                  <div style={{ fontSize: 12, color: colors.textMuted, marginTop: 4 }}>
                    Reasoning: {f.reasoning}
                  </div>
                )}
              </div>
            ))}
          </div>
        );
      })}
    </div>
  );
}
