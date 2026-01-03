"""
Core Engineering Functions

Pure, type-hinted functions for deterministic IDM calculations.
"""

from typing import Dict, List, Any, Optional

from roadscript.standards.service import StandardsService


def calculate_k_value(length_of_curve: float, algebraic_diff: float) -> float:
    """
    Calculate vertical curve K-value using IDM 43-4.0 (K = L / A).

    Args:
        length_of_curve: Vertical curve length (L) in feet
        algebraic_diff: Algebraic difference in grades (A) in percent

    Returns:
        Calculated K-value (feet per percent)
    """
    if length_of_curve <= 0:
        raise ValueError("Length of curve must be positive for IDM 43-4.0.")
    if algebraic_diff == 0:
        raise ValueError("Algebraic difference must be non-zero for IDM 43-4.0.")

    return length_of_curve / abs(algebraic_diff)


def evaluate_clear_zone_requirement(
    design_speed: int,
    adt: int,
    slope_position: str,
    slope_category: str,
    standards_service: Optional[StandardsService] = None,
) -> Dict[str, Any]:
    """
    Fetch required clear zone width from IDM 49-2.02 standards data.

    Args:
        design_speed: Design speed in mph
        adt: Average Daily Traffic (vehicles per day)
        slope_position: Slope position ("foreslope" or "backslope")
        slope_category: Slope category key from IDM 49-2.02 clear zone tables

    Returns:
        Required clear zone width range in feet (min/max and optional flags)
    """
    if adt < 0:
        raise ValueError("ADT must be non-negative for IDM 49-2.02.")
    if slope_position not in {"foreslope", "backslope"}:
        raise ValueError("slope_position must be 'foreslope' or 'backslope' for IDM 49-2.02.")

    service = standards_service or StandardsService()
    standard_value = service.get_clear_zone_width(
        design_speed=design_speed,
        adt=adt,
        slope_position=slope_position,
        slope_category=slope_category,
    )
    return standard_value.value
