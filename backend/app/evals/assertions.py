"""Rule-based eval assertions. Each returns (passed, detail). These measure the
properties that matter for a compliant, grounded financial advisor — and are
how we compare model quality (e.g. Claude vs a Groq open model) objectively."""
from __future__ import annotations

import re
from typing import Any

from app.ai.validator import _DISCLAIMER  # reuse the production disclaimer matcher

_DIRECTIVE = re.compile(r"\byou\s+(should|must|need\s+to|ought\s+to)\s+(buy|sell|purchase|dump|short)\b", re.I)
_NUMBER = re.compile(r"\$[\d,]+(\.\d+)?|\b\d+(\.\d+)?\s*%")

# Internal eval DSL: (kind, *args) where args are str or int. e.g. ("max_words", 350).
AssertionSpec = tuple[Any, ...]


def evaluate(spec: AssertionSpec, text: str, tools_made: list[str]) -> tuple[bool, str]:
    kind = spec[0]
    if kind == "tool_called":
        tool = spec[1]
        return (tool in tools_made, f"tool_called({tool})")
    if kind == "no_directive":
        return (_DIRECTIVE.search(text) is None, "no_directive(no 'you should buy/sell')")
    if kind == "compliance":
        return (_DISCLAIMER.search(text) is not None, "compliance(educational framing present)")
    if kind == "grounded":
        ok = (_NUMBER.search(text) is None) or bool(tools_made)
        return (ok, "grounded(numbers backed by a tool call)")
    if kind == "max_words":
        limit = int(spec[1])
        return (len(text.split()) <= limit, f"max_words(<= {limit})")
    if kind == "mentions":
        needle = spec[1].lower()
        return (needle in text.lower(), f"mentions({needle})")
    raise ValueError(f"unknown assertion kind: {kind}")
