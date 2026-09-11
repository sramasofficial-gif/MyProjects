import { useState } from "react";
import ReviewWizard from "./ReviewWizard.jsx";
import QuickReview from "./QuickReview.jsx";
import { colors } from "./theme.js";

export default function App() {
  const [tab, setTab] = useState("guided");

  const tabStyle = (active) => ({
    padding: "8px 16px",
    borderRadius: 8,
    border: "none",
    background: active ? colors.primary : "transparent",
    color: active ? "white" : colors.textMuted,
    fontWeight: 600,
    fontSize: 14,
    cursor: "pointer",
  });

  return (
    <div style={{ maxWidth: 920, margin: "40px auto 80px", fontFamily: "system-ui, sans-serif", color: colors.text }}>
      <h1 style={{ fontSize: 24, marginBottom: 4 }}>HLD Reviewer</h1>
      <p style={{ color: colors.textMuted, marginTop: 0 }}>
        Select sections and focus areas, route each to a model, review only what you need.
      </p>

      <div style={{ display: "flex", gap: 8, marginBottom: 24 }}>
        <button style={tabStyle(tab === "guided")} onClick={() => setTab("guided")}>
          Guided review
        </button>
        <button style={tabStyle(tab === "quick")} onClick={() => setTab("quick")}>
          Quick full / diff review
        </button>
      </div>

      {tab === "guided" ? <ReviewWizard /> : <QuickReview />}
    </div>
  );
}
