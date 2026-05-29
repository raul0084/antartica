from pathlib import Path
import json

BASE_PATH = Path(__file__).resolve().parents[1]

def load_json(name):
    with open(BASE_PATH / "data" / name) as f:
        return json.load(f)

def default_emission_factors():
    return load_json("emission_factors.json")

def default_uncertainties():
    return load_json("uncertainties.json")

def validate_calls(df):
    required = {"vaixellnom", "etautc", "imo", "mmsi", "etdutc", "terminalnom", "consignatari"}
    missing = required - set(df.columns)
    if missing:
        return False, f"Missing columns: {', '.join(missing)}"
    return True, ""

def validate_vaixells(df):
    required = {"vaixellnom", "imo", "mmsi", "fuel", "p_main", "p_aux", "p_gt", "eslora_metres"}
    missing = required - set(df.columns)
    if missing:
        return False, f"Missing columns: {', '.join(missing)}"
    return True, ""