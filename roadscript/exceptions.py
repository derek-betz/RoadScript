"""Custom exceptions for RoadScript standards enforcement."""


class StandardInterpolationRequiredError(ValueError):
    """Raised when IDM standards require interpolation for a missing design speed."""
