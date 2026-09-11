const SEVERITY_ORDER = { high: 0, medium: 1, low: 2 };
const SEVERITY_COLOR = { high: "#c0392b", medium: "#d68910", low: "#7f8c8d" };

export default function FindingsDashboard({ report }) {
  if (!report) return null;

  const allFindings = report.results.flatMap((r) => r.findings);
  const sorted = [...allFindings].sort(
    (a, b) => (SEVERITY_ORDER[a.severity] ?? 3) - (SEVERITY_ORDER[b.severity] ?? 3)
  );

  const counts = allFindings.reduce((acc, f) => {
    acc[f.severity] = (acc[f.severity] || 0) + 1;
    return acc;
  }, {});

  return (
    <div style={{ marginTop: 24 }}>
      <h3>
        Review results — {report.sections_reviewed ?? report.sections_reviewed_total} section(s) reviewed
        {report.sections_changed !== undefined && ` (${report.sections_changed} changed since last version)`}
      </h3>

      <div style={{ display: "flex", gap: 12, marginBottom: 16 }}>
        {["high", "medium", "low"].map((sev) => (
          <span
            key={sev}
            style={{
              padding: "4px 10px",
              borderRadius: 12,
              background: SEVERITY_COLOR[sev],
              color: "white",
              fontSize: 13,
            }}
          >
            {sev}: {counts[sev] || 0}
          </span>
        ))}
      </div>

      {sorted.length === 0 && <p>No findings — this batch looks clean.</p>}

      {sorted.map((f, i) => (
        <div
          key={i}
          style={{
            borderLeft: `4px solid ${SEVERITY_COLOR[f.severity] || "#999"}`,
            padding: "8px 12px",
            marginBottom: 8,
            background: "#fafafa",
          }}
        >
          <div style={{ fontSize: 12, color: "#666" }}>
            {f.section} · p.{f.page_start}-{f.page_end} · {f.criterion}
          </div>
          <div>{f.finding}</div>
          {f.reasoning && (
            <div style={{ fontSize: 12, color: "#888", marginTop: 4 }}>Reasoning: {f.reasoning}</div>
          )}
        </div>
      ))}
    </div>
  );
}
