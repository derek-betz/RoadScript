"""
Unit tests for Input Validators

Tests validation of inputs for all calculation types.
"""

import pytest
from roadscript.validation.validators import InputValidator


class TestInputValidator:
    """Test suite for InputValidator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = InputValidator()
    
    # Buffer Strip Validation Tests
    
    def test_buffer_strip_valid_inputs(self):
        """Test validation of valid buffer strip inputs."""
        inputs = {
            "road_classification": "interstate",
            "design_speed": 65,
            "terrain": "flat"
        }
        is_valid, errors = self.validator.validate_buffer_strip_inputs(inputs)
        assert is_valid
        assert len(errors) == 0
    
    def test_buffer_strip_missing_required_field(self):
        """Test validation fails when required field is missing."""
        inputs = {
            "road_classification": "interstate",
            "design_speed": 65
            # Missing terrain
        }
        is_valid, errors = self.validator.validate_buffer_strip_inputs(inputs)
        assert not is_valid
        assert any("terrain" in err for err in errors)
    
    def test_buffer_strip_invalid_classification(self):
        """Test validation fails with invalid road classification."""
        inputs = {
            "road_classification": "invalid_type",
            "design_speed": 65,
            "terrain": "flat"
        }
        is_valid, errors = self.validator.validate_buffer_strip_inputs(inputs)
        assert not is_valid
        assert any("road_classification" in err for err in errors)
    
    def test_buffer_strip_invalid_terrain(self):
        """Test validation fails with invalid terrain."""
        inputs = {
            "road_classification": "interstate",
            "design_speed": 65,
            "terrain": "underwater"
        }
        is_valid, errors = self.validator.validate_buffer_strip_inputs(inputs)
        assert not is_valid
        assert any("terrain" in err for err in errors)
    
    def test_buffer_strip_invalid_speed(self):
        """Test validation fails with out-of-range design speed."""
        inputs = {
            "road_classification": "interstate",
            "design_speed": 150,  # Too high
            "terrain": "flat"
        }
        is_valid, errors = self.validator.validate_buffer_strip_inputs(inputs)
        assert not is_valid
        assert any("speed" in err.lower() for err in errors)
    
    # Clear Zone Validation Tests
    
    def test_clear_zone_valid_inputs(self):
        """Test validation of valid clear zone inputs."""
        inputs = {
            "design_speed": 60,
            "adt": 5000,
            "slope_category": "fill_slope_6_1_or_flatter"
        }
        is_valid, errors = self.validator.validate_clear_zone_inputs(inputs)
        assert is_valid
        assert len(errors) == 0
    
    def test_clear_zone_missing_required_field(self):
        """Test validation fails when required field is missing."""
        inputs = {
            "design_speed": 60,
            "adt": 5000
            # Missing slope_category
        }
        is_valid, errors = self.validator.validate_clear_zone_inputs(inputs)
        assert not is_valid
        assert any("slope_category" in err for err in errors)
    
    def test_clear_zone_invalid_slope_category(self):
        """Test validation fails with invalid slope category."""
        inputs = {
            "design_speed": 60,
            "adt": 5000,
            "slope_category": "invalid_slope"
        }
        is_valid, errors = self.validator.validate_clear_zone_inputs(inputs)
        assert not is_valid
        assert any("slope_category" in err for err in errors)
    
    def test_clear_zone_invalid_speed(self):
        """Test validation fails with out-of-range design speed."""
        inputs = {
            "design_speed": 20,  # Too low
            "adt": 5000,
            "slope_category": "fill_slope_6_1_or_flatter"
        }
        is_valid, errors = self.validator.validate_clear_zone_inputs(inputs)
        assert not is_valid
        assert any("speed" in err.lower() for err in errors)
    
    def test_clear_zone_negative_adt(self):
        """Test validation fails with negative ADT."""
        inputs = {
            "design_speed": 60,
            "adt": -100,
            "slope_category": "fill_slope_6_1_or_flatter"
        }
        is_valid, errors = self.validator.validate_clear_zone_inputs(inputs)
        assert not is_valid
        assert any("ADT" in err for err in errors)
    
    # Geometry Validation Tests
    
    def test_geometry_valid_inputs(self):
        """Test validation of valid geometry inputs."""
        inputs = {
            "design_speed": 60
        }
        is_valid, errors = self.validator.validate_geometry_inputs(inputs)
        assert is_valid
        assert len(errors) == 0
    
    def test_geometry_missing_required_field(self):
        """Test validation fails when required field is missing."""
        inputs = {}
        is_valid, errors = self.validator.validate_geometry_inputs(inputs)
        assert not is_valid
        assert any("design_speed" in err for err in errors)
    
    def test_geometry_invalid_speed(self):
        """Test validation fails with out-of-range design speed."""
        inputs = {
            "design_speed": 200
        }
        is_valid, errors = self.validator.validate_geometry_inputs(inputs)
        assert not is_valid
        assert any("speed" in err.lower() for err in errors)
    
    def test_geometry_invalid_grade(self):
        """Test validation fails with out-of-range grade."""
        inputs = {
            "design_speed": 60,
            "grade": 20  # Too steep
        }
        is_valid, errors = self.validator.validate_geometry_inputs(inputs)
        assert not is_valid
        assert any("grade" in err.lower() for err in errors)
