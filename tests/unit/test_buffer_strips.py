"""
Unit tests for Buffer Strip Calculator

Tests IDM-compliant buffer strip width calculations.
"""

import pytest
from roadscript.core.buffer_strips import BufferStripCalculator


class TestBufferStripCalculator:
    """Test suite for BufferStripCalculator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = BufferStripCalculator()
    
    def test_interstate_buffer_strip(self):
        """Test buffer strip calculation for interstate highway."""
        result = self.calculator.calculate(
            road_classification="interstate",
            design_speed=65,
            terrain="flat",
            traffic_volume="medium"
        )
        
        assert result["width"] == 40.0  # Base width for 65 mph interstate
        assert result["compliant"]
        assert result["units"] == "feet"
        assert "standards_version" in result
    
    def test_buffer_strip_with_terrain_adjustment(self):
        """Test buffer strip with terrain adjustment factor."""
        result = self.calculator.calculate(
            road_classification="interstate",
            design_speed=65,
            terrain="rolling",
            traffic_volume="medium"
        )
        
        # Rolling terrain has 1.15 factor
        assert result["width"] == 46.0  # 40 * 1.15
        assert result["terrain_factor"] == 1.15
        assert result["compliant"]
    
    def test_buffer_strip_with_traffic_adjustment(self):
        """Test buffer strip with traffic volume adjustment."""
        result = self.calculator.calculate(
            road_classification="interstate",
            design_speed=65,
            terrain="flat",
            traffic_volume="high"
        )
        
        # High traffic has 1.1 factor
        assert result["width"] == 44.0  # 40 * 1.1
        assert result["traffic_factor"] == 1.1
        assert result["compliant"]
    
    def test_buffer_strip_combined_adjustments(self):
        """Test buffer strip with both terrain and traffic adjustments."""
        result = self.calculator.calculate(
            road_classification="interstate",
            design_speed=65,
            terrain="mountainous",
            traffic_volume="high"
        )
        
        # Mountainous (1.3) + high traffic (1.1)
        assert result["width"] == 57.2  # 40 * 1.3 * 1.1
        assert result["terrain_factor"] == 1.3
        assert result["traffic_factor"] == 1.1
    
    def test_us_route_buffer_strip(self):
        """Test buffer strip calculation for US route."""
        result = self.calculator.calculate(
            road_classification="us_route",
            design_speed=55,
            terrain="flat",
            traffic_volume="medium"
        )
        
        assert result["width"] == 30.0
        assert result["compliant"]
    
    def test_state_highway_buffer_strip(self):
        """Test buffer strip calculation for state highway."""
        result = self.calculator.calculate(
            road_classification="state_highway",
            design_speed=45,
            terrain="flat",
            traffic_volume="medium"
        )
        
        assert result["width"] == 25.0
        assert result["compliant"]
    
    def test_local_road_buffer_strip(self):
        """Test buffer strip calculation for local road."""
        result = self.calculator.calculate(
            road_classification="local_road",
            design_speed=35,
            terrain="flat",
            traffic_volume="medium"
        )
        
        assert result["width"] == 15.0
        assert result["compliant"]
    
    def test_invalid_road_classification(self):
        """Test that invalid road classification raises error."""
        with pytest.raises(ValueError) as exc_info:
            self.calculator.calculate(
                road_classification="invalid_type",
                design_speed=65,
                terrain="flat",
                traffic_volume="medium"
            )
        assert "validation failed" in str(exc_info.value).lower()
    
    def test_invalid_terrain(self):
        """Test that invalid terrain raises error."""
        with pytest.raises(ValueError) as exc_info:
            self.calculator.calculate(
                road_classification="interstate",
                design_speed=65,
                terrain="invalid_terrain",
                traffic_volume="medium"
            )
        assert "validation failed" in str(exc_info.value).lower()
    
    def test_out_of_range_speed(self):
        """Test that out-of-range speed raises error."""
        with pytest.raises(ValueError) as exc_info:
            self.calculator.calculate(
                road_classification="interstate",
                design_speed=150,
                terrain="flat",
                traffic_volume="medium"
            )
        assert "validation failed" in str(exc_info.value).lower()
    
    def test_closest_speed_matching(self):
        """Test that calculator uses closest speed if exact match not available."""
        # 63 mph not in standards, should use 65 mph
        result = self.calculator.calculate(
            road_classification="interstate",
            design_speed=63,
            terrain="flat",
            traffic_volume="medium"
        )
        
        # Should use 65 mph standard (40 ft)
        assert result["width"] == 40.0
        assert result["base_width"] == 40
