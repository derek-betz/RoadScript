"""
Integration tests for complete workflow

Tests end-to-end workflows combining multiple components.
"""

import pytest
from roadscript import (
    BufferStripCalculator,
    ClearZoneCalculator,
    GeometryCalculator,
    InputValidator,
    ComplianceChecker,
    StandardsLoader
)


class TestCompleteWorkflow:
    """Integration tests for complete calculation workflows."""
    
    def test_interstate_design_complete(self):
        """Test complete interstate highway design workflow."""
        # Initialize calculators
        buffer_calc = BufferStripCalculator()
        clear_zone_calc = ClearZoneCalculator()
        geom_calc = GeometryCalculator()
        
        design_speed = 70
        adt = 8000
        
        # Calculate buffer strip (use flat terrain to ensure compliance)
        buffer_result = buffer_calc.calculate(
            road_classification="interstate",
            design_speed=design_speed,
            terrain="flat",
            traffic_volume="medium"
        )
        
        assert buffer_result["compliant"]
        assert buffer_result["width"] > 0
        
        # Calculate clear zone
        clear_zone_result = clear_zone_calc.calculate(
            design_speed=design_speed,
            adt=adt,
            slope_category="fill_slope_6_1_or_flatter"
        )
        
        assert clear_zone_result["compliant"]
        assert clear_zone_result["width"] > 0
        
        # Calculate geometry
        radius_result = geom_calc.calculate_minimum_radius(design_speed=design_speed)
        ssd_result = geom_calc.calculate_stopping_sight_distance(design_speed=design_speed)
        
        assert radius_result["compliant"]
        assert ssd_result["compliant"]
        
        # Verify all calculations use same standards version
        assert buffer_result["standards_version"] == clear_zone_result["standards_version"]
        assert clear_zone_result["standards_version"] == radius_result["standards_version"]
    
    def test_local_road_design_complete(self):
        """Test complete local road design workflow."""
        buffer_calc = BufferStripCalculator()
        clear_zone_calc = ClearZoneCalculator()
        geom_calc = GeometryCalculator()
        
        design_speed = 35
        adt = 800
        
        # Calculate all parameters
        buffer_result = buffer_calc.calculate(
            road_classification="local_road",
            design_speed=design_speed,
            terrain="flat",
            traffic_volume="low"
        )
        
        clear_zone_result = clear_zone_calc.calculate(
            design_speed=30,  # Use 30 mph for clear zone (closest standard)
            adt=adt,
            slope_category="fill_slope_6_1_or_flatter"
        )
        
        radius_result = geom_calc.calculate_minimum_radius(design_speed=design_speed)
        
        # All should be compliant
        assert buffer_result["compliant"]
        assert clear_zone_result["compliant"]
        assert radius_result["compliant"]
        
        # Local roads have smaller values
        assert buffer_result["width"] < 30
        assert radius_result["minimum_radius"] < 500
    
    def test_validation_and_calculation_integration(self):
        """Test integration between validation and calculation."""
        validator = InputValidator()
        buffer_calc = BufferStripCalculator()
        
        # Valid inputs should pass validation and calculate (use flat terrain)
        inputs = {
            "road_classification": "state_highway",
            "design_speed": 50,
            "terrain": "flat"
        }
        
        is_valid, errors = validator.validate_buffer_strip_inputs(inputs)
        assert is_valid
        
        result = buffer_calc.calculate(**inputs)
        assert result["compliant"]
        
        # Invalid inputs should fail validation
        invalid_inputs = {
            "road_classification": "invalid_type",
            "design_speed": 50,
            "terrain": "flat"
        }
        
        is_valid, errors = validator.validate_buffer_strip_inputs(invalid_inputs)
        assert not is_valid
        
        with pytest.raises(ValueError):
            buffer_calc.calculate(**invalid_inputs)
    
    def test_compliance_checking_integration(self):
        """Test compliance checking with calculation results."""
        compliance = ComplianceChecker()
        buffer_calc = BufferStripCalculator()
        
        # Calculate buffer strip
        result = buffer_calc.calculate(
            road_classification="interstate",
            design_speed=65,
            terrain="flat",
            traffic_volume="medium"
        )
        
        # Verify compliance check
        inputs = {
            "road_classification": "interstate",
            "design_speed": 65,
            "terrain": "flat"
        }
        
        is_compliant, issues = compliance.check_buffer_strip_compliance(
            inputs,
            result["width"]
        )
        
        assert is_compliant == result["compliant"]
    
    def test_standards_loader_singleton(self):
        """Test that all components share same standards instance."""
        buffer_calc = BufferStripCalculator()
        clear_zone_calc = ClearZoneCalculator()
        geom_calc = GeometryCalculator()
        validator = InputValidator()
        
        # All should reference the same standards instance
        assert buffer_calc.standards is clear_zone_calc.standards
        assert clear_zone_calc.standards is geom_calc.standards
        assert geom_calc.standards is validator.standards
    
    def test_multi_calculation_consistency(self):
        """Test that multiple calculations produce consistent results."""
        buffer_calc = BufferStripCalculator()
        
        # Same inputs should produce same results
        result1 = buffer_calc.calculate(
            road_classification="us_route",
            design_speed=55,
            terrain="flat",
            traffic_volume="medium"
        )
        
        result2 = buffer_calc.calculate(
            road_classification="us_route",
            design_speed=55,
            terrain="flat",
            traffic_volume="medium"
        )
        
        assert result1["width"] == result2["width"]
        assert result1["base_width"] == result2["base_width"]
        assert result1["standards_version"] == result2["standards_version"]
