"""Candidate-facing invariants for the argument-validation boundary.

These run offline and need no provider key.
"""
from agent.tools import search_catalog, validate_search_args


def test_valid_query_returns_titles():
    result = search_catalog({"query": "Inception"})
    assert "error" not in result
    titles = {t["title"] for t in result["titles"]}
    assert "Inception" in titles


def test_blank_query_is_rejected():
    result = search_catalog({"query": "   "})
    assert result.get("error")
    assert result.get("titles") == []


def test_missing_query_is_rejected():
    checked = validate_search_args({"genre": "action"})
    assert checked.get("ok") is False


def test_non_string_query_is_rejected():
    checked = validate_search_args({"query": 12345})
    assert checked.get("ok") is False


def test_non_dict_args_are_rejected():
    checked = validate_search_args("Inception")
    assert checked.get("ok") is False


def test_unsupported_genre_is_rejected():
    checked = validate_search_args({"query": "the", "genre": "documentary"})
    assert checked.get("ok") is False


def test_supported_genre_is_normalized():
    checked = validate_search_args({"query": "Inception", "genre": "Sci-Fi"})
    assert checked.get("ok") is True
    assert checked["args"]["genre"] == "sci-fi"


def test_query_is_trimmed_but_preserved():
    checked = validate_search_args({"query": "  Interstellar  "})
    assert checked.get("ok") is True
    assert checked["args"]["query"].strip() == checked["args"]["query"]
    assert "Interstellar" in checked["args"]["query"]


def test_extra_keys_are_rejected():
    checked = validate_search_args(
        {"query": "Interstellar", "include_unreleased": True}
    )
    assert checked.get("ok") is False
    assert checked.get("error")

    result = search_catalog({"query": "Interstellar", "include_unreleased": True})
    assert result.get("error")
    assert result.get("titles") == []


def test_genre_filter_applies_in_search():
    result = search_catalog({"query": "the", "genre": "action"})
    assert "error" not in result
    for row in result["titles"]:
        assert row["genre"] == "action"

