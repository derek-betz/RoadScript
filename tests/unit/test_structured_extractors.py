"""Tests for structured extraction helpers."""

from roadscript.ingestion.structured_extractors import extract_geometry_standards


def test_extract_geometry_standards_basic_tables():
    sample_text = """
    Minimum Radius
    30 200
    40 360
    60 830

    K values
    30 19 37
    40 44 64
    60 151 136

    Stopping Sight Distance
    30 200
    60 570
    """
    geometry = extract_geometry_standards(sample_text)
    radius = geometry["horizontal_curves"]["minimum_radius"]["design_speed_radius"]
    assert radius["30"] == 200
    assert radius["60"] == 830

    crest = geometry["vertical_curves"]["minimum_length"]["crest_curves"]["K_values"]
    sag = geometry["vertical_curves"]["minimum_length"]["sag_curves"]["K_values"]
    assert crest["30"] == 19
    assert sag["30"] == 37
    assert crest["60"] == 151
    assert sag["60"] == 136

    ssd = geometry["vertical_curves"]["stopping_sight_distance"]["design_speed_ssd"]
    assert ssd["30"] == 200
    assert ssd["60"] == 570


def test_extract_geometry_standards_design_speed_ssd_table():
    sample_text = """
    Design Speed
    40 mph 45 mph 50 mph 55 mph 60 mph
    *Stopping Sight Distance
    42-1.0
    305 ft 360 ft 425 ft 495 ft 570 ft
    """
    geometry = extract_geometry_standards(sample_text)
    ssd = geometry["vertical_curves"]["stopping_sight_distance"]["design_speed_ssd"]
    assert ssd["40"] == 305
    assert ssd["55"] == 495


def test_extract_geometry_standards_multiline_ssd_table():
    sample_text = """
    Design Speed
    ---
    40 mph
    45 mph
    50 mph
    55 mph
    60 mph
    *Stopping Sight Distance
    42-1.0
    305 ft
    360 ft
    425 ft
    495 ft
    570 ft
    Decision Sight Distance
    """
    geometry = extract_geometry_standards(sample_text)
    ssd = geometry["vertical_curves"]["stopping_sight_distance"]["design_speed_ssd"]
    assert ssd["45"] == 360
    assert ssd["60"] == 570
