import { ImageResponse } from "next/og";

export const alt = "Fathom — Your AI financial advisor";
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
          background: "#06090f",
          backgroundImage:
            "radial-gradient(circle at 15% 10%, rgba(25,230,160,0.30), transparent 45%), radial-gradient(circle at 85% 90%, rgba(124,139,255,0.25), transparent 45%)",
          color: "#eaf0f8",
          fontFamily: "sans-serif",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 18, marginBottom: 28 }}>
          <div
            style={{
              width: 56,
              height: 56,
              borderRadius: 16,
              background: "#0c111c",
              border: "2px solid rgba(25,230,160,0.5)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#19e6a0",
              fontSize: 30,
            }}
          >
            F
          </div>
          <div style={{ fontSize: 34, fontWeight: 600 }}>Fathom</div>
        </div>
        <div style={{ fontSize: 72, fontWeight: 600, lineHeight: 1.05, maxWidth: 900 }}>
          Finally understand your money.
        </div>
        <div style={{ fontSize: 32, color: "#aab6cb", marginTop: 28, maxWidth: 820 }}>
          A grounded AI financial advisor over your real bank data — budgets, goals, debt &
          portfolio.
        </div>
      </div>
    ),
    { ...size },
  );
}
