"""Integration tests for the ingestion pipeline."""

from pathlib import Path

import pytest

fitz = pytest.importorskip("fitz")

from roadscript.ingestion.parse_documents import parse_documents


def _create_sample_pdf(path: Path) -> None:
    doc = fitz.open()
    page = doc.new_page()
    text = (
        "Minimum Radius\n"
        "30 200\n"
        "40 360\n"
        "60 830\n"
        "\n"
        "K values\n"
        "30 19 37\n"
        "40 44 64\n"
        "60 151 136\n"
        "\n"
        "Stopping Sight Distance\n"
        "30 200\n"
        "60 570\n"
    )
    page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()


def test_parse_documents_writes_structured_output(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    pdf_root = data_root / "indot_pdfs"
    parsed_root = data_root / "parsed_text"
    structured_root = data_root / "structured"
    vector_root = data_root / "vector_index"

    pdf_root.mkdir(parents=True)
    sample_pdf = pdf_root / "sample.pdf"
    _create_sample_pdf(sample_pdf)

    base_standards = data_root / "idm_standards.json"
    base_standards.write_text(
        "{"
        "\"metadata\": {},"
        "\"geometry\": {"
        "\"horizontal_curves\": {\"minimum_radius\": {\"design_speed_radius\": {}}},"
        "\"vertical_curves\": {"
        "\"minimum_length\": {"
        "\"crest_curves\": {\"K_values\": {}},"
        "\"sag_curves\": {\"K_values\": {}}"
        "},"
        "\"stopping_sight_distance\": {\"design_speed_ssd\": {}}"
        "}"
        "},"
        "\"clear_zones\": {}"
        "}",
        encoding="utf-8",
    )

    report = parse_documents(
        pdf_paths=[sample_pdf],
        rebuild_index=False,
        build_index=False,
        pdf_root=pdf_root,
        parsed_root=parsed_root,
        structured_root=structured_root,
        vector_root=vector_root,
        manifest_path=pdf_root / "manifest.json",
        base_standards_path=base_standards,
    )

    assert report["geometry_extracted"]
    structured_path = structured_root / "idm_standards.json"
    assert structured_path.exists()
    structured_data = structured_path.read_text(encoding="utf-8")
    assert "\"60\": 830" in structured_data
    assert "\"60\": 151" in structured_data
    assert "\"60\": 136" in structured_data
