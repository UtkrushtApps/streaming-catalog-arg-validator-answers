"""Selfcheck entry point (readiness probe) and optional key-gated model ping.

This does NOT call candidate stubs. It only verifies the package imports, the
static tool schema is well-formed, and fixtures are present.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

TASK_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_PATH = TASK_ROOT / "fixtures" / "tool_traces.jsonl"


def _selfcheck() -> int:
    # 1) Imports resolve.
    from agent import tools  # noqa: F401
    from agent import agent as agent_mod  # noqa: F401
    from agent.tools import SEARCH_CATALOG_SCHEMA, SUPPORTED_GENRES

    # 2) Static schema is well-formed.
    fn = SEARCH_CATALOG_SCHEMA.get("function", {})
    assert fn.get("name") == "search_catalog", "tool name must be search_catalog"
    params = fn.get("parameters", {})
    props = params.get("properties", {})
    assert "query" in props, "schema must declare 'query'"
    assert params.get("required") == ["query"], "only 'query' should be required"
    assert isinstance(SUPPORTED_GENRES, (set, frozenset, list, tuple))

    # 3) Fixtures present and parseable.
    assert FIXTURE_PATH.exists(), f"missing fixture: {FIXTURE_PATH}"
    count = 0
    with FIXTURE_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            json.loads(line)
            count += 1
    assert count > 0, "fixture file has no records"

    print(f"selfcheck ok: schema valid, {count} fixture traces loaded")
    return 0


def _model_ping() -> int:
    """Optional key-gated smoke ping. Never part of readiness gate."""
    if not (os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")):
        print("no provider key set; skipping model ping")
        return 0
    from agent.llm_client import LLMClient

    client = LLMClient()
    reply = client.simple_ping("Reply with the single word: ok")
    print(f"model ping reply: {reply!r}")
    return 0


def main(argv: list[str]) -> int:
    if "--selfcheck" in argv:
        return _selfcheck()
    if "--model-ping" in argv:
        return _model_ping()
    # Default: run one live agent turn (requires a key).
    from agent.agent import run_agent

    message = argv[1] if len(argv) > 1 else "is Inception available?"
    outcome = run_agent(message)
    print("\n=== RESULT ===")
    print("used_tool:", outcome.get("used_tool"))
    print("answer:", outcome.get("final_answer"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

