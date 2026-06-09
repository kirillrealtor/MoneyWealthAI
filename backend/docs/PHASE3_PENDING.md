# Phase 3 (AI Core) — Deferred Items & Required Inputs

The AI advisor is built and verified with a mocked LLM (every path except the
real Anthropic call is exercised by tests). To run it live you supply one key.

Legend: 🔑 key/account · ⚙️ config · 🧩 small code

## To run live
- 🔑 **`ANTHROPIC_API_KEY`** (platform.claude.com). Until set, advisor endpoints
  return a clean `503 AI_UNAVAILABLE`; everything up to the model call is built/tested.
- ⚙️ Model is `ADVISOR_MODEL` (default `claude-opus-4-8`). **Cost lever at scale:**
  set `ADVISOR_MODEL=claude-sonnet-4-6` (~$3/$15 vs $5/$25 per 1M). Classifier is
  `claude-haiku-4-5`. Adaptive thinking off by default (`ADVISOR_THINKING=true` to enable).
- ⚙️ Per-tier daily token budgets: `TOKEN_BUDGET_FREE/PLUS/PREMIUM` (10k/100k/500k).

## Built & verified (no action needed)
- Grounded agentic loop (max 5 tool rounds), 3 MCP tools (balances, spending, cash flow).
- **Tenant/user isolation in tools** — executors take user_id/tenant_id from the
  authenticated context (never the LLM) and run inside `with_tenant()`.
- Input safety (prompt-injection sanitizer, crisis protocol that bypasses the LLM,
  Haiku jailbreak classifier — fails open), output validator (grounding, compliance
  disclaimer, SQL/key-leak, length) with retry-once → safe fallback.
- Token budget enforcement + usage accounting; persona/compliance system prompt.
- Auth-gated, AI-rate-limited (10/min/user). Conversation persistence + feedback.

## Evals (built ✅) — run before trusting any model in production
- `python -m scripts.run_evals` runs the golden set against the configured provider,
  scores rule-based assertions (tool grounding, no buy/sell directive, educational
  framing, length), and **exits non-zero if pass rate < 90%**. Skips cleanly if no key.
- 🧩 Grow the golden set from 6 → 50+ cases (debt payoff, persona differentiation,
  crisis-adjacent, etc.) as you tune prompts.
- **Use it to compare Claude vs Groq objectively** before switching the production brain.

## Groq / free API (built ✅)
- Set `GROQ_API_KEY` + `ADVISOR_PROVIDER=groq` to run on Groq's free tier (open models).
- ⚠️ Open models are weaker at compliance framing — the validator catches violations
  (raising retry/cost), but for the *user-facing production advisor* run evals and prefer
  Claude (Sonnet 4.6 for cost). Keep Groq as the cheap dev/fallback tier.

## Deferred within Phase 3 (committed, not built yet)
- 🧩 **Streaming responses** (SSE) for the chat UI — the loop returns final text today.
- 🧩 **Provider fallback chain** (auto-failover Claude→Groq on error) — both providers
  exist behind `AdvisorProvider`; wire automatic failover when reliability data justifies it.
- 🧩 **Conversation summarization** past ~15k tokens (history is capped at N turns today).
- ⚙️ **Prompt caching** of the (stable) system prompt prefix to cut cost at volume.
- 🧩 Remaining MCP tools (debt, portfolio, goals, affordability) land with their
  Phase 4 modules.
