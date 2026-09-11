export const colors = {
  bg: "#f5f6f8",
  surface: "#ffffff",
  border: "#e1e4e8",
  text: "#1c2530",
  textMuted: "#5b6572",
  primary: "#1a56db",
  primaryHover: "#1543ab",
  high: "#c0392b",
  medium: "#c8791a",
  low: "#5b6572",
  success: "#1a7f4b",
};

export const card = {
  background: colors.surface,
  border: `1px solid ${colors.border}`,
  borderRadius: 10,
  padding: "20px 24px",
  boxShadow: "0 1px 2px rgba(16, 24, 40, 0.04)",
};

export const badge = (bg) => ({
  display: "inline-block",
  padding: "3px 10px",
  borderRadius: 999,
  fontSize: 12,
  fontWeight: 600,
  color: "white",
  background: bg,
});

export const button = (primary) => ({
  padding: "9px 18px",
  borderRadius: 8,
  border: primary ? "none" : `1px solid ${colors.border}`,
  background: primary ? colors.primary : colors.surface,
  color: primary ? "white" : colors.text,
  fontWeight: 600,
  fontSize: 14,
  cursor: "pointer",
});
