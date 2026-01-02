# RoadScript

## Deterministic Engineering Core for INDOT Roadway Design

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

RoadScript is a professional-grade Python engine that centralizes IDM (Indiana Design Manual) compliant mathematics for roadway design. It provides a modular, testable, and legally defensible framework for clear zones and geometric design calculations.

## 🎯 Purpose

This repository serves as the **Deterministic Engineering Core** for INDOT roadway design agents, providing:

- **Modular, testable Python engine** for IDM-compliant calculations
- **JSON-based "Source of Truth"** for IDM standards (version-controlled and auditable)
- **Validation layer** with automated pytest suites for legal defensibility
- **Professional audit logging** for complete traceability
- **Standard of Care compliance** for commercial AI design applications

## 🏗️ Architecture

### Core Components

1. **Data Layer** (`roadscript/data/`)
   - `idm_standards.json`: Authoritative JSON-based standards database

2. **Standards Module** (`roadscript/standards/`)
   - `loader.py`: Singleton loader for standards access

3. **Core Calculators** (`roadscript/core/`)
   - `clear_zones.py`: Clear zone width calculations
   - `geometry.py`: Geometric design parameters (curves, sight distance)
   - `engine.py`: Pure functions for core IDM math

4. **Validation Layer** (`roadscript/validation/`)
   - `validators.py`: Input validation and compliance checking
   - Pre-calculation input validation
   - Post-calculation compliance verification

5. **Validators** (`roadscript/validators/`)
   - `base.py`: ValidationResult and IDM 43-4.0 vertical curve checks

6. **Audit Logging** (`roadscript/logging/`, `roadscript/utils/`)
   - `audit.py`: Structured logging for all calculations
   - `utils/audit.py`: Validation audit log with revision tags
   - JSON-formatted audit trails
   - Legal defensibility and traceability

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/derek-betz/RoadScript.git
cd RoadScript

# Install the package
pip install -e .

# Install development dependencies
pip install -r requirements.txt
```

## 🚀 Quick Start

### Clear Zone Calculation

```python
from roadscript import ClearZoneCalculator

calculator = ClearZoneCalculator()

result = calculator.calculate(
    design_speed=60,
    adt=5000,
    slope_position="foreslope",
    slope_category="6_1_or_flatter"
)

print(f"Clear Zone Range: {result['min_width']}-{result['max_width']} feet")
print(f"ADT Category: {result['adt_category']}")
print(f"Compliant: {result['compliant']}")
```

### Geometric Design Calculations

```python
from roadscript import GeometryCalculator

calculator = GeometryCalculator()

# Minimum horizontal curve radius
radius_result = calculator.calculate_minimum_radius(design_speed=60)
print(f"Minimum Radius: {radius_result['minimum_radius']} feet")

# Vertical curve length
curve_result = calculator.calculate_vertical_curve_length(
    design_speed=60,
    grade_difference=4.0,
    curve_type="crest"
)
print(f"Curve Length: {curve_result['curve_length']} feet")

# Stopping sight distance
ssd_result = calculator.calculate_stopping_sight_distance(design_speed=60)
print(f"Stopping Sight Distance: {ssd_result['stopping_sight_distance']} feet")
```

## 🧪 Testing

RoadScript includes a comprehensive pytest suite for legal defensibility:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=roadscript --cov-report=html

# Run only unit tests
pytest tests/unit/ -v

# Run only integration tests
pytest tests/integration/ -v

# Run specific test markers
pytest -m unit
pytest -m integration
pytest -m compliance
```

### Test Coverage

- **Unit Tests**: Individual component testing
  - Standards loader
  - Input validators
  - Each calculator module
  - Compliance checkers

- **Integration Tests**: End-to-end workflow testing
  - Complete design workflows
  - Multi-component interactions
  - Standards consistency

- **Compliance Tests**: IDM standard verification
  - Boundary conditions
  - Edge cases
  - Standards conformance

## 📊 Standards Database

The `roadscript/data/idm_standards.json` file serves as the single source of truth for all calculations. It includes:

### Clear Zones
- Design speed-based requirements (30-70 mph)
- ADT (Average Daily Traffic) categories
- Foreslope and backslope category specifications
- IDM Figure 49-2A compliance

### Geometry
- Horizontal curve minimum radius
- Vertical curve lengths (crest and sag)
- Stopping sight distance
- Superelevation and friction factors

## 🔍 Validation & Compliance

Every calculation includes:

1. **Pre-calculation Input Validation**
   - Required field checking
   - Range validation
   - Type checking
   - IDM conformance
   - Missing design speeds raise `StandardInterpolationRequiredError`

2. **Post-calculation Compliance Checking**
   - Minimum/maximum standard verification
   - Warning generation for edge cases
   - Compliance flag in results

3. **Audit Trail Logging**
   - Timestamped calculation records
   - Input parameters logged
   - Output results logged
   - Standards version tracking
   - Validation results logged to `roadscript_audit.log` with revision tags

## 📝 Audit Logging

All calculations are automatically logged with:

```json
{
  "timestamp": "2024-01-01T12:00:00.000000",
  "calculation_type": "clear_zone",
  "status": "SUCCESS",
  "standards_version": "2024.1",
  "inputs": {
    "design_speed": 60,
    "adt": 5000,
    "slope_position": "foreslope",
    "slope_category": "6_1_or_flatter"
  },
  "outputs": {
    "min_width": 26,
    "max_width": 30,
    "compliant": true,
    "warnings": []
  }
}
```

Validation results (for example, IDM 43-4.0 vertical curve checks) are appended to `roadscript_audit.log` with a timestamp and revision tag.

## 🔒 Legal Defensibility

RoadScript is designed with legal defensibility in mind:

- **Version-controlled standards**: JSON standards tracked in git
- **Complete audit trails**: Every calculation logged with timestamps
- **Deterministic calculations**: Same inputs always produce same outputs
- **Test-driven development**: Comprehensive test coverage
- **Standards traceability**: Each result includes standards version used
- **Input validation**: Prevents invalid or out-of-range inputs
- **Compliance checking**: Automatic verification against IDM standards

## 🤝 Contributing

Contributions are welcome! When contributing, please:

1. Ensure all tests pass
2. Add tests for new functionality
3. Update documentation as needed
4. Follow existing code style
5. Update the standards JSON if needed (with proper documentation)

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **INDOT (Indiana Department of Transportation)** for design standards
- **AASHTO** for roadside design guidance
- **IDM (Indiana Design Manual)** as the authoritative source

## 📞 Support

For questions or issues, please open an issue on GitHub.

## 🗺️ Roadmap

Future enhancements may include:

- Additional geometric design calculations
- Drainage design modules
- Pavement design calculations
- Integration with CAD systems
- Web API for remote calculations
- Visualization tools for results

---

**Note**: This is a deterministic engineering tool. All calculations should be reviewed by a licensed professional engineer before use in production designs.
