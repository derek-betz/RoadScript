"""
Pytest suite for RoadScript vertical curve compliance.
"""

import pytest

from roadscript.exceptions import StandardInterpolationRequiredError
from roadscript.validators.base import validate_vertical_curve_k


class TestRoadScriptVerticalCurves:
    """Vertical curve validation tests (IDM 43-4.0)."""

    def test_case_1_crest_pass(self):
        """45 mph crest, L=400, A=5.0 -> K=80 (PASS)."""
        result = validate_vertical_curve_k(
            design_speed=45,
            curve_type="crest",
            length_of_curve=400,
            algebraic_diff=5.0
        )

        assert result.status
        assert result.actual_k == 80.0
        assert result.required_k == 61.0

    def test_case_2_crest_fail(self):
        """45 mph crest, L=200, A=4.0 -> K=50 (FAIL)."""
        result = validate_vertical_curve_k(
            design_speed=45,
            curve_type="crest",
            length_of_curve=200,
            algebraic_diff=4.0
        )

        assert not result.status
        assert "IDM 43-4.0" in result.message
        assert result.actual_k == 50.0
        assert result.required_k == 61.0

    def test_case_3_sag_pass(self):
        """45 mph sag, L=400, A=5.0 -> K=80 (PASS)."""
        result = validate_vertical_curve_k(
            design_speed=45,
            curve_type="sag",
            length_of_curve=400,
            algebraic_diff=5.0
        )

        assert result.status
        assert result.actual_k == 80.0
        assert result.required_k == 79.0

    def test_case_4_sag_fail(self):
        """45 mph sag, L=300, A=5.0 -> K=60 (FAIL)."""
        result = validate_vertical_curve_k(
            design_speed=45,
            curve_type="sag",
            length_of_curve=300,
            algebraic_diff=5.0
        )

        assert not result.status
        assert "IDM 43-4.0" in result.message
        assert result.actual_k == 60.0
        assert result.required_k == 79.0

    def test_case_5_missing_speed(self):
        """Design speed not in IDM table requires interpolation."""
        with pytest.raises(StandardInterpolationRequiredError):
            validate_vertical_curve_k(
                design_speed=47,
                curve_type="crest",
                length_of_curve=300,
                algebraic_diff=5.0
            )
