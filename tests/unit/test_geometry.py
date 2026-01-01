"""
Unit tests for Geometry Calculator

Tests IDM-compliant geometric design calculations.
"""

import pytest
from roadscript.core.geometry import GeometryCalculator


class TestGeometryCalculator:
    """Test suite for GeometryCalculator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = GeometryCalculator()
    
    # Minimum Radius Tests
    
    def test_minimum_radius_30_mph(self):
        """Test minimum radius calculation for 30 mph."""
        result = self.calculator.calculate_minimum_radius(design_speed=30)
        
        assert result["minimum_radius"] == 200
        assert result["design_speed"] == 30
        assert result["compliant"]
        assert result["units"] == "feet"
    
    def test_minimum_radius_60_mph(self):
        """Test minimum radius calculation for 60 mph."""
        result = self.calculator.calculate_minimum_radius(design_speed=60)
        
        assert result["minimum_radius"] == 830
        assert result["design_speed"] == 60
        assert result["compliant"]
    
    def test_minimum_radius_80_mph(self):
        """Test minimum radius calculation for 80 mph."""
        result = self.calculator.calculate_minimum_radius(design_speed=80)
        
        assert result["minimum_radius"] == 1570
        assert result["design_speed"] == 80
        assert result["compliant"]
    
    def test_minimum_radius_increases_with_speed(self):
        """Test that minimum radius increases with design speed."""
        result_30 = self.calculator.calculate_minimum_radius(design_speed=30)
        result_50 = self.calculator.calculate_minimum_radius(design_speed=50)
        result_70 = self.calculator.calculate_minimum_radius(design_speed=70)
        
        assert result_70["minimum_radius"] > result_50["minimum_radius"] > result_30["minimum_radius"]
    
    def test_minimum_radius_includes_friction_factor(self):
        """Test that result includes friction factor."""
        result = self.calculator.calculate_minimum_radius(design_speed=60)
        
        assert "friction_factor" in result
        assert 0 < result["friction_factor"] < 1
    
    def test_minimum_radius_includes_superelevation(self):
        """Test that result includes superelevation."""
        result = self.calculator.calculate_minimum_radius(design_speed=60)
        
        assert "superelevation_max" in result
        assert result["superelevation_max"] == 0.06
    
    # Vertical Curve Length Tests
    
    def test_vertical_curve_crest(self):
        """Test crest vertical curve length calculation."""
        result = self.calculator.calculate_vertical_curve_length(
            design_speed=60,
            grade_difference=4.0,
            curve_type="crest"
        )
        
        # K=151 for 60 mph crest, L = K * A = 151 * 4 = 604
        assert result["curve_length"] == 604.0
        assert result["k_value"] == 151
        assert result["curve_type"] == "crest"
        assert result["compliant"]
    
    def test_vertical_curve_sag(self):
        """Test sag vertical curve length calculation."""
        result = self.calculator.calculate_vertical_curve_length(
            design_speed=60,
            grade_difference=4.0,
            curve_type="sag"
        )
        
        # K=136 for 60 mph sag, L = K * A = 136 * 4 = 544
        assert result["curve_length"] == 544.0
        assert result["k_value"] == 136
        assert result["curve_type"] == "sag"
        assert result["compliant"]
    
    def test_vertical_curve_different_grade_differences(self):
        """Test vertical curves with different grade differences."""
        result_2 = self.calculator.calculate_vertical_curve_length(
            design_speed=60,
            grade_difference=2.0,
            curve_type="crest"
        )
        
        result_6 = self.calculator.calculate_vertical_curve_length(
            design_speed=60,
            grade_difference=6.0,
            curve_type="crest"
        )
        
        # Larger grade difference requires longer curve
        assert result_6["curve_length"] > result_2["curve_length"]
        assert result_6["curve_length"] == result_2["curve_length"] * 3
    
    def test_vertical_curve_negative_grade_difference(self):
        """Test that negative grade differences are handled (absolute value)."""
        result = self.calculator.calculate_vertical_curve_length(
            design_speed=60,
            grade_difference=-4.0,
            curve_type="crest"
        )
        
        assert result["curve_length"] == 604.0
        assert result["grade_difference"] == 4.0  # Stored as absolute
    
    # Stopping Sight Distance Tests
    
    def test_stopping_sight_distance_30_mph(self):
        """Test stopping sight distance for 30 mph."""
        result = self.calculator.calculate_stopping_sight_distance(design_speed=30)
        
        assert result["stopping_sight_distance"] == 200
        assert result["design_speed"] == 30
        assert result["compliant"]
    
    def test_stopping_sight_distance_60_mph(self):
        """Test stopping sight distance for 60 mph."""
        result = self.calculator.calculate_stopping_sight_distance(design_speed=60)
        
        assert result["stopping_sight_distance"] == 570
        assert result["design_speed"] == 60
        assert result["compliant"]
    
    def test_stopping_sight_distance_80_mph(self):
        """Test stopping sight distance for 80 mph."""
        result = self.calculator.calculate_stopping_sight_distance(design_speed=80)
        
        assert result["stopping_sight_distance"] == 910
        assert result["design_speed"] == 80
        assert result["compliant"]
    
    def test_stopping_sight_distance_increases_with_speed(self):
        """Test that SSD increases with design speed."""
        result_30 = self.calculator.calculate_stopping_sight_distance(design_speed=30)
        result_50 = self.calculator.calculate_stopping_sight_distance(design_speed=50)
        result_70 = self.calculator.calculate_stopping_sight_distance(design_speed=70)
        
        assert result_70["stopping_sight_distance"] > result_50["stopping_sight_distance"] > result_30["stopping_sight_distance"]
    
    # Error Handling Tests
    
    def test_invalid_design_speed(self):
        """Test that invalid design speed raises error."""
        with pytest.raises(ValueError) as exc_info:
            self.calculator.calculate_minimum_radius(design_speed=200)
        assert "validation failed" in str(exc_info.value).lower()
    
    def test_closest_speed_matching(self):
        """Test that calculator uses closest speed if exact match not available."""
        # 65 mph not in standards, should use closest
        result = self.calculator.calculate_minimum_radius(design_speed=65)
        
        # Should use 60 or 70 mph standard
        assert result["design_speed"] in [60, 70]
        assert result["minimum_radius"] > 0
        assert result["compliant"]
