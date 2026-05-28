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
