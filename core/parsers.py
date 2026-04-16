"""Unit tests for the voyage file parser."""

import pytest
import pandas as pd
import tempfile, os
from core.parsers import parse_voyage_file


SAMPLE_DATA = pd.DataFrame([
    {"phase": "Hotelling",  "duration_h": 8,  "load_factor": 0.0,  "engine_name": "Aux",  "power_kw": 1200,  "sfc_g_per_kwh": 210, "fuel_type": "MDO", "num_units": 2},
    {"phase": "At-Sea",     "duration_h": 48, "load_factor": 0.75, "engine_name": "Main", "power_kw": 12000, "sfc_g_per_kwh": 175, "fuel_type": "HFO", "num_units": 1},
    {"phase": "At-Sea",     "duration_h": 48, "load_factor": 0.75, "engine_name": "Aux",  "power_kw": 1200,  "sfc_g_per_kwh": 210, "fuel_type": "MDO", "num_units": 2},
])


def _write_csv(df, suffix=".csv"):
    f = tempfile.NamedTemporaryFile(suffix=suffix, delete=False, mode="w")
    df.to_csv(f, index=False)
    f.close()
    return f.name


def test_parse_csv_returns_correct_number_of_legs():
    path = _write_csv(SAMPLE_DATA)
    try:
        legs = parse_voyage_file(path)
        assert len(legs) == 2  # Hotelling + At-Sea
    finally:
        os.unlink(path)


def test_at_sea_has_two_engines():
    path = _write_csv(SAMPLE_DATA)
    try:
        legs = parse_voyage_file(path)
        at_sea = next(l for l in legs if l.phase == "At-Sea")
        assert len(at_sea.engines) == 2
    finally:
        os.unlink(path)


def test_missing_column_raises():
    bad_df = SAMPLE_DATA.drop(columns=["fuel_type"])
    path = _write_csv(bad_df)
    try:
        with pytest.raises(ValueError, match="Missing required columns"):
            parse_voyage_file(path)
    finally:
        os.unlink(path)


def test_unsupported_fuel_raises():
    bad_df = SAMPLE_DATA.copy()
    bad_df.loc[0, "fuel_type"] = "COAL"
    path = _write_csv(bad_df)
    try:
        with pytest.raises(ValueError, match="Unsupported fuel types"):
            parse_voyage_file(path)
    finally:
        os.unlink(path)


def test_unsupported_extension_raises():
    with pytest.raises(ValueError, match="Unsupported file type"):
        parse_voyage_file("voyage.txt")