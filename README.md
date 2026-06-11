# AI Financial Advisor — Monorepo

AI-native personal finance platform. Single repository, language-separated by app.

```
.
├── backend/          Python · FastAPI · aiosqlite · Redis  (API + AI orchestration)
│   ├── app/            application code
│   ├── db/migrations/  SQL schema (source of truth)
│   ├── scripts/        migration runner
│   ├── tests/          unit + integration
│   └── docs/           architecture, build sequence, security, pending items
├── frontend/         (coming) TypeScript · Next.js · React
├── docker-compose.yml   orchestrates datastores + services for local dev
└── .github/workflows/   CI (runs in ./backend)
```

## Why a monorepo (not split repos)
Backend (Python) and frontend (TypeScript) share no code — they coordinate via the
backend's auto-generated **OpenAPI** contract. For a small team a monorepo gives
atomic API+UI commits, one CI, and no cross-repo version coordination. A folder can
still be split into its own repo later (`git subtree split`) if needed.

## Quick start (backend)
```bash
docker compose up -d redis        # datastore (Redis :6380, SQLite is managed locally)
cd backend
python -m venv .venv && .venv/Scripts/activate   # Windows; use bin/activate on *nix
pip install -r requirements-dev.txt
python -m scripts.migrate
uvicorn app.main:app --reload --port 3000  # http://localhost:3000/docs
```

Full backend docs: [backend/README.md](backend/README.md).
Run everything in containers: `docker compose up --build`.

## Status
- ✅ Backend Phase 0 + 1 (+ security hardening, captcha) — see [backend/docs/](backend/docs/)
- ⏭️ Backend Phase 2 — Plaid sandbox
- ⏭️ Frontend — not started
