"""
Clear Zone Calculator Module

Calculates clear zone widths based on IDM standards for design speed,
traffic volume (ADT), and roadside slope characteristics.
"""

from typing import Dict, List, Any
from roadscript.standards.loader import StandardsLoader
from roadscript.validation.validators import InputValidator, ComplianceChecker
from roadscript.logging.audit import get_audit_logger
from roadscript.exceptions import StandardInterpolationRequiredError


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
        Determine AADT category from traffic volume per IDM 49-2.02.
        
        Args:
            adt: Average Daily Traffic count
            
        Returns:
            ADT category string
        """
        if adt < 750:
            return "<750"
        if adt < 1500:
            return "750-1500"
        if adt <= 6000:
            return "1500-6000"
        return ">6000"
    
    def calculate(
        self,
        design_speed: int,
        adt: int,
        slope_position: str,
        slope_category: str
    ) -> Dict[str, Any]:
        """
        Calculate clear zone width per IDM 49-2.02 standards.
        
        Args:
            design_speed: Design speed in mph (must be 30, 40, 45, 50, 55, 60, 65, or 70)
            adt: Average Daily Traffic (vehicles per day)
            slope_position: Slope position ("foreslope" or "backslope")
            slope_category: Slope category (e.g., 6_1_or_flatter, 5_1_or_4_1, 3_1)
            
        Returns:
            Dictionary containing:
                - min_width: Minimum clear zone width in feet
                - max_width: Maximum clear zone width in feet
                - asterisk: Whether the table entry carries an IDM asterisk note
                - design_speed: Design speed used
                - adt_category: ADT category used
                - slope_position: Slope position used
                - slope_category: Slope category used
                - compliant: Whether result meets IDM standards
                - warnings: List of any compliance warnings
                
        Raises:
            ValueError: If inputs fail validation
            StandardInterpolationRequiredError: If design speed is not in IDM 49-2.02
        """
        # Prepare inputs
        inputs = {
            "design_speed": design_speed,
            "adt": adt,
            "slope_position": slope_position,
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
        speed_key = str(design_speed)
        if speed_key not in speed_based:
            available_speeds: List[int] = sorted(int(speed) for speed in speed_based.keys())
            raise StandardInterpolationRequiredError(
                "Design speed "
                f"{design_speed} mph not found in IDM 49-2.02 table. "
                f"Available speeds: {available_speeds}"
            )
        
        speed_data = speed_based.get(speed_key, {})
        aadt_ranges = speed_data.get("aadt_ranges", {})
        aadt_data = aadt_ranges.get(adt_category, {})
        slope_key = "foreslopes" if slope_position == "foreslope" else "backslopes"
        slope_data = aadt_data.get(slope_key, {})
        width_range = slope_data.get(slope_category)

        if width_range is None:
            raise ValueError(
                f"Could not find clear zone width for design_speed={design_speed}, "
                f"slope_position={slope_position}, slope_category={slope_category}, "
                f"adt_category={adt_category}"
            )
        
        # Check compliance
        is_compliant, warnings = self.compliance.check_clear_zone_compliance(
            inputs,
            width_range
        )
        
        # Prepare results
        results = {
            "min_width": width_range.get("min"),
            "max_width": width_range.get("max"),
            "asterisk": width_range.get("asterisk", False),
            "design_speed": int(speed_key),
            "adt": adt,
            "adt_category": adt_category,
            "slope_position": slope_position,
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
