"""RAG query engine for INDOT standards."""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from roadscript.ai.cache import QueryCache, build_cache_key
from roadscript.ai.llm import get_openai_client
from roadscript.ai.vector_index import VectorIndex, load_index_config

LOG = logging.getLogger(__name__)


@dataclass
class Snippet:
    """Retrieved snippet for a query."""

    text: str
    metadata: Dict[str, Any]
    distance: float

    def as_dict(self) -> Dict[str, Any]:
        return {"text": self.text, "metadata": self.metadata, "distance": self.distance}


@dataclass
class QueryResult:
    """Result from RAG retrieval + extraction."""

    values: Optional[List[float]]
    method: str
    snippets: List[Snippet]
    raw: Optional[Dict[str, Any]] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "values": self.values,
            "method": self.method,
            "snippets": [snippet.as_dict() for snippet in self.snippets],
            "raw": self.raw,
        }


class QueryEngine:
    """Query engine that retrieves chunks and extracts structured values."""

    def __init__(
        self,
        index_path: Path,
        cache_path: Optional[Path] = None,
    ) -> None:
        embedding_config = load_index_config(index_path)
        self._index = VectorIndex(index_path, embedding_config=embedding_config)
        self._cache = QueryCache(cache_path or index_path / "rag_cache.json")
        self._llm = get_openai_client()

    def retrieve(self, query: str, top_k: int = 5) -> List[Snippet]:
        result = self._index.query(query, top_k=top_k)
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        snippets = []
        for doc, meta, dist in zip(documents, metadatas, distances):
            snippets.append(
                Snippet(text=str(doc), metadata=meta or {}, distance=float(dist))
            )
        return snippets

    def query_speed_value(
        self,
        query: str,
        speed: int,
        value_count: int,
        top_k: int = 5,
        allow_llm: bool = True,
    ) -> Optional[QueryResult]:
        cache_key = build_cache_key(query, str(speed), str(value_count))
        cached = self._cache.get(cache_key)
        if cached:
            return QueryResult(
                values=cached.get("values"),
                method=cached.get("method", "cache"),
                snippets=[Snippet(**snippet) for snippet in cached.get("snippets", [])],
                raw=cached.get("raw"),
            )

        snippets = self.retrieve(query, top_k=top_k)
        values = _extract_speed_values(snippets, speed, value_count)
        if values:
            result = QueryResult(values=values, method="regex", snippets=snippets)
            self._cache.set(cache_key, result.as_dict())
            return result

        if allow_llm and self._llm:
            prompt = _build_speed_prompt(query, speed, value_count, snippets)
            raw = self._llm.extract_json(prompt["system"], prompt["user"])
            values = raw.get("values")
            if isinstance(values, list) and len(values) >= value_count:
                casted = [float(val) for val in values[:value_count]]
                result = QueryResult(values=casted, method="llm", snippets=snippets, raw=raw)
                self._cache.set(cache_key, result.as_dict())
                return result

        self._cache.set(cache_key, {"values": None, "method": "miss", "snippets": []})
        return None

    def query_json(
        self,
        query: str,
        response_keys: List[str],
        top_k: int = 5,
    ) -> Optional[QueryResult]:
        cache_key = build_cache_key(query, "json", ",".join(response_keys))
        cached = self._cache.get(cache_key)
        if cached:
            return QueryResult(
                values=cached.get("values"),
                method=cached.get("method", "cache"),
                snippets=[Snippet(**snippet) for snippet in cached.get("snippets", [])],
                raw=cached.get("raw"),
            )

        snippets = self.retrieve(query, top_k=top_k)
        if not self._llm:
            return None
        prompt = _build_json_prompt(query, response_keys, snippets)
        raw = self._llm.extract_json(prompt["system"], prompt["user"])
        if not isinstance(raw, dict):
            return None
        result = QueryResult(values=None, method="llm", snippets=snippets, raw=raw)
        self._cache.set(cache_key, result.as_dict())
        return result


def _extract_speed_values(snippets: List[Snippet], speed: int, value_count: int) -> Optional[List[float]]:
    pattern = re.compile(r"\b" + re.escape(str(speed)) + r"\b")
    for snippet in snippets:
        for line in snippet.text.splitlines():
            if not pattern.search(line):
                continue
            tokens = re.findall(r"\d+(?:\.\d+)?", line)
            if not tokens:
                continue
            first = int(float(tokens[0]))
            if first != speed:
                continue
            if len(tokens) < value_count + 1:
                continue
            return [float(value) for value in tokens[1:value_count + 1]]
    return None


def _build_speed_prompt(
    query: str,
    speed: int,
    value_count: int,
    snippets: List[Snippet],
) -> Dict[str, str]:
    system = (
        "You extract numeric values from INDOT standards. "
        "Return JSON with keys: values (array of numbers) and source (string)."
    )
    context = "\n\n".join(snippet.text for snippet in snippets[:5])
    user = (
        f"Question: {query}\\n"
        f"Design speed: {speed} mph. "
        f"Extract {value_count} numeric value(s) from the table row for this speed.\\n"
        f"Context:\\n{context}"
    )
    return {"system": system, "user": user}


def _build_json_prompt(
    query: str,
    response_keys: List[str],
    snippets: List[Snippet],
) -> Dict[str, str]:
    system = (
        "You extract structured data from INDOT standards. "
        "Return JSON only, using the requested keys."
    )
    context = "\n\n".join(snippet.text for snippet in snippets[:5])
    user = (
        f"Question: {query}\\n"
        f"Return JSON with keys: {', '.join(response_keys)}.\\n"
        f"Context:\\n{context}"
    )
    return {"system": system, "user": user}
