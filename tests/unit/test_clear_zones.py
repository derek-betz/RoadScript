"""
Unit tests for Clear Zone Calculator

Tests IDM-compliant clear zone width calculations.
"""

import pytest
from roadscript.core.clear_zones import ClearZoneCalculator
from roadscript.exceptions import StandardInterpolationRequiredError


class TestClearZoneCalculator:
    """Test suite for ClearZoneCalculator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = ClearZoneCalculator()

    def test_clear_zone_low_volume_foreslope(self):
        """Test clear zone calculation for low traffic volume (foreslope)."""
        result = self.calculator.calculate(
            design_speed=60,
            adt=300,
            slope_position="foreslope",
            slope_category="6_1_or_flatter"
        )

        assert result["min_width"] == 16
        assert result["max_width"] == 18
        assert result["adt_category"] == "<750"
        assert result["compliant"]
        assert result["units"] == "feet"

    def test_clear_zone_medium_volume_foreslope(self):
        """Test clear zone calculation for medium traffic volume (foreslope)."""
        result = self.calculator.calculate(
            design_speed=60,
            adt=1000,
            slope_position="foreslope",
            slope_category="5_1_or_4_1"
        )

        assert result["min_width"] == 26
        assert result["max_width"] == 32
        assert result["asterisk"]
        assert result["adt_category"] == "750-1500"
        assert result["compliant"]

    def test_clear_zone_high_volume_foreslope(self):
        """Test clear zone calculation for high traffic volume (foreslope)."""
        result = self.calculator.calculate(
            design_speed=60,
            adt=5000,
            slope_position="foreslope",
            slope_category="6_1_or_flatter"
        )

        assert result["min_width"] == 26
        assert result["max_width"] == 30
        assert result["adt_category"] == "1500-6000"
        assert result["compliant"]

    def test_clear_zone_very_high_volume_backslope(self):
        """Test clear zone calculation for very high traffic volume (backslope)."""
        result = self.calculator.calculate(
            design_speed=60,
            adt=8000,
            slope_position="backslope",
            slope_category="4_1_or_5_1"
        )

        assert result["min_width"] == 24
        assert result["max_width"] == 26
        assert result["adt_category"] == ">6000"
        assert result["compliant"]

    def test_clear_zone_backslopes(self):
        """Test clear zone calculation for backslopes at 45 mph."""
        result = self.calculator.calculate(
            design_speed=45,
            adt=1200,
            slope_position="backslope",
            slope_category="3_1"
        )

        assert result["min_width"] == 10
        assert result["max_width"] == 12
        assert result["adt_category"] == "750-1500"
        assert result["compliant"]

    def test_adt_category_determination(self):
        """Test AADT category determination."""
        assert self.calculator._get_adt_category(749) == "<750"
        assert self.calculator._get_adt_category(750) == "750-1500"
        assert self.calculator._get_adt_category(1499) == "750-1500"
        assert self.calculator._get_adt_category(1500) == "1500-6000"
        assert self.calculator._get_adt_category(6000) == "1500-6000"
        assert self.calculator._get_adt_category(6001) == ">6000"

    def test_invalid_design_speed(self):
        """Test that invalid design speed raises error."""
        with pytest.raises(ValueError) as exc_info:
            self.calculator.calculate(
                design_speed=20,
                adt=1000,
                slope_position="foreslope",
                slope_category="6_1_or_flatter"
            )
        assert "validation failed" in str(exc_info.value).lower()

    def test_invalid_slope_position(self):
        """Test that invalid slope position raises error."""
        with pytest.raises(ValueError) as exc_info:
            self.calculator.calculate(
                design_speed=60,
                adt=1000,
                slope_position="side",
                slope_category="6_1_or_flatter"
            )
        assert "validation failed" in str(exc_info.value).lower()

    def test_invalid_slope_category(self):
        """Test that invalid slope category raises error."""
        with pytest.raises(ValueError) as exc_info:
            self.calculator.calculate(
                design_speed=60,
                adt=1000,
                slope_position="foreslope",
                slope_category="invalid_slope"
            )
        assert "validation failed" in str(exc_info.value).lower()

    def test_negative_adt(self):
        """Test that negative ADT raises error."""
        with pytest.raises(ValueError) as exc_info:
            self.calculator.calculate(
                design_speed=60,
                adt=-100,
                slope_position="foreslope",
                slope_category="6_1_or_flatter"
            )
        assert "validation failed" in str(exc_info.value).lower()

    def test_missing_speed_requires_interpolation(self):
        """Test that missing design speed raises StandardInterpolationRequiredError."""
        with pytest.raises(StandardInterpolationRequiredError):
            self.calculator.calculate(
                design_speed=62,
                adt=1000,
                slope_position="foreslope",
                slope_category="6_1_or_flatter"
            )
