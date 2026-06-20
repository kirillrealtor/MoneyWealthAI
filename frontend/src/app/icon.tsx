import { ImageResponse } from "next/og";

export const size = { width: 64, height: 64 };
export const contentType = "image/png";

// App icon / favicon — the MoneyWealth AI mark on the ink field, generated at build.
export default function Icon() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "#160d2b",
          borderRadius: 14,
          color: "#7c3aed",
          fontSize: 44,
          fontWeight: 700,
        }}
      >
        M
      </div>
    ),
    { ...size },
  );
}
