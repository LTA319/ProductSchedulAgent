# Technology Stack

## Core Technologies
- Python 3.8+
- Google OR-Tools (constraint programming solver)
- Streamlit (web UI framework)
- Pandas (data processing and Excel I/O)
- Plotly (interactive visualization)
- openpyxl (Excel file handling)

## Testing
- pytest (test runner)
- hypothesis (property-based testing)
- pytest-cov (coverage reporting)

## Common Commands

### Environment Setup
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run Application
```bash
# Quick start (automated)
./run.sh          # Linux/Mac
run.bat           # Windows

# Manual start
streamlit run ui/app.py
```

### Testing
```bash
# All tests
pytest tests/

# Property tests only
pytest tests/property_tests/ -v

# With coverage
pytest --cov=data_layer --cov=business_logic --cov=ui tests/
```

### Development Server
The Streamlit app runs on `http://localhost:8501` by default. To use a different port:
```bash
streamlit run ui/app.py --server.port 8502
```

## Package Management
Dependencies are managed via `requirements.txt`. When adding new dependencies, update this file and document the purpose in comments.
