"""
RoadScript - Deterministic Engineering Core for INDOT Roadway Design

A modular, testable Python engine that centralizes IDM-compliant math
for clear zones and geometry calculations. Designed for
legal defensibility and professional "Standard of Care" in commercial
AI design applications.
"""

__version__ = "1.0.0"
__author__ = "INDOT Engineering Core Team"

from roadscript.core.clear_zones import ClearZoneCalculator
from roadscript.core.engine import calculate_k_value, evaluate_clear_zone_requirement
from roadscript.core.geometry import GeometryCalculator
from roadscript.exceptions import StandardInterpolationRequiredError
from roadscript.validation.validators import InputValidator, ComplianceChecker
from roadscript.standards.loader import StandardsLoader
from roadscript.validators.base import ValidationResult, validate_vertical_curve_k

__all__ = [
    "ClearZoneCalculator",
    "calculate_k_value",
    "evaluate_clear_zone_requirement",
    "GeometryCalculator",
    "StandardInterpolationRequiredError",
    "InputValidator",
    "ComplianceChecker",
    "StandardsLoader",
    "ValidationResult",
    "validate_vertical_curve_k",
]
