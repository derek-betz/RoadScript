"""
RoadScript - Deterministic Engineering Core for INDOT Roadway Design

A modular, testable Python engine that centralizes IDM-compliant math
for buffer strips, clear zones, and geometry calculations. Designed for
legal defensibility and professional "Standard of Care" in commercial
AI design applications.
"""

__version__ = "1.0.0"
__author__ = "INDOT Engineering Core Team"

from roadscript.core.buffer_strips import BufferStripCalculator
from roadscript.core.clear_zones import ClearZoneCalculator
from roadscript.core.geometry import GeometryCalculator
from roadscript.validation.validators import InputValidator, ComplianceChecker
from roadscript.standards.loader import StandardsLoader

__all__ = [
    "BufferStripCalculator",
    "ClearZoneCalculator",
    "GeometryCalculator",
    "InputValidator",
    "ComplianceChecker",
    "StandardsLoader",
]
