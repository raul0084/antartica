# Ship Emissions Calculator

A generalised ship emissions modelling tool with a web interface.
Ported and generalised from MATLAB models developed for cruise ships in Barcelona port.

## Quickstart (Docker)

```bash
docker-compose up --build
```

- **API docs**: http://localhost:8000/docs
- **Web UI**:   http://localhost:8501

## Quickstart (local dev)

```bash
pip install -r requirements.txt

# Run API
uvicorn api.main:app --reload

# Run UI (separate terminal)
streamlit run app/main.py
```

## Input file format

See `data/sample_voyage.csv` for a template.

Required columns:
| Column | Description | Example |
|--------|-------------|---------|
| phase | Voyage phase name | At-Sea |
| duration_h | Duration (hours) | 48 |
| load_factor | Engine load 0–1 | 0.75 |
| engine_name | Engine label | Main Engine |
| power_kw | Installed power (kW) | 12000 |
| sfc_g_per_kwh | Specific fuel consumption | 175 |
| fuel_type | HFO / MDO / LNG / VLSFO | HFO |
| num_units | Number of identical engines | 1 |

## Running tests

```bash
pytest tests/ -v --cov=core
```