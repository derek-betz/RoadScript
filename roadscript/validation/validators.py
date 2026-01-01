"""
Validation Module

Provides input validation and compliance checking for all calculations.
Ensures data integrity and IDM standard compliance.
"""

from typing import Dict, Any, List, Tuple
from roadscript.standards.loader import StandardsLoader
from roadscript.logging.audit import get_audit_logger


class ValidationError(Exception):
    """Exception raised for validation failures."""
    pass


class InputValidator:
    """
    Validates input parameters for calculations.
    
    Ensures all required fields are present and values are within
    acceptable ranges per IDM standards.
    """
    
    def __init__(self):
        """Initialize the input validator."""
        self.standards = StandardsLoader()
        self.logger = get_audit_logger()
    
    def validate_buffer_strip_inputs(self, inputs: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate inputs for buffer strip calculations.
        
        Args:
            inputs: Dictionary containing input parameters
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        rules = self.standards.get_validation_rules().get("buffer_strips", {})
        errors = []
        
        # Check required fields
        required = rules.get("required_fields", [])
        for field in required:
            if field not in inputs:
                errors.append(f"Missing required field: {field}")
        
        # Validate road classification
        if "road_classification" in inputs:
            valid_classifications = rules.get("valid_classifications", [])
            if inputs["road_classification"] not in valid_classifications:
                errors.append(
                    f"Invalid road_classification: {inputs['road_classification']}. "
                    f"Must be one of: {', '.join(valid_classifications)}"
                )
        
        # Validate terrain
        if "terrain" in inputs:
            valid_terrains = rules.get("valid_terrains", [])
            if inputs["terrain"] not in valid_terrains:
                errors.append(
                    f"Invalid terrain: {inputs['terrain']}. "
                    f"Must be one of: {', '.join(valid_terrains)}"
                )
        
        # Validate design speed
        if "design_speed" in inputs:
            speed_range = rules.get("design_speed_range", [0, 100])
            speed = inputs["design_speed"]
            if not (speed_range[0] <= speed <= speed_range[1]):
                errors.append(
                    f"Design speed {speed} mph is outside valid range "
                    f"({speed_range[0]}-{speed_range[1]} mph)"
                )
        
        is_valid = len(errors) == 0
        status = "PASS" if is_valid else "FAIL"
        
        self.logger.log_validation(
            "buffer_strip_inputs",
            inputs,
            {"errors": errors},
            status
        )
        
        return is_valid, errors
    
    def validate_clear_zone_inputs(self, inputs: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate inputs for clear zone calculations.
        
        Args:
            inputs: Dictionary containing input parameters
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        rules = self.standards.get_validation_rules().get("clear_zones", {})
        errors = []
        
        # Check required fields
        required = rules.get("required_fields", [])
        for field in required:
            if field not in inputs:
                errors.append(f"Missing required field: {field}")
        
        # Validate design speed
        if "design_speed" in inputs:
            speed_range = rules.get("design_speed_range", [0, 100])
            speed = inputs["design_speed"]
            if not (speed_range[0] <= speed <= speed_range[1]):
                errors.append(
                    f"Design speed {speed} mph is outside valid range "
                    f"({speed_range[0]}-{speed_range[1]} mph)"
                )
        
        # Validate slope category
        if "slope_category" in inputs:
            valid_slopes = rules.get("valid_slope_categories", [])
            if inputs["slope_category"] not in valid_slopes:
                errors.append(
                    f"Invalid slope_category: {inputs['slope_category']}. "
                    f"Must be one of: {', '.join(valid_slopes)}"
                )
        
        # Validate ADT
        if "adt" in inputs:
            adt = inputs["adt"]
            if not isinstance(adt, (int, float)) or adt < 0:
                errors.append(f"ADT must be a non-negative number, got: {adt}")
        
        is_valid = len(errors) == 0
        status = "PASS" if is_valid else "FAIL"
        
        self.logger.log_validation(
            "clear_zone_inputs",
            inputs,
            {"errors": errors},
            status
        )
        
        return is_valid, errors
    
    def validate_geometry_inputs(self, inputs: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate inputs for geometry calculations.
        
        Args:
            inputs: Dictionary containing input parameters
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        rules = self.standards.get_validation_rules().get("geometry", {})
        errors = []
        
        # Check required fields
        required = rules.get("required_fields", [])
        for field in required:
            if field not in inputs:
                errors.append(f"Missing required field: {field}")
        
        # Validate design speed
        if "design_speed" in inputs:
            speed_range = rules.get("design_speed_range", [0, 100])
            speed = inputs["design_speed"]
            if not (speed_range[0] <= speed <= speed_range[1]):
                errors.append(
                    f"Design speed {speed} mph is outside valid range "
                    f"({speed_range[0]}-{speed_range[1]} mph)"
                )
        
        # Validate grade if present
        if "grade" in inputs:
            grade_range = rules.get("grade_range", [-15, 15])
            grade = inputs["grade"]
            if not (grade_range[0] <= grade <= grade_range[1]):
                errors.append(
                    f"Grade {grade}% is outside valid range "
                    f"({grade_range[0]}-{grade_range[1]}%)"
                )
        
        is_valid = len(errors) == 0
        status = "PASS" if is_valid else "FAIL"
        
        self.logger.log_validation(
            "geometry_inputs",
            inputs,
            {"errors": errors},
            status
        )
        
        return is_valid, errors


class ComplianceChecker:
    """
    Checks calculation results for IDM compliance.
    
    Verifies that calculated values meet or exceed minimum standards
    and fall within acceptable ranges.
    """
    
    def __init__(self):
        """Initialize the compliance checker."""
        self.standards = StandardsLoader()
        self.logger = get_audit_logger()
    
    def check_buffer_strip_compliance(
        self,
        inputs: Dict[str, Any],
        calculated_width: float
    ) -> Tuple[bool, List[str]]:
        """
        Check if calculated buffer strip width meets IDM standards.
        
        Args:
            inputs: Input parameters used in calculation
            calculated_width: Calculated buffer strip width
            
        Returns:
            Tuple of (is_compliant, list of warnings/issues)
        """
        issues = []
        buffer_standards = self.standards.get_buffer_strip_standards()
        
        classification = inputs.get("road_classification")
        if classification:
            class_standards = buffer_standards.get("standards", {}).get(classification, {})
            min_width = class_standards.get("min_width", 0)
            max_width = class_standards.get("max_width", 999)
            
            if calculated_width < min_width:
                issues.append(
                    f"Calculated width {calculated_width} ft is below minimum "
                    f"standard of {min_width} ft for {classification}"
                )
            
            if calculated_width > max_width:
                issues.append(
                    f"Calculated width {calculated_width} ft exceeds maximum "
                    f"standard of {max_width} ft for {classification}"
                )
        
        is_compliant = len(issues) == 0
        status = "PASS" if is_compliant else "WARNING"
        
        self.logger.log_validation(
            "buffer_strip_compliance",
            {"inputs": inputs, "calculated_width": calculated_width},
            {"issues": issues},
            status
        )
        
        return is_compliant, issues
    
    def check_clear_zone_compliance(
        self,
        inputs: Dict[str, Any],
        calculated_width: float
    ) -> Tuple[bool, List[str]]:
        """
        Check if calculated clear zone width meets IDM standards.
        
        Args:
            inputs: Input parameters used in calculation
            calculated_width: Calculated clear zone width
            
        Returns:
            Tuple of (is_compliant, list of warnings/issues)
        """
        issues = []
        
        # Clear zones should always be positive
        if calculated_width <= 0:
            issues.append(f"Clear zone width must be positive, got: {calculated_width} ft")
        
        # Typical minimum clear zone is 7 feet
        if calculated_width < 7:
            issues.append(
                f"Calculated clear zone {calculated_width} ft is below "
                f"typical minimum of 7 ft"
            )
        
        is_compliant = len(issues) == 0
        status = "PASS" if is_compliant else "WARNING"
        
        self.logger.log_validation(
            "clear_zone_compliance",
            {"inputs": inputs, "calculated_width": calculated_width},
            {"issues": issues},
            status
        )
        
        return is_compliant, issues
    
    def check_geometry_compliance(
        self,
        inputs: Dict[str, Any],
        calculated_values: Dict[str, float]
    ) -> Tuple[bool, List[str]]:
        """
        Check if calculated geometry meets IDM standards.
        
        Args:
            inputs: Input parameters used in calculation
            calculated_values: Dictionary of calculated geometric values
            
        Returns:
            Tuple of (is_compliant, list of warnings/issues)
        """
        issues = []
        geom_standards = self.standards.get_geometry_standards()
        
        # Check minimum radius if present
        if "minimum_radius" in calculated_values:
            design_speed = inputs.get("design_speed")
            if design_speed:
                min_radius_standards = geom_standards.get("horizontal_curves", {}).get(
                    "minimum_radius", {}
                ).get("design_speed_radius", {})
                
                required_radius = min_radius_standards.get(str(design_speed))
                if required_radius:
                    calc_radius = calculated_values["minimum_radius"]
                    if calc_radius < required_radius:
                        issues.append(
                            f"Calculated radius {calc_radius} ft is below minimum "
                            f"standard of {required_radius} ft for {design_speed} mph"
                        )
        
        is_compliant = len(issues) == 0
        status = "PASS" if is_compliant else "WARNING"
        
        self.logger.log_validation(
            "geometry_compliance",
            {"inputs": inputs, "calculated_values": calculated_values},
            {"issues": issues},
            status
        )
        
        return is_compliant, issues
