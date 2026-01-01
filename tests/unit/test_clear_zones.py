"""
Unit tests for Clear Zone Calculator

Tests IDM-compliant clear zone width calculations.
"""

import pytest
from roadscript.core.clear_zones import ClearZoneCalculator


class TestClearZoneCalculator:
    """Test suite for ClearZoneCalculator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = ClearZoneCalculator()
    
    def test_clear_zone_low_volume(self):
        """Test clear zone calculation for low traffic volume."""
        result = self.calculator.calculate(
            design_speed=60,
            adt=300,  # 0-500 ADT
            slope_category="fill_slope_6_1_or_flatter"
        )
        
        assert result["width"] == 16
        assert result["adt_category"] == "0-500"
        assert result["compliant"]
        assert result["units"] == "feet"
    
    def test_clear_zone_medium_volume(self):
        """Test clear zone calculation for medium traffic volume."""
        result = self.calculator.calculate(
            design_speed=60,
            adt=1000,  # 501-1500 ADT
            slope_category="fill_slope_6_1_or_flatter"
        )
        
        assert result["width"] == 20
        assert result["adt_category"] == "501-1500"
        assert result["compliant"]
    
    def test_clear_zone_high_volume(self):
        """Test clear zone calculation for high traffic volume."""
        result = self.calculator.calculate(
            design_speed=60,
            adt=5000,  # 1501-6000 ADT
            slope_category="fill_slope_6_1_or_flatter"
        )
        
        assert result["width"] == 26
        assert result["adt_category"] == "1501-6000"
        assert result["compliant"]
    
    def test_clear_zone_very_high_volume(self):
        """Test clear zone calculation for very high traffic volume."""
        result = self.calculator.calculate(
            design_speed=60,
            adt=8000,  # 6000+ ADT
            slope_category="fill_slope_6_1_or_flatter"
        )
        
        assert result["width"] == 32
        assert result["adt_category"] == "6000+"
        assert result["compliant"]
    
    def test_clear_zone_steeper_slope(self):
        """Test clear zone with steeper slope requires more width."""
        result = self.calculator.calculate(
            design_speed=60,
            adt=5000,
            slope_category="fill_slope_3_1_or_steeper"
        )
        
        # Steeper slopes require wider clear zones
        assert result["width"] == 30
        assert result["slope_category"] == "fill_slope_3_1_or_steeper"
        assert result["compliant"]
    
    def test_clear_zone_different_speeds(self):
        """Test clear zone calculations at different design speeds."""
        # 30 mph
        result_30 = self.calculator.calculate(
            design_speed=30,
            adt=300,
            slope_category="fill_slope_6_1_or_flatter"
        )
        assert result_30["width"] == 7
        
        # 50 mph
        result_50 = self.calculator.calculate(
            design_speed=50,
            adt=300,
            slope_category="fill_slope_6_1_or_flatter"
        )
        assert result_50["width"] == 12
        
        # 70 mph
        result_70 = self.calculator.calculate(
            design_speed=70,
            adt=300,
            slope_category="fill_slope_6_1_or_flatter"
        )
        assert result_70["width"] == 20
        
        # Higher speeds require wider clear zones
        assert result_70["width"] > result_50["width"] > result_30["width"]
    
    def test_adt_category_determination(self):
        """Test ADT category determination."""
        # Test boundary conditions
        assert self.calculator._get_adt_category(500) == "0-500"
        assert self.calculator._get_adt_category(501) == "501-1500"
        assert self.calculator._get_adt_category(1500) == "501-1500"
        assert self.calculator._get_adt_category(1501) == "1501-6000"
        assert self.calculator._get_adt_category(6000) == "1501-6000"
        assert self.calculator._get_adt_category(6001) == "6000+"
    
    def test_invalid_design_speed(self):
        """Test that invalid design speed raises error."""
        with pytest.raises(ValueError) as exc_info:
            self.calculator.calculate(
                design_speed=20,  # Too low
                adt=1000,
                slope_category="fill_slope_6_1_or_flatter"
            )
        assert "validation failed" in str(exc_info.value).lower()
    
    def test_invalid_slope_category(self):
        """Test that invalid slope category raises error."""
        with pytest.raises(ValueError) as exc_info:
            self.calculator.calculate(
                design_speed=60,
                adt=1000,
                slope_category="invalid_slope"
            )
        assert "validation failed" in str(exc_info.value).lower()
    
    def test_negative_adt(self):
        """Test that negative ADT raises error."""
        with pytest.raises(ValueError) as exc_info:
            self.calculator.calculate(
                design_speed=60,
                adt=-100,
                slope_category="fill_slope_6_1_or_flatter"
            )
        assert "validation failed" in str(exc_info.value).lower()
    
    def test_closest_speed_matching(self):
        """Test that calculator uses closest speed if exact match not available."""
        # 65 mph not in clear zone standards, should use 60 or 70
        result = self.calculator.calculate(
            design_speed=65,
            adt=1000,
            slope_category="fill_slope_6_1_or_flatter"
        )
        
        # Should use closest speed
        assert result["design_speed"] in [60, 70]
        assert result["width"] > 0
        assert result["compliant"]
