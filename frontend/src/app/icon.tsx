import { ImageResponse } from "next/og";

export const size = { width: 64, height: 64 };
export const contentType = "image/png";

// App icon / favicon — the Fathom mark on the ink field, generated at build.
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
          background: "#06090f",
          borderRadius: 14,
          color: "#19e6a0",
          fontSize: 44,
          fontWeight: 700,
        }}
      >
        F
      </div>
    ),
    { ...size },
  );
}
