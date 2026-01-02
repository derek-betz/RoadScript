"""
Core Engineering Functions

Pure, type-hinted functions for deterministic IDM calculations.
"""

from typing import Dict, List, Any

from roadscript.exceptions import StandardInterpolationRequiredError
from roadscript.standards.loader import StandardsLoader


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
    slope_category: str
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

    clear_zone_standards: Dict[str, Any] = StandardsLoader().get_clear_zone_standards()
    speed_based: Dict[str, Any] = clear_zone_standards.get("standards", {}).get(
        "design_speed_based", {}
    )
    speed_key = str(design_speed)
    if speed_key not in speed_based:
        available_speeds: List[int] = sorted(int(speed) for speed in speed_based.keys())
        raise StandardInterpolationRequiredError(
            "Design speed "
            f"{design_speed} mph not found in IDM 49-2.02 table. "
            f"Available speeds: {available_speeds}"
        )

    if adt < 750:
        adt_category = "<750"
    elif adt < 1500:
        adt_category = "750-1500"
    elif adt <= 6000:
        adt_category = "1500-6000"
    else:
        adt_category = ">6000"

    speed_data = speed_based[speed_key]
    aadt_ranges = speed_data.get("aadt_ranges", {})
    aadt_data = aadt_ranges.get(adt_category, {})
    slope_key = "foreslopes" if slope_position == "foreslope" else "backslopes"
    slope_data: Dict[str, Any] = aadt_data.get(slope_key, {})
    width_range = slope_data.get(slope_category)
    if width_range is None:
        raise ValueError(
            "Clear zone width not found for IDM 49-2.02 inputs: "
            f"design_speed={design_speed}, adt_category={adt_category}, "
            f"slope_position={slope_position}, slope_category={slope_category}"
        )

    return width_range
