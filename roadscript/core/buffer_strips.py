"""
Buffer Strip Calculator Module

Calculates buffer strip widths based on IDM standards for road classification,
design speed, terrain, and traffic volume.
"""

from typing import Dict, Any
from roadscript.standards.loader import StandardsLoader
from roadscript.validation.validators import InputValidator, ComplianceChecker
from roadscript.logging.audit import get_audit_logger


class BufferStripCalculator:
    """
    Calculates IDM-compliant buffer strip widths.
    
    Buffer strips are the areas between the roadway and adjacent features
    that provide safety, drainage, and maintenance space.
    """
    
    def __init__(self):
        """Initialize the buffer strip calculator."""
        self.standards = StandardsLoader()
        self.validator = InputValidator()
        self.compliance = ComplianceChecker()
        self.logger = get_audit_logger()
        
        # Log standards load
        metadata = self.standards.get_metadata()
        self.logger.log_standards_load(
            metadata.get("version", "unknown"),
            metadata
        )
    
    def calculate(
        self,
        road_classification: str,
        design_speed: int,
        terrain: str = "flat",
        traffic_volume: str = "medium"
    ) -> Dict[str, Any]:
        """
        Calculate buffer strip width per IDM standards.
        
        Args:
            road_classification: Type of road (interstate, us_route, state_highway, local_road)
            design_speed: Design speed in mph
            terrain: Terrain type (flat, rolling, mountainous)
            traffic_volume: Traffic volume level (low, medium, high)
            
        Returns:
            Dictionary containing:
                - width: Calculated buffer strip width in feet
                - base_width: Base width before adjustments
                - terrain_factor: Terrain adjustment factor
                - traffic_factor: Traffic volume adjustment factor
                - compliant: Whether result meets IDM standards
                - warnings: List of any compliance warnings
                
        Raises:
            ValidationError: If inputs fail validation
        """
        # Prepare inputs
        inputs = {
            "road_classification": road_classification,
            "design_speed": design_speed,
            "terrain": terrain,
            "traffic_volume": traffic_volume
        }
        
        # Validate inputs
        is_valid, errors = self.validator.validate_buffer_strip_inputs(inputs)
        if not is_valid:
            error_msg = "; ".join(errors)
            self.logger.log_error(
                "VALIDATION_ERROR",
                error_msg,
                {"inputs": inputs}
            )
            raise ValueError(f"Input validation failed: {error_msg}")
        
        # Get standards
        buffer_standards = self.standards.get_buffer_strip_standards()
        classification_standards = buffer_standards["standards"].get(road_classification, {})
        
        # Get base width from design speed
        speed_widths = classification_standards.get("design_speeds", {})
        base_width = speed_widths.get(str(design_speed))
        
        if base_width is None:
            # Find closest design speed
            available_speeds = sorted([int(s) for s in speed_widths.keys()])
            closest_speed = min(available_speeds, key=lambda x: abs(x - design_speed))
            base_width = speed_widths[str(closest_speed)]
        
        # Apply adjustment factors
        terrain_factors = buffer_standards["adjustment_factors"]["terrain"]
        traffic_factors = buffer_standards["adjustment_factors"]["traffic_volume"]
        
        terrain_factor = terrain_factors.get(terrain, 1.0)
        traffic_factor = traffic_factors.get(traffic_volume, 1.0)
        
        # Calculate final width
        calculated_width = base_width * terrain_factor * traffic_factor
        calculated_width = round(calculated_width, 1)
        
        # Check compliance
        is_compliant, warnings = self.compliance.check_buffer_strip_compliance(
            inputs,
            calculated_width
        )
        
        # Prepare results
        results = {
            "width": calculated_width,
            "base_width": base_width,
            "terrain_factor": terrain_factor,
            "traffic_factor": traffic_factor,
            "compliant": is_compliant,
            "warnings": warnings,
            "units": "feet",
            "standards_version": self.standards.get_metadata().get("version")
        }
        
        # Log calculation
        status = "SUCCESS" if is_compliant else "WARNING"
        self.logger.log_calculation(
            "buffer_strip",
            inputs,
            results,
            self.standards.get_metadata().get("version", "unknown"),
            status
        )
        
        return results
