import { ImageResponse } from "next/og";

export const alt = "MoneyWealth AI — Your AI financial advisor";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OgImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "80px",
          background: "#160d2b",
          backgroundImage:
            "radial-gradient(circle at 15% 10%, rgba(124,58,237,0.38), transparent 45%), radial-gradient(circle at 85% 90%, rgba(168,85,247,0.28), transparent 45%)",
          color: "#ece8f6",
          fontFamily: "sans-serif",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 18, marginBottom: 28 }}>
          <div
            style={{
              width: 56,
              height: 56,
              borderRadius: 16,
              background: "#241640",
              border: "2px solid rgba(124,58,237,0.55)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#7c3aed",
              fontSize: 30,
            }}
          >
            M
          </div>
          <div style={{ fontSize: 34, fontWeight: 600 }}>MoneyWealth AI</div>
        </div>
        <div style={{ fontSize: 72, fontWeight: 600, lineHeight: 1.05, maxWidth: 900 }}>
          Finally understand your money.
        </div>
        <div style={{ fontSize: 32, color: "#a99fc2", marginTop: 28, maxWidth: 820 }}>
          A grounded AI financial advisor over your real bank data — budgets, goals, debt &
          portfolio.
        </div>
      </div>
    ),
    { ...size },
  );
}
