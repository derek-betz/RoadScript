# Example Usage

This document provides detailed examples of using RoadScript for clear zone and geometric design calculations.

## Complete Interstate Highway Design

```python
from roadscript import ClearZoneCalculator, GeometryCalculator

# Design parameters
design_speed = 70  # mph
adt = 12000  # vehicles per day

# Initialize calculators
clear_zone_calc = ClearZoneCalculator()
geom_calc = GeometryCalculator()

# Calculate clear zone
clear_zone_result = clear_zone_calc.calculate(
    design_speed=design_speed,
    adt=adt,
    slope_position="foreslope",
    slope_category="6_1_or_flatter"
)

print("Clear Zone Analysis:")
print(f"  Range: {clear_zone_result['min_width']}-{clear_zone_result['max_width']} feet")
print(f"  ADT Category: {clear_zone_result['adt_category']}")
print(f"  Compliant: {clear_zone_result['compliant']}")

# Calculate geometric parameters
radius_result = geom_calc.calculate_minimum_radius(design_speed=design_speed)
ssd_result = geom_calc.calculate_stopping_sight_distance(design_speed=design_speed)

print("\nGeometric Design:")
print(f"  Minimum Radius: {radius_result['minimum_radius']} feet")
print(f"  Stopping Sight Distance: {ssd_result['stopping_sight_distance']} feet")
print(f"  Superelevation Max: {radius_result['superelevation_max']}")
```

## Local Road Design

```python
from roadscript import ClearZoneCalculator, GeometryCalculator

# Local road parameters
design_speed = 40  # mph
adt = 500  # vehicles per day

clear_zone_calc = ClearZoneCalculator()
geom_calc = GeometryCalculator()

# Calculate clear zone (use 30 mph standard speed)
clear_zone_result = clear_zone_calc.calculate(
    design_speed=30,
    adt=adt,
    slope_position="foreslope",
    slope_category="6_1_or_flatter"
)

radius_result = geom_calc.calculate_minimum_radius(design_speed=design_speed)

print(f"Local Road Design (Speed: {design_speed} mph, ADT: {adt}):")
print(f"  Clear Zone: {clear_zone_result['min_width']}-{clear_zone_result['max_width']} feet")
print(f"  Minimum Radius: {radius_result['minimum_radius']} feet")
```

## Vertical Curve Design

```python
from roadscript import GeometryCalculator

calc = GeometryCalculator()

# Design parameters
design_speed = 60  # mph
grade_1 = 3.0  # percent
grade_2 = -2.0  # percent
grade_difference = abs(grade_1 - grade_2)  # 5.0%

# Calculate crest curve
crest_result = calc.calculate_vertical_curve_length(
    design_speed=design_speed,
    grade_difference=grade_difference,
    curve_type="crest"
)

print("Crest Vertical Curve:")
print(f"  Design Speed: {design_speed} mph")
print(f"  Grade Difference: {grade_difference}%")
print(f"  Minimum Length: {crest_result['curve_length']} feet")
print(f"  K Value: {crest_result['k_value']}")

# Calculate sag curve
sag_result = calc.calculate_vertical_curve_length(
    design_speed=design_speed,
    grade_difference=grade_difference,
    curve_type="sag"
)

print("\nSag Vertical Curve:")
print(f"  Minimum Length: {sag_result['curve_length']} feet")
print(f"  K Value: {sag_result['k_value']}")
```

## Validation and Error Handling

```python
from roadscript import ClearZoneCalculator, InputValidator

validator = InputValidator()
calculator = ClearZoneCalculator()

# Example 1: Valid inputs
inputs = {
    "design_speed": 60,
    "adt": 5000,
    "slope_position": "foreslope",
    "slope_category": "6_1_or_flatter"
}

is_valid, errors = validator.validate_clear_zone_inputs(inputs)
if is_valid:
    result = calculator.calculate(**inputs)
    print(f"Calculation successful: {result['min_width']}-{result['max_width']} feet")
else:
    print(f"Validation errors: {errors}")

# Example 2: Invalid inputs
try:
    result = calculator.calculate(
        design_speed=60,
        adt=5000,
        slope_position="foreslope",
        slope_category="invalid_slope"
    )
except ValueError as e:
    print(f"Calculation failed: {e}")
```

## Compliance Checking

```python
from roadscript import ClearZoneCalculator, ComplianceChecker

calculator = ClearZoneCalculator()
compliance = ComplianceChecker()

# Calculate clear zone
result = calculator.calculate(
    design_speed=60,
    adt=5000,
    slope_position="foreslope",
    slope_category="6_1_or_flatter"
)

# Check compliance
inputs = {
    "design_speed": 60,
    "adt": 5000,
    "slope_position": "foreslope",
    "slope_category": "6_1_or_flatter"
}

is_compliant, issues = compliance.check_clear_zone_compliance(
    inputs,
    {"min": result["min_width"], "max": result["max_width"]}
)

if is_compliant:
    print("Design is compliant with IDM standards")
else:
    print("Compliance issues detected:")
    for issue in issues:
        print(f"  - {issue}")
```

## Batch Processing

```python
from roadscript import ClearZoneCalculator

calculator = ClearZoneCalculator()

# Multiple design scenarios
scenarios = [
    {"speed": 30, "adt": 400, "slope_position": "foreslope", "slope": "6_1_or_flatter"},
    {"speed": 50, "adt": 2000, "slope_position": "foreslope", "slope": "6_1_or_flatter"},
    {"speed": 60, "adt": 5000, "slope_position": "foreslope", "slope": "5_1_or_4_1"},
    {"speed": 70, "adt": 10000, "slope_position": "backslope", "slope": "4_1_or_5_1"},
]

print("Clear Zone Width Analysis:")
print("-" * 60)
for scenario in scenarios:
    result = calculator.calculate(
        design_speed=scenario["speed"],
        adt=scenario["adt"],
        slope_position=scenario["slope_position"],
        slope_category=scenario["slope"]
    )
    print(f"Speed: {scenario['speed']} mph, ADT: {scenario['adt']}")
    print(f"  Range: {result['min_width']}-{result['max_width']} feet ({result['adt_category']})")
    print()
```

## Standards Metadata Access

```python
from roadscript import StandardsLoader

loader = StandardsLoader()
metadata = loader.get_metadata()

print("IDM Standards Information:")
print(f"  Version: {metadata['version']}")
print(f"  Authority: {metadata['authority']}")
print(f"  Last Updated: {metadata['last_updated']}")
print(f"  Description: {metadata['description']}")
```
