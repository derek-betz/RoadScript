"""Simple JSON-backed cache for RAG query results."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class CacheEntry:
    """Cached query entry."""

    key: str
    payload: Dict[str, Any]


class QueryCache:
    """Persistent cache backed by a JSON file."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        self._cache = json.loads(self.path.read_text(encoding="utf-8"))

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self._cache, indent=2, ensure_ascii=True),
            encoding="utf-8",
        )

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        return self._cache.get(key)

    def set(self, key: str, payload: Dict[str, Any]) -> None:
        self._cache[key] = payload
        self._save()


def build_cache_key(*parts: str) -> str:
    hasher = hashlib.sha256()
    for part in parts:
        hasher.update(part.encode("utf-8"))
    return hasher.hexdigest()
