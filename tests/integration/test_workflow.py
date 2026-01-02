"""
Integration tests for complete workflow

Tests end-to-end workflows combining multiple components.
"""

import pytest
from roadscript import (
    ClearZoneCalculator,
    GeometryCalculator,
    InputValidator,
    ComplianceChecker
)


class TestCompleteWorkflow:
    """Integration tests for complete calculation workflows."""

    def test_interstate_design_complete(self):
        """Test complete interstate highway design workflow."""
        clear_zone_calc = ClearZoneCalculator()
        geom_calc = GeometryCalculator()

        design_speed = 70
        adt = 8000

        clear_zone_result = clear_zone_calc.calculate(
            design_speed=design_speed,
            adt=adt,
            slope_position="foreslope",
            slope_category="6_1_or_flatter"
        )

        assert clear_zone_result["compliant"]
        assert clear_zone_result["min_width"] > 0

        radius_result = geom_calc.calculate_minimum_radius(design_speed=design_speed)
        ssd_result = geom_calc.calculate_stopping_sight_distance(design_speed=design_speed)

        assert radius_result["compliant"]
        assert ssd_result["compliant"]

        assert clear_zone_result["standards_version"] == radius_result["standards_version"]

    def test_local_road_design_complete(self):
        """Test complete local road design workflow."""
        clear_zone_calc = ClearZoneCalculator()
        geom_calc = GeometryCalculator()

        design_speed = 40
        adt = 800

        clear_zone_result = clear_zone_calc.calculate(
            design_speed=30,
            adt=adt,
            slope_position="foreslope",
            slope_category="6_1_or_flatter"
        )

        radius_result = geom_calc.calculate_minimum_radius(design_speed=design_speed)

        assert clear_zone_result["compliant"]
        assert radius_result["compliant"]

        assert radius_result["minimum_radius"] < 500

    def test_validation_and_calculation_integration(self):
        """Test integration between validation and calculation."""
        validator = InputValidator()
        clear_zone_calc = ClearZoneCalculator()

        inputs = {
            "design_speed": 60,
            "adt": 5000,
            "slope_position": "foreslope",
            "slope_category": "6_1_or_flatter"
        }

        is_valid, errors = validator.validate_clear_zone_inputs(inputs)
        assert is_valid

        result = clear_zone_calc.calculate(**inputs)
        assert result["compliant"]

        invalid_inputs = {
            "design_speed": 60,
            "adt": 5000,
            "slope_position": "foreslope",
            "slope_category": "invalid_slope"
        }

        is_valid, errors = validator.validate_clear_zone_inputs(invalid_inputs)
        assert not is_valid

        with pytest.raises(ValueError):
            clear_zone_calc.calculate(**invalid_inputs)

    def test_compliance_checking_integration(self):
        """Test compliance checking with calculation results."""
        compliance = ComplianceChecker()
        clear_zone_calc = ClearZoneCalculator()

        result = clear_zone_calc.calculate(
            design_speed=60,
            adt=5000,
            slope_position="foreslope",
            slope_category="6_1_or_flatter"
        )

        inputs = {
            "design_speed": 60,
            "adt": 5000,
            "slope_position": "foreslope",
            "slope_category": "6_1_or_flatter"
        }

        is_compliant, issues = compliance.check_clear_zone_compliance(
            inputs,
            {"min": result["min_width"], "max": result["max_width"]}
        )

        assert is_compliant == result["compliant"]

    def test_standards_loader_singleton(self):
        """Test that all components share same standards instance."""
        clear_zone_calc = ClearZoneCalculator()
        geom_calc = GeometryCalculator()
        validator = InputValidator()

        assert clear_zone_calc.standards is geom_calc.standards
        assert geom_calc.standards is validator.standards

    def test_multi_calculation_consistency(self):
        """Test that multiple calculations produce consistent results."""
        clear_zone_calc = ClearZoneCalculator()

        result1 = clear_zone_calc.calculate(
            design_speed=60,
            adt=5000,
            slope_position="foreslope",
            slope_category="6_1_or_flatter"
        )

        result2 = clear_zone_calc.calculate(
            design_speed=60,
            adt=5000,
            slope_position="foreslope",
            slope_category="6_1_or_flatter"
        )

        assert result1["min_width"] == result2["min_width"]
        assert result1["max_width"] == result2["max_width"]
        assert result1["standards_version"] == result2["standards_version"]
