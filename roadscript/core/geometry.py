"""
Geometry Calculator Module

Calculates geometric design parameters including minimum horizontal curve radius,
vertical curve length, stopping sight distance, and superelevation.
"""

from typing import Dict, List, Any, Optional
from roadscript.standards.loader import StandardsLoader
from roadscript.standards.service import StandardsService
from roadscript.validation.validators import InputValidator, ComplianceChecker
from roadscript.logging.audit import get_audit_logger


class GeometryCalculator:
    """
    Calculates IDM-compliant geometric design parameters.
    
    Provides calculations for horizontal curves, vertical curves,
    stopping sight distance, and other geometric elements.
    """
    
    def __init__(self, standards_service: Optional[StandardsService] = None):
        """Initialize the geometry calculator."""
        self.standards = StandardsLoader()
        self.standards_service = standards_service or StandardsService()
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

        # Resolve minimum radius (structured + optional RAG verification)
        standard_value = self.standards_service.get_minimum_radius(design_speed)
        minimum_radius = standard_value.value
        e_max = curve_standards["superelevation_max"]
        speed_key = str(design_speed)
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
            "standards_version": self.standards.get_metadata().get("version"),
            "verification": {
                "verified": standard_value.verified,
                "source": standard_value.source,
                "details": standard_value.verification,
                "citation": standard_value.citation,
            },
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
        
        # Resolve K value (structured + optional RAG verification)
        standard_value = self.standards_service.get_vertical_curve_k(design_speed, curve_type)
        k_value = standard_value.value
        speed_key = str(design_speed)
        
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
            "standards_version": self.standards.get_metadata().get("version"),
            "verification": {
                "verified": standard_value.verified,
                "source": standard_value.source,
                "details": standard_value.verification,
                "citation": standard_value.citation,
            },
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
        
        # Resolve SSD (structured + optional RAG verification)
        standard_value = self.standards_service.get_stopping_sight_distance(design_speed)
        ssd = standard_value.value
        speed_key = str(design_speed)
        
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
            "standards_version": self.standards.get_metadata().get("version"),
            "verification": {
                "verified": standard_value.verified,
                "source": standard_value.source,
                "details": standard_value.verification,
                "citation": standard_value.citation,
            },
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
