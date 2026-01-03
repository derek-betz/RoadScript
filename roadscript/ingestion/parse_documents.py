"""Parse INDOT PDFs into text, structured tables, and vector index."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import fitz

from roadscript.ai.chunking import chunk_text
from roadscript.ai.vector_index import VectorIndex
from roadscript.ingestion.structured_extractors import (
    ExtractionResult,
    extract_clear_zone_standards,
    extract_geometry_standards,
    merge_structured_standards,
)

LOG = logging.getLogger(__name__)

DATA_ROOT = Path(__file__).resolve().parents[1] / "data"
PDF_ROOT = DATA_ROOT / "indot_pdfs"
PARSED_ROOT = DATA_ROOT / "parsed_text"
STRUCTURED_ROOT = DATA_ROOT / "structured"
VECTOR_ROOT = DATA_ROOT / "vector_index"
MANIFEST_PATH = PDF_ROOT / "manifest.json"
BASE_STANDARDS_PATH = DATA_ROOT / "idm_standards.json"


def _load_manifest(manifest_path: Path) -> Dict[str, object]:
    if manifest_path.exists():
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    return {}


def _list_pdf_paths(root: Path) -> List[Path]:
    paths = list(root.rglob("*.pdf")) + list(root.rglob("*.PDF"))
    return sorted(set(paths))


def _extract_pdf_text(pdf_path: Path) -> Tuple[str, List[str]]:
    doc = fitz.open(pdf_path)
    pages: List[str] = []
    for page in doc:
        text = page.get_text("text")
        pages.append(text)
    doc.close()
    full_text = "\n\n".join(pages)
    return full_text, pages


def _write_parsed_text(
    pdf_path: Path,
    pages: List[str],
    pdf_root: Path,
    parsed_root: Path,
) -> Path:
    relative = pdf_path.relative_to(pdf_root)
    output_path = parsed_root / relative.with_suffix(".txt")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = []
    for idx, page in enumerate(pages, start=1):
        content.append(f"--- Page {idx} ---")
        content.append(page.strip())
    output_path.write_text("\n\n".join(content), encoding="utf-8")
    return output_path


def _load_base_standards(base_standards_path: Path) -> Dict[str, object]:
    if not base_standards_path.exists():
        return {}
    return json.loads(base_standards_path.read_text(encoding="utf-8"))


def parse_documents(
    pdf_paths: Iterable[Path],
    rebuild_index: bool = True,
    build_index: bool = True,
    pdf_root: Path = PDF_ROOT,
    parsed_root: Path = PARSED_ROOT,
    structured_root: Path = STRUCTURED_ROOT,
    vector_root: Path = VECTOR_ROOT,
    manifest_path: Path = MANIFEST_PATH,
    base_standards_path: Path = BASE_STANDARDS_PATH,
) -> Dict[str, object]:
    """Parse documents and build structured + vector data artifacts."""
    logging.basicConfig(level=logging.INFO)
    pdf_list = list(pdf_paths)
    manifest = _load_manifest(manifest_path)
    manifest_docs = {}
    for source in manifest.get("sources", {}).values():
        for doc in source.get("documents", []):
            manifest_docs[doc.get("filename")] = doc

    texts: List[str] = []
    metadatas: List[Dict[str, object]] = []
    ids: List[str] = []
    combined_text = []

    for pdf_path in pdf_list:
        LOG.info("Parsing %s", pdf_path)
        try:
            full_text, pages = _extract_pdf_text(pdf_path)
        except Exception as exc:  # pragma: no cover - defensive
            LOG.error("Failed to parse %s: %s", pdf_path, exc)
            continue
        combined_text.append(full_text)
        _write_parsed_text(pdf_path, pages, pdf_root, parsed_root)

        relative = str(pdf_path.relative_to(pdf_root))
        metadata = manifest_docs.get(relative, {})
        chunked = chunk_text(full_text)
        for idx, chunk in enumerate(chunked):
            ids.append(f"{relative}:{idx}")
            texts.append(chunk)
            metadata_entry = {
                "source": relative,
                "label": metadata.get("label"),
                "version_year": metadata.get("version_year"),
                "version_date": metadata.get("version_date"),
            }
            metadatas.append(
                {key: value for key, value in metadata_entry.items() if value is not None}
            )

    if texts and build_index:
        vector_index = VectorIndex(vector_root)
        if rebuild_index:
            vector_index.reset()
        vector_index.add_documents(texts, metadatas, ids)
        vector_index.save_config()

    combined = "\n\n".join(combined_text)
    geometry = extract_geometry_standards(combined)
    clear_zones = extract_clear_zone_standards(combined)

    extraction = ExtractionResult(
        geometry=geometry,
        clear_zones=clear_zones,
        metadata={
            "sources": list(manifest.get("sources", {}).keys()),
        },
    )

    base_standards = _load_base_standards(base_standards_path)
    merged = merge_structured_standards(base_standards, extraction)
    structured_root.mkdir(parents=True, exist_ok=True)
    structured_path = structured_root / "idm_standards.json"
    structured_path.write_text(
        json.dumps(merged, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )

    report_path = structured_root / "extraction_report.json"
    report = {
        "geometry_extracted": bool(geometry),
        "clear_zones_extracted": bool(clear_zones),
        "documents_parsed": len(pdf_list),
    }
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")

    return report


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Parse INDOT PDFs.")
    parser.add_argument(
        "--rebuild-index",
        action="store_true",
        help="Rebuild the vector index from scratch.",
    )
    args = parser.parse_args()

    pdf_paths = _list_pdf_paths(PDF_ROOT)
    if not pdf_paths:
        LOG.warning("No PDFs found in %s", PDF_ROOT)
        return
    report = parse_documents(pdf_paths, rebuild_index=args.rebuild_index)
    LOG.info("Structured extraction report: %s", report)


if __name__ == "__main__":
    main()
