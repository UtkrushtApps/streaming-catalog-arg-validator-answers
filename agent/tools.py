"""Local read-only catalog tool, its schema, and the argument-validation boundary.

The schema, the catalog service, and the tool wrapper are complete and correct.
The ONLY thing you implement is `validate_search_args`, the boundary that cleans
and checks the model's tool-call arguments BEFORE they reach the catalog service.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# Genres the catalog actually supports. Validation must reject anything else.
SUPPORTED_GENRES = frozenset({"sci-fi", "action", "drama", "comedy"})

# Read-only tool schema advertised to the model. Correct; do not change.
SEARCH_CATALOG_SCHEMA: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "search_catalog",
        "description": (
            "Look up titles currently AVAILABLE to watch in the streaming "
            "catalog. Read-only. Call once when the user needs current catalog "
            "availability for a title or genre."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Title or keywords to search for.",
                },
                "genre": {
                    "type": "string",
                    "description": "Optional genre filter, e.g. 'sci-fi'.",
                },
            },
            "required": ["query"],
        },
    },
}

# ---------------------------------------------------------------------------
# Local catalog service (deterministic). Represents the external system.
# Complete and correct; do not change.
# ---------------------------------------------------------------------------
_CATALOG: List[Dict[str, Any]] = [
    {"id": "tt1375666", "title": "Inception", "genre": "sci-fi"},
    {"id": "tt0816692", "title": "Interstellar", "genre": "sci-fi"},
    {"id": "tt0468569", "title": "The Dark Knight", "genre": "action"},
    {"id": "tt0110912", "title": "Pulp Fiction", "genre": "drama"},
    {"id": "tt1856010", "title": "The Grand Budapest Hotel", "genre": "comedy"},
]


def catalog_search(query: str, genre: Optional[str] = None) -> Dict[str, Any]:
    """Deterministic substring search over the local catalog."""
    q = query.strip().lower()
    rows: List[Dict[str, Any]] = []
    for row in _CATALOG:
        if q not in row["title"].lower():
            continue
        if genre and row["genre"] != genre:
            continue
        rows.append(dict(row))
    return {"titles": rows}


# ---------------------------------------------------------------------------
# Candidate task: implement the argument-validation boundary.
# ---------------------------------------------------------------------------
def validate_search_args(raw_args: Any) -> Dict[str, Any]:
    """Validate model-produced tool-call arguments before dispatch.

    Input: `raw_args` is whatever the model produced for a search_catalog call
    (normally a dict parsed from JSON, but it may be malformed).

    Return one of:
      - {"ok": True, "args": {"query": <clean str>, "genre": <str or None>}}
        when arguments are valid. Only 'query' and 'genre' may appear in 'args'.
      - {"ok": False, "error": <short reason string>} when arguments are invalid.

    Rules:
      * raw_args must be a dict; 'query' is required, must be a string, and must
        be non-empty after trimming whitespace.
      * 'genre', if present and not None, must be a string that (after trimming
        and lowercasing) is one of SUPPORTED_GENRES; otherwise it is invalid.
      * Any keys other than 'query' and 'genre' are rejected and are never
        forwarded to the catalog service.
      * Never raise; always return one of the two shapes above.
    """
    try:
        if not isinstance(raw_args, dict):
            return {"ok": False, "error": "arguments must be an object"}

        allowed_keys = {"query", "genre"}
        extra_keys = [key for key in raw_args.keys() if key not in allowed_keys]
        if extra_keys:
            rendered = ", ".join(sorted(repr(key) for key in extra_keys))
            return {"ok": False, "error": f"unexpected argument(s): {rendered}"}

        if "query" not in raw_args:
            return {"ok": False, "error": "missing required argument: query"}

        query = raw_args.get("query")
        if not isinstance(query, str):
            return {"ok": False, "error": "query must be a string"}

        clean_query = query.strip()
        if not clean_query:
            return {"ok": False, "error": "query must be a non-empty string"}

        clean_genre: Optional[str] = None
        if "genre" in raw_args and raw_args.get("genre") is not None:
            genre = raw_args.get("genre")
            if not isinstance(genre, str):
                return {"ok": False, "error": "genre must be a string"}

            clean_genre = genre.strip().lower()
            if clean_genre not in SUPPORTED_GENRES:
                supported = ", ".join(sorted(SUPPORTED_GENRES))
                return {
                    "ok": False,
                    "error": f"unsupported genre: {clean_genre!r}; supported genres: {supported}",
                }

        return {"ok": True, "args": {"query": clean_query, "genre": clean_genre}}
    except Exception:
        # Tool dispatch must be total: malformed model output should become a
        # structured error, never an exception that can crash the agent loop.
        return {"ok": False, "error": "invalid arguments"}


def search_catalog(raw_args: Any) -> Dict[str, Any]:
    """Validate then dispatch. Returns a structured error on invalid args."""
    checked = validate_search_args(raw_args)
    if not checked.get("ok"):
        return {"error": checked.get("error", "invalid arguments"), "titles": []}
    args = checked["args"]
    return catalog_search(query=args["query"], genre=args.get("genre"))

