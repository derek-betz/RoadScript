"""
Unit tests for Standards Loader

Tests the JSON-based "Source of Truth" loading and access.
"""

import pytest
from roadscript.standards.loader import StandardsLoader


class TestStandardsLoader:
    """Test suite for StandardsLoader."""
    
    def test_singleton_pattern(self):
        """Test that StandardsLoader follows singleton pattern."""
        loader1 = StandardsLoader()
        loader2 = StandardsLoader()
        assert loader1 is loader2
    
    def test_get_standards(self):
        """Test getting complete standards dictionary."""
        loader = StandardsLoader()
        standards = loader.get_standards()
        
        assert isinstance(standards, dict)
        assert "metadata" in standards
        assert "buffer_strips" in standards
        assert "clear_zones" in standards
        assert "geometry" in standards
        assert "validation_rules" in standards
    
    def test_get_buffer_strip_standards(self):
        """Test getting buffer strip standards."""
        loader = StandardsLoader()
        buffer_standards = loader.get_buffer_strip_standards()
        
        assert isinstance(buffer_standards, dict)
        assert "description" in buffer_standards
        assert "standards" in buffer_standards
        assert "adjustment_factors" in buffer_standards
    
    def test_get_clear_zone_standards(self):
        """Test getting clear zone standards."""
        loader = StandardsLoader()
        clear_zone_standards = loader.get_clear_zone_standards()
        
        assert isinstance(clear_zone_standards, dict)
        assert "description" in clear_zone_standards
        assert "standards" in clear_zone_standards
    
    def test_get_geometry_standards(self):
        """Test getting geometry standards."""
        loader = StandardsLoader()
        geom_standards = loader.get_geometry_standards()
        
        assert isinstance(geom_standards, dict)
        assert "horizontal_curves" in geom_standards
        assert "vertical_curves" in geom_standards
    
    def test_get_validation_rules(self):
        """Test getting validation rules."""
        loader = StandardsLoader()
        rules = loader.get_validation_rules()
        
        assert isinstance(rules, dict)
        assert "buffer_strips" in rules
        assert "clear_zones" in rules
        assert "geometry" in rules
    
    def test_get_metadata(self):
        """Test getting standards metadata."""
        loader = StandardsLoader()
        metadata = loader.get_metadata()
        
        assert isinstance(metadata, dict)
        assert "version" in metadata
        assert "authority" in metadata
        assert "last_updated" in metadata
    
    def test_standards_structure(self):
        """Test that standards have expected structure."""
        loader = StandardsLoader()
        standards = loader.get_standards()
        
        # Check buffer strips structure
        buffer_strips = standards["buffer_strips"]
        assert "interstate" in buffer_strips["standards"]
        assert "us_route" in buffer_strips["standards"]
        assert "state_highway" in buffer_strips["standards"]
        assert "local_road" in buffer_strips["standards"]
        
        # Check clear zones structure
        clear_zones = standards["clear_zones"]
        assert "design_speed_based" in clear_zones["standards"]
        
        # Check geometry structure
        geometry = standards["geometry"]
        assert "horizontal_curves" in geometry
        assert "vertical_curves" in geometry
