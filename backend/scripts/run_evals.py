"""Run the AI eval suite against the configured provider and gate on pass rate.

Usage: python -m scripts.run_evals
Exit codes: 0 = passed (>= threshold) or skipped (no AI key); 1 = below threshold.
"""
from __future__ import annotations

import asyncio
import sys

from app.ai.provider import get_provider
from app.config import settings
from app.errors import ApiError
from app.evals.runner import run_all

THRESHOLD = 90.0


async def main() -> int:
    if not settings.ai_configured:
        print("No AI provider configured (ANTHROPIC_API_KEY / GROQ_API_KEY) — skipping evals.")
        return 0
    try:
        provider = get_provider()
    except ApiError:
        print("AI provider unavailable — skipping evals.")
        return 0

    rate, results = await run_all(provider)
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"[{status}] {r.case_id}  tools={r.tool_calls}  tokens={r.tokens}")
        for f in r.failures:
            print(f"        - {f}")
    print(f"\nProvider: {provider.name} | Pass rate: {rate:.1f}% (threshold {THRESHOLD:.0f}%)")
    return 0 if rate >= THRESHOLD else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
