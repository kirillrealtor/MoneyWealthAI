// k6 load test — run: k6 run tests/load/advisor_load_test.js
// Env: BASE_URL, AUTH_TOKEN (a valid access token for a seeded test user).
//
// Validates the 1M-scale performance targets from the architecture doc:
//   dashboard p95 < 500ms, AI p95 < 8s, error rate < 1%.
import http from "k6/http";
import { check, sleep } from "k6";

const BASE = __ENV.BASE_URL || "http://localhost:3000";
const TOKEN = __ENV.AUTH_TOKEN || "";
const AUTH = { headers: { Authorization: `Bearer ${TOKEN}`, "Content-Type": "application/json" } };

export const options = {
  stages: [
    { duration: "2m", target: 50 },   // ramp to 50 VUs
    { duration: "5m", target: 50 },   // hold
    { duration: "2m", target: 200 },  // spike
    { duration: "5m", target: 200 },  // hold
    { duration: "2m", target: 0 },    // ramp down
  ],
  thresholds: {
    http_req_failed: ["rate<0.01"],
    "http_req_duration{kind:dashboard}": ["p(95)<500"],
    "http_req_duration{kind:ai}": ["p(95)<8000"],
  },
};

export default function () {
  // Cheap read path (dashboard).
  const dash = http.get(`${BASE}/api/v1/budgets`, { ...AUTH, tags: { kind: "dashboard" } });
  check(dash, { "dashboard 200": (r) => r.status === 200 });
  sleep(1);

  // Notifications feed.
  const feed = http.get(`${BASE}/api/v1/notifications`, { ...AUTH, tags: { kind: "dashboard" } });
  check(feed, { "feed 200": (r) => r.status === 200 });
  sleep(2);

  // AI path (most expensive). Requires ANTHROPIC_API_KEY / GROQ_API_KEY on the server.
  const chat = http.post(
    `${BASE}/api/v1/advisor/chat`,
    JSON.stringify({ message: "How am I doing on my budget this month?" }),
    { ...AUTH, tags: { kind: "ai" } }
  );
  check(chat, { "chat 200/503": (r) => r.status === 200 || r.status === 503 });
  sleep(5);
}
