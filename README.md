# RoadScript

## Deterministic Engineering Core for INDOT Roadway Design

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

RoadScript is a professional-grade Python engine that centralizes IDM (Indiana Design Manual) compliant mathematics for roadway design. It provides a modular, testable, and legally defensible framework for buffer strips, clear zones, and geometric design calculations.

## 🎯 Purpose

This repository serves as the **Deterministic Engineering Core** for INDOT roadway design agents, providing:

- **Modular, testable Python engine** for IDM-compliant calculations
- **JSON-based "Source of Truth"** for IDM standards (version-controlled and auditable)
- **Validation layer** with automated pytest suites for legal defensibility
- **Professional audit logging** for complete traceability
- **Standard of Care compliance** for commercial AI design applications

## 🏗️ Architecture

### Core Components

1. **Standards Module** (`roadscript/standards/`)
   - `idm_standards.json`: Authoritative JSON-based standards database
   - `loader.py`: Singleton loader for standards access

2. **Core Calculators** (`roadscript/core/`)
   - `buffer_strips.py`: Buffer strip width calculations
   - `clear_zones.py`: Clear zone width calculations
   - `geometry.py`: Geometric design parameters (curves, sight distance)

3. **Validation Layer** (`roadscript/validation/`)
   - `validators.py`: Input validation and compliance checking
   - Pre-calculation input validation
   - Post-calculation compliance verification

4. **Audit Logging** (`roadscript/logging/`)
   - `audit.py`: Structured logging for all calculations
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

### Buffer Strip Calculation

```python
from roadscript import BufferStripCalculator

calculator = BufferStripCalculator()

result = calculator.calculate(
    road_classification="interstate",
    design_speed=65,
    terrain="rolling",
    traffic_volume="high"
)

print(f"Buffer Strip Width: {result['width']} feet")
print(f"Compliant: {result['compliant']}")
print(f"Standards Version: {result['standards_version']}")
```

### Clear Zone Calculation

```python
from roadscript import ClearZoneCalculator

calculator = ClearZoneCalculator()

result = calculator.calculate(
    design_speed=60,
    adt=5000,
    slope_category="fill_slope_6_1_or_flatter"
)

print(f"Clear Zone Width: {result['width']} feet")
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

The `idm_standards.json` file serves as the single source of truth for all calculations. It includes:

### Buffer Strips
- Road classifications (Interstate, US Route, State Highway, Local Road)
- Design speed-based widths
- Terrain adjustment factors (flat, rolling, mountainous)
- Traffic volume adjustment factors (low, medium, high)

### Clear Zones
- Design speed-based requirements (30-70 mph)
- ADT (Average Daily Traffic) categories
- Slope category specifications
- AASHTO Roadside Design Guide compliance

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

2. **Post-calculation Compliance Checking**
   - Minimum/maximum standard verification
   - Warning generation for edge cases
   - Compliance flag in results

3. **Audit Trail Logging**
   - Timestamped calculation records
   - Input parameters logged
   - Output results logged
   - Standards version tracking

## 📝 Audit Logging

All calculations are automatically logged with:

```json
{
  "timestamp": "2024-01-01T12:00:00.000000",
  "calculation_type": "buffer_strip",
  "status": "SUCCESS",
  "standards_version": "2024.1",
  "inputs": {
    "road_classification": "interstate",
    "design_speed": 65,
    "terrain": "rolling"
  },
  "outputs": {
    "width": 46.0,
    "compliant": true,
    "warnings": []
  }
}
```

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