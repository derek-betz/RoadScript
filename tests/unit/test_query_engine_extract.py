"""Unit tests for query extraction helpers."""

from roadscript.ai.query_engine import Snippet, _extract_speed_values


def test_extract_speed_values_single_column():
    snippets = [
        Snippet(text="Design Speed\n60 830\n", metadata={}, distance=0.0),
    ]
    values = _extract_speed_values(snippets, speed=60, value_count=1)
    assert values == [830.0]


def test_extract_speed_values_multi_column():
    snippets = [
        Snippet(text="Design Speed\n60 151 136\n", metadata={}, distance=0.0),
    ]
    values = _extract_speed_values(snippets, speed=60, value_count=2)
    assert values == [151.0, 136.0]
