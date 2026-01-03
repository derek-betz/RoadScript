"""Fetch INDOT standards PDFs and maintain a local manifest."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Pattern

import requests
from bs4 import BeautifulSoup

from roadscript.ingestion.sources import SourceConfig, get_sources
from roadscript.ingestion.utils import (
    LinkInfo,
    build_absolute_url,
    build_version_key,
    compute_sha256,
    matches_keywords,
    sanitize_filename,
)

LOG = logging.getLogger(__name__)

DATA_ROOT = Path(__file__).resolve().parents[1] / "data"
PDF_ROOT = DATA_ROOT / "indot_pdfs"
MANIFEST_PATH = PDF_ROOT / "manifest.json"


def _load_manifest() -> Dict[str, object]:
    if MANIFEST_PATH.exists():
        with MANIFEST_PATH.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    return {"sources": {}}


def _save_manifest(manifest: Dict[str, object]) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST_PATH.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, ensure_ascii=True)


def _scrape_page_links(
    session: requests.Session,
    page_url: str,
    link_regex: Optional[Pattern[str]],
    include_keywords: List[str],
    exclude_keywords: List[str],
) -> List[LinkInfo]:
    LOG.info("Fetching page: %s", page_url)
    response = session.get(page_url, timeout=60)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    links: List[LinkInfo] = []
    for anchor in soup.find_all("a"):
        href = anchor.get("href")
        if not href:
            continue
        if link_regex and not link_regex.search(href):
            continue
        text = " ".join(anchor.get_text(" ").split())
        composite = f"{text} {href}"
        if not matches_keywords(composite, include_keywords, exclude_keywords):
            continue
        url = build_absolute_url(page_url, href)
        version_key = build_version_key(composite)
        links.append(LinkInfo(url=url, text=text or href, version_key=version_key))
    return links


def _select_links(mode: str, links: List[LinkInfo]) -> List[LinkInfo]:
    if not links:
        return []
    if mode == "all":
        return sorted(links, key=lambda link: link.url)
    latest = max(
        links,
        key=lambda link: (link.version_key[0], link.version_key[1] or datetime.min),
    )
    return [latest]


def _head_metadata(
    session: requests.Session,
    url: str,
) -> Dict[str, Optional[str]]:
    try:
        response = session.head(url, allow_redirects=True, timeout=30)
        if response.status_code >= 400:
            return {}
        return {
            "etag": response.headers.get("ETag"),
            "last_modified": response.headers.get("Last-Modified"),
            "content_length": response.headers.get("Content-Length"),
        }
    except requests.RequestException:
        return {}


def _should_download(
    existing: Optional[Dict[str, object]],
    head_meta: Dict[str, Optional[str]],
    destination: Path,
) -> bool:
    if not destination.exists() or existing is None:
        return True
    if head_meta.get("etag") and existing.get("etag") != head_meta.get("etag"):
        return True
    if head_meta.get("last_modified") and existing.get("last_modified") != head_meta.get("last_modified"):
        return True
    return False


def _download_file(
    session: requests.Session,
    url: str,
    destination: Path,
    retries: int = 3,
) -> Dict[str, object]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_path = destination.with_suffix(destination.suffix + ".part")
    last_error: Optional[Exception] = None

    for attempt in range(1, retries + 1):
        try:
            with session.get(url, stream=True, timeout=120) as response:
                response.raise_for_status()
                with temp_path.open("wb") as handle:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            handle.write(chunk)
                temp_path.replace(destination)
                return {
                    "etag": response.headers.get("ETag"),
                    "last_modified": response.headers.get("Last-Modified"),
                    "content_length": response.headers.get("Content-Length"),
                    "sha256": compute_sha256(str(destination)),
                }
        except requests.RequestException as exc:
            last_error = exc
            LOG.warning("Download failed (%s/%s) for %s: %s", attempt, retries, url, exc)
            if temp_path.exists():
                temp_path.unlink()

    if last_error:
        raise last_error
    return {}


def fetch_indot_documents(
    sources: Optional[List[SourceConfig]] = None,
    dry_run: bool = False,
) -> Dict[str, object]:
    """Download INDOT PDFs and update manifest."""
    logging.basicConfig(level=logging.INFO)
    session = requests.Session()
    session.headers.update({"User-Agent": "RoadScript/1.0"})

    manifest = _load_manifest()
    manifest.setdefault("sources", {})
    manifest["generated_at"] = datetime.now(timezone.utc).isoformat()
    results: Dict[str, object] = {"downloaded": [], "skipped": []}

    for source in sources or get_sources():
        index_pages: List[LinkInfo] = []
        if source.index_link_regex or source.index_include_keywords or source.index_exclude_keywords:
            index_links = _scrape_page_links(
                session,
                source.index_url,
                source.index_link_regex,
                source.index_include_keywords,
                source.index_exclude_keywords,
            )
            index_pages = _select_links(source.index_download_mode, index_links)
        else:
            index_pages = [
                LinkInfo(
                    url=source.index_url,
                    text=source.name,
                    version_key=build_version_key(source.index_url),
                )
            ]

        if not index_pages:
            LOG.warning("No index pages found for %s", source.name)
            continue

        source_entry = manifest["sources"].setdefault(source.name, {})
        source_entry["index_url"] = source.index_url
        source_entry.setdefault("documents", [])
        known_docs = {doc["url"]: doc for doc in source_entry["documents"]}

        for index_page in index_pages:
            pdf_links = _scrape_page_links(
                session,
                index_page.url,
                source.link_regex,
                source.include_keywords,
                source.exclude_keywords,
            )
            selected_links = _select_links(source.download_mode, pdf_links)
            if not selected_links:
                LOG.warning("No PDF links found for %s on %s", source.name, index_page.url)
                continue

            for link in selected_links:
                filename = sanitize_filename(link.url, f"{source.name}")
                destination = PDF_ROOT / source.output_subdir / filename
                head_meta = _head_metadata(session, link.url)
                existing = known_docs.get(link.url)

                if existing is None and destination.exists():
                    metadata = {
                        "etag": head_meta.get("etag"),
                        "last_modified": head_meta.get("last_modified"),
                        "content_length": head_meta.get("content_length"),
                        "sha256": compute_sha256(str(destination)),
                    }
                    doc_entry = {
                        "url": link.url,
                        "filename": str(destination.relative_to(PDF_ROOT)),
                        "label": link.text,
                        "version_year": link.version_key[0],
                        "version_date": link.version_key[1].isoformat() if link.version_key[1] else None,
                        "downloaded_at": datetime.now(timezone.utc).isoformat(),
                        "index_page": index_page.url,
                        "discovered_on_disk": True,
                    }
                    doc_entry.update(metadata)
                    known_docs[link.url] = doc_entry
                    results["skipped"].append(link.url)
                    continue

                if not _should_download(existing, head_meta, destination):
                    results["skipped"].append(link.url)
                    continue

                if dry_run:
                    results["downloaded"].append(link.url)
                    continue

                LOG.info("Downloading %s", link.url)
                try:
                    metadata = _download_file(session, link.url, destination)
                except requests.RequestException as exc:
                    LOG.warning("Failed to download %s: %s", link.url, exc)
                    results["skipped"].append(link.url)
                    continue
                doc_entry = {
                    "url": link.url,
                    "filename": str(destination.relative_to(PDF_ROOT)),
                    "label": link.text,
                    "version_year": link.version_key[0],
                    "version_date": link.version_key[1].isoformat() if link.version_key[1] else None,
                    "downloaded_at": datetime.now(timezone.utc).isoformat(),
                    "index_page": index_page.url,
                }
                doc_entry.update(metadata)
                known_docs[link.url] = doc_entry
                results["downloaded"].append(link.url)

        source_entry["documents"] = list(known_docs.values())

    if not dry_run:
        _save_manifest(manifest)

    return results


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Fetch INDOT standards PDFs.")
    parser.add_argument("--dry-run", action="store_true", help="Report updates only.")
    args = parser.parse_args()

    result = fetch_indot_documents(dry_run=args.dry_run)
    LOG.info("Downloaded: %s", len(result["downloaded"]))
    LOG.info("Skipped: %s", len(result["skipped"]))


if __name__ == "__main__":
    main()
