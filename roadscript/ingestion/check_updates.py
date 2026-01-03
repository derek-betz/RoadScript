"""Check INDOT sources for updates and trigger ingestion."""

from __future__ import annotations

import logging

from roadscript.ingestion.fetch_indot_docs import fetch_indot_documents
from roadscript.ingestion.parse_documents import _list_pdf_paths, parse_documents, PDF_ROOT

LOG = logging.getLogger(__name__)


def check_for_updates(force: bool = False) -> bool:
    """Return True if updates were detected and ingested."""
    logging.basicConfig(level=logging.INFO)
    if force:
        LOG.info("Forced update requested.")
        fetch_indot_documents(dry_run=False)
        pdf_paths = _list_pdf_paths(PDF_ROOT)
        parse_documents(pdf_paths, rebuild_index=True)
        return True

    dry_run = fetch_indot_documents(dry_run=True)
    if not dry_run["downloaded"]:
        LOG.info("No updates detected.")
        return False

    LOG.info("Updates detected, downloading documents.")
    fetch_indot_documents(dry_run=False)
    pdf_paths = _list_pdf_paths(PDF_ROOT)
    parse_documents(pdf_paths, rebuild_index=True)
    return True


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Check INDOT updates and ingest.")
    parser.add_argument("--force", action="store_true", help="Force re-ingestion.")
    args = parser.parse_args()

    updated = check_for_updates(force=args.force)
    if updated:
        LOG.info("Ingestion completed.")
    else:
        LOG.info("No ingestion needed.")


if __name__ == "__main__":
    main()
