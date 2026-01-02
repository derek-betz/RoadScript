"""
Validator Base Module

Provides IDM-compliant validation results for deterministic checks.
"""

from dataclasses import dataclass
from typing import Dict, List, Any

from roadscript.core.engine import calculate_k_value
from roadscript.exceptions import StandardInterpolationRequiredError
from roadscript.standards.loader import StandardsLoader
from roadscript.utils.audit import log_validation_result


@dataclass(frozen=True)
class ValidationResult:
    """
    IDM 43-4.0 validation result for vertical curve K-values.

    Attributes:
        status: True if compliant, False otherwise
        message: Human-readable explanation
        idm_reference: IDM section reference
        actual_k: Calculated K-value
        required_k: Minimum required K-value
    """
    status: bool
    message: str
    idm_reference: str
    actual_k: float
    required_k: float


def validate_vertical_curve_k(
    design_speed: int,
    curve_type: str,
    length_of_curve: float,
    algebraic_diff: float
) -> ValidationResult:
    """
    Validate vertical curve K-values against IDM 43-4.0 minimums.

    Args:
        design_speed: Design speed in mph
        curve_type: "crest" or "sag"
        length_of_curve: Vertical curve length (L) in feet
        algebraic_diff: Algebraic difference in grades (A) in percent

    Returns:
        ValidationResult with compliance status and IDM 43-4.0 reference
    """
    curve_type_normalized = curve_type.lower().strip()
    if curve_type_normalized not in {"crest", "sag"}:
        raise ValueError("curve_type must be 'crest' or 'sag' for IDM 43-4.0.")

    geometry_standards: Dict[str, Any] = StandardsLoader().get_geometry_standards()
    minimum_length = geometry_standards.get("vertical_curves", {}).get("minimum_length", {})
    if curve_type_normalized == "crest":
        k_values = minimum_length.get("crest_curves", {}).get("K_values", {})
    else:
        k_values = minimum_length.get("sag_curves", {}).get("K_values", {})

    speed_key = str(design_speed)
    if speed_key not in k_values:
        available_speeds: List[int] = sorted(int(speed) for speed in k_values.keys())
        raise StandardInterpolationRequiredError(
            "Design speed "
            f"{design_speed} mph not found in IDM 43-4.0 K-values. "
            f"Available speeds: {available_speeds}"
        )

    required_k = float(k_values[speed_key])
    actual_k = calculate_k_value(length_of_curve, algebraic_diff)
    status = actual_k >= required_k

    if status:
        message = (
            "IDM 43-4.0 satisfied: "
            f"actual K {actual_k:.2f} >= required K {required_k:.2f}."
        )
    else:
        message = (
            "IDM 43-4.0 requires K >= "
            f"{required_k:.2f}; actual K is {actual_k:.2f}."
        )

    result = ValidationResult(
        status=status,
        message=message,
        idm_reference="IDM 43-4.0",
        actual_k=actual_k,
        required_k=required_k
    )

    metadata = StandardsLoader().get_metadata()
    revision_tag = metadata.get("revision_tag", "IDM_2024_v1")
    log_validation_result(result, revision_tag)

    return result
