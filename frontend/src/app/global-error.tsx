"use client";

// Root error boundary — replaces the whole document if the root layout throws,
// so it must render its own <html>/<body>. Kept minimal and dependency-free.
export default function GlobalError({ reset }: { error: Error; reset: () => void }) {
  return (
    <html lang="en">
      <body
        style={{
          margin: 0,
          minHeight: "100vh",
          display: "grid",
          placeItems: "center",
          background: "#06090f",
          color: "#eaf0f8",
          fontFamily: "system-ui, sans-serif",
          textAlign: "center",
        }}
      >
        <div>
          <h1 style={{ fontSize: "1.4rem", fontWeight: 500 }}>Something went wrong</h1>
          <p style={{ color: "#93a1b8", marginTop: 8 }}>Please reload the page.</p>
          <button
            onClick={reset}
            style={{
              marginTop: 20,
              padding: "10px 20px",
              borderRadius: 12,
              border: "none",
              background: "#7c3aed",
              color: "#06090f",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            Reload
          </button>
        </div>
      </body>
    </html>
  );
}
