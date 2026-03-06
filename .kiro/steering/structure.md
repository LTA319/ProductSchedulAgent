# Project Structure

## Architecture Pattern
Three-layer architecture with clear separation of concerns:

### data_layer/
Data access and model definitions. Handles parsing, validation, and data structures.
- `models.py` - Dataclass definitions for all domain objects (Order, Process, Equipment, etc.)
- `parser.py` - Excel file parsing logic
- `validator.py` - Data validation rules

### business_logic/
Core algorithms and business rules. No UI or data access concerns.
- `scheduler.py` - CP-SAT constraint programming solver implementation
- `metrics.py` - KPI calculations (utilization, on-time delivery, bottlenecks)
- `visualizer.py` - Gantt chart generation using Plotly

### ui/
Presentation layer using Streamlit.
- `app.py` - Main web application with file upload, scheduling triggers, and result display

### tests/
Comprehensive test suite with multiple testing strategies.
- `property_tests/` - Hypothesis-based property tests for each module
- `test_*.py` - Unit and integration tests
- `data_generators.py` - Test data generation utilities
- `example_data.xlsx` - Sample data for manual testing

### docs/
Documentation and reference materials.
- `DATA_FORMAT.md` - Excel data format specifications
- Sample data files and design documents

### .kiro/
Kiro-specific configuration and specifications.
- `specs/production-scheduling-agent/` - Requirements, design, and task documents

## Conventions

### Naming
- Use descriptive Chinese docstrings for modules and classes
- Use English for variable/function names
- Prefix private methods with underscore: `_preprocess_data()`

### Type Annotations
All public functions use Python type hints. Dataclasses are preferred for data structures.

### Time Units
- Input data: minutes (standard_time in Process)
- Internal calculations: minutes (scaled by time_scale factor)
- Output/display: hours (converted back for user-facing results)

### Module Imports
Each layer imports only from its own level or lower layers. UI imports from business_logic and data_layer, but not vice versa.
