"""Simple real-model agent loop with a single read-only tool.

The model decides whether to call search_catalog. When it does, we parse the
tool-call arguments and dispatch through the validation boundary in tools.py.
This file is complete; the only incomplete logic is the validator it calls.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from agent.llm_client import LLMClient
from agent.tools import SEARCH_CATALOG_SCHEMA, search_catalog

SYSTEM_PROMPT = (
    "You are a streaming catalog assistant. When a user asks whether a title or "
    "genre is available to watch, call search_catalog once to get current "
    "availability, then summarize only the returned titles. If the tool returns "
    "an error field, tell the user their request could not be processed. Do not "
    "call the tool for general movie trivia you already know."
)


def _trace(step: str, payload: Any) -> None:
    print(f"[trace] {step}: {json.dumps(payload, ensure_ascii=False, default=str)}")


def run_agent(user_message: str) -> Dict[str, Any]:
    client = LLMClient()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    first = client.complete(messages, tools=[SEARCH_CATALOG_SCHEMA])
    msg = first.choices[0].message
    tool_calls = getattr(msg, "tool_calls", None)

    if not tool_calls:
        return {"used_tool": False, "tool_result": None,
                "final_answer": msg.content or ""}

    call = tool_calls[0]
    try:
        raw_args = json.loads(call.function.arguments or "{}")
    except json.JSONDecodeError:
        raw_args = call.function.arguments
    _trace("tool_call", {"name": call.function.name, "raw_args": raw_args})

    result = search_catalog(raw_args)
    _trace("tool_result", result)

    messages.append({
        "role": "assistant", "content": None,
        "tool_calls": [{
            "id": call.id, "type": "function",
            "function": {"name": call.function.name,
                          "arguments": call.function.arguments},
        }],
    })
    messages.append({"role": "tool", "tool_call_id": call.id,
                     "content": json.dumps(result)})
    second = client.complete(messages)
    return {"used_tool": True, "tool_result": result,
            "final_answer": second.choices[0].message.content or ""}

