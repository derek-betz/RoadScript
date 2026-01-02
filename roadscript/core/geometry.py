"""
Geometry Calculator Module

Calculates geometric design parameters including minimum horizontal curve radius,
vertical curve length, stopping sight distance, and superelevation.
"""

from typing import Dict, List, Any
from roadscript.standards.loader import StandardsLoader
from roadscript.validation.validators import InputValidator, ComplianceChecker
from roadscript.logging.audit import get_audit_logger
from roadscript.exceptions import StandardInterpolationRequiredError


class GeometryCalculator:
    """
    Calculates IDM-compliant geometric design parameters.
    
    Provides calculations for horizontal curves, vertical curves,
    stopping sight distance, and other geometric elements.
    """
    
    def __init__(self):
        """Initialize the geometry calculator."""
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
    
    def calculate_minimum_radius(self, design_speed: int) -> Dict[str, Any]:
        """
        Calculate minimum horizontal curve radius for a given design speed.
        
        Args:
            design_speed: Design speed in mph
            
        Returns:
            Dictionary containing:
                - minimum_radius: Minimum curve radius in feet
                - design_speed: Design speed used
                - superelevation_max: Maximum superelevation rate
                - friction_factor: Side friction factor
                - compliant: Whether result meets IDM standards
                - warnings: List of any compliance warnings
                
        Raises:
            ValueError: If inputs fail validation
            StandardInterpolationRequiredError: If design speed is not in IDM standards
        """
        # Prepare inputs
        inputs = {"design_speed": design_speed}
        
        # Validate inputs
        is_valid, errors = self.validator.validate_geometry_inputs(inputs)
        if not is_valid:
            error_msg = "; ".join(errors)
            self.logger.log_error(
                "VALIDATION_ERROR",
                error_msg,
                {"inputs": inputs}
            )
            raise ValueError(f"Input validation failed: {error_msg}")
        
        # Get standards
        geom_standards = self.standards.get_geometry_standards()
        curve_standards = geom_standards["horizontal_curves"]["minimum_radius"]
        
        # Get parameters
        speed_key = str(design_speed)
        radius_table = curve_standards["design_speed_radius"]
        
        # Find radius (exact match required)
        if speed_key not in radius_table:
            available_speeds: List[int] = sorted(int(speed) for speed in radius_table.keys())
            raise StandardInterpolationRequiredError(
                "Design speed "
                f"{design_speed} mph not found in IDM geometry standards. "
                f"Available speeds: {available_speeds}"
            )
        
        minimum_radius = radius_table[speed_key]
        e_max = curve_standards["superelevation_max"]
        friction_factors = curve_standards["friction_factor"]
        friction_factor = friction_factors.get(speed_key, 0.12)
        
        # Prepare results
        calculated_values = {"minimum_radius": minimum_radius}
        
        # Check compliance
        is_compliant, warnings = self.compliance.check_geometry_compliance(
            inputs,
            calculated_values
        )
        
        results = {
            "minimum_radius": minimum_radius,
            "design_speed": int(speed_key),
            "superelevation_max": e_max,
            "friction_factor": friction_factor,
            "compliant": is_compliant,
            "warnings": warnings,
            "units": "feet",
            "standards_version": self.standards.get_metadata().get("version")
        }
        
        # Log calculation
        status = "SUCCESS" if is_compliant else "WARNING"
        self.logger.log_calculation(
            "minimum_radius",
            inputs,
            results,
            self.standards.get_metadata().get("version", "unknown"),
            status
        )
        
        return results
    
    def calculate_vertical_curve_length(
        self,
        design_speed: int,
        grade_difference: float,
        curve_type: str = "crest"
    ) -> Dict[str, Any]:
        """
        Calculate minimum vertical curve length per IDM 43-4.0.
        
        Args:
            design_speed: Design speed in mph
            grade_difference: Algebraic difference in grades (percent)
            curve_type: Type of curve ("crest" or "sag")
            
        Returns:
            Dictionary containing:
                - curve_length: Minimum curve length in feet
                - k_value: Rate of vertical curvature
                - design_speed: Design speed used
                - grade_difference: Grade difference used
                - curve_type: Type of curve
                - compliant: Whether result meets IDM standards
                - warnings: List of any compliance warnings
                
        Raises:
            ValueError: If inputs fail validation
            StandardInterpolationRequiredError: If design speed is not in IDM 43-4.0 K-values
        """
        # Prepare inputs
        inputs = {
            "design_speed": design_speed,
            "grade": abs(grade_difference),
            "curve_type": curve_type
        }
        
        # Validate inputs
        is_valid, errors = self.validator.validate_geometry_inputs(inputs)
        if not is_valid:
            error_msg = "; ".join(errors)
            self.logger.log_error(
                "VALIDATION_ERROR",
                error_msg,
                {"inputs": inputs}
            )
            raise ValueError(f"Input validation failed: {error_msg}")
        
        # Get standards
        geom_standards = self.standards.get_geometry_standards()
        vert_curve_standards = geom_standards["vertical_curves"]["minimum_length"]
        
        # Get K value
        speed_key = str(design_speed)
        if curve_type == "crest":
            k_values = vert_curve_standards["crest_curves"]["K_values"]
        else:
            k_values = vert_curve_standards["sag_curves"]["K_values"]
        
        # Find K value (exact match required)
        if speed_key not in k_values:
            available_speeds: List[int] = sorted(int(speed) for speed in k_values.keys())
            raise StandardInterpolationRequiredError(
                "Design speed "
                f"{design_speed} mph not found in IDM 43-4.0 K-values. "
                f"Available speeds: {available_speeds}"
            )
        
        k_value = k_values[speed_key]
        
        # Calculate curve length: L = K * A
        curve_length = k_value * abs(grade_difference)
        curve_length = round(curve_length, 1)
        
        # Prepare results
        calculated_values = {"curve_length": curve_length}
        
        # Check compliance
        is_compliant, warnings = self.compliance.check_geometry_compliance(
            inputs,
            calculated_values
        )
        
        results = {
            "curve_length": curve_length,
            "k_value": k_value,
            "design_speed": int(speed_key),
            "grade_difference": abs(grade_difference),
            "curve_type": curve_type,
            "compliant": is_compliant,
            "warnings": warnings,
            "units": "feet",
            "standards_version": self.standards.get_metadata().get("version")
        }
        
        # Log calculation
        status = "SUCCESS" if is_compliant else "WARNING"
        self.logger.log_calculation(
            "vertical_curve_length",
            inputs,
            results,
            self.standards.get_metadata().get("version", "unknown"),
            status
        )
        
        return results
    
    def calculate_stopping_sight_distance(self, design_speed: int) -> Dict[str, Any]:
        """
        Calculate stopping sight distance per IDM 43-4.0.
        
        Args:
            design_speed: Design speed in mph
            
        Returns:
            Dictionary containing:
                - stopping_sight_distance: SSD in feet
                - design_speed: Design speed used
                - compliant: Whether result meets IDM standards
                - warnings: List of any compliance warnings
                
        Raises:
            ValueError: If inputs fail validation
            StandardInterpolationRequiredError: If design speed is not in IDM SSD standards
        """
        # Prepare inputs
        inputs = {"design_speed": design_speed}
        
        # Validate inputs
        is_valid, errors = self.validator.validate_geometry_inputs(inputs)
        if not is_valid:
            error_msg = "; ".join(errors)
            self.logger.log_error(
                "VALIDATION_ERROR",
                error_msg,
                {"inputs": inputs}
            )
            raise ValueError(f"Input validation failed: {error_msg}")
        
        # Get standards
        geom_standards = self.standards.get_geometry_standards()
        ssd_table = geom_standards["vertical_curves"]["stopping_sight_distance"]["design_speed_ssd"]
        
        # Get SSD
        speed_key = str(design_speed)
        if speed_key not in ssd_table:
            available_speeds: List[int] = sorted(int(speed) for speed in ssd_table.keys())
            raise StandardInterpolationRequiredError(
                "Design speed "
                f"{design_speed} mph not found in IDM SSD standards. "
                f"Available speeds: {available_speeds}"
            )
        
        ssd = ssd_table[speed_key]
        
        # Prepare results
        calculated_values = {"stopping_sight_distance": ssd}
        
        # Check compliance
        is_compliant, warnings = self.compliance.check_geometry_compliance(
            inputs,
            calculated_values
        )
        
        results = {
            "stopping_sight_distance": ssd,
            "design_speed": int(speed_key),
            "compliant": is_compliant,
            "warnings": warnings,
            "units": "feet",
            "standards_version": self.standards.get_metadata().get("version")
        }
        
        # Log calculation
        status = "SUCCESS" if is_compliant else "WARNING"
        self.logger.log_calculation(
            "stopping_sight_distance",
            inputs,
            results,
            self.standards.get_metadata().get("version", "unknown"),
            status
        )
        
        return results
