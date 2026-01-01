"""
Clear Zone Calculator Module

Calculates clear zone widths based on IDM standards for design speed,
traffic volume (ADT), and roadside slope characteristics.
"""

from typing import Dict, Any
from roadscript.standards.loader import StandardsLoader
from roadscript.validation.validators import InputValidator, ComplianceChecker
from roadscript.logging.audit import get_audit_logger


class ClearZoneCalculator:
    """
    Calculates IDM-compliant clear zone widths.
    
    Clear zones are unobstructed, traversable areas beyond the edge of the
    traveled way for recovery of errant vehicles.
    """
    
    def __init__(self):
        """Initialize the clear zone calculator."""
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
    
    def _get_adt_category(self, adt: int) -> str:
        """
        Determine ADT category from traffic volume.
        
        Args:
            adt: Average Daily Traffic count
            
        Returns:
            ADT category string
        """
        if adt <= 500:
            return "0-500"
        elif adt <= 1500:
            return "501-1500"
        elif adt <= 6000:
            return "1501-6000"
        else:
            return "6000+"
    
    def calculate(
        self,
        design_speed: int,
        adt: int,
        slope_category: str
    ) -> Dict[str, Any]:
        """
        Calculate clear zone width per IDM standards.
        
        Args:
            design_speed: Design speed in mph (must be 30, 40, 50, 60, or 70)
            adt: Average Daily Traffic (vehicles per day)
            slope_category: Slope category (fill_slope_6_1_or_flatter, 
                           fill_slope_5_1_to_4_1, fill_slope_3_1_or_steeper)
            
        Returns:
            Dictionary containing:
                - width: Clear zone width in feet
                - design_speed: Design speed used
                - adt_category: ADT category used
                - slope_category: Slope category used
                - compliant: Whether result meets IDM standards
                - warnings: List of any compliance warnings
                
        Raises:
            ValueError: If inputs fail validation
        """
        # Prepare inputs
        inputs = {
            "design_speed": design_speed,
            "adt": adt,
            "slope_category": slope_category
        }
        
        # Validate inputs
        is_valid, errors = self.validator.validate_clear_zone_inputs(inputs)
        if not is_valid:
            error_msg = "; ".join(errors)
            self.logger.log_error(
                "VALIDATION_ERROR",
                error_msg,
                {"inputs": inputs}
            )
            raise ValueError(f"Input validation failed: {error_msg}")
        
        # Get standards
        clear_zone_standards = self.standards.get_clear_zone_standards()
        speed_based = clear_zone_standards["standards"]["design_speed_based"]
        
        # Determine ADT category
        adt_category = self._get_adt_category(adt)
        
        # Get clear zone width from standards
        # Use closest design speed if exact match not found
        speed_key = str(design_speed)
        if speed_key not in speed_based:
            available_speeds = sorted([int(s) for s in speed_based.keys()])
            closest_speed = min(available_speeds, key=lambda x: abs(x - design_speed))
            speed_key = str(closest_speed)
        
        speed_data = speed_based.get(speed_key, {})
        slope_data = speed_data.get(slope_category, {})
        clear_zone_width = slope_data.get(adt_category)
        
        if clear_zone_width is None:
            raise ValueError(
                f"Could not find clear zone width for design_speed={design_speed}, "
                f"slope_category={slope_category}, adt_category={adt_category}"
            )
        
        # Check compliance
        is_compliant, warnings = self.compliance.check_clear_zone_compliance(
            inputs,
            clear_zone_width
        )
        
        # Prepare results
        results = {
            "width": clear_zone_width,
            "design_speed": int(speed_key),
            "adt": adt,
            "adt_category": adt_category,
            "slope_category": slope_category,
            "compliant": is_compliant,
            "warnings": warnings,
            "units": "feet",
            "standards_version": self.standards.get_metadata().get("version")
        }
        
        # Log calculation
        status = "SUCCESS" if is_compliant else "WARNING"
        self.logger.log_calculation(
            "clear_zone",
            inputs,
            results,
            self.standards.get_metadata().get("version", "unknown"),
            status
        )
        
        return results
