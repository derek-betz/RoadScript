"""Local knowledge store for RoadScript."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "knowledge"
STORE_PATH = DATA_PATH / "roadscript_knowledge.json"
_LOCK = Lock()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_items() -> list[dict[str, Any]]:
    if not STORE_PATH.exists():
        return []
    with STORE_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_items(items: list[dict[str, Any]]) -> None:
    DATA_PATH.mkdir(parents=True, exist_ok=True)
    with STORE_PATH.open("w", encoding="utf-8") as handle:
        json.dump(items, handle, indent=2, ensure_ascii=True)


def add_item(item: dict[str, Any]) -> int:
    with _LOCK:
        items = _load_items()
        next_id = 1 + max((existing.get("id", 0) for existing in items), default=0)
        stored = {
            "id": next_id,
            "created_at": _utc_now(),
            **item,
        }
        items.append(stored)
        _write_items(items)
    return next_id


def query_items(
    *,
    source: str | None = None,
    topic: str | None = None,
    tag: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    with _LOCK:
        items = list(reversed(_load_items()))
    results: list[dict[str, Any]] = []
    for item in items:
        if source and item.get("source") != source:
            continue
        if topic and item.get("topic") != topic:
            continue
        tags = item.get("tags") or []
        if tag and tag not in tags:
            continue
        results.append(item)
        if len(results) >= limit:
            break
    return results
