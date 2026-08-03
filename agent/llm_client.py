"""Real LLM client wrapper (provided complete).

Live path calls a real model via litellm using the candidate's provider key.
This file is NOT part of the candidate task; do not edit it.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:  # pragma: no cover - dotenv optional at runtime
    pass


class LLMClient:
    """Thin wrapper around litellm.completion for chat + tool calling."""

    def __init__(self, model: Optional[str] = None) -> None:
        self.model = model or os.environ.get("MODEL", "gpt-4o-mini")

    def complete(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Any:
        import litellm

        kwargs: Dict[str, Any] = {"model": self.model, "messages": messages}
        if tools:
            kwargs["tools"] = tools
        return litellm.completion(**kwargs)

    def simple_ping(self, prompt: str) -> str:
        resp = self.complete([{"role": "user", "content": prompt}])
        return resp.choices[0].message.content or ""

