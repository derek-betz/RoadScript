"""Shared helpers for INDOT ingestion scripts."""

from dataclasses import dataclass
from datetime import datetime
import hashlib
import re
from typing import Iterable, List, Optional, Tuple
from urllib.parse import urljoin, urlparse


@dataclass(frozen=True)
class LinkInfo:
    """Represents a candidate PDF link on an index page."""

    url: str
    text: str
    version_key: Tuple[int, Optional[datetime]]


def _extract_year(text: str) -> int:
    match = re.search(r"\b(20\d{2})\b", text)
    if match:
        return int(match.group(1))
    month_match = re.search(
        r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)"
        r"[a-z]*[\\s_-]?(\\d{2})\b",
        text,
        re.IGNORECASE,
    )
    if month_match:
        return 2000 + int(month_match.group(1))
    return 0


def _extract_date(text: str) -> Optional[datetime]:
    patterns = [
        "%m/%d/%Y",
        "%m-%d-%Y",
        "%B %d, %Y",
        "%b %d, %Y",
    ]
    for pattern in patterns:
        try:
            return datetime.strptime(text, pattern)
        except ValueError:
            continue
    date_match = re.search(
        r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b", text
    )
    if date_match:
        raw = date_match.group(1)
        for pattern in ("%m/%d/%Y", "%m-%d-%Y", "%m/%d/%y", "%m-%d-%y"):
            try:
                return datetime.strptime(raw, pattern)
            except ValueError:
                continue
    return None


def build_version_key(text: str) -> Tuple[int, Optional[datetime]]:
    """Build a comparable version key from link text and url content."""
    year = _extract_year(text)
    date = _extract_date(text)
    return (year, date)


def sanitize_filename(url: str, fallback: str) -> str:
    """Return a safe filename derived from URL or fallback label."""
    parsed = urlparse(url)
    name = parsed.path.split("/")[-1]
    if not name or "." not in name:
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", fallback).strip("_")
        return f"{safe}.pdf"
    return name


def matches_keywords(text: str, include: Iterable[str], exclude: Iterable[str]) -> bool:
    lowered = text.lower()
    if include and not any(keyword in lowered for keyword in include):
        return False
    if exclude and any(keyword in lowered for keyword in exclude):
        return False
    return True


def compute_sha256(path: str) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def build_absolute_url(base_url: str, href: str) -> str:
    return urljoin(base_url, href)
