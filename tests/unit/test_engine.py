"""
Unit tests for core engine functions.
"""

import pytest

from roadscript.core.engine import calculate_k_value, evaluate_clear_zone_requirement
from roadscript.exceptions import StandardInterpolationRequiredError


class TestEngine:
    """Test suite for engine utilities."""

    def test_calculate_k_value_basic(self):
        """Test K-value calculation with positive inputs."""
        assert calculate_k_value(400, 5.0) == 80.0

    def test_calculate_k_value_negative_grade(self):
        """Test K-value calculation uses absolute grade difference."""
        assert calculate_k_value(400, -5.0) == 80.0

    def test_calculate_k_value_zero_length(self):
        """Test K-value calculation rejects zero length."""
        with pytest.raises(ValueError):
            calculate_k_value(0, 5.0)

    def test_calculate_k_value_zero_grade(self):
        """Test K-value calculation rejects zero algebraic difference."""
        with pytest.raises(ValueError):
            calculate_k_value(400, 0)

    def test_clear_zone_requirement_foreslope(self):
        """Test clear zone requirement lookup for foreslope range."""
        result = evaluate_clear_zone_requirement(
            design_speed=60,
            adt=5000,
            slope_position="foreslope",
            slope_category="6_1_or_flatter"
        )

        assert result["min"] == 26
        assert result["max"] == 30
        assert result.get("asterisk") is None

    def test_clear_zone_requirement_backslope(self):
        """Test clear zone requirement lookup for backslope range."""
        result = evaluate_clear_zone_requirement(
            design_speed=60,
            adt=8000,
            slope_position="backslope",
            slope_category="4_1_or_5_1"
        )

        assert result["min"] == 24
        assert result["max"] == 26

    def test_clear_zone_requirement_asterisk(self):
        """Test clear zone requirement lookup preserves asterisk flag."""
        result = evaluate_clear_zone_requirement(
            design_speed=55,
            adt=7000,
            slope_position="foreslope",
            slope_category="5_1_or_4_1"
        )

        assert result["min"] == 26
        assert result["max"] == 32
        assert result.get("asterisk") is True

    def test_clear_zone_requirement_invalid_speed(self):
        """Test missing design speed triggers interpolation error."""
        with pytest.raises(StandardInterpolationRequiredError):
            evaluate_clear_zone_requirement(
                design_speed=62,
                adt=5000,
                slope_position="foreslope",
                slope_category="6_1_or_flatter"
            )

    def test_clear_zone_requirement_invalid_slope_position(self):
        """Test invalid slope position raises error."""
        with pytest.raises(ValueError):
            evaluate_clear_zone_requirement(
                design_speed=60,
                adt=5000,
                slope_position="side",
                slope_category="6_1_or_flatter"
            )

    def test_clear_zone_requirement_missing_category(self):
        """Test invalid slope category raises error."""
        with pytest.raises(ValueError):
            evaluate_clear_zone_requirement(
                design_speed=60,
                adt=5000,
                slope_position="foreslope",
                slope_category="invalid_slope"
            )

    def test_clear_zone_requirement_negative_adt(self):
        """Test negative ADT raises error."""
        with pytest.raises(ValueError):
            evaluate_clear_zone_requirement(
                design_speed=60,
                adt=-1,
                slope_position="foreslope",
                slope_category="6_1_or_flatter"
            )
