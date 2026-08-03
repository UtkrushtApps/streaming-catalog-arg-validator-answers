# Solution Steps

1. Open `agent/tools.py` and focus only on the `validate_search_args` function; leave the tool schema, catalog service, system prompt, and agent loop unchanged.

2. Make the validator total by wrapping its logic defensively so malformed model-produced arguments are converted into `{"ok": False, "error": ...}` instead of raising during tool dispatch.

3. First require `raw_args` to be a dictionary/object. If it is not, return a structured error such as `arguments must be an object`.

4. Reject unexpected argument names before dispatch. Compare the input keys against the allowed set `{ "query", "genre" }`; if any other key is present, return `{"ok": False, "error": ...}` so no unrecognized model output reaches the catalog.

5. Validate the required `query` argument: it must exist, it must be a string, and `query.strip()` must be non-empty. Store the trimmed query for forwarding.

6. Validate optional `genre`: if omitted or `None`, forward it as `None`; otherwise require it to be a string, normalize with `strip().lower()`, and reject it unless it is in `SUPPORTED_GENRES`.

7. For valid inputs, return exactly `{"ok": True, "args": {"query": clean_query, "genre": clean_genre}}`, ensuring only clean `query` and `genre` fields can be forwarded.

8. Keep `search_catalog` dispatching through `validate_search_args`; on invalid validation results it returns `{"error": <reason>, "titles": []}`, and on valid results it calls the read-only `catalog_search` with the cleaned arguments.

9. Run `python -m agent --selfcheck` to confirm imports, schema shape, and fixtures are valid, then run the offline tests with `pytest` to confirm valid searches work and invalid tool-call arguments produce structured errors.

